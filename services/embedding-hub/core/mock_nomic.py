"""
Mock Nomic Multimodal 7B Model
Local implementation for testing without downloading actual models
Simulates Nomic embedding generation with realistic behavior
"""

import asyncio
import numpy as np
import hashlib
import time
import logging
from typing import Union, List, Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger("embedding-hub.mock-nomic")

@dataclass
class ModelConfig:
    """Configuration for mock Nomic model"""
    dimensions: int = 768
    max_sequence_length: int = 8192
    device: str = "mps"
    batch_size: int = 32

class MockNomicMultimodal:
    """
    Mock implementation of Nomic Multimodal 7B model
    
    Simulates realistic embedding generation behavior:
    - Consistent embeddings for same input (using hash-based seeding)
    - Realistic processing times
    - Proper error handling
    - Memory usage simulation
    """
    
    def __init__(self, dimensions: int = 768, device: str = "mps"):
        self.config = ModelConfig(dimensions=dimensions, device=device)
        self.is_initialized = False
        self.model_loaded = False
        
        # Simulation parameters
        self.base_processing_time_ms = 50  # Base processing time per request
        self.tokens_per_ms = 100  # Simulated processing speed
        
        logger.info(f"MockNomicMultimodal initialized - Dimensions: {dimensions}, Device: {device}")
    
    async def initialize(self):
        """Initialize the mock model (simulates model loading)"""
        
        logger.info("Loading Mock Nomic Multimodal 7B model...")
        
        # Simulate model loading time
        await asyncio.sleep(2.0)  # Simulate 2 second loading time
        
        self.is_initialized = True
        self.model_loaded = True
        
        logger.info(f"Mock model loaded successfully - {self.config.dimensions}D embeddings ready")
    
    async def embed(self, content: Union[str, List[str]], **kwargs) -> np.ndarray:
        """
        Generate embeddings for content
        
        Args:
            content: Text content or list of texts to embed
            **kwargs: Additional parameters (batch_size, etc.)
            
        Returns:
            numpy array of embeddings
        """
        
        if not self.is_initialized:
            raise RuntimeError("Model not initialized. Call initialize() first.")
        
        # Handle single string vs list
        if isinstance(content, str):
            content_list = [content]
            return_single = True
        else:
            content_list = content
            return_single = False
        
        # Generate embeddings for each item
        embeddings = []
        
        for text in content_list:
            # Simulate processing time based on content length
            await self._simulate_processing_time(text)
            
            # Generate consistent embedding based on content hash
            embedding = self._generate_deterministic_embedding(text)
            embeddings.append(embedding)
        
        embeddings_array = np.array(embeddings)
        
        if return_single:
            return embeddings_array[0]
        
        return embeddings_array
    
    def _generate_deterministic_embedding(self, text: str) -> np.ndarray:
        """Generate deterministic embedding based on text hash"""
        
        # Use SHA-256 hash for consistent seeding
        text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
        
        # Convert hash to integer seed
        seed = int(text_hash[:8], 16)
        
        # Generate embedding with this seed
        np.random.seed(seed % 2**32)  # Ensure seed fits in 32 bits
        
        # Generate random embedding
        embedding = np.random.normal(0, 1, self.config.dimensions)
        
        # Normalize to unit vector (common in embedding models)
        embedding = embedding / np.linalg.norm(embedding)
        
        # Add some content-based variations
        embedding = self._add_content_features(text, embedding)
        
        return embedding.astype(np.float32)
    
    def _add_content_features(self, text: str, base_embedding: np.ndarray) -> np.ndarray:
        """Add content-specific features to base embedding"""
        
        embedding = base_embedding.copy()
        text_lower = text.lower()
        
        # Add features based on content type
        if any(keyword in text_lower for keyword in ['function', 'class', 'def', 'import', 'var']):
            # Code content - emphasize certain dimensions
            embedding[:50] *= 1.2
            
        if any(keyword in text_lower for keyword in ['user:', 'assistant:', 'human:', 'ai:']):
            # Conversation content - emphasize other dimensions
            embedding[50:100] *= 1.2
            
        if any(keyword in text_lower for keyword in ['how', 'what', 'why', 'when', '?']):
            # Query content - emphasize question dimensions
            embedding[100:150] *= 1.2
            
        if '[VISUAL_CONTENT]' in text or '[IMAGE' in text:
            # Visual content - emphasize visual dimensions
            embedding[150:200] *= 1.2
            
        if '[CHUNKING_CONTEXT]' in text:
            # Late chunking content - emphasize structure dimensions
            embedding[200:250] *= 1.2
            
        if 'COMMUNITY_CONTEXT' in text or 'ENTITY:' in text:
            # Community detection content - emphasize relationship dimensions
            embedding[250:300] *= 1.2
        
        # Re-normalize after modifications
        embedding = embedding / np.linalg.norm(embedding)
        
        return embedding
    
    async def _simulate_processing_time(self, text: str):
        """Simulate realistic processing time based on content length"""
        
        # Calculate simulated processing time
        token_count = len(text.split())
        processing_time_ms = self.base_processing_time_ms + (token_count / self.tokens_per_ms)
        
        # Add some random variation (±20%)
        np.random.seed(int(time.time() * 1000) % 2**32)
        variation = np.random.uniform(0.8, 1.2)
        processing_time_ms *= variation
        
        # Convert to seconds and sleep
        processing_time_s = processing_time_ms / 1000
        await asyncio.sleep(min(processing_time_s, 0.5))  # Cap at 500ms for testing
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information and status"""
        
        return {
            "model_name": "nomic-embed-multimodal-7b-mock",
            "dimensions": self.config.dimensions,
            "max_sequence_length": self.config.max_sequence_length,
            "device": self.config.device,
            "is_initialized": self.is_initialized,
            "supports_multimodal": True,
            "memory_usage_gb": 7.0,  # Simulated memory usage
            "model_size_gb": 7.0
        }
    
    async def embed_batch(self, texts: List[str], batch_size: Optional[int] = None) -> np.ndarray:
        """
        Process texts in batches for efficient embedding generation
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size (uses model config if not specified)
            
        Returns:
            Array of embeddings for all texts
        """
        
        if batch_size is None:
            batch_size = self.config.batch_size
        
        all_embeddings = []
        
        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = await self.embed(batch)
            
            if batch_embeddings.ndim == 1:  # Single embedding
                all_embeddings.append(batch_embeddings)
            else:  # Multiple embeddings
                all_embeddings.extend(batch_embeddings)
        
        return np.array(all_embeddings)
    
    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between two embeddings"""
        
        # Ensure embeddings are normalized
        embedding1_norm = embedding1 / np.linalg.norm(embedding1)
        embedding2_norm = embedding2 / np.linalg.norm(embedding2)
        
        # Calculate cosine similarity
        similarity = np.dot(embedding1_norm, embedding2_norm)
        
        return float(similarity)
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the model"""
        
        try:
            # Test embedding generation
            test_embedding = await self.embed("health check test")
            
            return {
                "status": "healthy",
                "model_loaded": self.model_loaded,
                "test_embedding_shape": test_embedding.shape,
                "test_embedding_norm": float(np.linalg.norm(test_embedding)),
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "model_loaded": self.model_loaded,
                "timestamp": time.time()
            }
    
    def __repr__(self):
        return f"MockNomicMultimodal(dimensions={self.config.dimensions}, device='{self.config.device}', initialized={self.is_initialized})"