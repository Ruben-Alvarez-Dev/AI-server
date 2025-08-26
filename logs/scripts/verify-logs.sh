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
