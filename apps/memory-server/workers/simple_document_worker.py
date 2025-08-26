"""
Simplified Document Processing Worker  
For testing the async system without complex dependencies
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.celery_app import celery_app

# Simple logger
def log_info(message):
    print(f"[INFO] {time.strftime('%H:%M:%S')} - {message}")

def log_error(message):
    print(f"[ERROR] {time.strftime('%H:%M:%S')} - {message}")

@celery_app.task(bind=True, name='simple_process_document')
def simple_process_document(
    self,
    file_path: str,
    original_name: str,
    workspace: str = 'test',
    **kwargs
) -> Dict[str, Any]:
    """
    Simple document processor for testing
    """
    try:
        log_info(f"Processing document: {original_name}")
        
        # Update task state - Starting
        self.update_state(
            state='PROCESSING',
            meta={
                'current': 'Reading file',
                'filename': original_name,
                'progress': 20
            }
        )
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        log_info(f"Read {len(content)} characters from {original_name}")
        
        # Update state - Processing
        self.update_state(
            state='PROCESSING',
            meta={
                'current': 'Analyzing content',
                'filename': original_name,
                'progress': 50
            }
        )
        
        # Simulate processing time
        time.sleep(2)
        
        # Simple analysis
        word_count = len(content.split())
        line_count = len(content.splitlines())
        
        # Generate simple document ID
        import hashlib
        doc_id = f"doc_{hashlib.md5(content.encode()).hexdigest()[:8]}"
        
        # Update state - Storing
        self.update_state(
            state='PROCESSING',
            meta={
                'current': 'Storing document',
                'filename': original_name,
                'progress': 80,
                'document_id': doc_id
            }
        )
        
        # Create simple metadata
        metadata = {
            'document_id': doc_id,
            'original_name': original_name,
            'workspace': workspace,
            'word_count': word_count,
            'line_count': line_count,
            'file_size': len(content),
            'processed_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Simulate storage
        storage_dir = Path(__file__).parent.parent / 'data' / 'documents' / workspace
        storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Save document
        doc_file = storage_dir / f"{doc_id}.txt"
        meta_file = storage_dir / f"{doc_id}.meta.json"
        
        with open(doc_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        log_info(f"Document stored: {doc_file}")
        
        # Clean up temp file
        if file_path.startswith('/tmp/') or 'tmp' in file_path:
            try:
                os.unlink(file_path)
                log_info(f"Cleaned up temp file: {file_path}")
            except:
                pass
        
        # Final state
        self.update_state(
            state='SUCCESS',
            meta={
                'current': 'Complete',
                'progress': 100,
                'document_id': doc_id,
                'filename': original_name
            }
        )
        
        log_info(f"Successfully processed {original_name} -> {doc_id}")
        
        return {
            'status': 'success',
            'document_id': doc_id,
            'filename': original_name,
            'workspace': workspace,
            'metadata': metadata,
            'message': f'Document {original_name} processed successfully'
        }
        
    except Exception as e:
        log_error(f"Error processing {original_name}: {e}")
        
        self.update_state(
            state='FAILURE',
            meta={
                'error': str(e),
                'filename': original_name,
                'error_type': type(e).__name__
            }
        )
        raise

@celery_app.task(name='test_task')
def test_task():
    """Simple test task"""
    log_info("Test task started")
    time.sleep(1)
    log_info("Test task completed")
    return {"status": "success", "message": "Test task completed"}

if __name__ == "__main__":
    print("Simple document worker loaded")
    print("Available tasks:")
    print("  - simple_process_document")
    print("  - test_task")