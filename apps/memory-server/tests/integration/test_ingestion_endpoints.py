#!/usr/bin/env python3
"""
Test Ingestion Endpoints for Memory-Server
Tests the document ingestion system with real API calls
"""

import os
import sys
import asyncio
import tempfile
from pathlib import Path
import json
import requests
import time

# Test configuration
BASE_URL = "http://localhost:8001"
TEST_FILES_DIR = Path(__file__).parent / "test_files"

def create_test_files():
    """Create test files for ingestion testing"""
    TEST_FILES_DIR.mkdir(exist_ok=True)
    
    # Python code file
    python_file = TEST_FILES_DIR / "sample_code.py"
    python_file.write_text("""
def fibonacci(n):
    \"\"\"Generate Fibonacci sequence up to n terms\"\"\"
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
    
    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])
    
    return fib

if __name__ == "__main__":
    print("Fibonacci sequence:")
    result = fibonacci(10)
    print(result)
""")
    
    # Markdown documentation
    md_file = TEST_FILES_DIR / "documentation.md"
    md_file.write_text("""
# Memory-Server Documentation

## Overview
Memory-Server is a next-generation RAG system that incorporates state-of-the-art 2025 techniques:

- **LazyGraphRAG**: Zero-cost graph indexing with 1000x cost reduction
- **Late Chunking**: Context-preserving embeddings before chunking
- **Hybrid Retrieval**: Vector + Graph fusion for optimal results
- **Agentic RAG**: Multi-turn reasoning capabilities

## Quick Start

1. Install dependencies
2. Configure your API keys
3. Start the server
4. Begin ingesting documents

## API Endpoints

### Document Upload
```bash
curl -X POST "http://localhost:8001/api/v1/documents/upload" \
  -F "file=@document.pdf" \
  -F "workspace=research"
```

### Web Scraping
```bash
curl -X POST "http://localhost:8001/api/v1/documents/scrape-web" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "workspace": "research"}'
```
""")
    
    # JSON configuration
    json_file = TEST_FILES_DIR / "config.json"
    json_file.write_text(json.dumps({
        "api_settings": {
            "port": 8001,
            "host": "localhost",
            "debug": False
        },
        "memory_settings": {
            "working_memory_size": 131072,
            "episodic_memory_size": 2097152,
            "semantic_memory_unlimited": True
        },
        "models": {
            "embedding_model": "jinaai/jina-embeddings-v2-base-en",
            "colbert_model": "jinaai/jina-colbert-v2",
            "reranker_model": "cross-encoder/ms-marco-MiniLM-L-6-v2"
        }
    }, indent=2))
    
    print(f"✅ Test files created in {TEST_FILES_DIR}")
    return [python_file, md_file, json_file]

def test_server_health():
    """Test if server is running and healthy"""
    try:
        response = requests.get(f"{BASE_URL}/health/status", timeout=5)
        if response.status_code == 200:
            print("✅ Server is healthy and responding")
            return True
        else:
            print(f"⚠️  Server responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server - is it running?")
        print(f"   Make sure Memory-Server is running on {BASE_URL}")
        return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_workspaces_endpoint():
    """Test workspaces listing endpoint"""
    try:
        print("\n📋 Testing workspaces endpoint...")
        response = requests.get(f"{BASE_URL}/api/v1/documents/workspaces")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {len(data['workspaces'])} workspaces:")
            for workspace in data['workspaces']:
                count = data['total_documents'].get(workspace, 0)
                print(f"   - {workspace}: {count} documents")
            print(f"   Active workspace: {data['active_workspace']}")
            return True
        else:
            print(f"❌ Workspaces request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Workspaces test failed: {e}")
        return False

def test_document_upload():
    """Test single document upload"""
    try:
        print("\n📤 Testing document upload...")
        test_files = create_test_files()
        
        # Upload Python file
        python_file = test_files[0]
        
        with open(python_file, 'rb') as f:
            files = {'file': (python_file.name, f, 'text/plain')}
            data = {
                'workspace': 'code',
                'auto_summarize': True,
                'tags': 'python,fibonacci,algorithm'
            }
            
            response = requests.post(
                f"{BASE_URL}/api/v1/documents/upload",
                files=files,
                data=data,
                timeout=30
            )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Document uploaded successfully!")
            print(f"   Document ID: {result['document_id']}")
            print(f"   Workspace: {result['workspace']}")
            print(f"   Status: {result['processing_status']}")
            return True
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Document upload test failed: {e}")
        return False

def test_batch_upload():
    """Test batch document upload"""
    try:
        print("\n📦 Testing batch upload...")
        test_files = create_test_files()
        
        files_to_upload = []
        for test_file in test_files:
            files_to_upload.append(
                ('files', (test_file.name, open(test_file, 'rb'), 'text/plain'))
            )
        
        data = {
            'workspace': 'research',
            'auto_summarize': True,
            'tags': 'test,batch,documentation'
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/documents/upload-batch",
            files=files_to_upload,
            data=data,
            timeout=60
        )
        
        # Close file handles
        for _, (_, file_handle, _) in files_to_upload:
            file_handle.close()
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Batch upload completed!")
            print(f"   Total files: {result['total_files']}")
            print(f"   Processed: {result['processed']}")
            print(f"   Failed: {result['failed']}")
            if result['errors']:
                print(f"   Errors: {result['errors']}")
            return result['failed'] == 0
        else:
            print(f"❌ Batch upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Batch upload test failed: {e}")
        return False

def test_folder_processing():
    """Test folder processing"""
    try:
        print("\n📁 Testing folder processing...")
        
        request_data = {
            "folder_path": str(TEST_FILES_DIR),
            "workspace": "projects",
            "recursive": True,
            "file_patterns": ["*.py", "*.md", "*.json"],
            "exclude_patterns": [".git", "__pycache__"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/documents/process-folder",
            json=request_data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Folder processing completed!")
            print(f"   Total files: {result['total_files']}")
            print(f"   Processed: {result['processed']}")
            print(f"   Failed: {result['failed']}")
            return result['processed'] > 0
        else:
            print(f"❌ Folder processing failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Folder processing test failed: {e}")
        return False

def test_web_scraping():
    """Test web scraping functionality"""
    try:
        print("\n🌐 Testing web scraping...")
        
        request_data = {
            "url": "https://httpbin.org/html",  # Simple test page
            "workspace": "research",
            "max_pages": 1,
            "include_pdfs": False,
            "include_external": False
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/documents/scrape-web",
            json=request_data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Web scraping completed!")
            print(f"   URL: {result['url']}")
            print(f"   Pages scraped: {result['pages_scraped']}")
            print(f"   Document ID: {result['document_id']}")
            return True
        else:
            print(f"❌ Web scraping failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Web scraping test failed: {e}")
        return False

def test_workspace_creation():
    """Test workspace creation"""
    try:
        print("\n🏗️  Testing workspace creation...")
        
        workspace_name = "test_workspace"
        description = "Test workspace created by integration test"
        
        response = requests.post(
            f"{BASE_URL}/api/v1/documents/workspace/{workspace_name}",
            params={"description": description},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Workspace created successfully!")
            print(f"   Name: {result['workspace']}")
            print(f"   Message: {result['message']}")
            return True
        else:
            print(f"❌ Workspace creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Workspace creation test failed: {e}")
        return False

def test_ingestion_stats():
    """Test ingestion statistics endpoint"""
    try:
        print("\n📊 Testing ingestion stats...")
        
        response = requests.get(f"{BASE_URL}/api/v1/documents/stats")
        
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Statistics retrieved:")
            print(f"   Documents processed: {stats.get('documents_processed', 0)}")
            print(f"   Total chunks: {stats.get('total_chunks_created', 0)}")
            print(f"   Processing time: {stats.get('total_processing_time', 0):.2f}s")
            print(f"   Errors: {stats.get('errors', 0)}")
            return True
        else:
            print(f"❌ Stats request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Stats test failed: {e}")
        return False

def cleanup_test_files():
    """Clean up test files"""
    try:
        if TEST_FILES_DIR.exists():
            import shutil
            shutil.rmtree(TEST_FILES_DIR)
        print("🧹 Test files cleaned up")
    except Exception as e:
        print(f"⚠️  Error cleaning up test files: {e}")

def main():
    """Run all ingestion tests"""
    print("🧪 Memory-Server Ingestion Tests")
    print("=" * 50)
    
    tests = [
        ("Server Health", test_server_health),
        ("Workspaces Endpoint", test_workspaces_endpoint),
        ("Workspace Creation", test_workspace_creation),
        ("Document Upload", test_document_upload),
        ("Batch Upload", test_batch_upload),
        ("Folder Processing", test_folder_processing),
        ("Web Scraping", test_web_scraping),
        ("Ingestion Stats", test_ingestion_stats)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n🔧 Running: {test_name}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                failed += 1
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            failed += 1
            print(f"💥 {test_name} CRASHED: {e}")
        
        time.sleep(1)  # Brief pause between tests
    
    print("\n" + "=" * 50)
    print(f"📊 INGESTION TEST RESULTS:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    # Clean up
    cleanup_test_files()
    
    if failed == 0:
        print("\n🎉 ALL INGESTION TESTS PASSED! 🎉")
        print("✨ Memory-Server ingestion system is working correctly!")
        return True
    else:
        print(f"\n⚠️  {failed} tests failed.")
        print("💡 Check server logs and ensure Memory-Server is running properly.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)