# AI-Server Project Structure Guide

**Enterprise-Grade Multi-Service Architecture**

This document explains the rationale and organization of the AI-Server project structure.

---

## 🏗️ Directory Overview

```
AI-server/
├── 📱 apps/              # User-facing applications
├── 🔧 services/          # Background support services
├── 🛠️ tools/            # Development utilities
├── ⚡ bin/               # Executable scripts
├── 📦 src/               # Shared source code
├── 🎯 assets/            # Static resources
├── ⚙️ config/            # Environment configurations
├── 📝 docs/              # Documentation
├── 🧪 tests/             # Testing suite
├── 🚀 deploy/            # Deployment configs
├── 📊 monitoring/        # Observability
└── 🔒 security/          # Security assets
```

## 📱 Applications (`apps/`)

**Purpose**: User-facing applications that provide core business functionality.

```
apps/
├── llm-server/           # Main LLM API Server
│   ├── api/             # FastAPI routes
│   ├── models/          # Pydantic models
│   ├── core/            # Business logic
│   └── Dockerfile       # Container definition
├── memory-server/        # LazyGraphRAG Memory System
│   ├── api/             # Memory API endpoints  
│   ├── ingestion/       # Document processing
│   └── memory/          # Graph memory core
└── dashboard/           # Web UI (future)
    ├── frontend/        # React/Vue components
    └── api/             # Dashboard API
```

**Characteristics**:
- ✅ End-user facing
- ✅ Independently deployable
- ✅ Own their data models
- ✅ Team ownership boundaries
- ✅ Scalable horizontally

## 🔧 Services (`services/`)

**Purpose**: Background services that support applications.

```
services/
├── model-watcher/        # Automatic model detection
│   ├── watcher.py       # File system monitoring
│   └── auto_start.py    # Background startup
├── vector-db/           # Vector database service (future)
├── auth-service/        # Authentication service (future)
└── telemetry/           # Metrics collection (future)
```

**Characteristics**:
- 🔄 Background processing
- 🔄 Support other services
- 🔄 Shared across applications
- 🔄 Infrastructure concerns

## 🛠️ Tools (`tools/`)

**Purpose**: Development utilities and integrations.

```
tools/
├── cli-interfaces/       # Command-line tools
│   ├── open-interpreter/ # AI CLI assistant
│   └── opencode/        # Code-focused CLI
├── vscode-extension/    # VS Code activity tracker
├── web-scraper/         # Documentation scraper
└── mcp-servers/         # MCP protocol servers
```

**Characteristics**:
- 👨‍💻 Developer-facing
- 👨‍💻 Not deployed to production
- 👨‍💻 Enhance development experience

## ⚡ Executables (`bin/`)

**Purpose**: Startup scripts and command-line utilities.

```
bin/
├── start_ai_server.py   # Main startup (Python)
├── start_servers.sh     # Shell version
├── start_llm.sh        # LLM server only
├── start_memory.sh     # Memory server only
└── setup.sh            # Initial setup
```

**Usage**:
```bash
# Start entire ecosystem
./bin/start_ai_server.py

# Individual services  
./bin/start_llm.sh
./bin/start_memory.sh
```

## 📦 Shared Source (`src/`)

**Purpose**: Common libraries and utilities shared across applications.

```
src/
├── common/              # Shared utilities
│   ├── logging.py      # Logging configuration
│   ├── metrics.py      # Metrics collection
│   └── exceptions.py   # Common exceptions
├── models/              # Shared data models
│   ├── user.py         # User models
│   └── api.py          # API response models
├── protocols/           # Communication protocols
│   ├── mcp.py          # MCP protocol
│   └── websocket.py    # WebSocket handling
└── utils/               # Utility functions
    ├── model_utils.py   # Model loading helpers
    └── file_utils.py    # File operations
```

**Import Pattern**:
```python
from src.common.logging import setup_logging
from src.models.user import User
from src.utils.model_utils import load_model
```

## 🎯 Assets (`assets/`)

**Purpose**: Static resources organized by type.

```
assets/
├── models/              # AI model files
│   ├── llm/            # Large language models
│   │   ├── qwen2.5-32b-instruct-q6_k.gguf
│   │   └── deepseek-coder-v2-lite.gguf
│   ├── embedding/      # Embedding models
│   │   └── all-MiniLM-L6-v2/
│   └── vision/         # Computer vision models
│       └── clip-vit-base/
├── prompts/             # Prompt templates
│   ├── system/         # System prompts
│   └── user/           # User prompt templates
└── datasets/           # Training/fine-tuning data
    ├── conversations/  # Chat datasets
    └── code/           # Code datasets
```

## ⚙️ Configuration (`config/`)

**Purpose**: Environment-specific configurations.

```
config/
├── base/               # Base configuration
│   ├── logging.yaml    # Logging setup
│   └── models.yaml     # Model definitions
├── development/        # Development overrides
│   ├── llm_server.yaml
│   └── memory_server.yaml
├── production/         # Production settings
│   ├── security.yaml   # Security config
│   └── scaling.yaml    # Auto-scaling rules
└── profiles/           # User profiles
    ├── researcher.yaml  # Research-focused
    └── developer.yaml   # Development-focused
```

## 📝 Documentation (`docs/`)

**Purpose**: Comprehensive project documentation.

```
docs/
├── architecture/        # System design
│   ├── ADR-001-Directory-Structure.md
│   ├── Project-Structure.md
│   └── Service-Communication.md
├── api/                # API documentation
│   ├── llm-server-api.md
│   └── memory-server-api.md
├── deployment/         # Deployment guides
│   ├── docker.md       # Container deployment
│   ├── kubernetes.md   # K8s deployment
│   └── production.md   # Production setup
└── development/        # Development guides
    ├── contributing.md  # How to contribute
    ├── setup.md        # Local development
    └── testing.md      # Testing guidelines
```

## 🧪 Testing (`tests/`)

**Purpose**: Comprehensive test suite.

```
tests/
├── unit/               # Unit tests
│   ├── apps/           # App-specific tests
│   ├── services/       # Service tests
│   └── src/            # Shared code tests
├── integration/        # Integration tests
│   ├── api/            # API integration
│   └── workflows/      # End-to-end workflows
├── e2e/               # End-to-end tests
│   ├── user_flows/    # Complete user journeys
│   └── performance/   # Performance tests
└── fixtures/          # Test data
    ├── models/        # Test model files
    └── data/          # Sample datasets
```

## 🚀 Deployment (`deploy/`)

**Purpose**: Infrastructure as Code and deployment configs.

```
deploy/
├── docker/             # Container configurations
│   ├── Dockerfile.llm  # LLM server container
│   ├── Dockerfile.memory # Memory server container
│   └── docker-compose.yml # Local development
├── kubernetes/         # Kubernetes manifests
│   ├── namespaces/     # K8s namespaces
│   ├── services/       # Service definitions
│   └── ingress/        # Traffic routing
├── terraform/          # Cloud infrastructure
│   ├── aws/           # AWS resources
│   └── gcp/           # Google Cloud resources
└── scripts/           # Deployment automation
    ├── deploy.sh      # Main deployment script
    └── rollback.sh    # Rollback script
```

## 📊 Monitoring (`monitoring/`)

**Purpose**: Observability and operational insights.

```
monitoring/
├── metrics/            # Application metrics
│   ├── prometheus/    # Prometheus configs
│   └── grafana/       # Grafana dashboards
├── logs/              # Centralized logging
│   ├── application/   # App logs
│   └── system/        # System logs
└── alerts/            # Alerting rules
    ├── performance.yaml # Performance alerts
    └── errors.yaml     # Error alerts
```

## 🔒 Security (`security/`)

**Purpose**: Security assets and compliance.

```
security/
├── keys/              # Certificates and keys (gitignored)
│   ├── tls/          # TLS certificates
│   └── jwt/          # JWT signing keys
├── policies/          # Security policies
│   ├── rbac.yaml     # Role-based access
│   └── network.yaml  # Network policies
└── audit/            # Audit logs
    ├── access.log    # Access logs
    └── changes.log   # Configuration changes
```

---

## 🔄 Migration Notes

This structure evolved from a flatter organization to support:

1. **Team Scalability**: Clear ownership boundaries
2. **Deployment Independence**: Each app/service can deploy separately
3. **Code Organization**: Logical grouping of related functionality
4. **Industry Standards**: Following proven patterns from successful projects

## 📚 Related Documentation

- [ADR-001: Directory Structure Decision](./ADR-001-Directory-Structure.md)
- [Service Communication Patterns](./Service-Communication.md)
- [Development Setup Guide](../development/setup.md)
- [Deployment Guide](../deployment/docker.md)

---

**Maintained by**: AI-Server Team  
**Last Updated**: 2024-08-25  
**Version**: 3.0