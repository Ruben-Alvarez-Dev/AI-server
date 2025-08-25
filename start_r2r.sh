#!/bin/bash

# AI-SERVER - R2R RAG System Manager
# Persistent R2R Docker management

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

# Configuration
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
R2R_DIR="${BASE_DIR}/R2R/R2R"

# Function to check R2R status
check_r2r_status() {
    if curl -s http://localhost:7272/v3/health > /dev/null 2>&1; then
        return 0  # Running
    else
        return 1  # Not running
    fi
}

# Function to start R2R
start_r2r() {
    echo -e "${BLUE}🐳 Starting R2R RAG System...${NC}"
    
    if [ ! -d "$R2R_DIR" ]; then
        echo -e "${RED}❌ R2R directory not found: $R2R_DIR${NC}"
        exit 1
    fi

    cd "$R2R_DIR/docker"
    
    # Start R2R with Docker Compose
    echo -e "${CYAN}   Starting R2R containers...${NC}"
    docker compose -f compose.full.yaml --profile postgres up -d
    
    # Wait for R2R with real-time feedback
    echo -e "${YELLOW}⏳ Waiting for R2R to start...${NC}"
    max_attempts=60
    attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if check_r2r_status; then
            echo -e "\n${GREEN}✅ R2R RAG System is ready!${NC}"
            return 0
        fi
        
        ((attempt++))
        echo -ne "${CYAN}   Checking R2R... attempt $attempt/$max_attempts\r${NC}"
        sleep 1
    done
    
    echo -e "\n${RED}❌ R2R failed to start after $max_attempts seconds${NC}"
    return 1
}

# Function to stop R2R
stop_r2r() {
    echo -e "${YELLOW}🛑 Stopping R2R RAG System...${NC}"
    cd "$R2R_DIR/docker"
    docker compose -f compose.full.yaml down
    echo -e "${GREEN}✅ R2R stopped${NC}"
}

# Function to show R2R status
show_status() {
    if check_r2r_status; then
        echo -e "${GREEN}✅ R2R RAG System is running${NC}"
        echo -e "${WHITE}📡 R2R API: ${CYAN}http://localhost:7272${NC}"
        echo -e "${WHITE}❤️  Health: ${CYAN}http://localhost:7272/health${NC}"
    else
        echo -e "${RED}❌ R2R RAG System is not running${NC}"
    fi
}

# Main logic
case "${1:-status}" in
    start)
        echo -e "${PURPLE}🤖 AI-SERVER - R2R Manager${NC}"
        echo "=============================="
        echo ""
        
        if check_r2r_status; then
            echo -e "${GREEN}✅ R2R is already running${NC}"
            show_status
        else
            start_r2r
            show_status
        fi
        ;;
        
    stop)
        if check_r2r_status; then
            stop_r2r
        else
            echo -e "${YELLOW}⚠️  R2R is not running${NC}"
        fi
        ;;
        
    restart)
        echo -e "${PURPLE}🤖 AI-SERVER - R2R Restart${NC}"
        echo "==============================="
        echo ""
        
        if check_r2r_status; then
            stop_r2r
            sleep 2
        fi
        start_r2r
        show_status
        ;;
        
    status)
        show_status
        ;;
        
    logs)
        cd "$R2R_DIR/docker"
        docker compose -f compose.full.yaml logs -f
        ;;
        
    *)
        echo -e "${WHITE}AI-SERVER R2R Manager${NC}"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  start    - Start R2R if not running"
        echo "  stop     - Stop R2R"  
        echo "  restart  - Restart R2R"
        echo "  status   - Show R2R status (default)"
        echo "  logs     - Show R2R logs"
        echo ""
        exit 1
        ;;
esac