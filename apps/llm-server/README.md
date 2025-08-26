# LLM Server - AI Development Orchestration

High-performance AI development server optimized for M1 Ultra with specialized agents and workflow orchestration.

## Features

🎯 **Multi-Agent Orchestra**: 6 specialized AI agents working in coordination
- **Router**: Ultra-fast request routing (Qwen2-1.5B)
- **Architect**: System design and planning (Qwen2.5-32B)  
- **Primary Coder**: High-performance coding (Qwen2.5-Coder-7B)
- **Secondary Coder**: Backup coding with MoE efficiency (DeepSeek-Coder-V2-16B)
- **QA Checker**: Quality assurance and testing (Qwen2.5-14B)
- **Debugger**: Error analysis and debugging (DeepSeek-Coder-V2-16B)

⚡ **M1 Ultra Optimization**: 
- Metal GPU acceleration with llama.cpp
- Optimized for 64 GPU cores and 128GB unified memory
- Model pooling and efficient resource management

🔄 **LangGraph Workflows**:
- **Development**: Comprehensive development workflow
- **Quick Fix**: Rapid debugging and issue resolution  
- **Code Review**: Thorough code analysis and QA

## Quick Start

1. **Install and Setup**:
```bash
# Run the setup script
python llm-server/scripts/setup.py

# Or manual setup:
pip install -r requirements.txt
python llm-server/scripts/install_llama_cpp.py
python llm-server/scripts/download_models.py
```

2. **Configure**:
```bash
# Copy environment file
cp .env.example .env

# Edit configuration as needed
vim .env
```

3. **Run Server**:
```bash
# Start the server
python -m llm_server.server.main

# Or with uvicorn directly
uvicorn llm_server.server.main:app --host 0.0.0.0 --port 8000
```

4. **Access API**:
- API Documentation: http://localhost:8000/docs  
- Health Check: http://localhost:8000/health
- System Stats: http://localhost:8000/monitoring/stats

## API Usage

### Execute Development Workflow
```bash
curl -X POST "http://localhost:8000/workflows/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "request": "Create a REST API for user management",
    "workflow_type": "development",
    "context": {"language": "python", "framework": "fastapi"}
  }'
```

### Quick Fix Workflow  
```bash
curl -X POST "http://localhost:8000/workflows/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "request": "Fix this error: TypeError: cannot serialize object",
    "workflow_type": "quick_fix"
  }'
```

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   LangGraph      │    │   Specialized   │
│   Server        │───▶│   Workflows      │───▶│   AI Agents     │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Monitoring    │    │   Resource       │    │   llama.cpp     │
│   & Metrics     │    │   Management     │    │   Metal GPU     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Model Requirements

Total estimated storage: ~50GB

- Router: qwen2-1_5b-instruct-q6_k.gguf (~1.2GB)
- Architect: qwen2.5-32b-instruct-q6_k.gguf (~22GB)  
- Primary Coder: qwen2.5-coder-7b-instruct-q6_k.gguf (~5.8GB)
- Secondary Coder: deepseek-coder-v2-lite-instruct-q6_k.gguf (~10.5GB)
- QA Checker: qwen2.5-14b-instruct-q6_k.gguf (~10.2GB)
- Debugger: deepseek-coder-v2-lite-instruct-q6_k.gguf (~10.5GB)

## Performance

Expected performance on M1 Ultra:
- Router: 50+ tokens/second
- Other agents: 15-25 tokens/second average
- Memory usage: ~65-70GB (of 128GB available)
- Concurrent requests: Up to 10 workflows simultaneously

## Development

```bash
# Install development dependencies
pip install -r requirements.txt

# Run with auto-reload
uvicorn llm_server.server.main:app --reload

# Run tests (when available)
pytest
```

## Contributing

This is an M1 Ultra optimized AI development orchestration system. Contributions welcome!

## License

MIT License - see LICENSE file for details.