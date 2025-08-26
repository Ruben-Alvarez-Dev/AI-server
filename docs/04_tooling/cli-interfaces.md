# CLI Interfaces - Enhanced AI Assistants

## 📋 Visión General

**CLI Interfaces** son integraciones personalizadas de herramientas populares de IA (Open Interpreter y OpenCode) optimizadas específicamente para trabajar con el ecosistema AI-Server.

### **Composición del Sistema**
- **Open Interpreter Integration**: AI code executor con memoria persistente
- **OpenCode Integration**: AI coding assistant con context awareness
- **Memory-Server Integration**: Conexión directa con RAG system
- **LLM-Server Integration**: Local LLM processing
- **Workspace Management**: Organización contextual de proyectos

### **Propósito de Diseño**
Crear AI assistants que mantengan contexto completo del proyecto, aprendan de sesiones anteriores y proporcionen asistencia contextual basada en el conocimiento acumulado del equipo.

## 🏗️ Arquitectura de Integración

### **1. Open Interpreter Integration**

#### **Core Configuration (`config.py`)**
```python
class AIServerInterpreterConfig:
    def __init__(self):
        # Memory-Server integration
        self.memory_server_url = "http://localhost:8001"
        self.default_workspace = "code"
        
        # LLM Configuration
        self.llm_provider = "local"
        self.llm_model = "deepseek-coder:6.7b-instruct"
        
        # AI-Server features
        self.features = {
            "memory_integration": True,      # RAG integration
            "workspace_management": True,    # Context isolation  
            "auto_summarization": True,      # Session summaries
            "activity_tracking": True,       # Development tracking
            "web_search": True,             # Research capabilities
            "document_upload": True         # Knowledge ingestion
        }
```

#### **Memory Integration Layer (`memory_integration.py`)**
```python
class MemoryServerIntegration:
    async def search_memory(self, query: str, workspace: str = None) -> Dict:
        """Search existing codebase and documentation"""
        params = {
            "query": query,
            "limit": 5,
            "semantic": True,
            "workspace": workspace or self.default_workspace
        }
        # Returns contextual results from LazyGraphRAG
    
    async def upload_content(self, content: str, filename: str, 
                           workspace: str = None, tags: List[str] = None) -> Dict:
        """Save important code/docs for future reference"""
        # Automatic summarization and intelligent tagging
        # Integration with Late Chunking for optimal retrieval
    
    async def generate_summary(self, content: str, 
                             summary_type: str = "technical") -> Dict:
        """Generate contextual summaries"""
        # Extractive, abstractive, technical, or executive summaries
```

#### **Custom System Prompt**
```python
def get_system_message(self):
    return f"""You are an AI assistant with access to AI-Server ecosystem:

🗃️ MEMORY-SERVER: Advanced RAG with LazyGraphRAG
- Search existing code/docs before implementing
- Auto-save important work with intelligent tagging
- Generate summaries for complex implementations

🤖 LLM-SERVER: Local {self.llm_model}
- Code generation and analysis
- Technical question answering  
- Document processing

WORKFLOW:
1. Search Memory-Server for existing solutions (/search <query>)
2. Execute tasks with automatic documentation
3. Save reusable code to Memory-Server (/upload <content>)
4. Generate summaries for future reference (/summarize <content>)

Current workspace: {self.default_workspace}
"""
```

### **2. Enhanced Command System**

#### **Memory-Server Commands**
```bash
# Search existing codebase
/search "authentication implementation" code

# Upload important code snippets
/upload "JWT authentication utility" --workspace=code --tags=auth,jwt,security

# Generate technical summary
/summarize "Complex async pipeline implementation" --type=technical

# Switch workspace context
/workspace research

# List available workspaces
/workspaces
```

#### **Integration Commands**
```bash
# Web research with ingestion
/research "FastAPI best practices" --ingest=true --workspace=research

# Analyze existing project structure  
/analyze /path/to/project --depth=3 --save-summary=true

# Generate documentation
/document /path/to/code --type=api --upload=true

# Workspace summary
/workspace-summary code --last=7days
```

## 🔄 OpenCode Integration

### **Enhanced Code Assistant**

#### **Context-Aware Coding (`custom_opencode.py`)**
```python
class AIServerOpenCode:
    def __init__(self):
        self.memory = MemoryServerIntegration()
        self.workspace_context = WorkspaceManager()
        self.activity_tracker = ActivityTracker()
    
    async def enhanced_code_completion(self, context: str, cursor_position: int):
        """Context-aware code completion"""
        # 1. Analyze current file context
        file_analysis = self.analyze_current_file(context)
        
        # 2. Search similar patterns in Memory-Server
        similar_code = await self.memory.search_memory(
            query=f"code similar to {file_analysis.function_context}",
            workspace="code"
        )
        
        # 3. Generate completion with full context
        completion = self.generate_with_context(
            current_context=context,
            similar_patterns=similar_code,
            project_context=self.workspace_context.get_current()
        )
        
        # 4. Track coding patterns for improvement
        self.activity_tracker.log_completion(completion, context)
        
        return completion
```

#### **Project Understanding System**
```python
class ProjectContextManager:
    def analyze_project_structure(self, project_path: str) -> ProjectContext:
        """Deep project analysis for better assistance"""
        return ProjectContext(
            frameworks=self.detect_frameworks(project_path),
            architecture_patterns=self.detect_patterns(project_path),
            coding_style=self.analyze_style(project_path),
            dependencies=self.analyze_dependencies(project_path),
            documentation_style=self.analyze_docs(project_path)
        )
    
    def get_contextual_suggestions(self, current_file: str) -> List[Suggestion]:
        """Suggestions based on project context"""
        project_ctx = self.get_project_context()
        file_ctx = self.analyze_file_context(current_file)
        
        return [
            # Framework-specific suggestions
            # Architecture pattern adherence
            # Coding style consistency
            # Documentation completeness
            # Security best practices
        ]
```

## 🛠️ Workspace Management

### **Intelligent Context Isolation**
```python
class WorkspaceManager:
    WORKSPACES = {
        "code": {
            "description": "Active development and coding",
            "auto_tags": ["implementation", "coding", "development"],
            "search_scope": ["code", "documentation"],
            "summary_type": "technical"
        },
        "research": {
            "description": "Research and learning",
            "auto_tags": ["research", "learning", "analysis"],
            "search_scope": ["research", "documentation", "web"],
            "summary_type": "abstractive"
        },
        "projects": {
            "description": "Project planning and management", 
            "auto_tags": ["planning", "project", "management"],
            "search_scope": ["projects", "planning"],
            "summary_type": "executive"
        },
        "personal": {
            "description": "Personal notes and ideas",
            "auto_tags": ["personal", "notes", "ideas"],
            "search_scope": ["personal"],
            "summary_type": "extractive"
        }
    }
    
    def switch_workspace(self, new_workspace: str):
        """Smart workspace switching with context preservation"""
        # Save current session summary
        self.save_session_summary(self.current_workspace)
        
        # Load new workspace context
        self.load_workspace_context(new_workspace)
        
        # Update AI system prompt with new context
        self.update_system_prompt(new_workspace)
```

## 🚀 Installation & Usage

### **Setup Process**
```bash
cd tools/cli-interfaces/

# Setup Open Interpreter
cd open-interpreter/
pip install -r requirements.txt
python3 launch.py

# Setup OpenCode  
cd ../opencode/
pip install -r requirements.txt
python3 launch.py
```

### **Configuration**
```bash
# Environment variables
export MEMORY_SERVER_URL="http://localhost:8001"
export LLM_SERVER_URL="http://localhost:8000" 
export DEFAULT_WORKSPACE="code"
export LLM_MODEL="deepseek-coder:6.7b-instruct"

# Launch with AI-Server integration
python3 tools/cli-interfaces/open-interpreter/launch.py
```

### **Enhanced Workflow Examples**

#### **Research & Implementation**
```bash
# 1. Research phase
/workspace research
/search "FastAPI authentication patterns"
/research "JWT implementation best practices" --ingest=true

# 2. Implementation phase  
/workspace code
/search "authentication implementation" 
# Implement code with context from research
/upload "FastAPI JWT auth implementation" --tags=auth,jwt,fastapi

# 3. Documentation phase
/summarize "JWT authentication system" --type=technical
/document /path/to/auth/module --upload=true
```

#### **Debugging & Problem Solving**
```bash
# Search similar issues
/search "async timeout error handling" code

# Analyze current error with context
/analyze-error "TimeoutError in async pipeline" --context-files=pipeline.py,config.py

# Find related implementations
/search "similar error patterns" --workspace=code --limit=10

# Document solution
/upload "Async timeout handling solution" --tags=async,timeout,debugging
```

## 📊 Performance & Intelligence Features

### **Learning from History**
- **Pattern Recognition**: Aprende de coding patterns previos
- **Error Learning**: Recuerda soluciones a problemas comunes
- **Context Building**: Mejora sugerencias con uso continuado
- **Team Knowledge**: Shared learning entre team members

### **Intelligent Assistance**
- **Proactive Suggestions**: Sugiere mejores approaches basado en historial
- **Code Quality**: Consistency checking contra project patterns
- **Documentation**: Auto-generation basado en coding style
- **Refactoring**: Intelligent refactoring suggestions

### **Integration Benefits**
- **Zero Context Loss**: Nunca pierdes el contexto del proyecto
- **Cumulative Learning**: Knowledge base grows con cada sesión
- **Team Collaboration**: Shared knowledge y patterns
- **Quality Consistency**: Maintains code quality standards

## 🔒 Security & Privacy

### **Access Control**
```python
# Allowed paths configuration
self.allowed_paths = [
    str(ai_server_root),
    os.path.expanduser("~/Documents"),
    os.path.expanduser("~/Downloads")
]

# Security settings
self.require_confirmation = True  # Para code execution
self.sandbox_mode = False        # Production setting
```

### **Data Protection**
- **Local Processing**: Todo processing es local
- **Workspace Isolation**: Complete separation entre workspaces
- **Access Controls**: Configurable file system access
- **Audit Trail**: Complete logging via ATLAS

---

**Estado**: ✅ Completamente implementado y funcional  
**Integration**: Memory-Server, LLM-Server, ATLAS  
**Mantenimiento**: Internal AI-Server team  
**Licencia**: MIT (internal use)