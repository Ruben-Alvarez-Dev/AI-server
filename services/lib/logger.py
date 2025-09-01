"""
Logging wrapper around loguru for consistent logging across AI Server components.

Provides structured logging with context injection and multiple output handlers.
"""

import sys
import json
from pathlib import Path
from typing import Any, Dict, Optional, Union
from loguru import logger
from datetime import datetime


class LoggerConfig:
    """Logger configuration settings."""
    
    def __init__(
        self,
        level: str = "INFO",
        format_string: Optional[str] = None,
        log_dir: str = "logs",
        max_size: str = "100 MB",
        retention: str = "30 days",
        compression: str = "gz",
        structured: bool = True,
        include_context: bool = True,
    ):
        self.level = level
        self.format_string = format_string or self._default_format(structured)
        self.log_dir = Path(log_dir)
        self.max_size = max_size
        self.retention = retention
        self.compression = compression
        self.structured = structured
        self.include_context = include_context
    
    def _default_format(self, structured: bool) -> str:
        """Get default log format."""
        if structured:
            return (
                "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                "{extra[context]} | "
                "<level>{message}</level>"
            )
        else:
            return (
                "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan> | "
                "<level>{message}</level>"
            )


class ContextLogger:
    """Logger with context injection capabilities."""
    
    def __init__(self, name: str, config: Optional[LoggerConfig] = None):
        self.name = name
        self.config = config or LoggerConfig()
        self.context: Dict[str, Any] = {}
        self._setup_logger()
    
    def _setup_logger(self) -> None:
        """Setup loguru logger with configuration."""
        # Remove default handler
        logger.remove()
        
        # Console handler
        logger.add(
            sys.stderr,
            format=self.config.format_string,
            level=self.config.level,
            filter=self._context_filter,
        )
        
        # File handler for all logs
        self.config.log_dir.mkdir(parents=True, exist_ok=True)
        logger.add(
            self.config.log_dir / f"{self.name}.log",
            format=self.config.format_string,
            level=self.config.level,
            rotation=self.config.max_size,
            retention=self.config.retention,
            compression=self.config.compression,
            filter=self._context_filter,
            serialize=self.config.structured,
        )
        
        # Error file handler
        logger.add(
            self.config.log_dir / f"{self.name}_error.log",
            format=self.config.format_string,
            level="ERROR",
            rotation=self.config.max_size,
            retention=self.config.retention,
            compression=self.config.compression,
            filter=self._context_filter,
            serialize=self.config.structured,
        )
    
    def _context_filter(self, record) -> bool:
        """Filter to inject context into log records."""
        if self.config.include_context:
            context_str = self._format_context()
            record["extra"]["context"] = context_str
        else:
            record["extra"]["context"] = ""
        
        record["extra"]["component"] = self.name
        return True
    
    def _format_context(self) -> str:
        """Format context dictionary for display."""
        if not self.context:
            return ""
        
        context_parts = []
        for key, value in self.context.items():
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value, default=str)
            else:
                value_str = str(value)
            context_parts.append(f"{key}={value_str}")
        
        return " ".join(context_parts)
    
    def with_context(self, **kwargs) -> 'ContextLogger':
        """Create logger with additional context."""
        new_logger = ContextLogger(self.name, self.config)
        new_logger.context = {**self.context, **kwargs}
        return new_logger
    
    def add_context(self, **kwargs) -> None:
        """Add context to current logger."""
        self.context.update(kwargs)
    
    def clear_context(self) -> None:
        """Clear all context."""
        self.context.clear()
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        logger.bind(**kwargs).debug(message)
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        logger.bind(**kwargs).info(message)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        logger.bind(**kwargs).warning(message)
    
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs) -> None:
        """Log error message with optional exception."""
        if exception:
            logger.bind(**kwargs).opt(exception=True).error(f"{message}: {exception}")
        else:
            logger.bind(**kwargs).error(message)
    
    def critical(self, message: str, exception: Optional[Exception] = None, **kwargs) -> None:
        """Log critical message with optional exception."""
        if exception:
            logger.bind(**kwargs).opt(exception=True).critical(f"{message}: {exception}")
        else:
            logger.bind(**kwargs).critical(message)
    
    def exception(self, message: str, **kwargs) -> None:
        """Log exception with full traceback."""
        logger.bind(**kwargs).opt(exception=True).error(message)


class ComponentLogger:
    """Component-specific logger factory."""
    
    _loggers: Dict[str, ContextLogger] = {}
    _config: Optional[LoggerConfig] = None
    
    @classmethod
    def configure(cls, config: LoggerConfig) -> None:
        """Configure global logger settings."""
        cls._config = config
        # Update existing loggers
        for logger_instance in cls._loggers.values():
            logger_instance.config = config
            logger_instance._setup_logger()
    
    @classmethod
    def get_logger(cls, component: str) -> ContextLogger:
        """Get or create logger for component."""
        if component not in cls._loggers:
            config = cls._config or LoggerConfig()
            cls._loggers[component] = ContextLogger(component, config)
        
        return cls._loggers[component]
    
    @classmethod
    def set_level(cls, level: str) -> None:
        """Set log level for all loggers."""
        if cls._config:
            cls._config.level = level
        else:
            cls._config = LoggerConfig(level=level)
        
        # Update all existing loggers
        for logger_instance in cls._loggers.values():
            logger_instance.config.level = level
            logger_instance._setup_logger()


def get_logger(component: str) -> ContextLogger:
    """Get logger for component."""
    return ComponentLogger.get_logger(component)


def configure_logging(
    level: str = "INFO",
    log_dir: str = "logs",
    structured: bool = True,
    include_context: bool = True,
) -> None:
    """Configure global logging settings."""
    config = LoggerConfig(
        level=level,
        log_dir=log_dir,
        structured=structured,
        include_context=include_context,
    )
    ComponentLogger.configure(config)


# Performance logging utilities
class PerformanceLogger:
    """Logger for performance monitoring."""
    
    def __init__(self, component: str):
        self.logger = get_logger(f"{component}.perf")
        self.start_time: Optional[datetime] = None
        self.operation: Optional[str] = None
    
    def start_operation(self, operation: str, **context) -> None:
        """Start timing an operation."""
        self.operation = operation
        self.start_time = datetime.now()
        self.logger.with_context(**context).debug(f"Starting operation: {operation}")
    
    def end_operation(self, **context) -> Optional[float]:
        """End timing an operation and log duration."""
        if not self.start_time or not self.operation:
            self.logger.warning("end_operation called without start_operation")
            return None
        
        duration = (datetime.now() - self.start_time).total_seconds()
        
        self.logger.with_context(
            operation=self.operation,
            duration_seconds=duration,
            **context
        ).info(f"Operation completed: {self.operation} ({duration:.3f}s)")
        
        # Reset
        self.start_time = None
        operation = self.operation
        self.operation = None
        
        return duration
    
    def log_metric(self, metric_name: str, value: Union[int, float], unit: str = "", **context) -> None:
        """Log a performance metric."""
        self.logger.with_context(
            metric=metric_name,
            value=value,
            unit=unit,
            **context
        ).info(f"Metric: {metric_name}={value}{unit}")


# Audit logging utilities
class AuditLogger:
    """Logger for audit trails."""
    
    def __init__(self, component: str):
        self.logger = get_logger(f"{component}.audit")
    
    def log_action(
        self,
        action: str,
        resource: str,
        user_id: Optional[str] = None,
        result: str = "success",
        **context
    ) -> None:
        """Log an audit action."""
        self.logger.with_context(
            action=action,
            resource=resource,
            user_id=user_id,
            result=result,
            timestamp=datetime.now().isoformat(),
            **context
        ).info(f"Action: {action} on {resource} - {result}")
    
    def log_access(self, resource: str, user_id: Optional[str] = None, **context) -> None:
        """Log resource access."""
        self.log_action("access", resource, user_id, **context)
    
    def log_modification(self, resource: str, user_id: Optional[str] = None, **context) -> None:
        """Log resource modification."""
        self.log_action("modify", resource, user_id, **context)
    
    def log_deletion(self, resource: str, user_id: Optional[str] = None, **context) -> None:
        """Log resource deletion."""
        self.log_action("delete", resource, user_id, **context)