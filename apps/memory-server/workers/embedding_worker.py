"""
Embedding Processing Worker
Handles async embedding generation for documents
"""

from celery import Task
import asyncio
from typing import Dict, Any, List, Optional
import numpy as np
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.celery_app import celery_app
from core.config import get_config
from core.logging_config import get_logger

logger = get_logger("embedding-worker")
config = get_config()

class EmbeddingTask(Task):
    """Task with persistent embedding client"""
    _embedding_client = None
    _loop = None
    
    @property
    def embedding_client(self):
        """Lazy load embedding client"""
        if self._embedding_client is None:
            from core.embedding_client import EmbeddingHubClient
            self._embedding_client = EmbeddingHubClient(
                hub_host=config.EMBEDDING_HUB_HOST,
                hub_port=config.EMBEDDING_HUB_PORT
            )
            logger.info("Embedding client initialized")
        return self._embedding_client
    
    @property
    def loop(self):
        """Get or create event loop for async operations"""
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
        return self._loop

@celery_app.task(
    base=EmbeddingTask,
    bind=True,
    name='generate_embeddings',
    queue='embeddings',
    max_retries=3,
    default_retry_delay=30
)
def generate_embeddings(
    self,
    content: str,
    content_type: str = 'text',
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate embeddings for content
    
    Args:
        content: Text content to embed
        content_type: Type of content (text, code, conversation, etc.)
        metadata: Optional metadata for embedding generation
    
    Returns:
        Embeddings and metadata
    """
    try:
        logger.info(f"Generating embeddings for content type: {content_type}")
        
        # Update task state
        self.update_state(
            state='PROCESSING',
            meta={
                'current': 'Generating embeddings',
                'content_type': content_type,
                'progress': 50
            }
        )
        
        # Initialize client if needed
        if not self.loop.run_until_complete(self._ensure_client_initialized()):
            raise ConnectionError("Failed to initialize embedding client")
        
        # Generate embeddings
        embeddings = self.loop.run_until_complete(
            self.embedding_client.embed(
                content=content,
                content_type=content_type,
                metadata=metadata
            )
        )
        
        # Convert to list if numpy array
        if isinstance(embeddings, np.ndarray):
            embeddings = embeddings.tolist()
        
        logger.info(f"Successfully generated embeddings (dimension: {len(embeddings)})")
        
        return {
            'status': 'success',
            'embeddings': embeddings,
            'dimension': len(embeddings),
            'content_type': content_type,
            'metadata': metadata
        }
        
    except ConnectionError as e:
        logger.error(f"Connection error: {e}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            retry_delay = 30 * (2 ** self.request.retries)  # Exponential backoff
            logger.info(f"Retrying in {retry_delay} seconds (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e, countdown=retry_delay)
        
        raise
        
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        
        # Check if we should retry
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying task (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e)
        
        # Final failure
        self.update_state(
            state='FAILURE',
            meta={
                'error': str(e),
                'error_type': type(e).__name__
            }
        )
        raise

    async def _ensure_client_initialized(self) -> bool:
        """Ensure embedding client is initialized"""
        try:
            await self.embedding_client.initialize()
            return True
        except Exception as e:
            logger.error(f"Failed to initialize embedding client: {e}")
            return False

@celery_app.task(
    base=EmbeddingTask,
    bind=True,
    name='batch_generate_embeddings',
    queue='embeddings'
)
def batch_generate_embeddings(
    self,
    contents: List[str],
    content_type: str = 'text',
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate embeddings for multiple contents in batch
    
    Args:
        contents: List of text contents to embed
        content_type: Type of content
        metadata: Optional metadata
    
    Returns:
        Batch embeddings result
    """
    try:
        logger.info(f"Generating batch embeddings for {len(contents)} items")
        
        # Update task state
        self.update_state(
            state='PROCESSING',
            meta={
                'current': 'Processing batch embeddings',
                'total_items': len(contents),
                'progress': 10
            }
        )
        
        # Initialize client
        if not self.loop.run_until_complete(self._ensure_client_initialized()):
            raise ConnectionError("Failed to initialize embedding client")
        
        # Process in batches to avoid overwhelming the service
        batch_size = 10
        all_embeddings = []
        
        for i in range(0, len(contents), batch_size):
            batch = contents[i:i + batch_size]
            
            # Update progress
            progress = int((i / len(contents)) * 80) + 10
            self.update_state(
                state='PROCESSING',
                meta={
                    'current': f'Processing batch {i//batch_size + 1}/{(len(contents) + batch_size - 1)//batch_size}',
                    'total_items': len(contents),
                    'processed': i,
                    'progress': progress
                }
            )
            
            # Generate embeddings for batch
            batch_embeddings = self.loop.run_until_complete(
                self.embedding_client.embed(
                    content=batch,
                    content_type=content_type,
                    metadata=metadata
                )
            )
            
            all_embeddings.extend(batch_embeddings)
        
        logger.info(f"Successfully generated {len(all_embeddings)} embeddings")
        
        return {
            'status': 'success',
            'embeddings': all_embeddings,
            'total_count': len(all_embeddings),
            'content_type': content_type,
            'metadata': metadata
        }
        
    except Exception as e:
        logger.error(f"Error in batch embedding generation: {e}")
        
        self.update_state(
            state='FAILURE',
            meta={
                'error': str(e),
                'error_type': type(e).__name__
            }
        )
        raise

@celery_app.task(
    name='generate_query_embedding',
    queue='embeddings'
)
def generate_query_embedding(
    query: str,
    use_query_optimization: bool = True
) -> Dict[str, Any]:
    """
    Generate optimized embedding for search query
    
    Args:
        query: Search query text
        use_query_optimization: Apply query-specific optimizations
    
    Returns:
        Query embedding
    """
    try:
        logger.info(f"Generating query embedding: {query[:50]}...")
        
        # Use the specialized query embedding method
        task = generate_embeddings.apply_async(
            args=[query],
            kwargs={
                'content_type': 'query',
                'metadata': {'use_query_optimization': use_query_optimization}
            },
            queue='embeddings',
            priority=5  # Higher priority for queries
        )
        
        return {
            'task_id': task.id,
            'status': 'queued',
            'message': 'Query embedding generation started'
        }
        
    except Exception as e:
        logger.error(f"Error queuing query embedding: {e}")
        raise