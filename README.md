# 🤖 AI-SERVER

**Multi-Agent AI Development System with RAG & M1 Ultra Optimization**

*Advanced LLM server with virtual models, RAG integration, and multimodal support*

---

## 🚀 Quick Start

```bash
# Start all services (R2R + LLM Server)
./start_servers.sh

# Start CLI interface (Open Interpreter)
./start_cli.sh

# Test the system
curl http://localhost:8000/health
```

---

## 🏗️ System Architecture

```
AI-server/
├── 📡 llm-server/          # LLM Server with 4 virtual models
├── 🧠 R2R/                 # RAG system for enhanced context  
├── 🖥️  open-interpreter/    # CLI interface
├── 🛠️  tools/              # Utilities (web-scrapper, etc.)
├── 📚 docs/               # Complete documentation
├── ⚡ start_servers.sh    # Start R2R + LLM server
└── 🎯 start_cli.sh        # Start CLI interface
```

## 🎯 Virtual Models

| Model | Purpose | Optimized For |
|-------|---------|---------------|
| `cline-optimized` | Cline IDE integration | PLAN/ACT modes, multimodal |
| `openai-compatible` | 100% OpenAI standard | Pure API compatibility |
| `multimodal-enhanced` | Text + Docs + Images | Complex multimodal analysis |
| `thinking-enabled` | Reasoning mode | Always-on `<thinking>` tags |

## ⚡ Key Features

- **🎭 4 Virtual Models**: Specialized for different use cases
- **🧠 RAG Integration**: R2R system for 2M+ effective context
- **📷 Multimodal**: Text + Documents + Images processing
- **🔥 M1 Ultra Optimized**: Metal acceleration, 55+ tokens/sec
- **🔌 OpenAI Compatible**: Full API compatibility
- **🎯 Cline Ready**: Perfect integration with Cline IDE

## 📡 API Endpoints

### Main Server
- **Base URL**: `http://localhost:8000`
- **Health**: `/health`
- **Models**: `/v1/models`
- **Chat**: `/v1/chat/completions`
- **Docs**: `/docs`

### RAG System  
- **Base URL**: `http://localhost:7272`
- **Health**: `/health`

## 🔧 Configuration for Cline

```json
{
  "cline.apiProvider": "openai-compatible",
  "cline.openaiCompatible.baseUrl": "http://localhost:8000/v1",
  "cline.openaiCompatible.apiKey": "sk-llmserver-local-development-key-12345678",
  "cline.openaiCompatible.modelId": "cline-optimized"
}
```

## 🛠️ Tools & Utilities

- **Web-Scrapper**: Documentation scraping for RAG (`tools/web-scrapper/`)
- **Open Interpreter**: Advanced CLI interface with AI-Server integration
- **R2R RAG**: Knowledge retrieval and augmentation system

## 📚 Documentation

Complete documentation available in [`docs/`](./docs/):

- [📖 System Architecture](./docs/AI-SERVER-ARCHITECTURE.md)
- [🤖 LLM Server](./docs/LLM-SERVER.md)
- [🧠 RAG Integration](./docs/R2R-INTEGRATION.md)
- [🎯 Virtual Models](./docs/VIRTUAL-MODELS.md)
- [🔌 API Reference](./docs/API-ENDPOINTS.md)
- [⚙️ Installation](./docs/INSTALLATION.md)

## 🎪 System Requirements

- **macOS**: M1 Ultra optimized (works on other M1/M2)
- **RAM**: 64GB+ recommended (128GB optimal)
- **Python**: 3.8+
- **Docker**: Latest version
- **Metal**: GPU acceleration enabled

## 🔄 Development Workflow

1. **Start Services**: `./start_servers.sh`
2. **Configure Cline**: Use `cline-optimized` model
3. **Develop**: Use PLAN/ACT modes with full context
4. **CLI Access**: `./start_cli.sh` for terminal interaction
5. **RAG Enhancement**: Add docs via web-scrapper

## 🚨 Troubleshooting

### Common Issues
- **Port 8000 in use**: Script will attempt to free it
- **R2R startup fails**: Check Docker is running
- **Model not found**: Ensure models are in `llm-server/models/`

### Health Checks
```bash
curl http://localhost:8000/health    # LLM Server
curl http://localhost:7272/health    # R2R System
```

## 🔗 Integration Examples

### cURL
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-llmserver-local-development-key-12345678" \
  -d '{"model":"cline-optimized","messages":[{"role":"user","content":"Hello!"}]}'
```

### Python
```python
import openai

client = openai.OpenAI(
    api_key="sk-llmserver-local-development-key-12345678",
    base_url="http://localhost:8000/v1"
)

response = client.chat.completions.create(
    model="cline-optimized",
    messages=[{"role": "user", "content": "Hello AI!"}]
)
```

---

**Version**: 2.0  
**License**: MIT  
**Optimized For**: M1 Ultra, Cline IDE, RAG-enhanced development