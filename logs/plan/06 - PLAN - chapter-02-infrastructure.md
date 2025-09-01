# Chapter 2: Core Infrastructure
**29 tasks | Phase 2 | Prerequisites: Chapter 1 completed**

## 2.1 System Requirements Verification (6 tasks)

- [x] **2.1.1 Verify macOS version (14.0+)**  
  Run sw_vers -productVersion to check macOS version, ensuring it's 14.0 or higher for proper Metal support. Create a verification script that checks all requirements and provides clear error messages. Newer macOS versions include Metal Performance Shaders optimizations critical for LLM inference.

- [x] **2.1.2 Verify 128GB RAM available**  
  Use sysctl hw.memsize to verify total RAM and calculate available memory after OS overhead. The system requires substantial RAM for running multiple large language models simultaneously. Create a pre-flight check that ensures sufficient resources before starting services.

- [x] **2.1.3 Verify Apple Silicon (M1/M2/M3)**  
  Check for Apple Silicon using sysctl -n machdep.cpu.brand_string to ensure ARM64 architecture. The entire stack is optimized for Apple Silicon's unified memory architecture. Intel Macs won't provide the necessary Metal acceleration for acceptable performance.

- [x] **2.1.4 Verify 500GB+ free disk space**  
  Check available space using df -h and verify at least 500GB free for models, databases, and operational data. Large language models in GGUF format can be 30-50GB each, and the system needs room for logs, caches, and databases. Include growth projections in the check.

- [x] **2.1.5 Verify Metal GPU access**  
  Test Metal availability using metal-info or a simple Metal test program. Verify both Metal device existence and performance characteristics. This is crucial as all LLM inference relies on Metal acceleration for acceptable speeds.

- [x] **2.1.6 Verify Xcode Command Line Tools installed**  
  Check for Xcode tools using xcode-select -p and verify compiler availability. These tools are required for compiling llama.cpp and other native dependencies. Provide instructions for installation if missing: xcode-select --install.

## 2.2 Python Environment (6 tasks)

- [x] **2.2.1 Install Python 3.11+ via Homebrew**  
  Install Python 3.11 specifically (not 3.12+) for maximum compatibility using brew install python@3.11. This version provides the optimal balance of features and library support. Configure PATH to prioritize Homebrew Python over system Python.

- [x] **2.2.2 Create virtual environment for project**  
  Create a venv in the project root using python3.11 -m venv venv to isolate dependencies. This prevents conflicts with system packages and enables reproducible deployments. Document activation commands for different shells in the README.

- [x] **2.2.3 Install pip-tools for dependency management**  
  Install pip-tools to manage requirements.txt from requirements.in files, enabling better dependency resolution. This toolchain separates direct dependencies from transitive ones. Use pip-compile for reproducible builds and pip-sync for exact environment replication.

- [x] **2.2.4 Install base packages (Flask, pyyaml, loguru, pydantic)**  
  Install foundational packages that all components will use for web services, configuration, logging, and validation. These form the core of our Python infrastructure. Pin exact versions to ensure consistency across development environments.

- [x] **2.2.5 Install async packages (aiohttp, asyncio)**  
  Add asynchronous programming support for handling concurrent operations efficiently. These packages enable high-performance I/O operations crucial for message handling and API serving. Include aiofiles for async file operations.

- [x] **2.2.6 Setup Python path configuration**  
  Configure PYTHONPATH to include project root, enabling clean imports like from services.storage import DuckDBService. Add this to activation scripts and .env files. This eliminates the need for relative imports and makes code more maintainable.

## 2.3 Node.js Environment (4 tasks)

- [x] **2.3.1 Install Node.js 20+ via Homebrew**  
  Install latest LTS Node.js using brew install node@20 for frontend tooling and GUI development. Version 20 provides native ES modules and improved performance. Configure npm to use a local prefix to avoid global package pollution.

- [x] **2.3.2 Install pnpm as package manager**  
  Install pnpm globally using npm install -g pnpm for faster, more efficient package management. Pnpm uses hard links to save disk space and provides stricter dependency resolution. Configure workspace settings for monorepo support.

- [x] **2.3.3 Install global tools (nodemon, pm2)**  
  Install development tools: nodemon for auto-reloading during development, pm2 for process management in production. These tools improve developer experience and operational reliability. Configure pm2 ecosystem file for managing all services.

- [x] **2.3.4 Setup Node environment variables**  
  Configure NODE_ENV, NODE_OPTIONS for memory limits, and paths for module resolution. Set up .nvmrc file to ensure consistent Node version across team members. Include these in .env.example with documentation.

## 2.4 Rust Environment (3 tasks)

- [x] **2.4.1 Install Rust toolchain via rustup**  
  Install Rust using the official rustup installer for compiling performance-critical components like LanceDB. Choose stable channel with ARM64 target. Rust provides memory safety and performance for system-level components.

- [x] **2.4.2 Install cargo packages**  
  Install cargo-edit for easier dependency management and cargo-watch for development auto-compilation. These tools enhance the Rust development workflow. Include sccache for faster compilation times.

- [x] **2.4.3 Verify ARM64 compilation works**  
  Test Rust compilation for ARM64 target with a simple program to ensure Metal dependencies compile correctly. This verification prevents issues when building native extensions. Document any macOS-specific compilation flags needed.

## 2.5 Build Tools (4 tasks)

- [x] **2.5.1 Install cmake via Homebrew**  
  Install CMake using brew install cmake for building llama.cpp and other C++ components. CMake provides cross-platform build configuration essential for native code. Verify version 3.20+ for modern features support.

- [x] **2.5.2 Install make and build essentials**  
  Ensure GNU Make and essential build tools are available for compilation tasks. macOS provides BSD make by default, but some tools expect GNU make. Install coreutils for additional Unix utilities.

- [x] **2.5.3 Install pkg-config**  
  Install pkg-config for managing library compile and link flags, required by many native Python packages. This tool helps locate installed libraries and their dependencies. Configure PKG_CONFIG_PATH for Homebrew libraries.

- [x] **2.5.4 Install Metal Performance Shaders framework**  
  Verify Metal framework is available and install any additional Metal developer tools. These frameworks provide optimized operations for neural network inference. Document Metal version requirements and capability detection.

## 2.6 Core Libraries (6 tasks)

- [x] **2.6.1 Create services/lib/config.py**  
  Create configuration management module that loads and validates YAML configs with environment variable override support. This centralizes all configuration logic.

- [x] **2.6.2 Create services/lib/logger.py**  
  Build logging wrapper around loguru with structured logging, context injection, and multiple output handlers. This provides consistent logging across all components.

- [x] **2.6.3 Create services/lib/common.py**  
  Implement shared utilities: retry decorators, async helpers, validation functions, and common patterns. This reduces code duplication across services.

- [x] **2.6.4 Create services/lib/exceptions.py**  
  Define custom exception hierarchy for the project with error codes and structured error responses. This enables consistent error handling.

- [x] **2.6.5 Create services/lib/validators.py**  
  Create Pydantic models and validation schemas for all data structures. This ensures data integrity throughout the system.

- [x] **2.6.6 Create services/lib/constants.py**  
  Define system-wide constants, enums, and magic numbers in one place. This prevents hardcoded values scattered through code.

## Progress Summary
- **Total Tasks**: 29
- **Completed**: 29/29
- **Current Section**: Completed
- **Next Checkpoint**: Phase 3 → 3.1.1
