"""
Chunking Strategies for Late Chunking Engine
Different approaches to determine optimal chunk boundaries
"""

import asyncio
import re
from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from core.logging_config import get_logger

logger = get_logger("chunking-strategies")


class ChunkingStrategy(ABC):
    """Abstract base class for chunking strategies"""
    
    @abstractmethod
    async def calculate_boundaries(
        self, 
        text: str, 
        chunk_size: int, 
        overlap: float
    ) -> List[Tuple[int, int]]:
        """Calculate chunk boundaries for the given text"""
        pass
    
    def get_strategy_name(self) -> str:
        """Get the name of this strategy"""
        return self.__class__.__name__


class FixedSizeStrategy(ChunkingStrategy):
    """Simple fixed-size chunking with configurable overlap"""
    
    def __init__(self, respect_sentences: bool = True):
        self.respect_sentences = respect_sentences
    
    async def calculate_boundaries(
        self, 
        text: str, 
        chunk_size: int, 
        overlap: float
    ) -> List[Tuple[int, int]]:
        """Calculate boundaries using fixed size with optional sentence respect"""
        boundaries = []
        text_len = len(text)
        overlap_size = int(chunk_size * overlap)
        
        start = 0
        while start < text_len:
            end = min(start + chunk_size, text_len)
            
            # Try to respect sentence boundaries if enabled
            if self.respect_sentences and end < text_len:
                # Look for sentence ending within last 20% of chunk
                search_start = start + int(chunk_size * 0.8)
                sentence_end = text.rfind('.', search_start, end)
                
                if sentence_end > search_start:
                    end = sentence_end + 1
                else:
                    # Fall back to word boundary
                    word_boundary = text.rfind(' ', start + int(chunk_size * 0.8), end)
                    if word_boundary > start:
                        end = word_boundary
            
            boundaries.append((start, end))
            
            # Calculate next start with overlap
            start = max(start + chunk_size - overlap_size, end)
            
            if start >= text_len:
                break
        
        return boundaries


class SemanticStrategy(ChunkingStrategy):
    """Semantic chunking using sentence similarity"""
    
    def __init__(self, embedding_model=None, similarity_threshold: float = 0.7):
        self.embedding_model = embedding_model
        self.similarity_threshold = similarity_threshold
    
    async def calculate_boundaries(
        self, 
        text: str, 
        chunk_size: int, 
        overlap: float
    ) -> List[Tuple[int, int]]:
        """Calculate boundaries based on semantic similarity"""
        try:
            # Split into sentences
            sentences = self._split_sentences(text)
            if len(sentences) <= 2:
                return [(0, len(text))]
            
            # If no embedding model available, fall back to simple strategy
            if self.embedding_model is None:
                return await self._fallback_semantic_chunking(text, sentences, chunk_size, overlap)
            
            # Calculate sentence embeddings
            sentence_embeddings = await self._get_sentence_embeddings(sentences)
            
            # Find semantic boundaries
            boundaries = await self._find_semantic_boundaries(
                text, sentences, sentence_embeddings, chunk_size, overlap
            )
            
            return boundaries
            
        except Exception as e:
            logger.error(f"Semantic chunking failed: {e}")
            # Fallback to fixed size
            fallback = FixedSizeStrategy()
            return await fallback.calculate_boundaries(text, chunk_size, overlap)
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        try:
            import nltk
            from nltk.tokenize import sent_tokenize
            
            # Download punkt if needed
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                nltk.download('punkt', quiet=True)
            
            sentences = sent_tokenize(text)
            return [s.strip() for s in sentences if s.strip()]
            
        except ImportError:
            # Fallback to simple sentence splitting
            sentences = re.split(r'[.!?]+', text)
            return [s.strip() for s in sentences if s.strip()]
    
    async def _get_sentence_embeddings(self, sentences: List[str]) -> np.ndarray:
        """Get embeddings for sentences"""
        if self.embedding_model is None:
            raise ValueError("Embedding model not available")
        
        # Generate embeddings in batches for efficiency
        batch_size = 32
        embeddings = []
        
        for i in range(0, len(sentences), batch_size):
            batch = sentences[i:i + batch_size]
            batch_embeddings = self.embedding_model.encode(batch)
            embeddings.extend(batch_embeddings)
        
        return np.array(embeddings)
    
    async def _find_semantic_boundaries(
        self,
        text: str,
        sentences: List[str],
        embeddings: np.ndarray,
        chunk_size: int,
        overlap: float
    ) -> List[Tuple[int, int]]:
        """Find boundaries based on semantic similarity between sentences"""
        # Calculate similarity between consecutive sentences
        similarities = []
        for i in range(len(embeddings) - 1):
            sim = cosine_similarity(
                embeddings[i].reshape(1, -1),
                embeddings[i + 1].reshape(1, -1)
            )[0][0]
            similarities.append(sim)
        
        # Find semantic break points (low similarity)
        break_points = [0]  # Always start with 0
        
        for i, similarity in enumerate(similarities):
            if similarity < self.similarity_threshold:
                # Check if this creates a reasonable chunk size
                current_pos = self._sentence_to_char_position(i + 1, sentences, text)
                if current_pos - break_points[-1] > chunk_size // 2:
                    break_points.append(current_pos)
        
        # Add end position
        if break_points[-1] != len(text):
            break_points.append(len(text))
        
        # Convert break points to boundaries
        boundaries = []
        overlap_chars = int(chunk_size * overlap)
        
        for i in range(len(break_points) - 1):
            start = break_points[i]
            end = break_points[i + 1]
            
            # Add overlap to previous chunk if not first chunk
            if i > 0:
                start = max(0, start - overlap_chars)
            
            boundaries.append((start, end))
        
        return boundaries
    
    def _sentence_to_char_position(self, sentence_idx: int, sentences: List[str], text: str) -> int:
        """Convert sentence index to character position in text"""
        if sentence_idx >= len(sentences):
            return len(text)
        
        # Find the position by searching for the sentence
        search_pos = 0
        for i in range(sentence_idx):
            pos = text.find(sentences[i], search_pos)
            if pos != -1:
                search_pos = pos + len(sentences[i])
        
        return search_pos
    
    async def _fallback_semantic_chunking(
        self, 
        text: str, 
        sentences: List[str], 
        chunk_size: int, 
        overlap: float
    ) -> List[Tuple[int, int]]:
        """Fallback semantic chunking without embeddings"""
        logger.warning("Using fallback semantic chunking")
        
        # Use simple heuristics for semantic breaks
        boundaries = []
        current_start = 0
        current_pos = 0
        overlap_chars = int(chunk_size * overlap)
        
        for sentence in sentences:
            sentence_pos = text.find(sentence, current_pos)
            if sentence_pos == -1:
                continue
            
            sentence_end = sentence_pos + len(sentence)
            
            # Check if adding this sentence exceeds chunk size
            if sentence_end - current_start > chunk_size:
                # Create chunk up to previous sentence
                if current_pos > current_start:
                    boundaries.append((current_start, current_pos))
                    current_start = max(current_pos - overlap_chars, sentence_pos)
            
            current_pos = sentence_end
        
        # Add final chunk
        if current_pos > current_start:
            boundaries.append((current_start, len(text)))
        
        return boundaries


class RecursiveStrategy(ChunkingStrategy):
    """Recursive chunking that tries multiple separators"""
    
    def __init__(self, separators: List[str] = None):
        self.separators = separators or [
            "\n\n",  # Paragraphs
            "\n",    # Lines
            ". ",    # Sentences
            " ",     # Words
            ""       # Characters (last resort)
        ]
    
    async def calculate_boundaries(
        self, 
        text: str, 
        chunk_size: int, 
        overlap: float
    ) -> List[Tuple[int, int]]:
        """Recursively split using different separators"""
        chunks = await self._recursive_split(text, chunk_size)
        
        # Convert chunks to boundaries with overlap
        boundaries = []
        overlap_chars = int(chunk_size * overlap)
        
        current_pos = 0
        for chunk in chunks:
            start_pos = text.find(chunk, current_pos)
            if start_pos == -1:
                continue
            
            end_pos = start_pos + len(chunk)
            
            # Add overlap from previous chunk
            if boundaries:
                start_pos = max(0, start_pos - overlap_chars)
            
            boundaries.append((start_pos, end_pos))
            current_pos = end_pos
        
        return boundaries
    
    async def _recursive_split(self, text: str, chunk_size: int) -> List[str]:
        """Recursively split text using separators"""
        if len(text) <= chunk_size:
            return [text]
        
        # Try each separator
        for separator in self.separators:
            if separator in text:
                splits = text.split(separator)
                
                # Reconstruct with separator
                reconstructed_splits = []
                for i, split in enumerate(splits):
                    if i > 0 and separator != "":
                        reconstructed_splits.append(separator + split)
                    else:
                        reconstructed_splits.append(split)
                
                # Group splits into chunks
                chunks = []
                current_chunk = ""
                
                for split in reconstructed_splits:
                    # Check if adding this split exceeds chunk size
                    if len(current_chunk) + len(split) > chunk_size:
                        if current_chunk:
                            chunks.append(current_chunk)
                            current_chunk = split
                        else:
                            # Split is too large, need to split further
                            sub_chunks = await self._recursive_split(split, chunk_size)
                            chunks.extend(sub_chunks)
                    else:
                        current_chunk += split
                
                # Add final chunk
                if current_chunk:
                    chunks.append(current_chunk)
                
                return chunks
        
        # If no separators work, split by characters
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]


class HybridStrategy(ChunkingStrategy):
    """Hybrid strategy that combines multiple approaches"""
    
    def __init__(self, embedding_model=None):
        self.embedding_model = embedding_model
        self.semantic_strategy = SemanticStrategy(embedding_model)
        self.recursive_strategy = RecursiveStrategy()
        self.fixed_strategy = FixedSizeStrategy()
    
    async def calculate_boundaries(
        self, 
        text: str, 
        chunk_size: int, 
        overlap: float
    ) -> List[Tuple[int, int]]:
        """Use hybrid approach to find optimal boundaries"""
        try:
            # For short texts, use fixed strategy
            if len(text) < chunk_size * 3:
                return await self.fixed_strategy.calculate_boundaries(text, chunk_size, overlap)
            
            # For medium texts, try semantic strategy
            if len(text) < chunk_size * 10 and self.embedding_model is not None:
                semantic_boundaries = await self.semantic_strategy.calculate_boundaries(
                    text, chunk_size, overlap
                )
                
                # Validate semantic boundaries
                if self._validate_boundaries(semantic_boundaries, text, chunk_size):
                    return semantic_boundaries
            
            # For long texts or when semantic fails, use recursive
            recursive_boundaries = await self.recursive_strategy.calculate_boundaries(
                text, chunk_size, overlap
            )
            
            if self._validate_boundaries(recursive_boundaries, text, chunk_size):
                return recursive_boundaries
            
            # Final fallback to fixed strategy
            return await self.fixed_strategy.calculate_boundaries(text, chunk_size, overlap)
            
        except Exception as e:
            logger.error(f"Hybrid chunking failed: {e}")
            # Ultimate fallback
            return await self.fixed_strategy.calculate_boundaries(text, chunk_size, overlap)
    
    def _validate_boundaries(
        self, 
        boundaries: List[Tuple[int, int]], 
        text: str, 
        chunk_size: int
    ) -> bool:
        """Validate that boundaries are reasonable"""
        if not boundaries:
            return False
        
        # Check that boundaries cover the full text
        if boundaries[0][0] != 0 or boundaries[-1][1] != len(text):
            return False
        
        # Check chunk sizes are reasonable
        for start, end in boundaries:
            chunk_len = end - start
            if chunk_len < chunk_size * 0.3 or chunk_len > chunk_size * 2:
                return False
        
        # Check for overlaps/gaps
        for i in range(len(boundaries) - 1):
            current_end = boundaries[i][1]
            next_start = boundaries[i + 1][0]
            
            # Allow some overlap but not too much
            if next_start > current_end or current_end - next_start > chunk_size:
                return False
        
        return True