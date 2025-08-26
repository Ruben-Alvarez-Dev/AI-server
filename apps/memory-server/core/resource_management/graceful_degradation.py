"""
Graceful Degradation Manager
Intelligent service degradation based on resource pressure
"""

import asyncio
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Callable, Set
from datetime import datetime, timedelta
from enum import Enum

from core.logging_config import get_logger

logger = get_logger("graceful_degradation")

class ServicePriority(Enum):
    """Service priority levels"""
    CRITICAL = 1      # Core system functions, never disable
    HIGH = 2          # Important features, disable only in emergency
    MEDIUM = 3        # Nice-to-have features, disable under pressure
    LOW = 4           # Optional features, disable aggressively

class DegradationLevel(Enum):
    """System degradation levels"""
    NORMAL = "normal"           # All services active
    CONSERVATION = "conservation"   # Reduce resource usage
    DEGRADED = "degraded"       # Disable non-essential features
    MINIMAL = "minimal"         # Only critical services
    EMERGENCY = "emergency"     # Survival mode

@dataclass
class ServiceConfiguration:
    """Service configuration and resource impact"""
    name: str
    priority: ServicePriority
    resource_usage: Dict[str, float]  # disk_mb, ram_mb, cpu_percent
    dependencies: Set[str]
    disable_callback: Optional[Callable] = None
    enable_callback: Optional[Callable] = None
    is_active: bool = True

@dataclass
class DegradationAction:
    """Action taken during degradation"""
    timestamp: datetime
    level: DegradationLevel
    action_type: str  # "disable_service", "reduce_resources", "change_mode"
    service_name: Optional[str]
    details: str
    resource_savings: Dict[str, float]

class GracefulDegradationManager:
    """
    Manages graceful service degradation based on resource pressure
    """
    
    # Service registry with resource usage profiles
    SERVICE_REGISTRY = {
        "core_api": ServiceConfiguration(
            name="core_api",
            priority=ServicePriority.CRITICAL,
            resource_usage={"disk_mb": 50, "ram_mb": 200, "cpu_percent": 5},
            dependencies=set()
        ),
        "health_monitor": ServiceConfiguration(
            name="health_monitor", 
            priority=ServicePriority.CRITICAL,
            resource_usage={"disk_mb": 10, "ram_mb": 50, "cpu_percent": 2},
            dependencies=set()
        ),
        "embedding_engine": ServiceConfiguration(
            name="embedding_engine",
            priority=ServicePriority.HIGH,
            resource_usage={"disk_mb": 500, "ram_mb": 1024, "cpu_percent": 15},
            dependencies={"core_api"}
        ),
        "conversation_capture": ServiceConfiguration(
            name="conversation_capture",
            priority=ServicePriority.HIGH,
            resource_usage={"disk_mb": 100, "ram_mb": 128, "cpu_percent": 3},
            dependencies={"core_api"}
        ),
        "lazy_graph_rag": ServiceConfiguration(
            name="lazy_graph_rag",
            priority=ServicePriority.HIGH,
            resource_usage={"disk_mb": 200, "ram_mb": 512, "cpu_percent": 8},
            dependencies={"embedding_engine"}
        ),
        "late_chunking": ServiceConfiguration(
            name="late_chunking",
            priority=ServicePriority.MEDIUM,
            resource_usage={"disk_mb": 150, "ram_mb": 256, "cpu_percent": 5},
            dependencies={"embedding_engine"}
        ),
        "web_scraping": ServiceConfiguration(
            name="web_scraping",
            priority=ServicePriority.MEDIUM,
            resource_usage={"disk_mb": 300, "ram_mb": 400, "cpu_percent": 10},
            dependencies={"core_api"}
        ),
        "debug_session_capture": ServiceConfiguration(
            name="debug_session_capture",
            priority=ServicePriority.MEDIUM,
            resource_usage={"disk_mb": 200, "ram_mb": 128, "cpu_percent": 4},
            dependencies={"conversation_capture"}
        ),
        "terminal_capture": ServiceConfiguration(
            name="terminal_capture",
            priority=ServicePriority.MEDIUM,
            resource_usage={"disk_mb": 50, "ram_mb": 64, "cpu_percent": 2},
            dependencies={"core_api"}
        ),
        "advanced_analytics": ServiceConfiguration(
            name="advanced_analytics",
            priority=ServicePriority.LOW,
            resource_usage={"disk_mb": 400, "ram_mb": 512, "cpu_percent": 12},
            dependencies={"embedding_engine", "lazy_graph_rag"}
        ),
        "background_indexing": ServiceConfiguration(
            name="background_indexing",
            priority=ServicePriority.LOW,
            resource_usage={"disk_mb": 100, "ram_mb": 256, "cpu_percent": 6},
            dependencies={"embedding_engine"}
        ),
        "detailed_logging": ServiceConfiguration(
            name="detailed_logging",
            priority=ServicePriority.LOW,
            resource_usage={"disk_mb": 200, "ram_mb": 32, "cpu_percent": 1},
            dependencies=set()
        ),
        "metrics_collection": ServiceConfiguration(
            name="metrics_collection",
            priority=ServicePriority.LOW,
            resource_usage={"disk_mb": 50, "ram_mb": 64, "cpu_percent": 2},
            dependencies=set()
        )
    }
    
    # Degradation level configurations
    DEGRADATION_CONFIGS = {
        DegradationLevel.NORMAL: {
            "max_services": None,
            "priority_cutoff": ServicePriority.LOW,
            "resource_multiplier": 1.0,
            "feature_flags": {"detailed_logs": True, "debug_mode": True, "metrics": True}
        },
        DegradationLevel.CONSERVATION: {
            "max_services": None,
            "priority_cutoff": ServicePriority.LOW,
            "resource_multiplier": 0.8,
            "feature_flags": {"detailed_logs": False, "debug_mode": True, "metrics": True}
        },
        DegradationLevel.DEGRADED: {
            "max_services": None,
            "priority_cutoff": ServicePriority.MEDIUM,
            "resource_multiplier": 0.6,
            "feature_flags": {"detailed_logs": False, "debug_mode": False, "metrics": True}
        },
        DegradationLevel.MINIMAL: {
            "max_services": 8,
            "priority_cutoff": ServicePriority.HIGH,
            "resource_multiplier": 0.4,
            "feature_flags": {"detailed_logs": False, "debug_mode": False, "metrics": False}
        },
        DegradationLevel.EMERGENCY: {
            "max_services": 4,
            "priority_cutoff": ServicePriority.CRITICAL,
            "resource_multiplier": 0.2,
            "feature_flags": {"detailed_logs": False, "debug_mode": False, "metrics": False}
        }
    }
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.current_level = DegradationLevel.NORMAL
        self.services = self.SERVICE_REGISTRY.copy()
        self.degradation_history: List[DegradationAction] = []
        self.service_callbacks: Dict[str, Dict[str, Callable]] = {}
        
        # Performance tracking
        self.resource_savings = {"disk_mb": 0, "ram_mb": 0, "cpu_percent": 0}
        self.services_disabled = 0
        self.last_degradation_time = None
        
        # State persistence
        self.state_file = base_path / "degradation_state.json"
    
    async def assess_degradation_need(self, resource_state: Dict[str, float]) -> DegradationLevel:
        """Assess required degradation level based on resource state"""
        
        disk_percent = resource_state.get("disk_usage_percent", 0)
        ram_percent = resource_state.get("ram_usage_percent", 0)  
        cpu_percent = resource_state.get("cpu_usage_percent", 0)
        
        # Determine required degradation level
        if (disk_percent >= 95 or ram_percent >= 95 or cpu_percent >= 95):
            return DegradationLevel.EMERGENCY
        elif (disk_percent >= 90 or ram_percent >= 90 or cpu_percent >= 90):
            return DegradationLevel.MINIMAL
        elif (disk_percent >= 80 or ram_percent >= 85 or cpu_percent >= 80):
            return DegradationLevel.DEGRADED
        elif (disk_percent >= 70 or ram_percent >= 75 or cpu_percent >= 70):
            return DegradationLevel.CONSERVATION
        else:
            return DegradationLevel.NORMAL
    
    async def apply_degradation(self, target_level: DegradationLevel, reason: str = "resource_pressure"):
        """Apply degradation to target level"""
        
        if target_level == self.current_level:
            return
        
        old_level = self.current_level
        self.current_level = target_level
        self.last_degradation_time = datetime.now()
        
        logger.warning(f"Applying degradation: {old_level.value} → {target_level.value} (reason: {reason})")
        
        try:
            # Apply degradation based on target level
            await self._apply_service_degradation(target_level)
            await self._apply_resource_adjustments(target_level)
            await self._apply_feature_flags(target_level)
            
            # Record degradation action
            action = DegradationAction(
                timestamp=datetime.now(),
                level=target_level,
                action_type="level_change",
                service_name=None,
                details=f"Degradation level changed from {old_level.value} to {target_level.value}",
                resource_savings=self.resource_savings.copy()
            )
            
            self.degradation_history.append(action)
            
            # Persist state
            await self._save_state()
            
            logger.info(f"Degradation applied successfully. Services disabled: {self.services_disabled}, "
                       f"Resource savings: {self.resource_savings}")
            
        except Exception as e:
            logger.error(f"Error applying degradation: {e}")
            # Attempt rollback
            self.current_level = old_level
            raise
    
    async def _apply_service_degradation(self, level: DegradationLevel):
        """Apply service-level degradation"""
        
        config = self.DEGRADATION_CONFIGS[level]
        priority_cutoff = config["priority_cutoff"]
        max_services = config["max_services"]
        
        # Reset counters
        self.services_disabled = 0
        self.resource_savings = {"disk_mb": 0, "ram_mb": 0, "cpu_percent": 0}
        
        # Sort services by priority (critical first)
        sorted_services = sorted(
            self.services.items(), 
            key=lambda x: (x[1].priority.value, x[0])
        )
        
        active_services = 0
        
        for service_name, service_config in sorted_services:
            should_be_active = True
            
            # Check priority cutoff
            if service_config.priority.value > priority_cutoff.value:
                should_be_active = False
            
            # Check max services limit
            if max_services and active_services >= max_services:
                should_be_active = False
            
            # Apply service state change
            if should_be_active and not service_config.is_active:
                await self._enable_service(service_name)
                active_services += 1
            elif not should_be_active and service_config.is_active:
                await self._disable_service(service_name)
            elif should_be_active:
                active_services += 1
    
    async def _enable_service(self, service_name: str):
        """Enable a service"""
        
        service_config = self.services[service_name]
        
        # Check dependencies are met
        for dependency in service_config.dependencies:
            if dependency not in self.services or not self.services[dependency].is_active:
                logger.warning(f"Cannot enable {service_name}: dependency {dependency} not active")
                return
        
        # Call enable callback if present
        callbacks = self.service_callbacks.get(service_name, {})
        enable_callback = callbacks.get("enable")
        
        if enable_callback:
            try:
                await enable_callback()
            except Exception as e:
                logger.error(f"Error enabling service {service_name}: {e}")
                return
        
        # Update service state
        service_config.is_active = True
        
        # Update resource accounting
        for resource, amount in service_config.resource_usage.items():
            if resource in self.resource_savings:
                self.resource_savings[resource] -= amount
        
        logger.info(f"Service enabled: {service_name}")
    
    async def _disable_service(self, service_name: str):
        """Disable a service"""
        
        service_config = self.services[service_name]
        
        # Don't disable if other services depend on this one
        dependents = [
            name for name, config in self.services.items()
            if service_name in config.dependencies and config.is_active
        ]
        
        if dependents:
            logger.warning(f"Cannot disable {service_name}: required by {dependents}")
            return
        
        # Call disable callback if present
        callbacks = self.service_callbacks.get(service_name, {})
        disable_callback = callbacks.get("disable")
        
        if disable_callback:
            try:
                await disable_callback()
            except Exception as e:
                logger.error(f"Error disabling service {service_name}: {e}")
                return
        
        # Update service state
        service_config.is_active = False
        self.services_disabled += 1
        
        # Update resource savings
        for resource, amount in service_config.resource_usage.items():
            if resource in self.resource_savings:
                self.resource_savings[resource] += amount
        
        # Record action
        action = DegradationAction(
            timestamp=datetime.now(),
            level=self.current_level,
            action_type="disable_service",
            service_name=service_name,
            details=f"Disabled service {service_name} for resource conservation",
            resource_savings=service_config.resource_usage.copy()
        )
        
        self.degradation_history.append(action)
        
        logger.warning(f"Service disabled: {service_name}")
    
    async def _apply_resource_adjustments(self, level: DegradationLevel):
        """Apply resource usage adjustments"""
        
        config = self.DEGRADATION_CONFIGS[level]
        multiplier = config["resource_multiplier"]
        
        # This would typically adjust buffer sizes, processing threads, etc.
        # For now, we'll just log the intended adjustments
        
        adjustments = {
            "buffer_size_multiplier": multiplier,
            "processing_threads": max(1, int(4 * multiplier)),
            "cache_size_multiplier": multiplier,
            "batch_size_multiplier": multiplier
        }
        
        logger.info(f"Resource adjustments applied: {adjustments}")
        
        # Record resource adjustment action
        action = DegradationAction(
            timestamp=datetime.now(),
            level=level,
            action_type="adjust_resources",
            service_name=None,
            details=f"Applied resource multiplier: {multiplier}",
            resource_savings={"adjustment_multiplier": multiplier}
        )
        
        self.degradation_history.append(action)
    
    async def _apply_feature_flags(self, level: DegradationLevel):
        """Apply feature flag changes"""
        
        config = self.DEGRADATION_CONFIGS[level]
        feature_flags = config["feature_flags"]
        
        # Apply feature flags (would integrate with actual feature flag system)
        for flag, enabled in feature_flags.items():
            logger.debug(f"Feature flag {flag}: {'enabled' if enabled else 'disabled'}")
        
        # Record feature flag changes
        action = DegradationAction(
            timestamp=datetime.now(),
            level=level,
            action_type="feature_flags",
            service_name=None,
            details=f"Applied feature flags: {feature_flags}",
            resource_savings={}
        )
        
        self.degradation_history.append(action)
    
    def register_service_callbacks(self, service_name: str, enable_callback: Callable, disable_callback: Callable):
        """Register callbacks for service enable/disable"""
        
        self.service_callbacks[service_name] = {
            "enable": enable_callback,
            "disable": disable_callback
        }
        
        logger.info(f"Callbacks registered for service: {service_name}")
    
    async def force_service_state(self, service_name: str, enabled: bool):
        """Force a service to enabled or disabled state"""
        
        if service_name not in self.services:
            raise ValueError(f"Unknown service: {service_name}")
        
        if enabled:
            await self._enable_service(service_name)
        else:
            await self._disable_service(service_name)
    
    def get_degradation_status(self) -> Dict[str, Any]:
        """Get current degradation status"""
        
        active_services = [name for name, config in self.services.items() if config.is_active]
        inactive_services = [name for name, config in self.services.items() if not config.is_active]
        
        return {
            "current_level": self.current_level.value,
            "services_active": len(active_services),
            "services_disabled": len(inactive_services),
            "active_services": active_services,
            "inactive_services": inactive_services,
            "resource_savings": self.resource_savings.copy(),
            "last_degradation_time": self.last_degradation_time.isoformat() if self.last_degradation_time else None,
            "total_actions": len(self.degradation_history)
        }
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get detailed service status"""
        
        status = {}
        
        for service_name, config in self.services.items():
            status[service_name] = {
                "priority": config.priority.name,
                "is_active": config.is_active,
                "resource_usage": config.resource_usage.copy(),
                "dependencies": list(config.dependencies),
                "has_callbacks": service_name in self.service_callbacks
            }
        
        return status
    
    def get_degradation_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get degradation history for specified hours"""
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_actions = [
            action for action in self.degradation_history 
            if action.timestamp > cutoff_time
        ]
        
        return [
            {
                "timestamp": action.timestamp.isoformat(),
                "level": action.level.value,
                "action_type": action.action_type,
                "service_name": action.service_name,
                "details": action.details,
                "resource_savings": action.resource_savings
            }
            for action in recent_actions
        ]
    
    async def _save_state(self):
        """Save degradation state to disk"""
        
        try:
            state = {
                "current_level": self.current_level.value,
                "services": {
                    name: {
                        "is_active": config.is_active,
                        "priority": config.priority.name,
                        "resource_usage": config.resource_usage
                    }
                    for name, config in self.services.items()
                },
                "resource_savings": self.resource_savings,
                "services_disabled": self.services_disabled,
                "last_degradation_time": self.last_degradation_time.isoformat() if self.last_degradation_time else None
            }
            
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            self.state_file.write_text(json.dumps(state, indent=2))
            
        except Exception as e:
            logger.error(f"Error saving degradation state: {e}")
    
    async def load_state(self):
        """Load degradation state from disk"""
        
        try:
            if not self.state_file.exists():
                return
            
            state = json.loads(self.state_file.read_text())
            
            self.current_level = DegradationLevel(state["current_level"])
            self.resource_savings = state.get("resource_savings", {"disk_mb": 0, "ram_mb": 0, "cpu_percent": 0})
            self.services_disabled = state.get("services_disabled", 0)
            
            if state.get("last_degradation_time"):
                self.last_degradation_time = datetime.fromisoformat(state["last_degradation_time"])
            
            # Restore service states
            for service_name, service_state in state.get("services", {}).items():
                if service_name in self.services:
                    self.services[service_name].is_active = service_state["is_active"]
            
            logger.info(f"Loaded degradation state: {self.current_level.value}")
            
        except Exception as e:
            logger.error(f"Error loading degradation state: {e}")
    
    async def calculate_resource_impact(self) -> Dict[str, Any]:
        """Calculate total resource impact of current degradation"""
        
        total_usage = {"disk_mb": 0, "ram_mb": 0, "cpu_percent": 0}
        active_usage = {"disk_mb": 0, "ram_mb": 0, "cpu_percent": 0}
        
        for service_name, config in self.services.items():
            # Add to total
            for resource, amount in config.resource_usage.items():
                total_usage[resource] += amount
            
            # Add to active if service is running
            if config.is_active:
                for resource, amount in config.resource_usage.items():
                    active_usage[resource] += amount
        
        savings_percentage = {}
        for resource in total_usage:
            if total_usage[resource] > 0:
                savings_percentage[resource] = (
                    (total_usage[resource] - active_usage[resource]) / total_usage[resource]
                ) * 100
            else:
                savings_percentage[resource] = 0
        
        return {
            "total_potential_usage": total_usage,
            "current_active_usage": active_usage,
            "resource_savings": self.resource_savings.copy(),
            "savings_percentage": savings_percentage,
            "degradation_level": self.current_level.value
        }