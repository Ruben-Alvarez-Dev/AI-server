#!/usr/bin/env python3
"""
AI-Server Startup Script
Starts all core services with dependency checking
"""

import os
import sys
import time
import subprocess
import threading
import importlib
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent  # Go up one level since we're now in bin/
sys.path.append(str(project_root))

class AIServerManager:
    """Manages AI-Server ecosystem startup with dependency checking"""
    
    def __init__(self):
        self.project_root = project_root
        self.processes = []
        self.threads = []
        self.venv_path = self.project_root / "venv"
        
    def check_and_install_dependencies(self, service_name, requirements_list, install_path=None):
        """Check and install missing dependencies for a service"""
        print(f"🔍 Checking dependencies for {service_name}...")
        
        # Activate virtual environment if it exists
        if self.venv_path.exists():
            venv_python = self.venv_path / "bin" / "python3"
            venv_pip = self.venv_path / "bin" / "pip"
        else:
            print("⚠️ Virtual environment not found, creating one...")
            subprocess.run([sys.executable, "-m", "venv", str(self.venv_path)], check=True)
            venv_python = self.venv_path / "bin" / "python3"
            venv_pip = self.venv_path / "bin" / "pip"
        
        missing_deps = []
        
        # Check each requirement
        for req in requirements_list:
            try:
                subprocess.run([str(venv_python), "-c", f"import {req.split('==')[0].split('>=')[0].split('[')[0].replace('-', '_')}"], 
                             check=True, capture_output=True)
                print(f"  ✅ {req}")
            except subprocess.CalledProcessError:
                missing_deps.append(req)
                print(f"  ❌ {req} - Missing")
        
        # Install missing dependencies
        if missing_deps:
            print(f"📦 Installing {len(missing_deps)} missing dependencies...")
            try:
                subprocess.run([str(venv_pip), "install"] + missing_deps, check=True)
                print("✅ Dependencies installed successfully")
                return True
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to install dependencies: {e}")
                return False
        else:
            print("✅ All dependencies satisfied")
            return True
    
    def start_model_watcher(self):
        """Start Model Watcher in background"""
        try:
            from services.model_watcher.auto_start import start_watcher_background
            thread = start_watcher_background()
            self.threads.append(thread)
            return True
        except Exception as e:
            print(f"⚠️ Model Watcher failed to start: {e}")
            return False
    
    def start_memory_server(self):
        """Start Memory-Server with dependency checking"""
        print("2️⃣ Starting Memory-Server...")
        
        # Memory-Server core dependencies
        memory_deps = [
            "fastapi", "uvicorn", "structlog", "rich", "sentence-transformers", 
            "faiss-cpu", "neo4j", "psutil", "python-multipart", "aiofiles",
            "networkx", "numpy", "torch", "aiohttp"
        ]
        
        # Check and install dependencies
        if not self.check_and_install_dependencies("Memory-Server", memory_deps):
            print("❌ Memory-Server dependencies failed")
            return False
        
        try:
            memory_server_path = self.project_root / "apps" / "memory-server"
            venv_python = self.venv_path / "bin" / "python3"
            
            process = subprocess.Popen(
                [str(venv_python), "-m", "uvicorn", "api.main:app", "--reload", "--port", "8001"],
                cwd=str(memory_server_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.processes.append(process)
            print("✅ Memory-Server starting on http://localhost:8001")
            return True
        except Exception as e:
            print(f"❌ Memory-Server failed to start: {e}")
            return False
    
    def start_llm_server(self):
        """Start LLM-Server with dependency checking"""
        print("3️⃣ Starting LLM-Server...")
        
        # LLM-Server core dependencies  
        llm_deps = [
            "fastapi", "uvicorn", "transformers", "torch", "requests"
        ]
        
        # Check and install dependencies
        if not self.check_and_install_dependencies("LLM-Server", llm_deps):
            print("❌ LLM-Server dependencies failed")
            return False
        
        try:
            llm_server_path = self.project_root / "apps" / "llm-server"
            venv_python = self.venv_path / "bin" / "python3"
            
            process = subprocess.Popen(
                [str(venv_python), "server/main.py"],
                cwd=str(llm_server_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.processes.append(process)
            print("✅ LLM-Server starting on http://localhost:8000")
            return True
        except Exception as e:
            print(f"❌ LLM-Server failed to start: {e}")
            return False
    
    def check_services_health(self):
        """Check if services are running using venv python"""
        print("🏥 Checking services health...")
        
        venv_python = self.venv_path / "bin" / "python3"
        
        # Use venv python to check health endpoints
        health_script = '''
import requests
import time
import sys

time.sleep(5)  # Wait for services to start

services = [
    ("Memory-Server", "http://localhost:8001/health/status"),
    ("LLM-Server", "http://localhost:8000/health")
]

all_healthy = True
for name, url in services:
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"✅ {name} - {url}")
        else:
            print(f"⚠️ {name} - Status {response.status_code}")
            all_healthy = False
    except Exception as e:
        print(f"❌ {name} - {str(e)}")
        all_healthy = False

if all_healthy:
    print("🎉 All services are healthy!")
    sys.exit(0)
else:
    print("⚠️ Some services have issues")
    sys.exit(1)
'''
        
        try:
            result = subprocess.run([str(venv_python), "-c", health_script], 
                                  capture_output=True, text=True, timeout=15)
            print(result.stdout)
            if result.stderr:
                print("Errors:", result.stderr)
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False
    
    def start_all(self):
        """Start all AI-Server services"""
        print("""
╔══════════════════════════════════════╗
║       AI-SERVER ECOSYSTEM v1.0       ║
╚══════════════════════════════════════╝
        """)
        
        print("🚀 Starting services...\n")
        
        # Start Model Watcher
        print("1️⃣ Starting Model Watcher...")
        self.start_model_watcher()
        
        # Start Memory-Server
        print("2️⃣ Starting Memory-Server...")
        self.start_memory_server()
        
        # Start LLM-Server
        print("3️⃣ Starting LLM-Server...")
        self.start_llm_server()
        
        # Check health
        print("\n🏥 Checking services health...")
        self.check_services_health()
        
        print("""
╔══════════════════════════════════════╗
║         ALL SERVICES STARTED         ║
╠══════════════════════════════════════╣
║ Memory-Server: http://localhost:8001 ║
║ LLM-Server:    http://localhost:8000 ║
║ Model Watcher: Running in background ║
╚══════════════════════════════════════╝

📁 Drop models in: assets/models/
🗂️ LLM models: assets/models/llm/
🎯 Embeddings: assets/models/embedding/
👁️ Vision: assets/models/vision/

Press Ctrl+C to stop all services
        """)
        
        # Keep running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.shutdown()
    
    def shutdown(self):
        """Shutdown all services"""
        print("\n🛑 Shutting down AI-Server...")
        
        # Stop processes
        for process in self.processes:
            process.terminate()
            process.wait()
        
        print("👋 AI-Server stopped")
        sys.exit(0)

def main():
    """Main entry point"""
    manager = AIServerManager()
    
    # Create models directory if not exists
    models_dir = project_root / "models"
    models_dir.mkdir(exist_ok=True)
    
    # Start everything
    manager.start_all()

if __name__ == "__main__":
    main()