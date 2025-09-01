# AI-Server

A comprehensive AI infrastructure system integrating Memory Server, LLM orchestration, and intelligent GUI with ATLAS black-box enhancement.

## Architecture Overview

The AI-Server system consists of multiple interconnected components:

- **Memory Server**: Hierarchical memory management with embeddings and vector search
- **LLM Server**: Multi-profile LLM orchestration with dynamic model switching
- **GUI Server**: Real-time web interface with monitoring dashboards
- **ATLAS Interface**: Black-box enhancement system (public interface only)
- **Messaging Layer**: Apache Pulsar, NATS, and Benthos for async communication
- **Storage Layer**: PostgreSQL with pgvector, Redis cache, and S3-compatible storage

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker and Docker Compose
- CUDA-compatible GPU (optional, for acceleration)
- 16GB+ RAM recommended

### Installation

```bash
# Clone repository
git clone https://github.com/Ruben-Alvarez-Dev/ai-server.git
cd ai-server

# Install dependencies
make install

# Download models
make download-models

# Start services
make run-all
```

### Basic Usage

Access the web interface at `http://localhost:8003`

API endpoints available at:
- Memory Server: `http://localhost:8001`
- LLM Server: `http://localhost:8002`
- ATLAS Interface: `http://localhost:8004/atlas/v1/`

## Features

### Memory Management
- Hierarchical memory organization (Project → Session → Conversation → Task)
- Automatic cleanup based on IPC (Importance, Priority, Context) scoring
- Vector similarity search with embedding models
- Persistent storage with compression

### LLM Profiles
- **DEV**: Lightweight models for development
- **PRODUCTIVITY**: Balanced performance for daily tasks
- **ACADEMIC**: High-quality models for research
- **GENERAL**: Versatile general-purpose models

### Real-time Monitoring
- System health metrics
- Model performance tracking
- Request/response analytics
- Resource utilization graphs

### ATLAS Integration
- Public interface for content enhancement
- Black-box processing system
- Seamless integration with all components

## Configuration

All configuration files are located in `/config/`:

- `system.yaml`: Global system settings
- `profiles.yaml`: LLM profile definitions
- `models.yaml`: Model configurations and URLs
- `messaging.yaml`: Pulsar, NATS, Benthos settings
- `monitoring.yaml`: Prometheus and alerting rules
- `gui.yaml`: Dashboard and UI configuration

## Development

### Project Structure

```
ai-server/
├── config/           # Configuration files
├── servers/          # Server implementations
│   ├── memory-server/
│   ├── llm-server/
│   └── gui-server/
├── services/         # Shared services
│   ├── messaging/
│   ├── storage/
│   └── embeddings/
├── api/              # API layer
├── models/           # Model storage
├── logs/             # Application logs
└── tests/            # Test suite
```

### Testing

```bash
# Run all tests
make test

# Run specific server tests
make test-memory
make test-llm
make test-gui
```

### Contributing

Please follow the project rules in `logs/plan/`:
- `01 - RULES - language_communication_rules.md`
- `02 - RULES - development_standards.md`
- `03 - RULES - commit_conventions.md`

#### Git Workflow & Hooks
- Single branch: `main` only. Direct commits, no PRs.
- Enable repo hooks: `bash tools/git/setup-hooks.sh`.
- Organic commits: use `scripts/organic-commit.sh` (auto-validates and commits with a smart message). Requires author: `Ruben-Alvarez-Dev <ruben.alvarez.dev@gmail.com>`.
- Commit format: `<type>: <description>` where type ∈ `feat|fix|refactor|docs|test|chore|feat(atlas)|docs(log)|docs(plan)`.
- Directory rules: keep `logs/` and `plan/` tracked; always ignore `OLD_VERSION/`.
- ATLAS Black Box: only public interfaces, `atlas_` prefix, never document internals.
- Checkpoint logs: every code commit must include a new file `logs/YYYY-MM-DD_HHMMSS_X.Y.Z_keyword.md`.
 - Pre-commit validations: branch=main, single-author, directory rules, ATLAS compliance, English-only comments, TS interfaces `I*`, CSS `.atlas-` (no `.atlas_`), significance check, optional Black/Prettier.

## License

MIT License - See LICENSE file for details

## Status

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Version](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
