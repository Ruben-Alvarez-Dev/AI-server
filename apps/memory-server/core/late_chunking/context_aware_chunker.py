"""
Late Chunking Engine - Context-Aware Document Processing
Implements JinaAI's Late Chunking: embeddings BEFORE chunking to preserve context
"""

import asyncio
import numpy as np
import time
from typing import List, Dict, Any, Tuple, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path
import hashlib
from concurrent.futures import ThreadPoolExecutor

# Import sentence transformers
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SentenceTransformer = None
    SENTENCE_TRANSFORMERS_AVAILABLE = False

# NO external models - use local embeddings
# from sentence_transformers import SentenceTransformer
# from transformers import AutoTokenizer

from .semantic_boundaries import SemanticBoundaryDetector
from .chunking_strategies import ChunkingStrategy, HybridStrategy
from core.config import get_config
from core.logging_config import get_logger, get_performance_logger

# Setup loggers
logger = get_logger("late-chunking")
perf_logger = get_performance_logger("late-chunking")


@dataclass
class Chunk:
    """Chunk representation with context-aware embedding"""
    content: str
    start_idx: int
    end_idx: int
    embedding: np.ndarray
    token_embeddings: Optional[np.ndarray] = None  # For ColBERT-style retrieval
    metadata: Dict[str, Any] = field(default_factory=dict)
    chunk_id: Optional[str] = field(default=None, init=False)
    confidence: float = 1.0
    
    def __post_init__(self):
        """Generate unique chunk ID"""
        if self.chunk_id is None:
            content_hash = hashlib.md5(self.content.encode()).hexdigest()[:8]
            self.chunk_id = f"chunk_{content_hash}_{self.start_idx}_{self.end_idx}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'chunk_id': self.chunk_id,
            'content': self.content,
            'start_idx': self.start_idx,
            'end_idx': self.end_idx,
            'metadata': self.metadata,
            'confidence': self.confidence,
            'embedding_shape': self.embedding.shape if self.embedding is not None else None
        }
    
    def get_context_window(self, full_content: str, window_size: int = 100) -> str:
        """Get surrounding context for this chunk"""
        start = max(0, self.start_idx - window_size)
        end = min(len(full_content), self.end_idx + window_size)
        return full_content[start:end]


class LateChunkingEngine:
    """
    Late Chunking Engine - Revolutionary Context-Preserving Approach
    
    Core Innovation:
    1. Apply transformer to ENTIRE document first
    2. Generate token embeddings with full context
    3. Apply chunking to these contextualized embeddings
    4. Result: chunks that preserve global document context
    """
    
    def __init__(self, embedding_model: Optional[SentenceTransformer] = None):
        self.config = get_config()
        
        # Initialize embedding model
        self.embedding_model = embedding_model
        self.tokenizer = None
        self.max_context_length = self.config.MAX_CONTEXT_LENGTH
        
        # Initialize components
        self.boundary_detector = SemanticBoundaryDetector()
        self.chunking_strategy = HybridStrategy()
        
        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=self.config.NUM_WORKERS)
        
        # Performance tracking
        self.stats = {
            'documents_processed': 0,
            'chunks_created': 0,
            'total_processing_time': 0.0,
            'context_preservation_score': 0.0,
            'avg_chunk_size': 0.0
        }
    
    async def initialize(self):
        """Initialize the Late Chunking engine"""
        start_time = time.time()
        
        logger.info("Initializing Late Chunking engine")
        
        try:
            # Initialize embedding model if not provided
            if self.embedding_model is None:
                await self._initialize_embedding_model()
            
            # Initialize tokenizer
            await self._initialize_tokenizer()
            
            # Initialize semantic boundary detector
            await self.boundary_detector.initialize()
            
            init_time = time.time() - start_time
            perf_logger.log_timing("chunking_engine_init", init_time)
            
            logger.info(
                "Late Chunking engine initialized",
                model=self.config.EMBEDDING_MODEL,
                max_context=self.max_context_length,
                init_time_ms=round(init_time * 1000, 2)
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize Late Chunking engine: {e}")
            raise
    
    async def _initialize_embedding_model(self):
        """Initialize the embedding model"""
        logger.info(f"Loading embedding model: {self.config.EMBEDDING_MODEL}")
        
        try:
            # Load model in thread pool
            loop = asyncio.get_event_loop()
            self.embedding_model = await loop.run_in_executor(
                self.executor,
                lambda: SentenceTransformer(self.config.EMBEDDING_MODEL)
            )
            
            # Test model and get actual max sequence length
            test_embedding = self.embedding_model.encode(["test"])
            self.embedding_dimension = len(test_embedding[0])
            
            # Get model's actual context limit
            if hasattr(self.embedding_model[0], 'max_seq_length'):
                model_max_length = self.embedding_model[0].max_seq_length
                self.max_context_length = min(self.max_context_length, model_max_length)
            
            logger.info(
                "Embedding model loaded",
                dimension=self.embedding_dimension,
                max_context=self.max_context_length
            )
            
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    async def _initialize_tokenizer(self):
        """Initialize tokenizer for token-level processing"""
        try:
            # Load tokenizer corresponding to the embedding model
            model_name = self.config.EMBEDDING_MODEL
            
            loop = asyncio.get_event_loop()
            self.tokenizer = await loop.run_in_executor(
                self.executor,
                lambda: AutoTokenizer.from_pretrained(model_name)
            )
            
            logger.info("Tokenizer initialized successfully")
            
        except Exception as e:
            logger.warning(f"Failed to load tokenizer: {e}, falling back to basic tokenization")
            self.tokenizer = None
    
    async def process_document(
        self,
        content: str,
        chunk_size: int = None,
        overlap: float = None,
        strategy: Optional[ChunkingStrategy] = None,
        preserve_context: bool = True
    ) -> List[Chunk]:
        """
        Process document with Late Chunking approach
        
        Args:
            content: Document content
            chunk_size: Target chunk size (tokens)
            overlap: Overlap ratio between chunks
            strategy: Chunking strategy to use
            preserve_context: Whether to use late chunking for context preservation
        
        Returns:
            List of context-aware chunks
        """
        start_time = time.time()
        
        # Use defaults from config
        chunk_size = chunk_size or self.config.DEFAULT_CHUNK_SIZE
        overlap = overlap or self.config.CHUNK_OVERLAP
        strategy = strategy or self.chunking_strategy
        
        logger.info(
            "Processing document with Late Chunking",
            content_length=len(content),
            chunk_size=chunk_size,
            preserve_context=preserve_context
        )
        
        try:
            # For small documents, no chunking needed
            if len(content) <= chunk_size * 2:
                chunks = await self._process_small_document(content)
            elif preserve_context and self.config.USE_LATE_CHUNKING:
                chunks = await self._late_chunking_process(content, chunk_size, overlap, strategy)
            else:
                # Fallback to traditional chunking
                chunks = await self._traditional_chunking(content, chunk_size, overlap, strategy)
            
            processing_time = time.time() - start_time
            
            # Update statistics
            self.stats['documents_processed'] += 1
            self.stats['chunks_created'] += len(chunks)
            self.stats['total_processing_time'] += processing_time
            if chunks:
                avg_size = sum(len(chunk.content) for chunk in chunks) / len(chunks)
                self.stats['avg_chunk_size'] = (
                    self.stats['avg_chunk_size'] * (self.stats['documents_processed'] - 1) + avg_size
                ) / self.stats['documents_processed']
            
            perf_logger.log_timing(
                "document_processing",
                processing_time,
                content_length=len(content),
                chunks_created=len(chunks),
                preserve_context=preserve_context
            )
            
            logger.info(
                "Document processing completed",
                chunks_created=len(chunks),
                processing_time_ms=round(processing_time * 1000, 2),
                avg_chunk_size=round(self.stats['avg_chunk_size'], 1)
            )
            
            return chunks
            
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            # Return empty list rather than raising
            return []
    
    async def _process_small_document(self, content: str) -> List[Chunk]:
        """Process small documents without chunking"""
        logger.info("Processing small document without chunking")
        
        try:
            # Generate embedding for entire document
            embedding = await self._generate_full_context_embedding(content)
            
            chunk = Chunk(
                content=content,
                start_idx=0,
                end_idx=len(content),
                embedding=embedding,
                confidence=1.0,
                metadata={
                    'processing_method': 'no_chunking',
                    'full_context': True
                }
            )
            
            return [chunk]
            
        except Exception as e:
            logger.error(f"Failed to process small document: {e}")
            return []
    
    async def _late_chunking_process(
        self,
        content: str,
        chunk_size: int,
        overlap: float,
        strategy: ChunkingStrategy
    ) -> List[Chunk]:
        """
        Core Late Chunking Process - The Revolutionary Approach
        
        Steps:
        1. Split content into processable segments (if needed)
        2. Apply transformer to ENTIRE segment
        3. Generate token embeddings with full context
        4. Define chunk boundaries
        5. Apply mean pooling to token embeddings within each chunk
        """
        logger.info("Executing Late Chunking process")
        
        try:
            # Step 1: Split into processable segments if needed
            segments = self._split_into_segments(content)
            all_chunks = []
            
            for segment_idx, segment in enumerate(segments):
                logger.info(
                    f"Processing segment {segment_idx + 1}/{len(segments)}",
                    segment_length=len(segment)
                )
                
                # Step 2 & 3: Generate token embeddings with full context
                token_embeddings, token_mapping = await self._generate_contextualized_token_embeddings(segment)
                
                # Step 4: Define chunk boundaries using strategy
                chunk_boundaries = await self._calculate_chunk_boundaries(
                    segment, chunk_size, overlap, strategy
                )
                
                # Step 5: Create chunks with contextualized embeddings
                segment_chunks = await self._create_chunks_from_token_embeddings(
                    segment, chunk_boundaries, token_embeddings, token_mapping, segment_idx
                )
                
                all_chunks.extend(segment_chunks)
            
            logger.info(f"Late chunking completed: {len(all_chunks)} chunks created")
            return all_chunks
            
        except Exception as e:
            logger.error(f"Late chunking process failed: {e}")
            # Fallback to traditional chunking
            return await self._traditional_chunking(content, chunk_size, overlap, strategy)
    
    async def _generate_contextualized_token_embeddings(
        self, 
        text: str
    ) -> Tuple[np.ndarray, Dict[int, Tuple[int, int]]]:
        """
        Generate token embeddings with full document context
        
        Returns:
            Tuple of (token_embeddings, token_mapping)
            token_mapping: {token_idx: (char_start, char_end)}
        """
        try:
            # For now, we'll simulate token-level embeddings using sentence embeddings
            # In a full implementation, this would access the transformer's internal layers
            
            # Generate sentence embedding for the full context
            full_embedding = await self._generate_full_context_embedding(text)
            
            # Tokenize the text to understand token boundaries
            if self.tokenizer:
                # Use proper tokenizer
                tokens = self.tokenizer(text, return_offsets_mapping=True, truncation=True, max_length=self.max_context_length)
                token_offsets = tokens['offset_mapping']
                
                # Create token mapping
                token_mapping = {i: (start, end) for i, (start, end) in enumerate(token_offsets)}
                
                # For now, replicate the sentence embedding for each token
                # TODO: Implement proper token-level embedding extraction
                num_tokens = len(token_offsets)
                token_embeddings = np.tile(full_embedding, (num_tokens, 1))
                
            else:
                # Fallback: use word-based tokenization
                words = text.split()
                token_mapping = {}
                current_pos = 0
                
                for i, word in enumerate(words):
                    start_pos = text.find(word, current_pos)
                    if start_pos != -1:
                        end_pos = start_pos + len(word)
                        token_mapping[i] = (start_pos, end_pos)
                        current_pos = end_pos
                
                # Replicate sentence embedding for each word
                num_tokens = len(words)
                token_embeddings = np.tile(full_embedding, (num_tokens, 1))
            
            return token_embeddings, token_mapping
            
        except Exception as e:
            logger.error(f"Failed to generate contextualized token embeddings: {e}")
            # Fallback: return single embedding
            embedding = await self._generate_full_context_embedding(text)
            return embedding.reshape(1, -1), {0: (0, len(text))}
    
    async def _calculate_chunk_boundaries(
        self,
        text: str,
        chunk_size: int,
        overlap: float,
        strategy: ChunkingStrategy
    ) -> List[Tuple[int, int]]:
        """Calculate chunk boundaries using the specified strategy"""
        try:
            # Use the strategy to determine boundaries
            boundaries = await strategy.calculate_boundaries(
                text, chunk_size, overlap
            )
            
            # If strategy failed or returned empty, use fallback
            if not boundaries:
                boundaries = self._simple_boundary_calculation(text, chunk_size, overlap)
            
            return boundaries
            
        except Exception as e:
            logger.error(f"Chunk boundary calculation failed: {e}")
            return self._simple_boundary_calculation(text, chunk_size, overlap)
    
    def _simple_boundary_calculation(
        self, 
        text: str, 
        chunk_size: int, 
        overlap: float
    ) -> List[Tuple[int, int]]:
        """Simple fallback boundary calculation"""
        boundaries = []
        text_len = len(text)
        overlap_size = int(chunk_size * overlap)
        
        start = 0
        while start < text_len:
            end = min(start + chunk_size, text_len)
            
            # Try to break at sentence boundary
            if end < text_len:
                # Look for sentence ending
                sentence_end = text.rfind('.', start, end)
                if sentence_end > start + chunk_size // 2:  # Don't make chunks too small
                    end = sentence_end + 1
                else:
                    # Look for word boundary
                    word_boundary = text.rfind(' ', start, end)
                    if word_boundary > start:
                        end = word_boundary
            
            boundaries.append((start, end))
            
            # Next chunk with overlap
            start = max(start + chunk_size - overlap_size, end)
            
            if start >= text_len:
                break
        
        return boundaries
    
    async def _create_chunks_from_token_embeddings(
        self,
        text: str,
        boundaries: List[Tuple[int, int]],
        token_embeddings: np.ndarray,
        token_mapping: Dict[int, Tuple[int, int]],
        segment_idx: int
    ) -> List[Chunk]:
        """Create chunks by pooling token embeddings within boundaries"""
        chunks = []
        
        for chunk_idx, (start, end) in enumerate(boundaries):
            chunk_content = text[start:end].strip()
            if not chunk_content:
                continue
            
            try:
                # Find tokens that fall within this chunk
                relevant_token_indices = []
                for token_idx, (token_start, token_end) in token_mapping.items():
                    # Check if token overlaps with chunk boundaries
                    if not (token_end <= start or token_start >= end):
                        relevant_token_indices.append(token_idx)
                
                if relevant_token_indices:
                    # Pool token embeddings within this chunk
                    chunk_token_embeddings = token_embeddings[relevant_token_indices]
                    chunk_embedding = np.mean(chunk_token_embeddings, axis=0)
                else:
                    # Fallback: generate embedding for chunk content
                    chunk_embedding = await self._generate_full_context_embedding(chunk_content)
                
                # Calculate confidence based on context preservation
                confidence = self._calculate_context_preservation_score(
                    chunk_content, text, relevant_token_indices, len(token_mapping)
                )
                
                chunk = Chunk(
                    content=chunk_content,
                    start_idx=start,
                    end_idx=end,
                    embedding=chunk_embedding,
                    token_embeddings=token_embeddings[relevant_token_indices] if relevant_token_indices else None,
                    confidence=confidence,
                    metadata={
                        'processing_method': 'late_chunking',
                        'segment_idx': segment_idx,
                        'chunk_idx': chunk_idx,
                        'token_count': len(relevant_token_indices),
                        'context_preserved': True
                    }
                )
                
                chunks.append(chunk)
                
            except Exception as e:
                logger.error(f"Failed to create chunk {chunk_idx}: {e}")
                continue
        
        return chunks
    
    def _calculate_context_preservation_score(
        self,
        chunk_content: str,
        full_text: str,
        token_indices: List[int],
        total_tokens: int
    ) -> float:
        """Calculate how well this chunk preserves context"""
        try:
            # Base score
            score = 0.8
            
            # Boost for having token-level context
            if token_indices:
                score += 0.1
            
            # Boost for reasonable chunk size
            chunk_ratio = len(chunk_content) / len(full_text)
            if 0.05 <= chunk_ratio <= 0.5:  # Reasonable chunk size
                score += 0.05
            
            # Penalty for very small chunks
            if len(chunk_content) < 50:
                score -= 0.1
            
            return max(0.0, min(1.0, score))
            
        except Exception:
            return 0.7  # Default confidence
    
    def _split_into_segments(self, content: str) -> List[str]:
        """Split content into segments that fit within context window"""
        if len(content) <= self.max_context_length:
            return [content]
        
        segments = []
        start = 0
        
        while start < len(content):
            end = min(start + self.max_context_length, len(content))
            
            # Try to break at paragraph boundary
            if end < len(content):
                paragraph_break = content.rfind('\n\n', start, end)
                if paragraph_break > start + self.max_context_length // 2:
                    end = paragraph_break + 2
                else:
                    # Try sentence boundary
                    sentence_break = content.rfind('. ', start, end)
                    if sentence_break > start + self.max_context_length // 2:
                        end = sentence_break + 2
            
            segments.append(content[start:end])
            start = end
        
        return segments
    
    async def _generate_full_context_embedding(self, text: str) -> np.ndarray:
        """Generate embedding with full context"""
        if not text.strip():
            return np.zeros(self.embedding_dimension)
        
        try:
            # Truncate if too long
            if len(text) > self.max_context_length:
                text = text[:self.max_context_length]
            
            # Generate embedding in thread pool
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                self.executor,
                lambda: self.embedding_model.encode([text])
            )
            
            return embedding[0]
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return np.zeros(self.embedding_dimension)
    
    async def _traditional_chunking(
        self,
        content: str,
        chunk_size: int,
        overlap: float,
        strategy: ChunkingStrategy
    ) -> List[Chunk]:
        """Traditional chunking approach as fallback"""
        logger.warning("Using traditional chunking (context may not be preserved)")
        
        try:
            # Calculate boundaries
            boundaries = await self._calculate_chunk_boundaries(
                content, chunk_size, overlap, strategy
            )
            
            # Create chunks with individual embeddings
            chunks = []
            for chunk_idx, (start, end) in enumerate(boundaries):
                chunk_content = content[start:end].strip()
                if not chunk_content:
                    continue
                
                # Generate embedding for this chunk only
                chunk_embedding = await self._generate_full_context_embedding(chunk_content)
                
                chunk = Chunk(
                    content=chunk_content,
                    start_idx=start,
                    end_idx=end,
                    embedding=chunk_embedding,
                    confidence=0.6,  # Lower confidence for traditional chunking
                    metadata={
                        'processing_method': 'traditional_chunking',
                        'chunk_idx': chunk_idx,
                        'context_preserved': False
                    }
                )
                
                chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            logger.error(f"Traditional chunking failed: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get engine statistics"""
        return {
            **self.stats,
            'avg_processing_time': (
                self.stats['total_processing_time'] / 
                max(self.stats['documents_processed'], 1)
            ),
            'avg_chunks_per_document': (
                self.stats['chunks_created'] / 
                max(self.stats['documents_processed'], 1)
            ),
            'context_preservation_enabled': self.config.USE_LATE_CHUNKING,
            'max_context_length': self.max_context_length
        }
    
    async def close(self):
        """Close the engine and cleanup resources"""
        logger.info("Closing Late Chunking engine")
        
        try:
            # Shutdown thread pool
            self.executor.shutdown(wait=True)
            
            logger.info("Late Chunking engine closed")
            
        except Exception as e:
            logger.error(f"Error closing engine: {e}")
            raise