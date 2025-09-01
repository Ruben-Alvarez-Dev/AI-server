#!/usr/bin/env python3
"""
Neo4j Heap Configuration Manager

Manages Neo4j JVM heap limits dynamically based on available system memory.
Configures heap to 15% of available RAM and page cache to 10% additional,
with G1GC optimization for ARM64 performance.
"""

import os
import psutil
import logging
import subprocess
from typing import Dict, Any, Tuple
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Neo4jHeapConfigurator:
    """Neo4j heap configuration and optimization."""
    
    def __init__(self, neo4j_home: str = None):
        self.neo4j_home = neo4j_home or "/Users/server/Code/AI-projects/AI-server/services/storage/neo4j/neo4j-community-5.23.0"
        self.config_file = f"{self.neo4j_home}/conf/neo4j.conf"
        
        # Calculate memory allocation
        self.total_ram_gb = psutil.virtual_memory().total / (1024**3)
        self.heap_percentage = 0.15  # 15% for heap
        self.cache_percentage = 0.10  # 10% for page cache
        
        self.heap_size_gb = max(1, int(self.total_ram_gb * self.heap_percentage))
        self.cache_size_gb = max(1, int(self.total_ram_gb * self.cache_percentage))
        
        logger.info(f"System RAM: {self.total_ram_gb:.1f}GB")
        logger.info(f"Neo4j heap allocation: {self.heap_size_gb}GB ({self.heap_percentage*100}%)")
        logger.info(f"Neo4j page cache allocation: {self.cache_size_gb}GB ({self.cache_percentage*100}%)")
    
    def get_current_memory_config(self) -> Dict[str, Any]:
        """Get current Neo4j memory configuration."""
        if not os.path.exists(self.config_file):
            logger.error(f"Neo4j config file not found: {self.config_file}")
            return {}
        
        config = {}
        try:
            with open(self.config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('#') or not line:
                        continue
                    
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        if 'memory' in key.lower():
                            config[key] = value
            
            return config
            
        except Exception as e:
            logger.error(f"Failed to read config file: {e}")
            return {}
    
    def validate_memory_allocation(self) -> Dict[str, Any]:
        """Validate current memory allocation against system resources."""
        
        # Get system memory info
        memory = psutil.virtual_memory()
        available_gb = memory.available / (1024**3)
        used_gb = memory.used / (1024**3)
        
        # Calculate recommended allocation
        recommended_heap = max(1, int(self.total_ram_gb * self.heap_percentage))
        recommended_cache = max(1, int(self.total_ram_gb * self.cache_percentage))
        
        total_neo4j_allocation = recommended_heap + recommended_cache
        
        validation = {
            "system_memory": {
                "total_gb": round(self.total_ram_gb, 2),
                "available_gb": round(available_gb, 2),
                "used_gb": round(used_gb, 2),
                "usage_percentage": round((used_gb / self.total_ram_gb) * 100, 1)
            },
            "neo4j_allocation": {
                "heap_gb": recommended_heap,
                "page_cache_gb": recommended_cache,
                "total_gb": total_neo4j_allocation,
                "percentage_of_total": round((total_neo4j_allocation / self.total_ram_gb) * 100, 1)
            },
            "recommendations": []
        }
        
        # Validation checks
        if total_neo4j_allocation > available_gb:
            validation["recommendations"].append({
                "type": "WARNING",
                "message": f"Neo4j allocation ({total_neo4j_allocation}GB) exceeds available memory ({available_gb:.1f}GB)"
            })
        
        if self.total_ram_gb < 8:
            validation["recommendations"].append({
                "type": "WARNING", 
                "message": "System has less than 8GB RAM - consider increasing memory for optimal performance"
            })
        
        if total_neo4j_allocation < 2:
            validation["recommendations"].append({
                "type": "INFO",
                "message": "Neo4j allocation is less than 2GB - performance may be limited for large datasets"
            })
        
        return validation
    
    def get_jvm_optimization_flags(self) -> Dict[str, str]:
        """Get JVM optimization flags for ARM64."""
        return {
            "server.jvm.additional": [
                "-XX:+UseG1GC",  # G1 garbage collector for low latency
                "-XX:MaxGCPauseMillis=200",  # Target max GC pause time
                "-XX:+UnlockExperimentalVMOptions",
                "-XX:+UseTransparentHugePages",  # ARM64 optimization
                "-XX:+AggressiveOpts",  # Enable aggressive optimizations
                f"-XX:NewRatio=2",  # Young/Old generation ratio
                "-Dfile.encoding=UTF-8",
                "-Djava.awt.headless=true"  # Headless mode for server
            ]
        }
    
    def update_heap_configuration(self) -> bool:
        """Update Neo4j heap configuration with optimized settings."""
        logger.info("Updating Neo4j heap configuration...")
        
        try:
            # Read current config
            if not os.path.exists(self.config_file):
                logger.error(f"Config file not found: {self.config_file}")
                return False
            
            with open(self.config_file, 'r') as f:
                config_lines = f.readlines()
            
            # Prepare new configuration values
            new_config = {
                "server.memory.heap.initial_size": f"{self.heap_size_gb}g",
                "server.memory.heap.max_size": f"{self.heap_size_gb}g", 
                "server.memory.pagecache.size": f"{self.cache_size_gb}g"
            }
            
            # Add JVM optimization flags
            jvm_flags = self.get_jvm_optimization_flags()["server.jvm.additional"]
            
            # Update existing config lines
            updated_lines = []
            updated_keys = set()
            
            for line in config_lines:
                line = line.rstrip('\n')
                
                # Check if this line configures a key we want to update
                found_key = None
                for key in new_config:
                    if line.strip().startswith(key):
                        found_key = key
                        break
                
                if found_key:
                    updated_lines.append(f"{found_key}={new_config[found_key]}\n")
                    updated_keys.add(found_key)
                    logger.info(f"Updated {found_key}={new_config[found_key]}")
                else:
                    updated_lines.append(line + '\n')
            
            # Add any missing configuration keys
            for key, value in new_config.items():
                if key not in updated_keys:
                    updated_lines.append(f"{key}={value}\n")
                    logger.info(f"Added {key}={value}")
            
            # Add JVM flags (remove existing ones first)
            filtered_lines = []
            for line in updated_lines:
                if not line.strip().startswith("server.jvm.additional"):
                    filtered_lines.append(line)
            
            # Add optimized JVM flags
            for flag in jvm_flags:
                filtered_lines.append(f"server.jvm.additional={flag}\n")
                logger.info(f"Added JVM flag: {flag}")
            
            # Write updated config
            with open(self.config_file, 'w') as f:
                f.writelines(filtered_lines)
            
            logger.info("Neo4j heap configuration updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update heap configuration: {e}")
            return False
    
    def check_neo4j_process(self) -> Dict[str, Any]:
        """Check if Neo4j process is running and its memory usage."""
        try:
            # Find Neo4j process
            neo4j_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cmdline']):
                try:
                    if 'java' in proc.info['name'].lower() and any('neo4j' in arg for arg in proc.info['cmdline']):
                        memory_mb = proc.info['memory_info'].rss / (1024 * 1024)
                        neo4j_processes.append({
                            "pid": proc.info['pid'],
                            "memory_mb": round(memory_mb, 2),
                            "memory_gb": round(memory_mb / 1024, 2)
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            return {
                "running": len(neo4j_processes) > 0,
                "processes": neo4j_processes,
                "total_memory_gb": round(sum(p["memory_gb"] for p in neo4j_processes), 2) if neo4j_processes else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to check Neo4j process: {e}")
            return {"running": False, "error": str(e)}
    
    def generate_configuration_report(self) -> Dict[str, Any]:
        """Generate comprehensive configuration report."""
        logger.info("Generating Neo4j heap configuration report...")
        
        report = {
            "timestamp": psutil.boot_time(),
            "system_info": {
                "total_ram_gb": round(self.total_ram_gb, 2),
                "cpu_count": psutil.cpu_count(),
                "platform": os.uname().machine
            },
            "memory_allocation": {
                "heap_gb": self.heap_size_gb,
                "page_cache_gb": self.cache_size_gb,
                "total_neo4j_gb": self.heap_size_gb + self.cache_size_gb
            },
            "current_config": self.get_current_memory_config(),
            "validation": self.validate_memory_allocation(),
            "process_status": self.check_neo4j_process(),
            "jvm_optimizations": self.get_jvm_optimization_flags()
        }
        
        return report


def main():
    """Main function to configure Neo4j heap limits."""
    configurator = Neo4jHeapConfigurator()
    
    print("="*60)
    print("NEO4J HEAP CONFIGURATION MANAGER")
    print("="*60)
    
    # Generate report
    report = configurator.generate_configuration_report()
    
    print(f"System RAM: {report['system_info']['total_ram_gb']}GB")
    print(f"Neo4j Heap: {report['memory_allocation']['heap_gb']}GB (15%)")
    print(f"Neo4j Page Cache: {report['memory_allocation']['page_cache_gb']}GB (10%)")
    print(f"Total Neo4j Memory: {report['memory_allocation']['total_neo4j_gb']}GB")
    
    # Validate memory allocation
    validation = report['validation']
    print(f"\nMemory Validation:")
    print(f"  Available RAM: {validation['system_memory']['available_gb']:.1f}GB")
    print(f"  System Usage: {validation['system_memory']['usage_percentage']}%")
    
    if validation['recommendations']:
        print(f"  Recommendations:")
        for rec in validation['recommendations']:
            print(f"    {rec['type']}: {rec['message']}")
    
    # Check Neo4j process status
    if report['process_status']['running']:
        processes = report['process_status']['processes']
        total_memory = report['process_status']['total_memory_gb']
        print(f"\nNeo4j Status: ✅ Running ({len(processes)} process(es))")
        print(f"  Current memory usage: {total_memory}GB")
    else:
        print(f"\nNeo4j Status: ⏹️  Not running")
    
    # Update configuration
    print(f"\nUpdating heap configuration...")
    if configurator.update_heap_configuration():
        print("✅ Heap configuration updated successfully")
    else:
        print("❌ Failed to update heap configuration")
    
    # Save detailed report
    import json
    report_path = "/Users/server/Code/AI-projects/AI-server/services/storage/data/neo4j/heap_config_report.json"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"📄 Detailed report saved to: {report_path}")
    print("="*60)


if __name__ == "__main__":
    main()