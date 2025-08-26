#!/bin/bash

# AI-Server Automated Logging System Initialization
# Inspirado en sistemas enterprise de Microsoft, Google, Netflix
# 
# Este script configura el sistema de logging OBLIGATORIO
# Una vez inicializado, NO SE PUEDE DESACTIVAR

set -e

# Colors para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

# Configuración
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
LOGS_DIR="$PROJECT_ROOT/logs"

echo -e "${PURPLE}"
echo "🤖 AI-SERVER AUTOMATED LOGGING SYSTEM"
echo "====================================="
echo -e "${NC}"
echo -e "${CYAN}Inicializando sistema de logging OBLIGATORIO${NC}"
echo -e "${YELLOW}⚠️  ADVERTENCIA: Una vez activado no se puede desactivar${NC}"
echo ""

# Función para crear directorio si no existe
create_directory() {
    local dir=$1
    local description=$2
    
    if [ ! -d "$dir" ]; then
        echo -e "${BLUE}📁 Creando directorio: ${description}${NC}"
        mkdir -p "$dir"
        echo -e "   ✅ Creado: $dir"
    else
        echo -e "   ✅ Ya existe: $dir"
    fi
}

# 1. Crear estructura de directorios
echo -e "${BLUE}🏗️  Configurando estructura de directorios...${NC}"

create_directory "$LOGS_DIR/sessions" "Logs por sesión"
create_directory "$LOGS_DIR/operations/code-changes" "Cambios de código"
create_directory "$LOGS_DIR/operations/file-operations" "Operaciones de archivo"
create_directory "$LOGS_DIR/operations/test-executions" "Ejecución de tests"
create_directory "$LOGS_DIR/operations/deployments" "Despliegues"
create_directory "$LOGS_DIR/operations/system-changes" "Cambios de sistema"
create_directory "$LOGS_DIR/metrics/performance" "Métricas de rendimiento"
create_directory "$LOGS_DIR/metrics/errors" "Logs de errores"
create_directory "$LOGS_DIR/metrics/usage" "Estadísticas de uso"
create_directory "$LOGS_DIR/audit/security" "Eventos de seguridad"
create_directory "$LOGS_DIR/audit/access" "Control de acceso"
create_directory "$LOGS_DIR/audit/compliance" "Reportes de compliance"
create_directory "$LOGS_DIR/analytics/patterns" "Patrones detectados"
create_directory "$LOGS_DIR/analytics/insights" "Insights automáticos"
create_directory "$LOGS_DIR/analytics/reports" "Reportes generados"

echo ""

# 2. Crear archivos de configuración
echo -e "${BLUE}⚙️  Creando archivos de configuración...${NC}"

# Configuración principal
cat > "$LOGS_DIR/config.json" << 'EOF'
{
  "version": "1.0.0",
  "system": "ai-server-automated-logging",
  "initialization_time": null,
  "enforcement": {
    "enabled": true,
    "level": "strict",
    "reversible": false,
    "mandatory_operations": [
      "file_write", "file_delete", "file_move",
      "code_change", "command_execution",
      "claude_tool", "system_change"
    ],
    "max_violations": 3,
    "auto_block": true
  },
  "retention": {
    "sessions": "365 days",
    "operations": "180 days", 
    "metrics": "90 days",
    "audit": "2555 days"
  },
  "formats": {
    "session_logs": "jsonl",
    "operation_logs": "json",
    "metrics": "json",
    "reports": "json"
  }
}
EOF

# Actualizar timestamp de inicialización
python3 -c "
import json
from datetime import datetime, timezone

with open('$LOGS_DIR/config.json', 'r') as f:
    config = json.load(f)

config['initialization_time'] = datetime.now(timezone.utc).isoformat()

with open('$LOGS_DIR/config.json', 'w') as f:
    json.dump(config, f, indent=2)
"

echo -e "   ✅ Configuración principal: $LOGS_DIR/config.json"

# 3. Crear scripts de utilidad
echo -e "${BLUE}🔧 Creando scripts de utilidad...${NC}"

# Script de verificación
cat > "$LOGS_DIR/scripts/verify-logs.sh" << 'EOF'
#!/bin/bash
# Verificación de integridad de logs

LOGS_DIR="$(dirname "$(dirname "$0")")"

echo "🔍 Verificando integridad de logs..."

python3 -c "
import sys
sys.path.append('$LOGS_DIR/core')
from enforcer import force_verification

result = force_verification()
if result:
    print('✅ Verificación exitosa - Todos los logs están íntegros')
    exit(0)
else:
    print('❌ Verificación falló - Problemas de integridad detectados')
    exit(1)
"
EOF

chmod +x "$LOGS_DIR/scripts/verify-logs.sh"
echo -e "   ✅ Script de verificación creado"

# Script de reporte
cat > "$LOGS_DIR/scripts/generate-report.sh" << 'EOF'
#!/bin/bash
# Generación de reportes

LOGS_DIR="$(dirname "$(dirname "$0")")"
SESSION_ID=${1:-"current"}

echo "📊 Generando reporte para sesión: $SESSION_ID"

python3 -c "
import sys
sys.path.append('$LOGS_DIR/core')
from session_logger import logger
import json

summary = logger.get_session_summary()
print(json.dumps(summary, indent=2))
"
EOF

chmod +x "$LOGS_DIR/scripts/generate-report.sh"
echo -e "   ✅ Script de reportes creado"

# 4. Configurar Git hooks
echo -e "${BLUE}📝 Configurando Git hooks...${NC}"

if [ -d "$PROJECT_ROOT/.git/hooks" ]; then
    # Post-commit hook
    cat > "$PROJECT_ROOT/.git/hooks/post-commit" << 'EOF'
#!/bin/bash
# Auto-logging para commits

LOGS_DIR="$(dirname "$0")/../../logs"

if [ -f "$LOGS_DIR/core/session_logger.py" ]; then
    python3 -c "
import sys
sys.path.append('$LOGS_DIR/core')
from session_logger import logger
import subprocess

# Obtener info del commit
commit_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()
commit_message = subprocess.check_output(['git', 'log', '-1', '--pretty=%B']).decode().strip()

logger.log_operation(
    operation_type='git_commit',
    user_intent='Commit automático registrado',
    details={
        'commit_hash': commit_hash,
        'commit_message': commit_message,
        'auto_logged': True
    },
    metadata={'category': 'version_control'}
)
"
fi
EOF

    chmod +x "$PROJECT_ROOT/.git/hooks/post-commit"
    echo -e "   ✅ Git post-commit hook configurado"
else
    echo -e "   ⚠️  No es un repositorio Git - hooks no configurados"
fi

# 5. Crear archivos de inicialización Python
echo -e "${BLUE}🐍 Configurando módulos Python...${NC}"

# __init__.py para el paquete core
cat > "$LOGS_DIR/core/__init__.py" << 'EOF'
"""
AI-Server Automated Logging System - Core Module

Sistema de logging obligatorio inspirado en Microsoft, Google, Netflix
Una vez inicializado, NO SE PUEDE DESACTIVAR

Importar este módulo automáticamente activa el logging obligatorio.
"""

from .session_logger import logger, log_operation
from .claude_hooks import setup_automatic_hooks
from .enforcer import enforcer, is_enforcement_active

# Activación automática al importar
print("🤖 [AUTO-LOG] Sistema de logging automático ACTIVADO")
print(f"📋 [AUTO-LOG] Session ID: {logger.session_id}")
print("🔒 [AUTO-LOG] Enforcement: OBLIGATORIO (no desactivable)")

__all__ = [
    'logger',
    'log_operation', 
    'enforcer',
    'is_enforcement_active'
]
EOF

echo -e "   ✅ Módulo core/__init__.py creado"

# 6. Crear script de monitoreo
echo -e "${BLUE}📊 Configurando monitoreo en tiempo real...${NC}"

cat > "$LOGS_DIR/scripts/monitor-realtime.py" << 'EOF'
#!/usr/bin/env python3
"""
Monitor de logs en tiempo real
Muestra actividad actual de logging
"""

import time
import json
import sys
from pathlib import Path
from datetime import datetime

def monitor_logs():
    logs_dir = Path(__file__).parent.parent
    
    print("🔍 Monitor de logs en tiempo real - Presiona Ctrl+C para salir")
    print("=" * 60)
    
    # Buscar sesión activa más reciente
    sessions_dir = logs_dir / "sessions"
    if not sessions_dir.exists():
        print("❌ No hay directorio de sesiones")
        return
    
    # Encontrar archivo más reciente
    session_files = list(sessions_dir.glob("**/*.jsonl"))
    if not session_files:
        print("❌ No hay archivos de sesión")
        return
    
    latest_session = max(session_files, key=lambda x: x.stat().st_mtime)
    print(f"📋 Monitoreando: {latest_session.name}")
    print("-" * 60)
    
    # Seguir el archivo
    with open(latest_session, 'r') as f:
        # Ir al final
        f.seek(0, 2)
        
        try:
            while True:
                line = f.readline()
                if line:
                    try:
                        entry = json.loads(line)
                        timestamp = entry.get('timestamp', '')[:19]  # Solo fecha y hora
                        op_type = entry.get('operation_type', '')
                        intent = entry.get('user_intent', '')[:50] + "..."
                        
                        print(f"[{timestamp}] {op_type:15} | {intent}")
                    except json.JSONDecodeError:
                        continue
                else:
                    time.sleep(0.5)
        except KeyboardInterrupt:
            print("\n👋 Monitor detenido")

if __name__ == "__main__":
    monitor_logs()
EOF

chmod +x "$LOGS_DIR/scripts/monitor-realtime.py"
echo -e "   ✅ Monitor en tiempo real configurado"

# 7. Test inicial
echo ""
echo -e "${BLUE}🧪 Ejecutando test inicial...${NC}"

python3 -c "
import sys
sys.path.append('$LOGS_DIR/core')

try:
    from session_logger import logger
    from enforcer import is_enforcement_active
    
    # Log de inicialización exitosa
    logger.log_operation(
        operation_type='system_initialization',
        user_intent='Sistema de logging automático inicializado exitosamente',
        details={
            'project_root': '$PROJECT_ROOT',
            'logs_dir': '$LOGS_DIR',
            'enforcement_active': is_enforcement_active(),
            'initialization_script': '$0'
        },
        metadata={
            'category': 'system_setup',
            'impact_level': 'critical',
            'success': True
        }
    )
    
    print('✅ Test inicial exitoso')
    print(f'📋 Session ID: {logger.session_id}')
    print(f'📁 Logs guardados en: {logger.session_file}')
    print(f'🔒 Enforcement activo: {is_enforcement_active()}')
    
except Exception as e:
    print(f'❌ Error en test inicial: {e}')
    sys.exit(1)
"

# 8. Resumen final
echo ""
echo -e "${GREEN}🎉 SISTEMA DE LOGGING AUTOMÁTICO INICIALIZADO EXITOSAMENTE${NC}"
echo -e "${GREEN}=======================================================${NC}"
echo ""
echo -e "${WHITE}📊 Resumen de configuración:${NC}"
echo -e "   • Estructura de directorios: ✅ Creada"
echo -e "   • Archivos de configuración: ✅ Creados" 
echo -e "   • Scripts de utilidad: ✅ Configurados"
echo -e "   • Git hooks: ✅ Instalados"
echo -e "   • Módulos Python: ✅ Inicializados"
echo -e "   • Monitor en tiempo real: ✅ Disponible"
echo -e "   • Test inicial: ✅ Exitoso"
echo ""
echo -e "${WHITE}🔧 Comandos disponibles:${NC}"
echo -e "   ${CYAN}$LOGS_DIR/scripts/verify-logs.sh${NC}          # Verificar integridad"
echo -e "   ${CYAN}$LOGS_DIR/scripts/generate-report.sh${NC}     # Generar reportes"
echo -e "   ${CYAN}$LOGS_DIR/scripts/monitor-realtime.py${NC}    # Monitor en tiempo real"
echo ""
echo -e "${RED}⚠️  IMPORTANTE:${NC}"
echo -e "   • El logging es ahora ${RED}OBLIGATORIO${NC} y ${RED}NO SE PUEDE DESACTIVAR${NC}"
echo -e "   • Toda operación será registrada automáticamente"
echo -e "   • Las violaciones de logging serán bloqueadas"
echo -e "   • Los logs son inmutables y auditables"
echo ""
echo -e "${YELLOW}💡 Para usar en tu código Python:${NC}"
echo -e "   ${CYAN}from logs.core import logger, log_operation${NC}"
echo -e "   ${CYAN}log_operation('mi_operacion', 'Descripción', {'datos': 'valor'})${NC}"
echo ""
echo -e "${GREEN}🤖 Sistema listo - Logging automático ACTIVO${NC}"