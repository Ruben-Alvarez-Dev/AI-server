"""
Adaptive Resource Management System
Enterprise-grade resource monitoring and adaptation
"""

import asyncio
import psutil
import shutil
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any, Literal, Optional
from datetime import datetime, timedelta
import json

from core.logging_config import get_logger

logger = get_logger("resource_management")

@dataclass
class SystemState:
    """Current system resource state"""
    disk_usage_percent: float
    ram_usage_percent: float
    nvme_connected: bool
    available_disk_gb: float
    available_ram_gb: float
    system_pressure: Literal["low", "medium", "high", "critical"]
    cpu_usage_percent: float
    load_average: float
    
@dataclass
class PressureAnalysis:
    """Analysis of system pressure and required actions"""
    disk_pressure: float
    memory_pressure: float
    cpu_pressure: float
    action_needed: bool
    recommended_mode: str
    cleanup_required: bool
    immediate_action: Optional[str] = None

class AdaptiveResourceManager:
    """
    Central resource manager that adapts system behavior
    based on real-time resource availability
    """
    
    PRESSURE_THRESHOLDS = {
        "disk": {"medium": 70, "high": 85, "critical": 95},
        "ram": {"medium": 75, "high": 90, "critical": 95},
        "cpu": {"medium": 70, "high": 85, "critical": 95}
    }
    
    OPERATION_MODES = {
        "full_capture": {"priority": 1, "resource_usage": 1.0},
        "selective": {"priority": 2, "resource_usage": 0.6},
        "minimal": {"priority": 3, "resource_usage": 0.3},
        "emergency": {"priority": 4, "resource_usage": 0.1}
    }
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.current_mode = "full_capture"
        self.last_analysis = None
        self.mode_change_history = []
        self.emergency_triggers = []
        
        # Safety margins
        self.SAFETY_MARGINS = {
            "disk_usage_max": 90,      # Never exceed 90% disk
            "memory_usage_max": 85,    # Never exceed 85% RAM
            "emergency_free_space": 5, # Always keep 5GB free minimum
            "critical_data_backup": 2  # 2 copies of critical data
        }
        
    async def get_system_state(self) -> SystemState:
        """Analyze current system resource state"""
        try:
            # Disk usage analysis
            disk_usage = psutil.disk_usage(str(self.base_path))
            disk_percent = (disk_usage.used / disk_usage.total) * 100
            available_disk_gb = disk_usage.free / (1024**3)
            
            # Memory analysis
            memory = psutil.virtual_memory()
            ram_percent = memory.percent
            available_ram_gb = memory.available / (1024**3)
            
            # CPU analysis
            cpu_percent = psutil.cpu_percent(interval=1)
            load_avg = psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else cpu_percent
            
            # NVME detection
            nvme_connected = self._detect_nvme_connection()
            
            # Calculate overall system pressure
            pressure = self._calculate_system_pressure(disk_percent, ram_percent, cpu_percent)
            
            state = SystemState(
                disk_usage_percent=disk_percent,
                ram_usage_percent=ram_percent,
                nvme_connected=nvme_connected,
                available_disk_gb=available_disk_gb,
                available_ram_gb=available_ram_gb,
                system_pressure=pressure,
                cpu_usage_percent=cpu_percent,
                load_average=load_avg
            )
            
            logger.debug(f"System state: {pressure} pressure, {disk_percent:.1f}% disk, {ram_percent:.1f}% RAM")
            return state
            
        except Exception as e:
            logger.error(f"Error getting system state: {e}")
            # Return safe fallback state
            return SystemState(
                disk_usage_percent=50.0,
                ram_usage_percent=50.0, 
                nvme_connected=False,
                available_disk_gb=10.0,
                available_ram_gb=4.0,
                system_pressure="medium",
                cpu_usage_percent=50.0,
                load_average=2.0
            )
    
    def _calculate_system_pressure(self, disk: float, ram: float, cpu: float) -> str:
        """Calculate overall system pressure level"""
        
        # Check critical thresholds first
        if (disk >= self.PRESSURE_THRESHOLDS["disk"]["critical"] or
            ram >= self.PRESSURE_THRESHOLDS["ram"]["critical"] or
            cpu >= self.PRESSURE_THRESHOLDS["cpu"]["critical"]):
            return "critical"
        
        # Check high thresholds
        if (disk >= self.PRESSURE_THRESHOLDS["disk"]["high"] or
            ram >= self.PRESSURE_THRESHOLDS["ram"]["high"] or
            cpu >= self.PRESSURE_THRESHOLDS["cpu"]["high"]):
            return "high"
        
        # Check medium thresholds
        if (disk >= self.PRESSURE_THRESHOLDS["disk"]["medium"] or
            ram >= self.PRESSURE_THRESHOLDS["ram"]["medium"] or
            cpu >= self.PRESSURE_THRESHOLDS["cpu"]["medium"]):
            return "medium"
        
        return "low"
    
    def _detect_nvme_connection(self) -> bool:
        """Detect if external NVME is connected and accessible"""
        try:
            # Common NVME mount points on macOS
            possible_mounts = [
                "/Volumes/AI-Server-NVME",
                "/Volumes/External-NVME", 
                "/Volumes/Memory-Server",
                # Add more potential mount points
            ]
            
            for mount_point in possible_mounts:
                if Path(mount_point).exists() and Path(mount_point).is_dir():
                    # Test write access
                    test_file = Path(mount_point) / ".ai-server-test"
                    try:
                        test_file.write_text("test")
                        test_file.unlink()
                        logger.debug(f"NVME detected at {mount_point}")
                        return True
                    except:
                        continue
            
            # Check for any external drives with sufficient space (>100GB)
            partitions = psutil.disk_partitions()
            for partition in partitions:
                if '/Volumes/' in partition.mountpoint:
                    try:
                        usage = psutil.disk_usage(partition.mountpoint)
                        free_gb = usage.free / (1024**3)
                        if free_gb > 100:  # At least 100GB free
                            return True
                    except:
                        continue
                        
            return False
            
        except Exception as e:
            logger.debug(f"Error detecting NVME: {e}")
            return False
    
    async def analyze_pressure(self, state: SystemState) -> PressureAnalysis:
        """Analyze system pressure and determine required actions"""
        
        # Calculate individual pressure scores
        disk_pressure = state.disk_usage_percent
        memory_pressure = state.ram_usage_percent  
        cpu_pressure = state.cpu_usage_percent
        
        # Determine if action is needed
        action_needed = (
            disk_pressure > 70 or 
            memory_pressure > 75 or 
            cpu_pressure > 70
        )
        
        # Recommend operation mode
        if state.system_pressure == "critical":
            recommended_mode = "emergency"
        elif state.system_pressure == "high":
            recommended_mode = "minimal"
        elif state.system_pressure == "medium":
            recommended_mode = "selective"
        else:
            recommended_mode = "full_capture"
        
        # Determine if cleanup is required
        cleanup_required = disk_pressure > 80 or memory_pressure > 80
        
        # Immediate action for critical situations
        immediate_action = None
        if state.system_pressure == "critical":
            if disk_pressure > 95:
                immediate_action = "emergency_disk_cleanup"
            elif memory_pressure > 95:
                immediate_action = "emergency_memory_cleanup"
        
        analysis = PressureAnalysis(
            disk_pressure=disk_pressure,
            memory_pressure=memory_pressure,
            cpu_pressure=cpu_pressure,
            action_needed=action_needed,
            recommended_mode=recommended_mode,
            cleanup_required=cleanup_required,
            immediate_action=immediate_action
        )
        
        self.last_analysis = analysis
        return analysis
    
    async def adapt_to_pressure(self, state: SystemState) -> Dict[str, Any]:
        """Adapt system behavior to current resource pressure"""
        
        analysis = await self.analyze_pressure(state)
        adaptations = {"changes": [], "mode": self.current_mode}
        
        try:
            # Handle immediate critical actions
            if analysis.immediate_action:
                await self._handle_immediate_action(analysis.immediate_action)
                adaptations["changes"].append(f"emergency_action_{analysis.immediate_action}")
            
            # Change operation mode if needed
            if analysis.recommended_mode != self.current_mode:
                await self._change_operation_mode(analysis.recommended_mode, state.system_pressure)
                adaptations["mode"] = analysis.recommended_mode
                adaptations["changes"].append(f"mode_change_{analysis.recommended_mode}")
            
            # Apply pressure-specific adaptations
            if state.system_pressure == "critical":
                adaptations["changes"].extend(await self._critical_adaptations(state))
            elif state.system_pressure == "high":
                adaptations["changes"].extend(await self._high_pressure_adaptations(state))
            elif state.system_pressure == "medium":
                adaptations["changes"].extend(await self._medium_pressure_adaptations(state))
            
            logger.info(f"Applied {len(adaptations['changes'])} adaptations for {state.system_pressure} pressure")
            return adaptations
            
        except Exception as e:
            logger.error(f"Error adapting to pressure: {e}")
            return {"changes": [], "mode": self.current_mode, "error": str(e)}
    
    async def _handle_immediate_action(self, action: str):
        """Handle immediate emergency actions"""
        
        if action == "emergency_disk_cleanup":
            # Emergency disk cleanup - remove all temp files, logs older than 1 day
            temp_dirs = [
                self.base_path / "temp",
                self.base_path / "cache", 
                self.base_path / "logs" / "debug"
            ]
            
            for temp_dir in temp_dirs:
                if temp_dir.exists():
                    try:
                        shutil.rmtree(temp_dir)
                        temp_dir.mkdir(exist_ok=True)
                        logger.warning(f"Emergency cleanup of {temp_dir}")
                    except Exception as e:
                        logger.error(f"Failed emergency cleanup of {temp_dir}: {e}")
        
        elif action == "emergency_memory_cleanup":
            # Force garbage collection and clear caches
            import gc
            gc.collect()
            logger.warning("Emergency memory cleanup executed")
    
    async def _change_operation_mode(self, new_mode: str, reason: str):
        """Change system operation mode"""
        
        old_mode = self.current_mode
        self.current_mode = new_mode
        
        # Record mode change
        self.mode_change_history.append({
            "timestamp": datetime.now().isoformat(),
            "from_mode": old_mode,
            "to_mode": new_mode,
            "reason": reason
        })
        
        # Keep only last 100 mode changes
        if len(self.mode_change_history) > 100:
            self.mode_change_history = self.mode_change_history[-100:]
        
        logger.warning(f"Operation mode changed: {old_mode} → {new_mode} (reason: {reason})")
    
    async def _critical_adaptations(self, state: SystemState) -> list:
        """Apply critical pressure adaptations"""
        changes = []
        
        # Disable all non-essential features
        changes.append("disabled_debug_logging")
        changes.append("disabled_verbose_capture")
        changes.append("emergency_compression_enabled")
        
        # Aggressive cleanup
        changes.append("aggressive_temp_cleanup")
        changes.append("forced_garbage_collection")
        
        return changes
    
    async def _high_pressure_adaptations(self, state: SystemState) -> list:
        """Apply high pressure adaptations"""
        changes = []
        
        # Reduce buffer sizes
        changes.append("reduced_buffer_sizes")
        changes.append("increased_compression")
        
        # Reduce capture scope
        changes.append("selective_capture_only")
        changes.append("disabled_debug_sessions")
        
        return changes
    
    async def _medium_pressure_adaptations(self, state: SystemState) -> list:
        """Apply medium pressure adaptations"""
        changes = []
        
        # Moderate optimizations
        changes.append("moderate_compression")
        changes.append("background_cleanup_scheduled")
        
        return changes
    
    def get_current_configuration(self) -> Dict[str, Any]:
        """Get current adaptive configuration"""
        return {
            "mode": self.current_mode,
            "last_analysis": self.last_analysis.__dict__ if self.last_analysis else None,
            "mode_change_history": self.mode_change_history[-5:],  # Last 5 changes
            "safety_margins": self.SAFETY_MARGINS
        }
    
    async def force_mode_change(self, new_mode: str, reason: str = "manual"):
        """Force a mode change (for testing or manual intervention)"""
        if new_mode in self.OPERATION_MODES:
            await self._change_operation_mode(new_mode, f"manual: {reason}")
            logger.info(f"Forced mode change to {new_mode}")
        else:
            raise ValueError(f"Invalid mode: {new_mode}")
    
    def is_safe_operation(self, operation_type: str, estimated_resource_use: Dict[str, float]) -> bool:
        """Check if an operation is safe given current resource state"""
        
        if not self.last_analysis:
            return False  # Conservative approach
        
        # Check if operation would exceed safety margins
        future_disk = self.last_analysis.disk_pressure + estimated_resource_use.get("disk", 0)
        future_memory = self.last_analysis.memory_pressure + estimated_resource_use.get("memory", 0)
        
        if future_disk > self.SAFETY_MARGINS["disk_usage_max"]:
            return False
        if future_memory > self.SAFETY_MARGINS["memory_usage_max"]:
            return False
            
        return True