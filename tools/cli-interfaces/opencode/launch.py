#!/usr/bin/env python3
"""
Quick launcher for AI-Server OpenCode
"""

import sys
import os
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def main():
    """Launch AI-Server OpenCode"""
    print("🚀 Launching AI-Server OpenCode...")
    
    # Import and run
    try:
        from custom_opencode import main as run_opencode
        run_opencode()
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Try installing requirements: pip install -r requirements.txt")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)

if __name__ == "__main__":
    main()