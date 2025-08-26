"""
Open Interpreter Configuration for AI-Server Integration
Customizes Open Interpreter to work seamlessly with Memory-Server and LLM-Server
"""

import os
import sys
from pathlib import Path

# Add AI-Server modules to path
ai_server_root = Path(__file__).parent.parent.parent
sys.path.append(str(ai_server_root / "memory-server"))
sys.path.append(str(ai_server_root / "llm-server"))

class AIServerInterpreterConfig:
    """Configuration for AI-Server customized Open Interpreter"""
    
    def __init__(self):
        # Memory-Server integration
        self.memory_server_url = os.getenv("MEMORY_SERVER_URL", "http://localhost:8001")
        self.default_workspace = os.getenv("DEFAULT_WORKSPACE", "code")
        
        # LLM Configuration
        self.llm_provider = os.getenv("LLM_PROVIDER", "local")
        self.llm_model = os.getenv("LLM_MODEL", "deepseek-coder:6.7b-instruct")
        self.llm_api_base = os.getenv("LLM_API_BASE")
        self.llm_api_key = os.getenv("LLM_API_KEY")

        # Open Interpreter settings
        self.auto_save_to_memory = True
        self.enable_activity_tracking = True
        self.workspace_isolation = True
        
        # File system access
        self.allowed_paths = [
            str(ai_server_root),
            os.path.expanduser("~/Documents"),
            os.path.expanduser("~/Downloads")
        ]
        
        # Security settings
        self.require_confirmation = True
        self.sandbox_mode = False  # Set to True for production
        
        # Integration features
        self.features = {
            "memory_integration": True,
            "workspace_management": True, 
            "auto_summarization": True,
            "activity_tracking": True,
            "web_search": True,
            "document_upload": True
        }
    
    def get_system_message(self):
        """Custom system message for AI-Server integration"""
        return f"""You are an AI assistant with access to a comprehensive AI-Server ecosystem:

🗃️ MEMORY-SERVER: Advanced RAG system with LazyGraphRAG and Late Chunking
- Access documents across workspaces: {self.default_workspace}, research, projects, personal
- Smart summarization with multiple types (extractive, abstractive, technical, etc.)
- Intelligent auto-tagging and content analysis

🤖 LLM-SERVER: Configured with {self.llm_provider} using model {self.llm_model}
- Code generation and analysis
- Document processing and summarization
- Technical question answering

🛠️ CAPABILITIES:
- Execute code with automatic workspace documentation
- Search and analyze existing codebase with Memory-Server
- Generate summaries and documentation automatically
- Track development activity for enhanced context
- Web scraping and research with intelligent ingestion

When working on projects:
1. First search Memory-Server for relevant existing code/docs
2. Execute tasks while documenting your work automatically
3. Save important outputs to Memory-Server with proper tagging
4. Generate summaries for complex work for future reference

Always consider the existing codebase context before making changes.
Current workspace: {self.default_workspace}
"""

    def get_interpreter_config(self):
        """Return configuration dict for Open Interpreter"""
        config = {
            "system_message": self.get_system_message(),
            "model": self.llm_model,
            "temperature": 0.1,
            "max_tokens": 4000,
            "safe_mode": self.require_confirmation,
            "auto_run": not self.require_confirmation,
            "custom_instructions": self.get_custom_instructions()
        }

        # Default to local provider if no specific provider is set
        is_local = self.llm_provider in ["local", "lmstudio", "ollama"]
        config["local"] = is_local

        if self.llm_api_base:
            config["api_base"] = self.llm_api_base
        
        if self.llm_api_key:
            config["api_key"] = self.llm_api_key
        elif is_local:
            # For many local servers, API key is not needed or a placeholder
            config["api_key"] = "None"
            
        return config
    
    def get_custom_instructions(self):
        """Custom instructions for enhanced AI-Server integration"""
        return """
MEMORY-SERVER INTEGRATION COMMANDS:
- Use /search <query> [workspace] to search documents
- Use /upload <content> [workspace] to save important findings
- Use /summarize <content> [type] to generate summaries
- Use /workspaces to list available workspaces

DEVELOPMENT WORKFLOW:
1. Always search existing codebase first with /search
2. Document significant code changes automatically
3. Generate technical summaries for complex implementations
4. Tag work appropriately (language, framework, feature, etc.)

BEST PRACTICES:
- Search before implementing to avoid duplication
- Save reusable code snippets to Memory-Server
- Generate documentation for complex solutions
- Use appropriate workspaces for different types of work
"""