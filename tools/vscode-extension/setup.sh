#!/bin/bash
# VSCode Extension Setup Script
# Part of AI-Server Tools Ecosystem

set -e

echo "🚀 AI-Server VSCode Extension Setup"
echo "=================================="

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "📍 Extension path: $SCRIPT_DIR"
echo "📍 Project root: $PROJECT_ROOT"

# Check prerequisites
echo ""
echo "🔍 Checking prerequisites..."

# Node.js check
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed"
    echo "   Install with: brew install node"
    exit 1
fi
echo "✅ Node.js: $(node --version)"

# NPM check  
if ! command -v npm &> /dev/null; then
    echo "❌ NPM is required but not installed"
    exit 1
fi
echo "✅ NPM: $(npm --version)"

# VSCode check
VSCODE_PATH=""
if [ -d "/Applications/Visual Studio Code.app" ]; then
    VSCODE_PATH="/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code"
elif [ -d "/Applications/Visual Studio Code - Insiders.app" ]; then
    VSCODE_PATH="/Applications/Visual Studio Code - Insiders.app/Contents/Resources/app/bin/code"
else
    echo "⚠️  VSCode not found in Applications"
    echo "   Extension will be packaged but not auto-installed"
fi

if [ -n "$VSCODE_PATH" ] && [ -f "$VSCODE_PATH" ]; then
    echo "✅ VSCode CLI: $VSCODE_PATH"
else
    VSCODE_PATH=""
fi

# Setup process
echo ""
echo "📦 Installing dependencies..."
cd "$SCRIPT_DIR"

# Install Node.js dependencies
npm install

# Install build tools globally if needed
if ! command -v vsce &> /dev/null; then
    echo "📦 Installing vsce (VSCode Extension Manager)..."
    npm install -g @vscode/vsce
fi

echo ""
echo "🔨 Building extension..."

# Compile TypeScript
npm run compile

# Package extension
echo "📦 Packaging extension..."
vsce package --no-yarn

# Find the generated .vsix file
VSIX_FILE=$(ls *.vsix | head -n1)

if [ -z "$VSIX_FILE" ]; then
    echo "❌ Failed to create extension package"
    exit 1
fi

echo "✅ Extension packaged: $VSIX_FILE"

# Install if VSCode is available
if [ -n "$VSCODE_PATH" ]; then
    echo ""
    echo "🔧 Installing extension..."
    "$VSCODE_PATH" --install-extension "$VSIX_FILE"
    echo "✅ Extension installed successfully"
else
    echo ""
    echo "📋 Manual installation required:"
    echo "   1. Open VSCode"
    echo "   2. Command Palette (Ctrl+Shift+P)"
    echo "   3. 'Extensions: Install from VSIX'"
    echo "   4. Select: $SCRIPT_DIR/$VSIX_FILE"
fi

echo ""
echo "🎯 Next steps:"
echo "   1. Restart VSCode"
echo "   2. Look for 'Memory-Server Activity' panel in sidebar"
echo "   3. Configure Memory-Server URL in settings"
echo "   4. Start coding - activity will be tracked automatically!"

echo ""
echo "⚙️  Configuration:"
echo "   • Memory-Server API: http://localhost:8001/api/v1/documents/activity"
echo "   • Default Workspace: code"
echo "   • Extension Settings: File → Preferences → Settings → Memory-Server"

echo ""
echo "✅ Setup complete!"