#!/bin/bash

# AI-Server - Unified Startup Script
# Starts all components as a single orchestrated system

set -e

echo "🤖 Starting AI-Server - M1 Ultra Optimization"
echo "=================================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_DIR="$(dirname "$0")"
R2R_DIR="${BASE_DIR}/../R2R"
LOGS_DIR="${BASE_DIR}/logs"
PID_FILE="${BASE_DIR}/orchestra.pid"

# Create necessary directories
mkdir -p "$LOGS_DIR"
mkdir -p "$R2R_DIR"

# Function to log messages
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
}

# Cleanup function
cleanup() {
    log "🛑 Shutting down AI-Server..."
    
    # Stop R2R Docker containers
    if [ -d "$R2R_DIR" ]; then
        cd "$R2R_DIR"
        docker compose -f compose.full.yaml down 2>/dev/null || true
    fi
    
    # Kill background processes
    if [ -f "$PID_FILE" ]; then
        while IFS= read -r pid; do
            kill "$pid" 2>/dev/null || true
        done < "$PID_FILE"
        rm -f "$PID_FILE"
    fi
    
    log "✅ AI-Server shutdown complete"
}

# Set trap for cleanup on exit
trap cleanup EXIT INT TERM

# Check system requirements
check_requirements() {
    log "🔍 Checking system requirements..."
    
    # Check RAM
    TOTAL_RAM=$(sysctl -n hw.memsize)
    TOTAL_RAM_GB=$((TOTAL_RAM / 1024 / 1024 / 1024))
    
    if [ "$TOTAL_RAM_GB" -lt 64 ]; then
        error "Insufficient RAM: ${TOTAL_RAM_GB}GB (minimum 64GB required)"
        exit 1
    fi
    
    log "✅ RAM Check: ${TOTAL_RAM_GB}GB available"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker not found. Please install Docker Desktop."
        exit 1
    fi
    
    log "✅ Docker available: $(docker --version)"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        error "Python 3 not found."
        exit 1
    fi
    
    log "✅ Python available: $(python3 --version)"
}

# Setup R2R if not exists
setup_r2r() {
    log "🐳 Setting up R2R RAG System..."
    
    if [ ! -d "$R2R_DIR/.git" ]; then
        info "Cloning R2R repository..."
        git clone https://github.com/SciPhi-AI/R2R.git "$R2R_DIR"
    else
        info "R2R already exists, pulling latest updates..."
        cd "$R2R_DIR"
        git pull origin main
    fi
    
    cd "$R2R_DIR"
    
    # Configure R2R for local use
    export R2R_CONFIG_NAME=full
    export POSTGRES_PASSWORD="secure_password_$(date +%s)"
    export POSTGRES_USER=r2r_user
    export POSTGRES_DB=r2r_db
    
    log "✅ R2R configured with local settings"
}

# Start R2R system
start_r2r() {
    log "🚀 Starting R2R RAG System..."
    
    cd "$R2R_DIR"
    
    # Start R2R with Docker Compose
    docker compose -f compose.full.yaml --profile postgres up -d
    
    # Wait for R2R to be ready
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:7272/health > /dev/null 2>&1; then
            log "✅ R2R is ready at http://localhost:7272"
            break
        fi
        
        ((attempt++))
        info "Waiting for R2R... attempt $attempt/$max_attempts"
        sleep 2
    done
    
    if [ $attempt -eq $max_attempts ]; then
        error "R2R failed to start after $max_attempts attempts"
        exit 1
    fi
}

# Start Memory Server
start_memory_server() {
    log "🧠 Starting Modular Memory System..."
    
    cd "$BASE_DIR"
    
    # Start memory server in background
    python3 -m rag_components.memory.modular > "$LOGS_DIR/memory_server.log" 2>&1 &
    local memory_pid=$!
    echo "$memory_pid" >> "$PID_FILE"
    
    log "✅ Memory Server started (PID: $memory_pid)"
}

# Start LLM Server
start_llm_server() {
    log "🤖 Starting LLM Server with 6-Agent Orchestra..."
    
    cd "$BASE_DIR"
    
    # Start main LLM server
    python3 -m server.main > "$LOGS_DIR/llm_server.log" 2>&1 &
    local llm_pid=$!
    echo "$llm_pid" >> "$PID_FILE"
    
    # Wait for server to be ready
    local max_attempts=20
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            log "✅ LLM Server ready at http://localhost:8000"
            break
        fi
        
        ((attempt++))
        info "Waiting for LLM Server... attempt $attempt/$max_attempts"
        sleep 3
    done
    
    if [ $attempt -eq $max_attempts ]; then
        error "LLM Server failed to start"
        exit 1
    fi
    
    log "✅ LLM Server started (PID: $llm_pid)"
}

# Display system status
show_status() {
    log "📊 AI Orchestra Status Dashboard"
    echo "=================================="
    echo "🐳 R2R RAG System:      http://localhost:7272"
    echo "🤖 LLM Server API:      http://localhost:8000"
    echo "📚 API Documentation:   http://localhost:8000/docs"
    echo "🔍 Health Check:        http://localhost:8000/health"
    echo "📋 System Stats:        http://localhost:8000/monitoring/stats"
    echo ""
    echo "📁 Logs Directory:      $LOGS_DIR"
    echo "🔧 PID File:            $PID_FILE"
    echo ""
    
    # Show memory usage
    local mem_info=$(vm_stat | grep "Pages free" | awk '{print $3}' | tr -d '.')
    local free_gb=$((mem_info * 16384 / 1024 / 1024 / 1024))
    echo "💾 Available RAM:       ${free_gb}GB"
    echo ""
    
    log "✅ AI Orchestra is fully operational!"
    echo ""
    echo "Press Ctrl+C to shutdown the entire system"
}

# Main execution
main() {
    log "🎭 Initializing AI Orchestra..."
    
    check_requirements
    setup_r2r
    start_r2r
    start_memory_server
    start_llm_server
    show_status
    
    # Keep script running to maintain all services
    log "🎶 AI Orchestra running... (Press Ctrl+C to stop)"
    
    # Monitor services
    while true; do
        sleep 30
        
        # Check if R2R is still running
        if ! curl -s http://localhost:7272/health > /dev/null 2>&1; then
            warning "R2R appears to be down, attempting restart..."
            start_r2r
        fi
        
        # Check if LLM Server is still running
        if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
            warning "LLM Server appears to be down, attempting restart..."
            start_llm_server
        fi
    done
}

# Run main function
main