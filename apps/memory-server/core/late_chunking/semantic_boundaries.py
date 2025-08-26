"""
Semantic Boundary Detection for Late Chunking
Identifies optimal semantic boundaries for text chunking
"""

from typing import List, Tuple, Optional
import numpy as np
from abc import ABC, abstractmethod

from core.config import get_config
from core.logging_config import get_logger

logger = get_logger(__name__)

class BoundaryDetector(ABC):
    """Abstract base class for boundary detection"""
    
    @abstractmethod
    async def detect_boundaries(self, text: str, embeddings: np.ndarray, chunk_size: int) -> List[int]:
        """Detect semantic boundaries in text"""
        pass

class SemanticBoundaryDetector(BoundaryDetector):
    """Semantic boundary detector using embedding similarity"""
    
    def __init__(self, similarity_threshold: float = 0.7):
        self.config = get_config()
        self.similarity_threshold = similarity_threshold
    
    async def initialize(self):
        """Initialize the boundary detector"""
        logger.info("SemanticBoundaryDetector initialized")
        return True
        
    async def detect_boundaries(self, text: str, embeddings: np.ndarray, chunk_size: int) -> List[int]:
        """Detect boundaries based on semantic similarity drops"""
        if len(embeddings) == 0:
            return [0, len(text)]
            
        # Simple sentence-based boundaries for now
        boundaries = self._find_sentence_boundaries(text)
        
        # Filter boundaries to respect chunk size
        filtered_boundaries = [0]
        current_pos = 0
        
        for boundary in boundaries:
            if boundary - current_pos >= chunk_size:
                filtered_boundaries.append(boundary)
                current_pos = boundary
                
        # Ensure we end at text length
        if filtered_boundaries[-1] != len(text):
            filtered_boundaries.append(len(text))
            
        return filtered_boundaries
    
    def _find_sentence_boundaries(self, text: str) -> List[int]:
        """Find sentence boundaries in text"""
        import re
        
        # Simple sentence boundary detection
        sentences = re.split(r'[.!?]+', text)
        boundaries = []
        current_pos = 0
        
        for sentence in sentences:
            if sentence.strip():
                current_pos += len(sentence)
                # Find the actual end position including punctuation
                while current_pos < len(text) and text[current_pos] in '.!? \n\t':
                    current_pos += 1
                boundaries.append(min(current_pos, len(text)))
                
        return boundaries
    
    def _calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between embeddings"""
        dot_product = np.dot(embedding1, embedding2)
        norms = np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
        
        if norms == 0:
            return 0.0
            
        return dot_product / norms