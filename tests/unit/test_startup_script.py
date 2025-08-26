"""
Unit tests for AI-Server startup script (bin/start_ai_server.py)
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, call
from pathlib import Path
import sys
import subprocess

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from tests.test_config import TestConfig


class TestAIServerManager:
    """Test the AIServerManager class functionality"""
    
    @pytest.fixture
    def manager(self):
        """Create AIServerManager instance for testing"""
        # Mock the project root and import
        with patch('sys.path'):
            # Import here to avoid issues during test collection
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "start_ai_server", 
                project_root / "bin" / "start_ai_server.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module.AIServerManager()
    
    def test_manager_initialization(self, manager):
        """Test AIServerManager initializes correctly"""
        assert manager.project_root is not None
        assert isinstance(manager.processes, list)
        assert isinstance(manager.threads, list)
        assert len(manager.processes) == 0
        assert len(manager.threads) == 0
    
    @patch('subprocess.Popen')
    def test_start_memory_server_success(self, mock_popen, manager):
        """Test memory server starts successfully"""
        # Mock successful process
        mock_process = MagicMock()
        mock_popen.return_value = mock_process
        
        result = manager.start_memory_server()
        
        assert result is True
        assert len(manager.processes) == 1
        
        # Verify subprocess call
        mock_popen.assert_called_once()
        call_args = mock_popen.call_args
        assert "python3" in call_args[0][0]
        assert "-m" in call_args[0][0]
        assert "uvicorn" in call_args[0][0]
        assert "api.main:app" in call_args[0][0]
        assert "--port" in call_args[0][0]
        assert "8001" in call_args[0][0]
    
    @patch('subprocess.Popen')
    def test_start_memory_server_failure(self, mock_popen, manager):
        """Test memory server start failure"""
        # Mock failed process
        mock_popen.side_effect = Exception("Process failed")
        
        result = manager.start_memory_server()
        
        assert result is False
        assert len(manager.processes) == 0
    
    @patch('subprocess.Popen')
    def test_start_llm_server_success(self, mock_popen, manager):
        """Test LLM server starts successfully"""
        # Mock successful process
        mock_process = MagicMock()
        mock_popen.return_value = mock_process
        
        result = manager.start_llm_server()
        
        assert result is True
        assert len(manager.processes) == 1
        
        # Verify subprocess call
        mock_popen.assert_called_once()
        call_args = mock_popen.call_args
        assert "python3" in call_args[0][0]
        assert "server/main.py" in call_args[0][0]
    
    @patch('subprocess.Popen')
    def test_start_llm_server_failure(self, mock_popen, manager):
        """Test LLM server start failure"""
        # Mock failed process
        mock_popen.side_effect = Exception("Process failed")
        
        result = manager.start_llm_server()
        
        assert result is False
        assert len(manager.processes) == 0
    
    @patch('services.model_watcher.auto_start.start_watcher_background')
    def test_start_model_watcher_success(self, mock_start_watcher, manager):
        """Test model watcher starts successfully"""
        # Mock successful watcher start
        mock_thread = MagicMock()
        mock_start_watcher.return_value = mock_thread
        
        result = manager.start_model_watcher()
        
        assert result is True
        assert len(manager.threads) == 1
        mock_start_watcher.assert_called_once()
    
    @patch('services.model_watcher.auto_start.start_watcher_background')
    def test_start_model_watcher_failure(self, mock_start_watcher, manager):
        """Test model watcher start failure"""
        # Mock failed watcher start
        mock_start_watcher.side_effect = ImportError("Module not found")
        
        result = manager.start_model_watcher()
        
        assert result is False
        assert len(manager.threads) == 0
    
    @patch('requests.get')
    @patch('time.sleep')
    def test_check_services_health_success(self, mock_sleep, mock_get, manager):
        """Test services health check when all healthy"""
        # Mock successful health responses
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # Should not raise any exceptions
        manager.check_services_health()
        
        # Verify health checks were made
        expected_calls = [
            call("http://localhost:8001/health/status", timeout=5),
            call("http://localhost:8000/health", timeout=5)
        ]
        mock_get.assert_has_calls(expected_calls)
    
    @patch('requests.get')
    @patch('time.sleep')
    def test_check_services_health_failure(self, mock_sleep, mock_get, manager):
        """Test services health check when services are down"""
        # Mock failed health responses
        mock_get.side_effect = Exception("Connection refused")
        
        # Should not raise any exceptions (errors are logged, not raised)
        manager.check_services_health()
        
        # Verify health checks were attempted
        assert mock_get.call_count == 2
    
    def test_shutdown(self, manager):
        """Test manager shutdown process"""
        # Add mock processes
        mock_process1 = MagicMock()
        mock_process2 = MagicMock()
        manager.processes = [mock_process1, mock_process2]
        
        with pytest.raises(SystemExit):
            manager.shutdown()
        
        # Verify processes were terminated
        mock_process1.terminate.assert_called_once()
        mock_process1.wait.assert_called_once()
        mock_process2.terminate.assert_called_once()
        mock_process2.wait.assert_called_once()


class TestMainFunctions:
    """Test module-level functions"""
    
    @patch('pathlib.Path.mkdir')
    @patch.object(sys, 'argv', ['start_ai_server.py'])
    def test_main_function(self, mock_mkdir):
        """Test main function execution"""
        # Mock the AIServerManager to avoid actual startup
        with patch('start_ai_server.AIServerManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            
            # Import and test main function
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "start_ai_server", 
                project_root / "bin" / "start_ai_server.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Mock start_all to avoid infinite loop
            with patch.object(mock_manager, 'start_all'):
                module.main()
            
            # Verify manager was created and started
            mock_manager_class.assert_called_once()
            mock_manager.start_all.assert_called_once()
            
            # Verify models directory creation was attempted
            mock_mkdir.assert_called()


class TestProcessManagement:
    """Test process management functionality"""
    
    def test_process_list_management(self):
        """Test process list is managed correctly"""
        # This would test the actual process management
        # Implementation depends on how processes are tracked
        pass
    
    def test_thread_list_management(self):
        """Test thread list is managed correctly"""  
        # This would test the actual thread management
        # Implementation depends on how threads are tracked
        pass


class TestErrorHandling:
    """Test error handling scenarios"""
    
    def test_import_error_handling(self):
        """Test handling of import errors"""
        # Test scenarios where imports fail
        pass
    
    def test_subprocess_error_handling(self):
        """Test handling of subprocess errors"""
        # Test scenarios where subprocess.Popen fails
        pass
    
    def test_network_error_handling(self):
        """Test handling of network/health check errors"""
        # Test scenarios where health checks fail
        pass