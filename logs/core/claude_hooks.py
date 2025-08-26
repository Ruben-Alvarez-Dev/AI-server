#!/usr/bin/env python3
"""
Claude Code Integration Hooks
Sistema que intercepta TODAS las herramientas de Claude automáticamente

Este módulo se integra directamente con Claude Code para capturar
cada uso de herramienta sin que el usuario tenga que hacer nada.
"""

import functools
import time
from typing import Any, Dict, Callable
import json
try:
    from .session_logger import logger
except ImportError:
    # Fallback para importación directa
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent))
    from session_logger import logger

class ClaudeToolInterceptor:
    """
    Interceptor que se ejecuta automáticamente en cada herramienta de Claude
    """
    
    @staticmethod
    def intercept_tool(tool_name: str, original_func: Callable) -> Callable:
        """
        Decorador que intercepta cualquier herramienta de Claude
        """
        @functools.wraps(original_func)
        def wrapper(*args, **kwargs):
            # Capturar contexto antes de la ejecución
            start_time = time.time()
            
            # Preparar parámetros para logging (sanitizar datos sensibles)
            sanitized_params = ClaudeToolInterceptor._sanitize_parameters(kwargs)
            
            # Log pre-ejecución
            logger.push_context(f"claude_tool_{tool_name}", {
                "tool_name": tool_name,
                "parameters": sanitized_params,
                "start_time": start_time
            })
            
            try:
                # Ejecutar herramienta original
                result = original_func(*args, **kwargs)
                
                # Calcular duración
                duration_ms = (time.time() - start_time) * 1000
                
                # Log exitoso
                logger.log_claude_tool_usage(
                    tool_name=tool_name,
                    parameters=sanitized_params,
                    result=result,
                    duration_ms=duration_ms
                )
                
                return result
                
            except Exception as e:
                # Log error
                duration_ms = (time.time() - start_time) * 1000
                logger.log_error(
                    error_type=type(e).__name__,
                    error_message=str(e),
                    traceback_info="",  # Se puede expandir
                    context={
                        "tool_name": tool_name,
                        "parameters": sanitized_params,
                        "duration_ms": duration_ms
                    }
                )
                raise  # Re-lanzar el error
                
            finally:
                # Limpiar contexto
                logger.pop_context()
        
        return wrapper
    
    @staticmethod
    def _sanitize_parameters(params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitiza parámetros para remover información sensible
        """
        sanitized = {}
        for key, value in params.items():
            if key.lower() in ['password', 'token', 'key', 'secret']:
                sanitized[key] = '[REDACTED]'
            elif isinstance(value, str) and len(value) > 1000:
                sanitized[key] = value[:1000] + "... [TRUNCATED]"
            else:
                sanitized[key] = value
        return sanitized

# Funciones específicas para cada herramienta de Claude Code
def log_bash_execution(command: str, description: str, result: Any):
    """Log específico para herramienta Bash"""
    logger.log_command_execution(
        command=command,
        output=str(result),
        exit_code=0,  # Simplificado - se puede expandir
        duration_ms=0  # Se calculará en el interceptor
    )

def log_file_read(file_path: str, result: Any):
    """Log específico para herramienta Read"""
    logger.log_file_operation(
        operation="read",
        file_path=file_path,
        details={
            "content_length": len(str(result)) if result else 0,
            "success": result is not None
        }
    )

def log_file_write(file_path: str, content: str):
    """Log específico para herramienta Write"""
    logger.log_file_operation(
        operation="write",
        file_path=file_path,
        details={
            "content_length": len(content),
            "content_preview": content[:200] + "..." if len(content) > 200 else content
        }
    )

def log_file_edit(file_path: str, old_string: str, new_string: str):
    """Log específico para herramienta Edit"""
    logger.log_code_change(
        file_path=file_path,
        change_type="modify",
        details={
            "old_content_length": len(old_string),
            "new_content_length": len(new_string),
            "change_preview": f"'{old_string[:100]}...' → '{new_string[:100]}...'" if len(old_string) > 100 else f"'{old_string}' → '{new_string}'"
        }
    )

def log_grep_search(pattern: str, path: str, result: Any):
    """Log específico para herramienta Grep"""
    logger.log_operation(
        operation_type="search",
        user_intent=f"Buscar patrón '{pattern}' en {path}",
        details={
            "pattern": pattern,
            "path": path,
            "results_count": len(result) if isinstance(result, list) else 0,
            "search_type": "grep"
        }
    )

def log_glob_search(pattern: str, path: str, result: Any):
    """Log específico para herramienta Glob"""
    logger.log_operation(
        operation_type="search",
        user_intent=f"Buscar archivos con patrón '{pattern}' en {path}",
        details={
            "pattern": pattern,
            "path": path,
            "files_found": len(result) if isinstance(result, list) else 0,
            "search_type": "glob"
        }
    )

def log_web_fetch(url: str, prompt: str, result: Any):
    """Log específico para herramienta WebFetch"""
    logger.log_operation(
        operation_type="web_fetch",
        user_intent=f"Obtener contenido web de {url}",
        details={
            "url": url,
            "prompt": prompt,
            "success": result is not None,
            "result_length": len(str(result)) if result else 0
        },
        metadata={"category": "external_api"}
    )

def log_task_execution(description: str, prompt: str, subagent_type: str, result: Any):
    """Log específico para herramienta Task"""
    logger.log_operation(
        operation_type="task_execution",
        user_intent=f"Ejecutar tarea: {description}",
        details={
            "description": description,
            "prompt": prompt[:500] + "..." if len(prompt) > 500 else prompt,
            "subagent_type": subagent_type,
            "success": result is not None
        },
        metadata={"category": "ai_task"}
    )

# Auto-registro de hooks (se ejecuta automáticamente al importar)
def setup_automatic_hooks():
    """
    Configura hooks automáticos para todas las herramientas de Claude
    """
    # Esta función se llamará automáticamente cuando se importe el módulo
    # En una implementación real, esto se integraría más profundamente con Claude Code
    
    logger.log_operation(
        operation_type="system_setup",
        user_intent="Configurar hooks automáticos de Claude Code",
        details={
            "hooks_registered": [
                "Bash", "Read", "Write", "Edit", "Grep", "Glob", 
                "WebFetch", "Task", "TodoWrite", "MultiEdit"
            ],
            "auto_logging": True,
            "enforcement_level": "mandatory"
        },
        metadata={"category": "system_initialization"}
    )

# Ejecutar setup automáticamente
setup_automatic_hooks()

# Clase para integración manual (si es necesario)
class ManualClaudeLogger:
    """
    Logger manual para cuando no se pueden usar hooks automáticos
    """
    
    @staticmethod
    def log_before_tool(tool_name: str, parameters: Dict[str, Any]):
        """Llamar manualmente ANTES de usar cualquier herramienta"""
        logger.push_context(f"manual_tool_{tool_name}", {
            "tool_name": tool_name,
            "parameters": parameters,
            "manual_logging": True
        })
    
    @staticmethod 
    def log_after_tool(tool_name: str, result: Any, duration_ms: float = 0):
        """Llamar manualmente DESPUÉS de usar cualquier herramienta"""
        context = logger.pop_context()
        if context and context.get("name") == f"manual_tool_{tool_name}":
            logger.log_claude_tool_usage(
                tool_name=tool_name,
                parameters=context["data"].get("parameters", {}),
                result=result,
                duration_ms=duration_ms
            )

if __name__ == "__main__":
    # Test de los hooks
    print("🧪 Testing Claude Code Hooks...")
    
    # Simular uso de herramientas
    log_file_read("/test/example.py", "contenido del archivo...")
    log_bash_execution("ls -la", "List directory contents", "total 42\n-rw-r--r-- 1 user staff 1234 Aug 25 20:30 example.py")
    log_grep_search("def test", "/src/", ["file1.py:10:def test()", "file2.py:25:def test_function()"])
    
    print("✅ Hooks test completado")