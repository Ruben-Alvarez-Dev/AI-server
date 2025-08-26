"""
Vector Store Implementation for Memory-Server
Provides FAISS-based vector storage with similarity search
Uses Embedding Hub for vector generation
"""

import os
import pickle
import asyncio
from pathlib import Path
from typing import List, Tuple, Optional, Union, Dict, Any
import numpy as np

try:
    import faiss
except ImportError:
    faiss = None

from core.config import get_config
from core.logging_config import get_logger
from core.embedding_client import get_embedding_client, EmbeddingAgent
from core.local_embeddings import get_local_embeddings, get_hash_embeddings

logger = get_logger(__name__)

class VectorStore:
    """FAISS-based vector store for embeddings"""
    
    def __init__(self, dimension: int = 768):
        self.config = get_config()
        self.dimension = dimension
        self.index = None
        self.id_to_metadata = {}
        self.next_id = 0
        self.embedding_client = None
        self.fallback_embeddings = None
        self.use_embedding_hub = self.config.USE_EMBEDDING_HUB
        
    async def initialize(self):
        """Initialize FAISS index and embedding client"""
        if faiss is None:
            logger.warning("FAISS not available, using mock vector store")
            return
            
        # Create HNSW index for better performance
        self.index = faiss.IndexHNSWFlat(self.dimension, self.config.HNSW_M)
        self.index.hnsw.efConstruction = self.config.HNSW_EF_CONSTRUCTION
        self.index.hnsw.efSearch = self.config.HNSW_EF_SEARCH
        
        # Initialize embedding client if enabled
        if self.use_embedding_hub:
            try:
                self.embedding_client = await get_embedding_client()
                logger.info("Connected to Embedding Hub")
            except Exception as e:
                logger.warning(f"Failed to connect to Embedding Hub: {e}, using fallback")
                self.use_embedding_hub = False
        
        # Initialize fallback embeddings
        if not self.use_embedding_hub:
            self.fallback_embeddings = get_local_embeddings(self.dimension)
            logger.info("Using local embeddings fallback")
        
        logger.info(f"Vector store initialized with dimension {self.dimension}")
    
    async def embed_text(self, 
                        text: str, 
                        content_type: str = "text",
                        metadata: Optional[Dict[str, Any]] = None,
                        agent: Optional[EmbeddingAgent] = None) -> np.ndarray:
        """Generate embedding for text using appropriate method"""
        
        if self.use_embedding_hub and self.embedding_client:
            try:
                embedding = await self.embedding_client.embed(
                    content=text,
                    content_type=content_type,
                    metadata=metadata,
                    agent=agent
                )
                return np.array(embedding, dtype=np.float32)
            except Exception as e:
                logger.warning(f"Embedding Hub failed, using fallback: {e}")
        
        # Use fallback embeddings
        if self.fallback_embeddings:
            return self.fallback_embeddings.embed(text)
        else:
            # Use hash-based as last resort
            hash_embeddings = get_hash_embeddings(self.dimension)
            return hash_embeddings.embed(text)
    
    async def embed_texts(self, 
                         texts: List[str],
                         content_type: str = "text", 
                         metadata: Optional[Dict[str, Any]] = None,
                         agent: Optional[EmbeddingAgent] = None) -> np.ndarray:
        """Generate embeddings for multiple texts"""
        
        if self.use_embedding_hub and self.embedding_client:
            try:
                embeddings = await self.embedding_client.embed(
                    content=texts,
                    content_type=content_type,
                    metadata=metadata,
                    agent=agent
                )
                return np.array(embeddings, dtype=np.float32)
            except Exception as e:
                logger.warning(f"Embedding Hub batch failed, using fallback: {e}")
        
        # Use fallback embeddings
        if self.fallback_embeddings:
            return np.array([self.fallback_embeddings.embed(text) for text in texts])
        else:
            hash_embeddings = get_hash_embeddings(self.dimension)
            return np.array([hash_embeddings.embed(text) for text in texts])
    
    async def add_texts(self, 
                       texts: List[str],
                       metadata: Optional[List[Dict[str, Any]]] = None,
                       content_type: str = "text",
                       agent: Optional[EmbeddingAgent] = None) -> List[int]:
        """Add texts by generating embeddings and storing them"""
        
        if metadata is None:
            metadata = [{}] * len(texts)
        
        # Generate embeddings
        embeddings = await self.embed_texts(texts, content_type, {}, agent)
        
        # Add metadata about the text content
        enriched_metadata = []
        for i, text in enumerate(texts):
            meta = metadata[i].copy() if i < len(metadata) else {}
            meta.update({
                'text': text,
                'content_type': content_type,
                'text_length': len(text),
                'word_count': len(text.split())
            })
            enriched_metadata.append(meta)
        
        # Store in vector index
        return self.add_vectors(embeddings, enriched_metadata)
    
    async def search_texts(self, 
                          query: str,
                          k: int = 10,
                          content_type: str = "query",
                          metadata: Optional[Dict[str, Any]] = None) -> List[Tuple[int, float, Dict[str, Any]]]:
        """Search for similar texts using query embedding"""
        
        # Generate query embedding
        query_embedding = await self.embed_text(
            query, 
            content_type=content_type,
            metadata=metadata,
            agent=EmbeddingAgent.QUERY
        )
        
        # Search in vector store
        return self.search(query_embedding.reshape(1, -1), k)
    
    def add_vectors(self, vectors: np.ndarray, metadata: List[dict]) -> List[int]:
        """Add vectors to the index"""
        if self.index is None:
            logger.warning("Index not initialized")
            return []
            
        if len(vectors) != len(metadata):
            raise ValueError("Vectors and metadata must have same length")
            
        # Add vectors to index
        self.index.add(vectors.astype(np.float32))
        
        # Store metadata
        ids = []
        for meta in metadata:
            self.id_to_metadata[self.next_id] = meta
            ids.append(self.next_id)
            self.next_id += 1
            
        logger.info(f"Added {len(vectors)} vectors to index")
        return ids
    
    def search(self, query_vector: np.ndarray, k: int = 10) -> Tuple[List[float], List[dict]]:
        """Search for similar vectors"""
        if self.index is None:
            logger.warning("Index not initialized, returning empty results")
            return [], []
            
        query_vector = query_vector.astype(np.float32).reshape(1, -1)
        scores, indices = self.index.search(query_vector, k)
        
        # Get metadata for results
        results_metadata = []
        results_scores = []
        
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx in self.id_to_metadata:
                results_scores.append(float(score))
                results_metadata.append(self.id_to_metadata[idx])
                
        return results_scores, results_metadata
    
    def save(self, save_path: Path):
        """Save index and metadata"""
        if self.index is not None:
            faiss.write_index(self.index, str(save_path / "faiss.index"))
        
        with open(save_path / "vector_metadata.pkl", "wb") as f:
            pickle.dump({
                "id_to_metadata": self.id_to_metadata,
                "next_id": self.next_id,
                "dimension": self.dimension
            }, f)
            
        logger.info(f"Vector store saved to {save_path}")
    
    def load(self, load_path: Path):
        """Load index and metadata"""
        if (load_path / "faiss.index").exists():
            self.index = faiss.read_index(str(load_path / "faiss.index"))
            
        if (load_path / "vector_metadata.pkl").exists():
            with open(load_path / "vector_metadata.pkl", "rb") as f:
                data = pickle.load(f)
                self.id_to_metadata = data["id_to_metadata"]
                self.next_id = data["next_id"] 
                self.dimension = data["dimension"]
                
        logger.info(f"Vector store loaded from {load_path}")
    
    def get_stats(self) -> dict:
        """Get vector store statistics"""
        return {
            "total_vectors": self.index.ntotal if self.index else 0,
            "dimension": self.dimension,
            "index_type": type(self.index).__name__ if self.index else "None"
        }