"""
Configuration management module for AI Server.

Provides centralized configuration loading and validation with environment 
variable override support.
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, Union
from pydantic import BaseModel, validator


class ConfigError(Exception):
    """Configuration-related errors."""
    pass


class BaseConfig(BaseModel):
    """Base configuration class with common settings."""
    
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        case_sensitive = False


class DatabaseConfig(BaseConfig):
    """Database configuration."""
    url: str = "postgresql://localhost:5432/ai_server"
    redis_url: str = "redis://localhost:6379/0"
    pool_size: int = 10
    max_overflow: int = 20


class ServerConfig(BaseConfig):
    """Server configuration."""
    memory_server_port: int = 8001
    llm_server_port: int = 8002
    gui_server_port: int = 8003
    atlas_server_port: int = 8004
    host: str = "localhost"
    debug: bool = False


class ModelConfig(BaseConfig):
    """Model configuration."""
    models_path: str = "./models"
    default_profile: str = "GENERAL"
    gpu_enabled: bool = True
    max_gpu_memory_gb: int = 8


class MessagingConfig(BaseConfig):
    """Messaging configuration."""
    pulsar_url: str = "pulsar://localhost:6650"
    nats_url: str = "nats://localhost:4222"
    benthos_api_port: int = 4195


class SecurityConfig(BaseConfig):
    """Security configuration."""
    secret_key: str = "change-this-secret-key-in-production"
    jwt_secret_key: str = "your-jwt-secret-here"
    session_timeout_minutes: int = 60
    rate_limit_per_minute: int = 60


class AtlasConfig(BaseConfig):
    """ATLAS configuration."""
    enabled: bool = True
    endpoint: str = "http://localhost:8004/atlas/v1"
    timeout_seconds: int = 30
    rate_limit: int = 100


class AppConfig(BaseConfig):
    """Main application configuration."""
    database: DatabaseConfig = DatabaseConfig()
    server: ServerConfig = ServerConfig()
    models: ModelConfig = ModelConfig()
    messaging: MessagingConfig = MessagingConfig()
    security: SecurityConfig = SecurityConfig()
    atlas: AtlasConfig = AtlasConfig()
    
    log_level: str = "INFO"
    environment: str = "development"


class ConfigManager:
    """Configuration manager for loading and validating configs."""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self._config: Optional[AppConfig] = None
    
    def load_config(self, config_file: str = "system.yaml") -> AppConfig:
        """Load configuration from YAML file with environment overrides."""
        config_path = self.config_dir / config_file
        
        if not config_path.exists():
            raise ConfigError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_path, 'r') as f:
                yaml_data = yaml.safe_load(f)
            
            # Override with environment variables
            yaml_data = self._apply_env_overrides(yaml_data)
            
            self._config = AppConfig(**yaml_data)
            return self._config
            
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in {config_path}: {e}")
        except Exception as e:
            raise ConfigError(f"Error loading configuration: {e}")
    
    def get_config(self) -> AppConfig:
        """Get current configuration, loading default if not loaded."""
        if self._config is None:
            self.load_config()
        return self._config
    
    def reload_config(self) -> AppConfig:
        """Reload configuration from file."""
        self._config = None
        return self.load_config()
    
    def _apply_env_overrides(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides to configuration."""
        env_mappings = {
            'DATABASE_URL': ['database', 'url'],
            'REDIS_URL': ['database', 'redis_url'],
            'MEMORY_SERVER_PORT': ['server', 'memory_server_port'],
            'LLM_SERVER_PORT': ['server', 'llm_server_port'],
            'GUI_SERVER_PORT': ['server', 'gui_server_port'],
            'ATLAS_SERVER_PORT': ['server', 'atlas_server_port'],
            'LOG_LEVEL': ['log_level'],
            'DEBUG_MODE': ['server', 'debug'],
            'SECRET_KEY': ['security', 'secret_key'],
            'JWT_SECRET_KEY': ['security', 'jwt_secret_key'],
            'MODELS_PATH': ['models', 'models_path'],
            'DEFAULT_PROFILE': ['models', 'default_profile'],
            'GPU_ENABLED': ['models', 'gpu_enabled'],
            'MAX_GPU_MEMORY_GB': ['models', 'max_gpu_memory_gb'],
            'PULSAR_URL': ['messaging', 'pulsar_url'],
            'NATS_URL': ['messaging', 'nats_url'],
            'ATLAS_ENABLED': ['atlas', 'enabled'],
            'ATLAS_ENDPOINT': ['atlas', 'endpoint'],
        }
        
        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                self._set_nested_config(config_data, config_path, env_value)
        
        return config_data
    
    def _set_nested_config(self, config_data: Dict[str, Any], 
                          path: list[str], value: str) -> None:
        """Set nested configuration value from environment variable."""
        current = config_data
        
        # Navigate to parent
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set final value with type conversion
        final_key = path[-1]
        current[final_key] = self._convert_env_value(value)
    
    def _convert_env_value(self, value: str) -> Union[str, int, bool]:
        """Convert environment variable string to appropriate type."""
        # Boolean conversion
        if value.lower() in ('true', 'yes', '1', 'on'):
            return True
        if value.lower() in ('false', 'no', '0', 'off'):
            return False
        
        # Integer conversion
        if value.isdigit():
            return int(value)
        
        # String (default)
        return value


# Global configuration manager instance
config_manager = ConfigManager()


def get_config() -> AppConfig:
    """Get application configuration."""
    return config_manager.get_config()


def reload_config() -> AppConfig:
    """Reload application configuration."""
    return config_manager.reload_config()