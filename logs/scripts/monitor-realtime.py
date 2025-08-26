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
