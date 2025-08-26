#!/usr/bin/env python3
"""
Setup script for LLM Server
Initializes the environment and downloads required models
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from scripts.install_llama_cpp import LlamaCppInstaller
from scripts.download_models import ModelDownloader


async def setup_llm_server():
    """Complete setup process for LLM Server"""
    print("🚀 Setting up LLM Server...")
    
    try:
        # Step 1: Install llama.cpp with M1 Ultra optimizations
        print("\n📦 Installing llama-cpp-python with M1 Ultra optimizations...")
        installer = LlamaCppInstaller()
        installer.install()
        
        # Step 2: Download required models
        print("\n📥 Downloading AI models...")
        downloader = ModelDownloader("./models")
        await downloader.download_all_models()
        
        print("\n✅ LLM Server setup completed successfully!")
        print("\nNext steps:")
        print("1. Review configuration in .env file")
        print("2. Run: python -m llm_server.server.main")
        print("3. Access API documentation at: http://localhost:8000/docs")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(setup_llm_server())