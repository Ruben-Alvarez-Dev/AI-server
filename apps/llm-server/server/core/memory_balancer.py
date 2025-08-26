"""
Memory Balancer - Automatic Resource Management for M1 Ultra
Dynamically adjusts number of active coders based on memory pressure
"""

import asyncio
import logging
import psutil
import time
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import subprocess

logger = logging.getLogger(__name__)

class MemoryPressure(Enum):
    LOW = "low"           # < 60% RAM used
    MODERATE = "moderate" # 60-75% RAM used  
    HIGH = "high"         # 75-85% RAM used
    CRITICAL = "critical" # > 85% RAM used

class CoderPriority(Enum):
    ESSENTIAL = 1    # Never shutdown (router, architect)
    HIGH = 2         # Shutdown only under critical pressure
    MEDIUM = 3       # Shutdown under high pressure
    LOW = 4          # Shutdown under moderate pressure

@dataclass
class CoderResource:
    """Resource allocation info for each coder"""
    coder_name: str
    model_name: str
    allocated_ram_gb: int
    priority: CoderPriority
    current_status: str = "inactive"  # inactive, loading, active, suspended
    last_used: datetime = None
    usage_frequency: int = 0
    performance_score: float = 1.0
    
class MemoryBalancer:
    """
    Intelligent Memory Balancer for AI Orchestra
    
    Features:
    - Real-time memory monitoring
    - Dynamic coder scaling (1-6 based on pressure)
    - Priority-based resource allocation
    - Graceful model loading/unloading
    - Performance optimization
    - M1 Ultra specific optimizations
    """
    
    def __init__(self, max_ram_gb: int = 70):
        self.max_ram_gb = max_ram_gb
        self.active_coders: Set[str] = set()
        self.suspended_coders: Set[str] = set()
        
        # Default coder configurations with priorities
        self.coder_configs = {
            "router": CoderResource("router", "qwen2-1.5b", 2, CoderPriority.ESSENTIAL),
            "architect": CoderResource("architect", "qwen2.5-32b", 25, CoderPriority.ESSENTIAL),
            "zeta_fullstack": CoderResource("zeta_fullstack", "llama-3.1-8b", 8, CoderPriority.HIGH),
            "alpha_frontend": CoderResource("alpha_frontend", "qwen2.5-coder-7b", 8, CoderPriority.MEDIUM),
            "beta_backend": CoderResource("beta_backend", "deepseek-v2-lite", 12, CoderPriority.MEDIUM),
            "delta_ai": CoderResource("delta_ai", "qwen2.5-coder-14b", 13, CoderPriority.MEDIUM),
            "epsilon_mobile": CoderResource("epsilon_mobile", "codestral-22b", 18, CoderPriority.LOW),
            "gamma_systems": CoderResource("gamma_systems", "qwen2.5-32b", 25, CoderPriority.LOW),
            "vision_agent": CoderResource("vision_agent", "moondream2", 6, CoderPriority.MEDIUM)
        }
        
        # Memory monitoring state
        self.current_pressure = MemoryPressure.LOW
        self.memory_history = []
        self.balancing_active = False
        
        # Performance tracking
        self.stats = {
            'pressure_changes': 0,
            'coders_suspended': 0,
            'coders_resumed': 0,
            'memory_freed_gb': 0.0,
            'last_balance_time': None
        }
        
        # Start monitoring
        self.monitoring_task = None
        
        logger.info(f"MemoryBalancer initialized with {max_ram_gb}GB budget")
    
    async def start_monitoring(self, check_interval: float = 5.0):
        """Start continuous memory monitoring"""
        
        if self.monitoring_task and not self.monitoring_task.done():
            logger.warning("Memory monitoring already running")
            return
        
        self.monitoring_task = asyncio.create_task(
            self._monitoring_loop(check_interval)
        )
        
        logger.info("Memory monitoring started")
    
    async def stop_monitoring(self):
        """Stop memory monitoring"""
        
        if self.monitoring_task and not self.monitoring_task.done():
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Memory monitoring stopped")
    
    async def _monitoring_loop(self, check_interval: float):
        """Main memory monitoring loop"""
        
        while True:
            try:
                # Get current memory state
                memory_info = await self._get_memory_info()
                
                # Determine pressure level
                new_pressure = self._calculate_pressure(memory_info)
                
                # Check if pressure changed significantly
                if new_pressure != self.current_pressure:
                    logger.info(f"Memory pressure changed: {self.current_pressure.value} → {new_pressure.value}")
                    
                    self.current_pressure = new_pressure
                    self.stats['pressure_changes'] += 1
                    
                    # Trigger rebalancing
                    await self._rebalance_coders()
                
                # Store memory history
                self.memory_history.append({
                    'timestamp': datetime.now(),
                    'memory_info': memory_info,
                    'pressure': new_pressure,
                    'active_coders': len(self.active_coders)
                })
                
                # Keep only last hour of history
                cutoff_time = datetime.now().timestamp() - 3600
                self.memory_history = [
                    h for h in self.memory_history 
                    if h['timestamp'].timestamp() > cutoff_time
                ]
                
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Memory monitoring error: {e}")
                await asyncio.sleep(check_interval)
    
    async def _get_memory_info(self) -> Dict[str, Any]:
        """Get comprehensive memory information for M1 Ultra"""
        
        try:
            # Get system memory info
            memory = psutil.virtual_memory()
            
            # Get macOS specific memory pressure using vm_stat
            vm_stat_result = subprocess.run(
                ['vm_stat'], 
                capture_output=True, 
                text=True,
                timeout=5
            )
            
            # Parse vm_stat output for more detailed info
            vm_info = {}
            if vm_stat_result.returncode == 0:
                for line in vm_stat_result.stdout.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        try:
                            # Extract numeric value and convert pages to GB
                            numeric_value = int(value.strip().rstrip('.'))
                            vm_info[key.strip()] = (numeric_value * 16384) / (1024**3)  # Pages to GB
                        except ValueError:
                            pass
            
            # Calculate AI Orchestra specific usage
            ai_memory_usage = sum(
                config.allocated_ram_gb 
                for name, config in self.coder_configs.items() 
                if name in self.active_coders
            )
            
            return {
                'total_gb': memory.total / (1024**3),
                'available_gb': memory.available / (1024**3),
                'used_gb': memory.used / (1024**3),
                'used_percent': memory.percent,
                'free_gb': memory.free / (1024**3),
                'ai_orchestra_usage_gb': ai_memory_usage,
                'pressure_level': self._get_macos_memory_pressure(),
                'vm_stat': vm_info,
                'swap_used_gb': psutil.swap_memory().used / (1024**3)
            }
            
        except Exception as e:
            logger.error(f"Failed to get memory info: {e}")
            # Fallback basic info
            memory = psutil.virtual_memory()
            return {
                'total_gb': memory.total / (1024**3),
                'used_percent': memory.percent,
                'available_gb': memory.available / (1024**3)
            }
    
    def _get_macos_memory_pressure(self) -> str:
        """Get macOS memory pressure indicator"""
        
        try:
            result = subprocess.run(
                ['memory_pressure'], 
                capture_output=True, 
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                output = result.stdout.lower()
                if 'normal' in output:
                    return 'normal'
                elif 'warn' in output:
                    return 'warning'
                elif 'critical' in output:
                    return 'critical'
            
        except Exception as e:
            logger.debug(f"Could not get macOS memory pressure: {e}")
        
        return 'unknown'
    
    def _calculate_pressure(self, memory_info: Dict[str, Any]) -> MemoryPressure:
        """Calculate memory pressure level"""
        
        used_percent = memory_info.get('used_percent', 0)
        macos_pressure = memory_info.get('pressure_level', 'normal')
        ai_usage_gb = memory_info.get('ai_orchestra_usage_gb', 0)
        
        # Consider multiple factors
        pressure_score = 0
        
        # Base score from system memory usage
        if used_percent > 85:
            pressure_score += 4
        elif used_percent > 75:
            pressure_score += 3
        elif used_percent > 60:
            pressure_score += 2
        else:
            pressure_score += 1
        
        # Adjust for macOS memory pressure
        if macos_pressure == 'critical':
            pressure_score += 2
        elif macos_pressure == 'warning':
            pressure_score += 1
        
        # Adjust for AI Orchestra usage relative to budget
        usage_ratio = ai_usage_gb / self.max_ram_gb if self.max_ram_gb > 0 else 0
        if usage_ratio > 0.9:
            pressure_score += 2
        elif usage_ratio > 0.8:
            pressure_score += 1
        
        # Map score to pressure level
        if pressure_score >= 6:
            return MemoryPressure.CRITICAL
        elif pressure_score >= 4:
            return MemoryPressure.HIGH
        elif pressure_score >= 2:
            return MemoryPressure.MODERATE
        else:
            return MemoryPressure.LOW
    
    async def _rebalance_coders(self):
        """Rebalance active coders based on current memory pressure"""
        
        if self.balancing_active:
            logger.debug("Rebalancing already in progress, skipping")
            return
        
        self.balancing_active = True
        
        try:
            logger.info(f"Rebalancing coders for {self.current_pressure.value} memory pressure")
            
            if self.current_pressure == MemoryPressure.CRITICAL:
                await self._handle_critical_pressure()
            elif self.current_pressure == MemoryPressure.HIGH:
                await self._handle_high_pressure()
            elif self.current_pressure == MemoryPressure.MODERATE:
                await self._handle_moderate_pressure()
            else:  # LOW pressure
                await self._handle_low_pressure()
            
            self.stats['last_balance_time'] = datetime.now()
            
        finally:
            self.balancing_active = False
    
    async def _handle_critical_pressure(self):
        """Handle critical memory pressure - keep only essential coders"""
        
        # Suspend all non-essential coders
        to_suspend = []
        
        for name, config in self.coder_configs.items():
            if (name in self.active_coders and 
                config.priority != CoderPriority.ESSENTIAL):
                to_suspend.append(name)
        
        for coder_name in to_suspend:
            await self._suspend_coder(coder_name, "Critical memory pressure")
        
        logger.warning(f"Critical pressure: Suspended {len(to_suspend)} coders, keeping essentials only")
    
    async def _handle_high_pressure(self):
        """Handle high memory pressure - keep essential + high priority"""
        
        # Suspend medium and low priority coders
        to_suspend = []
        
        for name, config in self.coder_configs.items():
            if (name in self.active_coders and 
                config.priority in [CoderPriority.MEDIUM, CoderPriority.LOW]):
                to_suspend.append(name)
        
        # Sort by priority and usage to suspend least used first
        to_suspend.sort(key=lambda name: (
            self.coder_configs[name].priority.value,
            -self.coder_configs[name].usage_frequency
        ))
        
        for coder_name in to_suspend:
            await self._suspend_coder(coder_name, "High memory pressure")
        
        logger.info(f"High pressure: Suspended {len(to_suspend)} medium/low priority coders")
    
    async def _handle_moderate_pressure(self):
        """Handle moderate memory pressure - suspend lowest priority unused"""
        
        # Suspend only low priority coders that haven't been used recently
        to_suspend = []
        current_time = datetime.now()
        
        for name, config in self.coder_configs.items():
            if (name in self.active_coders and 
                config.priority == CoderPriority.LOW):
                
                # Check if unused for more than 10 minutes
                if (config.last_used is None or 
                    (current_time - config.last_used).total_seconds() > 600):
                    to_suspend.append(name)
        
        for coder_name in to_suspend:
            await self._suspend_coder(coder_name, "Moderate pressure - unused low priority")
        
        if to_suspend:
            logger.info(f"Moderate pressure: Suspended {len(to_suspend)} unused low priority coders")
    
    async def _handle_low_pressure(self):
        """Handle low memory pressure - resume suspended coders if beneficial"""
        
        # Resume suspended coders based on priority and recent usage
        to_resume = []
        
        for name in self.suspended_coders.copy():
            config = self.coder_configs.get(name)
            if not config:
                continue
            
            # Resume high priority coders first
            if config.priority in [CoderPriority.HIGH, CoderPriority.MEDIUM]:
                to_resume.append(name)
            # Resume low priority if they were used recently
            elif config.usage_frequency > 0:
                to_resume.append(name)
        
        # Sort by priority for resumption order
        to_resume.sort(key=lambda name: self.coder_configs[name].priority.value)
        
        # Resume coders while we have memory budget
        current_usage = sum(
            config.allocated_ram_gb 
            for name, config in self.coder_configs.items() 
            if name in self.active_coders
        )
        
        for coder_name in to_resume:
            config = self.coder_configs[coder_name]
            if current_usage + config.allocated_ram_gb <= self.max_ram_gb:
                await self._resume_coder(coder_name, "Low pressure - resuming suspended coder")
                current_usage += config.allocated_ram_gb
        
        if to_resume:
            logger.info(f"Low pressure: Resumed {len(to_resume)} suspended coders")
    
    async def _suspend_coder(self, coder_name: str, reason: str):
        """Suspend a coder to free memory"""
        
        if coder_name not in self.active_coders:
            return
        
        config = self.coder_configs.get(coder_name)
        if not config:
            return
        
        # Mark as suspended
        self.active_coders.discard(coder_name)
        self.suspended_coders.add(coder_name)
        config.current_status = "suspended"
        
        # Track statistics
        self.stats['coders_suspended'] += 1
        self.stats['memory_freed_gb'] += config.allocated_ram_gb
        
        logger.info(f"Suspended {coder_name} ({config.allocated_ram_gb}GB freed): {reason}")
        
        # TODO: In full implementation, send signal to actual coder process to unload model
        # This would involve IPC with the actual model servers
    
    async def _resume_coder(self, coder_name: str, reason: str):
        """Resume a suspended coder"""
        
        if coder_name not in self.suspended_coders:
            return
        
        config = self.coder_configs.get(coder_name)
        if not config:
            return
        
        # Mark as active
        self.suspended_coders.discard(coder_name)
        self.active_coders.add(coder_name)
        config.current_status = "loading"  # Will be "active" once model loads
        
        # Track statistics
        self.stats['coders_resumed'] += 1
        
        logger.info(f"Resuming {coder_name} ({config.allocated_ram_gb}GB allocated): {reason}")
        
        # TODO: In full implementation, send signal to coder process to load model
    
    async def request_coder(self, coder_name: str, task_priority: str = "medium") -> bool:
        """Request a coder for use - may trigger resume or deny based on memory"""
        
        config = self.coder_configs.get(coder_name)
        if not config:
            return False
        
        # Update usage statistics
        config.last_used = datetime.now()
        config.usage_frequency += 1
        
        # If already active, just return True
        if coder_name in self.active_coders:
            return True
        
        # If suspended, check if we can resume
        if coder_name in self.suspended_coders:
            current_usage = sum(
                c.allocated_ram_gb 
                for name, c in self.coder_configs.items() 
                if name in self.active_coders
            )
            
            # Check if we have budget
            if current_usage + config.allocated_ram_gb <= self.max_ram_gb:
                await self._resume_coder(coder_name, f"Requested for {task_priority} priority task")
                return True
            else:
                # Try to make space by suspending lower priority coders
                if await self._make_space_for_coder(coder_name, task_priority):
                    await self._resume_coder(coder_name, f"Made space for {task_priority} priority task")
                    return True
        
        return False
    
    async def _make_space_for_coder(self, requested_coder: str, task_priority: str) -> bool:
        """Try to make space for a requested coder by suspending others"""
        
        requested_config = self.coder_configs.get(requested_coder)
        if not requested_config:
            return False
        
        needed_memory = requested_config.allocated_ram_gb
        
        # Find coders we can suspend to make space
        candidates = []
        
        for name, config in self.coder_configs.items():
            if (name in self.active_coders and 
                name != requested_coder and
                config.priority.value >= requested_config.priority.value):
                
                # Prefer suspending coders that haven't been used recently
                unused_time = 0
                if config.last_used:
                    unused_time = (datetime.now() - config.last_used).total_seconds()
                
                candidates.append((name, config.allocated_ram_gb, unused_time))
        
        # Sort by priority and unused time
        candidates.sort(key=lambda x: (-x[1], -x[2]))  # Prefer larger, more unused
        
        # Suspend candidates until we have enough space
        freed_memory = 0
        for name, memory, unused_time in candidates:
            if freed_memory >= needed_memory:
                break
            
            await self._suspend_coder(name, f"Making space for {requested_coder}")
            freed_memory += memory
        
        return freed_memory >= needed_memory
    
    def get_active_coders(self) -> List[str]:
        """Get list of currently active coders"""
        return list(self.active_coders)
    
    def get_suspended_coders(self) -> List[str]:
        """Get list of currently suspended coders"""
        return list(self.suspended_coders)
    
    def get_memory_status(self) -> Dict[str, Any]:
        """Get comprehensive memory status"""
        
        active_memory = sum(
            config.allocated_ram_gb 
            for name, config in self.coder_configs.items() 
            if name in self.active_coders
        )
        
        suspended_memory = sum(
            config.allocated_ram_gb 
            for name, config in self.coder_configs.items() 
            if name in self.suspended_coders
        )
        
        return {
            'current_pressure': self.current_pressure.value,
            'active_coders': len(self.active_coders),
            'suspended_coders': len(self.suspended_coders),
            'active_memory_gb': active_memory,
            'suspended_memory_gb': suspended_memory,
            'total_budget_gb': self.max_ram_gb,
            'utilization_percent': (active_memory / self.max_ram_gb) * 100,
            'available_memory_gb': self.max_ram_gb - active_memory,
            'coder_details': {
                name: {
                    'status': 'active' if name in self.active_coders else 'suspended',
                    'memory_gb': config.allocated_ram_gb,
                    'priority': config.priority.value,
                    'last_used': config.last_used.isoformat() if config.last_used else None,
                    'usage_frequency': config.usage_frequency
                }
                for name, config in self.coder_configs.items()
            },
            'statistics': self.stats
        }
    
    async def force_rebalance(self):
        """Force immediate rebalancing regardless of current state"""
        
        logger.info("Forcing memory rebalancing")
        await self._rebalance_coders()
    
    def set_coder_priority(self, coder_name: str, priority: CoderPriority):
        """Update coder priority"""
        
        if coder_name in self.coder_configs:
            self.coder_configs[coder_name].priority = priority
            logger.info(f"Updated {coder_name} priority to {priority.name}")
    
    def get_memory_history(self, hours: int = 1) -> List[Dict[str, Any]]:
        """Get memory usage history"""
        
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        
        return [
            {
                **h,
                'timestamp': h['timestamp'].isoformat(),
                'pressure': h['pressure'].value
            }
            for h in self.memory_history 
            if h['timestamp'].timestamp() > cutoff_time
        ]

# Global memory balancer instance
memory_balancer = MemoryBalancer()

# Export
__all__ = ['MemoryBalancer', 'MemoryPressure', 'CoderPriority', 'memory_balancer']