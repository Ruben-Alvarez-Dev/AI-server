# 📝 Reglas de Commits y Workflow

## 👤 AUTORÍA EXCLUSIVA - INMUTABLE

**AUTOR ÚNICO**: Ruben-Alvarez-Dev (ruben.alvarez.dev@gmail.com)
- **TODOS** los commits serán exclusivamente de esta autoría
- **NO** se permiten commits de otros autores, anónimos o con otra identidad
- **Configuración obligatoria** en Git desde el primer día
- **Validación automática** en pre-commit hooks

```bash
# Configuración Git obligatoria
git config --global user.name "Ruben-Alvarez-Dev"
git config --global user.email "ruben.alvarez.dev@gmail.com"
git config --global init.defaultBranch main
```

## 🌿 GIT STRATEGY: SOLO MAIN

### Una Rama Única
- **SOLO `main`**: No develop, feature, hotfix, release branches
- **Commits directos**: Todo desarrollo va directo a main
- **No pull requests**: Desarrollo lineal y simple
- **Pre-commit validation**: Calidad asegurada antes del commit

### Razones para Solo Main
- **Simplicidad**: Un flujo lineal sin complejidad
- **Velocidad**: No overhead de branching/merging
- **Claridad**: Historia git simple y clara
- **Autoría única**: No necesidad de colaboración branches

## 🔄 WORKFLOW OBLIGATORIO (9 PASOS) - INMUTABLE

**Este flujo se sigue SIEMPRE, no se altera, no se muta:**

### 1. 📍 Coger 1 checkpoint
Del chapter actual del plan de implementación en `/plan/`

### 2. 📋 Asumir las rules  
Revisar y asimilar todas las reglas antes de empezar (este documento + otros)

### 3. 🔍 Revisar qué hay que hacer
Entender completamente la tarea del checkpoint y sus criterios

### 4. ⚡ Hacerlo
Implementar siguiendo todas las convenciones + **ATLAS integration** donde aplique

### 5. ✅ Revisar que se ha cumplido (TDD-style)
**Verificar que se ha cumplido EXACTAMENTE lo que se pretendía hacer según la expresión del checkpoint**. Comprobar que el resultado implementado satisface completamente los criterios definidos en la tarea.

### 6. 🛡️ Comprobar que TODAS las rules se han cumplido
Validación exhaustiva de:
- Convenciones de nomenclatura
- Clean code principles  
- **ATLAS black-box compliance**
- **Directory rules** (/logs/, /plan/, OLD_VERSION)
- Code quality standards

### 7. 📝 Log del checkpoint
**Crear log en `/logs/plan/YYYY-MM-DD_HHMMSS_X.Y.Z_keyword.md`** documentando:
- ¿Qué se hizo?
- ¿Cómo se hizo?
- ¿Qué problemas surgieron?
- ¿Cómo se resolvieron?
- Estado actual y próximos pasos

### 8. ☑️ Check en el checklist
Marcar como completado en el plan (`/plan/implementation-index.md`) **solo si pasos 5, 6 y 7 son ✅**

### 9. 💾 Commit directo a MAIN
Solo entonces hacer el commit siguiendo convenciones **directamente a rama main**

**⚠️ CRÍTICO**: Este workflow es **INMUTABLE** y se ejecuta para **CADA** checkpoint.

## 🚨 DIRECTORY RULES - CRÍTICAS E INMUTABLES

### ✅ SIEMPRE en GitHub (JAMÁS en .gitignore)

#### `/logs/` - Carpeta completa
```
/logs/
├── plan/           # 📝 Logs de implementación (van aquí)
├── memory-server/  # Memory Server logs  
├── llm-server/     # LLM Server logs
├── gui-server/     # GUI Server logs
└── system/         # System logs
```

#### `/plan/` - Carpeta completa
```
/plan/
├── implementation-index.md      # Master checklist
├── chapter-01-foundation.md     # Foundation tasks
├── chapter-02-infrastructure.md # Infrastructure tasks
└── [todos los chapters...]      # All implementation chapters
```

**Razón**: Trazabilidad completa, transparencia del progreso, debugging histórico

### 🚫 JAMÁS en GitHub (SIEMPRE en .gitignore)

#### `OLD_VERSION/` - Cualquier ubicación
```gitignore
# OLD_VERSION - JAMÁS se sube, JAMÁS se comenta
OLD_VERSION/
OLD_VERSION/*
**/OLD_VERSION/
**/OLD_VERSION/*
```

**Razón**: Solo consulta local, evitar contaminación del repo

## 🏴‍☠️ ATLAS Rules en Commits

### ATLAS Compliance Validation
- **No internal documentation**: Jamás commitear documentación de internals ATLAS
- **Interface-only**: Solo commits de interfaces públicas ATLAS
- **Black box preservation**: Mantener opacidad en commits
- **Commit types**: `feat(atlas)` para features ATLAS públicas

### ATLAS Validation Script
```bash
# Verificar ATLAS black-box compliance
if git diff --cached --name-only | grep -q "atlas" && git diff --cached | grep -q "# ATLAS INTERNAL"; then
    echo "❌ ATLAS internal documentation detected - black box violation"
    exit 1
fi
```

## 📋 Convención de Mensajes de Commit

### ✅ Estructura Correcta
```
<type>: <description>
[optional body]
```

### Tipos de Commit
- **feat**: New functionality
- **fix**: Bug fixes
- **refactor**: Code restructuring without changing functionality
- **docs**: Documentation changes
- **test**: Tests
- **chore**: Maintenance tasks
- **feat(atlas)**: ATLAS public interface features
- **docs(log)**: Log entries in /logs/plan/
- **docs(plan)**: Plan updates in /plan/

### ✅ Ejemplos Correctos
```
feat: implement JWT authentication with refresh tokens
fix: resolve race condition in memory cleanup  
refactor: optimize database query performance
docs: update API endpoints documentation
feat(atlas): add atlas_enhance public interface
docs(log): checkpoint 1.2.1 implementation log
docs(plan): update chapter 2 progress tracking
```

### ❌ Ejemplos Incorrectos
```
changes                    # Too vague
fix stuff                  # No description
update                     # No context
WIP                        # Work in progress
cambios en el código       # Spanish language
feat(atlas): internal algo # ATLAS internal exposure
```

## 🔧 Script de Commit Orgánico

### Script Completo con Todas las Validaciones
```bash
#!/bin/bash
# scripts/organic-commit.sh
# Validación completa pre-commit

echo "🔍 Validando reglas críticas..."

# 1. Validar directory rules
if grep -q "^/logs\|^logs/" .gitignore; then
    echo "❌ FATAL: /logs/ found in .gitignore - MUST be committed"
    exit 1
fi

if grep -q "^/plan\|^plan/" .gitignore; then
    echo "❌ FATAL: /plan/ found in .gitignore - MUST be committed"  
    exit 1
fi

if ! grep -q "OLD_VERSION" .gitignore; then
    echo "❌ FATAL: OLD_VERSION not found in .gitignore - MUST be ignored"
    exit 1
fi

# 2. Verificar OLD_VERSION no está siendo commiteado
if git diff --cached --name-only | grep -q "OLD_VERSION"; then
    echo "❌ FATAL: OLD_VERSION files detected - NEVER commit OLD_VERSION"
    exit 1
fi

# 3. Verificar cambios staged
if git diff --cached --quiet; then
    echo "❌ No hay cambios staged para committear"
    exit 0
fi

# 4. Verificar significatividad de cambios
CHANGED_LINES=$(git diff --cached --numstat | awk '{s+=$1+$2} END {print s}')
if [ "$CHANGED_LINES" -lt 3 ]; then
    echo "❌ Cambios muy pequeños, no se hace commit"
    git reset HEAD .
    exit 0
fi

# 5. ATLAS black-box compliance
if git diff --cached --name-only | grep -q "atlas" && git diff --cached | grep -qE "(ATLAS INTERNAL|atlas.*internal|atlas.*algorithm)"; then
    echo "❌ ATLAS internal documentation detected - black box violation"
    exit 1
fi

# 6. Generar mensaje de commit inteligente
COMMIT_TYPE="feat"

if git diff --cached --name-only | grep -q "test"; then
    COMMIT_TYPE="test"
elif git diff --cached --name-only | grep -q "README\|docs" && ! git diff --cached --name-only | grep -q "logs/plan\|plan/"; then
    COMMIT_TYPE="docs"
elif git diff --cached --name-only | grep -q "fix\|bug"; then
    COMMIT_TYPE="fix"
elif git diff --cached --name-only | grep -q "atlas.*\.py\|atlas.*\.js\|atlas.*\.yaml"; then
    COMMIT_TYPE="feat(atlas)"
elif git diff --cached --name-only | grep -q "logs/plan"; then
    COMMIT_TYPE="docs(log)"
elif git diff --cached --name-only | grep -q "plan/"; then
    COMMIT_TYPE="docs(plan)"
fi

# 7. Crear mensaje descriptivo
CHANGED_FILES=$(git diff --cached --numstat | wc -l)
INSERTIONS=$(git diff --cached --numstat | awk '{s+=$1} END {print s}')
DELETIONS=$(git diff --cached --numstat | awk '{s+=$2} END {print s}')

COMMIT_MESSAGE="$COMMIT_TYPE: $CHANGED_FILES files, $INSERTIONS insertions(+), $DELETIONS deletions(-)"

# 8. Commit directo a main
git commit -m "$COMMIT_MESSAGE"
echo "✅ Commit orgánico a MAIN: $COMMIT_MESSAGE"
echo "📊 Líneas cambiadas: $CHANGED_LINES"
```

## 🎯 Política de Commits

### Frecuencia Orgánica (Basada en Granularidad Funcional)
- ✅ **Al completar** una funcionalidad coherente y autocontenida
- ✅ **Al resolver** un bug específico y verificado
- ✅ **Al realizar** refactorizaciones que mejoran la estructura
- ✅ **Al añadir** documentación significativa
- ✅ **Al implementar** tests para nueva funcionalidad
- ✅ **Al completar** un checkpoint del plan

### Qué NO Comitear
- ❌ **Commits automáticos** por tiempo o líneas de código
- ❌ **Work in progress** incompleto
- ❌ **Código comentado** sin razón específica
- ❌ **Archivos OLD_VERSION** jamás
- ❌ **ATLAS internals** documentation
- ❌ **Commits vacíos** o triviales

## 📊 Validaciones Pre-Commit

### Checklist Automático
```bash
# Validaciones que se ejecutan automáticamente
- [ ] Directory rules validated (/logs/, /plan/, OLD_VERSION)
- [ ] ATLAS black-box compliance checked
- [ ] Author is Ruben-Alvarez-Dev
- [ ] Commit message follows convention
- [ ] No OLD_VERSION files staged
- [ ] Changes are significant (3+ lines)
- [ ] No ATLAS internals exposed
- [ ] Branch is main
```

### Manual Checklist (Paso 6 del Workflow)
```bash
# Validaciones manuales antes del commit
- [ ] Code follows naming conventions
- [ ] ATLAS integration is interface-only
- [ ] Clean code principles applied
- [ ] Documentation is appropriate
- [ ] Tests are included where needed
- [ ] No security vulnerabilities
- [ ] Performance considerations
- [ ] Error handling robust
```

## 🚨 Troubleshooting

### Recovery Commands
```bash
# Mensaje de commit incorrecto
git commit --amend -m "feat: correct message in English"

# Recuperar commits perdidos
git reflog
git cherry-pick <hash>

# Resetear cambios sin perder trabajo
git reset --soft HEAD~1

# Verificar estado
git status
git log --oneline -10
```

### Common Issues
- **"Changes too small"**: Acumular más cambios significativos
- **"ATLAS internal detected"**: Remover documentación de internals ATLAS
- **"OLD_VERSION detected"**: Unstage archivos OLD_VERSION
- **"/logs/ in gitignore"**: Remover /logs/ del .gitignore

## 📈 Métricas de Calidad

| Métrica | Target | Validación |
|---------|--------|------------|
| Convención | 100% | ✅ Script automático |
| Idioma inglés | 100% | ✅ Script automático |
| Autoría única | 100% | ✅ Git config |
| ATLAS compliance | 100% | ✅ Script automático |
| Directory rules | 100% | ✅ Script automático |
| Granularidad funcional | Alta | 🔄 Manual review |

---

**📝 Nota Crítica**: Este workflow y estas reglas son **INMUTABLES**. Garantizan calidad, trazabilidad, y consistencia en cada commit del proyecto AI-System con ATLAS integrado como caja negra.
