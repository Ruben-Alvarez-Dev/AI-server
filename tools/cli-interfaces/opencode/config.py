"""
OpenCode Configuration for AI-Server Integration
Customizes OpenCode CLI to work seamlessly with Memory-Server and Model Pool
"""

import os
import sys
from pathlib import Path

# Add AI-Server modules to path
ai_server_root = Path(__file__).parent.parent.parent
sys.path.append(str(ai_server_root))
sys.path.append(str(ai_server_root / "core"))

class OpenCodeConfig:
    """Configuration for OpenCode with AI-Server integration"""
    
    def __init__(self):
        # Memory-Server integration
        self.memory_server_url = os.getenv("MEMORY_SERVER_URL", "http://localhost:8001")
        self.default_workspace = os.getenv("DEFAULT_WORKSPACE", "code")
        
        # Model configuration - uses pool
        self.model_pool_dir = ai_server_root / "models" / "pool"
        self.preferred_model_category = "llm/code"  # OpenCode prefers code models
        
        # OpenCode specific settings
        self.enable_memory_search = True
        self.auto_document_changes = True
        self.use_local_models = True
        
        # Integration features
        self.features = {
            "memory_integration": True,
            "model_pool_access": True,
            "workspace_aware": True,
            "auto_summarization": True,
            "code_analysis": True
        }
    
    def get_model_path(self):
        """Get best code model from pool"""
        try:
            from core.model_finder import ModelFinder
            finder = ModelFinder(self.model_pool_dir)
            
            # Try to find specific code models
            model = finder.find_model(task="code", keywords=["deepseek", "code"])
            if model:
                return str(model)
            
            # Fallback to any code model
            model = finder.find_model(task="code")
            if model:
                return str(model)
                
            # Last resort - any LLM
            model = finder.find_model(task="general")
            if model:
                return str(model)
                
        except Exception as e:
            print(f"⚠️ Could not find model from pool: {e}")
            
        return None
    
    def get_opencode_config(self):
        """Return configuration for OpenCode"""
        model_path = self.get_model_path()
        
        config = {
            "model": model_path if model_path else "deepseek-coder:6.7b",
            "model_type": "gguf" if model_path and model_path.endswith('.gguf') else "default",
            "memory_server": self.memory_server_url,
            "workspace": self.default_workspace,
            "features": self.features,
            "commands": self.get_custom_commands()
        }
        
        return config
    
    def get_custom_commands(self):
        """Custom commands for OpenCode"""
        return {
            "search": {
                "description": "Search Memory-Server for code/docs",
                "endpoint": f"{self.memory_server_url}/api/v1/documents/search",
                "method": "GET"
            },
            "save": {
                "description": "Save code snippet to Memory-Server",
                "endpoint": f"{self.memory_server_url}/api/v1/documents/upload",
                "method": "POST"
            },
            "summarize": {
                "description": "Generate technical summary",
                "endpoint": f"{self.memory_server_url}/api/v1/documents/summarize/content",
                "method": "POST"
            },
            "workspaces": {
                "description": "List available workspaces",
                "endpoint": f"{self.memory_server_url}/api/v1/documents/workspaces",
                "method": "GET"
            }
        }
    
    def get_system_prompt(self):
        """System prompt for OpenCode with AI-Server context"""
        model_info = f"Using model from pool: {self.get_model_path()}" if self.get_model_path() else "No model found in pool"
        
        return f"""You are OpenCode, an AI coding assistant integrated with AI-Server ecosystem.

{model_info}

CAPABILITIES:
- Access to Memory-Server for code search and documentation
- Model pool at: {self.model_pool_dir}
- Current workspace: {self.default_workspace}

WORKFLOW:
1. Search existing code first with Memory-Server
2. Use models from the organized pool
3. Document important changes
4. Generate technical summaries

COMMANDS:
- search <query> - Search codebase
- save <code> - Save to Memory-Server
- summarize <content> - Generate summary
- workspaces - List workspaces
"""