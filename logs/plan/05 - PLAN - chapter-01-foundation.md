# Chapter 1: Project Foundation
**33 tasks | Phase 1 | Prerequisites: None**

## 1.1 Repository Setup (6 tasks)

- [x] **1.1.1 Create GitHub repository ai-server**  
  Create a new public repository named ai-server on GitHub with no initial files. This will be our central version control hub for the entire project. We start with an empty repo to maintain full control over the initial structure and avoid conflicts with auto-generated files.

- [x] **1.1.2 Initialize with README.md**  
  Create a comprehensive README.md that includes project vision, architecture overview, and quick start instructions. This serves as the entry point for anyone discovering the project. Include badges for build status, license, and version to establish professionalism from day one.

- [x] **1.1.3 Configure .gitignore for Python, Node, macOS, models, logs**  
  Combine Python, Node.js, and macOS gitignore templates, then add custom rules for /models/*.gguf, /logs/, and /var/. This prevents accidentally committing large model files (often several GB each) and sensitive logs. Use GitHub's gitignore templates as a base and extend with project-specific patterns.

- [x] **1.1.4 Setup branch protection rules for main branch**  
  Configure GitHub branch protection to require pull request reviews before merging to main, enable status checks, and dismiss stale reviews. This enforces code quality from the start and prevents accidental direct pushes to production branch. Include administrators in restrictions to maintain discipline.

- [x] **1.1.5 Create develop branch**  
  Skipped per main-only strategy (no develop branch used).

- [x] **1.1.6 Configure branch naming convention (feature/, fix/, docs/*)**  
  Skipped per main-only strategy (no feature branch naming enforced).

## 1.2 Project Structure (11 tasks)

- [x] **1.2.1 Create /config/ directory**  
  Initialize the configuration directory that will hold all YAML configuration files. This centralized location makes it easy to manage settings and enables configuration-as-code practices. Create a README in this directory explaining each config file's purpose.

- [x] **1.2.2 Create /servers/ directory structure**  
  Create /servers/ with subdirectories for memory-server/, llm-server/, and gui-server/. Each server is a standalone Python application with its own main.py entry point. This separation allows independent development and deployment of each component.

- [x] **1.2.3 Create /services/ directory structure**  
  Build the shared services structure including /services/messaging/, /services/storage/, /services/embeddings/, etc. These are reusable modules that servers import, avoiding code duplication. Follow a clear namespace pattern for easy importing.

- [x] **1.2.4 Create /api/ directory**  
  Set up /api/ with /api/rest/ and /api/websocket/ subdirectories for API layer code. This separation from server logic enables API versioning and protocol flexibility. Include OpenAPI specification files here for documentation.

- [x] **1.2.5 Create /mcp/ directory**  
  Initialize the Model Context Protocol directory for desktop client integration. This will contain the MCP server implementation and tool definitions. Structure it as a standalone package that can be registered with compatible MCP desktop clients.

- [x] **1.2.6 Create /models/ directory with subdirectories**  
  Create /models/shared/ for Memory Server models and /models/profiles/ with subdirectories for each LLM profile (dev/, productivity/, academic/, general/). Include a .gitkeep in each directory and a README explaining the expected model files and formats.

- [x] **1.2.7 Create /tools/ directory**  
  Structure /tools/ with subdirectories for setup scripts, CLI tools, VSCode extension, OpenWebUI integration, and development utilities. Each tool should be self-contained with its own README. This organization keeps auxiliary tools separate from core server code.

- [x] **1.2.8 Create /tests/ directory**  
  Initialize pytest structure with conftest.py for shared fixtures and separate test files mirroring the source structure. Include /tests/fixtures/ for test data files. Start with a simple test that verifies the project structure exists to ensure testing works from day one.

- [x] **1.2.9 Create /docs/ directory**  
  Create documentation structure with /docs/architecture/, /docs/api/, and /docs/development/ subdirectories. Copy the three development standard documents here immediately. Use Markdown for all documentation to enable easy versioning and GitHub rendering.

- [x] **1.2.10 Create /logs/ directory**  
  Set up log directory structure with subdirectories for each server and a /logs/system/ for shared logs. Include a .gitkeep but ensure .gitignore excludes actual log files. Configure log rotation policies from the start to prevent disk filling.

- [x] **1.2.11 Create /var/ directory with /var/run/ and /var/state/**  
  Create /var/run/ for PID files and sockets, /var/state/ for runtime state that should persist across restarts. This follows Unix conventions and keeps runtime data separate from code. Include .gitkeep files but exclude actual runtime data in .gitignore.

## 1.3 Development Environment (8 tasks)

- [x] **1.3.1 Create requirements.txt with initial dependencies**  
  Start with core dependencies: Flask==3.0.0, PyYAML==6.0.1, loguru==0.7.2, pydantic==2.5.0, python-dotenv==1.0.0. Use specific versions to ensure reproducibility. Include comments grouping dependencies by purpose (web, config, logging, validation).

- [x] **1.3.2 Create package.json for Node dependencies**  
  Initialize package.json with Node.js dependencies for frontend tooling: monaco-editor, chart.js, socket.io-client, webpack, and development tools. Set Node engine requirement to >=20.0.0. Configure scripts for build, dev, and test commands.

- [x] **1.3.3 Create Makefile with common commands**  
  Write a Makefile with targets for common operations: make install, make test, make run-memory, make run-llm, make run-gui, make clean. This provides a consistent interface regardless of the underlying complexity. Include help target that documents all available commands.

- [x] **1.3.4 Create .env.example template**  
  Create template with all required environment variables documented but with placeholder values. Include clear comments explaining each variable's purpose and valid values. Never commit actual .env files, only the example template.

- [x] **1.3.5 Create setup.py for package installation**  
  Configure setup.py to make the project pip-installable in development mode (pip install -e .). Define entry points for CLI commands and specify package dependencies. This enables proper Python module importing across the project.

- [x] **1.3.6 Copy development standards documents to /docs**  
  Copy the three development guides (language-and-communication.md, development-standards.md, commit-conventions.md) to /docs/development/. These establish coding standards from project inception. Reference them in CONTRIBUTING.md.

- [x] **1.3.7 Setup pre-commit hooks configuration**  
  Configure pre-commit hooks for code formatting (black, isort), linting (flake8, pylint), and security checks (bandit). Include YAML validation for config files. This catches issues before they enter version control, maintaining code quality automatically.

- [x] **1.3.8 Create .editorconfig file**  
  Define consistent coding styles across different editors: indent style, size, line endings, charset, and trim trailing whitespace. This ensures code looks consistent regardless of contributor's editor choice. Include specific rules for Python, JavaScript, YAML, and Markdown files.

## 1.4 Base Configuration Files (8 tasks)

- [x] **1.4.1 Create config/system.yaml template**  
  Define system-wide settings including resource limits, file paths, network ports, and global timeouts. Start with conservative defaults that can run on minimal hardware. Include extensive comments explaining each setting's impact and valid ranges.

- [x] **1.4.2 Create config/profiles.yaml template**  
  Structure the four LLM profiles (DEV, PRODUCTIVITY, ACADEMIC, GENERAL) with placeholder model configurations. Define the schema clearly even if not all models are downloaded yet. Include switching logic configuration and resource allocation per profile.

- [x] **1.4.3 Create config/models.yaml template**  
  Create detailed model configurations including quantization levels, context sizes, and GPU layer allocations. Group by server (Memory Server models vs LLM Server models). Include download URLs and expected checksums for verification.

- [x] **1.4.4 Create config/autocleanup.yaml template**  
  Define cleanup policies including TTL per hierarchy level, IPC thresholds, compression settings, and cleanup schedules. Start with conservative values that preserve data longer. Include emergency cleanup triggers and procedures.

- [x] **1.4.5 Create config/messaging.yaml template**  
  Configure Pulsar topics, NATS subjects, and Benthos pipelines. Define message schemas, retention policies, and rate limits. Include connection parameters and retry logic. Structure for easy addition of new message types.

- [x] **1.4.6 Create config/monitoring.yaml template**  
  Set up Prometheus scraping configs, alert rules, and dashboard definitions. Define metrics to collect from each component. Include log levels and output destinations. Configure health check endpoints and thresholds.

- [x] **1.4.7 Create config/gui.yaml template**  
  Configure GUI Server settings including dashboard layouts, widget configurations, refresh rates, and WebSocket parameters. Define user preference defaults and theme settings. Include cache and session management configuration.

- [x] **1.4.8 Create config/endpoints.yaml template**  
  Define all API endpoints dynamically in YAML format. This enables runtime configuration of routes without code changes. Include versioning, methods, handlers, and middleware configuration.

## Progress Summary
- **Total Tasks**: 33
- **Completed**: 33/33
- **Current Section**: Completed
- **Next Checkpoint**: Phase 2 → 2.1.1 System Verification
