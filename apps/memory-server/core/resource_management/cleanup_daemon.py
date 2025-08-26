"""
Intelligent Cleanup Daemon
Proactive cleanup system that prevents resource exhaustion
"""

import asyncio
import psutil
import shutil
import gzip
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
import json
import aiofiles
import hashlib

from core.logging_config import get_logger

logger = get_logger("cleanup_daemon")

@dataclass
class CleanupRule:
    """Cleanup rule configuration"""
    name: str
    path_pattern: str
    max_age_hours: int
    max_size_mb: Optional[int]
    priority: int  # Lower = higher priority
    compress_before_delete: bool
    backup_before_delete: bool
    file_extensions: Optional[Set[str]] = None

@dataclass  
class CleanupStats:
    """Cleanup operation statistics"""
    files_deleted: int = 0
    files_compressed: int = 0
    files_backed_up: int = 0
    bytes_freed: int = 0
    bytes_compressed: int = 0
    errors: int = 0
    duration_seconds: float = 0.0

class IntelligentCleanupDaemon:
    """
    Proactive cleanup daemon that maintains system health
    """
    
    CLEANUP_RULES = [
        # Emergency rules (highest priority)
        CleanupRule(
            name="emergency_temp_cleanup",
            path_pattern="temp/**/*.tmp",
            max_age_hours=1,
            max_size_mb=None,
            priority=1,
            compress_before_delete=False,
            backup_before_delete=False,
            file_extensions={".tmp", ".temp", ".cache"}
        ),
        
        CleanupRule(
            name="emergency_log_cleanup", 
            path_pattern="logs/debug/**/*.log",
            max_age_hours=6,
            max_size_mb=100,
            priority=2,
            compress_before_delete=True,
            backup_before_delete=False,
            file_extensions={".log"}
        ),
        
        # Standard rules
        CleanupRule(
            name="old_debug_sessions",
            path_pattern="debug_sessions/**/*.json",
            max_age_hours=72,  # 3 days
            max_size_mb=None,
            priority=10,
            compress_before_delete=True,
            backup_before_delete=True,
            file_extensions={".json", ".jsonl"}
        ),
        
        CleanupRule(
            name="expired_embeddings_cache",
            path_pattern="embeddings_cache/**/*.pkl",
            max_age_hours=168,  # 1 week
            max_size_mb=1000,  # 1GB per file
            priority=15,
            compress_before_delete=True,
            backup_before_delete=False,
            file_extensions={".pkl", ".cache"}
        ),
        
        CleanupRule(
            name="old_conversation_history",
            path_pattern="conversations/**/*.jsonl",
            max_age_hours=720,  # 30 days
            max_size_mb=None,
            priority=20,
            compress_before_delete=True,
            backup_before_delete=True,
            file_extensions={".jsonl", ".json"}
        ),
        
        CleanupRule(
            name="stale_processing_files",
            path_pattern="processing/**/*",
            max_age_hours=12,
            max_size_mb=None,
            priority=5,
            compress_before_delete=False,
            backup_before_delete=False
        ),
        
        CleanupRule(
            name="large_temp_files",
            path_pattern="**/*.tmp",
            max_age_hours=24,
            max_size_mb=500,  # 500MB
            priority=8,
            compress_before_delete=False,
            backup_before_delete=False,
            file_extensions={".tmp", ".temp"}
        )
    ]
    
    COMPRESSION_TARGETS = {
        ".log": ".gz",
        ".json": ".gz", 
        ".jsonl": ".gz",
        ".txt": ".gz",
        ".csv": ".gz"
    }
    
    def __init__(self, base_path: Path, backup_path: Optional[Path] = None):
        self.base_path = base_path
        self.backup_path = backup_path or (base_path / "backups")
        self.cleanup_stats = CleanupStats()
        self.is_running = False
        self.emergency_mode = False
        
        # Ensure backup directory exists
        self.backup_path.mkdir(parents=True, exist_ok=True)
        
        # Cleanup intervals (seconds)
        self.INTERVALS = {
            "normal": 300,      # 5 minutes
            "aggressive": 60,   # 1 minute
            "emergency": 10     # 10 seconds
        }
        
        self.current_interval = self.INTERVALS["normal"]
    
    async def start_daemon(self):
        """Start the cleanup daemon"""
        
        if self.is_running:
            logger.warning("Cleanup daemon already running")
            return
        
        self.is_running = True
        logger.info("Starting intelligent cleanup daemon")
        
        try:
            while self.is_running:
                await self._cleanup_cycle()
                await asyncio.sleep(self.current_interval)
                
        except Exception as e:
            logger.error(f"Cleanup daemon error: {e}")
        finally:
            self.is_running = False
            logger.info("Cleanup daemon stopped")
    
    async def stop_daemon(self):
        """Stop the cleanup daemon"""
        self.is_running = False
        logger.info("Stopping cleanup daemon")
    
    async def _cleanup_cycle(self):
        """Execute one cleanup cycle"""
        
        cycle_start = datetime.now()
        
        try:
            # Check system pressure and adjust mode
            await self._assess_system_pressure()
            
            # Execute cleanup rules based on current mode
            if self.emergency_mode:
                await self._emergency_cleanup()
            else:
                await self._standard_cleanup()
            
            # Update statistics
            cycle_duration = (datetime.now() - cycle_start).total_seconds()
            self.cleanup_stats.duration_seconds = cycle_duration
            
            logger.debug(f"Cleanup cycle completed in {cycle_duration:.2f}s")
            
        except Exception as e:
            logger.error(f"Cleanup cycle error: {e}")
            self.cleanup_stats.errors += 1
    
    async def _assess_system_pressure(self):
        """Assess current system pressure and adjust cleanup mode"""
        
        # Get disk usage
        disk_usage = psutil.disk_usage(str(self.base_path))
        disk_percent = (disk_usage.used / disk_usage.total) * 100
        
        # Get memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # Determine cleanup mode based on pressure
        old_mode = self.emergency_mode
        old_interval = self.current_interval
        
        if disk_percent > 90 or memory_percent > 90:
            self.emergency_mode = True
            self.current_interval = self.INTERVALS["emergency"]
        elif disk_percent > 80 or memory_percent > 80:
            self.emergency_mode = False
            self.current_interval = self.INTERVALS["aggressive"]
        else:
            self.emergency_mode = False
            self.current_interval = self.INTERVALS["normal"]
        
        # Log mode changes
        if old_mode != self.emergency_mode or old_interval != self.current_interval:
            mode = "emergency" if self.emergency_mode else "normal"
            logger.warning(f"Cleanup mode changed to {mode} (disk: {disk_percent:.1f}%, mem: {memory_percent:.1f}%)")
    
    async def _emergency_cleanup(self):
        """Execute emergency cleanup (most aggressive)"""
        
        logger.warning("Executing emergency cleanup")
        
        # Only run highest priority rules (priority <= 5)
        emergency_rules = [rule for rule in self.CLEANUP_RULES if rule.priority <= 5]
        
        for rule in sorted(emergency_rules, key=lambda x: x.priority):
            await self._execute_cleanup_rule(rule, aggressive=True)
    
    async def _standard_cleanup(self):
        """Execute standard cleanup cycle"""
        
        # Run rules based on system pressure
        disk_usage = psutil.disk_usage(str(self.base_path))
        disk_percent = (disk_usage.used / disk_usage.total) * 100
        
        # Determine which rules to run
        if disk_percent > 75:
            # Run high and medium priority rules
            rules_to_run = [rule for rule in self.CLEANUP_RULES if rule.priority <= 15]
        elif disk_percent > 60:
            # Run medium priority rules
            rules_to_run = [rule for rule in self.CLEANUP_RULES if rule.priority <= 20] 
        else:
            # Run low priority maintenance
            rules_to_run = [rule for rule in self.CLEANUP_RULES if rule.priority > 15]
        
        # Execute selected rules
        for rule in sorted(rules_to_run, key=lambda x: x.priority):
            await self._execute_cleanup_rule(rule, aggressive=False)
    
    async def _execute_cleanup_rule(self, rule: CleanupRule, aggressive: bool = False):
        """Execute a specific cleanup rule"""
        
        logger.debug(f"Executing cleanup rule: {rule.name}")
        
        try:
            # Find files matching the rule
            target_files = await self._find_target_files(rule)
            
            if not target_files:
                return
            
            # Process each file
            for file_path in target_files:
                try:
                    await self._process_file(file_path, rule, aggressive)
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
                    self.cleanup_stats.errors += 1
            
            logger.debug(f"Completed cleanup rule: {rule.name} ({len(target_files)} files)")
            
        except Exception as e:
            logger.error(f"Error executing cleanup rule {rule.name}: {e}")
            self.cleanup_stats.errors += 1
    
    async def _find_target_files(self, rule: CleanupRule) -> List[Path]:
        """Find files matching cleanup rule criteria"""
        
        target_files = []
        cutoff_time = datetime.now() - timedelta(hours=rule.max_age_hours)
        
        # Use glob pattern to find candidate files
        pattern_parts = rule.path_pattern.split("/")
        search_root = self.base_path
        
        try:
            # Handle different path patterns
            if "**" in rule.path_pattern:
                # Recursive search
                for file_path in search_root.rglob("*"):
                    if await self._matches_rule_criteria(file_path, rule, cutoff_time):
                        target_files.append(file_path)
            else:
                # Direct pattern match
                for file_path in search_root.glob(rule.path_pattern):
                    if await self._matches_rule_criteria(file_path, rule, cutoff_time):
                        target_files.append(file_path)
        
        except Exception as e:
            logger.error(f"Error finding target files for {rule.name}: {e}")
        
        # Sort by modification time (oldest first for fair cleanup)
        target_files.sort(key=lambda x: x.stat().st_mtime)
        
        return target_files
    
    async def _matches_rule_criteria(self, file_path: Path, rule: CleanupRule, cutoff_time: datetime) -> bool:
        """Check if file matches rule criteria"""
        
        if not file_path.is_file():
            return False
        
        try:
            file_stat = file_path.stat()
            file_time = datetime.fromtimestamp(file_stat.st_mtime)
            
            # Check age
            if file_time > cutoff_time:
                return False
            
            # Check size
            if rule.max_size_mb:
                file_size_mb = file_stat.st_size / (1024 * 1024)
                if file_size_mb < rule.max_size_mb:
                    return False
            
            # Check file extension
            if rule.file_extensions:
                if file_path.suffix.lower() not in rule.file_extensions:
                    return False
            
            return True
            
        except Exception as e:
            logger.debug(f"Error checking file criteria for {file_path}: {e}")
            return False
    
    async def _process_file(self, file_path: Path, rule: CleanupRule, aggressive: bool):
        """Process a single file according to cleanup rule"""
        
        file_size = file_path.stat().st_size
        
        try:
            # Backup if required and not aggressive mode
            if rule.backup_before_delete and not aggressive:
                await self._backup_file(file_path)
                self.cleanup_stats.files_backed_up += 1
            
            # Compress if required and not aggressive mode  
            if rule.compress_before_delete and not aggressive:
                compressed_path = await self._compress_file(file_path)
                if compressed_path:
                    file_path = compressed_path
                    self.cleanup_stats.files_compressed += 1
            
            # Delete the file
            file_path.unlink()
            self.cleanup_stats.files_deleted += 1
            self.cleanup_stats.bytes_freed += file_size
            
            logger.debug(f"Cleaned up: {file_path}")
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            self.cleanup_stats.errors += 1
            raise
    
    async def _backup_file(self, file_path: Path) -> Path:
        """Create backup of file before deletion"""
        
        # Create backup directory structure
        rel_path = file_path.relative_to(self.base_path)
        backup_file = self.backup_path / rel_path
        backup_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Add timestamp to backup name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{backup_file.stem}_{timestamp}{backup_file.suffix}"
        backup_file = backup_file.parent / backup_name
        
        # Copy file to backup location
        shutil.copy2(file_path, backup_file)
        
        logger.debug(f"Backed up: {file_path} → {backup_file}")
        return backup_file
    
    async def _compress_file(self, file_path: Path) -> Optional[Path]:
        """Compress file before deletion"""
        
        if file_path.suffix not in self.COMPRESSION_TARGETS:
            return None
        
        compressed_suffix = self.COMPRESSION_TARGETS[file_path.suffix]
        compressed_path = file_path.with_suffix(f"{file_path.suffix}{compressed_suffix}")
        
        try:
            # Compress file using gzip
            async with aiofiles.open(file_path, 'rb') as f_in:
                content = await f_in.read()
            
            with gzip.open(compressed_path, 'wb') as f_out:
                f_out.write(content)
            
            # Verify compression
            if compressed_path.exists():
                original_size = file_path.stat().st_size
                compressed_size = compressed_path.stat().st_size
                compression_ratio = compressed_size / original_size
                
                # Only keep compressed version if significant savings
                if compression_ratio < 0.8:  # At least 20% savings
                    self.cleanup_stats.bytes_compressed += (original_size - compressed_size)
                    logger.debug(f"Compressed: {file_path} ({compression_ratio:.2%} of original)")
                    return compressed_path
                else:
                    # Remove compressed version if not beneficial
                    compressed_path.unlink()
                    return None
            
        except Exception as e:
            logger.error(f"Error compressing {file_path}: {e}")
            if compressed_path.exists():
                compressed_path.unlink()
            return None
        
        return None
    
    async def force_cleanup(self, rule_name: Optional[str] = None):
        """Force immediate cleanup execution"""
        
        logger.info("Force cleanup initiated")
        
        if rule_name:
            # Execute specific rule
            rule = next((r for r in self.CLEANUP_RULES if r.name == rule_name), None)
            if rule:
                await self._execute_cleanup_rule(rule, aggressive=True)
            else:
                raise ValueError(f"Unknown cleanup rule: {rule_name}")
        else:
            # Execute emergency cleanup
            await self._emergency_cleanup()
        
        logger.info("Force cleanup completed")
    
    def get_cleanup_stats(self) -> Dict[str, Any]:
        """Get current cleanup statistics"""
        
        return {
            "files_deleted": self.cleanup_stats.files_deleted,
            "files_compressed": self.cleanup_stats.files_compressed,
            "files_backed_up": self.cleanup_stats.files_backed_up,
            "bytes_freed": self.cleanup_stats.bytes_freed,
            "bytes_compressed": self.cleanup_stats.bytes_compressed,
            "errors": self.cleanup_stats.errors,
            "last_duration_seconds": self.cleanup_stats.duration_seconds,
            "emergency_mode": self.emergency_mode,
            "current_interval": self.current_interval,
            "is_running": self.is_running
        }
    
    def reset_stats(self):
        """Reset cleanup statistics"""
        self.cleanup_stats = CleanupStats()
        logger.info("Cleanup statistics reset")
    
    async def get_disk_usage_report(self) -> Dict[str, Any]:
        """Generate detailed disk usage report"""
        
        report = {
            "total_usage": {},
            "directory_breakdown": {},
            "large_files": [],
            "cleanup_candidates": {}
        }
        
        # Overall disk usage
        disk_usage = psutil.disk_usage(str(self.base_path))
        report["total_usage"] = {
            "total_gb": disk_usage.total / (1024**3),
            "used_gb": disk_usage.used / (1024**3),  
            "free_gb": disk_usage.free / (1024**3),
            "usage_percent": (disk_usage.used / disk_usage.total) * 100
        }
        
        # Directory breakdown
        for item in self.base_path.iterdir():
            if item.is_dir():
                try:
                    dir_size = await self._calculate_directory_size(item)
                    report["directory_breakdown"][item.name] = {
                        "size_gb": dir_size / (1024**3),
                        "size_mb": dir_size / (1024**2)
                    }
                except:
                    continue
        
        # Find large files (>100MB)
        large_files = []
        try:
            for file_path in self.base_path.rglob("*"):
                if file_path.is_file():
                    file_size = file_path.stat().st_size
                    if file_size > 100 * 1024 * 1024:  # >100MB
                        large_files.append({
                            "path": str(file_path.relative_to(self.base_path)),
                            "size_mb": file_size / (1024**2),
                            "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                        })
        except:
            pass
        
        # Sort by size and limit to top 20
        report["large_files"] = sorted(large_files, key=lambda x: x["size_mb"], reverse=True)[:20]
        
        # Cleanup candidates
        for rule in self.CLEANUP_RULES:
            try:
                candidates = await self._find_target_files(rule)
                if candidates:
                    total_size = sum(f.stat().st_size for f in candidates)
                    report["cleanup_candidates"][rule.name] = {
                        "file_count": len(candidates),
                        "total_size_mb": total_size / (1024**2),
                        "potential_savings_mb": total_size / (1024**2)
                    }
            except:
                continue
        
        return report
    
    async def _calculate_directory_size(self, directory: Path) -> int:
        """Calculate total size of directory"""
        
        total_size = 0
        try:
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except:
            pass
        
        return total_size