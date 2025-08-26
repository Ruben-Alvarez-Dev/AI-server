"""
Integration Tests for Async Document Processing
Tests the complete flow: Upload → Queue → Processing → Status → Result
"""

import asyncio
import pytest
import tempfile
import json
import time
from pathlib import Path
from httpx import AsyncClient
from fastapi.testclient import TestClient

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.main import app
from core.config import get_config
from workers.simple_document_worker import simple_process_document


class TestAsyncIntegration:
    """Integration tests for async document processing system"""
    
    @pytest.fixture
    def client(self):
        """Test client fixture"""
        return TestClient(app)
    
    @pytest.fixture
    def sample_document(self):
        """Create sample document for testing"""
        content = """# Integration Test Document
        
This is a comprehensive test document for the async processing system.

## Features Tested
- Document upload via async API
- Task queue processing 
- Status tracking
- Result retrieval
- Error handling

## Content Analysis
The system should detect this as a markdown document and process it accordingly.
It should generate appropriate embeddings and store the document in the specified workspace.

## Expected Results
- Document ID generated
- Chunks created for vector search
- Embeddings generated via hub
- Document searchable in workspace
"""
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            return f.name, content, 'integration_test.md'
    
    def test_redis_connection(self):
        """Test Redis connection is working"""
        import redis
        
        try:
            r = redis.Redis(host='localhost', port=8801, db=0)
            r.ping()
            assert True, "Redis connection successful"
        except Exception as e:
            pytest.fail(f"Redis connection failed: {e}")
    
    def test_celery_workers_available(self):
        """Test Celery workers are active"""
        try:
            from core.celery_app import celery_app
            
            inspect = celery_app.control.inspect()
            active_workers = inspect.active()
            
            assert active_workers is not None, "No workers available"
            assert len(active_workers) > 0, "No active workers found"
            
            # Check specific tasks are registered
            registered = inspect.registered()
            assert registered is not None, "No registered tasks"
            
            for worker, tasks in registered.items():
                assert 'simple_process_document' in tasks, f"Required task not found in {worker}"
                
        except Exception as e:
            pytest.fail(f"Celery worker check failed: {e}")
    
    def test_async_upload_endpoint(self, client, sample_document):
        """Test async upload endpoint returns task ID"""
        temp_path, content, filename = sample_document
        
        try:
            with open(temp_path, 'rb') as f:
                response = client.post(
                    "/api/v1/async/upload",
                    files={"file": (filename, f, "text/markdown")},
                    data={
                        "workspace": "integration_test",
                        "auto_summarize": False,
                        "tags": "integration,test,async"
                    }
                )
            
            # Check response structure
            assert response.status_code == 200, f"Upload failed: {response.text}"
            
            data = response.json()
            assert data["success"] is True, "Upload not successful"
            assert "task_id" in data, "No task ID returned"
            assert data["workspace"] == "integration_test", "Wrong workspace"
            assert data["processing_status"] == "queued", "Wrong initial status"
            assert "/status/" in data["check_status_url"], "No status URL"
            
            return data["task_id"]
            
        finally:
            # Cleanup
            Path(temp_path).unlink(missing_ok=True)
    
    def test_task_status_tracking(self, client, sample_document):
        """Test task status tracking through completion"""
        temp_path, content, filename = sample_document
        
        try:
            # Upload document
            with open(temp_path, 'rb') as f:
                upload_response = client.post(
                    "/api/v1/async/upload",
                    files={"file": (filename, f, "text/markdown")},
                    data={"workspace": "integration_test"}
                )
            
            assert upload_response.status_code == 200
            task_id = upload_response.json()["task_id"]
            
            # Track status until completion
            max_wait = 30  # 30 seconds max
            start_time = time.time()
            final_status = None
            
            while time.time() - start_time < max_wait:
                status_response = client.get(f"/api/v1/async/status/{task_id}")
                assert status_response.status_code == 200, "Status check failed"
                
                status_data = status_response.json()
                assert status_data["task_id"] == task_id, "Wrong task ID"
                
                current_status = status_data["status"]
                
                if status_data["ready"]:
                    final_status = status_data
                    break
                    
                # Check intermediate statuses are valid
                assert current_status in ["PENDING", "PROCESSING"], f"Invalid status: {current_status}"
                
                if current_status == "PROCESSING":
                    assert "current" in status_data, "No current step info"
                    assert isinstance(status_data.get("progress", 0), int), "Invalid progress"
                
                time.sleep(1)
            
            # Verify final status
            assert final_status is not None, "Task did not complete in time"
            assert final_status["status"] == "SUCCESS", f"Task failed: {final_status.get('error', 'Unknown error')}"
            assert final_status["ready"] is True, "Task not marked as ready"
            
            # Verify result structure
            result = final_status.get("result")
            assert result is not None, "No result data"
            assert "document_id" in result, "No document ID in result"
            assert result["filename"] == filename, "Wrong filename in result"
            assert result["workspace"] == "integration_test", "Wrong workspace in result"
            
            return result["document_id"]
            
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_batch_upload(self, client):
        """Test batch upload functionality"""
        # Create multiple test files
        files_data = []
        temp_files = []
        
        try:
            for i in range(3):
                content = f"""# Batch Test Document {i+1}
                
This is batch test document number {i+1}.
It should be processed independently but in parallel.

Content: Document {i+1} with unique identifier {i+1}.
"""
                with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
                    f.write(content)
                    temp_files.append(f.name)
                    files_data.append(f.name)
            
            # Upload batch
            files = [
                ("files", (f"batch_test_{i}.md", open(temp_file, 'rb'), "text/markdown"))
                for i, temp_file in enumerate(temp_files)
            ]
            
            response = client.post(
                "/api/v1/async/upload-batch",
                files=files,
                data={
                    "workspace": "batch_test",
                    "auto_summarize": False,
                    "tags": "batch,integration,test"
                }
            )
            
            # Close file handles
            for _, (_, file_handle, _) in files:
                file_handle.close()
            
            # Check response
            assert response.status_code == 200, f"Batch upload failed: {response.text}"
            
            data = response.json()
            assert data["success"] is True, "Batch upload not successful"
            assert data["total_files"] == 3, "Wrong number of files"
            assert len(data["task_ids"]) == 3, "Wrong number of task IDs"
            assert data["workspace"] == "batch_test", "Wrong workspace"
            
            # Wait for all tasks to complete
            task_ids = data["task_ids"]
            completed_tasks = []
            
            max_wait = 60  # 1 minute for batch
            start_time = time.time()
            
            while len(completed_tasks) < len(task_ids) and time.time() - start_time < max_wait:
                for task_id in task_ids:
                    if task_id not in completed_tasks:
                        status_response = client.get(f"/api/v1/async/status/{task_id}")
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            if status_data["ready"]:
                                completed_tasks.append(task_id)
                
                time.sleep(2)
            
            # Verify all completed successfully
            assert len(completed_tasks) == len(task_ids), f"Only {len(completed_tasks)}/{len(task_ids)} tasks completed"
            
            return task_ids
            
        finally:
            # Cleanup
            for temp_file in temp_files:
                Path(temp_file).unlink(missing_ok=True)
    
    def test_health_check(self, client):
        """Test async health check endpoint"""
        response = client.get("/api/v1/async/health")
        assert response.status_code == 200, "Health check failed"
        
        data = response.json()
        assert data["async_processing"] is True, "Async processing not available"
        assert data["redis_connection"] is True, "Redis not connected"
        assert data["workers_available"] is True, "Workers not available"
        assert isinstance(data["active_workers"], list), "Invalid active workers format"
        assert len(data["active_workers"]) > 0, "No active workers"
    
    def test_stats_endpoint(self, client):
        """Test async stats endpoint"""
        response = client.get("/api/v1/async/stats")
        assert response.status_code == 200, "Stats endpoint failed"
        
        data = response.json()
        assert data["celery_available"] is True, "Celery not available"
        assert isinstance(data["workers"], int), "Invalid workers count"
        assert data["workers"] > 0, "No workers reported"
        assert isinstance(data["total_processed"], int), "Invalid processed count"
        assert isinstance(data["active_tasks"], int), "Invalid active tasks count"
    
    def test_redirect_endpoints(self, client):
        """Test that old endpoints redirect properly"""
        # Test upload redirect
        upload_response = client.post("/api/v1/upload")
        assert upload_response.status_code == 301, "Upload redirect failed"
        
        data = upload_response.json()
        assert "/async/upload" in data["redirect_to"], "Wrong redirect URL"
        assert "async processing" in data["message"], "Wrong redirect message"
        
        # Test batch redirect
        batch_response = client.post("/api/v1/upload-batch")
        assert batch_response.status_code == 301, "Batch redirect failed"
        
        batch_data = batch_response.json()
        assert "/async/upload-batch" in batch_data["redirect_to"], "Wrong batch redirect URL"
    
    def test_error_handling(self, client):
        """Test error handling in async system"""
        # Test invalid task ID
        response = client.get("/api/v1/async/status/invalid-task-id")
        assert response.status_code == 200, "Should handle invalid task ID gracefully"
        
        data = response.json()
        assert data["status"] == "PENDING", "Invalid task should show as PENDING"
        
        # Test file too large (if configured)
        # This test depends on MAX_FILE_SIZE configuration
        
        # Test invalid file type
        response = client.post(
            "/api/v1/async/upload",
            files={"file": ("test.exe", b"fake executable content", "application/octet-stream")},
            data={"workspace": "error_test"}
        )
        
        # Should still accept but may process differently
        assert response.status_code in [200, 413, 400], "Error handling issue"
    
    def test_concurrent_uploads(self, client):
        """Test system handles concurrent uploads without blocking"""
        import threading
        import queue
        
        results = queue.Queue()
        errors = queue.Queue()
        
        def upload_document(doc_num):
            try:
                content = f"# Concurrent Test {doc_num}\nThis is document {doc_num} for concurrency testing."
                
                with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
                    f.write(content)
                    temp_path = f.name
                
                try:
                    with open(temp_path, 'rb') as f:
                        response = client.post(
                            "/api/v1/async/upload",
                            files={"file": (f"concurrent_{doc_num}.md", f, "text/markdown")},
                            data={"workspace": "concurrent_test"}
                        )
                    
                    assert response.status_code == 200, f"Concurrent upload {doc_num} failed"
                    data = response.json()
                    results.put(data["task_id"])
                    
                finally:
                    Path(temp_path).unlink(missing_ok=True)
                    
            except Exception as e:
                errors.put((doc_num, str(e)))
        
        # Start 5 concurrent uploads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=upload_document, args=(i,))
            thread.start()
            threads.append(thread)
        
        # Wait for all to complete
        for thread in threads:
            thread.join(timeout=30)
        
        # Check results
        assert errors.empty(), f"Concurrent upload errors: {list(errors.queue)}"
        assert results.qsize() == 5, f"Only {results.qsize()}/5 uploads succeeded"


# Pytest configuration
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment"""
    # Ensure Redis and Celery are running
    import redis
    
    try:
        r = redis.Redis(host='localhost', port=8801, db=0)
        r.ping()
    except Exception as e:
        pytest.skip(f"Redis not available for testing: {e}")
    
    try:
        from core.celery_app import celery_app
        inspect = celery_app.control.inspect()
        if not inspect.active():
            pytest.skip("No Celery workers available for testing")
    except Exception as e:
        pytest.skip(f"Celery not available for testing: {e}")


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "-s"])