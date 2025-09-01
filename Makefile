# AI-Server Makefile
# Common commands for development and deployment

.PHONY: help install clean test run-memory run-llm run-gui run-all stop download-models
 .PHONY: deps-compile deps-sync preflight

# Default target
help:
	@echo "AI-Server Development Commands:"
	@echo ""
	@echo "Setup Commands:"
	@echo "  install          Install all dependencies (Python + Node.js)"
	@echo "  download-models  Download required models"
	@echo "  clean           Clean build artifacts and caches"
	@echo ""
	@echo "Development Commands:"
	@echo "  run-memory      Start Memory Server"
	@echo "  run-llm         Start LLM Server"
	@echo "  run-gui         Start GUI Server"
	@echo "  run-all         Start all servers"
	@echo "  stop            Stop all running servers"
	@echo ""
	@echo "Testing Commands:"
	@echo "  test            Run all tests"
	@echo "  test-memory     Run Memory Server tests"
	@echo "  test-llm        Run LLM Server tests" 
	@echo "  test-gui        Run GUI Server tests"
	@echo ""
	@echo "Quality Commands:"
	@echo "  lint            Run linting checks"
	@echo "  format          Format code"
	@echo "  type-check      Run type checking"

# Installation
install:
	@echo "Installing Python dependencies..."
	pip install -r requirements.txt
	@echo "Installing Node.js dependencies..."
	npm install
	@echo "Setting up pre-commit hooks..."
	pre-commit install
	@echo "Installation complete!"

# Dependencies via pip-tools
deps-compile:
	@echo "Compiling requirements.txt from requirements.in (pip-tools)..."
	pip install pip-tools && pip-compile --generate-hashes -o requirements.txt requirements.in

deps-sync:
	@echo "Syncing environment to requirements.txt (pip-tools)..."
	pip install pip-tools && pip-sync requirements.txt

# System preflight
preflight:
	@echo "Running system preflight checks..."
	bash tools/system/preflight.sh

# Model download
download-models:
	@echo "Creating models directories..."
	mkdir -p models/shared models/profiles/{dev,productivity,academic,general}
	@echo "Download models manually from URLs in config/models.yaml"
	@echo "Models directory structure created!"

# Cleaning
clean:
	@echo "Cleaning Python cache..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Cleaning Node.js cache..."
	rm -rf node_modules/.cache 2>/dev/null || true
	@echo "Cleaning build artifacts..."
	rm -rf dist/ build/ *.egg-info/ 2>/dev/null || true
	@echo "Clean complete!"

# Server execution
run-memory:
	@echo "Starting Memory Server..."
	cd servers/memory-server && python main.py

run-llm:
	@echo "Starting LLM Server..."
	cd servers/llm-server && python main.py

run-gui:
	@echo "Starting GUI Server..."
	cd servers/gui-server && python main.py

run-all:
	@echo "Starting all servers..."
	@echo "Memory Server: http://localhost:8001"
	@echo "LLM Server: http://localhost:8002"
	@echo "GUI Server: http://localhost:8003"
	@echo "Use Ctrl+C to stop all servers"
	# TODO: Implement parallel server startup

stop:
	@echo "Stopping all servers..."
	pkill -f "python.*main.py" 2>/dev/null || true
	@echo "All servers stopped!"

# Testing
test:
	@echo "Running all tests..."
	pytest tests/ -v --cov=servers --cov=services

test-memory:
	@echo "Running Memory Server tests..."
	pytest tests/test_memory_server.py -v

test-llm:
	@echo "Running LLM Server tests..."
	pytest tests/test_llm_server.py -v

test-gui:
	@echo "Running GUI Server tests..."
	pytest tests/test_gui_server.py -v

# Code quality
lint:
	@echo "Running Python linting..."
	flake8 servers/ services/ --max-line-length=88
	@echo "Running JavaScript linting..."
	npm run lint

format:
	@echo "Formatting Python code..."
	black servers/ services/
	@echo "Formatting JavaScript code..."
	npm run format

type-check:
	@echo "Running type checking..."
	mypy servers/ services/ --ignore-missing-imports
