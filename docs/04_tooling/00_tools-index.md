# AI-Server Tools & Components - Master Index

## 📋 Visión General

**AI-Server Tools Ecosystem** - Conjunto completo de herramientas desarrolladas internamente para crear un ecosistema AI empresarial completamente integrado y automatizado.

### **Philosophy de Diseño**
Todas las herramientas siguen principios consistentes:
- **Local-First**: Processing completamente local
- **Auto-Integration**: Conexión automática entre componentes  
- **Enterprise-Grade**: Estándares de reliability y security
- **Zero-Config**: Funcionamiento inmediato sin configuración
- **Intelligent**: Automated decision making y learning

---

## 🏗️ Core Tools Architecture

```
AI-Server Ecosystem
├── 🔒 ATLAS (Audit & Logging)          # Backbone de auditoría
├── 🧠 Memory-Server Integration         # RAG system connectivity  
├── 💻 Development Tools                 # Coding assistance
├── 🌐 Research & Ingestion             # Knowledge acquisition
├── 🔌 External Integrations            # Third-party connectivity
└── 🎯 Background Services              # System optimization
```

---

## 🔒 **1. ATLAS - Automated Logging System**

### **Propósito**
Sistema de auditoría automática inmutable que registra **cada operación** sin intervención humana.

### **Componentes Técnicos**
- **Core Engine**: `logs/core/session_logger.py`
- **Security Layer**: `logs/core/enforcer.py` 
- **Integration Hooks**: `logs/core/claude_hooks.py`
- **Initialization**: `logs/scripts/init-logging-system.sh`

### **Capacidades Clave**
- ✅ **Blockchain-style integrity** con hash linking
- ✅ **Zero-tolerance enforcement** (no se puede desactivar)
- ✅ **Automatic integration** con Git, VSCode, Claude Code
- ✅ **Enterprise compliance** (SOX, GDPR, ISO27001 ready)

### **Integration Points**
```python
from logs.core import logger
logger.log_operation("my_operation", "Description", {"data": "value"})
```

**📄 Documentation**: [ATLAS - Automated Logging System](automated-logging-system.md)

---

## 💻 **2. VSCode Activity Tracker Extension**

### **Propósito** 
Extensión VSCode que captura **toda la actividad de development** y la envía al Memory-Server para procesamiento RAG.

### **Arquitectura**
- **Language**: TypeScript 5.9.2 + Node.js 18+
- **Event System**: Real-time capture de editing, debugging, terminal
- **Buffer Management**: Async processing con offline resilience
- **Security**: Pattern-based redaction y data protection

### **Eventos Capturados**
- `edit` - Cambios en archivos con diff tracking
- `openFile/closeFile` - File access patterns
- `commit` - Git activity con metadata completa
- `debug` - Debugging sessions y breakpoints
- `terminal` - Command execution tracking

### **Workspace Intelligence**
```typescript
workspaces: ['code', 'research', 'projects', 'personal']
// Auto-tagging contextual por workspace
```

**📄 Documentation**: [VSCode Activity Tracker Extension](vscode-activity-tracker.md)

---

## 🌐 **3. Web Scraper Tool** 

### **Propósito**
Herramienta para extraer automáticamente documentación completa de sitios web y convertirla a Markdown para ingesta RAG.

### **Engine**
- **Browser**: Playwright Chromium automation
- **JavaScript**: Full SPA support con networkidle detection
- **Output**: Unified markdown con preserved structure
- **Processing**: Async single-page crawler

### **Workflow**
```bash
python3 tools/web-scraper/scraper.py https://docs.example.com/
# Output: docs_example_com.md (ready for Memory-Server ingestion)
```

### **Capabilities**
- ✅ **JavaScript-aware** scraping (React, Vue, Angular)
- ✅ **Domain-scoped** crawling para focused ingestion
- ✅ **Structure preservation** con consistent formatting
- ✅ **Memory-Server ready** output format

**📄 Documentation**: [Web Scraper Tool](web-scraper.md)

---

## 🤖 **4. CLI Interfaces - Enhanced AI Assistants**

### **Propósito**
Integraciones customizadas de Open Interpreter y OpenCode optimizadas específicamente para AI-Server ecosystem.

### **Components**
- **Open Interpreter Integration**: AI code executor con persistent memory
- **OpenCode Integration**: Context-aware coding assistant  
- **Memory-Server Integration**: Direct RAG connectivity
- **Workspace Management**: Contextual project organization

### **Enhanced Capabilities**
```python
# Memory-Server integration
/search "authentication patterns" code
/upload "JWT utility implementation" --tags=auth,jwt
/summarize "Complex async pipeline" --type=technical
/workspace research  # Switch context
```

### **AI Enhancement Features**
- **Context Preservation**: Nunca pierde project context
- **Learning System**: Mejora con cada sesión 
- **Pattern Recognition**: Aprende team coding styles
- **Intelligent Suggestions**: Proactive code assistance

**📄 Documentation**: [CLI Interfaces](cli-interfaces.md)

---

## 🔌 **5. MCP Servers - Model Context Protocol**

### **Propósito**
Implementación MCP que expone AI-Server capabilities como tools utilizables por Claude Desktop y otros MCP clients.

### **Architecture**
- **Protocol**: MCP v1.0 con stdio transport
- **Type Safety**: Zod schemas para validation
- **Integration**: Direct Memory-Server API calls
- **Error Handling**: Robust fallback mechanisms

### **Available Tools**
```typescript
tools: [
  'memory_search',      // Advanced RAG search
  'document_upload',    // Content ingestion with LazyGraphRAG
  'web_scrape',         // Automated web content extraction  
  'web_search',         // Intelligent search con auto-ingestion
  'summarize_content',  // Multi-type summarization
  'track_activity'      // Development activity logging
]
```

### **Claude Desktop Integration**
```json
// claude_desktop_config.json
{
  "mcpServers": {
    "memory-server": {
      "command": "node",
      "args": ["/.../memory-server-mcp/dist/index.js"]
    }
  }
}
```

**📄 Documentation**: [MCP Servers](mcp-servers.md)

---

## 🎯 **6. Model Watcher Service**

### **Propósito**
Background service que monitorea automáticamente `/assets/models/` y organiza modelos AI en estructura categorizada.

### **Intelligence System**
```python
classification_rules = {
    'llm/code': ['code', 'coder', 'starcoder'],
    'llm/chat': ['chat', 'instruct', 'assistant'], 
    'embedding': ['embed', 'e5', 'bge', 'sentence'],
    'multimodal': ['llava', 'vision', 'clip']
}
```

### **Pool Organization**
```
assets/models/pool/
├── llm/code/           # Programming models
├── llm/chat/           # Conversational models
├── embedding/          # Vector models  
├── multimodal/         # Vision models
└── uncategorized/      # Unclassified
```

### **Features**
- ✅ **Real-time monitoring** con watchdog
- ✅ **Intelligent categorization** by filename patterns
- ✅ **Symbolic linking** para avoid duplication
- ✅ **Registry system** con metadata y checksums

**📄 Documentation**: [Model Watcher Service](model-watcher.md)

---

## 🔄 Integration Matrix

### **Cross-Component Communication**

| Component | ATLAS | VSCode Ext | Web Scraper | CLI Tools | MCP | Model Watcher |
|-----------|-------|------------|-------------|-----------|-----|---------------|
| **ATLAS** | - | ✅ Logs | ✅ Logs | ✅ Logs | ✅ Logs | ✅ Logs |
| **VSCode Extension** | 📝 Logged | - | ❌ None | 🔗 Shared Memory | ❌ None | ❌ None |
| **Web Scraper** | 📝 Logged | ❌ None | - | 🔗 CLI invoke | 🔗 MCP tool | ❌ None |
| **CLI Tools** | 📝 Logged | 🔗 Activity | 🔗 Research | - | ❌ None | 🔗 Model query |
| **MCP Servers** | 📝 Logged | ❌ None | 🔗 Web tools | ❌ None | - | ❌ None |
| **Model Watcher** | 📝 Logged | ❌ None | ❌ None | 🔗 Recommendations | ❌ None | - |

### **Data Flow Architecture**
```
User Activity → VSCode Extension → Memory-Server (RAG)
                     ↓
User Commands → CLI Tools → Memory-Server + LLM-Server
                     ↓                    
Claude Desktop → MCP Server → Memory-Server API
                     ↓
Web Research → Web Scraper → Document Ingestion
                     ↓
All Operations → ATLAS → Immutable Audit Trail
```

---

## 🚀 Installation & Setup Guide

### **Complete Ecosystem Setup**
```bash
# 1. Initialize ATLAS (mandatory logging)
./logs/scripts/init-logging-system.sh

# 2. Setup VSCode Extension
cd tools/vscode-activity-tracker/
./build-extension.sh
code --install-extension *.vsix

# 3. Configure CLI Tools
cd tools/cli-interfaces/open-interpreter/
python3 launch.py

# 4. Build MCP Server
cd tools/mcp-servers/memory-server-mcp/
npm install && npm run build

# 5. Start Model Watcher
python3 services/model-watcher/auto_start.py

# 6. Verify ecosystem
./logs/scripts/verify-logs.sh
```

### **Environment Variables**
```bash
# Memory-Server connectivity
export MEMORY_SERVER_URL="http://localhost:8001"
export LLM_SERVER_URL="http://localhost:8000"

# Default workspace
export DEFAULT_WORKSPACE="code"

# Model configuration  
export LLM_MODEL="deepseek-coder:6.7b-instruct"

# ATLAS configuration
export ATLAS_ENFORCEMENT="strict"
```

---

## 📊 Performance Metrics

### **System Impact Analysis**

| Component | Memory Usage | CPU Impact | Network | Storage |
|-----------|--------------|------------|---------|---------|
| **ATLAS** | 5-10MB | <1% | None | ~10MB/day |
| **VSCode Extension** | 2-5MB | <1% | Batch HTTP | ~1MB/day |
| **Web Scraper** | 50-100MB | 5-15% | High (scraping) | Variable |
| **CLI Tools** | 20-50MB | 2-5% | HTTP API | ~5MB/session |
| **MCP Server** | 5-15MB | <1% | HTTP API | None |
| **Model Watcher** | 10-20MB | <1% | None | Registry only |

### **Integration Benefits**
- **Context Preservation**: 100% - nunca pierde información
- **Knowledge Accumulation**: Exponential learning curve
- **Team Collaboration**: Shared knowledge base
- **Quality Consistency**: Automated standards enforcement
- **Audit Compliance**: Complete traceability

---

## 🔒 Security & Privacy

### **Data Protection Standards**
- **Local Processing**: 100% local, no external APIs
- **Pattern Redaction**: Automated secrets/tokens filtering
- **Access Control**: Configurable file system permissions
- **Audit Trail**: Complete immutable logging via ATLAS
- **Workspace Isolation**: Complete context separation

### **Compliance Features**
- **SOX Compliance**: Complete financial audit trail
- **GDPR Ready**: Local processing, configurable retention
- **ISO27001**: Information security management
- **Enterprise Security**: Bank-level audit capabilities

---

## 📈 Roadmap & Future Enhancements

### **Phase 1: Foundation** ✅ (Completed)
- ATLAS logging system
- VSCode activity tracking
- Web scraping automation
- CLI tool integrations

### **Phase 2: Intelligence** ✅ (Completed)
- MCP server implementation  
- Model organization system
- Cross-component integration
- Performance optimization

### **Phase 3: Advanced Features** 🔄 (In Progress)
- **Real-time collaboration** entre team members
- **Predictive coding assistance** basado en patterns
- **Automated documentation** generation
- **Advanced analytics** y insights

### **Phase 4: Enterprise Scale** 🔮 (Planned)
- **Multi-team support** con isolated namespaces
- **Cloud deployment** options
- **Scalable architecture** para large organizations
- **Advanced security** features y compliance

---

## 🤝 Contributing & Maintenance

### **Internal Development**
- **Team**: AI-Server internal development team
- **Standards**: Python 3.13+, TypeScript 5.3+, Enterprise patterns
- **Testing**: Comprehensive test suites con CI/CD
- **Documentation**: Professional-grade documentation

### **Quality Assurance**
- **Code Review**: Mandatory peer review process
- **Testing Coverage**: >90% test coverage requirement
- **Performance Monitoring**: Continuous performance tracking
- **Security Audits**: Regular security assessments

---

## 📞 Support & Resources

### **Documentation Hub**
- **Architecture**: [Design Documentation](../01_design/)
- **Installation**: [Installation Guide](../02_installation/)  
- **User Manual**: [User Manual](../03_user_manual/)
- **API Reference**: [Tooling Documentation](../04_tooling/)

### **Internal Support**
- **Issue Tracking**: Internal repository issues
- **Team Communication**: Internal channels
- **Knowledge Base**: Comprehensive internal wiki
- **Training Materials**: Team onboarding resources

---

**Version**: 3.0  
**Last Updated**: 2025-08-25  
**Maintained by**: AI-Server Internal Team  
**Status**: ✅ Production Ready - Complete Ecosystem