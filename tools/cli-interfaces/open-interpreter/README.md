# Open Interpreter - AI-Server Integration

Open Interpreter customizado para trabajar seamlessly con Memory-Server y LLM-Server.

## 🚀 Features

- **🧠 Memory-Server Integration**: Búsqueda automática en la base de conocimientos
- **💾 Auto-Save**: Guarda conversaciones y código importante automáticamente  
- **🏷️ Smart Tagging**: Etiquetado inteligente de actividades de desarrollo
- **📝 Auto-Summarization**: Resúmenes técnicos automáticos
- **🗂️ Workspace Management**: Organización por workspaces (code, research, projects)
- **🌐 Web Integration**: Búsqueda web con ingesta automática

## 🛠️ Installation

```bash
cd tools/open-interpreter
pip install -r requirements.txt
```

## 🎯 Usage

### Interactive Mode
```bash
python custom_interpreter.py
```

### Available Functions
```python
# Search existing codebase
search_docs('authentication', workspace='code')

# Save important code
save_to_memory(code, 'auth_system.py', tags=['auth', 'security'])

# Generate technical summaries  
get_summary(implementation, 'technical')

# List workspaces
show_workspaces()

# Web search with auto-save
search_web_docs('FastAPI authentication', auto_save=True)
```

## 🔧 Configuration

Environment variables:
- `MEMORY_SERVER_URL`: Memory-Server endpoint (default: http://localhost:8001)
- `LLM_SERVER_URL`: LLM-Server endpoint (default: http://localhost:8000)
- `DEFAULT_WORKSPACE`: Default workspace (default: code)
- `PREFERRED_MODEL`: LLM model (default: deepseek-coder:6.7b-instruct)

## 🌊 Workflow

1. **Search First**: `search_docs('topic')` - Busca código/docs existentes
2. **Develop**: Trabaja en tu tarea con contexto completo
3. **Save Results**: `save_to_memory(code, 'file.py')` - Guarda trabajo importante
4. **Document**: `get_summary(work)` - Genera documentación técnica

## 🔗 Integration

- Conecta automáticamente con Memory-Server para búsqueda y storage
- Usa LLM-Server para inferencia local optimizada
- Tracking de actividad para mejorar asistencia contextual
- Workspace isolation para diferentes tipos de proyectos