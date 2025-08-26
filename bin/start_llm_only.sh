#!/bin/bash

# AI-SERVER - LLM Server Only
# Quick startup for development

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

echo -e "${PURPLE}"
echo "🤖 AI-SERVER - LLM ONLY"
echo "========================"
echo -e "${NC}"
echo -e "${CYAN}Starting LLM Server with Virtual Models${NC}"
echo ""

# Configuration  
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
LLM_DIR="${BASE_DIR}/llm-server"

# Check LLM Server directory
if [ ! -d "$LLM_DIR" ]; then
    echo -e "${RED}❌ LLM Server directory not found: $LLM_DIR${NC}"
    exit 1
fi

# Kill existing processes
echo -e "${YELLOW}🧹 Cleaning up existing processes...${NC}"
pkill -f "python.*real_server.py" 2>/dev/null || true

# Check if port 8000 is available  
if lsof -i :8000 >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Port 8000 is in use. Attempting to free it...${NC}"
    sleep 2
fi

# Start LLM Server
echo -e "${BLUE}🤖 Starting LLM Server...${NC}"
cd "$LLM_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Start LLM Server
echo -e "${CYAN}   Starting LLM Server...${NC}"
./start.sh &
LLM_PID=$!

# Wait for LLM Server to be ready
echo -e "${YELLOW}⏳ Waiting for LLM Server to start...${NC}"
max_attempts=20
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ LLM Server is ready!${NC}"
        break
    fi
    
    ((attempt++))
    echo -e "${CYAN}   Attempt $attempt/$max_attempts...${NC}"
    sleep 3
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "${RED}❌ LLM Server failed to start${NC}"
    kill $LLM_PID 2>/dev/null || true
    exit 1
fi

cd "$BASE_DIR"

# Success message
echo ""
echo -e "${GREEN}🎉 AI-SERVER LLM IS READY!${NC}"
echo -e "${GREEN}=============================${NC}"
echo ""
echo -e "${WHITE}📡 LLM Server:        ${CYAN}http://localhost:8000${NC}"
echo -e "${WHITE}📚 API Documentation: ${CYAN}http://localhost:8000/docs${NC}"
echo -e "${WHITE}❤️  Health Check:      ${CYAN}http://localhost:8000/health${NC}"
echo ""
echo -e "${WHITE}🎯 Virtual Models Available:${NC}"
echo -e "   • ${YELLOW}cline-optimized${NC}      - For Cline IDE (recommended)"
echo -e "   • ${YELLOW}openai-compatible${NC}   - 100% OpenAI API standard"
echo -e "   • ${YELLOW}multimodal-enhanced${NC} - Text + Documents + Images"
echo -e "   • ${YELLOW}thinking-enabled${NC}    - Always-on reasoning mode"
echo ""
echo -e "${WHITE}🔧 Quick Test:${NC}"
echo -e "${CYAN}curl http://localhost:8000/v1/models${NC}"
echo ""
echo -e "${WHITE}🎪 Cline Configuration:${NC}"
echo -e "${CYAN}Base URL: http://localhost:8000/v1${NC}"
echo -e "${CYAN}API Key:  sk-llmserver-local-development-key-12345678${NC}"
echo -e "${CYAN}Model:    cline-optimized${NC}"
echo ""
echo -e "${GREEN}Press Ctrl+C to stop${NC}"

# Keep running and monitor
trap 'echo -e "\n${YELLOW}🛑 Stopping LLM Server...${NC}"; pkill -f "python.*real_server.py" 2>/dev/null || true; echo -e "${GREEN}✅ Stopped${NC}"; exit 0' INT TERM

# Simple monitoring
while true; do
    sleep 30
    if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  LLM Server appears down${NC}"
    fi
done