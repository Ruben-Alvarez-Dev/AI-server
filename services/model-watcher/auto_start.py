#!/usr/bin/env python3
"""
Auto-start script for Model Watcher
Can be called from AI-Server startup
"""

import os
import sys
import subprocess
import threading
from pathlib import Path

def start_watcher_background():
    """Start watcher in background thread"""
    watcher_path = Path(__file__).parent / "watcher.py"
    
    def run_watcher():
        try:
            # Add current directory to Python path
            sys.path.insert(0, str(Path(__file__).parent))
            
            # Import and run
            from watcher import start_watcher
            start_watcher()
        except Exception as e:
            print(f"❌ Model Watcher failed: {e}")
    
    # Start in daemon thread
    thread = threading.Thread(target=run_watcher, daemon=True)
    thread.start()
    print("✅ Model Watcher started in background")
    return thread

def start_watcher_subprocess():
    """Start watcher as subprocess"""
    watcher_path = Path(__file__).parent / "watcher.py"
    
    process = subprocess.Popen(
        [sys.executable, str(watcher_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        daemon=True
    )
    
    print(f"✅ Model Watcher started as subprocess (PID: {process.pid})")
    return process

if __name__ == "__main__":
    # If run directly, start as subprocess
    start_watcher_subprocess()
    
    # Keep running
    try:
        import time
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n👋 Stopping Model Watcher")
        sys.exit(0)