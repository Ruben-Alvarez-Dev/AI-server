"""
FAISS Vector Store with GPU Optimization for M1 Ultra
High-performance vector similarity search
"""

import asyncio
import logging
import pickle
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import faiss
import os
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class VectorStore:
    """
    FAISS-based vector store optimized for M1 Ultra
    Supports both CPU and GPU acceleration
    """
    
    def __init__(
        self,
        dimension: int = 384,  # sentence-transformers default
        index_type: str = "IVF",
        nlist: int = 100,
        store_path: str = "./vector_store",
        use_gpu: bool = False
    ):
        self.dimension = dimension
        self.index_type = index_type
        self.nlist = nlist
        self.store_path = Path(store_path)
        self.use_gpu = use_gpu
        
        # Initialize FAISS index
        self.index = None
        self.document_store = {}  # id -> document mapping
        self.metadata_store = {}  # id -> metadata mapping
        self.next_id = 0
        
        # Create storage directory
        self.store_path.mkdir(parents=True, exist_ok=True)
        
        self._initialize_index()
        
        logger.info(f"VectorStore initialized: dim={dimension}, type={index_type}, gpu={use_gpu}")
    
    def _initialize_index(self):
        """Initialize FAISS index based on configuration"""
        
        if self.index_type == "Flat":
            # Brute force exact search (slower but accurate)
            self.index = faiss.IndexFlatL2(self.dimension)
        elif self.index_type == "IVF":
            # Inverted File index (faster approximate search)
            quantizer = faiss.IndexFlatL2(self.dimension)
            self.index = faiss.IndexIVFFlat(quantizer, self.dimension, self.nlist)
        elif self.index_type == "HNSW":
            # Hierarchical NSW (good for high-dimensional data)
            self.index = faiss.IndexHNSWFlat(self.dimension, 32)
        else:
            logger.warning(f"Unknown index type {self.index_type}, using Flat")
            self.index = faiss.IndexFlatL2(self.dimension)
        
        # GPU acceleration for M1 Ultra
        if self.use_gpu and faiss.get_num_gpus() > 0:
            try:
                self.index = faiss.index_cpu_to_gpu(faiss.StandardGpuResources(), 0, self.index)
                logger.info("Successfully initialized GPU-accelerated FAISS index")
            except Exception as e:
                logger.warning(f"GPU acceleration failed, using CPU: {e}")
                self.use_gpu = False
        
        logger.info(f"FAISS index initialized: {type(self.index).__name__}")
    
    async def add_documents(
        self, 
        documents: List[Dict[str, Any]], 
        embeddings: np.ndarray
    ) -> List[int]:
        """Add documents with their embeddings to the store"""
        
        if len(documents) != len(embeddings):
            raise ValueError("Number of documents must match number of embeddings")
        
        # Validate embedding dimensions
        if embeddings.shape[1] != self.dimension:
            raise ValueError(f"Embedding dimension {embeddings.shape[1]} doesn't match store dimension {self.dimension}")
        
        # Generate IDs for new documents
        document_ids = list(range(self.next_id, self.next_id + len(documents)))
        self.next_id += len(documents)
        
        # Store documents and metadata
        for doc_id, document in zip(document_ids, documents):
            self.document_store[doc_id] = document.get('content', '')
            self.metadata_store[doc_id] = {
                'title': document.get('title', ''),
                'source': document.get('source', ''),
                'timestamp': document.get('timestamp', 0),
                'chunk_id': document.get('chunk_id', 0),
                'metadata': document.get('metadata', {})
            }
        
        # Train index if needed (for IVF)
        if hasattr(self.index, 'is_trained') and not self.index.is_trained:
            if len(embeddings) >= self.nlist:
                logger.info("Training FAISS index...")
                self.index.train(embeddings.astype(np.float32))
            else:
                logger.warning(f"Not enough vectors to train IVF index (need {self.nlist}, have {len(embeddings)})")
        
        # Add embeddings to index
        self.index.add(embeddings.astype(np.float32))
        
        logger.info(f"Added {len(documents)} documents to vector store (total: {self.index.ntotal})")
        
        return document_ids
    
    async def similarity_search(
        self, 
        query_embedding: np.ndarray, 
        k: int = 5,
        score_threshold: float = None
    ) -> List[Dict[str, Any]]:
        """Search for similar documents using query embedding"""
        
        if query_embedding.shape[0] != self.dimension:
            raise ValueError(f"Query embedding dimension {query_embedding.shape[0]} doesn't match store dimension {self.dimension}")
        
        if self.index.ntotal == 0:
            logger.warning("Vector store is empty")
            return []
        
        # Perform search
        query_vector = query_embedding.reshape(1, -1).astype(np.float32)
        scores, indices = self.index.search(query_vector, min(k, self.index.ntotal))
        
        # Convert results
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:  # FAISS returns -1 for empty slots
                continue
                
            if score_threshold is not None and score > score_threshold:
                continue
            
            document_id = int(idx)
            
            result = {
                'id': document_id,
                'content': self.document_store.get(document_id, ''),
                'metadata': self.metadata_store.get(document_id, {}),
                'score': float(score),
                'similarity': 1.0 / (1.0 + score)  # Convert L2 distance to similarity
            }
            
            results.append(result)
        
        logger.debug(f"Similarity search returned {len(results)} results")
        
        return results
    
    async def search_by_text(
        self, 
        query: str, 
        embeddings_engine,
        k: int = 5,
        score_threshold: float = None
    ) -> List[Dict[str, Any]]:
        """Search using text query (requires embeddings engine)"""
        
        # Generate embedding for query
        query_embedding = await embeddings_engine.embed_text(query)
        
        return await self.similarity_search(query_embedding, k, score_threshold)
    
    async def batch_search(
        self, 
        query_embeddings: np.ndarray, 
        k: int = 5
    ) -> List[List[Dict[str, Any]]]:
        """Batch search for multiple queries"""
        
        if query_embeddings.shape[1] != self.dimension:
            raise ValueError(f"Query embedding dimension {query_embeddings.shape[1]} doesn't match store dimension {self.dimension}")
        
        if self.index.ntotal == 0:
            return [[] for _ in range(len(query_embeddings))]
        
        # Perform batch search
        scores, indices = self.index.search(query_embeddings.astype(np.float32), min(k, self.index.ntotal))
        
        # Convert results
        batch_results = []
        for query_scores, query_indices in zip(scores, indices):
            query_results = []
            
            for score, idx in zip(query_scores, query_indices):
                if idx == -1:
                    continue
                
                document_id = int(idx)
                
                result = {
                    'id': document_id,
                    'content': self.document_store.get(document_id, ''),
                    'metadata': self.metadata_store.get(document_id, {}),
                    'score': float(score),
                    'similarity': 1.0 / (1.0 + score)
                }
                
                query_results.append(result)
            
            batch_results.append(query_results)
        
        return batch_results
    
    async def get_document(self, document_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve specific document by ID"""
        
        if document_id not in self.document_store:
            return None
        
        return {
            'id': document_id,
            'content': self.document_store[document_id],
            'metadata': self.metadata_store[document_id]
        }
    
    async def update_document(
        self, 
        document_id: int, 
        new_embedding: np.ndarray,
        new_content: str = None,
        new_metadata: Dict[str, Any] = None
    ):
        """Update existing document (requires full reindex for FAISS)"""
        
        if document_id not in self.document_store:
            raise ValueError(f"Document {document_id} not found")
        
        # Update document data
        if new_content is not None:
            self.document_store[document_id] = new_content
        
        if new_metadata is not None:
            self.metadata_store[document_id].update(new_metadata)
        
        logger.warning("Document updated in metadata, but FAISS requires full reindex for embedding updates")
    
    async def delete_documents(self, document_ids: List[int]):
        """Delete documents (requires full reindex for FAISS)"""
        
        removed_count = 0
        for doc_id in document_ids:
            if doc_id in self.document_store:
                del self.document_store[doc_id]
                del self.metadata_store[doc_id]
                removed_count += 1
        
        logger.warning(f"Documents removed from metadata ({removed_count}), but FAISS requires full reindex")
    
    async def save_to_disk(self):
        """Save index and metadata to disk"""
        
        # Save FAISS index
        index_path = self.store_path / "index.faiss"
        
        if self.use_gpu and hasattr(self.index, 'gpu'):
            # Copy GPU index to CPU for saving
            cpu_index = faiss.index_gpu_to_cpu(self.index)
            faiss.write_index(cpu_index, str(index_path))
        else:
            faiss.write_index(self.index, str(index_path))
        
        # Save metadata
        metadata_path = self.store_path / "metadata.json"
        metadata = {
            'document_store': self.document_store,
            'metadata_store': self.metadata_store,
            'next_id': self.next_id,
            'dimension': self.dimension,
            'index_type': self.index_type,
            'nlist': self.nlist
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Vector store saved to {self.store_path}")
    
    async def load_from_disk(self):
        """Load index and metadata from disk"""
        
        index_path = self.store_path / "index.faiss"
        metadata_path = self.store_path / "metadata.json"
        
        if not index_path.exists() or not metadata_path.exists():
            logger.warning("No saved vector store found, using empty store")
            return
        
        try:
            # Load FAISS index
            self.index = faiss.read_index(str(index_path))
            
            # Apply GPU acceleration if requested
            if self.use_gpu and faiss.get_num_gpus() > 0:
                try:
                    self.index = faiss.index_cpu_to_gpu(faiss.StandardGpuResources(), 0, self.index)
                    logger.info("Loaded index with GPU acceleration")
                except Exception as e:
                    logger.warning(f"GPU acceleration failed after loading: {e}")
            
            # Load metadata
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Convert string keys back to integers for document_store
            self.document_store = {int(k): v for k, v in metadata['document_store'].items()}
            self.metadata_store = {int(k): v for k, v in metadata['metadata_store'].items()}
            self.next_id = metadata['next_id']
            
            logger.info(f"Vector store loaded: {self.index.ntotal} documents")
            
        except Exception as e:
            logger.error(f"Failed to load vector store: {e}")
            self._initialize_index()  # Fallback to empty index
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        
        return {
            'total_documents': self.index.ntotal if self.index else 0,
            'dimension': self.dimension,
            'index_type': self.index_type,
            'gpu_enabled': self.use_gpu,
            'is_trained': getattr(self.index, 'is_trained', True),
            'storage_path': str(self.store_path),
            'memory_usage': {
                'document_store': len(self.document_store),
                'metadata_store': len(self.metadata_store)
            }
        }
    
    async def clear(self):
        """Clear all data from vector store"""
        
        self._initialize_index()
        self.document_store.clear()
        self.metadata_store.clear()
        self.next_id = 0
        
        logger.info("Vector store cleared")

# Export
__all__ = ['VectorStore']