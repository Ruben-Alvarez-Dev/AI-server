#!/usr/bin/env python3
"""
Simple test for async system using simplified worker
"""

import sys
import os
import tempfile
import time
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

def test_simple_worker():
    """Test the simple worker"""
    print("🧪 Testing simple async worker...")
    
    try:
        from workers.simple_document_worker import simple_process_document, test_task
        
        # First, test simple task
        print("📝 Testing simple task...")
        result = test_task.apply_async()
        result.get(timeout=10)  # Wait up to 10 seconds
        print("✅ Simple task completed")
        
        # Now test document processing
        print("📄 Testing document processing...")
        
        # Create test content
        test_content = """# Simple Test Document

This is a simple test for the async document processing system.

## Content
- Line 1
- Line 2  
- Line 3

End of document.
"""
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(test_content)
            temp_path = f.name
        
        print(f"📁 Created test file: {temp_path}")
        
        # Process with simple worker
        result = simple_process_document.apply_async(
            args=[temp_path, 'simple_test.md'],
            kwargs={'workspace': 'test_simple'}
        )
        
        print(f"🚀 Task queued: {result.id}")
        
        # Monitor progress
        timeout = 15
        start_time = time.time()
        
        while not result.ready() and (time.time() - start_time) < timeout:
            status = result.status
            print(f"   Status: {status}")
            
            if status == 'PROCESSING' and result.info:
                info = result.info
                current = info.get('current', 'Processing...')
                progress = info.get('progress', 0)
                print(f"   Progress: {progress}% - {current}")
            
            time.sleep(1)
        
        # Check result
        if result.ready():
            if result.successful():
                doc_result = result.result
                print("✅ Document processed successfully!")
                print(f"   Document ID: {doc_result.get('document_id')}")
                print(f"   Workspace: {doc_result.get('workspace')}")
                return True
            else:
                print(f"❌ Task failed: {result.result}")
                return False
        else:
            print("⏰ Task timeout")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🚀 Simple Async System Test")
    print("=" * 30)
    
    success = test_simple_worker()
    
    if success:
        print("\n✅ Simple async system is working!")
    else:
        print("\n❌ Test failed")
    
    return success

if __name__ == "__main__":
    main()