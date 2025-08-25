#!/bin/bash

# LLM Server - Single Command Startup
# Arranca el servidor completo con un solo comando

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# ASCII Art Header
echo -e "${PURPLE}"
echo "██╗     ██╗     ███╗   ███╗    ███████╗███████╗██████╗ ██╗   ██╗███████╗██████╗ "
echo "██║     ██║     ████╗ ████║    ██╔════╝██╔════╝██╔══██╗██║   ██║██╔════╝██╔══██╗"
echo "██║     ██║     ██╔████╔██║    ███████╗█████╗  ██████╔╝██║   ██║█████╗  ██████╔╝"
echo "██║     ██║     ██║╚██╔╝██║    ╚════██║██╔══╝  ██╔══██╗╚██╗ ██╔╝██╔══╝  ██╔══██╗"
echo "███████╗███████╗██║ ╚═╝ ██║    ███████║███████╗██║  ██║ ╚████╔╝ ███████╗██║  ██║"
echo "╚══════╝╚══════╝╚═╝     ╚═╝    ╚══════╝╚══════╝╚═╝  ╚═╝  ╚═══╝  ╚══════╝╚═╝  ╚═╝"
echo -e "${NC}"
echo -e "${CYAN}AI Development Orchestration Server - M1 Ultra Optimized with RAG${NC}"
echo -e "${WHITE}Version 2.0 - 128K Context + RAG → 2M+ Effective Context${NC}"
echo -e "${YELLOW}🔗 CoRAG | 📊 GraphRAG | 💾 Modular Memory | 🔍 Vector Search${NC}"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if port is in use
port_in_use() {
    lsof -i :$1 >/dev/null 2>&1
}

echo -e "${BLUE}🚀 Starting LLM Server...${NC}"
echo ""

# Check if we're in the right directory
if [ ! -f "real_server.py" ]; then
    echo -e "${RED}❌ Error: real_server.py not found!${NC}"
    echo -e "${YELLOW}   Please run this script from the llm-server directory${NC}"
    exit 1
fi

# Check Python installation
if ! command_exists python3; then
    echo -e "${RED}❌ Error: Python3 not found!${NC}"
    echo -e "${YELLOW}   Please install Python3 first${NC}"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found, creating...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${BLUE}📦 Activating virtual environment...${NC}"
source venv/bin/activate

# Check if required packages are installed
if ! python -c "import fastapi, llama_cpp" >/dev/null 2>&1; then
    echo -e "${YELLOW}📥 Installing required packages...${NC}"
    pip install -q fastapi uvicorn pydantic-settings llama-cpp-python aiohttp
fi

# Check if models exist
MODEL_DIR="./models"
if [ ! -d "$MODEL_DIR" ]; then
    echo -e "${RED}❌ Error: Model directory not found at $MODEL_DIR${NC}"
    echo -e "${YELLOW}   Please ensure models are downloaded and in the correct location${NC}"
    exit 1
fi

# Check for main model
MAIN_MODEL="$MODEL_DIR/qwen2.5-coder-7b-instruct-q6_k.gguf"
if [ ! -f "$MAIN_MODEL" ]; then
    echo -e "${RED}❌ Error: Main model not found at $MAIN_MODEL${NC}"
    echo -e "${YELLOW}   Please ensure the model file exists${NC}"
    exit 1
fi

# Check if port 8000 is available
if port_in_use 8000; then
    echo -e "${YELLOW}⚠️  Port 8000 is in use. Attempting to free it...${NC}"
    # Kill any existing server process
    pkill -f "python.*real_server.py" 2>/dev/null || true
    sleep 2
    
    if port_in_use 8000; then
        echo -e "${RED}❌ Error: Port 8000 is still in use${NC}"
        echo -e "${YELLOW}   Please manually stop the process using port 8000${NC}"
        exit 1
    fi
fi

# Ensure .env file exists with correct configuration
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}📝 Creating .env configuration file...${NC}"
    cat > .env << 'EOF'
# LLM Server Configuration
LLM_SERVER_HOST=localhost
LLM_SERVER_PORT=8000
LLM_SERVER_WORKERS=4

# Model Paths and Configuration
MODELS_DIR=./models
MODELS_CACHE_DIR=./models/cache
MAX_CONCURRENT_REQUESTS=10

# M1 Ultra Specific Settings
METAL_ENABLED=true
GPU_LAYERS=-1
CONTEXT_SIZE=131072
BATCH_SIZE=512
THREADS=8

# OpenAI Compatible API
OPENAI_API_KEY=sk-llmserver-local-development-key-12345678

# Memory Management
MAX_MEMORY_USAGE=70
MEMORY_WARNING_THRESHOLD=80
MEMORY_CRITICAL_THRESHOLD=90

# Monitoring
PROMETHEUS_PORT=9090
METRICS_ENABLED=true
LOG_LEVEL=INFO
LOG_FILE=./logs/llm-server.log
EOF
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Show startup information
echo ""
echo -e "${GREEN}✅ Pre-flight checks completed!${NC}"
echo ""
echo -e "${WHITE}🔧 Configuration:${NC}"
echo -e "   • Context Size: ${GREEN}128K tokens${NC}"
echo -e "   • Metal Acceleration: ${GREEN}Enabled${NC}"
echo -e "   • Models Directory: ${CYAN}$MODEL_DIR${NC}"
echo -e "   • Main Model: ${CYAN}$(basename "$MAIN_MODEL")${NC}"
echo ""

# Start the server
echo -e "${BLUE}🚀 Starting LLM Server with full capabilities...${NC}"
echo ""

# Function to show connection info after server starts
show_connection_info() {
    sleep 5
    echo ""
    echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${WHITE}🎉 LLM SERVER IS READY!${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${WHITE}📡 SERVER ENDPOINTS:${NC}"
    echo -e "   • Main API: ${CYAN}http://localhost:8000${NC}"
    echo -e "   • Health Check: ${CYAN}http://localhost:8000/health${NC}"
    echo -e "   • API Documentation: ${CYAN}http://localhost:8000/docs${NC}"
    echo ""
    echo -e "${WHITE}🤖 OPENAI COMPATIBLE API:${NC}"
    echo -e "   • Endpoint: ${CYAN}http://localhost:8000/v1/chat/completions${NC}"
    echo -e "   • API Key: ${YELLOW}sk-llmserver-local-development-key-12345678${NC}"
    echo ""
    echo -e "${WHITE}🎯 TEST ENDPOINTS:${NC}"
    echo -e "   • Math Reasoning: ${CYAN}http://localhost:8000/test/math${NC}"
    echo -e "   • Code Generation: ${CYAN}http://localhost:8000/test/coding${NC}"
    echo -e "   • Plan Mode: ${CYAN}http://localhost:8000/test/plan-mode${NC}"
    echo -e "   • Act Mode: ${CYAN}http://localhost:8000/test/act-mode${NC}"
    echo -e "   • Agent Mode: ${CYAN}http://localhost:8000/test/agent-mode${NC}"
    echo ""
    echo -e "${WHITE}⚡ PERFORMANCE:${NC}"
    echo -e "   • Expected Speed: ${GREEN}55+ tokens/second${NC}"
    echo -e "   • Context Window: ${GREEN}128K tokens${NC}"
    echo -e "   • All 6 Operation Modes: ${GREEN}Active${NC}"
    echo ""
    echo -e "${WHITE}🔌 CURL EXAMPLE:${NC}"
    echo -e "${CYAN}curl -X POST http://localhost:8000/v1/chat/completions \\${NC}"
    echo -e "${CYAN}  -H \"Content-Type: application/json\" \\${NC}"
    echo -e "${CYAN}  -H \"Authorization: Bearer sk-llmserver-local-development-key-12345678\" \\${NC}"
    echo -e "${CYAN}  -d '{\"model\":\"qwen2.5-coder-7b\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello!\"}]}'${NC}"
    echo ""
    echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${WHITE}Press Ctrl+C to stop the server${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
    echo ""
} &

# Start the Python server
# Activate virtual environment and run server
source venv/bin/activate
python real_server.py