# 🗺️ Memory-Server Endpoint Mapping
**Updated Architecture**: Async-first with Hub Centralized Embeddings

## 🎯 Primary Endpoints (Active)

### **Async Processing** (Recommended)
```http
BASE_URL: http://localhost:8001/api/v1/async

POST   /upload                    # Async single document upload  
POST   /upload-batch              # Async batch document upload
GET    /status/{task_id}          # Check task processing status
GET    /health                    # Async system health check  
GET    /stats                     # Processing performance stats
DELETE /task/{task_id}            # Cancel pending task
```

### **Core Services**
```http
BASE_URL: http://localhost:8001/api/v1

GET    /workspaces               # List all workspaces
POST   /workspaces/{name}        # Create new workspace
GET    /documents/{workspace}    # List documents in workspace
DELETE /documents/{workspace}/{id} # Delete specific document
POST   /search                   # Search documents
```

### **System & Health**
```http
BASE_URL: http://localhost:8001

GET    /health                   # System health check
GET    /health/detailed          # Detailed health metrics
GET    /                        # API information
```

## 🔄 Redirect Endpoints

### **Auto-Redirect to Async**
```http
POST   /api/v1/upload            # → Redirects to /async/upload
POST   /api/v1/upload-batch      # → Redirects to /async/upload-batch
```
*Returns 301 with redirect information and usage instructions*

## 🏚️ Legacy Endpoints (Deprecated)

### **Synchronous Processing** (Compatibility Only)
```http
⚠️  DEPRECATED - Use async versions instead

POST   /api/v1/upload-sync       # LEGACY: Blocking single upload
POST   /api/v1/upload-batch-sync # LEGACY: Blocking batch upload
```

## 🧠 Embedding Services

### **Centralized Hub** (Active)
```http
BASE_URL: http://localhost:8900

POST   /embed/late-chunking      # Document processing agent
POST   /embed/code               # Code analysis agent  
POST   /embed/conversation       # Dialogue processing agent
POST   /embed/visual             # Image/UI analysis agent
POST   /embed/query              # Search optimization agent
POST   /embed/community          # Graph clustering agent

GET    /health                   # Hub health status
GET    /status                   # Detailed hub information
```

### **Specialized Services** (Reserved)
```http
🔒 RESERVED FOR FUTURE USE

http://localhost:8111            # Late-chunking service
http://localhost:8112            # Code service  
http://localhost:8113            # Conversation service
http://localhost:8114            # Visual service
http://localhost:8115            # Query service
http://localhost:8116            # Community service
```

## 🔧 System Monitoring

### **Flower Dashboard**
```http
BASE_URL: http://localhost:8811

GET    /                        # Main dashboard
GET    /api/workers             # Worker status API
GET    /api/tasks               # Task status API
```

### **Redis Queue**
```http
Connection: localhost:8801
Databases:
  0: Celery broker (task queue)
  1: Celery results backend  
  2-15: Available for expansion
```

## 📊 Request/Response Examples

### **Async Upload**
```bash
# Request
curl -X POST http://localhost:8001/api/v1/async/upload \
  -F "file=@document.pdf" \
  -F "workspace=research" \
  -F "tags=async,test"

# Response  
{
  "success": true,
  "task_id": "abc123...",
  "workspace": "research", 
  "processing_status": "queued",
  "message": "Document queued for processing",
  "check_status_url": "/api/v1/async/status/abc123..."
}
```

### **Status Check**
```bash
# Request
curl http://localhost:8001/api/v1/async/status/abc123...

# Response (Processing)
{
  "task_id": "abc123...",
  "status": "PROCESSING", 
  "ready": false,
  "progress": 65,
  "current": "Generating embeddings",
  "meta": {
    "filename": "document.pdf",
    "workspace": "research"
  }
}

# Response (Completed)
{
  "task_id": "abc123...",
  "status": "SUCCESS",
  "ready": true, 
  "result": {
    "document_id": "doc_a1b2c3",
    "filename": "document.pdf",
    "workspace": "research",
    "message": "Document processed successfully"
  }
}
```

### **Redirect Response**
```bash
# Request  
curl -X POST http://localhost:8001/api/v1/upload

# Response (301)
{
  "message": "Upload endpoint has moved to async processing",
  "redirect_to": "/api/v1/async/upload", 
  "reason": "Better performance and no blocking",
  "documentation": "Use POST /api/v1/async/upload for uploading documents"
}
```

## 🎯 Client Integration

### **Python Example**
```python
import requests
import time

# Async upload
response = requests.post(
    'http://localhost:8001/api/v1/async/upload',
    files={'file': open('doc.pdf', 'rb')},
    data={'workspace': 'research'}
)

task_id = response.json()['task_id']

# Check status
while True:
    status = requests.get(f'http://localhost:8001/api/v1/async/status/{task_id}')
    if status.json()['ready']:
        break
    time.sleep(1)

print("Document processed:", status.json()['result'])
```

### **JavaScript Example**
```javascript
// Async upload
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('workspace', 'research');

const response = await fetch('/api/v1/async/upload', {
    method: 'POST',
    body: formData
});

const {task_id} = await response.json();

// Poll status
const checkStatus = async () => {
    const status = await fetch(`/api/v1/async/status/${task_id}`);
    const data = await status.json();
    
    if (data.ready) {
        console.log('Done:', data.result);
    } else {
        setTimeout(checkStatus, 1000);
    }
};

checkStatus();
```

## 🔐 Security & Rate Limiting

### **Current Settings**
- **Rate Limiting**: 100 requests/minute per client
- **File Size Limit**: 50MB per file
- **Concurrent Tasks**: Unlimited (queue-based)
- **Task Timeout**: 5 minutes per document

### **Authentication**
```http
# Optional API Key (if configured)
Headers:
  Authorization: Bearer {API_KEY}
  X-API-Key: {API_KEY}
```

## 🎛️ Configuration

### **Environment Variables**
```bash
REDIS_URL=redis://localhost:8801
MEMORY_SERVER_HOST=localhost  
MEMORY_SERVER_PORT=8001
EMBEDDING_HUB_HOST=localhost
EMBEDDING_HUB_PORT=8900
FLOWER_PORT=8810
```

### **Feature Flags**
```python
# In core/config.py
USE_ASYNC_PROCESSING=True      # Enable async endpoints
USE_EMBEDDING_HUB=True         # Use centralized hub  
ENABLE_LEGACY_ENDPOINTS=True   # Keep sync endpoints for compatibility
REDIRECT_SYNC_TO_ASYNC=True    # Auto-redirect old endpoints
```

---

**🎯 This mapping reflects the current async-first architecture with centralized embeddings and reserved expansion paths.**