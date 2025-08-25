"""
Memory-Server Logging Configuration
Structured logging with Rich console output and file rotation
"""

import sys
import logging
import logging.handlers
from pathlib import Path
from typing import Optional, Dict, Any
import structlog
from rich.console import Console
from rich.logging import RichHandler
from rich.traceback import install as install_rich_traceback

from .config import get_config


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[Path] = None,
    enable_rich: bool = True,
    enable_structlog: bool = True
) -> logging.Logger:
    """
    Setup comprehensive logging system for Memory-Server
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Path to log file (optional)
        enable_rich: Enable Rich console output
        enable_structlog: Enable structured logging
    
    Returns:
        Configured logger instance
    """
    config = get_config()
    
    # Use config defaults if not provided
    log_level = log_level or config.LOG_LEVEL.value
    
    if log_file is None and config.ENABLE_FILE_LOGGING:
        log_file = config.LOGS_DIR / "memory-server.log"
    
    # Install rich traceback for better error display
    if enable_rich:
        install_rich_traceback(show_locals=config.DEBUG_MODE)
    
    # Clear any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    # Create console handler with Rich
    handlers = []
    
    if enable_rich:
        console = Console(stderr=True)
        rich_handler = RichHandler(
            console=console,
            rich_tracebacks=True,
            tracebacks_show_locals=config.DEBUG_MODE,
            markup=True
        )
        rich_handler.setLevel(getattr(logging, log_level))
        handlers.append(rich_handler)
    else:
        # Fallback to standard console handler
        console_handler = logging.StreamHandler(sys.stderr)
        console_formatter = logging.Formatter(config.LOG_FORMAT)
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(getattr(logging, log_level))
        handlers.append(console_handler)
    
    # Add file handler with rotation if enabled
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Use rotating file handler
        file_handler = logging.handlers.TimedRotatingFileHandler(
            filename=log_file,
            when='midnight',
            interval=1,
            backupCount=30,  # Keep 30 days of logs
            encoding='utf-8'
        )
        
        # File formatter (more detailed than console)
        file_formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)  # File gets all logs
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level),
        handlers=handlers,
        force=True
    )
    
    # Setup structured logging with structlog
    if enable_structlog:
        setup_structlog(log_level)
    
    # Create Memory-Server specific logger
    logger = logging.getLogger("memory-server")
    logger.setLevel(getattr(logging, log_level))
    
    # Log system information
    logger.info("🚀 Memory-Server logging initialized")
    logger.info(f"📊 Log level: {log_level}")
    if log_file:
        logger.info(f"📝 Log file: {log_file}")
    
    return logger


def setup_structlog(log_level: str = "INFO"):
    """
    Configure structured logging with structlog
    
    Args:
        log_level: Logging level for structlog
    """
    
    # Define processors for structured logging
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]
    
    # Configure structlog
    structlog.configure(
        processors=shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


class ContextualLogger:
    """
    Enhanced logger with contextual information for Memory-Server components
    """
    
    def __init__(self, component: str, logger: Optional[logging.Logger] = None):
        self.component = component
        self.logger = logger or logging.getLogger("memory-server")
        self.context: Dict[str, Any] = {"component": component}
    
    def with_context(self, **kwargs) -> 'ContextualLogger':
        """Add context to logger"""
        new_logger = ContextualLogger(self.component, self.logger)
        new_logger.context = {**self.context, **kwargs}
        return new_logger
    
    def _log_with_context(self, level: str, message: str, **kwargs):
        """Log message with context"""
        context_str = " | ".join([f"{k}={v}" for k, v in self.context.items()])
        full_message = f"[{context_str}] {message}"
        
        if kwargs:
            extra_str = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
            full_message += f" | {extra_str}"
        
        getattr(self.logger, level)(full_message)
    
    def debug(self, message: str, **kwargs):
        self._log_with_context("debug", message, **kwargs)
    
    def info(self, message: str, **kwargs):
        self._log_with_context("info", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log_with_context("warning", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self._log_with_context("error", message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        self._log_with_context("exception", message, **kwargs)


class ComponentLogger:
    """
    Factory for creating component-specific loggers
    """
    
    _loggers: Dict[str, ContextualLogger] = {}
    
    @classmethod
    def get_logger(cls, component: str) -> ContextualLogger:
        """Get or create a component-specific logger"""
        if component not in cls._loggers:
            cls._loggers[component] = ContextualLogger(component)
        return cls._loggers[component]


class PerformanceLogger:
    """
    Specialized logger for performance metrics
    """
    
    def __init__(self, component: str):
        self.component = component
        self.logger = ComponentLogger.get_logger(f"perf.{component}")
    
    def log_timing(self, operation: str, duration: float, **context):
        """Log operation timing"""
        self.logger.info(
            f"Operation completed",
            operation=operation,
            duration_ms=round(duration * 1000, 2),
            **context
        )
    
    def log_memory(self, operation: str, memory_mb: float, **context):
        """Log memory usage"""
        self.logger.info(
            f"Memory usage",
            operation=operation,
            memory_mb=round(memory_mb, 2),
            **context
        )
    
    def log_throughput(self, operation: str, items: int, duration: float, **context):
        """Log throughput metrics"""
        throughput = items / duration if duration > 0 else 0
        self.logger.info(
            f"Throughput metrics",
            operation=operation,
            items=items,
            duration_s=round(duration, 2),
            items_per_second=round(throughput, 2),
            **context
        )


# Initialize default logger
default_logger = None

def get_logger(component: str = "memory-server") -> ContextualLogger:
    """Get a component-specific logger"""
    global default_logger
    
    if default_logger is None:
        # Setup logging if not already done
        setup_logging()
        default_logger = True
    
    return ComponentLogger.get_logger(component)


def get_performance_logger(component: str) -> PerformanceLogger:
    """Get a performance logger for a component"""
    return PerformanceLogger(component)