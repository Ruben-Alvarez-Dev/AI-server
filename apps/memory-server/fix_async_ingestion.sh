#!/bin/bash

# 🚀 Script de Corrección Rápida - Sistema de Ingesta Asíncrona
# Autor: Rubén Álvarez
# Fecha: 2025-08-26

set -e  # Exit on error

echo "🔧 Memory-Server Async Fix - Starting..."
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${YELLOW}⚠️  Warning: This script is optimized for macOS${NC}"
fi

# Step 1: Check and Install Redis
echo -e "\n${GREEN}Step 1: Checking Redis installation...${NC}"
if command -v redis-cli &> /dev/null; then
    echo "✅ Redis is installed"
    
    # Check if Redis is running
    if redis-cli ping &> /dev/null; then
        echo "✅ Redis is running"
    else
        echo "Starting Redis..."
        brew services start redis 2>/dev/null || redis-server --daemonize yes
        sleep 2
        if redis-cli ping &> /dev/null; then
            echo "✅ Redis started successfully"
        else
            echo -e "${RED}❌ Failed to start Redis${NC}"
            exit 1
        fi
    fi
else
    echo "Redis not found. Installing..."
    if command -v brew &> /dev/null; then
        brew install redis
        brew services start redis
        echo "✅ Redis installed and started"
    else
        echo -e "${RED}❌ Homebrew not found. Please install Redis manually${NC}"
        exit 1
    fi
fi

# Step 2: Install Python dependencies
echo -e "\n${GREEN}Step 2: Installing Python dependencies...${NC}"
cd /Users/server/AI-projects/AI-server

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo -e "${YELLOW}⚠️  No virtual environment found, using global Python${NC}"
fi

# Install required packages
pip install -q redis==5.0.1 celery==5.3.4 flower==2.0.1 aioredis==2.0.1
echo "✅ Python packages installed"

# Step 3: Create Celery configuration
echo -e "\n${GREEN}Step 3: Creating Celery configuration...${NC}"

# Create celery_app.py
cat > apps/memory-server/core/celery_app.py << 'EOF'
"""
Celery Configuration for Memory-Server
Async task processing with Redis
"""

from celery import Celery
import os

# Create Celery instance
celery_app = Celery(
    'memory_server',
    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/1'),
    include=['workers.document_worker', 'workers.embedding_worker']
)

# Configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max per task
    task_soft_time_limit=240,  # Warning at 4 minutes
    worker_prefetch_multiplier=1,  # One task at a time per worker
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks (memory management)
    task_acks_late=True,  # Acknowledge task after completion
    task_reject_on_worker_lost=True,  # Requeue tasks if worker dies
)

# Beat schedule for periodic tasks (if needed)
celery_app.conf.beat_schedule = {
    'cleanup-temp-files': {
        'task': 'workers.maintenance.cleanup_temp_files',
        'schedule': 3600.0,  # Every hour
    },
}

print("✅ Celery configured with Redis broker")
EOF

echo "✅ Celery configuration created"

# Step 4: Create workers directory structure
echo -e "\n${GREEN}Step 4: Creating workers structure...${NC}"

mkdir -p apps/memory-server/workers
touch apps/memory-server/workers/__init__.py

# Create document worker
cat > apps/memory-server/workers/document_worker.py << 'EOF'
"""
Document Processing Worker
Handles async document ingestion
"""

from celery import Task
import asyncio
from typing import Dict, Any
import logging
from core.celery_app import celery_app

logger = logging.getLogger(__name__)

class DocumentIngestionTask(Task):
    """Task with persistent document processor"""
    _processor = None
    
    @property
    def processor(self):
        if self._processor is None:
            from api.utils.document_processor import DocumentProcessor
            self._processor = DocumentProcessor()
        return self._processor

@celery_app.task(base=DocumentIngestionTask, bind=True, name='process_document')
def process_document(self, file_path: str, original_name: str, **kwargs) -> Dict[str, Any]:
    """
    Process document asynchronously
    
    Args:
        file_path: Path to temporary file
        original_name: Original filename
        **kwargs: Additional processing options
    
    Returns:
        Processing result with document_id
    """
    try:
        # Update task state
        self.update_state(
            state='PROCESSING',
            meta={
                'current': 'Analyzing document',
                'filename': original_name,
                'progress': 10
            }
        )
        
        # Run async processing in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Process document
            doc_id = loop.run_until_complete(
                self.processor.process_file(
                    file_path=file_path,
                    original_name=original_name,
                    **kwargs
                )
            )
            
            self.update_state(
                state='SUCCESS',
                meta={
                    'current': 'Complete',
                    'progress': 100,
                    'document_id': doc_id
                }
            )
            
            return {
                'status': 'success',
                'document_id': doc_id,
                'message': f'Document {original_name} processed successfully'
            }
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error processing document {original_name}: {e}")
        self.update_state(
            state='FAILURE',
            meta={
                'error': str(e),
                'filename': original_name
            }
        )
        raise

@celery_app.task(name='batch_process_documents')
def batch_process_documents(file_paths: list, workspace: str = 'research'):
    """Process multiple documents in batch"""
    results = []
    for file_path, original_name in file_paths:
        task = process_document.delay(file_path, original_name, workspace=workspace)
        results.append({
            'filename': original_name,
            'task_id': task.id
        })
    return results
EOF

echo "✅ Workers created"

# Step 5: Create startup script
echo -e "\n${GREEN}Step 5: Creating startup script...${NC}"

cat > apps/memory-server/start_async_workers.sh << 'EOF'
#!/bin/bash

# Start Celery Workers for Memory-Server

echo "🚀 Starting Memory-Server Async Workers..."

# Check Redis
if ! redis-cli ping &> /dev/null; then
    echo "❌ Redis is not running. Please start Redis first."
    exit 1
fi

# Start Celery worker
echo "Starting Celery worker..."
celery -A core.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --pool=prefork \
    --hostname=memory_worker@%h \
    --queues=default,documents,embeddings \
    &

# Start Flower for monitoring (optional)
echo "Starting Flower monitoring on http://localhost:8810..."
celery -A core.celery_app flower --port=8810 &

echo "✅ Workers started!"
echo ""
echo "📊 Monitor workers at: http://localhost:8810"
echo "🛑 To stop: pkill -f celery"
EOF

chmod +x apps/memory-server/start_async_workers.sh
echo "✅ Startup script created"

# Step 6: Test the setup
echo -e "\n${GREEN}Step 6: Testing setup...${NC}"

# Test Redis connection
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis connection: OK"
else
    echo -e "${RED}❌ Redis connection: FAILED${NC}"
    exit 1
fi

# Test Celery import
python -c "from apps.memory_server.core.celery_app import celery_app; print('✅ Celery import: OK')" 2>/dev/null || {
    echo -e "${YELLOW}⚠️  Celery import needs path adjustment${NC}"
}

# Create test task
python << 'PYTEST'
import sys
sys.path.insert(0, '/Users/server/AI-projects/AI-server')
try:
    from apps.memory_server.core.celery_app import celery_app
    
    @celery_app.task
    def test_task():
        return "Hello from Celery!"
    
    # Send test task
    result = test_task.delay()
    print(f"✅ Test task sent with ID: {result.id}")
except Exception as e:
    print(f"⚠️  Test task failed: {e}")
PYTEST

echo -e "\n${GREEN}=========================================${NC}"
echo -e "${GREEN}✨ Async Setup Complete!${NC}"
echo -e "${GREEN}=========================================${NC}"

echo -e "\n📋 Next Steps:"
echo "1. Start workers: cd apps/memory-server && ./start_async_workers.sh"
echo "2. Update API endpoints to use Celery tasks"
echo "3. Test with multiple file uploads"
echo "4. Monitor at http://localhost:5555"

echo -e "\n📊 Quick Test Commands:"
echo "  redis-cli ping                    # Test Redis"
echo "  celery -A core.celery_app status  # Check workers"
echo "  celery -A core.celery_app inspect active  # View active tasks"

echo -e "\n🔧 Configuration Files Created:"
echo "  - apps/memory-server/core/celery_app.py"
echo "  - apps/memory-server/workers/document_worker.py"
echo "  - apps/memory-server/start_async_workers.sh"

echo -e "\n${YELLOW}⚠️  Remember to update the API endpoints to use async tasks!${NC}"