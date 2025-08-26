"""
Storage Tier Management System
Dynamic storage allocation between internal SSD and external NVME
"""

import asyncio
import psutil
import shutil
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Literal
from datetime import datetime, timedelta
import json

from core.logging_config import get_logger

logger = get_logger("storage_tier")

@dataclass
class StorageLocation:
    """Storage location configuration"""
    path: Path
    type: Literal["internal", "external_nvme", "temp"]
    max_size_gb: float
    current_usage_gb: float
    is_available: bool
    priority: int  # Lower number = higher priority
    speed_class: Literal["ssd", "nvme", "hdd"]

@dataclass
class DataCategory:
    """Data category with storage preferences"""
    name: str
    priority: Literal["critical", "high", "medium", "low"]
    preferred_location: Literal["internal", "external_nvme", "temp"]
    max_age_days: Optional[int]
    compression_enabled: bool
    backup_required: bool

class StorageTierManager:
    """
    Intelligent storage tier management that adapts to available storage
    """
    
    # Data category definitions
    DATA_CATEGORIES = {
        "system_config": DataCategory(
            name="system_config",
            priority="critical",
            preferred_location="internal",
            max_age_days=None,
            compression_enabled=False,
            backup_required=True
        ),
        "active_conversations": DataCategory(
            name="active_conversations", 
            priority="high",
            preferred_location="external_nvme",
            max_age_days=30,
            compression_enabled=True,
            backup_required=True
        ),
        "code_sessions": DataCategory(
            name="code_sessions",
            priority="high", 
            preferred_location="external_nvme",
            max_age_days=14,
            compression_enabled=True,
            backup_required=False
        ),
        "embeddings_cache": DataCategory(
            name="embeddings_cache",
            priority="medium",
            preferred_location="external_nvme",
            max_age_days=7,
            compression_enabled=True,
            backup_required=False
        ),
        "temp_processing": DataCategory(
            name="temp_processing",
            priority="low",
            preferred_location="temp",
            max_age_days=1,
            compression_enabled=False,
            backup_required=False
        ),
        "debug_logs": DataCategory(
            name="debug_logs",
            priority="low",
            preferred_location="temp",
            max_age_days=3,
            compression_enabled=True,
            backup_required=False
        ),
        "archived_sessions": DataCategory(
            name="archived_sessions",
            priority="medium",
            preferred_location="external_nvme",
            max_age_days=90,
            compression_enabled=True,
            backup_required=True
        )
    }
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.storage_locations: Dict[str, StorageLocation] = {}
        self.tier_mappings: Dict[str, str] = {}  # category -> current location
        self.migration_queue: List[Dict[str, Any]] = []
        
        # Initialize storage discovery
        asyncio.create_task(self._discover_storage_locations())
    
    async def _discover_storage_locations(self):
        """Discover and configure available storage locations"""
        
        # Internal SSD (always available)
        internal_path = self.base_path
        internal_usage = psutil.disk_usage(str(internal_path))
        
        self.storage_locations["internal"] = StorageLocation(
            path=internal_path,
            type="internal",
            max_size_gb=(internal_usage.total * 0.4) / (1024**3),  # 40% of internal disk
            current_usage_gb=self._calculate_usage(internal_path),
            is_available=True,
            priority=2,
            speed_class="ssd"
        )
        
        # External NVME detection
        nvme_location = await self._detect_external_nvme()
        if nvme_location:
            nvme_usage = psutil.disk_usage(str(nvme_location))
            self.storage_locations["external_nvme"] = StorageLocation(
                path=nvme_location,
                type="external_nvme", 
                max_size_gb=(nvme_usage.total * 0.8) / (1024**3),  # 80% of external
                current_usage_gb=self._calculate_usage(nvme_location),
                is_available=True,
                priority=1,
                speed_class="nvme"
            )
            logger.info(f"External NVME detected at {nvme_location}")
        
        # Temp storage (internal disk temp area)
        temp_path = internal_path / "temp" / "storage"
        temp_path.mkdir(parents=True, exist_ok=True)
        
        self.storage_locations["temp"] = StorageLocation(
            path=temp_path,
            type="temp",
            max_size_gb=min(5.0, (internal_usage.total * 0.1) / (1024**3)),  # 5GB or 10% max
            current_usage_gb=self._calculate_usage(temp_path),
            is_available=True,
            priority=3,
            speed_class="ssd"
        )
        
        # Initialize tier mappings
        await self._initialize_tier_mappings()
        
        logger.info(f"Discovered {len(self.storage_locations)} storage locations")
    
    async def _detect_external_nvme(self) -> Optional[Path]:
        """Detect external NVME connection"""
        
        # Check common mount points
        possible_mounts = [
            "/Volumes/AI-Server-NVME",
            "/Volumes/Memory-Server", 
            "/Volumes/External-SSD",
            "/Volumes/T7"  # Samsung T7 common name
        ]
        
        for mount_point in possible_mounts:
            path = Path(mount_point)
            if path.exists() and path.is_dir():
                try:
                    # Test write access
                    test_file = path / ".memory-server-test"
                    test_file.write_text("storage_test")
                    test_file.unlink()
                    
                    # Check available space (>50GB minimum)
                    usage = psutil.disk_usage(str(path))
                    if usage.free > 50 * (1024**3):
                        return path / "memory-server-data"
                except:
                    continue
        
        # Auto-detect external drives with sufficient space
        partitions = psutil.disk_partitions()
        for partition in partitions:
            if '/Volumes/' in partition.mountpoint:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    free_gb = usage.free / (1024**3)
                    
                    if free_gb > 100:  # At least 100GB free
                        nvme_path = Path(partition.mountpoint) / "memory-server-data"
                        nvme_path.mkdir(exist_ok=True)
                        return nvme_path
                except:
                    continue
        
        return None
    
    def _calculate_usage(self, path: Path) -> float:
        """Calculate current usage of a path in GB"""
        try:
            if not path.exists():
                return 0.0
            
            total_size = 0
            for file_path in path.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            
            return total_size / (1024**3)
        except:
            return 0.0
    
    async def _initialize_tier_mappings(self):
        """Initialize data category to storage location mappings"""
        
        for category_name, category in self.DATA_CATEGORIES.items():
            # Try preferred location first
            preferred_location = category.preferred_location
            
            if (preferred_location in self.storage_locations and 
                self.storage_locations[preferred_location].is_available):
                self.tier_mappings[category_name] = preferred_location
            else:
                # Fallback to best available location
                self.tier_mappings[category_name] = self._select_fallback_location(category)
        
        logger.info(f"Initialized tier mappings: {self.tier_mappings}")
    
    def _select_fallback_location(self, category: DataCategory) -> str:
        """Select best fallback storage location for a category"""
        
        # Sort locations by priority (lower number = higher priority)
        available_locations = [
            (name, loc) for name, loc in self.storage_locations.items() 
            if loc.is_available
        ]
        available_locations.sort(key=lambda x: x[1].priority)
        
        # For critical data, prefer internal storage as fallback
        if category.priority == "critical":
            return "internal"
        
        # Otherwise, use highest priority available location
        return available_locations[0][0] if available_locations else "internal"
    
    async def allocate_storage(self, category: str, estimated_size_gb: float) -> Path:
        """Allocate storage for a data category"""
        
        if category not in self.DATA_CATEGORIES:
            raise ValueError(f"Unknown data category: {category}")
        
        target_location = self.tier_mappings.get(category, "internal")
        storage_loc = self.storage_locations[target_location]
        
        # Check if allocation would exceed limits
        if (storage_loc.current_usage_gb + estimated_size_gb > storage_loc.max_size_gb):
            # Try to free space or migrate to different tier
            success = await self._handle_storage_pressure(category, estimated_size_gb)
            if not success:
                # Emergency fallback to temp storage
                target_location = "temp"
                storage_loc = self.storage_locations["temp"]
        
        # Create category subdirectory
        category_path = storage_loc.path / category
        category_path.mkdir(parents=True, exist_ok=True)
        
        # Update usage tracking
        storage_loc.current_usage_gb += estimated_size_gb
        
        logger.debug(f"Allocated {estimated_size_gb:.2f}GB in {target_location} for {category}")
        return category_path
    
    async def _handle_storage_pressure(self, category: str, needed_gb: float) -> bool:
        """Handle storage pressure by cleanup or migration"""
        
        target_location = self.tier_mappings[category]
        storage_loc = self.storage_locations[target_location]
        
        # Try cleanup first
        freed_gb = await self._cleanup_expired_data(target_location)
        
        if freed_gb >= needed_gb:
            storage_loc.current_usage_gb -= freed_gb
            return True
        
        # Try migration to lower priority storage
        migrated_gb = await self._migrate_to_lower_tier(target_location, needed_gb)
        
        if migrated_gb >= needed_gb:
            storage_loc.current_usage_gb -= migrated_gb
            return True
        
        return False
    
    async def _cleanup_expired_data(self, location: str) -> float:
        """Cleanup expired data in a storage location"""
        
        storage_loc = self.storage_locations[location]
        freed_gb = 0.0
        
        for category_name in self.DATA_CATEGORIES:
            if self.tier_mappings.get(category_name) != location:
                continue
            
            category = self.DATA_CATEGORIES[category_name]
            if not category.max_age_days:
                continue
            
            category_path = storage_loc.path / category_name
            if not category_path.exists():
                continue
            
            # Remove files older than max_age_days
            cutoff_time = datetime.now() - timedelta(days=category.max_age_days)
            
            for file_path in category_path.rglob("*"):
                if file_path.is_file():
                    try:
                        file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if file_time < cutoff_time:
                            file_size_gb = file_path.stat().st_size / (1024**3)
                            file_path.unlink()
                            freed_gb += file_size_gb
                    except:
                        continue
        
        if freed_gb > 0:
            logger.info(f"Cleaned up {freed_gb:.2f}GB expired data from {location}")
        
        return freed_gb
    
    async def _migrate_to_lower_tier(self, from_location: str, needed_gb: float) -> float:
        """Migrate data to lower priority storage tier"""
        
        migrated_gb = 0.0
        
        # Find categories that can be migrated to lower tiers
        for category_name, current_location in self.tier_mappings.items():
            if current_location != from_location:
                continue
            
            category = self.DATA_CATEGORIES[category_name]
            if category.priority == "critical":
                continue  # Never migrate critical data
            
            # Find lower priority storage location
            target_location = self._find_lower_tier(from_location)
            if not target_location:
                continue
            
            # Migrate category data
            source_path = self.storage_locations[from_location].path / category_name
            target_path = self.storage_locations[target_location].path / category_name
            
            if source_path.exists():
                try:
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(source_path), str(target_path))
                    
                    migrated_size = self._calculate_usage(target_path)
                    migrated_gb += migrated_size
                    
                    # Update tier mapping
                    self.tier_mappings[category_name] = target_location
                    
                    logger.info(f"Migrated {category_name} from {from_location} to {target_location}")
                    
                    if migrated_gb >= needed_gb:
                        break
                        
                except Exception as e:
                    logger.error(f"Failed to migrate {category_name}: {e}")
        
        return migrated_gb
    
    def _find_lower_tier(self, current_location: str) -> Optional[str]:
        """Find a lower priority storage tier"""
        
        current_priority = self.storage_locations[current_location].priority
        
        # Find available locations with higher priority number (lower priority)
        candidates = [
            name for name, loc in self.storage_locations.items()
            if loc.is_available and loc.priority > current_priority
        ]
        
        if not candidates:
            return None
        
        # Return the one with lowest priority number among candidates
        return min(candidates, key=lambda x: self.storage_locations[x].priority)
    
    async def get_storage_status(self) -> Dict[str, Any]:
        """Get current storage status"""
        
        status = {
            "locations": {},
            "tier_mappings": self.tier_mappings,
            "total_used_gb": 0.0,
            "total_available_gb": 0.0
        }
        
        for name, location in self.storage_locations.items():
            # Refresh current usage
            location.current_usage_gb = self._calculate_usage(location.path)
            
            status["locations"][name] = {
                "path": str(location.path),
                "type": location.type,
                "max_size_gb": location.max_size_gb,
                "current_usage_gb": location.current_usage_gb,
                "available_gb": location.max_size_gb - location.current_usage_gb,
                "usage_percent": (location.current_usage_gb / location.max_size_gb) * 100,
                "is_available": location.is_available,
                "speed_class": location.speed_class
            }
            
            status["total_used_gb"] += location.current_usage_gb
            status["total_available_gb"] += location.max_size_gb
        
        status["overall_usage_percent"] = (status["total_used_gb"] / status["total_available_gb"]) * 100
        
        return status
    
    async def optimize_storage_layout(self):
        """Optimize data placement across storage tiers"""
        
        logger.info("Starting storage layout optimization")
        
        # Refresh storage availability
        await self._discover_storage_locations()
        
        # Re-evaluate tier mappings based on current conditions
        for category_name, category in self.DATA_CATEGORIES.items():
            current_location = self.tier_mappings.get(category_name, "internal")
            optimal_location = self._get_optimal_location(category)
            
            if optimal_location != current_location:
                success = await self._migrate_category(category_name, current_location, optimal_location)
                if success:
                    self.tier_mappings[category_name] = optimal_location
        
        logger.info("Storage layout optimization completed")
    
    def _get_optimal_location(self, category: DataCategory) -> str:
        """Determine optimal storage location for a category"""
        
        # Check if preferred location is available and has space
        preferred = category.preferred_location
        if (preferred in self.storage_locations and 
            self.storage_locations[preferred].is_available):
            
            storage_loc = self.storage_locations[preferred]
            if storage_loc.current_usage_gb < storage_loc.max_size_gb * 0.8:  # 80% threshold
                return preferred
        
        # Find best alternative based on priority and availability
        return self._select_fallback_location(category)
    
    async def _migrate_category(self, category_name: str, from_location: str, to_location: str) -> bool:
        """Migrate entire category between storage locations"""
        
        source_path = self.storage_locations[from_location].path / category_name
        target_path = self.storage_locations[to_location].path / category_name
        
        if not source_path.exists():
            return True  # Nothing to migrate
        
        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source_path), str(target_path))
            
            logger.info(f"Successfully migrated {category_name}: {from_location} → {to_location}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to migrate {category_name}: {e}")
            return False
    
    def get_path_for_category(self, category: str) -> Path:
        """Get current storage path for a data category"""
        
        if category not in self.DATA_CATEGORIES:
            raise ValueError(f"Unknown data category: {category}")
        
        location = self.tier_mappings.get(category, "internal")
        return self.storage_locations[location].path / category