#!/usr/bin/env python3
"""
Basic Functionality Tests for Memory-Server
Tests core components without external dependencies
"""

import sys
import traceback
import tempfile
from pathlib import Path

def test_configuration():
    """Test configuration system"""
    print("🔧 Testing Configuration System...")
    
    try:
        from core.config import MemoryServerConfig, get_config
        
        # Test default configuration
        config = MemoryServerConfig()
        assert config.API_PORT == 8001
        assert config.EMBEDDING_MODEL == "jinaai/jina-embeddings-v2-base-en"
        assert config.MAX_CONTEXT_LENGTH == 8192
        print("  ✅ Default configuration created")
        
        # Test path creation
        assert config.DATA_DIR.exists()
        assert config.MODELS_DIR.exists()
        assert config.CACHE_DIR.exists()
        print("  ✅ Directories created successfully")
        
        # Test global config
        global_config = get_config()
        assert isinstance(global_config, MemoryServerConfig)
        print("  ✅ Global configuration accessible")
        
        # Test model path generation
        embedding_path = config.get_model_path("embedding")
        assert embedding_path.parent == config.MODELS_DIR
        print("  ✅ Model path generation works")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Configuration test failed: {e}")
        traceback.print_exc()
        return False


def test_logging():
    """Test logging system"""
    print("📝 Testing Logging System...")
    
    try:
        from core.logging_config import get_logger, get_performance_logger
        
        # Test basic logger
        logger = get_logger("test")
        logger.info("Test log message")
        print("  ✅ Basic logger works")
        
        # Test performance logger
        perf_logger = get_performance_logger("test")
        perf_logger.log_timing("test_operation", 0.1)
        print("  ✅ Performance logger works")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Logging test failed: {e}")
        return False


def test_document_class():
    """Test Document class"""
    print("📄 Testing Document Class...")
    
    try:
        from core.lazy_graph import Document
        
        # Test basic creation
        doc = Document(
            id="test_doc",
            content="This is a test document.",
            metadata={"source": "test"}
        )
        
        assert doc.id == "test_doc"
        assert doc.content_hash is not None
        assert doc.created_at is not None
        print("  ✅ Document creation works")
        
        # Test serialization
        doc_dict = doc.to_dict()
        restored_doc = Document.from_dict(doc_dict)
        assert restored_doc.id == doc.id
        assert restored_doc.content == doc.content
        print("  ✅ Document serialization works")
        
        # Test hash generation
        doc2 = Document(id="doc2", content="This is a test document.")
        assert doc.content_hash == doc2.content_hash  # Same content
        
        doc3 = Document(id="doc3", content="Different content")
        assert doc.content_hash != doc3.content_hash  # Different content
        print("  ✅ Content hash generation works")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Document test failed: {e}")
        traceback.print_exc()
        return False


def test_chunk_class():
    """Test Chunk class"""
    print("📦 Testing Chunk Class...")
    
    try:
        import numpy as np
        from core.late_chunking import Chunk
        
        # Test chunk creation
        embedding = np.random.rand(768)
        chunk = Chunk(
            content="Test chunk content",
            start_idx=0,
            end_idx=18,
            embedding=embedding
        )
        
        assert chunk.content == "Test chunk content"
        assert chunk.chunk_id is not None
        assert chunk.confidence == 1.0
        print("  ✅ Chunk creation works")
        
        # Test serialization
        chunk_dict = chunk.to_dict()
        assert "chunk_id" in chunk_dict
        assert "content" in chunk_dict
        assert "embedding_shape" in chunk_dict
        print("  ✅ Chunk serialization works")
        
        # Test context window
        full_text = "This is the beginning. Test chunk content. This is the end."
        context = chunk.get_context_window(full_text, window_size=10)
        assert "beginning" in context
        assert "end" in context
        print("  ✅ Context window extraction works")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Chunk test failed: {e}")
        traceback.print_exc()
        return False


def test_chunking_strategies():
    """Test chunking strategies"""
    print("🔄 Testing Chunking Strategies...")
    
    try:
        from core.late_chunking.chunking_strategies import (
            FixedSizeStrategy, 
            HybridStrategy
        )
        
        # Test fixed size strategy
        strategy = FixedSizeStrategy()
        text = "First sentence. Second sentence. Third sentence."
        
        import asyncio
        boundaries = asyncio.run(strategy.calculate_boundaries(text, chunk_size=20, overlap=0.2))
        
        assert len(boundaries) >= 1
        assert boundaries[0][0] == 0
        assert boundaries[-1][1] == len(text)
        print("  ✅ Fixed size strategy works")
        
        # Test hybrid strategy
        hybrid_strategy = HybridStrategy()
        boundaries = asyncio.run(hybrid_strategy.calculate_boundaries(text, chunk_size=20, overlap=0.2))
        
        assert len(boundaries) >= 1
        print("  ✅ Hybrid strategy works")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Chunking strategies test failed: {e}")
        traceback.print_exc()
        return False


def test_fusion_layer():
    """Test fusion layer (basic functionality)"""
    print("🔀 Testing Fusion Layer...")
    
    try:
        from core.hybrid_store.fusion_layer import FusionLayer, RetrievalResult
        
        # Test fusion layer creation
        fusion = FusionLayer()
        assert fusion.config is not None
        print("  ✅ Fusion layer creation works")
        
        # Test retrieval result
        result = RetrievalResult(
            id="test1",
            content="Test content",
            score=0.9,
            source="vector"
        )
        
        result_dict = result.to_dict()
        assert result_dict["id"] == "test1"
        assert result_dict["score"] == 0.9
        print("  ✅ Retrieval result works")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Fusion layer test failed: {e}")
        traceback.print_exc()
        return False


def test_api_imports():
    """Test API module imports"""
    print("🌐 Testing API Module Imports...")
    
    try:
        # Test main API app import
        from api.main import app, get_app_state
        assert app is not None
        print("  ✅ FastAPI app imports successfully")
        
        # Test app state
        state = get_app_state()
        assert isinstance(state, dict)
        assert "initialized" in state
        print("  ✅ App state accessible")
        
        return True
        
    except Exception as e:
        print(f"  ❌ API imports test failed: {e}")
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all basic functionality tests"""
    print("🧪 Starting Memory-Server Basic Functionality Tests\n" + "="*60)
    
    tests = [
        test_configuration,
        test_logging,
        test_document_class,
        test_chunk_class, 
        test_chunking_strategies,
        test_fusion_layer,
        test_api_imports
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ❌ Test {test.__name__} crashed: {e}")
            failed += 1
        print()
    
    print("="*60)
    print(f"📊 Test Results:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 All basic functionality tests PASSED!")
        return True
    else:
        print(f"\n⚠️  {failed} tests FAILED. Check the logs above.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)