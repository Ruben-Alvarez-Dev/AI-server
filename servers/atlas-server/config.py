"""
ATLAS Server Configuration Module
Loads and manages public configuration parameters.

IMPORTANT: Only public configuration is loaded and documented.
Internal ATLAS core configuration is completely opaque.
"""

import yaml
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class AtlasServerConfig(BaseModel):
    """ATLAS server configuration - public parameters only."""
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8004, description="Server port") 
    workers: int = Field(default=1, description="Worker processes")
    reload: bool = Field(default=False, description="Auto-reload (disabled for black-box)")
    log_level: str = Field(default="WARNING", description="Log level")


class AtlasApiConfig(BaseModel):
    """ATLAS API configuration - public interface settings."""
    version: str = Field(default="v1", description="API version")
    base_path: str = Field(default="/atlas", description="Base API path")
    docs_url: str = Field(default="/atlas/docs", description="OpenAPI docs URL")
    redoc_url: str = Field(default="/atlas/redoc", description="ReDoc URL")
    max_request_size_mb: int = Field(default=10, description="Max request size")
    request_timeout_seconds: int = Field(default=30, description="Request timeout")


class AtlasRateLimitConfig(BaseModel):
    """Rate limiting configuration."""
    enabled: bool = Field(default=True, description="Rate limiting enabled")
    requests_per_minute: int = Field(default=100, description="Requests per minute")
    burst_limit: int = Field(default=20, description="Burst limit")


class AtlasSecurityConfig(BaseModel):
    """Security configuration - public parameters only."""
    cors_enabled: bool = Field(default=True, description="CORS enabled")
    cors_origins: List[str] = Field(default=["*"], description="CORS origins")
    api_key_required: bool = Field(default=False, description="API key required")
    https_only: bool = Field(default=False, description="HTTPS only")


class AtlasMonitoringConfig(BaseModel):
    """Monitoring configuration - public metrics only."""
    metrics_enabled: bool = Field(default=True, description="Metrics enabled")
    metrics_port: int = Field(default=9004, description="Metrics port")
    metrics_path: str = Field(default="/atlas/metrics", description="Metrics path")
    health_check_interval: int = Field(default=30, description="Health check interval")


class AtlasIntegrationConfig(BaseModel):
    """Integration settings with other services."""
    memory_server_url: str = Field(default="http://localhost:8001", description="Memory Server URL")
    llm_server_url: str = Field(default="http://localhost:8002", description="LLM Server URL") 
    gui_server_url: str = Field(default="http://localhost:8003", description="GUI Server URL")


class AtlasConfig(BaseModel):
    """
    Complete ATLAS configuration.
    
    IMPORTANT: Only public configuration parameters are included.
    Internal ATLAS core configuration is completely opaque.
    """
    server: AtlasServerConfig = Field(default_factory=AtlasServerConfig)
    api: AtlasApiConfig = Field(default_factory=AtlasApiConfig)
    rate_limiting: AtlasRateLimitConfig = Field(default_factory=AtlasRateLimitConfig)
    security: AtlasSecurityConfig = Field(default_factory=AtlasSecurityConfig)
    monitoring: AtlasMonitoringConfig = Field(default_factory=AtlasMonitoringConfig)
    integration: AtlasIntegrationConfig = Field(default_factory=AtlasIntegrationConfig)
    
    # Public processing parameters
    processing_modes: Dict[str, Dict[str, Any]] = Field(
        default_factory=lambda: {
            "default": {"enabled": True, "timeout_seconds": 10},
            "enhance": {"enabled": True, "timeout_seconds": 15},
            "analyze": {"enabled": True, "timeout_seconds": 20},
            "optimize": {"enabled": True, "timeout_seconds": 25}
        }
    )
    
    enhancement_types: Dict[str, Dict[str, Any]] = Field(
        default_factory=lambda: {
            "quality": {"enabled": True, "confidence_threshold": 0.7},
            "clarity": {"enabled": True, "confidence_threshold": 0.8},
            "structure": {"enabled": True, "confidence_threshold": 0.75},
            "coherence": {"enabled": True, "confidence_threshold": 0.8}
        }
    )


def load_atlas_config(config_path: Optional[str] = None) -> AtlasConfig:
    """
    Load ATLAS configuration from YAML file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        AtlasConfig instance with loaded settings
        
    Note:
        Only public configuration is loaded - internal settings are opaque.
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / "config" / "atlas.yaml"
    
    try:
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Extract atlas section
        atlas_data = config_data.get('atlas', {})
        
        return AtlasConfig(**atlas_data)
        
    except Exception as e:
        logger.warning(f"Failed to load ATLAS config from {config_path}: {e}")
        logger.info("Using default ATLAS configuration")
        return AtlasConfig()


# Global configuration instance
atlas_config = load_atlas_config()

# Note: Internal ATLAS core configuration is completely opaque and not accessible