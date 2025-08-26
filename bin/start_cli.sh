#!/bin/bash

# AI-SERVER - CLI Startup (Open Interpreter)
# Starts Open Interpreter with AI-Server integration

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
echo "🖥️  AI-SERVER CLI - OPEN INTERPRETER"
echo "====================================="
echo -e "${NC}"
echo -e "${CYAN}Starting Open Interpreter CLI Interface${NC}"
echo -e "${WHITE}Integrated with AI-Server LLM Backend${NC}"
echo ""

# Configuration
BASE_DIR="$(dirname "$0")"
CLI_DIR="${BASE_DIR}/open-interpreter"
LLM_SERVER_URL="http://localhost:8000/v1"
API_KEY="sk-llmserver-local-development-key-12345678"

# Check if LLM Server is running
echo -e "${BLUE}🔍 Checking LLM Server connection...${NC}"
if ! curl -s "$LLM_SERVER_URL/models" > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  LLM Server not detected at $LLM_SERVER_URL${NC}"
    echo -e "${CYAN}   Start it first with: ${WHITE}./start_servers.sh${NC}"
    echo ""
    echo -e "${YELLOW}Would you like to continue anyway? (y/N)${NC}"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo -e "${RED}❌ Aborted${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ LLM Server is running${NC}"
fi

# Check Open Interpreter directory
if [ ! -d "$CLI_DIR" ]; then
    echo -e "${RED}❌ Open Interpreter directory not found: $CLI_DIR${NC}"
    echo -e "${CYAN}   Setting up Open Interpreter...${NC}"
    mkdir -p "$CLI_DIR"
    cd "$CLI_DIR"
    
    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate
    
    # Install Open Interpreter
    pip install --upgrade pip
    pip install open-interpreter
    
    cd "$BASE_DIR"
    echo -e "${GREEN}✅ Open Interpreter installed${NC}"
else
    echo -e "${GREEN}✅ Open Interpreter directory found${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}📦 Activating Open Interpreter environment...${NC}"
cd "$CLI_DIR"

if [ ! -f "venv/bin/activate" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found, creating...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install open-interpreter
else
    source venv/bin/activate
fi

# Check if Open Interpreter is installed
if ! command -v interpreter &> /dev/null; then
    echo -e "${YELLOW}📦 Installing Open Interpreter...${NC}"
    pip install --upgrade open-interpreter
fi

cd "$BASE_DIR"

# Display configuration info
echo ""
echo -e "${GREEN}🚀 STARTING OPEN INTERPRETER${NC}"
echo -e "${GREEN}==============================${NC}"
echo ""
echo -e "${WHITE}🔧 Configuration:${NC}"
echo -e "   • LLM Server:     ${CYAN}$LLM_SERVER_URL${NC}"
echo -e "   • API Key:        ${CYAN}$API_KEY${NC}"
echo -e "   • Available Models:"
echo -e "     - ${YELLOW}cline-optimized${NC}      (Recommended for development)"
echo -e "     - ${YELLOW}openai-compatible${NC}   (Standard OpenAI format)"
echo -e "     - ${YELLOW}multimodal-enhanced${NC} (Text + Documents + Images)"
echo -e "     - ${YELLOW}thinking-enabled${NC}    (Reasoning mode)"
echo ""
echo -e "${WHITE}💡 Usage Examples:${NC}"
echo -e "${CYAN}   > Create a Python script to analyze this data${NC}"
echo -e "${CYAN}   > Help me debug this code${NC}"
echo -e "${CYAN}   > Set up a new React project${NC}"
echo ""
echo -e "${WHITE}🎯 Tips:${NC}"
echo -e "   • Type ${YELLOW}'exit'${NC} to quit"
echo -e "   • Type ${YELLOW}'%model cline-optimized'${NC} to switch models"  
echo -e "   • Upload files by dragging them to the terminal"
echo ""
echo -e "${GREEN}Starting Open Interpreter with AI-Server integration...${NC}"
echo ""

# Set environment variables for Open Interpreter
export OPENAI_API_BASE="$LLM_SERVER_URL"
export OPENAI_API_KEY="$API_KEY"

# Start Open Interpreter with configuration
cd "$CLI_DIR"
source venv/bin/activate

# Configure Open Interpreter to use our server
interpreter --api_base "$LLM_SERVER_URL" \
           --api_key "$API_KEY" \
           --model "cline-optimized" \
           --auto_run false \
           --max_output 10000