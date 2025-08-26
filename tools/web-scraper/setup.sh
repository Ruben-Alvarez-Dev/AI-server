#!/bin/bash
# AI-Server Web Scraper Setup Script
# Installs Playwright and dependencies for web scraping

set -e

echo "🌐 AI-Server Web Scraper Setup"
echo "=============================="

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "📍 Tool path: $SCRIPT_DIR"
echo "📍 Project root: $PROJECT_ROOT"

# Check if virtual environment exists
VENV_PATH="$PROJECT_ROOT/venv"
if [ ! -d "$VENV_PATH" ]; then
    echo "❌ Virtual environment not found at $VENV_PATH"
    echo "   Please run the main AI-Server setup first"
    exit 1
fi

echo "✅ Using virtual environment: $VENV_PATH"

# Activate virtual environment
source "$VENV_PATH/bin/activate"

echo ""
echo "📦 Installing Python dependencies..."
pip install -r "$SCRIPT_DIR/requirements.txt"

echo ""
echo "🎭 Installing Playwright browsers..."
playwright install

echo ""
echo "✅ Web Scraper setup complete!"
echo ""
echo "🎯 Usage examples:"
echo "   # Scrape a website"
echo "   python3 $SCRIPT_DIR/scraper.py https://example.com"
echo ""
echo "   # Output goes to: example_com.md (ready for Memory-Server)"
echo ""
echo "🔗 Integration:"
echo "   • Output files are optimized for Memory-Server ingestion"
echo "   • Use Memory-Server document upload API to ingest scraped content"
echo "   • Supports JavaScript-heavy sites with full page rendering"