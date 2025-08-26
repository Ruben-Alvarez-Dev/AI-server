"""
Unit Tests for Async Components
Tests individual components in isolation
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from workers.simple_document_worker import simple_process_document
from core.celery_app import celery_app


class TestAsyncWorkers:
    """Unit tests for async workers"""
    
    def test_simple_worker_task_registration(self):
        """Test that worker tasks are properly registered"""
        inspect = celery_app.control.inspect()
        registered_tasks = inspect.registered()
        
        # Should have at least one worker
        assert registered_tasks is not None, "No registered tasks found"
        assert len(registered_tasks) > 0, "No workers with registered tasks"
        
        # Check for required tasks
        all_tasks = []
        for worker_tasks in registered_tasks.values():
            all_tasks.extend(worker_tasks)
        
        required_tasks = [
            'simple_process_document',
            'test_task'
        ]
        
        for task in required_tasks:
            assert task in all_tasks, f"Required task '{task}' not registered"
    
    def test_document_processing_logic(self):
        """Test document processing logic without Celery"""
        # Create test document
        test_content = """# Unit Test Document

This is a test document for unit testing the processing logic.

## Content
- Item 1
- Item 2
- Item 3

End of test document.
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(test_content)
            temp_path = f.name
        
        try:
            # Mock the update_state method since we're testing outside Celery context
            with patch.object(simple_process_document, 'update_state') as mock_update:
                # Execute the task function directly
                result = simple_process_document.run(
                    temp_path,
                    'unit_test.md',
                    workspace='unit_test'
                )
                
                # Verify result structure
                assert isinstance(result, dict), "Result should be dictionary"
                assert result['status'] == 'success', "Processing should succeed"
                assert 'document_id' in result, "Should generate document ID"
                assert result['filename'] == 'unit_test.md', "Should preserve filename"
                assert result['workspace'] == 'unit_test', "Should use correct workspace"
                
                # Verify update_state was called
                assert mock_update.call_count > 0, "Should update state during processing"
                
                # Check final state update
                final_call = mock_update.call_args_list[-1]
                assert final_call[1]['state'] == 'SUCCESS', "Final state should be SUCCESS"
                
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_file_content_analysis(self):
        """Test file content analysis and metadata generation"""
        # Test different file types
        test_cases = [
            ("test.md", "# Markdown\nContent", "markdown"),
            ("test.py", "def hello():\n    print('world')", "python"),
            ("test.txt", "Plain text content", "text"),
            ("test.json", '{"key": "value"}', "json")
        ]
        
        for filename, content, expected_type in test_cases:
            with tempfile.NamedTemporaryFile(mode='w', suffix=Path(filename).suffix, delete=False) as f:
                f.write(content)
                temp_path = f.name
            
            try:
                with patch.object(simple_process_document, 'update_state'):
                    result = simple_process_document.run(
                        temp_path,
                        filename,
                        workspace='content_test'
                    )
                    
                    metadata = result.get('metadata', {})
                    assert 'word_count' in metadata, f"Missing word count for {filename}"
                    assert 'line_count' in metadata, f"Missing line count for {filename}"
                    assert metadata['word_count'] > 0, f"Invalid word count for {filename}"
                    assert metadata['line_count'] > 0, f"Invalid line count for {filename}"
                    
            finally:
                Path(temp_path).unlink(missing_ok=True)
    
    def test_error_handling(self):
        """Test error handling in worker"""
        # Test non-existent file
        with patch.object(simple_process_document, 'update_state') as mock_update:
            with pytest.raises(FileNotFoundError):
                simple_process_document.run(
                    '/nonexistent/file.txt',
                    'missing.txt',
                    workspace='error_test'
                )
            
            # Should have called update_state with FAILURE
            failure_calls = [call for call in mock_update.call_args_list 
                           if call[1].get('state') == 'FAILURE']
            assert len(failure_calls) > 0, "Should update state to FAILURE on error"
    
    def test_document_storage(self):
        """Test document storage functionality"""
        test_content = "Storage test content"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_path = f.name
        
        try:
            with patch.object(simple_process_document, 'update_state'):
                result = simple_process_document.run(
                    temp_path,
                    'storage_test.txt',
                    workspace='storage_test'
                )
                
                doc_id = result['document_id']
                workspace = result['workspace']
                
                # Check if files were created in expected location
                expected_dir = Path(__file__).parent.parent / 'data' / 'documents' / workspace
                doc_file = expected_dir / f"{doc_id}.txt"
                meta_file = expected_dir / f"{doc_id}.meta.json"
                
                assert doc_file.exists(), f"Document file not created: {doc_file}"
                assert meta_file.exists(), f"Metadata file not created: {meta_file}"
                
                # Verify content
                with open(doc_file, 'r') as f:
                    stored_content = f.read()
                assert stored_content == test_content, "Content mismatch in stored file"
                
                # Verify metadata
                with open(meta_file, 'r') as f:
                    metadata = json.load(f)
                assert metadata['document_id'] == doc_id, "Metadata document ID mismatch"
                assert metadata['original_name'] == 'storage_test.txt', "Metadata filename mismatch"
                
                # Cleanup test files
                doc_file.unlink(missing_ok=True)
                meta_file.unlink(missing_ok=True)
                
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestAsyncConfig:
    """Unit tests for async configuration"""
    
    def test_celery_config(self):
        """Test Celery configuration"""
        # Test broker URL
        assert 'redis://localhost:8801' in celery_app.conf.broker_url, "Wrong Redis broker URL"
        
        # Test task serialization
        assert celery_app.conf.task_serializer == 'json', "Should use JSON serialization"
        assert celery_app.conf.result_serializer == 'json', "Should use JSON result serialization"
        
        # Test task routing
        routes = celery_app.conf.task_routes
        assert isinstance(routes, dict), "Task routes should be configured"
    
    def test_redis_config(self):
        """Test Redis configuration"""
        import redis
        
        # Test connection parameters
        r = redis.Redis(host='localhost', port=8801, db=0)
        
        # Test basic operations
        test_key = 'test_async_config'
        test_value = 'test_value'
        
        r.set(test_key, test_value)
        retrieved = r.get(test_key)
        r.delete(test_key)
        
        assert retrieved.decode() == test_value, "Redis basic operations failed"


class TestAsyncSchemas:
    """Unit tests for async API schemas"""
    
    def test_schema_imports(self):
        """Test that schemas can be imported correctly"""
        from api.schemas.async_schemas import (
            AsyncDocumentUploadResponse,
            AsyncBatchUploadResponse,
            TaskStatusResponse,
            AsyncHealthResponse,
            AsyncStatsResponse
        )
        
        # Basic validation that classes exist and are BaseModel subclasses
        from pydantic import BaseModel
        
        schemas = [
            AsyncDocumentUploadResponse,
            AsyncBatchUploadResponse, 
            TaskStatusResponse,
            AsyncHealthResponse,
            AsyncStatsResponse
        ]
        
        for schema_class in schemas:
            assert issubclass(schema_class, BaseModel), f"{schema_class.__name__} should be BaseModel subclass"
    
    def test_response_schema_validation(self):
        """Test response schema validation"""
        from api.schemas.async_schemas import AsyncDocumentUploadResponse, TaskStatus
        
        # Valid response data
        valid_data = {
            "success": True,
            "task_id": "test-123",
            "workspace": "test",
            "processing_status": "queued",
            "message": "Test message",
            "estimated_completion": "2025-08-26T18:30:00Z",
            "check_status_url": "/status/test-123"
        }
        
        # Should validate successfully
        response = AsyncDocumentUploadResponse(**valid_data)
        assert response.success is True
        assert response.task_id == "test-123"
        
        # Test TaskStatus enum
        assert TaskStatus.PENDING == "PENDING"
        assert TaskStatus.PROCESSING == "PROCESSING"
        assert TaskStatus.SUCCESS == "SUCCESS"
        assert TaskStatus.FAILURE == "FAILURE"


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "-s"])