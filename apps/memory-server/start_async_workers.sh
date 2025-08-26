#!/bin/bash

# 🚀 Start Celery Workers for Memory-Server Async Processing
# This script starts all necessary components for async document processing

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Memory-Server Async Workers...${NC}"
echo "=============================================="

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Check if we're in the right directory
if [ ! -f "$SCRIPT_DIR/core/celery_app.py" ]; then
    echo -e "${RED}❌ Error: celery_app.py not found. Please run from memory-server directory.${NC}"
    exit 1
fi

# Activate virtual environment if it exists
if [ -f "$PROJECT_ROOT/venv/bin/activate" ]; then
    echo -e "${YELLOW}🔧 Activating virtual environment...${NC}"
    source "$PROJECT_ROOT/venv/bin/activate"
    echo -e "${GREEN}✅ Virtual environment activated${NC}"
else
    echo -e "${YELLOW}⚠️  No virtual environment found, using global Python${NC}"
fi

# Check Redis connection
echo -e "\n${YELLOW}🔍 Checking Redis connection...${NC}"
if redis-cli ping &> /dev/null; then
    echo -e "${GREEN}✅ Redis is running${NC}"
else
    echo -e "${RED}❌ Redis is not running. Starting Redis...${NC}"
    if command -v brew &> /dev/null; then
        brew services start redis
        sleep 2
        if redis-cli ping &> /dev/null; then
            echo -e "${GREEN}✅ Redis started successfully${NC}"
        else
            echo -e "${RED}❌ Failed to start Redis. Please start it manually.${NC}"
            exit 1
        fi
    else
        echo -e "${RED}❌ Please start Redis manually: redis-server${NC}"
        exit 1
    fi
fi

# Set Python path to include project root
export PYTHONPATH="$PROJECT_ROOT:$SCRIPT_DIR:$PYTHONPATH"
echo -e "${YELLOW}🔧 PYTHONPATH set to: $PYTHONPATH${NC}"

# Change to memory-server directory
cd "$SCRIPT_DIR"

# Check Celery installation and configuration
echo -e "\n${YELLOW}🔍 Testing Celery configuration...${NC}"
python -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')
try:
    from apps.memory_server.core.celery_app import celery_app
    print('✅ Celery configuration loaded successfully')
    print(f'   Broker: {celery_app.conf.broker_url}')
    print(f'   Backend: {celery_app.conf.result_backend}')
except Exception as e:
    print(f'❌ Error loading Celery configuration: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Celery configuration test failed${NC}"
    exit 1
fi

# Create log directory
LOG_DIR="$SCRIPT_DIR/data/logs"
mkdir -p "$LOG_DIR"

# Function to start a service with proper logging
start_service() {
    local service_name="$1"
    local command="$2"
    local log_file="$LOG_DIR/${service_name}.log"
    local pid_file="$LOG_DIR/${service_name}.pid"
    
    echo -e "${YELLOW}🚀 Starting $service_name...${NC}"
    
    # Start service in background
    nohup $command > "$log_file" 2>&1 &
    local pid=$!
    
    # Save PID
    echo $pid > "$pid_file"
    
    # Wait a bit and check if process is still running
    sleep 2
    if kill -0 $pid 2>/dev/null; then
        echo -e "${GREEN}✅ $service_name started (PID: $pid)${NC}"
        echo "   Log: $log_file"
        echo "   PID: $pid_file"
    else
        echo -e "${RED}❌ Failed to start $service_name${NC}"
        echo "   Check log: $log_file"
        return 1
    fi
}

# Start Celery Worker for document processing
echo -e "\n${BLUE}📄 Starting Document Processing Worker...${NC}"
start_service "celery-worker-documents" \
    "celery -A core.celery_app worker --loglevel=info --concurrency=4 --pool=prefork --hostname=documents@%h --queues=documents,default"

# Start Celery Worker for embeddings
echo -e "\n${BLUE}🧮 Starting Embeddings Processing Worker...${NC}"
start_service "celery-worker-embeddings" \
    "celery -A core.celery_app worker --loglevel=info --concurrency=2 --pool=prefork --hostname=embeddings@%h --queues=embeddings"

# Start Flower for monitoring
echo -e "\n${BLUE}🌸 Starting Flower Monitoring Dashboard...${NC}"
start_service "flower-monitor" \
    "celery -A core.celery_app flower --port=8811 --broker=redis://localhost:8801/0"

# Wait a bit for services to fully start
echo -e "\n${YELLOW}⏳ Waiting for services to initialize...${NC}"
sleep 5

# Check worker status
echo -e "\n${YELLOW}🔍 Checking worker status...${NC}"
python -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')
try:
    from apps.memory_server.core.celery_app import celery_app
    
    inspect = celery_app.control.inspect()
    active_workers = inspect.active()
    
    if active_workers:
        print('✅ Active workers found:')
        for worker, tasks in active_workers.items():
            print(f'   - {worker}: {len(tasks)} active tasks')
    else:
        print('⚠️  No active workers found (they may still be starting up)')
        
    # Check queues
    reserved = inspect.reserved()
    if reserved:
        total_reserved = sum(len(tasks) for tasks in reserved.values())
        print(f'📋 Reserved tasks: {total_reserved}')
    
except Exception as e:
    print(f'❌ Error checking worker status: {e}')
"

echo -e "\n${GREEN}=============================================="
echo -e "✨ Memory-Server Async Workers Started! ✨"
echo -e "==============================================${NC}"

echo -e "\n${BLUE}📊 Service URLs:${NC}"
echo "  • Flower Monitoring: http://localhost:8811"
echo "  • Memory-Server API: http://localhost:8001" 
echo "  • New async endpoints: http://localhost:8001/api/v1/async/"

echo -e "\n${BLUE}📋 Available Endpoints:${NC}"
echo "  • POST /api/v1/async/upload         - Upload single document (async)"
echo "  • POST /api/v1/async/upload-batch   - Upload multiple documents (async)"
echo "  • GET  /api/v1/async/status/{task_id} - Check task status"
echo "  • GET  /api/v1/async/health         - Check async system health"
echo "  • GET  /api/v1/async/stats          - Get processing statistics"

echo -e "\n${BLUE}🔧 Management Commands:${NC}"
echo "  • Check workers: celery -A core.celery_app inspect active"
echo "  • Check queues:  celery -A core.celery_app inspect reserved"
echo "  • Purge queues:  celery -A core.celery_app purge"

echo -e "\n${BLUE}📁 Log Files:${NC}"
echo "  • Document Worker: $LOG_DIR/celery-worker-documents.log"
echo "  • Embeddings Worker: $LOG_DIR/celery-worker-embeddings.log"
echo "  • Flower Monitor: $LOG_DIR/flower-monitor.log"

echo -e "\n${YELLOW}🛑 To stop all services:${NC}"
echo "  pkill -f celery"
echo "  pkill -f flower"

echo -e "\n${GREEN}🎉 System ready for high-volume async document processing!${NC}"

# Create a simple test file for user to try
cat > test_async_upload.py << 'EOF'
#!/usr/bin/env python3
"""
Simple test script for async document upload
"""

import requests
import time
import json

def test_async_upload():
    # Test file content
    test_content = "This is a test document for async processing."
    
    # Create test file
    files = {'file': ('test_doc.txt', test_content, 'text/plain')}
    data = {
        'workspace': 'test',
        'auto_summarize': True,
        'tags': 'test,async'
    }
    
    print("🚀 Testing async document upload...")
    
    # Upload document
    response = requests.post(
        'http://localhost:8001/api/v1/async/upload',
        files=files,
        data=data
    )
    
    if response.status_code == 200:
        result = response.json()
        task_id = result['task_id']
        print(f"✅ Document uploaded successfully!")
        print(f"   Task ID: {task_id}")
        
        # Check status
        print("\n📊 Checking task status...")
        for i in range(10):  # Check for up to 30 seconds
            status_response = requests.get(f'http://localhost:8001/api/v1/async/status/{task_id}')
            if status_response.status_code == 200:
                status = status_response.json()
                print(f"   Status: {status['status']} - {status.get('current', 'N/A')}")
                
                if status['ready']:
                    if status['status'] == 'SUCCESS':
                        print(f"✅ Document processed successfully!")
                        print(f"   Document ID: {status['result']['document_id']}")
                    else:
                        print(f"❌ Processing failed: {status.get('error', 'Unknown error')}")
                    break
            time.sleep(3)
        else:
            print("⏳ Processing is taking longer than expected...")
    
    else:
        print(f"❌ Upload failed: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_async_upload()
EOF

chmod +x test_async_upload.py

echo -e "\n${YELLOW}🧪 Test the system:${NC}"
echo "  python test_async_upload.py"