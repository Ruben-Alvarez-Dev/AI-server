"""
Global pytest configuration and fixtures for AI-Server testing
"""

import pytest
import asyncio
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Generator, AsyncGenerator
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from tests.test_config import TestConfig


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_config():
    """Test configuration fixture"""
    return TestConfig()


@pytest.fixture(scope="session")
def project_root_path():
    """Project root path fixture"""
    return project_root


@pytest.fixture(scope="function")
def temp_dir():
    """Create temporary directory for test files"""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture(scope="function")
def test_logger():
    """Test-specific logger fixture"""
    logger = logging.getLogger("test")
    logger.setLevel(logging.DEBUG)
    
    # Create handler if not exists
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


@pytest.fixture(scope="session")
def mock_models_dir(test_config):
    """Create mock models directory structure"""
    models_dir = test_config.TEST_MODELS_DIR
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # Create mock model files
    (models_dir / "qwen2-1_5b-instruct-q6_k.gguf").touch()
    (models_dir / "qwen2_5-32b-instruct-q6_k.gguf").touch()
    (models_dir / "qwen2_5-coder-7b-instruct-q6_k.gguf").touch()
    (models_dir / "deepseek-coder-v2-lite-instruct-q6_k.gguf").touch()
    (models_dir / "qwen2_5-14b-instruct-q6_k.gguf").touch()
    
    yield models_dir
    
    # Cleanup
    if models_dir.exists():
        shutil.rmtree(models_dir)


@pytest.fixture(scope="function") 
async def mock_memory_server():
    """Mock memory server for testing"""
    class MockMemoryServer:
        def __init__(self):
            self.started = False
            self.port = 8001
            
        async def start(self):
            self.started = True
            
        async def stop(self):
            self.started = False
            
        def is_healthy(self):
            return self.started
    
    server = MockMemoryServer()
    yield server
    await server.stop()


@pytest.fixture(scope="function")
async def mock_llm_server():
    """Mock LLM server for testing"""
    class MockLLMServer:
        def __init__(self):
            self.started = False
            self.port = 8000
            
        async def start(self):
            self.started = True
            
        async def stop(self):
            self.started = False
            
        def is_healthy(self):
            return self.started
    
    server = MockLLMServer()
    yield server
    await server.stop()


@pytest.fixture(scope="function")
def mock_subprocess():
    """Mock subprocess for testing startup scripts"""
    class MockProcess:
        def __init__(self, returncode=0):
            self.returncode = returncode
            self.stdout = b"Mock stdout"
            self.stderr = b"Mock stderr"
            
        def terminate(self):
            pass
            
        def wait(self):
            return self.returncode
    
    class MockSubprocess:
        def __init__(self):
            self.processes = []
            
        def Popen(self, *args, **kwargs):
            process = MockProcess()
            self.processes.append(process)
            return process
    
    return MockSubprocess()


@pytest.fixture(autouse=True)
def setup_test_environment(test_config):
    """Auto-setup test environment for each test"""
    # Ensure test directories exist
    test_config.TEST_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    test_config.TEST_FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    test_config.TEST_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Set test environment variables
    os.environ["TESTING"] = "true"
    os.environ["TEST_MODE"] = "true"
    
    yield
    
    # Cleanup environment
    os.environ.pop("TESTING", None) 
    os.environ.pop("TEST_MODE", None)


def pytest_configure(config):
    """Pytest configuration hook"""
    # Add custom markers
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test" 
    )
    config.addinivalue_line(
        "markers", "functional: mark test as functional test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on file location"""
    for item in items:
        # Add markers based on file path
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "functional" in str(item.fspath):
            item.add_marker(pytest.mark.functional)