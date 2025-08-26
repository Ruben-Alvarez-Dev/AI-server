"""
Document Processing Worker
Handles async document ingestion with proper error handling
"""

from celery import Task, states
import asyncio
from typing import Dict, Any, Optional
import logging
import os
import tempfile
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.celery_app import celery_app
from core.config import get_config
from core.logging_config import get_logger

logger = get_logger("document-worker")
config = get_config()

class DocumentIngestionTask(Task):
    """Task with persistent document processor"""
    _processor = None
    _loop = None
    
    @property
    def processor(self):
        """Lazy load document processor"""
        if self._processor is None:
            from api.utils.document_processor import DocumentProcessor
            self._processor = DocumentProcessor()
            logger.info("Document processor initialized")
        return self._processor
    
    @property
    def loop(self):
        """Get or create event loop for async operations"""
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
        return self._loop

@celery_app.task(
    base=DocumentIngestionTask,
    bind=True,
    name='process_document',
    queue='documents',
    max_retries=3,
    default_retry_delay=60
)
def process_document(
    self,
    file_path: str,
    original_name: str,
    workspace: str = 'research',
    auto_summarize: bool = True,
    tags: Optional[list] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Process document asynchronously
    
    Args:
        file_path: Path to temporary file
        original_name: Original filename
        workspace: Target workspace
        auto_summarize: Generate automatic summary
        tags: Optional tags to add
        **kwargs: Additional processing options
    
    Returns:
        Processing result with document_id
    """
    try:
        logger.info(f"Starting processing of document: {original_name}")
        
        # Update task state - Starting
        self.update_state(
            state='PROCESSING',
            meta={
                'current': 'Starting document analysis',
                'filename': original_name,
                'workspace': workspace,
                'progress': 10
            }
        )
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Update state - Processing
        self.update_state(
            state='PROCESSING',
            meta={
                'current': 'Analyzing document content',
                'filename': original_name,
                'progress': 30
            }
        )
        
        # Run async processing in sync context
        try:
            # Process document using async processor
            doc_id = self.loop.run_until_complete(
                self.processor.process_file(
                    file_path=file_path,
                    original_name=original_name,
                    workspace=workspace,
                    auto_summarize=auto_summarize,
                    tags=tags or []
                )
            )
            
            # Update state - Generating embeddings
            self.update_state(
                state='PROCESSING',
                meta={
                    'current': 'Generating embeddings',
                    'filename': original_name,
                    'progress': 70,
                    'document_id': doc_id
                }
            )
            
            # Clean up temporary file if it exists
            try:
                if os.path.exists(file_path) and file_path.startswith('/tmp/'):
                    os.remove(file_path)
                    logger.info(f"Cleaned up temporary file: {file_path}")
            except Exception as e:
                logger.warning(f"Could not clean up temp file {file_path}: {e}")
            
            # Update state - Complete
            self.update_state(
                state='SUCCESS',
                meta={
                    'current': 'Processing complete',
                    'progress': 100,
                    'document_id': doc_id,
                    'filename': original_name,
                    'workspace': workspace
                }
            )
            
            logger.info(f"Successfully processed document {original_name} -> {doc_id}")
            
            return {
                'status': 'success',
                'document_id': doc_id,
                'filename': original_name,
                'workspace': workspace,
                'message': f'Document {original_name} processed successfully'
            }
            
        except Exception as e:
            logger.error(f"Error in async processing: {e}")
            raise
            
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        self.update_state(
            state='FAILURE',
            meta={
                'error': str(e),
                'filename': original_name,
                'error_type': 'FileNotFound'
            }
        )
        raise
        
    except Exception as e:
        logger.error(f"Error processing document {original_name}: {e}")
        
        # Check if we should retry
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying task (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e)
        
        # Final failure
        self.update_state(
            state='FAILURE',
            meta={
                'error': str(e),
                'filename': original_name,
                'error_type': type(e).__name__
            }
        )
        raise

@celery_app.task(
    name='batch_process_documents',
    queue='documents'
)
def batch_process_documents(
    file_paths: list,
    workspace: str = 'research',
    auto_summarize: bool = True
) -> Dict[str, Any]:
    """
    Process multiple documents in batch
    
    Args:
        file_paths: List of (file_path, original_name) tuples
        workspace: Target workspace
        auto_summarize: Generate automatic summaries
    
    Returns:
        Batch processing results
    """
    results = []
    tasks = []
    
    for file_path, original_name in file_paths:
        # Queue each document as separate task
        task = process_document.apply_async(
            args=[file_path, original_name],
            kwargs={'workspace': workspace, 'auto_summarize': auto_summarize},
            queue='documents'
        )
        
        tasks.append(task)
        results.append({
            'filename': original_name,
            'task_id': task.id,
            'status': 'queued'
        })
    
    logger.info(f"Queued {len(tasks)} documents for batch processing")
    
    return {
        'status': 'success',
        'total_documents': len(file_paths),
        'tasks': results,
        'message': f'Batch processing started for {len(file_paths)} documents'
    }

@celery_app.task(
    name='check_document_status',
    queue='default'
)
def check_document_status(task_id: str) -> Dict[str, Any]:
    """
    Check the status of a document processing task
    
    Args:
        task_id: Celery task ID
    
    Returns:
        Task status and metadata
    """
    from celery.result import AsyncResult
    
    result = AsyncResult(task_id, app=celery_app)
    
    response = {
        'task_id': task_id,
        'status': result.status,
        'ready': result.ready()
    }
    
    if result.status == 'PENDING':
        response['message'] = 'Task is waiting to be processed'
    elif result.status == 'PROCESSING':
        response['meta'] = result.info
    elif result.status == 'SUCCESS':
        response['result'] = result.result
    elif result.status == 'FAILURE':
        response['error'] = str(result.info)
        response['traceback'] = result.traceback
    
    return response