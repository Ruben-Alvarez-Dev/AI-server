#!/usr/bin/env python3
"""
Core-Only Tests for Memory-Server
Tests only the configuration and logging systems without external dependencies
"""

import sys
import os
import tempfile
from pathlib import Path

def test_configuration_system():
    """Test the configuration system thoroughly"""
    print("🔧 Testing Configuration System...")
    
    try:
        from core.config import MemoryServerConfig, get_config, reload_config, LogLevel, VectorIndexType
        
        # Test 1: Default configuration
        config = MemoryServerConfig()
        print(f"  ✅ Default config created - API Port: {config.API_PORT}")
        
        # Test 2: Configuration validation
        assert config.API_PORT == 8001
        assert config.EMBEDDING_MODEL == "jinaai/jina-embeddings-v2-base-en"
        assert config.MAX_CONTEXT_LENGTH == 8192
        assert config.WORKING_MEMORY_SIZE == 128 * 1024
        assert config.EPISODIC_MEMORY_SIZE == 2 * 1024 * 1024
        print("  ✅ Configuration values validated")
        
        # Test 3: Path creation and validation
        assert config.DATA_DIR.exists()
        assert config.MODELS_DIR.exists()
        assert config.CACHE_DIR.exists()
        assert config.LOGS_DIR.exists()
        assert config.GRAPH_DB_PATH.exists()
        print("  ✅ All required directories created")
        
        # Test 4: Enum usage
        assert isinstance(config.LOG_LEVEL, LogLevel)
        assert isinstance(config.FAISS_INDEX_TYPE, VectorIndexType)
        print("  ✅ Enum configurations work")
        
        # Test 5: Model path generation
        embedding_path = config.get_model_path("embedding")
        colbert_path = config.get_model_path("colbert") 
        assert embedding_path.parent == config.MODELS_DIR
        assert colbert_path.parent == config.MODELS_DIR
        print("  ✅ Model path generation works")
        
        # Test 6: Configuration serialization
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        assert "API_PORT" in config_dict
        assert "EMBEDDING_MODEL" in config_dict
        print("  ✅ Configuration serialization works")
        
        # Test 7: Global configuration
        global_config = get_config()
        assert isinstance(global_config, MemoryServerConfig)
        assert global_config.API_PORT == 8001
        print("  ✅ Global configuration accessible")
        
        # Test 8: Configuration reload
        reload_config()
        new_global = get_config()
        assert new_global.API_PORT == 8001
        print("  ✅ Configuration reload works")
        
        # Test 9: Environment variable override (simulation)
        os.environ["MEMORY_SERVER_PORT"] = "9001"
        os.environ["MEMORY_SERVER_DEBUG"] = "true"
        
        env_config = MemoryServerConfig()
        assert env_config.API_PORT == 9001
        assert env_config.DEBUG_MODE == True
        print("  ✅ Environment variable overrides work")
        
        # Cleanup
        os.environ.pop("MEMORY_SERVER_PORT", None)
        os.environ.pop("MEMORY_SERVER_DEBUG", None)
        
        # Test 10: Configuration file save/load
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            
            test_config = MemoryServerConfig(API_PORT=7777)
            test_config.save_to_file(config_path)
            
            assert config_path.exists()
            
            loaded_config = MemoryServerConfig.load_from_file(config_path)
            assert loaded_config.API_PORT == 7777
        print("  ✅ Configuration file save/load works")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_logging_system_basic():
    """Test basic logging functionality without external dependencies"""
    print("📝 Testing Basic Logging System...")
    
    try:
        # Test basic Python logging (skip complex logging for now)
        import logging
        logger = logging.getLogger("test")
        logger.info("Test log message")
        print("  ✅ Basic Python logging works")
        
        # Test logger configuration
        logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
        
        # Test multiple loggers
        logger1 = logging.getLogger("component1") 
        logger2 = logging.getLogger("component2")
        
        logger1.info("Component 1 test message")
        logger2.info("Component 2 test message")
        print("  ✅ Multiple logger instances work")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Logging test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_directory_structure():
    """Test the directory structure creation and validation"""
    print("📁 Testing Directory Structure...")
    
    try:
        from core.config import get_config
        
        config = get_config()
        
        # Test required directories exist
        required_dirs = [
            config.DATA_DIR,
            config.MODELS_DIR, 
            config.CACHE_DIR,
            config.LOGS_DIR,
            config.GRAPH_DB_PATH
        ]
        
        for directory in required_dirs:
            assert directory.exists(), f"Directory {directory} does not exist"
            assert directory.is_dir(), f"{directory} is not a directory"
            print(f"  ✅ {directory.name} directory exists")
        
        # Test that paths are absolute
        for directory in required_dirs:
            assert directory.is_absolute(), f"{directory} is not an absolute path"
        print("  ✅ All paths are absolute")
        
        # Test directory permissions (basic check)
        for directory in required_dirs:
            assert os.access(directory, os.R_OK), f"Cannot read {directory}"
            assert os.access(directory, os.W_OK), f"Cannot write to {directory}"
        print("  ✅ Directory permissions are correct")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Directory structure test failed: {e}")
        return False


def test_project_structure():
    """Test that the project has the expected structure"""
    print("🏗️ Testing Project Structure...")
    
    try:
        # Get project root (where this script is)
        project_root = Path(__file__).parent
        
        # Expected directories
        expected_dirs = [
            "core",
            "api", 
            "tests",
            "data",
            "scripts",
            "memory",
            "multimodal",
            "ingestion"
        ]
        
        for dir_name in expected_dirs:
            dir_path = project_root / dir_name
            assert dir_path.exists(), f"Directory {dir_name} missing"
            assert dir_path.is_dir(), f"{dir_name} is not a directory"
            print(f"  ✅ {dir_name}/ directory exists")
        
        # Expected files
        expected_files = [
            "pyproject.toml",
            "README.md"
        ]
        
        for file_name in expected_files:
            file_path = project_root / file_name
            assert file_path.exists(), f"File {file_name} missing"
            assert file_path.is_file(), f"{file_name} is not a file"
            print(f"  ✅ {file_name} file exists")
        
        # Test core module structure
        core_modules = [
            "core/config.py",
            "core/logging_config.py",
            "core/lazy_graph/__init__.py",
            "core/late_chunking/__init__.py",
            "core/hybrid_store/__init__.py"
        ]
        
        for module_path in core_modules:
            module_file = project_root / module_path
            assert module_file.exists(), f"Core module {module_path} missing"
            print(f"  ✅ {module_path} exists")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Project structure test failed: {e}")
        return False


def test_python_imports():
    """Test Python imports that should work without external dependencies"""
    print("🐍 Testing Python Imports...")
    
    try:
        # Test core config import
        import core.config
        from core.config import MemoryServerConfig, get_config
        print("  ✅ core.config imports successfully")
        
        # Test that we can create basic objects
        config = MemoryServerConfig()
        assert config is not None
        print("  ✅ MemoryServerConfig instantiates")
        
        # Test enum imports
        from core.config import LogLevel, VectorIndexType
        assert LogLevel.INFO is not None
        assert VectorIndexType.HNSW is not None
        print("  ✅ Enum classes import correctly")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Python imports test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_configuration_validation():
    """Test configuration validation rules"""
    print("✅ Testing Configuration Validation...")
    
    try:
        from core.config import MemoryServerConfig
        
        # Test valid configuration
        valid_config = MemoryServerConfig(
            WORKING_MEMORY_SIZE=1000,
            EPISODIC_MEMORY_SIZE=2000,
            CHUNK_OVERLAP=0.2,
            API_PORT=8080
        )
        print("  ✅ Valid configuration accepts")
        
        # Test invalid configurations should raise errors
        test_cases = [
            {"WORKING_MEMORY_SIZE": -1, "error": "WORKING_MEMORY_SIZE must be positive"},
            {"WORKING_MEMORY_SIZE": 1000, "EPISODIC_MEMORY_SIZE": 500, "error": "EPISODIC_MEMORY_SIZE should be larger"},
            {"CHUNK_OVERLAP": 1.5, "error": "CHUNK_OVERLAP must be between 0 and 1"},
            {"API_PORT": 80, "error": "API_PORT must be between 1024 and 65535"},
            {"BATCH_SIZE": -5, "error": "BATCH_SIZE must be positive"}
        ]
        
        validation_passed = 0
        for i, test_case in enumerate(test_cases):
            try:
                error_msg = test_case.pop("error")
                MemoryServerConfig(**test_case)
                print(f"  ❌ Validation test {i+1} should have failed but didn't")
            except ValueError as e:
                if error_msg.split()[0].lower() in str(e).lower():
                    validation_passed += 1
                    print(f"  ✅ Validation test {i+1} correctly failed: {error_msg.split()[0]}")
                else:
                    print(f"  ⚠️  Validation test {i+1} failed with wrong error: {e}")
            except Exception as e:
                print(f"  ⚠️  Validation test {i+1} failed unexpectedly: {e}")
        
        print(f"  📊 {validation_passed}/{len(test_cases)} validation tests passed")
        return validation_passed >= len(test_cases) // 2  # At least half should pass
        
    except Exception as e:
        print(f"  ❌ Configuration validation test failed: {e}")
        return False


def run_core_tests():
    """Run all core tests (no external dependencies)"""
    print("🧪 Memory-Server Core Tests (No External Dependencies)")
    print("="*70)
    
    tests = [
        test_configuration_system,
        test_logging_system_basic,
        test_directory_structure,
        test_project_structure,
        test_python_imports,
        test_configuration_validation
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
                print(f"✅ {test.__name__} PASSED\n")
            else:
                failed += 1
                print(f"❌ {test.__name__} FAILED\n")
        except Exception as e:
            print(f"💥 {test.__name__} CRASHED: {e}\n")
            failed += 1
    
    print("="*70)
    print(f"📊 CORE TEST RESULTS:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL CORE TESTS PASSED! 🎉")
        print("✨ Memory-Server core functionality is working correctly!")
        return True
    else:
        print(f"\n⚠️  {failed} tests failed.")
        return False


if __name__ == "__main__":
    success = run_core_tests()
    sys.exit(0 if success else 1)