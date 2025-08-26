# Quick Start Guide

**Get AI-Server running in 5 minutes**

*The fastest way to get started with AI-Server for demos, testing, or first-time exploration.*

---

## ⚡ Prerequisites

- **macOS**: 12.0+ (M1/M2/M3 recommended)
- **RAM**: 16GB minimum
- **Storage**: 50GB free space
- **Python**: 3.8+

---

## 🚀 Installation Steps

### 1. Clone and Setup
```bash
# Clone the repository
git clone <repository-url> AI-server
cd AI-server

# Run setup script
./bin/setup.sh
```

### 2. Download a Model
```bash
# Download a basic model (example - replace with actual model)
mkdir -p assets/models/llm
cd assets/models/llm

# Download a lightweight model for testing
wget https://huggingface.co/model-url/resolve/main/model.gguf
```

### 3. Start the Services
```bash
# Start all services with one command
./bin/start_ai_server.py
```

You should see:
```
╔══════════════════════════════════════╗
║       AI-SERVER ECOSYSTEM v3.0       ║
╚══════════════════════════════════════╝

✅ Memory-Server starting on http://localhost:8001
✅ LLM-Server starting on http://localhost:8000  
✅ Model Watcher: Running in background
```

### 4. Test the Installation
```bash
# Test LLM Server
curl http://localhost:8000/health

# Test Memory Server
curl http://localhost:8001/health/status

# Test chat completion
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-llmserver-local" \
  -d '{
    "model": "cline-optimized",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

---

## 🎯 What You Have Now

### Running Services
- **LLM Server**: `http://localhost:8000` - AI chat completions
- **Memory Server**: `http://localhost:8001` - Document search and ingestion  
- **Model Watcher**: Background service monitoring your models

### Available Models
- `cline-optimized` - Best for IDE integration
- `openai-compatible` - Standard OpenAI API compatibility
- `multimodal-enhanced` - Text + image processing
- `thinking-enabled` - Advanced reasoning mode

---

## 🔧 IDE Integration (Optional)

### For Cline IDE
Add this to your Cline settings:
```json
{
  "cline.apiProvider": "openai-compatible",
  "cline.openaiCompatible.baseUrl": "http://localhost:8000/v1",
  "cline.openaiCompatible.apiKey": "sk-llmserver-local",
  "cline.openaiCompatible.modelId": "cline-optimized"
}
```

### For VS Code + Continue
```json
{
  "models": [{
    "title": "AI-Server Local",
    "provider": "openai",
    "model": "cline-optimized",
    "apiKey": "sk-llmserver-local",
    "apiBase": "http://localhost:8000/v1"
  }]
}
```

---

## 🚨 Common Issues

### Port Already in Use
```bash
# Kill processes on ports 8000/8001
lsof -ti:8000 | xargs kill
lsof -ti:8001 | xargs kill
```

### Model Not Found
- Ensure model files are in `assets/models/llm/`
- Check file permissions: `chmod 644 assets/models/llm/*.gguf`
- Restart services: `./bin/start_ai_server.py`

### Permission Denied
```bash
# Fix script permissions
chmod +x bin/*.sh bin/*.py

# Fix model directory permissions  
chmod -R 755 assets/models/
```

---

## ✅ Success Checklist

- [ ] Services start without errors
- [ ] Health checks return 200 OK
- [ ] Chat completion works
- [ ] Models are detected automatically
- [ ] IDE integration configured (optional)

---

## 📚 Next Steps

1. **[User Manual](../03_user_manual/)** - Learn to use the system effectively
2. **[System Architecture](../01_design/03_system-architecture.md)** - Understand how it works
3. **[API Documentation](../04_tooling/01_llm-server-api.md)** - Build integrations

---

**Need help?** Check [Common Issues](../03_user_manual/15_common-issues.md) or [Troubleshooting](08_troubleshooting.md)