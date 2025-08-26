#!/usr/bin/env python3
"""
Test script for the new async document processing system
Tests both the Celery workers and the FastAPI endpoints
"""

import sys
import os
from pathlib import Path
import tempfile
import time
import asyncio

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

def test_celery_directly():
    """Test Celery worker directly"""
    print("🧪 Testing Celery worker directly...")
    
    try:
        from core.celery_app import celery_app
        from workers.document_worker import process_document
        
        # Create test content
        test_content = """# Test Document

This is a test document for the async processing system.
It contains some basic markdown content to test the ingestion pipeline.

## Features to Test
- Document processing
- Async task handling  
- Status tracking
- Error handling

The system should be able to process this document without any issues.
"""
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(test_content)
            temp_path = f.name
        
        print(f"📁 Created test file: {temp_path}")
        
        # Send task to Celery
        print("🚀 Sending task to worker...")
        result = process_document.apply_async(
            args=[temp_path, 'test_async_document.md'],
            kwargs={
                'workspace': 'async_test',
                'auto_summarize': False,
                'tags': ['test', 'async', 'celery']
            }
        )
        
        print(f"✅ Task queued with ID: {result.id}")
        
        # Monitor task progress
        print("📊 Monitoring task progress...")
        timeout = 30  # 30 seconds timeout
        start_time = time.time()
        
        while not result.ready() and (time.time() - start_time) < timeout:
            print(f"   Status: {result.status}")
            if result.status == 'PROCESSING' and result.info:
                info = result.info
                current = info.get('current', 'Processing...')
                progress = info.get('progress', 0)
                print(f"   Progress: {progress}% - {current}")
            
            time.sleep(2)
        
        # Check final result
        if result.ready():
            if result.successful():
                doc_result = result.result
                print("✅ Document processed successfully!")
                print(f"   Document ID: {doc_result.get('document_id')}")
                print(f"   Status: {doc_result.get('status')}")
                print(f"   Message: {doc_result.get('message')}")
                return True
            else:
                print(f"❌ Task failed: {result.result}")
                return False
        else:
            print("⏰ Task timeout - may still be processing")
            return False
            
    except Exception as e:
        print(f"❌ Error in Celery test: {e}")
        return False
    finally:
        # Clean up
        try:
            if 'temp_path' in locals():
                os.unlink(temp_path)
                print(f"🧹 Cleaned up: {temp_path}")
        except:
            pass

def test_redis_connection():
    """Test Redis connection"""
    print("\n🔍 Testing Redis connection...")
    
    try:
        import redis
        
        # Test connection to our custom Redis instance
        r = redis.Redis(host='localhost', port=8801, db=0, decode_responses=True)
        
        # Test basic operations
        r.set('test_key', 'test_value')
        value = r.get('test_key')
        r.delete('test_key')
        
        if value == 'test_value':
            print("✅ Redis connection successful")
            
            # Check queue info
            queue_info = r.info()
            print(f"   Redis version: {queue_info.get('redis_version', 'unknown')}")
            print(f"   Connected clients: {queue_info.get('connected_clients', 0)}")
            return True
        else:
            print("❌ Redis test failed")
            return False
            
    except Exception as e:
        print(f"❌ Redis connection error: {e}")
        return False

def test_worker_status():
    """Test worker status"""
    print("\n👷 Testing worker status...")
    
    try:
        from core.celery_app import celery_app
        
        # Check worker status
        inspect = celery_app.control.inspect()
        
        # Get active workers
        active_workers = inspect.active()
        if active_workers:
            print(f"✅ Found {len(active_workers)} active workers:")
            for worker, tasks in active_workers.items():
                print(f"   - {worker}: {len(tasks)} active tasks")
            return True
        else:
            print("❌ No active workers found")
            return False
            
    except Exception as e:
        print(f"❌ Error checking workers: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 AI-Server Memory-Server Async System Test")
    print("=" * 50)
    
    # Run tests
    tests = [
        ("Redis Connection", test_redis_connection),
        ("Worker Status", test_worker_status),
        ("Celery Direct", test_celery_directly)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        print("-" * 30)
        success = test_func()
        results.append((test_name, success))
        print()
    
    # Summary
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Async system is ready!")
        print("\n🔗 Access points:")
        print("   • Flower Monitor: http://localhost:8810")
        print("   • Memory-Server API: http://localhost:8001")
        print("   • Redis: localhost:8801")
    else:
        print("⚠️  Some tests failed. Check the logs above.")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)