# Testing Guide - AI-Server

## Overview

Comprehensive testing framework for AI-Server with unit, integration, and functional tests. Features structured logging, performance metrics, and detailed reporting.

## Quick Start

```bash
# Install test dependencies
pip install -r tests/requirements.txt

# Run all tests
python tests/run_tests.py --all

# Run specific test category
python tests/run_tests.py --unit
python tests/run_tests.py --integration
python tests/run_tests.py --functional

# Run component-specific tests
python tests/run_tests.py --component memory-server
python tests/run_tests.py --component llm-server
python tests/run_tests.py --component model-watcher
python tests/run_tests.py --component startup

# Run with coverage
python tests/run_tests.py --coverage

# Run performance tests
python tests/run_tests.py --performance
```

## Testing Architecture

### Directory Structure

```
tests/
├── conftest.py              # Global pytest configuration
├── test_config.py          # Test-specific configuration
├── requirements.txt        # Testing dependencies
├── run_tests.py           # Main test runner script
├── pytest.ini            # Pytest configuration
├── unit/                  # Unit tests
├── integration/           # Integration tests
├── functional/            # Functional tests
├── fixtures/              # Test data and mocks
├── logs/                  # Test execution logs
└── reports/               # Test reports and coverage
```

### Test Categories

#### 1. Unit Tests (`tests/unit/`)
- **Purpose**: Test individual components in isolation
- **Scope**: Single functions, classes, modules
- **Mocking**: Heavy use of mocks for dependencies
- **Speed**: Fast execution (< 1 second per test)

**Components tested:**
- `test_startup_script.py` - Startup script functionality
- `test_memory_server.py` - Memory-Server core components
- `test_llm_server.py` - LLM-Server agents and workflows
- `test_model_watcher.py` - Model Watcher service

#### 2. Integration Tests (`tests/integration/`)
- **Purpose**: Test component interactions
- **Scope**: Multiple components working together
- **Mocking**: Limited mocking, real component integration
- **Speed**: Medium execution (1-10 seconds per test)

**Areas tested:**
- Server communication
- API endpoint interactions
- Service orchestration
- Data flow between components

#### 3. Functional Tests (`tests/functional/`)
- **Purpose**: Test complete user workflows
- **Scope**: End-to-end scenarios
- **Mocking**: Minimal mocking, real system usage
- **Speed**: Slower execution (10+ seconds per test)

**Workflows tested:**
- Complete system startup
- Document processing workflows
- LLM request/response cycles
- Memory operations

## Test Configuration

### Environment Variables

```bash
# Test mode flags
TESTING=true
TEST_MODE=true

# Server ports (non-conflicting)
MEMORY_SERVER_TEST_PORT=8091
LLM_SERVER_TEST_PORT=8090

# Timeouts
SERVER_START_TIMEOUT=30
API_REQUEST_TIMEOUT=10
HEALTH_CHECK_TIMEOUT=5

# Performance thresholds
MAX_STARTUP_TIME=60
MAX_API_RESPONSE_TIME=2.0
MIN_MEMORY_EFFICIENCY=0.8
```

### Test Fixtures

#### Global Fixtures (`conftest.py`)
- `test_config` - Test configuration object
- `project_root_path` - Project root directory
- `temp_dir` - Temporary directory for test files
- `test_logger` - Test-specific logger
- `mock_models_dir` - Mock models directory
- `mock_memory_server` - Mock Memory-Server instance
- `mock_llm_server` - Mock LLM-Server instance

#### Component-Specific Fixtures
- Mock subprocess for startup testing
- Temporary model files
- Test documents and data
- Mock HTTP responses

## Logging and Reporting

### Log Files (`tests/logs/`)
```
test_execution.log       # Main test runner logs
component_tests.log      # Component-specific test logs
integration_tests.log    # Integration test logs
performance_tests.log    # Performance test logs
pytest.log              # Pytest internal logs
```

### Reports (`tests/reports/`)
```
test_results.json       # Comprehensive test results
unit_tests.xml         # JUnit XML for unit tests
integration_tests.xml  # JUnit XML for integration tests
functional_tests.xml   # JUnit XML for functional tests
coverage/              # HTML coverage reports
benchmark.json         # Performance benchmark data
```

### Result Format

```json
{
  "start_time": "2025-01-15T10:00:00",
  "end_time": "2025-01-15T10:05:30",
  "duration": 330.5,
  "tests_run": 156,
  "passed": 142,
  "failed": 3,
  "skipped": 11,
  "coverage": 85.2,
  "components": {
    "unit": {
      "tests_run": 89,
      "passed": 84,
      "failed": 2,
      "skipped": 3,
      "duration": 45.3
    }
  },
  "performance": {
    "avg_test_time": 2.1,
    "slowest_tests": [...]
  }
}
```

## Performance Testing

### Benchmarks
- Startup time measurement
- API response times
- Memory usage tracking
- Component initialization speed

### Thresholds
- **Startup**: < 60 seconds
- **API Response**: < 2 seconds
- **Memory Efficiency**: > 80%
- **Test Suite**: < 10 minutes

## Writing Tests

### Unit Test Template

```python
"""
Unit tests for [Component Name]
"""

import pytest
from unittest.mock import patch, MagicMock
from tests.test_config import TestConfig

class TestComponentName:
    """Test [Component] functionality"""
    
    @pytest.fixture
    def component(self):
        """Create component instance for testing"""
        return ComponentClass()
    
    def test_component_initialization(self, component):
        """Test component initializes correctly"""
        assert component is not None
        assert component.some_property == expected_value
    
    @patch('module.dependency')
    def test_component_method(self, mock_dependency, component):
        """Test component method with mocked dependency"""
        mock_dependency.return_value = "mocked_result"
        
        result = component.method_under_test()
        
        assert result == "expected_result"
        mock_dependency.assert_called_once()
```

### Integration Test Template

```python
"""
Integration tests for [Component Interaction]
"""

import pytest
import asyncio
from tests.test_config import TestConfig

class TestComponentIntegration:
    """Test integration between components"""
    
    @pytest.mark.asyncio
    async def test_component_communication(self):
        """Test components communicate correctly"""
        # Setup components
        component_a = ComponentA()
        component_b = ComponentB()
        
        # Test interaction
        result = await component_a.send_message(component_b, "test")
        
        assert result.status == "success"
        assert result.data is not None
```

### Functional Test Template

```python
"""
Functional tests for [Complete Workflow]
"""

import pytest
import asyncio
from tests.test_config import TestConfig

class TestWorkflowFunctionality:
    """Test complete workflow functionality"""
    
    @pytest.mark.functional
    @pytest.mark.slow
    async def test_complete_workflow(self):
        """Test end-to-end workflow"""
        # This test runs actual system components
        # Use sparingly due to resource requirements
        
        # Start services
        await start_test_services()
        
        try:
            # Execute workflow
            result = await execute_complete_workflow()
            
            # Verify results
            assert result.success is True
            assert len(result.steps) == expected_step_count
            
        finally:
            # Cleanup
            await stop_test_services()
```

## Test Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.unit          # Unit test
@pytest.mark.integration   # Integration test  
@pytest.mark.functional    # Functional test
@pytest.mark.slow          # Slow running test
@pytest.mark.network       # Requires network
@pytest.mark.models        # Requires model files
@pytest.mark.startup       # Startup functionality
@pytest.mark.memory_server # Memory-Server specific
@pytest.mark.llm_server    # LLM-Server specific
@pytest.mark.model_watcher # Model Watcher specific
```

Run specific markers:
```bash
pytest -m "unit and not slow"
pytest -m "integration or functional"
pytest -m memory_server
```

## Continuous Integration

### Pre-commit Testing
```bash
# Fast test suite for development
python tests/run_tests.py --unit --timeout 60
```

### Full Testing Pipeline
```bash
# Complete test suite for CI/CD
python tests/run_tests.py --all --coverage --performance
```

### Quality Gates
- **Unit Tests**: 100% pass rate required
- **Coverage**: > 80% required
- **Integration**: > 90% pass rate required
- **Performance**: All thresholds must be met

## Troubleshooting

### Common Issues

#### Import Errors
```bash
# Ensure project root is in Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### Port Conflicts
```bash
# Check for port conflicts
lsof -i :8090 -i :8091
```

#### Model File Issues
```bash
# Verify test models directory
ls -la tests/fixtures/test_models/
```

#### Permission Issues
```bash
# Fix permissions
chmod -R 755 tests/
```

### Debug Mode
```bash
# Run with verbose logging
python tests/run_tests.py --all --verbose

# Run single test with debugging
pytest tests/unit/test_startup_script.py::TestAIServerManager::test_manager_initialization -v -s
```

## Best Practices

### Test Organization
- One test file per source file
- Group related tests in classes
- Use descriptive test names
- Keep tests independent

### Mocking Strategy
- Mock external dependencies
- Use real objects for internal components
- Mock I/O operations and network calls
- Keep mocks simple and focused

### Performance
- Run fast tests first
- Use parallel execution for independent tests
- Cache expensive setups
- Clean up resources properly

### Maintenance
- Update tests when code changes
- Remove obsolete tests
- Keep test data current
- Document complex test scenarios