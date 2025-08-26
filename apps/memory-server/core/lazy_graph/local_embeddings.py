"""
Local Embeddings Implementation
No external dependencies, no downloads, pure local computation
"""

import numpy as np
import hashlib
from typing import List, Union
from sklearn.feature_extraction.text import TfidfVectorizer
import logging

logger = logging.getLogger(__name__)

class LocalEmbeddingModel:
    """
    Local embedding model that doesn't require any downloads
    Uses TF-IDF for semantic similarity without external models
    """
    
    def __init__(self, dimension: int = 768):
        self.dimension = dimension
        self.vectorizer = TfidfVectorizer(
            max_features=dimension,
            ngram_range=(1, 2),
            stop_words='english'
        )
        self.is_fitted = False
        self.vocabulary = []
        
    def encode(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        Generate embeddings for texts using local computation
        No external API calls or model downloads
        """
        if isinstance(texts, str):
            texts = [texts]
        
        try:
            # If vectorizer is not fitted yet, fit it with the input
            if not self.is_fitted:
                # Initialize with basic vocabulary
                initial_texts = texts + [
                    "document", "code", "function", "data", "memory", "server",
                    "activity", "file", "system", "user", "development", "debug"
                ]
                self.vectorizer.fit(initial_texts)
                self.is_fitted = True
                logger.info("Local embedding model initialized")
            
            # Transform texts to TF-IDF vectors
            if len(texts) == 0:
                return np.zeros((0, self.dimension))
            
            # Get TF-IDF vectors
            tfidf_vectors = self.vectorizer.transform(texts).toarray()
            
            # Pad or truncate to match desired dimension
            current_dim = tfidf_vectors.shape[1]
            
            if current_dim < self.dimension:
                # Pad with zeros if needed
                padding = np.zeros((len(texts), self.dimension - current_dim))
                embeddings = np.hstack([tfidf_vectors, padding])
            elif current_dim > self.dimension:
                # Truncate if needed
                embeddings = tfidf_vectors[:, :self.dimension]
            else:
                embeddings = tfidf_vectors
            
            # Normalize vectors
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1  # Avoid division by zero
            embeddings = embeddings / norms
            
            return embeddings.astype(np.float32)
            
        except Exception as e:
            logger.error(f"Error generating local embeddings: {e}")
            # Fallback to hash-based embeddings
            return self._hash_embeddings(texts)
    
    def _hash_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Fallback: Generate deterministic embeddings using hashing
        """
        embeddings = []
        
        for text in texts:
            # Create deterministic hash
            text_hash = hashlib.sha256(text.encode()).hexdigest()
            
            # Convert hash to vector
            np.random.seed(int(text_hash[:8], 16))
            embedding = np.random.randn(self.dimension)
            
            # Normalize
            embedding = embedding / np.linalg.norm(embedding)
            embeddings.append(embedding)
        
        return np.array(embeddings, dtype=np.float32)
    
    def get_sentence_embedding_dimension(self) -> int:
        """Get embedding dimension"""
        return self.dimension

class FastLocalEmbeddings:
    """
    Ultra-fast local embeddings using simple hashing
    No dependencies, instant startup
    """
    
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        logger.info(f"Fast local embeddings initialized (dim={dimension})")
    
    def encode(self, texts: Union[str, List[str]]) -> np.ndarray:
        """Generate embeddings using fast hashing"""
        if isinstance(texts, str):
            texts = [texts]
        
        embeddings = []
        for text in texts:
            # Simple but deterministic embedding
            words = text.lower().split()
            
            # Initialize embedding
            embedding = np.zeros(self.dimension)
            
            # Add word contributions
            for i, word in enumerate(words):
                # Hash word to get indices
                word_hash = int(hashlib.md5(word.encode()).hexdigest()[:8], 16)
                
                # Update embedding positions
                for j in range(min(10, self.dimension)):  # Use first 10 positions per word
                    idx = (word_hash + j) % self.dimension
                    # Use word position and hash for value
                    value = 1.0 / (1.0 + i) * ((word_hash >> j) & 1) * 2 - 1
                    embedding[idx] += value
            
            # Normalize
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            
            embeddings.append(embedding)
        
        return np.array(embeddings, dtype=np.float32)
    
    def get_sentence_embedding_dimension(self) -> int:
        """Get embedding dimension"""
        return self.dimension