#!/bin/bash

# Embedding Hub Startup Script
# Starts the centralized embedding service with 6 specialized agents

echo "🚀 Starting Embedding Hub Service..."
echo "=================================================="
echo "Port: 8900"
echo "Agents: 6 specialized preprocessing agents"
echo "Model: Nomic Multimodal 7B (Mock for testing)"
echo "=================================================="

# Check if config exists
if [ ! -f "config.yaml" ]; then
    echo "❌ Error: config.yaml not found"
    echo "Please ensure you're running this from the embedding-hub directory"
    exit 1
fi

# Check Python dependencies
echo "📦 Checking Python dependencies..."

REQUIRED_PACKAGES="fastapi uvicorn numpy pyyaml"

for package in $REQUIRED_PACKAGES; do
    if ! python -c "import $package" 2>/dev/null; then
        echo "❌ Missing package: $package"
        echo "Installing required packages..."
        pip install $package
    fi
done

# Set Python path
export PYTHONPATH="${PWD}:${PYTHONPATH}"

echo "✅ Dependencies checked"
echo ""

# Start the service
echo "🎯 Starting Embedding Hub on port 8900..."
echo "Available endpoints:"
echo "  • http://localhost:8900/embed/late-chunking  (Late Chunking specialist)"
echo "  • http://localhost:8900/embed/code           (Code specialist)"
echo "  • http://localhost:8900/embed/conversation   (Conversation specialist)"
echo "  • http://localhost:8900/embed/visual         (Visual specialist)" 
echo "  • http://localhost:8900/embed/query          (Query specialist)"
echo "  • http://localhost:8900/embed/community      (Community specialist)"
echo ""
echo "📊 Status endpoint: http://localhost:8900/status"
echo "❤️  Health check: http://localhost:8900/health"
echo ""
echo "Press Ctrl+C to stop the service"
echo "=================================================="

# Start the server
python server.py