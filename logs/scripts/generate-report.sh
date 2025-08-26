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
