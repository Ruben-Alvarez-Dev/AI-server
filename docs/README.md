# AI-Server Documentation

**Enterprise-Grade Multi-Service AI Platform Documentation**

*Complete technical documentation organized for different audiences and use cases.*

---

## 📚 Documentation Structure

This documentation follows an **enterprise flat structure** used by major tech companies like Google, Microsoft, and Meta. Each section is organized by audience and reading flow.

### 📖 Reading Path

```
01_design → 02_installation → 03_user_manual → 04_tooling
   ↓            ↓                ↓               ↓
Understand   Implement        Operate        Extend
```

---

## 🎯 Quick Navigation

### 🏗️ 01. Design Documentation
**Audience**: Architects, decision makers, new team members  
**Purpose**: Understand what AI-Server is and how it's designed

- [📋 Architecture Decisions](01_design/01_overview-architecture-decisions.md)
- [🏢 Project Structure](01_design/02_project-structure-guide.md)  
- [⚙️ System Architecture](01_design/03_system-architecture.md)
- [🧠 Memory System Design](01_design/04_memory-server-design.md)
- [🔬 Research Background](01_design/05_memory-server-research.md)

### ⚡ 02. Installation Documentation  
**Audience**: Users, developers  
**Purpose**: Get AI-Server running locally on your machine

- [🚀 Quick Start Guide](02_installation/01_quick-start.md) ← **Start here**
- [💻 Local Development](02_installation/02_local-development.md)
- [📊 System Requirements](02_installation/03_system-requirements.md)
- [🚨 Troubleshooting](02_installation/04_troubleshooting.md)

### 📖 03. User Manual
**Audience**: End users, operators  
**Purpose**: Learn to use AI-Server effectively

- [🎯 First Steps](03_user_manual/01_first-steps.md)
- [💬 Chat Completions](03_user_manual/03_chat-completions.md)
- [🧠 Memory Management](03_user_manual/06_memory-management.md)
- [🔧 IDE Integration](03_user_manual/09_cline-integration.md)
- [🚨 Troubleshooting](03_user_manual/15_common-issues.md)

### 🛠️ 04. Tooling Documentation
**Audience**: Developers, integrators  
**Purpose**: Build applications and integrations with AI-Server

- [📋 **Tools Master Index**](04_tooling/00_tools-index.md) ⭐ **← START HERE**
- [🔌 LLM Server API](04_tooling/01_llm-server-api.md)
- [🧠 Memory Server API](04_tooling/02_memory-server-api.md)
- [🐍 Python SDK](04_tooling/05_python-sdk.md)
- [🌐 JavaScript SDK](04_tooling/06_javascript-sdk.md)
- [🔧 CLI Tools](04_tooling/09_cli-tools.md)

**🏗️ Internal Tools (Complete Ecosystem):**
- [🔒 ATLAS - Automated Logging System](04_tooling/automated-logging-system.md)
- [💻 VSCode Activity Tracker](04_tooling/vscode-activity-tracker.md)
- [🌐 Web Scraper Tool](04_tooling/web-scraper.md)
- [🤖 CLI Interfaces (AI Assistants)](04_tooling/cli-interfaces.md)
- [🔌 MCP Servers](04_tooling/mcp-servers.md)
- [🎯 Model Watcher Service](04_tooling/model-watcher.md)

---

## 🚀 Getting Started

### New to AI-Server?
1. **Understand**: Read [Design Documentation](01_design/) to grasp the architecture
2. **Install**: Follow [Quick Start Guide](02_installation/01_quick-start.md) to get running
3. **Use**: Learn basic operations in [User Manual](03_user_manual/)
4. **Extend**: Build integrations with [Tooling Documentation](04_tooling/)

### Quick Installation
```bash
# Clone and setup
git clone <repository-url> AI-server
cd AI-server
./bin/setup.sh

# Start services  
./bin/start_ai_server.py

# Test installation
curl http://localhost:8000/health
```

---

## 🏗️ System Overview

AI-Server is an enterprise-grade multi-service AI platform featuring:

### Core Applications
- **LLM Server** (`apps/llm-server/`) - OpenAI-compatible chat completions
- **Memory Server** (`apps/memory-server/`) - LazyGraphRAG intelligent memory

### Support Services  
- **Model Watcher** (`services/model-watcher/`) - Automatic model management
- **Vector Database** (planned) - Scalable vector storage

### Development Tools
- **CLI Interfaces** (`tools/cli-interfaces/`) - Command-line AI assistants
- **VS Code Extension** (`tools/vscode-extension/`) - IDE integration
- **Web Scraper** (`tools/web-scraper/`) - Documentation ingestion
- **ATLAS** (`logs/`) - Automated logging & audit system 🔒

---

## 📊 Architecture Principles

### Local Multi-App Pattern
```
apps/         # User-facing applications (LLM + Memory servers)
services/     # Background support services (Model Watcher)  
tools/        # Development utilities (CLI tools, extensions)
bin/          # Executable scripts (startup/shutdown)
src/          # Shared libraries
assets/       # Resources (AI models, prompts, datasets)
```

### Design Philosophy
- **Local-first**: Runs entirely on your machine
- **Simple deployment**: Python scripts, no containers required
- **Modular architecture**: Independent services that work together

### Team Scalability
- Clear ownership boundaries
- Independent development cycles  
- Modular architecture for team growth

---

## 🎯 Key Features

### 🧠 Intelligent Memory (LazyGraphRAG)
- 1000x cost reduction vs traditional GraphRAG
- Context-preserving late chunking
- Multi-modal document processing

### 🔥 Performance Optimized
- **55+ tokens/sec** on M1 Ultra
- **<100ms** first token latency
- **128K native context** with unlimited extension

### 🔌 Universal Compatibility  
- 100% OpenAI API compatibility
- IDE integrations (Cline, Cursor, Continue)
- Multi-language SDKs (Python, JavaScript)

---

## 📈 Development Status

| Component | Status | Description |
|-----------|--------|-------------|
| LLM Server | ✅ Working | Local chat completions API |
| Memory Server | ✅ Working | Document search with LazyGraphRAG |
| Model Watcher | ✅ Working | Automatic model detection |
| CLI Tools | ✅ Working | Open Interpreter, OpenCode integration |
| VS Code Extension | ✅ Working | Development activity tracking |
| Web Scraper | ✅ Working | Documentation ingestion |
| **ATLAS Logging** | ✅ **Working** | **Automated audit trail & compliance** |
| System Health Monitor | 🔄 Planned | Component integrity monitoring |
| Web Dashboard | 🔄 Future | Management web interface |
| Docker Support | 🔄 Future | Containerized deployment |
| Cloud Deployment | 🔄 Future | AWS/GCP deployment options |

---

## 🤝 Contributing

We welcome contributions! Please start with:

1. [Design Documentation](01_design/) - Understand the architecture
2. [Local Development Setup](02_installation/02_local-development.md) - Get environment ready
3. [Contributing Guidelines](04_tooling/contributing.md) - Follow our standards

---

## 📞 Support

- **Quick Issues**: Check [Troubleshooting](03_user_manual/15_common-issues.md)
- **Installation Problems**: See [Installation Troubleshooting](02_installation/08_troubleshooting.md)  
- **API Questions**: Reference [Tooling Documentation](04_tooling/)
- **Bug Reports**: Create an issue in the repository
- **Feature Requests**: Use GitHub Discussions

---

## 📄 Document Standards

This documentation follows:
- **Enterprise flat structure** (no deep nesting)
- **Numbered sections** for logical reading order
- **Audience-specific organization** (design → install → use → develop)
- **Descriptive filenames** that indicate exact content
- **Cross-references** for easy navigation

---

**Version**: 3.0  
**Last Updated**: 2024-08-25  
**Maintained by**: AI-Server Team

**Start here**: [Quick Start Guide](02_installation/01_quick-start.md)