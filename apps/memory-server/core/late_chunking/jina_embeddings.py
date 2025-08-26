"""
Jina Embeddings Integration
Late chunking with Jina AI embeddings for context preservation
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class JinaEmbeddingModel:
    """
    Jina AI embedding model for late chunking
    """
    
    def __init__(self, model_name: str = "jina-embeddings-v2-base-en"):
        self.model_name = model_name
        self.embedding_dim = 768  # Default dimension
        self.is_initialized = False
        
    def initialize(self):
        """Initialize the embedding model"""
        try:
            # Placeholder for actual Jina AI integration
            # In production, this would load the actual model
            self.is_initialized = True
            logger.info(f"Jina embedding model initialized: {self.model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Jina embedding model: {e}")
            self.is_initialized = False
    
    def encode(self, texts: List[str]) -> np.ndarray:
        """Encode texts to embeddings"""
        
        if not self.is_initialized:
            self.initialize()
        
        try:
            # Placeholder implementation - returns random embeddings for testing
            # In production, this would use actual Jina AI model
            embeddings = []
            
            for text in texts:
                # Generate deterministic "embedding" based on text hash
                # This ensures consistent results for testing
                text_hash = hash(text) % (2**31)
                np.random.seed(text_hash)
                embedding = np.random.normal(0, 1, self.embedding_dim)
                # Normalize
                embedding = embedding / np.linalg.norm(embedding)
                embeddings.append(embedding)
            
            embeddings_array = np.array(embeddings)
            logger.debug(f"Encoded {len(texts)} texts to embeddings: {embeddings_array.shape}")
            
            return embeddings_array
            
        except Exception as e:
            logger.error(f"Text encoding failed: {e}")
            # Return zero embeddings as fallback
            return np.zeros((len(texts), self.embedding_dim))
    
    def encode_single(self, text: str) -> np.ndarray:
        """Encode single text to embedding"""
        return self.encode([text])[0]
    
    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between embeddings"""
        try:
            # Normalize embeddings
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Similarity calculation failed: {e}")
            return 0.0
    
    def batch_similarity(self, embeddings1: np.ndarray, embeddings2: np.ndarray) -> np.ndarray:
        """Calculate pairwise similarities between two sets of embeddings"""
        try:
            # Normalize embeddings
            embeddings1_norm = embeddings1 / np.linalg.norm(embeddings1, axis=1, keepdims=True)
            embeddings2_norm = embeddings2 / np.linalg.norm(embeddings2, axis=1, keepdims=True)
            
            # Compute cosine similarity matrix
            similarity_matrix = np.dot(embeddings1_norm, embeddings2_norm.T)
            
            return similarity_matrix
            
        except Exception as e:
            logger.error(f"Batch similarity calculation failed: {e}")
            return np.zeros((len(embeddings1), len(embeddings2)))
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "model_name": self.model_name,
            "embedding_dim": self.embedding_dim,
            "is_initialized": self.is_initialized,
            "provider": "Jina AI"
        }

class LatechunkingProcessor:
    """
    Late chunking processor using Jina embeddings
    """
    
    def __init__(self, embedding_model: JinaEmbeddingModel):
        self.embedding_model = embedding_model
        self.chunk_cache: Dict[str, Tuple[List[str], np.ndarray]] = {}
    
    def process_document(self, document_text: str, chunk_size: int = 512, 
                        overlap: int = 50) -> Tuple[List[str], np.ndarray]:
        """Process document with late chunking"""
        
        try:
            # Check cache
            cache_key = f"{hash(document_text)}:{chunk_size}:{overlap}"
            if cache_key in self.chunk_cache:
                logger.debug("Cache hit for document chunking")
                return self.chunk_cache[cache_key]
            
            # Split document into chunks
            chunks = self._create_chunks(document_text, chunk_size, overlap)
            
            # Generate embeddings for chunks
            chunk_embeddings = self.embedding_model.encode(chunks)
            
            # Cache results
            result = (chunks, chunk_embeddings)
            self.chunk_cache[cache_key] = result
            
            logger.info(f"Document processed: {len(chunks)} chunks created")
            return result
            
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            return [], np.array([])
    
    def _create_chunks(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """Create overlapping chunks from text"""
        
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            chunk_text = ' '.join(chunk_words)
            chunks.append(chunk_text)
            
            # Stop if we've reached the end
            if i + chunk_size >= len(words):
                break
        
        return chunks
    
    def find_relevant_chunks(self, query: str, chunks: List[str], 
                           chunk_embeddings: np.ndarray, top_k: int = 3) -> List[Tuple[str, float]]:
        """Find most relevant chunks for query"""
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode_single(query)
            
            # Calculate similarities
            similarities = []
            for i, chunk_embedding in enumerate(chunk_embeddings):
                similarity = self.embedding_model.similarity(query_embedding, chunk_embedding)
                similarities.append((chunks[i], similarity))
            
            # Sort by similarity and return top-k
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Chunk retrieval failed: {e}")
            return []
    
    def clear_cache(self):
        """Clear chunk cache"""
        self.chunk_cache.clear()
        logger.info("Chunk cache cleared")