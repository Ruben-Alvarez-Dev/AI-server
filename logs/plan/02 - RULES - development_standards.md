# 🛠️ Reglas de Desarrollo General

## 🏴‍☠️ SISTEMA ATLAS (Black Box Integration)

### Reglas Fundamentales ATLAS
- **ATLAS es CAJA NEGRA**: Solo interfaces públicas documentadas
- **Internals completamente opacos**: Jamás documentar funcionamiento interno
- **Integration-first**: Cada componente debe considerar integración ATLAS
- **Testing black-box únicamente**: Solo probar interfaces públicas
- **Interface definition first**: Definir APIs públicas antes que implementación

### ATLAS Development Rules
- **Prefijo obligatorio**: `atlas_` para todas las interfaces públicas
- **Directorio separado**: `/atlas/` para código ATLAS con `/public/` y `/core/` (opaco)
- **Documentation**: Solo `/docs/atlas/` para interfaces públicas
- **Configuration**: Solo parámetros externos en `atlas.yaml`
- **Testing**: Solo en `test_atlas_interface.py` para interfaces públicas

## 🎯 Principios Fundamentales de Desarrollo

### ✅ Clean Code Principles
- **DRY** (Don't Repeat Yourself) - Eliminar duplicación de código
- **KISS** (Keep It Simple, Stupid) - Simplicidad ante todo
- **YAGNI** (You Aren't Gonna Need It) - No añadir funcionalidad innecesaria
- **Single Responsibility** - Cada componente una sola responsabilidad
- **SOLID principles** aplicados apropiadamente
- **Black Box Compliance** - ATLAS internals nunca expuestos

### 🧩 Componentización
- **Crear componentes reutilizables** siempre que sea posible
- **Separar responsabilidades** claramente entre componentes
- **Mantener componentes pequeños** y enfocados en una tarea
- **Usar composición** sobre herencia para flexibilidad
- **Interfaces bien definidas** - Contracts claros entre componentes
- **ATLAS integration points** - Cada componente considera ATLAS donde aplique

## 🏗️ Arquitectura y Organización

### 📁 Estructura de Proyecto
- **Separación clara por funcionalidad**: `/servers/`, `/services/`, `/api/`
- **Modularidad obligatoria**: Cada feature en su propio módulo
- **Dependency injection**: Evitar acoplamiento fuerte entre componentes
- **Configuración externa**: Variables de entorno y archivos YAML
- **ATLAS separation**: Directorio `/atlas/` independiente como caja negra

### 🔄 Comunicación entre Componentes
- **Interfaces bien definidas** - Contracts claros y estables
- **Event-driven apropiado** - Desacoplamiento mediante eventos
- **APIs RESTful** - Para comunicación entre servicios
- **Mensajes semánticos** - Comunicación clara y comprensible
- **ATLAS integration** - Via interfaces públicas únicamente
- **Message queuing** - Apache Pulsar y NATS para async communication

### 🌿 Git Strategy: SOLO MAIN
- **UNA rama únicamente**: `main` - No develop, feature, hotfix, etc.
- **Commits directos a main**: Todo el desarrollo va directo
- **Pre-commit validation**: Validación exhaustiva antes de commit
- **Organic commits**: Solo cuando hay contenido significativo
- **Autoría única**: Ruben-Alvarez-Dev exclusivamente

## 🚀 Prácticas de Desarrollo

### 🔍 Code Review Checklist (Pre-commit)
- [ ] **Standards seguidos**: Nomenclatura y convenciones del proyecto
- [ ] **Nomenclatura consistente**: camelCase, PascalCase, UPPER_SNAKE_CASE
- [ ] **Single responsibility**: Funciones y componentes enfocados
- [ ] **Código legible**: Fácil de entender y mantener
- [ ] **Documentación adecuada**: Comentarios en inglés, APIs documentadas
- [ ] **Error handling robusto**: Manejo apropiado de errores y edge cases
- [ ] **Performance considerations**: Optimización apropiada
- [ ] **Security aplicada**: Validación de inputs, sanitización
- [ ] **ATLAS black-box compliance**: No exposición de internals
- [ ] **Logs/Plan rules**: /logs/ y /plan/ no en .gitignore, OLD_VERSION sí

### 📋 Pre-commit Validations
- **Validar nomenclatura** - Convenciones seguidas correctamente
- **Verificar no duplicación** - Código DRY aplicado
- **Revisar complejidad** - Mantener simplicidad (KISS)
- **Confirmar documentación** - Comentarios adecuados en inglés
- **ATLAS compliance** - No documentación de internals
- **Directory rules** - /logs/, /plan/ no ignorados, OLD_VERSION sí ignorado

## 🧠 Mentalidad de Desarrollo

### 💡 Enfoque Pragmático
- **Resolver problemas reales** - No sobre-ingeniería innecesaria
- **Iterar rápidamente** - Mejora continua y feedback loops
- **Mantenibilidad primero** - Código fácil de entender y modificar
- **Escalabilidad considerada** - Preparado para crecimiento futuro
- **Interface-first thinking** - Diseñar interfaces antes que implementación

### 🎯 Calidad sobre Cantidad
- **Commits orgánicos significativos** - Granularidad funcional, no temporal
- **Refactor constante** - Mejorar código mientras se desarrolla
- **Simplificar siempre** - Eliminar complejidad innecesaria
- **Revisar críticamente** - Auto-review exhaustivo del código
- **Black box discipline** - Mantener ATLAS como caja negra siempre

## 📝 Convenciones Técnicas Detalladas

### 🔤 Estilos de Nomenclatura
```typescript
// Variables y funciones
const userProfile = {...};           // camelCase
const isLoading = false;             // camelCase boolean
function calculateTotal() {...}      // camelCase function
function atlas_enhance() {...}       // ATLAS public function

// Clases y constantes  
class UserService {...}              // PascalCase class
class AtlasConnector {...}           // PascalCase ATLAS class
const MAX_RETRIES = 3;               // UPPER_SNAKE_CASE constant
const ATLAS_ENDPOINT = 'url';        // ATLAS constant

// Interfaces y tipos
interface IUserData {...}            // I + PascalCase
interface IAtlasConfig {...}         // ATLAS interface
type UserType = 'admin' | 'user';    // PascalCase + Type
type AtlasRequestType = {...};       // ATLAS type
```

### 🎨 Metodología BEM (CSS)
```css
/* Blocks - Componentes principales */
.header { }                    /* Block */
.menu { }                      /* Block */
.atlas-panel { }               /* ATLAS Block */

/* Elements - Partes del bloque */
.header__logo { }              /* Element */
.menu__item { }                /* Element */
.atlas-panel__status { }       /* ATLAS Element */

/* Modifiers - Variaciones */
.header--fixed { }             /* Modifier */
.menu__item--active { }        /* Element + Modifier */
.atlas-panel--loading { }      /* ATLAS Modifier */
```

## 📁 Organización de Archivos

### Estructura por Funcionalidad
```
/servers/
├── memory-server/             # Memory Server components
├── llm-server/               # LLM orchestration
├── gui-server/               # Web interface
└── atlas-server/             # 🏴‍☠️ ATLAS (black box)

/services/
├── messaging/                # Pulsar, NATS, Benthos
├── storage/                  # Databases
├── embeddings/               # Embedding models
├── atlas/                    # 🏴‍☠️ ATLAS client interfaces only
└── lib/                      # Shared utilities

/atlas/                       # 🏴‍☠️ ATLAS ROOT
├── public/                   # ✅ Public interfaces only
└── core/                     # 🚫 BLACK BOX - opaque
```

## 🚫 Directorio Rules CRÍTICAS

### ✅ SIEMPRE en GitHub (JAMÁS en .gitignore)
- **`/logs/`** - Todos los logs incluido `/logs/plan/` para trazabilidad
- **`/plan/`** - Master checklist e implementación chapters
- **Razón**: Trazabilidad completa y transparencia del progreso

### 🚫 JAMÁS en GitHub (SIEMPRE en .gitignore)
- **`OLD_VERSION/`** - Versiones obsoletas solo para consulta local
- **Razón**: Evitar contaminación del repositorio y confusión

### Validation Script
```bash
# Verification in pre-commit
if grep -q "^/logs\|^logs/" .gitignore; then
    echo "❌ FATAL: /logs/ in .gitignore - MUST be committed"
    exit 1
fi

if ! grep -q "OLD_VERSION" .gitignore; then
    echo "❌ FATAL: OLD_VERSION not in .gitignore - MUST be ignored"
    exit 1
fi
```

## 🧪 Testing Strategy

### Unit Testing
- **Test coverage mínimo**: 80% para componentes críticos
- **Test naming**: Descriptivo y en inglés
- **Mocking apropiado**: External dependencies y ATLAS internals
- **ATLAS testing**: Solo interfaces públicas, jamás internals

### Integration Testing
- **End-to-end workflows**: Flujos completos de usuario
- **ATLAS integration**: Solo testing de interfaces públicas
- **Message flow testing**: Pulsar y NATS communication
- **Database integration**: Storage layer testing

### ATLAS Testing Rules
```python
# ✅ Correcto - Solo interface pública
def test_atlas_public_api():
    response = atlas_client.process(request)
    assert response.status == "success"

# ❌ Incorrecto - Testing internals
def test_atlas_internal_state():  # PROHIBITED
    internal_state = atlas._private_method()  # NEVER
```

## 🔧 Development Tools

### Required Tools
- **Python 3.11+**: Core development language
- **Node.js 20+**: Frontend tooling
- **llama.cpp**: LLM inference engine
- **Docker**: For OpenWebUI and services
- **Git**: Version control (solo main branch)

### Code Quality Tools
- **Black**: Python code formatting
- **Pylint**: Python linting
- **Prettier**: JavaScript/CSS formatting
- **Pre-commit hooks**: Automated validation

---

**📝 Nota Crítica**: Estas reglas aseguran código limpio, mantenible y bien estructurado, con ATLAS integrado como caja negra y flujo git simplificado en rama main única.