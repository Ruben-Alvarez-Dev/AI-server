"""
Settings management for LLM Server
"""

import os
from typing import List, Optional
from functools import lru_cache
from pydantic import BaseSettings


class LLMServerSettings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    reload: bool = False
    
    # Model paths
    models_dir: str = "./models"
    router_model_path: str = "./models/qwen2-1_5b-instruct-q6_k.gguf"
    architect_model_path: str = "./models/qwen2_5-32b-instruct-q6_k.gguf"
    coder_primary_model_path: str = "./models/qwen2_5-coder-7b-instruct-q6_k.gguf"
    coder_secondary_model_path: str = "./models/deepseek-coder-v2-lite-instruct-q6_k.gguf"
    qa_checker_model_path: str = "./models/qwen2_5-14b-instruct-q6_k.gguf"
    debugger_model_path: str = "./models/deepseek-coder-v2-lite-instruct-q6_k.gguf"
    
    # Performance settings
    max_concurrent_requests: int = 10
    request_timeout: int = 600
    enable_metrics: bool = True
    enable_monitoring: bool = True
    
    # Security
    enable_cors: bool = True
    cors_origins: List[str] = ["*"]
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = "./logs/llm-server.log"
    
    # Feature flags
    enable_swagger_ui: bool = True
    enable_background_tasks: bool = True
    
    class Config:
        env_file = ".env"
        env_prefix = "LLM_SERVER_"


@lru_cache()
def get_settings() -> LLMServerSettings:
    """Get cached settings instance"""
    return LLMServerSettings()