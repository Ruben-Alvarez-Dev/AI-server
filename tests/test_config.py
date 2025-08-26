"""
Test configuration and settings for AI-Server testing
"""

import os
from pathlib import Path
from typing import Dict, Any


class TestConfig:
    """Configuration class for testing environment"""
    
    def __init__(self):
        # Project paths
        self.PROJECT_ROOT = Path(__file__).parent.parent
        self.TESTS_ROOT = Path(__file__).parent
        
        # Test directories
        self.TEST_LOGS_DIR = self.TESTS_ROOT / "logs"
        self.TEST_FIXTURES_DIR = self.TESTS_ROOT / "fixtures"
        self.TEST_REPORTS_DIR = self.TESTS_ROOT / "reports"
        self.TEST_MODELS_DIR = self.TESTS_ROOT / "fixtures" / "test_models"
        
        # Server configurations for testing
        self.MEMORY_SERVER_TEST_PORT = 8091
        self.LLM_SERVER_TEST_PORT = 8090
        
        # Test timeouts (in seconds)
        self.SERVER_START_TIMEOUT = 30
        self.API_REQUEST_TIMEOUT = 10
        self.HEALTH_CHECK_TIMEOUT = 5
        
        # Test model paths (mock models for testing)
        self.TEST_MODEL_PATHS = {
            "router": self.TEST_MODELS_DIR / "qwen2-1_5b-instruct-q6_k.gguf",
            "architect": self.TEST_MODELS_DIR / "qwen2_5-32b-instruct-q6_k.gguf",
            "coder_primary": self.TEST_MODELS_DIR / "qwen2_5-coder-7b-instruct-q6_k.gguf",
            "coder_secondary": self.TEST_MODELS_DIR / "deepseek-coder-v2-lite-instruct-q6_k.gguf",
            "qa_checker": self.TEST_MODELS_DIR / "qwen2_5-14b-instruct-q6_k.gguf",
            "debugger": self.TEST_MODELS_DIR / "deepseek-coder-v2-lite-instruct-q6_k.gguf"
        }
        
        # API endpoints for testing
        self.MEMORY_SERVER_ENDPOINTS = {
            "health": f"http://localhost:{self.MEMORY_SERVER_TEST_PORT}/health/status",
            "root": f"http://localhost:{self.MEMORY_SERVER_TEST_PORT}/",
            "documents": f"http://localhost:{self.MEMORY_SERVER_TEST_PORT}/api/v1/documents",
            "search": f"http://localhost:{self.MEMORY_SERVER_TEST_PORT}/api/v1/search"
        }
        
        self.LLM_SERVER_ENDPOINTS = {
            "health": f"http://localhost:{self.LLM_SERVER_TEST_PORT}/health",
            "root": f"http://localhost:{self.LLM_SERVER_TEST_PORT}/",
            "workflows": f"http://localhost:{self.LLM_SERVER_TEST_PORT}/workflows",
            "agents": f"http://localhost:{self.LLM_SERVER_TEST_PORT}/agents"
        }
        
        # Logging configuration
        self.LOG_LEVEL = "DEBUG"
        self.LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
        
        # Test data
        self.TEST_DOCUMENT_CONTENT = """
        Este es un documento de prueba para el sistema Memory-Server.
        Contiene información de ejemplo que será procesada por LazyGraphRAG
        y el sistema de Late Chunking para validar la funcionalidad básica.
        """
        
        self.TEST_LLM_PROMPT = "Explica brevemente qué es la inteligencia artificial"
        
        # Performance thresholds
        self.MAX_STARTUP_TIME = 60  # seconds
        self.MAX_API_RESPONSE_TIME = 2.0  # seconds
        self.MIN_MEMORY_EFFICIENCY = 0.8  # 80% efficiency expected
        
    def get_log_file_path(self, log_type: str) -> Path:
        """Get path for specific log file type"""
        return self.TEST_LOGS_DIR / f"{log_type}.log"
        
    def get_fixture_path(self, fixture_name: str) -> Path:
        """Get path for test fixture"""
        return self.TEST_FIXTURES_DIR / fixture_name
        
    def get_report_path(self, report_name: str) -> Path:
        """Get path for test report"""
        return self.TEST_REPORTS_DIR / report_name
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for logging/debugging"""
        return {
            "project_root": str(self.PROJECT_ROOT),
            "tests_root": str(self.TESTS_ROOT),
            "memory_server_port": self.MEMORY_SERVER_TEST_PORT,
            "llm_server_port": self.LLM_SERVER_TEST_PORT,
            "timeouts": {
                "server_start": self.SERVER_START_TIMEOUT,
                "api_request": self.API_REQUEST_TIMEOUT,
                "health_check": self.HEALTH_CHECK_TIMEOUT
            },
            "performance_thresholds": {
                "max_startup_time": self.MAX_STARTUP_TIME,
                "max_api_response_time": self.MAX_API_RESPONSE_TIME,
                "min_memory_efficiency": self.MIN_MEMORY_EFFICIENCY
            }
        }


# Global test configuration instance
test_config = TestConfig()