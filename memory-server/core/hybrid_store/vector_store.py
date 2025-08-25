"""
Vector Store Implementation for Memory-Server
Provides FAISS-based vector storage with similarity search
"""

import os
import pickle
from pathlib import Path
from typing import List, Tuple, Optional, Union
import numpy as np

try:
    import faiss
except ImportError:
    faiss = None

from core.config import get_config
from core.logging_config import get_logger

logger = get_logger(__name__)

class VectorStore:
    """FAISS-based vector store for embeddings"""
    
    def __init__(self, dimension: int = 768):
        self.config = get_config()
        self.dimension = dimension
        self.index = None
        self.id_to_metadata = {}
        self.next_id = 0
        
    def initialize(self):
        """Initialize FAISS index"""
        if faiss is None:
            logger.warning("FAISS not available, using mock vector store")
            return
            
        # Create HNSW index for better performance
        self.index = faiss.IndexHNSWFlat(self.dimension, self.config.HNSW_M)
        self.index.hnsw.efConstruction = self.config.HNSW_EF_CONSTRUCTION
        self.index.hnsw.efSearch = self.config.HNSW_EF_SEARCH
        
        logger.info(f"Vector store initialized with dimension {self.dimension}")
    
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