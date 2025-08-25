#!/bin/bash

# AI-SERVER - Unified Server Startup
# Starts R2R RAG System + LLM Server

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

# Header
echo -e "${PURPLE}"
echo "🤖 AI-SERVER - UNIFIED STARTUP"
echo "================================="
echo -e "${NC}"
echo -e "${CYAN}Starting R2R RAG System + LLM Server${NC}"
echo -e "${WHITE}Version 2.0 - Multi-Modal with Virtual Models${NC}"
echo ""

# Configuration
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
R2R_DIR="${BASE_DIR}/R2R/R2R"
LLM_DIR="${BASE_DIR}/llm-server"
LOGS_DIR="${BASE_DIR}/logs"

# Create logs directory
mkdir -p "$LOGS_DIR"

# Function to check if port is in use
port_in_use() {
    lsof -i :$1 >/dev/null 2>&1
}

# Function to wait for service
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $name is ready${NC}"
            return 0
        fi
        
        ((attempt++))
        echo -e "${YELLOW}⏳ Waiting for $name... attempt $attempt/$max_attempts${NC}"
        sleep 2
    done
    
    echo -e "${RED}❌ $name failed to start after $max_attempts attempts${NC}"
    return 1
}

# Check system requirements
echo -e "${BLUE}🔍 Checking system requirements...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found. Please install Docker Desktop.${NC}"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 not found.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ System requirements OK${NC}"
echo ""

# Kill existing LLM processes (leave R2R running)
echo -e "${YELLOW}🧹 Cleaning up existing LLM processes...${NC}"
pkill -f "python.*real_server.py" 2>/dev/null || true

# Check R2R RAG System
echo -e "${BLUE}🐳 Checking R2R RAG System...${NC}"

# First check if R2R is already running
if curl -s http://localhost:7272/v3/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ R2R is already running${NC}"
else
    echo -e "${YELLOW}⚡ R2R not running, starting containers...${NC}"
    
    if [ ! -d "$R2R_DIR" ]; then
        echo -e "${RED}❌ R2R directory not found: $R2R_DIR${NC}"
        exit 1
    fi

    cd "$R2R_DIR/docker"
    
    # Start R2R with Docker Compose (detached, persistent)
    echo -e "${CYAN}   Starting R2R containers...${NC}"
    docker compose -f compose.full.yaml --profile postgres up -d
    
    cd "$BASE_DIR"
    
    # Wait for R2R to be ready with real-time feedback
    echo -e "${YELLOW}⏳ Waiting for R2R to start...${NC}"
    max_attempts=60
    attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:7272/v3/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ R2R RAG System is ready!${NC}"
            break
        fi
        
        ((attempt++))
        echo -ne "${CYAN}   Checking R2R... attempt $attempt/$max_attempts\r${NC}"
        sleep 1
    done
    
    if [ $attempt -eq $max_attempts ]; then
        echo -e "\n${RED}❌ R2R failed to start after $max_attempts seconds${NC}"
        exit 1
    fi
    echo ""
fi

# Start LLM Server
echo -e "${BLUE}🤖 Starting LLM Server...${NC}"

if [ ! -d "$LLM_DIR" ]; then
    echo -e "${RED}❌ LLM Server directory not found: $LLM_DIR${NC}"
    exit 1
fi

cd "$LLM_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Start LLM Server in background
echo -e "${CYAN}   Starting LLM Server...${NC}"
./start.sh &
LLM_PID=$!

cd "$BASE_DIR"

# Wait for LLM Server to be ready
if ! wait_for_service "http://localhost:8000/health" "LLM Server"; then
    echo -e "${RED}❌ Failed to start LLM Server${NC}"
    kill $LLM_PID 2>/dev/null || true
    exit 1
fi

# Success message
echo ""
echo -e "${GREEN}🎉 AI-SERVER IS READY!${NC}"
echo -e "${GREEN}========================${NC}"
echo ""
echo -e "${WHITE}📡 Services Running:${NC}"
echo -e "   • R2R RAG System:    ${CYAN}http://localhost:7272${NC}"
echo -e "   • LLM Server API:    ${CYAN}http://localhost:8000${NC}"
echo -e "   • API Documentation: ${CYAN}http://localhost:8000/docs${NC}"
echo ""
echo -e "${WHITE}🎯 Virtual Models Available:${NC}"
echo -e "   • ${YELLOW}cline-optimized${NC}      - For Cline IDE integration"
echo -e "   • ${YELLOW}openai-compatible${NC}   - 100% OpenAI API standard"
echo -e "   • ${YELLOW}multimodal-enhanced${NC} - Text + Documents + Images"
echo -e "   • ${YELLOW}thinking-enabled${NC}    - Always-on reasoning mode"
echo ""
echo -e "${WHITE}🔧 Quick Tests:${NC}"
echo -e "${CYAN}curl http://localhost:8000/health${NC}"
echo -e "${CYAN}curl http://localhost:8000/v1/models${NC}"
echo ""
echo -e "${WHITE}📚 Documentation: ${CYAN}./docs/README.md${NC}"
echo ""
echo -e "${GREEN}Press Ctrl+C to stop LLM Server (R2R stays running)${NC}"
echo -e "${WHITE}💡 To manage R2R: ${CYAN}./start_r2r.sh [start|stop|restart|status|logs]${NC}"

# Keep script running and monitor services
trap 'echo -e "\n${YELLOW}🛑 Shutting down LLM Server...${NC}"; pkill -f "python.*real_server.py" 2>/dev/null || true; echo -e "${GREEN}✅ LLM Server stopped (R2R left running)${NC}"; exit 0' INT TERM

# Monitor services
while true; do
    sleep 30
    
    # Check R2R
    if ! curl -s http://localhost:7272/v3/health > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  R2R appears down, check logs${NC}"
    fi
    
    # Check LLM Server  
    if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  LLM Server appears down, check logs${NC}"
    fi
done