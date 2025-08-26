"""
Custom Open Interpreter with AI-Server Integration
Main entry point for running Open Interpreter with Memory-Server and LLM-Server integration
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

try:
    import interpreter
    from interpreter import interpreter as oi
except ImportError:
    print("❌ Open Interpreter not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "open-interpreter"])
    import interpreter
    from interpreter import interpreter as oi

from config import AIServerInterpreterConfig
from memory_integration import MemoryServerIntegration, memory_server

class AIServerInterpreter:
    """Custom Open Interpreter with AI-Server integration"""
    
    def __init__(self, config_override: Optional[Dict[str, Any]] = None):
        self.config = AIServerInterpreterConfig()
        self.memory = MemoryServerIntegration(
            base_url=self.config.memory_server_url,
            default_workspace=self.config.default_workspace
        )
        
        # Apply configuration
        interpreter_config = self.config.get_interpreter_config()
        if config_override:
            interpreter_config.update(config_override)
        
        self._configure_interpreter(interpreter_config)
        self._setup_custom_functions()
    
    def _configure_interpreter(self, config: Dict[str, Any]):
        """Configure Open Interpreter with AI-Server settings"""
        # Set local model
        oi.local = config.get("local", True)
        oi.model = config.get("model", "deepseek-coder:6.7b-instruct")
        oi.api_base = config.get("api_base", "http://localhost:8000")
        oi.temperature = config.get("temperature", 0.1)
        oi.max_tokens = config.get("max_tokens", 4000)
        oi.auto_run = config.get("auto_run", False)
        
        # Set system message
        oi.system_message = config.get("system_message", "")
        
        # Custom instructions
        if config.get("custom_instructions"):
            oi.system_message += "\n\n" + config["custom_instructions"]
        
        print(f"🤖 Configured AI-Server Interpreter:")
        print(f"   Model: {oi.model}")
        print(f"   LLM Server: {oi.api_base}")
        print(f"   Memory Server: {self.config.memory_server_url}")
        print(f"   Default Workspace: {self.config.default_workspace}")
    
    def _setup_custom_functions(self):
        """Setup custom function integration"""
        # Add Memory-Server functions to interpreter's namespace
        oi.computer.run("python", f"""
# Memory-Server Integration Functions
import sys
sys.path.append('{current_dir}')
from memory_integration import search_memory, upload_content, summarize_content, list_workspaces, track_activity, web_search

def search_docs(query, workspace=None, limit=5):
    \"\"\"Search documents in Memory-Server\"\"\"
    result = search_memory(query, workspace, limit)
    if 'error' in result:
        print(f"❌ Search failed: {{result['error']}}")
        return None
    
    if result.get('results'):
        print(f"🔍 Found {{len(result['results'])}} results for '{{query}}':")
        for i, doc in enumerate(result['results'], 1):
            print(f"{{i}}. {{doc.get('title', 'Untitled')}} (Score: {{doc.get('score', 'N/A')}})")
            print(f"   Workspace: {{doc.get('workspace', 'Unknown')}}")
            print(f"   Summary: {{doc.get('summary', 'No summary available')[:100]}}...")
            print()
    else:
        print(f"🔍 No results found for '{{query}}'")
    return result

def save_to_memory(content, filename, workspace=None, tags=None):
    \"\"\"Save content to Memory-Server\"\"\"
    result = upload_content(content, filename, workspace, tags)
    if 'error' in result:
        print(f"❌ Save failed: {{result['error']}}")
        return None
    
    print(f"✅ Saved to Memory-Server:")
    print(f"   Document ID: {{result.get('document_id', 'Unknown')}}")
    print(f"   Workspace: {{result.get('workspace', 'Unknown')}}")
    print(f"   Status: {{result.get('processing_status', 'Unknown')}}")
    return result

def get_summary(content, summary_type='technical', workspace=None):
    \"\"\"Generate summary using Memory-Server\"\"\"
    result = summarize_content(content, summary_type, workspace)
    if 'error' in result:
        print(f"❌ Summarization failed: {{result['error']}}")
        return None
    
    print(f"📝 Summary ({{result.get('summary_type', 'unknown')}} - {{result.get('confidence', 0)*100:.1f}}% confidence):")
    print(result.get('summary', 'No summary available'))
    return result

def show_workspaces():
    \"\"\"Show available workspaces\"\"\"
    result = list_workspaces()
    if 'error' in result:
        print(f"❌ Failed to list workspaces: {{result['error']}}")
        return None
    
    print(f"📁 Available Workspaces (Active: {{result.get('active_workspace', 'Unknown')}}):")
    for ws in result.get('workspaces', []):
        count = result.get('total_documents', {{}}).get(ws, 0)
        active = " ⭐" if ws == result.get('active_workspace') else ""
        print(f"   - {{ws}}: {{count}} documents{{active}}")
    return result

def search_web_docs(query, search_type='documentation', auto_save=False):
    \"\"\"Search web and optionally save results\"\"\"
    result = web_search(query, search_type, None, auto_save)
    if 'error' in result:
        print(f"❌ Web search failed: {{result['error']}}")
        return None
    
    print(f"🌐 Web Search Results for '{{query}}':")
    for i, item in enumerate(result.get('results', []), 1):
        print(f"{{i}}. {{item.get('title', 'Untitled')}}")
        print(f"   URL: {{item.get('url', 'No URL')}}")
        print(f"   {{item.get('snippet', 'No preview')[:150]}}...")
        print()
    
    if auto_save:
        print(f"💾 Results automatically saved to Memory-Server")
    return result

# Make functions available globally
globals().update({{
    'search_docs': search_docs,
    'save_to_memory': save_to_memory, 
    'get_summary': get_summary,
    'show_workspaces': show_workspaces,
    'search_web_docs': search_web_docs
}})

print("✅ AI-Server integration functions loaded:")
print("   - search_docs(query, workspace=None, limit=5)")
print("   - save_to_memory(content, filename, workspace=None, tags=None)")
print("   - get_summary(content, summary_type='technical', workspace=None)")
print("   - show_workspaces()")
print("   - search_web_docs(query, search_type='documentation', auto_save=False)")
""")
    
    def start_interactive(self):
        """Start interactive session"""
        print("\n🚀 AI-Server Interpreter Ready!")
        print("\n💡 Available Memory-Server commands:")
        print("   • search_docs('query') - Search existing codebase and docs")
        print("   • save_to_memory(content, 'filename.ext') - Save important work")
        print("   • get_summary(content) - Generate technical summaries")
        print("   • show_workspaces() - List available workspaces")
        print("   • search_web_docs('query') - Search web documentation")
        print("\n🎯 Workflow Tips:")
        print("   1. Search existing code first: search_docs('authentication')")
        print("   2. Work on your task")
        print("   3. Save results: save_to_memory(code, 'auth_system.py')")
        print("   4. Generate docs: get_summary(implementation)")
        print()
        
        # Start the interactive session
        oi.chat()
    
    def run_code(self, code: str, language: str = "python") -> Any:
        """Run code and automatically track activity"""
        # Track activity
        asyncio.run(self.memory.track_activity(
            activity_type="code_execution",
            content=code,
            metadata={
                "language": language,
                "executed_by": "ai_server_interpreter"
            }
        ))
        
        # Execute code
        result = oi.computer.run(language, code)
        return result
    
    def chat(self, message: str, auto_save: bool = True) -> Any:
        """Chat with interpreter and optionally save important responses"""
        result = oi.chat(message)
        
        if auto_save and self.config.auto_save_to_memory:
            # Save the conversation to memory
            conversation_content = f"User: {message}\n\nAssistant: {str(result)}"
            asyncio.run(self.memory.upload_content(
                content=conversation_content,
                filename=f"conversation_{int(asyncio.get_event_loop().time())}.md",
                workspace="conversations",
                tags=["open-interpreter", "conversation"],
                auto_summarize=True
            ))
        
        return result

def main():
    """Main entry point"""
    print("🤖 Starting AI-Server Open Interpreter...")
    
    # Check if Memory-Server is running
    import requests
    try:
        response = requests.get("http://localhost:8001/health/status", timeout=5)
        if response.status_code == 200:
            print("✅ Memory-Server is running")
        else:
            print("⚠️  Memory-Server returned unexpected status")
    except requests.exceptions.RequestException:
        print("❌ Memory-Server not accessible at http://localhost:8001")
        print("   Please start Memory-Server first")
        return
    
    # Check if LLM-Server is running
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ LLM-Server is running")
        else:
            print("⚠️  LLM-Server returned unexpected status")
    except requests.exceptions.RequestException:
        print("❌ LLM-Server not accessible at http://localhost:8000")
        print("   Please start LLM-Server first")
        return
    
    # Create and start interpreter
    ai_interpreter = AIServerInterpreter()
    ai_interpreter.start_interactive()

if __name__ == "__main__":
    main()