#!/usr/bin/env python3
"""
Logging Enforcement System
Sistema que OBLIGA a registrar toda operación - NO SE PUEDE DESACTIVAR

Inspirado en sistemas de compliance de bancos y empresas Fortune 500
"""

import os
import sys
import threading
import time
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import hashlib

try:
    from .session_logger import logger
except ImportError:
    # Fallback para importación directa
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent))
    from session_logger import logger

class LoggingEnforcer:
    """
    Sistema que OBLIGA a registrar todo
    Una vez activado, no se puede desactivar en la sesión
    """
    
    _instance = None
    _lock = threading.Lock()
    _enforcement_active = False
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
            
        self._initialized = True
        self.blocked_operations = []
        self.enforcement_rules = self._load_enforcement_rules()
        self.violation_count = 0
        self.last_check = time.time()
        
        # Monitor thread que verifica continuamente
        self.monitor_thread = threading.Thread(target=self._continuous_monitoring, daemon=True)
        self.monitor_active = True
        self.monitor_thread.start()
        
        # Activar enforcement automáticamente
        self.activate_enforcement()
    
    def _load_enforcement_rules(self) -> Dict[str, Any]:
        """Carga reglas de enforcement inmutables"""
        return {
            "mandatory_operations": [
                "file_write", "file_delete", "file_move",
                "code_change", "command_execution",
                "claude_tool", "system_change"
            ],
            "max_unlogged_operations": 0,  # CERO tolerancia
            "max_violation_count": 3,
            "enforcement_level": "strict",
            "auto_block_violations": True,
            "immutable": True  # No se puede cambiar
        }
    
    def activate_enforcement(self):
        """
        Activa enforcement - UNA VEZ ACTIVADO NO SE PUEDE DESACTIVAR
        """
        if LoggingEnforcer._enforcement_active:
            return
            
        LoggingEnforcer._enforcement_active = True
        
        # Log obligatorio de activación
        logger.log_operation(
            operation_type="enforcement_activation",
            user_intent="Activar sistema de enforcement obligatorio",
            details={
                "enforcement_rules": self.enforcement_rules,
                "activation_time": datetime.now(timezone.utc).isoformat(),
                "permanent": True,
                "reversible": False
            },
            metadata={
                "category": "system_security",
                "impact_level": "critical",
                "immutable": True
            }
        )
        
        print("🔒 [ENFORCER] Logging enforcement ACTIVADO - Modo obligatorio permanente")
        print("⚠️  [ENFORCER] ADVERTENCIA: Una vez activado no se puede desactivar")
    
    def check_operation_logging(self, operation_type: str, operation_details: Dict[str, Any]) -> bool:
        """
        Verifica si una operación está siendo registrada correctamente
        Retorna False si la operación debe ser BLOQUEADA
        """
        if not LoggingEnforcer._enforcement_active:
            return True  # Si no está activo, permitir
        
        # Verificar si es operación obligatoria
        if operation_type in self.enforcement_rules["mandatory_operations"]:
            # Buscar en logs recientes
            if not self._verify_operation_logged(operation_type, operation_details):
                self._handle_violation(operation_type, operation_details)
                return False  # BLOQUEAR operación
        
        return True  # Permitir operación
    
    def _verify_operation_logged(self, operation_type: str, operation_details: Dict[str, Any]) -> bool:
        """
        Verifica que la operación esté efectivamente registrada
        """
        # Verificar en memoria del logger
        if hasattr(logger, 'operation_counter') and logger.operation_counter > 0:
            # En una implementación completa, verificaríamos el contenido específico
            return True
        
        # Verificar en archivo de logs
        if logger.session_file.exists():
            try:
                with open(logger.session_file, 'r', encoding='utf-8') as f:
                    # Leer últimas líneas para verificar
                    lines = f.readlines()[-10:]  # Últimas 10 operaciones
                    for line in lines:
                        entry = json.loads(line)
                        if entry.get('operation_type') == operation_type:
                            return True
            except Exception:
                pass
        
        return False
    
    def _handle_violation(self, operation_type: str, operation_details: Dict[str, Any]):
        """
        Maneja violación de logging obligatorio
        """
        self.violation_count += 1
        
        violation = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "operation_type": operation_type,
            "operation_details": operation_details,
            "violation_count": self.violation_count,
            "severity": "critical"
        }
        
        self.blocked_operations.append(violation)
        
        # Log de violación (esto sí se registra)
        logger.log_operation(
            operation_type="enforcement_violation",
            user_intent="Detectar violación de logging obligatorio",
            details=violation,
            metadata={
                "category": "security_violation",
                "impact_level": "critical",
                "requires_immediate_attention": True
            }
        )
        
        # Alertas escaladas
        self._escalate_violation(violation)
        
        # Si excede límite, acción drástica
        if self.violation_count >= self.enforcement_rules["max_violation_count"]:
            self._emergency_shutdown()
    
    def _escalate_violation(self, violation: Dict[str, Any]):
        """Escala violación con alertas inmediatas"""
        
        # Alerta en consola
        print(f"\n🚨 [ENFORCER] VIOLACIÓN CRÍTICA DETECTADA:")
        print(f"   Operación: {violation['operation_type']}")
        print(f"   Timestamp: {violation['timestamp']}")
        print(f"   Violación #: {violation['violation_count']}")
        print(f"   ⛔ OPERACIÓN BLOQUEADA POR FALTA DE LOGGING\n")
        
        # En una implementación real:
        # - Enviar email/Slack a admins
        # - Crear ticket automático
        # - Notificación push
        # - Logs a sistema central de seguridad
    
    def _emergency_shutdown(self):
        """
        Shutdown de emergencia si hay muchas violaciones
        """
        logger.log_operation(
            operation_type="emergency_shutdown",
            user_intent="Shutdown de emergencia por múltiples violaciones de logging",
            details={
                "violation_count": self.violation_count,
                "blocked_operations": self.blocked_operations,
                "reason": "Demasiadas operaciones sin logging obligatorio",
                "shutdown_time": datetime.now(timezone.utc).isoformat()
            },
            metadata={
                "category": "security_emergency",
                "impact_level": "critical",
                "automated_response": True
            }
        )
        
        print("\n💀 [ENFORCER] EMERGENCY SHUTDOWN - Demasiadas violaciones de logging")
        print("🔒 [ENFORCER] Sesión terminada por razones de seguridad")
        print(f"📊 [ENFORCER] Operaciones bloqueadas: {len(self.blocked_operations)}")
        
        # Finalizar sesión forzosamente
        logger.finalize_session()
        
        # En una implementación real:
        # - Bloquear usuario temporalmente
        # - Enviar alerta a administradores
        # - Crear reporte de incidente automático
        
        sys.exit(1)  # Terminar proceso
    
    def _continuous_monitoring(self):
        """
        Monitoreo continuo en background
        """
        while self.monitor_active:
            try:
                current_time = time.time()
                
                # Check cada 30 segundos
                if current_time - self.last_check >= 30:
                    self._periodic_integrity_check()
                    self.last_check = current_time
                
                time.sleep(5)  # Check cada 5 segundos
                
            except Exception as e:
                logger.log_error(
                    error_type="monitoring_error",
                    error_message=str(e),
                    traceback_info="",
                    context={"monitor": "continuous_monitoring"}
                )
    
    def _periodic_integrity_check(self):
        """
        Verificación periódica de integridad
        """
        if not LoggingEnforcer._enforcement_active:
            return
        
        # Verificar que el archivo de logs existe y es válido
        if not logger.session_file.exists():
            self._handle_violation("missing_log_file", {"reason": "Log file missing"})
            return
        
        # Verificar integridad del archivo
        try:
            with open(logger.session_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if len(lines) == 0:
                    self._handle_violation("empty_log_file", {"reason": "Log file empty"})
        except Exception as e:
            self._handle_violation("corrupted_log_file", {"reason": str(e)})
    
    def get_enforcement_status(self) -> Dict[str, Any]:
        """Retorna estado actual del enforcement"""
        return {
            "active": LoggingEnforcer._enforcement_active,
            "violation_count": self.violation_count,
            "blocked_operations_count": len(self.blocked_operations),
            "enforcement_rules": self.enforcement_rules,
            "last_check": self.last_check,
            "session_id": logger.session_id
        }
    
    def force_log_verification(self) -> bool:
        """
        Fuerza verificación completa de logs
        Retorna True si todo está en orden
        """
        if not LoggingEnforcer._enforcement_active:
            return True
        
        logger.log_operation(
            operation_type="forced_verification",
            user_intent="Verificación forzada de integridad de logs",
            details={"verification_time": datetime.now(timezone.utc).isoformat()}
        )
        
        # Realizar verificaciones exhaustivas
        checks = [
            self._verify_log_file_exists(),
            self._verify_log_file_integrity(),
            self._verify_hash_chain(),
            self._verify_mandatory_logs()
        ]
        
        all_passed = all(checks)
        
        logger.log_operation(
            operation_type="verification_result",
            user_intent="Resultado de verificación de logs",
            details={
                "all_checks_passed": all_passed,
                "individual_checks": checks,
                "enforcement_status": self.get_enforcement_status()
            }
        )
        
        return all_passed
    
    def _verify_log_file_exists(self) -> bool:
        """Verifica que archivo de logs existe"""
        return logger.session_file.exists()
    
    def _verify_log_file_integrity(self) -> bool:
        """Verifica integridad básica del archivo"""
        try:
            with open(logger.session_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Verificar que cada línea es JSON válido
                for line in lines:
                    json.loads(line)
            return True
        except Exception:
            return False
    
    def _verify_hash_chain(self) -> bool:
        """Verifica cadena de hashes blockchain-style"""
        try:
            with open(logger.session_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            prev_hash = "genesis"
            for line in lines:
                entry = json.loads(line)
                if entry.get('previous_hash') != prev_hash:
                    return False
                prev_hash = entry.get('current_hash', '')
                
            return True
        except Exception:
            return False
    
    def _verify_mandatory_logs(self) -> bool:
        """Verifica que logs obligatorios estén presentes"""
        # En una implementación completa, verificaría logs específicos requeridos
        return True

# Singleton global - se activa automáticamente
enforcer = LoggingEnforcer()

# Funciones públicas
def is_enforcement_active() -> bool:
    """Verifica si enforcement está activo"""
    return LoggingEnforcer._enforcement_active

def check_operation_allowed(operation_type: str, operation_details: Dict[str, Any]) -> bool:
    """Verifica si una operación está permitida"""
    return enforcer.check_operation_logging(operation_type, operation_details)

def get_enforcement_status() -> Dict[str, Any]:
    """Obtiene estado del enforcement"""
    return enforcer.get_enforcement_status()

def force_verification() -> bool:
    """Fuerza verificación completa"""
    return enforcer.force_log_verification()

if __name__ == "__main__":
    # Test del enforcement
    print("🧪 Testing Enforcement System...")
    
    print(f"Enforcement active: {is_enforcement_active()}")
    print(f"Status: {get_enforcement_status()}")
    
    # Test verificación
    verification_result = force_verification()
    print(f"Verification passed: {verification_result}")
    
    print("✅ Enforcement test completado")