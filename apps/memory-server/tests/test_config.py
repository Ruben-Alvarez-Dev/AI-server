"""
Test Configuration System
"""

import pytest
import os
import tempfile
from pathlib import Path

from core.config import MemoryServerConfig, get_config, reload_config


class TestMemoryServerConfig:
    """Test the configuration system"""
    
    def test_default_config_creation(self):
        """Test default configuration creation"""
        config = MemoryServerConfig()
        
        assert config.EMBEDDING_MODEL == "jinaai/jina-embeddings-v2-base-en"
        assert config.WORKING_MEMORY_SIZE == 128 * 1024
        assert config.EPISODIC_MEMORY_SIZE == 2 * 1024 * 1024
        assert config.API_PORT == 8001
        assert config.MAX_CONTEXT_LENGTH == 8192
    
    def test_path_initialization(self):
        """Test that paths are properly initialized"""
        config = MemoryServerConfig()
        
        assert config.DATA_DIR.exists()
        assert config.MODELS_DIR.exists()
        assert config.CACHE_DIR.exists()
        assert config.LOGS_DIR.exists()
        
        # Paths should be absolute
        assert config.DATA_DIR.is_absolute()
        assert config.MODELS_DIR.is_absolute()
    
    def test_environment_variable_override(self):
        """Test environment variable overrides"""
        # Set environment variable
        os.environ["MEMORY_SERVER_PORT"] = "9001"
        os.environ["MEMORY_SERVER_DEBUG"] = "true"
        
        try:
            config = MemoryServerConfig()
            assert config.API_PORT == 9001
            assert config.DEBUG_MODE == True
        finally:
            # Cleanup
            os.environ.pop("MEMORY_SERVER_PORT", None)
            os.environ.pop("MEMORY_SERVER_DEBUG", None)
    
    def test_validation(self):
        """Test configuration validation"""
        # Test invalid working memory size
        with pytest.raises(ValueError, match="WORKING_MEMORY_SIZE must be positive"):
            MemoryServerConfig(WORKING_MEMORY_SIZE=-1)
        
        # Test invalid chunk overlap
        with pytest.raises(ValueError, match="CHUNK_OVERLAP must be between 0 and 1"):
            MemoryServerConfig(CHUNK_OVERLAP=1.5)
    
    def test_model_paths(self):
        """Test model path generation"""
        config = MemoryServerConfig()
        
        embedding_path = config.get_model_path("embedding")
        assert embedding_path.name == "jinaai_jina-embeddings-v2-base-en"
        assert embedding_path.parent == config.MODELS_DIR
        
        with pytest.raises(ValueError, match="Unknown model type"):
            config.get_model_path("nonexistent")
    
    def test_to_dict_conversion(self):
        """Test configuration to dictionary conversion"""
        config = MemoryServerConfig()
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert "API_PORT" in config_dict
        assert "EMBEDDING_MODEL" in config_dict
        
        # Path objects should be converted to strings
        assert isinstance(config_dict["BASE_DIR"], str)
    
    def test_save_and_load_config(self):
        """Test saving and loading configuration"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            
            # Create and save config
            original_config = MemoryServerConfig(API_PORT=9999)
            original_config.save_to_file(config_path)
            
            assert config_path.exists()
            
            # Load config
            loaded_config = MemoryServerConfig.load_from_file(config_path)
            assert loaded_config.API_PORT == 9999


def test_global_config():
    """Test global configuration instance"""
    config1 = get_config()
    config2 = get_config()
    
    # Should return the same instance
    assert config1 is config2
    
    # Test reload
    original_port = config1.API_PORT
    reload_config()
    config3 = get_config()
    assert config3.API_PORT == original_port  # Should have same default


if __name__ == "__main__":
    pytest.main([__file__, "-v"])