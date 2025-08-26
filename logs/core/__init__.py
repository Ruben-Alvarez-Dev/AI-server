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
