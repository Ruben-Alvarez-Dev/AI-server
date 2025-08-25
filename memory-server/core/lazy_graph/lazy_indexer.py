"""
LazyGraphRAG Indexer - Zero-Cost Graph Indexing
Based on Microsoft Research LazyGraphRAG - 0.1% cost of traditional GraphRAG
"""

import asyncio
import numpy as np
import pickle
from typing import List, Dict, Any, Tuple, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path
import faiss
import time
from concurrent.futures import ThreadPoolExecutor
import hashlib

from core.config import get_config
from core.logging_config import get_logger, get_performance_logger

# Setup loggers
logger = get_logger("lazy-graph")
perf_logger = get_performance_logger("lazy-graph")


@dataclass
class Document:
    """Document representation for LazyGraphRAG"""
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[np.ndarray] = None
    content_hash: Optional[str] = field(default=None, init=False)
    created_at: Optional[float] = field(default_factory=time.time)
    
    def __post_init__(self):
        """Generate content hash for deduplication"""
        if self.content_hash is None:
            self.content_hash = hashlib.md5(self.content.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'content': self.content,
            'metadata': self.metadata,
            'content_hash': self.content_hash,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Document':
        """Create document from dictionary"""
        return cls(
            id=data['id'],
            content=data['content'],
            metadata=data.get('metadata', {}),
            created_at=data.get('created_at', time.time())
        )


class LazyGraphIndexer:
    """
    LazyGraphRAG Indexer - Only vectorization, no pre-built graphs
    
    Key Principles:
    1. No expensive graph pre-processing
    2. Dynamic subgraph generation on query
    3. Community detection on-demand
    4. 1000x cost reduction vs traditional GraphRAG
    """
    
    def __init__(self, embedding_model=None):
        self.config = get_config()
        self.embedding_model = embedding_model
        
        # FAISS index for vector storage
        self.vector_index: Optional[faiss.Index] = None
        self.dimension = self.config.VECTOR_DIMENSION
        
        # Document storage
        self.documents: Dict[str, Document] = {}
        self.id_mapping: Dict[str, int] = {}  # external_id -> faiss_id
        self.reverse_mapping: Dict[int, str] = {}  # faiss_id -> external_id
        self.next_id = 0
        
        # Performance tracking
        self.stats = {
            'total_documents': 0,
            'total_embeddings': 0,
            'indexing_time': 0.0,
            'last_update': time.time()
        }
        
        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=self.config.NUM_WORKERS)
    
    async def initialize(self):
        """Initialize the LazyGraphRAG indexer"""
        start_time = time.time()
        
        logger.info("Initializing LazyGraphRAG indexer")
        
        try:
            # Initialize embedding model if not provided
            if self.embedding_model is None:
                await self._initialize_embedding_model()
            
            # Initialize FAISS index
            await self._initialize_vector_index()
            
            # Load existing data if available
            await self._load_existing_data()
            
            init_time = time.time() - start_time
            perf_logger.log_timing("indexer_initialization", init_time)
            
            logger.info(
                "LazyGraphRAG indexer initialized successfully",
                documents=len(self.documents),
                init_time_ms=round(init_time * 1000, 2)
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize LazyGraphRAG indexer: {e}")
            raise
    
    async def _initialize_embedding_model(self):
        """Initialize the embedding model"""
        logger.info(f"Loading embedding model: {self.config.EMBEDDING_MODEL}")
        
        try:
            # Import here to avoid loading if model is provided
            from sentence_transformers import SentenceTransformer
            
            # Load model in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self.embedding_model = await loop.run_in_executor(
                self.executor,
                lambda: SentenceTransformer(self.config.EMBEDDING_MODEL)
            )
            
            # Get actual dimension from model
            test_embedding = self.embedding_model.encode(["test"])
            self.dimension = len(test_embedding[0])
            
            logger.info(
                "Embedding model loaded",
                model=self.config.EMBEDDING_MODEL,
                dimension=self.dimension
            )
            
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    async def _initialize_vector_index(self):
        """Initialize FAISS vector index optimized for M1"""
        logger.info(f"Initializing FAISS index: {self.config.FAISS_INDEX_TYPE.value}")
        
        try:
            if self.config.FAISS_INDEX_TYPE.value == "HNSW":
                # HNSW index for high-quality approximate search
                self.vector_index = faiss.IndexHNSWFlat(
                    self.dimension, 
                    self.config.HNSW_M
                )
                
                # Configure HNSW parameters
                self.vector_index.hnsw.efConstruction = self.config.HNSW_EF_CONSTRUCTION
                self.vector_index.hnsw.efSearch = self.config.HNSW_EF_SEARCH
                
            elif self.config.FAISS_INDEX_TYPE.value == "IVF":
                # IVF index for very large datasets
                quantizer = faiss.IndexFlatL2(self.dimension)
                self.vector_index = faiss.IndexIVFFlat(quantizer, self.dimension, 1024)
                
            else:
                # Flat index for exact search (small datasets)
                self.vector_index = faiss.IndexFlatIP(self.dimension)  # Inner product
            
            logger.info("FAISS index initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize FAISS index: {e}")
            raise
    
    async def _load_existing_data(self):
        """Load existing indexed data"""
        index_path = self.config.DATA_DIR / "lazy_graph_index"
        
        if not index_path.exists():
            logger.info("No existing index found, starting fresh")
            return
        
        try:
            logger.info("Loading existing index data")
            
            # Load FAISS index
            faiss_path = index_path / "faiss.index"
            if faiss_path.exists():
                self.vector_index = faiss.read_index(str(faiss_path))
                logger.info("FAISS index loaded")
            
            # Load metadata
            metadata_path = index_path / "metadata.pkl"
            if metadata_path.exists():
                with open(metadata_path, 'rb') as f:
                    data = pickle.load(f)
                
                self.documents = {
                    doc_id: Document.from_dict(doc_data)
                    for doc_id, doc_data in data.get('documents', {}).items()
                }
                self.id_mapping = data.get('id_mapping', {})
                self.reverse_mapping = data.get('reverse_mapping', {})
                self.next_id = data.get('next_id', 0)
                self.stats = data.get('stats', self.stats)
                
                logger.info(
                    "Metadata loaded",
                    documents=len(self.documents),
                    next_id=self.next_id
                )
            
        except Exception as e:
            logger.warning(f"Failed to load existing data: {e}")
            # Continue with fresh initialization
    
    async def index_document(self, document: Document) -> str:
        """
        Index a single document - Core LazyGraphRAG operation
        Only generates embeddings, NO graph pre-processing
        """
        start_time = time.time()
        
        try:
            # Check for duplicates
            if self._is_duplicate(document):
                logger.info(f"Document {document.id} is a duplicate, skipping")
                return document.id
            
            # Generate embedding if not present
            if document.embedding is None:
                document.embedding = await self._generate_embedding(document.content)
            
            # Add to FAISS index
            embedding_array = document.embedding.reshape(1, -1).astype('float32')
            
            # Normalize for cosine similarity
            faiss.normalize_L2(embedding_array)
            
            # Add to index
            self.vector_index.add(embedding_array)
            
            # Update mappings
            faiss_id = self.next_id
            self.id_mapping[document.id] = faiss_id
            self.reverse_mapping[faiss_id] = document.id
            self.next_id += 1
            
            # Store document
            self.documents[document.id] = document
            
            # Update stats
            self.stats['total_documents'] += 1
            self.stats['total_embeddings'] += 1
            self.stats['last_update'] = time.time()
            
            index_time = time.time() - start_time
            self.stats['indexing_time'] += index_time
            
            perf_logger.log_timing(
                "document_indexing", 
                index_time,
                doc_id=document.id,
                content_length=len(document.content)
            )
            
            logger.info(
                "Document indexed successfully",
                doc_id=document.id,
                content_length=len(document.content),
                index_time_ms=round(index_time * 1000, 2)
            )
            
            return document.id
            
        except Exception as e:
            logger.error(f"Failed to index document {document.id}: {e}")
            raise
    
    async def index_documents(self, documents: List[Document]) -> List[str]:
        """Index multiple documents in batch"""
        start_time = time.time()
        
        logger.info(f"Indexing {len(documents)} documents in batch")
        
        try:
            # Process documents in parallel
            tasks = [self.index_document(doc) for doc in documents]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Separate successful results from exceptions
            successful_ids = []
            failed_count = 0
            
            for result in results:
                if isinstance(result, Exception):
                    failed_count += 1
                    logger.error(f"Document indexing failed: {result}")
                else:
                    successful_ids.append(result)
            
            batch_time = time.time() - start_time
            perf_logger.log_throughput(
                "batch_indexing",
                len(successful_ids),
                batch_time,
                failed=failed_count
            )
            
            logger.info(
                "Batch indexing completed",
                total=len(documents),
                successful=len(successful_ids),
                failed=failed_count,
                batch_time_s=round(batch_time, 2)
            )
            
            return successful_ids
            
        except Exception as e:
            logger.error(f"Batch indexing failed: {e}")
            raise
    
    async def vector_search(
        self, 
        query: Union[str, np.ndarray], 
        k: int = 20,
        threshold: float = 0.0
    ) -> List[Document]:
        """
        Vector search - First step of LazyGraphRAG pipeline
        
        Args:
            query: Query string or embedding vector
            k: Number of results to return
            threshold: Minimum similarity threshold
        
        Returns:
            List of candidate documents for graph construction
        """
        start_time = time.time()
        
        try:
            # Generate query embedding if string provided
            if isinstance(query, str):
                query_embedding = await self._generate_embedding(query)
            else:
                query_embedding = query
            
            # Prepare for FAISS search
            query_vector = query_embedding.reshape(1, -1).astype('float32')
            faiss.normalize_L2(query_vector)
            
            # Search in FAISS
            search_k = min(k * 2, len(self.documents))  # Search more for filtering
            scores, indices = self.vector_index.search(query_vector, search_k)
            
            # Convert results to documents
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1:  # No more results
                    break
                
                if score >= threshold and idx in self.reverse_mapping:
                    doc_id = self.reverse_mapping[idx]
                    if doc_id in self.documents:
                        document = self.documents[doc_id]
                        # Add similarity score to metadata
                        document.metadata['similarity_score'] = float(score)
                        results.append(document)
                
                if len(results) >= k:
                    break
            
            search_time = time.time() - start_time
            perf_logger.log_timing(
                "vector_search",
                search_time,
                query_type=type(query).__name__,
                results_count=len(results),
                k=k
            )
            
            logger.info(
                "Vector search completed",
                results=len(results),
                search_time_ms=round(search_time * 1000, 2),
                avg_score=round(np.mean([doc.metadata.get('similarity_score', 0) for doc in results]), 3) if results else 0
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
    
    async def _generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text"""
        if not text.strip():
            return np.zeros(self.dimension)
        
        try:
            # Handle very long texts
            if len(text) > self.config.MAX_CONTEXT_LENGTH:
                # Truncate or use sliding window
                text = text[:self.config.MAX_CONTEXT_LENGTH]
            
            # Generate embedding in thread pool
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                self.executor,
                lambda: self.embedding_model.encode([text])
            )
            
            return embedding[0]
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            # Return zero vector as fallback
            return np.zeros(self.dimension)
    
    def _is_duplicate(self, document: Document) -> bool:
        """Check if document is a duplicate"""
        # Check by content hash
        for existing_doc in self.documents.values():
            if existing_doc.content_hash == document.content_hash:
                return True
        return False
    
    async def save(self, path: Optional[Path] = None):
        """Save index and metadata to disk"""
        if path is None:
            path = self.config.DATA_DIR / "lazy_graph_index"
        
        start_time = time.time()
        
        try:
            path.mkdir(parents=True, exist_ok=True)
            
            # Save FAISS index
            if self.vector_index is not None:
                faiss_path = path / "faiss.index"
                faiss.write_index(self.vector_index, str(faiss_path))
            
            # Save metadata
            metadata = {
                'documents': {doc_id: doc.to_dict() for doc_id, doc in self.documents.items()},
                'id_mapping': self.id_mapping,
                'reverse_mapping': self.reverse_mapping,
                'next_id': self.next_id,
                'stats': self.stats,
                'config': {
                    'dimension': self.dimension,
                    'index_type': self.config.FAISS_INDEX_TYPE.value
                }
            }
            
            metadata_path = path / "metadata.pkl"
            with open(metadata_path, 'wb') as f:
                pickle.dump(metadata, f)
            
            save_time = time.time() - start_time
            perf_logger.log_timing("index_save", save_time, documents=len(self.documents))
            
            logger.info(
                "Index saved successfully",
                path=str(path),
                documents=len(self.documents),
                save_time_ms=round(save_time * 1000, 2)
            )
            
        except Exception as e:
            logger.error(f"Failed to save index: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get indexer statistics"""
        return {
            **self.stats,
            'index_size': len(self.documents),
            'faiss_index_size': self.vector_index.ntotal if self.vector_index else 0,
            'dimension': self.dimension,
            'memory_usage_mb': self._estimate_memory_usage()
        }
    
    def _estimate_memory_usage(self) -> float:
        """Estimate memory usage in MB"""
        # Rough estimation
        doc_memory = len(self.documents) * 1024  # 1KB per doc metadata
        vector_memory = self.dimension * len(self.documents) * 4  # float32
        mapping_memory = len(self.id_mapping) * 64  # mappings
        
        total_bytes = doc_memory + vector_memory + mapping_memory
        return total_bytes / (1024 * 1024)  # Convert to MB
    
    async def close(self):
        """Close the indexer and cleanup resources"""
        logger.info("Closing LazyGraphRAG indexer")
        
        try:
            # Save current state
            await self.save()
            
            # Shutdown thread pool
            self.executor.shutdown(wait=True)
            
            logger.info("LazyGraphRAG indexer closed successfully")
            
        except Exception as e:
            logger.error(f"Error closing indexer: {e}")
            raise