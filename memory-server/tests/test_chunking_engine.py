"""
Test Late Chunking Engine
"""

import pytest
import numpy as np
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from core.late_chunking import LateChunkingEngine, Chunk
from core.late_chunking.chunking_strategies import (
    FixedSizeStrategy, 
    SemanticStrategy, 
    HybridStrategy
)


class TestChunk:
    """Test Chunk class"""
    
    def test_chunk_creation(self):
        """Test basic chunk creation"""
        embedding = np.random.rand(768)
        
        chunk = Chunk(
            content="This is a test chunk.",
            start_idx=0,
            end_idx=22,
            embedding=embedding,
            metadata={"source": "test"}
        )
        
        assert chunk.content == "This is a test chunk."
        assert chunk.start_idx == 0
        assert chunk.end_idx == 22
        assert chunk.chunk_id is not None
        assert chunk.confidence == 1.0
        assert np.array_equal(chunk.embedding, embedding)
    
    def test_chunk_id_generation(self):
        """Test unique chunk ID generation"""
        embedding = np.random.rand(768)
        
        chunk1 = Chunk("Same content", 0, 12, embedding)
        chunk2 = Chunk("Same content", 0, 12, embedding)
        chunk3 = Chunk("Different content", 0, 17, embedding)
        
        # Same content at same position should have same ID
        assert chunk1.chunk_id == chunk2.chunk_id
        # Different content should have different ID
        assert chunk1.chunk_id != chunk3.chunk_id
    
    def test_chunk_serialization(self):
        """Test chunk to dictionary conversion"""
        embedding = np.random.rand(768)
        
        chunk = Chunk(
            content="Test content",
            start_idx=5,
            end_idx=17,
            embedding=embedding,
            metadata={"key": "value"}
        )
        
        chunk_dict = chunk.to_dict()
        
        assert isinstance(chunk_dict, dict)
        assert chunk_dict["content"] == "Test content"
        assert chunk_dict["start_idx"] == 5
        assert chunk_dict["end_idx"] == 17
        assert chunk_dict["embedding_shape"] == (768,)
    
    def test_context_window(self):
        """Test context window extraction"""
        full_content = "This is the beginning. This is a test chunk. This is the end."
        embedding = np.random.rand(768)
        
        chunk = Chunk(
            content="This is a test chunk.",
            start_idx=23,
            end_idx=44,
            embedding=embedding
        )
        
        context = chunk.get_context_window(full_content, window_size=10)
        assert "beginning" in context
        assert "end" in context


class TestChunkingStrategies:
    """Test different chunking strategies"""
    
    def test_fixed_size_strategy(self):
        """Test fixed size chunking strategy"""
        strategy = FixedSizeStrategy(respect_sentences=True)
        
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        boundaries = asyncio.run(strategy.calculate_boundaries(text, chunk_size=30, overlap=0.2))
        
        assert len(boundaries) >= 1
        assert all(isinstance(b, tuple) and len(b) == 2 for b in boundaries)
        assert boundaries[0][0] == 0  # Should start at beginning
        assert boundaries[-1][1] == len(text)  # Should end at text end
    
    def test_semantic_strategy_without_model(self):
        """Test semantic strategy without embedding model"""
        strategy = SemanticStrategy(embedding_model=None)
        
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        boundaries = asyncio.run(strategy.calculate_boundaries(text, chunk_size=25, overlap=0.1))
        
        assert len(boundaries) >= 1
        assert boundaries[0][0] == 0
        assert boundaries[-1][1] == len(text)
    
    @patch('core.late_chunking.chunking_strategies.nltk')
    def test_semantic_strategy_sentence_splitting(self, mock_nltk):
        """Test semantic strategy sentence splitting"""
        # Mock NLTK
        mock_nltk.data.find.side_effect = LookupError()
        mock_nltk.download.return_value = None
        
        strategy = SemanticStrategy()
        
        # Test _split_sentences method
        text = "First sentence. Second sentence! Third sentence?"
        sentences = strategy._split_sentences(text)
        
        assert len(sentences) >= 1
        assert all(isinstance(s, str) for s in sentences)
    
    def test_hybrid_strategy(self):
        """Test hybrid chunking strategy"""
        strategy = HybridStrategy(embedding_model=None)
        
        # Short text should use fixed strategy
        short_text = "Short text."
        boundaries = asyncio.run(strategy.calculate_boundaries(short_text, chunk_size=100, overlap=0.1))
        
        assert len(boundaries) == 1
        assert boundaries[0] == (0, len(short_text))
        
        # Long text should use recursive strategy
        long_text = "A" * 1000 + "\n\n" + "B" * 1000
        boundaries = asyncio.run(strategy.calculate_boundaries(long_text, chunk_size=500, overlap=0.1))
        
        assert len(boundaries) >= 2


class TestLateChunkingEngine:
    """Test Late Chunking Engine"""
    
    @pytest.fixture
    def mock_embedding_model(self):
        """Create mock embedding model"""
        mock_model = Mock()
        mock_model.encode.return_value = np.random.rand(1, 768)
        # Mock max_seq_length attribute
        mock_model.__getitem__ = Mock(return_value=Mock(max_seq_length=512))
        return mock_model
    
    @pytest.fixture
    def sample_texts(self):
        """Sample texts for testing"""
        return [
            "Short text for testing.",
            """This is a longer document that should be chunked into multiple pieces. 
            It contains several sentences and should test the chunking algorithm properly. 
            The late chunking approach should preserve context across these chunks.""",
            """Very long document. """ * 1000  # Long document
        ]
    
    @pytest.mark.asyncio
    async def test_engine_initialization(self, mock_embedding_model):
        """Test engine initialization"""
        engine = LateChunkingEngine(embedding_model=mock_embedding_model)
        await engine.initialize()
        
        assert engine.embedding_model is mock_embedding_model
        assert engine.boundary_detector is not None
        assert engine.chunking_strategy is not None
        assert engine.max_context_length > 0
    
    @pytest.mark.asyncio
    async def test_small_document_processing(self, mock_embedding_model, sample_texts):
        """Test processing small documents without chunking"""
        engine = LateChunkingEngine(embedding_model=mock_embedding_model)
        await engine.initialize()
        
        chunks = await engine.process_document(
            content=sample_texts[0],
            chunk_size=100
        )
        
        assert len(chunks) == 1
        assert chunks[0].content == sample_texts[0]
        assert chunks[0].start_idx == 0
        assert chunks[0].end_idx == len(sample_texts[0])
        assert chunks[0].metadata['processing_method'] == 'no_chunking'
    
    @pytest.mark.asyncio
    async def test_late_chunking_process(self, mock_embedding_model, sample_texts):
        """Test late chunking process"""
        engine = LateChunkingEngine(embedding_model=mock_embedding_model)
        await engine.initialize()
        
        chunks = await engine.process_document(
            content=sample_texts[1],
            chunk_size=50,
            preserve_context=True
        )
        
        assert len(chunks) >= 2
        assert all(isinstance(chunk, Chunk) for chunk in chunks)
        assert all(chunk.embedding is not None for chunk in chunks)
        assert all(chunk.confidence > 0 for chunk in chunks)
    
    @pytest.mark.asyncio
    async def test_traditional_chunking_fallback(self, mock_embedding_model, sample_texts):
        """Test fallback to traditional chunking"""
        engine = LateChunkingEngine(embedding_model=mock_embedding_model)
        await engine.initialize()
        
        chunks = await engine.process_document(
            content=sample_texts[1],
            chunk_size=50,
            preserve_context=False  # Force traditional chunking
        )
        
        assert len(chunks) >= 2
        assert all(isinstance(chunk, Chunk) for chunk in chunks)
        # Traditional chunking should have lower confidence
        assert all(chunk.confidence <= 0.7 for chunk in chunks)
        assert all(chunk.metadata['processing_method'] == 'traditional_chunking' for chunk in chunks)
    
    @pytest.mark.asyncio
    async def test_segment_splitting(self, mock_embedding_model):
        """Test splitting content into segments"""
        engine = LateChunkingEngine(embedding_model=mock_embedding_model)
        engine.max_context_length = 100  # Set small limit for testing
        
        long_text = "A" * 250  # 250 characters
        segments = engine._split_into_segments(long_text)
        
        assert len(segments) >= 3  # Should split into multiple segments
        assert all(len(seg) <= engine.max_context_length for seg in segments)
        assert "".join(segments) == long_text  # Should reconstruct original
    
    @pytest.mark.asyncio
    async def test_error_handling(self, mock_embedding_model):
        """Test error handling in various scenarios"""
        engine = LateChunkingEngine(embedding_model=mock_embedding_model)
        await engine.initialize()
        
        # Test with empty content
        chunks = await engine.process_document("")
        assert len(chunks) == 0
        
        # Test with None content (should handle gracefully)
        with pytest.raises(AttributeError):
            await engine.process_document(None)
        
        # Test with very long content
        very_long = "A" * 100000
        chunks = await engine.process_document(very_long, chunk_size=1000)
        assert len(chunks) > 0
    
    @pytest.mark.asyncio
    async def test_statistics_tracking(self, mock_embedding_model, sample_texts):
        """Test statistics tracking"""
        engine = LateChunkingEngine(embedding_model=mock_embedding_model)
        await engine.initialize()
        
        # Process multiple documents
        for text in sample_texts[:2]:
            await engine.process_document(text, chunk_size=50)
        
        stats = engine.get_statistics()
        
        assert stats['documents_processed'] == 2
        assert stats['chunks_created'] > 0
        assert stats['total_processing_time'] > 0
        assert stats['avg_processing_time'] >= 0
        assert stats['context_preservation_enabled'] == True
    
    @pytest.mark.asyncio
    async def test_boundary_calculation(self, mock_embedding_model):
        """Test chunk boundary calculation"""
        engine = LateChunkingEngine(embedding_model=mock_embedding_model)
        await engine.initialize()
        
        text = "First sentence. Second sentence. Third sentence."
        boundaries = await engine._calculate_chunk_boundaries(
            text, chunk_size=20, overlap=0.2, strategy=FixedSizeStrategy()
        )
        
        assert len(boundaries) >= 2
        assert all(isinstance(b, tuple) and len(b) == 2 for b in boundaries)
        
        # Check overlap
        for i in range(len(boundaries) - 1):
            current_end = boundaries[i][1]
            next_start = boundaries[i + 1][0]
            assert next_start <= current_end  # Should have overlap


if __name__ == "__main__":
    pytest.main([__file__, "-v"])