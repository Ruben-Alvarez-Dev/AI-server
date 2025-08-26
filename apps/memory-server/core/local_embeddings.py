"""
Local Embeddings Fallback
Hash-based and TF-IDF embeddings that don't require model downloads
Used as fallback when Embedding Hub is unavailable
"""

import numpy as np
import hashlib
from typing import List, Dict, Any, Union
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
import re
from collections import Counter
import logging

from core.logging_config import get_logger

# Setup logger
logger = get_logger("local-embeddings")

class LocalEmbeddings:
    """
    Local embedding generation without requiring model downloads
    
    Uses combination of:
    1. Hash-based embeddings for consistency
    2. TF-IDF for semantic similarity
    3. SVD for dimensionality reduction
    """
    
    def __init__(self, dimensions: int = 768):
        self.dimensions = dimensions
        self.tfidf_vectorizer = None
        self.svd_reducer = None
        self.vocabulary = set()
        self.is_fitted = False
        
        logger.info(f"LocalEmbeddings initialized with {dimensions} dimensions")
    
    def fit(self, texts: List[str]):
        """Fit the TF-IDF vectorizer on a corpus of texts"""
        
        if not texts:
            logger.warning("No texts provided for fitting")
            return
        
        # Initialize TF-IDF vectorizer
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=10000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.95
        )
        
        # Fit TF-IDF
        try:
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
            
            # Fit SVD for dimensionality reduction
            target_components = min(self.dimensions, tfidf_matrix.shape[1], len(texts))
            self.svd_reducer = TruncatedSVD(
                n_components=target_components,
                random_state=42
            )
            
            self.svd_reducer.fit(tfidf_matrix)
            self.is_fitted = True
            
            logger.info(f"LocalEmbeddings fitted on {len(texts)} texts, {target_components} components")
            
        except Exception as e:
            logger.error(f"Error fitting local embeddings: {e}")
            self.is_fitted = False
    
    def embed(self, text: Union[str, List[str]]) -> Union[np.ndarray, List[np.ndarray]]:
        """Generate embeddings for text(s)"""
        
        if isinstance(text, str):
            return self._embed_single(text)
        else:
            return [self._embed_single(t) for t in text]
    
    def _embed_single(self, text: str) -> np.ndarray:
        """Generate embedding for a single text"""
        
        # Generate hash-based embedding for consistency
        hash_embedding = self._generate_hash_embedding(text)
        
        # Generate TF-IDF based embedding if fitted
        if self.is_fitted and self.tfidf_vectorizer is not None:
            tfidf_embedding = self._generate_tfidf_embedding(text)
            
            # Combine hash and TF-IDF embeddings
            combined = np.concatenate([hash_embedding, tfidf_embedding])
            
            # Ensure correct dimensions
            if len(combined) > self.dimensions:
                combined = combined[:self.dimensions]
            elif len(combined) < self.dimensions:
                # Pad with zeros
                padding = np.zeros(self.dimensions - len(combined))
                combined = np.concatenate([combined, padding])
            
            # Normalize
            combined = combined / np.linalg.norm(combined)
            
            return combined.astype(np.float32)
        else:
            return hash_embedding
    
    def _generate_hash_embedding(self, text: str) -> np.ndarray:
        """Generate consistent hash-based embedding"""
        
        # Use multiple hash functions for different parts of the embedding
        embedding_parts = []
        
        # Base hash
        base_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        
        # Create multiple hash seeds
        hash_seeds = [
            f"{base_hash}_0",
            f"{base_hash}_1", 
            f"{base_hash}_2",
            f"{base_hash}_3"
        ]
        
        part_size = self.dimensions // 4
        
        for seed in hash_seeds:
            # Convert hash to integers and normalize
            seed_hash = hashlib.sha256(seed.encode()).hexdigest()
            
            # Take chunks of hex and convert to floats
            part = []
            for i in range(0, min(len(seed_hash), part_size * 2), 2):
                hex_chunk = seed_hash[i:i+2]
                # Convert to float in range [-1, 1]
                float_val = (int(hex_chunk, 16) / 255.0) * 2 - 1
                part.append(float_val)
            
            # Pad or trim to exact size
            while len(part) < part_size:
                part.append(0.0)
            part = part[:part_size]
            
            embedding_parts.extend(part)
        
        # Ensure exact dimensions
        embedding = np.array(embedding_parts[:self.dimensions])
        
        # Add content-based variations
        embedding = self._add_content_features(text, embedding)
        
        # Normalize
        embedding = embedding / np.linalg.norm(embedding)
        
        return embedding.astype(np.float32)
    
    def _generate_tfidf_embedding(self, text: str) -> np.ndarray:
        """Generate TF-IDF based embedding"""
        
        try:
            # Transform text to TF-IDF
            tfidf_vector = self.tfidf_vectorizer.transform([text])
            
            # Reduce dimensionality
            reduced_vector = self.svd_reducer.transform(tfidf_vector)
            
            # Flatten and return
            return reduced_vector.flatten()
            
        except Exception as e:
            logger.warning(f"Error generating TF-IDF embedding: {e}")
            # Return zero vector as fallback
            return np.zeros(self.svd_reducer.n_components if self.svd_reducer else 100)
    
    def _add_content_features(self, text: str, base_embedding: np.ndarray) -> np.ndarray:
        """Add content-specific features to base embedding"""
        
        embedding = base_embedding.copy()
        text_lower = text.lower()
        
        # Feature indices for different content types
        code_indices = slice(0, 50)
        conversation_indices = slice(50, 100) 
        query_indices = slice(100, 150)
        visual_indices = slice(150, 200)
        chunking_indices = slice(200, 250)
        community_indices = slice(250, 300)
        
        # Code content features
        if any(kw in text for kw in ['def ', 'function', 'class ', 'import ', '{']):
            embedding[code_indices] *= 1.3
        
        # Conversation features  
        if any(kw in text_lower for kw in ['user:', 'assistant:', 'human:', 'ai:']):
            embedding[conversation_indices] *= 1.3
        
        # Query features
        if text.strip().endswith('?') or any(kw in text_lower for kw in ['how', 'what', 'why']):
            embedding[query_indices] *= 1.3
        
        # Visual content features
        if any(kw in text_lower for kw in ['image', 'screenshot', 'visual', 'ui']):
            embedding[visual_indices] *= 1.3
        
        # Document/chunking features
        if len(text) > 1000 or 'paragraph' in text_lower or 'section' in text_lower:
            embedding[chunking_indices] *= 1.3
        
        # Community/graph features
        if '[ENTITY:' in text or 'relationship' in text_lower or 'community' in text_lower:
            embedding[community_indices] *= 1.3
        
        return embedding
    
    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between embeddings"""
        
        # Ensure embeddings are normalized
        emb1_norm = embedding1 / np.linalg.norm(embedding1)
        emb2_norm = embedding2 / np.linalg.norm(embedding2)
        
        # Calculate cosine similarity
        similarity = np.dot(emb1_norm, emb2_norm)
        
        return float(similarity)
    
    def get_info(self) -> Dict[str, Any]:
        """Get information about the local embeddings"""
        
        return {
            "type": "local_embeddings",
            "dimensions": self.dimensions,
            "is_fitted": self.is_fitted,
            "has_tfidf": self.tfidf_vectorizer is not None,
            "has_svd": self.svd_reducer is not None,
            "vocabulary_size": len(self.vocabulary) if self.vocabulary else 0
        }

class HashBasedEmbeddings:
    """
    Simple hash-based embeddings for extreme minimal setup
    Used when even TF-IDF is not available
    """
    
    def __init__(self, dimensions: int = 768):
        self.dimensions = dimensions
        logger.info(f"HashBasedEmbeddings initialized with {dimensions} dimensions")
    
    def embed(self, text: Union[str, List[str]]) -> Union[np.ndarray, List[np.ndarray]]:
        """Generate hash-based embeddings"""
        
        if isinstance(text, str):
            return self._embed_single(text)
        else:
            return [self._embed_single(t) for t in text]
    
    def _embed_single(self, text: str) -> np.ndarray:
        """Generate single hash-based embedding"""
        
        # Multiple hash functions for different embedding segments
        hashes = [
            hashlib.md5(text.encode()).hexdigest(),
            hashlib.sha1(text.encode()).hexdigest(),
            hashlib.sha256(text.encode()).hexdigest()[:32],  # Truncate SHA256
        ]
        
        embedding = []
        segment_size = self.dimensions // len(hashes)
        
        for hash_str in hashes:
            segment = []
            for i in range(0, len(hash_str), 2):
                hex_pair = hash_str[i:i+2]
                # Convert to float in range [-1, 1]
                float_val = (int(hex_pair, 16) / 255.0) * 2 - 1
                segment.append(float_val)
            
            # Pad or trim to segment size
            while len(segment) < segment_size:
                segment.append(0.0)
            segment = segment[:segment_size]
            
            embedding.extend(segment)
        
        # Ensure exact dimensions
        embedding = embedding[:self.dimensions]
        while len(embedding) < self.dimensions:
            embedding.append(0.0)
        
        embedding = np.array(embedding, dtype=np.float32)
        
        # Normalize
        embedding = embedding / np.linalg.norm(embedding)
        
        return embedding
    
    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity"""
        return float(np.dot(embedding1, embedding2))

# Singleton instances
_local_embeddings = None
_hash_embeddings = None

def get_local_embeddings(dimensions: int = 768) -> LocalEmbeddings:
    """Get singleton local embeddings instance"""
    global _local_embeddings
    
    if _local_embeddings is None:
        _local_embeddings = LocalEmbeddings(dimensions)
    
    return _local_embeddings

def get_hash_embeddings(dimensions: int = 768) -> HashBasedEmbeddings:
    """Get singleton hash embeddings instance"""
    global _hash_embeddings
    
    if _hash_embeddings is None:
        _hash_embeddings = HashBasedEmbeddings(dimensions)
    
    return _hash_embeddings