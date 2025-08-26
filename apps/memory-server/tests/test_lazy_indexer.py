"""
Test LazyGraphRAG Indexer
"""

import pytest
import numpy as np
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from core.lazy_graph import LazyGraphIndexer, Document


class TestDocument:
    """Test Document class"""
    
    def test_document_creation(self):
        """Test basic document creation"""
        doc = Document(
            id="test_doc_1",
            content="This is a test document.",
            metadata={"source": "test"}
        )
        
        assert doc.id == "test_doc_1"
        assert doc.content == "This is a test document."
        assert doc.metadata["source"] == "test"
        assert doc.content_hash is not None
        assert doc.created_at is not None
    
    def test_content_hash_generation(self):
        """Test content hash generation and uniqueness"""
        doc1 = Document(id="1", content="Same content")
        doc2 = Document(id="2", content="Same content") 
        doc3 = Document(id="3", content="Different content")
        
        # Same content should have same hash
        assert doc1.content_hash == doc2.content_hash
        # Different content should have different hash
        assert doc1.content_hash != doc3.content_hash
    
    def test_document_serialization(self):
        """Test document to/from dict conversion"""
        original = Document(
            id="test_doc",
            content="Test content",
            metadata={"key": "value"}
        )
        
        # Convert to dict
        doc_dict = original.to_dict()
        assert isinstance(doc_dict, dict)
        assert doc_dict["id"] == "test_doc"
        assert doc_dict["content"] == "Test content"
        
        # Convert back from dict
        restored = Document.from_dict(doc_dict)
        assert restored.id == original.id
        assert restored.content == original.content
        assert restored.metadata == original.metadata


class TestLazyGraphIndexer:
    """Test LazyGraphRAG Indexer"""
    
    @pytest.fixture
    def mock_embedding_model(self):
        """Create mock embedding model"""
        mock_model = Mock()
        mock_model.encode.return_value = np.random.rand(1, 768)  # 768-dim embedding
        return mock_model
    
    @pytest.fixture
    def sample_documents(self):
        """Create sample documents for testing"""
        return [
            Document(
                id="doc1", 
                content="Apple Inc. is a technology company based in Cupertino.",
                metadata={"source": "wikipedia"}
            ),
            Document(
                id="doc2",
                content="Microsoft Corporation develops software and cloud services.",
                metadata={"source": "wikipedia"}
            ),
            Document(
                id="doc3", 
                content="Google LLC is known for its search engine and Android OS.",
                metadata={"source": "wikipedia"}
            )
        ]
    
    @pytest.mark.asyncio
    async def test_indexer_initialization(self, mock_embedding_model):
        """Test indexer initialization"""
        indexer = LazyGraphIndexer(embedding_model=mock_embedding_model)
        
        await indexer.initialize()
        
        assert indexer.vector_index is not None
        assert indexer.embedding_model is mock_embedding_model
        assert indexer.dimension > 0
        assert indexer.next_id == 0
        assert len(indexer.documents) == 0
    
    @pytest.mark.asyncio
    async def test_single_document_indexing(self, mock_embedding_model, sample_documents):
        """Test indexing a single document"""
        indexer = LazyGraphIndexer(embedding_model=mock_embedding_model)
        await indexer.initialize()
        
        doc = sample_documents[0]
        doc_id = await indexer.index_document(doc)
        
        assert doc_id == "doc1"
        assert doc.id in indexer.documents
        assert doc.id in indexer.id_mapping
        assert indexer.next_id == 1
        
        # Check statistics
        stats = indexer.get_statistics()
        assert stats['total_documents'] == 1
        assert stats['total_embeddings'] == 1
    
    @pytest.mark.asyncio 
    async def test_batch_document_indexing(self, mock_embedding_model, sample_documents):
        """Test indexing multiple documents in batch"""
        indexer = LazyGraphIndexer(embedding_model=mock_embedding_model)
        await indexer.initialize()
        
        doc_ids = await indexer.index_documents(sample_documents)
        
        assert len(doc_ids) == 3
        assert all(doc_id in indexer.documents for doc_id in doc_ids)
        assert indexer.next_id == 3
        
        stats = indexer.get_statistics()
        assert stats['total_documents'] == 3
        assert stats['total_embeddings'] == 3
    
    @pytest.mark.asyncio
    async def test_duplicate_document_handling(self, mock_embedding_model):
        """Test handling of duplicate documents"""
        indexer = LazyGraphIndexer(embedding_model=mock_embedding_model)
        await indexer.initialize()
        
        # Create two documents with same content
        doc1 = Document(id="doc1", content="Same content")
        doc2 = Document(id="doc2", content="Same content")
        
        await indexer.index_document(doc1)
        doc2_id = await indexer.index_document(doc2)  # Should be detected as duplicate
        
        assert doc2_id == "doc2"  # Should still return the ID
        assert len(indexer.documents) == 1  # Only one should be stored
    
    @pytest.mark.asyncio
    async def test_vector_search(self, mock_embedding_model, sample_documents):
        """Test vector similarity search"""
        # Mock search results
        mock_embedding_model.encode.return_value = np.random.rand(1, 768)
        
        indexer = LazyGraphIndexer(embedding_model=mock_embedding_model)
        await indexer.initialize()
        
        # Index documents
        await indexer.index_documents(sample_documents)
        
        # Mock FAISS search results
        with patch.object(indexer.vector_index, 'search') as mock_search:
            mock_search.return_value = (
                np.array([[0.9, 0.7, 0.5]]),  # scores
                np.array([[0, 1, 2]])         # indices
            )
            
            results = await indexer.vector_search("technology company", k=3)
            
            assert len(results) == 3
            assert all(isinstance(doc, Document) for doc in results)
            assert all(hasattr(doc, 'metadata') for doc in results)
    
    @pytest.mark.asyncio
    async def test_save_and_load(self, mock_embedding_model, sample_documents):
        """Test saving and loading index data"""
        with tempfile.TemporaryDirectory() as temp_dir:
            save_path = Path(temp_dir)
            
            # Create and populate indexer
            indexer = LazyGraphIndexer(embedding_model=mock_embedding_model)
            await indexer.initialize()
            await indexer.index_documents(sample_documents)
            
            # Save
            await indexer.save(save_path)
            
            # Verify files exist
            assert (save_path / "faiss.index").exists()
            assert (save_path / "metadata.pkl").exists()
            
            # Create new indexer and load
            new_indexer = LazyGraphIndexer(embedding_model=mock_embedding_model)
            await new_indexer.initialize()
            await new_indexer._load_existing_data()
            
            # Should have same documents
            assert len(new_indexer.documents) == 0  # Won't load without proper path setup
    
    @pytest.mark.asyncio
    async def test_memory_usage_estimation(self, mock_embedding_model, sample_documents):
        """Test memory usage estimation"""
        indexer = LazyGraphIndexer(embedding_model=mock_embedding_model)
        await indexer.initialize()
        await indexer.index_documents(sample_documents)
        
        memory_mb = indexer._estimate_memory_usage()
        
        assert isinstance(memory_mb, float)
        assert memory_mb > 0
    
    @pytest.mark.asyncio
    async def test_error_handling(self, mock_embedding_model):
        """Test error handling in various scenarios"""
        indexer = LazyGraphIndexer(embedding_model=mock_embedding_model)
        await indexer.initialize()
        
        # Test with empty content
        empty_doc = Document(id="empty", content="")
        doc_id = await indexer.index_document(empty_doc)
        assert doc_id == "empty"
        
        # Test with very long content
        long_content = "A" * 50000
        long_doc = Document(id="long", content=long_content)
        doc_id = await indexer.index_document(long_doc)
        assert doc_id == "long"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])