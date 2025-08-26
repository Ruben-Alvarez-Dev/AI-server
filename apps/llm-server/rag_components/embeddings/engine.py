"""
Embeddings Engine using Sentence Transformers
Optimized for M1 Ultra with batch processing
"""

import asyncio
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Union, Tuple
import torch
from sentence_transformers import SentenceTransformer
import time

logger = logging.getLogger(__name__)

class EmbeddingsEngine:
    """
    High-performance embeddings engine using Sentence Transformers
    Optimized for M1 Ultra with MPS acceleration
    """
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        device: str = "auto",
        batch_size: int = 32,
        max_seq_length: int = 512
    ):
        self.model_name = model_name
        self.batch_size = batch_size
        self.max_seq_length = max_seq_length
        
        # Device selection for M1 Ultra
        if device == "auto":
            if torch.backends.mps.is_available():
                self.device = "mps"  # M1 Ultra Metal Performance Shaders
                logger.info("Using M1 Ultra MPS acceleration for embeddings")
            elif torch.cuda.is_available():
                self.device = "cuda"
                logger.info("Using CUDA acceleration for embeddings")
            else:
                self.device = "cpu"
                logger.info("Using CPU for embeddings")
        else:
            self.device = device
        
        # Load model
        self.model = None
        self.dimension = None
        self._load_model()
        
        # Performance tracking
        self.embedding_stats = {
            'total_embeddings': 0,
            'total_time': 0.0,
            'avg_time_per_embedding': 0.0,
            'batch_count': 0
        }
        
        logger.info(f"EmbeddingsEngine initialized: {model_name} on {self.device}, dim={self.dimension}")
    
    def _load_model(self):
        """Load sentence transformer model"""
        
        try:
            self.model = SentenceTransformer(self.model_name, device=self.device)
            self.model.max_seq_length = self.max_seq_length
            
            # Get embedding dimension
            test_embedding = self.model.encode(["test"], show_progress_bar=False)
            self.dimension = test_embedding.shape[1]
            
            logger.info(f"Loaded embeddings model: {self.model_name}, dimension: {self.dimension}")
            
        except Exception as e:
            logger.error(f"Failed to load embeddings model {self.model_name}: {e}")
            # Fallback to a smaller model
            try:
                self.model_name = "all-MiniLM-L12-v2"
                self.model = SentenceTransformer(self.model_name, device=self.device)
                test_embedding = self.model.encode(["test"], show_progress_bar=False)
                self.dimension = test_embedding.shape[1]
                logger.info(f"Fallback model loaded: {self.model_name}")
            except Exception as e2:
                logger.error(f"Fallback model also failed: {e2}")
                raise
    
    async def embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for single text"""
        
        if not text or not text.strip():
            return np.zeros(self.dimension, dtype=np.float32)
        
        start_time = time.time()
        
        # Generate embedding
        try:
            embedding = self.model.encode(
                text,
                convert_to_numpy=True,
                show_progress_bar=False,
                batch_size=1
            )
            
            # Update stats
            self.embedding_stats['total_embeddings'] += 1
            self.embedding_stats['total_time'] += time.time() - start_time
            self.embedding_stats['avg_time_per_embedding'] = (
                self.embedding_stats['total_time'] / self.embedding_stats['total_embeddings']
            )
            
            return embedding.astype(np.float32)
            
        except Exception as e:
            logger.error(f"Failed to generate embedding for text: {e}")
            return np.zeros(self.dimension, dtype=np.float32)
    
    async def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for multiple texts (batch processing)"""
        
        if not texts:
            return np.array([], dtype=np.float32).reshape(0, self.dimension)
        
        # Filter empty texts
        valid_texts = [text if text and text.strip() else " " for text in texts]
        
        start_time = time.time()
        
        try:
            # Generate embeddings in batches
            all_embeddings = []
            
            for i in range(0, len(valid_texts), self.batch_size):
                batch_texts = valid_texts[i:i + self.batch_size]
                
                batch_embeddings = self.model.encode(
                    batch_texts,
                    convert_to_numpy=True,
                    show_progress_bar=len(valid_texts) > 100,
                    batch_size=self.batch_size
                )
                
                all_embeddings.append(batch_embeddings)
            
            # Combine batches
            embeddings = np.vstack(all_embeddings) if all_embeddings else np.array([])
            
            # Update stats
            self.embedding_stats['total_embeddings'] += len(texts)
            self.embedding_stats['batch_count'] += 1
            self.embedding_stats['total_time'] += time.time() - start_time
            self.embedding_stats['avg_time_per_embedding'] = (
                self.embedding_stats['total_time'] / self.embedding_stats['total_embeddings']
            )
            
            logger.debug(f"Generated {len(texts)} embeddings in {time.time() - start_time:.2f}s")
            
            return embeddings.astype(np.float32)
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings for {len(texts)} texts: {e}")
            return np.zeros((len(texts), self.dimension), dtype=np.float32)
    
    async def embed_documents(self, documents: List[Dict[str, Any]]) -> np.ndarray:
        """Generate embeddings for documents with content field"""
        
        texts = []
        for doc in documents:
            content = doc.get('content', '')
            title = doc.get('title', '')
            
            # Combine title and content for better embeddings
            if title and content:
                text = f"{title}\n{content}"
            elif title:
                text = title
            elif content:
                text = content
            else:
                text = " "  # Fallback for empty documents
            
            texts.append(text)
        
        return await self.embed_texts(texts)
    
    async def compute_similarity(
        self, 
        embedding1: np.ndarray, 
        embedding2: np.ndarray
    ) -> float:
        """Compute cosine similarity between two embeddings"""
        
        try:
            # Normalize embeddings
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            # Cosine similarity
            similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
            
            # Clip to valid range
            similarity = np.clip(similarity, -1.0, 1.0)
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Failed to compute similarity: {e}")
            return 0.0
    
    async def find_similar_texts(
        self, 
        query_text: str, 
        candidate_texts: List[str], 
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """Find most similar texts to query"""
        
        if not candidate_texts:
            return []
        
        # Generate embeddings
        query_embedding = await self.embed_text(query_text)
        candidate_embeddings = await self.embed_texts(candidate_texts)
        
        # Calculate similarities
        similarities = []
        for i, candidate_embedding in enumerate(candidate_embeddings):
            similarity = await self.compute_similarity(query_embedding, candidate_embedding)
            similarities.append((candidate_texts[i], similarity))
        
        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    async def cluster_texts(
        self, 
        texts: List[str], 
        num_clusters: int = 5
    ) -> List[List[int]]:
        """Cluster texts based on semantic similarity"""
        
        if len(texts) <= num_clusters:
            return [[i] for i in range(len(texts))]
        
        try:
            from sklearn.cluster import KMeans
            
            # Generate embeddings
            embeddings = await self.embed_texts(texts)
            
            # Perform clustering
            kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(embeddings)
            
            # Group texts by cluster
            clusters = [[] for _ in range(num_clusters)]
            for i, label in enumerate(cluster_labels):
                clusters[label].append(i)
            
            return clusters
            
        except ImportError:
            logger.warning("scikit-learn not available for clustering")
            # Simple fallback clustering
            return [list(range(len(texts)))]
        except Exception as e:
            logger.error(f"Clustering failed: {e}")
            return [list(range(len(texts)))]
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the embeddings model"""
        
        return {
            'model_name': self.model_name,
            'dimension': self.dimension,
            'device': self.device,
            'max_seq_length': self.max_seq_length,
            'batch_size': self.batch_size,
            'performance_stats': self.embedding_stats
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get performance statistics"""
        
        stats = self.embedding_stats.copy()
        
        if stats['total_embeddings'] > 0:
            stats['embeddings_per_second'] = stats['total_embeddings'] / stats['total_time'] if stats['total_time'] > 0 else 0
        else:
            stats['embeddings_per_second'] = 0
        
        return {
            'model_info': self.get_model_info(),
            'performance': stats
        }
    
    async def reset_statistics(self):
        """Reset performance statistics"""
        
        self.embedding_stats = {
            'total_embeddings': 0,
            'total_time': 0.0,
            'avg_time_per_embedding': 0.0,
            'batch_count': 0
        }
        
        logger.info("Embeddings statistics reset")
    
    async def warm_up(self):
        """Warm up the model with a test embedding"""
        
        logger.info("Warming up embeddings model...")
        
        test_texts = [
            "This is a test sentence for model warm-up.",
            "Another test sentence to initialize the model properly.",
            "Final warm-up text to ensure optimal performance."
        ]
        
        await self.embed_texts(test_texts)
        await self.reset_statistics()  # Don't count warm-up in stats
        
        logger.info("Embeddings model warmed up successfully")

# Export
__all__ = ['EmbeddingsEngine']