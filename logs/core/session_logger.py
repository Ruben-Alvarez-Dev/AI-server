#!/usr/bin/env python3
"""
AI-Server Automated Session Logger
Inspirado en sistemas de Microsoft, Google, Netflix

Sistema obligatorio que registra TODA actividad automáticamente
"""

import json
import os
import sys
import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import threading
import queue
import time

@dataclass
class LogEntry:
    """Estructura inmutable de cada entrada de log"""
    timestamp: str
    session_id: str
    operation_id: str
    operation_type: str
    user_intent: str
    details: Dict[str, Any]
    context: Dict[str, Any]
    metadata: Dict[str, Any]
    previous_hash: str = ""
    current_hash: str = ""

class SessionLogger:
    """
    Logger principal que captura TODO automáticamente
    Sistema obligatorio - no se puede desactivar
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton - solo una instancia por sesión"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
            
        self._initialized = True
        self.session_id = self._generate_session_id()
        self.start_time = datetime.now(timezone.utc)
        self.operation_counter = 0
        self.context_stack = []
        self.last_hash = "genesis"
        
        # Queue para procesamiento asíncrono
        self.log_queue = queue.Queue()
        self.processing_thread = threading.Thread(target=self._process_logs, daemon=True)
        self.processing_thread.start()
        
        # Setup directorios
        self.logs_dir = Path(__file__).parent.parent
        self.session_dir = self._setup_session_directory()
        self.session_file = self.session_dir / f"{self.session_id}.jsonl"
        
        # Log inicial obligatorio
        self._log_session_start()
        
        print(f"🤖 [AUTO-LOG] Session {self.session_id} iniciada - Logging OBLIGATORIO activo")
    
    def _generate_session_id(self) -> str:
        """Genera ID único para la sesión"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"session-{timestamp}-{unique_id}"
    
    def _setup_session_directory(self) -> Path:
        """Configura directorio de la sesión"""
        date_str = self.start_time.strftime("%Y-%m-%d")
        session_dir = self.logs_dir / "sessions" / date_str
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir
    
    def _calculate_hash(self, entry: LogEntry) -> str:
        """Calcula hash inmutable para integridad blockchain-style"""
        content = json.dumps(asdict(entry), sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]
    
    def _process_logs(self):
        """Procesa logs de forma asíncrona"""
        while True:
            try:
                entry = self.log_queue.get(timeout=1)
                if entry is None:  # Señal de parada
                    break
                    
                # Escribir a archivo JSONL
                with open(self.session_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(asdict(entry), ensure_ascii=False) + '\n')
                    f.flush()
                    
                self.log_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"❌ [AUTO-LOG] Error procesando logs: {e}")
    
    def _log_session_start(self):
        """Log obligatorio de inicio de sesión"""
        self.log_operation(
            operation_type="session_start",
            user_intent="Iniciar nueva sesión de desarrollo",
            details={
                "session_id": self.session_id,
                "start_time": self.start_time.isoformat(),
                "working_directory": str(Path.cwd()),
                "python_version": sys.version,
                "user": os.getenv('USER', 'unknown')
            }
        )
    
    def log_operation(self, 
                     operation_type: str, 
                     user_intent: str,
                     details: Dict[str, Any], 
                     metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Registra cualquier operación automáticamente
        OBLIGATORIO - no se puede omitir
        """
        self.operation_counter += 1
        operation_id = f"op-{self.operation_counter:04d}"
        
        # Context automático
        context = {
            "session_id": self.session_id,
            "operation_sequence": self.operation_counter,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "working_directory": str(Path.cwd()),
            "context_stack": self.context_stack.copy()
        }
        
        # Metadata por defecto
        if metadata is None:
            metadata = {}
        metadata.update({
            "logged_at": datetime.now(timezone.utc).isoformat(),
            "thread_id": threading.get_ident(),
            "mandatory": True  # Marca que es log obligatorio
        })
        
        # Crear entrada
        entry = LogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            session_id=self.session_id,
            operation_id=operation_id,
            operation_type=operation_type,
            user_intent=user_intent,
            details=details,
            context=context,
            metadata=metadata,
            previous_hash=self.last_hash
        )
        
        # Calcular hash para integridad
        entry.current_hash = self._calculate_hash(entry)
        self.last_hash = entry.current_hash
        
        # Encolar para procesamiento asíncrono
        self.log_queue.put(entry)
        
        return operation_id
    
    def log_code_change(self, 
                       file_path: str, 
                       change_type: str,
                       details: Dict[str, Any]) -> str:
        """Registra cambios de código - OBLIGATORIO"""
        return self.log_operation(
            operation_type="code_change",
            user_intent=f"Modificar código en {file_path}",
            details={
                "file_path": file_path,
                "change_type": change_type,  # create, modify, delete
                **details
            },
            metadata={
                "category": "code",
                "impact_level": "high" if change_type in ["create", "delete"] else "medium"
            }
        )
    
    def log_command_execution(self, 
                            command: str, 
                            output: str, 
                            exit_code: int,
                            duration_ms: float) -> str:
        """Registra ejecución de comandos - OBLIGATORIO"""
        return self.log_operation(
            operation_type="command_execution",
            user_intent=f"Ejecutar comando: {command}",
            details={
                "command": command,
                "output": output[:1000] + "..." if len(output) > 1000 else output,
                "exit_code": exit_code,
                "duration_ms": duration_ms,
                "success": exit_code == 0
            },
            metadata={
                "category": "system",
                "impact_level": "medium"
            }
        )
    
    def log_file_operation(self, 
                          operation: str, 
                          file_path: str, 
                          details: Dict[str, Any]) -> str:
        """Registra operaciones de archivo - OBLIGATORIO"""
        return self.log_operation(
            operation_type="file_operation",
            user_intent=f"Operación de archivo: {operation} en {file_path}",
            details={
                "operation": operation,  # read, write, delete, move, etc.
                "file_path": file_path,
                **details
            },
            metadata={
                "category": "filesystem",
                "impact_level": "medium"
            }
        )
    
    def log_claude_tool_usage(self, 
                             tool_name: str,
                             parameters: Dict[str, Any],
                             result: Any,
                             duration_ms: float) -> str:
        """Registra uso de herramientas Claude - OBLIGATORIO"""
        return self.log_operation(
            operation_type="claude_tool",
            user_intent=f"Usar herramienta Claude: {tool_name}",
            details={
                "tool_name": tool_name,
                "parameters": parameters,
                "result_type": type(result).__name__,
                "result_preview": str(result)[:200] + "..." if len(str(result)) > 200 else str(result),
                "duration_ms": duration_ms,
                "success": True  # Si llegó aquí, fue exitoso
            },
            metadata={
                "category": "claude_interaction",
                "impact_level": "high"
            }
        )
    
    def log_error(self, 
                  error_type: str,
                  error_message: str,
                  traceback_info: str,
                  context: Dict[str, Any]) -> str:
        """Registra errores - OBLIGATORIO"""
        return self.log_operation(
            operation_type="error",
            user_intent=f"Error ocurrido: {error_type}",
            details={
                "error_type": error_type,
                "error_message": error_message,
                "traceback": traceback_info,
                "error_context": context
            },
            metadata={
                "category": "error",
                "impact_level": "high",
                "requires_attention": True
            }
        )
    
    def push_context(self, context_name: str, context_data: Dict[str, Any]):
        """Añade contexto al stack"""
        self.context_stack.append({
            "name": context_name,
            "data": context_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    def pop_context(self) -> Optional[Dict[str, Any]]:
        """Remueve contexto del stack"""
        return self.context_stack.pop() if self.context_stack else None
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Genera resumen de la sesión actual"""
        current_time = datetime.now(timezone.utc)
        duration = current_time - self.start_time
        
        return {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "current_time": current_time.isoformat(),
            "duration_seconds": duration.total_seconds(),
            "operations_logged": self.operation_counter,
            "session_file": str(self.session_file),
            "status": "active"
        }
    
    def finalize_session(self):
        """Finaliza la sesión - OBLIGATORIO al terminar"""
        self.log_operation(
            operation_type="session_end",
            user_intent="Finalizar sesión de desarrollo",
            details={
                "session_summary": self.get_session_summary(),
                "total_operations": self.operation_counter,
                "final_hash": self.last_hash
            }
        )
        
        # Esperar que se procesen todos los logs
        self.log_queue.join()
        self.log_queue.put(None)  # Señal de parada
        self.processing_thread.join(timeout=5)
        
        print(f"🔒 [AUTO-LOG] Session {self.session_id} finalizada - {self.operation_counter} operaciones registradas")

# Singleton global - se inicializa automáticamente
logger = SessionLogger()

# Función de conveniencia
def log_operation(operation_type: str, user_intent: str, details: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> str:
    """Función global para logging obligatorio"""
    return logger.log_operation(operation_type, user_intent, details, metadata)

# Hook de finalización automática
import atexit
atexit.register(logger.finalize_session)

if __name__ == "__main__":
    # Test del sistema
    print("🧪 Testing Automated Logging System...")
    
    logger.log_operation(
        operation_type="test",
        user_intent="Probar sistema de logging automático",
        details={"test_data": "hello world", "test_number": 42}
    )
    
    logger.log_code_change(
        file_path="/test/example.py",
        change_type="modify",
        details={"lines_changed": 5, "reason": "Testing"}
    )
    
    print(f"✅ Test completado. Logs en: {logger.session_file}")
    print(f"📊 Session summary: {logger.get_session_summary()}")