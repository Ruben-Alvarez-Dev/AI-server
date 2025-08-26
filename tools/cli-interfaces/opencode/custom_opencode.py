"""
Custom OpenCode with AI-Server Integration
Main entry point for running OpenCode with Memory-Server integration
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
    # Try to import opencode if installed
    import opencode
except ImportError:
    print("❌ OpenCode not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "opencode"])
    try:
        import opencode
    except ImportError:
        print("⚠️  OpenCode installation failed. Using fallback mode.")
        opencode = None

from config import OpenCodeConfig
from memory_integration import OpenCodeMemoryIntegration, search_code, save_snippet, summarize_code, track_session

class AIServerOpenCode:
    """Custom OpenCode with AI-Server integration"""
    
    def __init__(self, config_override: Optional[Dict[str, Any]] = None):
        self.config = OpenCodeConfig()
        self.memory = OpenCodeMemoryIntegration(
            base_url=self.config.memory_server_url,
            default_workspace=self.config.default_workspace
        )
        
        # Apply configuration
        opencode_config = self.config.get_opencode_config()
        if config_override:
            opencode_config.update(config_override)
        
        self._configure_opencode(opencode_config)
        self._setup_custom_functions()
        
        # Track session start
        self.session_start_time = asyncio.get_event_loop().time()
        self.files_edited = []
        self.languages_used = set()
    
    def _configure_opencode(self, config: Dict[str, Any]):
        """Configure OpenCode with AI-Server settings"""
        print(f"🤖 Configured AI-Server OpenCode:")
        print(f"   Model: {config.get('model', 'Not specified')}")
        print(f"   Memory Server: {config.get('memory_server')}")
        print(f"   Default Workspace: {config.get('workspace')}")
        
        # Store config for use in functions
        self.opencode_config = config
    
    def _setup_custom_functions(self):
        """Setup custom function integration for OpenCode"""
        # Create a custom command processor
        self.commands = {
            'search': self.cmd_search,
            'save': self.cmd_save,
            'summarize': self.cmd_summarize,
            'workspaces': self.cmd_workspaces,
            'session': self.cmd_session_info,
            'help': self.cmd_help
        }
        
        print("\n✅ AI-Server integration functions loaded:")
        print("   Commands available:")
        for cmd, func in self.commands.items():
            print(f"   - /{cmd}")
    
    def cmd_search(self, query: str, workspace: Optional[str] = None) -> None:
        """Search for code in Memory-Server"""
        print(f"🔍 Searching for: {query}")
        result = search_code(query, workspace)
        
        if result.get('success'):
            results = result.get('results', [])
            if results:
                print(f"\n📚 Found {len(results)} results:")
                for i, doc in enumerate(results[:5], 1):
                    print(f"\n{i}. {doc.get('title', 'Untitled')}")
                    print(f"   Score: {doc.get('score', 'N/A')}")
                    print(f"   Workspace: {doc.get('workspace', 'Unknown')}")
                    if doc.get('summary'):
                        print(f"   Summary: {doc['summary'][:150]}...")
                    if doc.get('code_snippet'):
                        print(f"   Code Preview:")
                        print(f"   {doc['code_snippet'][:200]}...")
            else:
                print("No results found.")
        else:
            print(f"❌ Search failed: {result.get('error')}")
    
    def cmd_save(self, code: str, filename: str, language: Optional[str] = None, tags: Optional[List[str]] = None) -> None:
        """Save code snippet to Memory-Server"""
        print(f"💾 Saving code to: {filename}")
        
        # Auto-detect language from filename if not provided
        if not language and '.' in filename:
            ext = filename.split('.')[-1]
            language_map = {
                'py': 'python', 'js': 'javascript', 'ts': 'typescript',
                'java': 'java', 'cpp': 'cpp', 'c': 'c', 'cs': 'csharp',
                'go': 'go', 'rs': 'rust', 'rb': 'ruby', 'php': 'php'
            }
            language = language_map.get(ext, ext)
        
        result = save_snippet(
            code=code,
            filename=filename,
            language=language,
            tags=tags
        )
        
        if result.get('success'):
            print(f"✅ {result.get('message')}")
            print(f"   Document ID: {result.get('document_id')}")
            self.files_edited.append(filename)
            if language:
                self.languages_used.add(language)
        else:
            print(f"❌ Save failed: {result.get('error')}")
    
    def cmd_summarize(self, code: str, summary_type: str = "technical") -> None:
        """Generate summary of code"""
        print(f"📝 Generating {summary_type} summary...")
        result = summarize_code(code, summary_type)
        
        if result.get('success'):
            print(f"\n📋 Summary (Confidence: {result.get('confidence', 0)*100:.1f}%):")
            print(result.get('summary'))
        else:
            print(f"❌ Summarization failed: {result.get('error')}")
    
    def cmd_workspaces(self) -> None:
        """List available workspaces"""
        print("📁 Fetching workspaces...")
        
        # Use async to get workspaces
        async def get_workspaces():
            result = await self.memory.list_workspaces()
            return result
        
        try:
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(get_workspaces())
            
            if 'workspaces' in result:
                print(f"\n📂 Available Workspaces (Active: {result.get('active_workspace', 'none')}):")
                for ws in result['workspaces']:
                    count = result.get('total_documents', {}).get(ws, 0)
                    active = " ⭐" if ws == result.get('active_workspace') else ""
                    print(f"   - {ws}: {count} documents{active}")
            else:
                print("❌ Could not fetch workspaces")
        except Exception as e:
            print(f"❌ Error fetching workspaces: {e}")
    
    def cmd_session_info(self) -> None:
        """Show current session information"""
        duration = int((asyncio.get_event_loop().time() - self.session_start_time) / 60)
        
        print("\n📊 Current Session:")
        print(f"   Duration: {duration} minutes")
        print(f"   Files edited: {len(self.files_edited)}")
        if self.files_edited:
            for f in self.files_edited[-5:]:
                print(f"     - {f}")
        print(f"   Languages used: {', '.join(self.languages_used) if self.languages_used else 'None'}")
        print(f"   Workspace: {self.config.default_workspace}")
    
    def cmd_help(self) -> None:
        """Show help for available commands"""
        print("\n💡 AI-Server OpenCode Commands:")
        print("\n🔍 Search & Discovery:")
        print("   /search <query> [workspace] - Search for code/documentation")
        print("\n💾 Save & Document:")
        print("   /save <code> <filename> [language] [tags] - Save code snippet")
        print("   /summarize <code> [type] - Generate technical summary")
        print("\n📁 Organization:")
        print("   /workspaces - List available workspaces")
        print("   /session - Show current session info")
        print("\n❓ Help:")
        print("   /help - Show this help message")
        print("\n🎯 Workflow Tips:")
        print("   1. Search first: /search authentication")
        print("   2. Save important work: /save 'code' 'auth.py'")
        print("   3. Document complex code: /summarize 'implementation'")
    
    def process_command(self, input_text: str) -> bool:
        """Process custom commands"""
        if not input_text.startswith('/'):
            return False
        
        parts = input_text[1:].split(maxsplit=1)
        if not parts:
            return False
        
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if cmd in self.commands:
            try:
                # Parse arguments based on command
                if cmd == 'search':
                    self.commands[cmd](args)
                elif cmd == 'save':
                    # Expecting: code filename [language] [tags]
                    # Simple parsing - in real use would need better parsing
                    self.commands[cmd](args, f"snippet_{asyncio.get_event_loop().time()}.txt")
                elif cmd == 'summarize':
                    self.commands[cmd](args)
                else:
                    self.commands[cmd]()
                return True
            except Exception as e:
                print(f"❌ Command error: {e}")
                return True
        
        return False
    
    def start_interactive(self):
        """Start interactive session"""
        print("\n🚀 AI-Server OpenCode Ready!")
        print("\n💡 Available Memory-Server commands:")
        print("   Type /help for all commands")
        print("\n🎯 Quick Start:")
        print("   /search <query> - Search existing code")
        print("   /save <code> <filename> - Save your work")
        print("   /summarize <code> - Generate documentation")
        print()
        
        # Main interactive loop
        while True:
            try:
                user_input = input("\n🤖 OpenCode> ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'q']:
                    self.shutdown()
                    break
                
                # Check for custom commands
                if self.process_command(user_input):
                    continue
                
                # If OpenCode is available, pass through
                if opencode:
                    print("⚠️  Standard OpenCode integration not yet implemented")
                    print("   Use Memory-Server commands (starting with /) for now")
                else:
                    print("💬 " + user_input)
                    print("   (OpenCode not installed - using command mode only)")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                self.shutdown()
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def shutdown(self):
        """Clean shutdown with session tracking"""
        duration = int((asyncio.get_event_loop().time() - self.session_start_time) / 60)
        
        if duration > 1 and (self.files_edited or self.languages_used):
            print("\n📊 Saving session data...")
            result = track_session(
                files=self.files_edited,
                languages=list(self.languages_used),
                duration=duration,
                description=f"OpenCode session with {len(self.files_edited)} files"
            )
            if result.get('success'):
                print("✅ Session tracked in Memory-Server")
        
        # Close memory connection
        asyncio.run(self.memory.close())
        print("👋 OpenCode session ended")

def main():
    """Main entry point"""
    print("🤖 Starting AI-Server OpenCode...")
    
    # Check if Memory-Server is running
    import requests
    try:
        response = requests.get("http://localhost:8001/health/status", timeout=5)
        if response.status_code == 200:
            print("✅ Memory-Server is running")
        else:
            print("⚠️  Memory-Server returned unexpected status")
    except requests.exceptions.RequestException:
        print("⚠️  Memory-Server not accessible at http://localhost:8001")
        print("   Some features may not work")
    
    # Create and start OpenCode
    ai_opencode = AIServerOpenCode()
    ai_opencode.start_interactive()

if __name__ == "__main__":
    main()