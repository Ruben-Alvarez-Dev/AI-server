"""
Memory-Server Configuration System
Centralized configuration management with environment variable support
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging

# Setup logger
logger = logging.getLogger(__name__)


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO" 
    WARNING = "WARNING"
    ERROR = "ERROR"


class VectorIndexType(str, Enum):
    HNSW = "HNSW"
    IVF = "IVF"
    FLAT = "FLAT"


@dataclass
class MemoryServerConfig:
    """
    Comprehensive configuration for Memory-Server
    Supports environment variables and file-based configuration
    """
    
    # === Path Configuration ===
    BASE_DIR: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    DATA_DIR: Path = field(init=False)
    MODELS_DIR: Path = field(init=False)
    CACHE_DIR: Path = field(init=False)
    LOGS_DIR: Path = field(init=False)
    GRAPH_DB_PATH: Path = field(init=False)
    
    # === Model Configuration ===
    # Embedding Hub Configuration (replaces individual model loading)
    USE_EMBEDDING_HUB: bool = True
    EMBEDDING_HUB_HOST: str = "localhost"
    EMBEDDING_HUB_PORT: int = 8900
    EMBEDDING_HUB_TIMEOUT: int = 30
    
    # Legacy model configs (for fallback if hub unavailable) - Use working model
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"  # Use working sentence transformer model
    COLBERT_MODEL: str = "disabled"
    CODE_MODEL: str = "microsoft/codebert-base"
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    MULTIMODAL_MODEL: str = "openai/clip-vit-large-patch14"
    
    # === Memory Configuration === 
    # Optimized for M1 Ultra with 128GB RAM
    WORKING_MEMORY_SIZE: int = 256 * 1024  # 256K tokens (increased for M1 Ultra)
    EPISODIC_MEMORY_SIZE: int = 8 * 1024 * 1024  # 8M tokens (4x increase) 
    SEMANTIC_MEMORY_UNLIMITED: bool = True
    PROCEDURAL_MEMORY_SIZE: int = 50000  # 50K patterns (5x increase)
    
    # === Vector Store Configuration ===
    VECTOR_DIMENSION: int = 768
    FAISS_INDEX_TYPE: VectorIndexType = VectorIndexType.HNSW
    HNSW_M: int = 32  # Número de conexiones bidireccionales
    HNSW_EF_CONSTRUCTION: int = 200  # Calidad de construcción
    HNSW_EF_SEARCH: int = 100  # Calidad de búsqueda
    MAX_RESULTS: int = 50
    
    # === Graph Configuration ===
    NEO4J_EMBEDDED: bool = True
    USE_NETWORKX_FALLBACK: bool = True
    GRAPH_MAX_HOPS: int = 3
    COMMUNITY_DETECTION_ALGORITHM: str = "louvain"
    
    # === Late Chunking Configuration ===
    MAX_CONTEXT_LENGTH: int = 8192  # Jina v3 limit
    DEFAULT_CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: float = 0.2  # 20%
    SEMANTIC_THRESHOLD: float = 0.7
    USE_LATE_CHUNKING: bool = True
    
    # === Agentic RAG Configuration ===
    MAX_REASONING_TURNS: int = 5
    CONFIDENCE_THRESHOLD: float = 0.9
    ENABLE_MULTI_TURN: bool = True
    REASONING_TIMEOUT: int = 60  # seconds
    
    # === Performance Configuration ===
    # Optimized for M1 Ultra 128GB RAM - High Performance Settings
    MAX_CONCURRENT_REQUESTS: int = 500  # 5x increase for M1 Ultra
    QUERY_TIMEOUT: int = 60  # Extended for complex queries
    BATCH_SIZE: int = 128  # 4x increase for better throughput  
    NUM_WORKERS: int = 12  # Leverage M1 Ultra's 20 CPU cores
    ENABLE_CACHING: bool = True
    CACHE_TTL: int = 7200  # 2 hours (longer caching with ample RAM)
    
    # === API Configuration ===
    API_HOST: str = "localhost"
    API_PORT: int = 8001
    WEBSOCKET_PORT: int = 8002
    GRPC_PORT: int = 8003
    API_PREFIX: str = "/api/v1"
    ENABLE_CORS: bool = True
    MAX_FILE_SIZE: int = 500 * 1024 * 1024  # 500MB max file size (10x increase for M1 Ultra)
    
    # === Logging Configuration ===
    LOG_LEVEL: LogLevel = LogLevel.INFO
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ENABLE_FILE_LOGGING: bool = True
    LOG_ROTATION: str = "1 day"
    LOG_RETENTION: str = "30 days"
    
    # === Monitoring Configuration ===
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    ENABLE_HEALTH_CHECKS: bool = True
    HEALTH_CHECK_INTERVAL: int = 30  # seconds
    
    # === Security Configuration ===
    API_KEY: Optional[str] = None
    ENABLE_RATE_LIMITING: bool = True
    RATE_LIMIT_PER_MINUTE: int = 100
    ENABLE_REQUEST_VALIDATION: bool = True
    
    # === External API Keys ===
    SERPER_API_KEY: str = field(default_factory=lambda: os.getenv("SERPER_API_KEY", ""))
    FIRECRAWL_API_KEY: str = field(default_factory=lambda: os.getenv("FIRECRAWL_API_KEY", ""))
    TAVILY_API_KEY: str = field(default_factory=lambda: os.getenv("TAVILY_API_KEY", ""))
    OPENAI_API_KEY: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    ANTHROPIC_API_KEY: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    
    # === Multimodal Configuration ===
    ENABLE_OCR: bool = True
    ENABLE_IMAGE_ANALYSIS: bool = True
    ENABLE_CODE_ANALYSIS: bool = True
    MAX_IMAGE_SIZE_MB: int = 10
    SUPPORTED_IMAGE_FORMATS: list = field(
        default_factory=lambda: [".jpg", ".jpeg", ".png", ".pdf", ".tiff"]
    )
    
    # === Development/Debug Configuration ===
    DEBUG_MODE: bool = False
    ENABLE_PROFILING: bool = False
    MOCK_MODELS: bool = False  # Para testing sin descargar modelos
    
    def __post_init__(self):
        """Initialize computed paths and environment variable overrides"""
        # Set up paths
        self.DATA_DIR = self.BASE_DIR / "data"
        self.MODELS_DIR = self.DATA_DIR / "models"
        self.CACHE_DIR = self.DATA_DIR / "cache"
        self.LOGS_DIR = self.DATA_DIR / "logs"
        self.GRAPH_DB_PATH = self.DATA_DIR / "neo4j"
        
        # Create directories
        for path in [self.DATA_DIR, self.MODELS_DIR, self.CACHE_DIR, 
                    self.LOGS_DIR, self.GRAPH_DB_PATH]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Override with environment variables
        self._load_from_environment()
        
        # Validate configuration
        self._validate_config()
    
    def _load_from_environment(self):
        """Load configuration from environment variables"""
        env_mappings = {
            # API Configuration
            "MEMORY_SERVER_HOST": "API_HOST",
            "MEMORY_SERVER_PORT": ("API_PORT", int),
            "MEMORY_SERVER_DEBUG": ("DEBUG_MODE", bool),
            
            # Model Configuration
            "EMBEDDING_MODEL": "EMBEDDING_MODEL",
            "COLBERT_MODEL": "COLBERT_MODEL",
            "CODE_MODEL": "CODE_MODEL",
            
            # Performance
            "MAX_CONCURRENT_REQUESTS": ("MAX_CONCURRENT_REQUESTS", int),
            "BATCH_SIZE": ("BATCH_SIZE", int),
            "QUERY_TIMEOUT": ("QUERY_TIMEOUT", int),
            
            # Memory
            "WORKING_MEMORY_SIZE": ("WORKING_MEMORY_SIZE", int),
            "EPISODIC_MEMORY_SIZE": ("EPISODIC_MEMORY_SIZE", int),
            
            # Security
            "API_KEY": "API_KEY",
            "RATE_LIMIT_PER_MINUTE": ("RATE_LIMIT_PER_MINUTE", int),
            
            # Logging
            "LOG_LEVEL": "LOG_LEVEL",
        }
        
        for env_var, config_attr in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                try:
                    if isinstance(config_attr, tuple):
                        attr_name, type_converter = config_attr
                        if type_converter == bool:
                            env_value = env_value.lower() in ('true', '1', 'yes', 'on')
                        else:
                            env_value = type_converter(env_value)
                        setattr(self, attr_name, env_value)
                    else:
                        setattr(self, config_attr, env_value)
                    
                    logger.info(f"Config override from env: {config_attr} = {env_value}")
                    
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid environment variable {env_var}={env_value}: {e}")
    
    def _validate_config(self):
        """Validate configuration values"""
        errors = []
        
        # Validate memory sizes
        if self.WORKING_MEMORY_SIZE <= 0:
            errors.append("WORKING_MEMORY_SIZE must be positive")
        
        if self.EPISODIC_MEMORY_SIZE <= self.WORKING_MEMORY_SIZE:
            errors.append("EPISODIC_MEMORY_SIZE should be larger than WORKING_MEMORY_SIZE")
        
        # Validate chunk configuration
        if not 0 < self.CHUNK_OVERLAP < 1:
            errors.append("CHUNK_OVERLAP must be between 0 and 1")
        
        if self.DEFAULT_CHUNK_SIZE <= 0:
            errors.append("DEFAULT_CHUNK_SIZE must be positive")
        
        # Validate performance settings
        if self.MAX_CONCURRENT_REQUESTS <= 0:
            errors.append("MAX_CONCURRENT_REQUESTS must be positive")
        
        if self.BATCH_SIZE <= 0:
            errors.append("BATCH_SIZE must be positive")
        
        # Validate ports
        for port_attr in ["API_PORT", "WEBSOCKET_PORT", "GRPC_PORT", "METRICS_PORT"]:
            port = getattr(self, port_attr)
            if not (1024 <= port <= 65535):
                errors.append(f"{port_attr} must be between 1024 and 65535")
        
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"- {e}" for e in errors)
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("✅ Configuration validation passed")
    
    def get_model_path(self, model_type: str) -> Path:
        """Get local path for a specific model type"""
        model_paths = {
            "embedding": self.EMBEDDING_MODEL,
            "colbert": self.COLBERT_MODEL,
            "code": self.CODE_MODEL,
            "reranker": self.RERANKER_MODEL,
            "multimodal": self.MULTIMODAL_MODEL
        }
        
        if model_type not in model_paths:
            raise ValueError(f"Unknown model type: {model_type}")
        
        model_name = model_paths[model_type]
        return self.MODELS_DIR / model_name.replace("/", "_")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        result = {}
        for field_name, field_def in self.__dataclass_fields__.items():
            value = getattr(self, field_name)
            if isinstance(value, Path):
                result[field_name] = str(value)
            elif isinstance(value, Enum):
                result[field_name] = value.value
            else:
                result[field_name] = value
        return result
    
    def save_to_file(self, path: Path):
        """Save configuration to file"""
        import json
        
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        
        logger.info(f"Configuration saved to {path}")
    
    @classmethod
    def load_from_file(cls, path: Path) -> 'MemoryServerConfig':
        """Load configuration from file"""
        import json
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        # Convert string paths back to Path objects and filter out invalid keys
        filtered_data = {}
        valid_fields = {field.name for field in cls.__dataclass_fields__.values() if field.init}
        
        for key, value in data.items():
            # Skip init=False fields like DATA_DIR, MODELS_DIR, etc
            if key in valid_fields:
                if key.endswith('_DIR') or key.endswith('_PATH'):
                    filtered_data[key] = Path(value)
                else:
                    filtered_data[key] = value
        
        config = cls(**filtered_data)
        logger.info(f"Configuration loaded from {path}")
        return config


# Global configuration instance
config = MemoryServerConfig()

# Convenience function for getting configuration
def get_config() -> MemoryServerConfig:
    """Get the global configuration instance"""
    return config

def reload_config():
    """Reload configuration (useful for testing)"""
    global config
    config = MemoryServerConfig()
    logger.info("Configuration reloaded")
    return config