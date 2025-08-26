# OpenCode - AI-Server Integration

OpenCode CLI integrado con Memory-Server y el Model Pool de AI-Server.

## 🚀 Features

- **📦 Model Pool Integration**: Usa modelos del pool organizado automáticamente
- **🔍 Memory-Server Search**: Búsqueda de código en tu base de conocimientos
- **💾 Auto-Save**: Guarda snippets importantes automáticamente
- **📝 Technical Summaries**: Resúmenes técnicos de código
- **🗂️ Workspace Aware**: Organización por workspaces
- **📊 Session Tracking**: Tracking de sesiones de desarrollo

## 🛠️ Installation

OpenCode ya está instalado. Esta integración lo conecta con AI-Server.

## 🎯 Configuration

### Environment Variables
```bash
export MEMORY_SERVER_URL="http://localhost:8001"
export DEFAULT_WORKSPACE="code"
```

### Model Selection
OpenCode automáticamente busca modelos en el pool:
1. Busca modelos de código (`llm/code/`)
2. Si no hay, busca modelos generales (`llm/general/`)
3. Usa el mejor modelo disponible

## 💡 Usage

### Interactive Mode
```bash
python custom_opencode.py
# or
python launch.py
```

### Available Commands
```bash
# Search existing codebase
/search authentication implementation

# Save code snippet  
/save "def authenticate(user)..." "auth.py"

# Generate technical summary
/summarize "complex code here"

# List workspaces
/workspaces

# Show session info
/session

# Get help
/help
```

### Workflow Example
```bash
🤖 OpenCode> /search "JWT authentication"
🔍 Found 3 results for JWT...

🤖 OpenCode> /save "def verify_jwt(token)..." "jwt_utils.py" python
💾 Code saved to Memory-Server: doc_123

🤖 OpenCode> /summarize "complex implementation"  
📝 Technical summary generated...
```

## 🔗 Integration Points

### Model Pool
- **Location**: `/models/pool/llm/code/`
- **Auto-detection**: Encuentra el mejor modelo de código disponible
- **Fallback**: Usa modelos generales si no hay específicos de código

### Memory-Server
- **Search**: Acceso completo a la base de conocimientos
- **Upload**: Guarda snippets con auto-tagging
- **Summarization**: Genera resúmenes técnicos
- **Activity**: Tracking de sesiones de desarrollo

## 📁 File Structure

```
tools/cli-interfaces/opencode/
├── custom_opencode.py     # OpenCode con AI-Server integration
├── launch.py             # Launcher script
├── config.py              # Configuración principal
├── memory_integration.py  # Integración con Memory-Server  
├── README.md             # Esta documentación
└── requirements.txt      # Dependencias
```

## 🌊 Workflow

1. **Model Selection**: OpenCode busca en el pool el mejor modelo
2. **Context Search**: Busca código relevante en Memory-Server
3. **Code Generation**: Genera código con contexto completo
4. **Auto Documentation**: Guarda y documenta cambios importantes

## 🔧 Customization

Edita `config.py` para:
- Cambiar categoría de modelo preferida
- Ajustar workspace por defecto
- Configurar features específicas

## 📝 Notes

- OpenCode usa **copias físicas** del pool, no symlinks
- Los modelos se seleccionan automáticamente del pool organizado
- La integración es transparente - OpenCode funciona normal pero mejorado