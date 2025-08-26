# Installation Documentation

**Getting AI-Server running locally on your machine**

*Simple Python-based installation for local development and testing.*

---

## 📋 Installation Methods

### 🚀 Quick Start (Recommended)
- **[01_quick-start.md](01_quick-start.md)** - Get running in 5 minutes
- Best for: First-time users, demos, basic usage

### 🔧 Development Setup
- **[02_local-development.md](02_local-development.md)** - Full development environment
- Best for: Contributors, customization, debugging

### 📊 System Requirements
- **[03_system-requirements.md](03_system-requirements.md)** - Hardware and software needs
- **[04_troubleshooting.md](04_troubleshooting.md)** - Common installation issues

---

## 🎯 Simple Installation Flow

```
1. Check Requirements → 2. Clone Repository → 3. Run Setup → 4. Start Services
```

---

## ⚡ Prerequisites

Before installing, ensure you have:
- **Operating System**: macOS 12+ (M1/M2/M3 optimized) or Linux
- **Python**: 3.8 or higher
- **RAM**: 16GB minimum (32GB recommended)
- **Storage**: 100GB available space for models
- **Network**: Internet connection for initial model downloads

---

## 🔧 What You'll Get

### Local Services
- **LLM Server**: `http://localhost:8000` - Chat completions API
- **Memory Server**: `http://localhost:8001` - Document search and ingestion
- **Model Watcher**: Background service for model management

### File Structure
- **`bin/`**: Executable scripts to start/stop services
- **`apps/`**: Core applications (LLM + Memory servers)
- **`assets/models/`**: AI models storage
- **`tools/`**: Development utilities and CLI tools

---

## 🔐 Security Notes

- All services run locally by default (no external connections)
- Local API keys generated automatically
- Model files stored locally (no telemetry)
- Firewall: Only local ports 8000-8001 used

---

## 🚀 Roadmap (Future Features)

*These features are planned but not yet implemented:*

- **Docker Support**: Containerized deployment
- **Cloud Deployment**: AWS/GCP deployment guides  
- **Kubernetes**: Production orchestration
- **Multi-node Setup**: Distributed deployment

---

**Next**: After installation, learn how to use the system in [User Manual](../03_user_manual/)