#!/usr/bin/env python3
"""
Neo4j Database Configuration

Modern Neo4j setup using official Python driver with local server instance.
Replaces obsolete embedded JAR approach with recommended server-based solution.
Optimized for ARM64 macOS with memory management and performance tuning.
"""

import os
import psutil
from typing import Optional, Dict, Any
from neo4j import GraphDatabase, Driver
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Neo4jConfig:
    """Neo4j database configuration and connection management."""
    
    def __init__(self):
        self.host = "localhost"
        self.port = 7687
        self.http_port = 7474
        self.username = "neo4j"
        self.password = "ai-server-neo4j"
        self.database = "neo4j"
        
        # Memory configuration based on system RAM (15% heap + 10% page cache)
        total_ram_gb = psutil.virtual_memory().total / (1024**3)
        self.heap_size_gb = max(1, int(total_ram_gb * 0.15))  # 15% for heap
        self.page_cache_gb = max(1, int(total_ram_gb * 0.10))  # 10% for page cache
        
        logger.info(f"Neo4j memory configuration - Total RAM: {total_ram_gb:.1f}GB")
        logger.info(f"Heap size: {self.heap_size_gb}GB, Page cache: {self.page_cache_gb}GB")
        
        self.data_dir = "/Users/server/Code/AI-projects/AI-server/services/storage/data/neo4j"
        self.driver: Optional[Driver] = None
    
    def get_connection_uri(self) -> str:
        """Get Neo4j connection URI."""
        return f"bolt://{self.host}:{self.port}"
    
    def get_jvm_args(self) -> Dict[str, str]:
        """Get JVM arguments for Neo4j server optimization."""
        return {
            "server.memory.heap.initial_size": f"{self.heap_size_gb}g",
            "server.memory.heap.max_size": f"{self.heap_size_gb}g",
            "server.memory.pagecache.size": f"{self.page_cache_gb}g",
            "server.jvm.additional": [
                "-XX:+UseG1GC",  # G1 garbage collector for low latency
                "-XX:+UnlockExperimentalVMOptions",
                "-XX:+UseTransparentHugePages",  # ARM64 optimization
                "-Dfile.encoding=UTF-8"
            ]
        }
    
    def create_data_directory(self) -> None:
        """Create Neo4j data directory structure."""
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(f"{self.data_dir}/databases", exist_ok=True)
        os.makedirs(f"{self.data_dir}/transactions", exist_ok=True)
        os.makedirs(f"{self.data_dir}/logs", exist_ok=True)
        
        logger.info(f"Neo4j data directory created: {self.data_dir}")
    
    def get_driver(self) -> Driver:
        """Get Neo4j driver instance."""
        if self.driver is None:
            try:
                self.driver = GraphDatabase.driver(
                    self.get_connection_uri(),
                    auth=(self.username, self.password),
                    max_connection_lifetime=3600,  # 1 hour
                    max_connection_pool_size=50,
                    connection_acquisition_timeout=60,  # 60 seconds
                    encrypted=False  # Local connection
                )
                logger.info("Neo4j driver created successfully")
            except Exception as e:
                logger.error(f"Failed to create Neo4j driver: {e}")
                raise
        
        return self.driver
    
    def test_connection(self) -> bool:
        """Test Neo4j database connection."""
        try:
            with self.get_driver().session(database=self.database) as session:
                result = session.run("RETURN 1 as test")
                test_value = result.single()["test"]
                
                if test_value == 1:
                    logger.info("Neo4j connection test successful")
                    return True
                else:
                    logger.error("Neo4j connection test failed - unexpected result")
                    return False
                    
        except Exception as e:
            logger.error(f"Neo4j connection test failed: {e}")
            return False
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get Neo4j server information."""
        try:
            with self.get_driver().session(database=self.database) as session:
                # Get version and configuration
                version_result = session.run("CALL dbms.components()")
                version_info = version_result.single()
                
                # Get database stats
                stats_result = session.run("CALL db.stats.retrieve('GRAPH COUNTS')")
                stats = {record["section"]: record for record in stats_result}
                
                return {
                    "version": version_info["versions"][0] if version_info else "unknown",
                    "edition": version_info["edition"] if version_info else "unknown",
                    "stats": stats,
                    "heap_size_gb": self.heap_size_gb,
                    "page_cache_gb": self.page_cache_gb
                }
                
        except Exception as e:
            logger.error(f"Failed to get server info: {e}")
            return {}
    
    def close_driver(self) -> None:
        """Close Neo4j driver connection."""
        if self.driver:
            self.driver.close()
            self.driver = None
            logger.info("Neo4j driver closed")


def get_neo4j_config() -> Neo4jConfig:
    """Get configured Neo4j instance."""
    return Neo4jConfig()


if __name__ == "__main__":
    # Test Neo4j configuration
    config = get_neo4j_config()
    
    print("Neo4j Configuration:")
    print(f"  Connection URI: {config.get_connection_uri()}")
    print(f"  Data Directory: {config.data_dir}")
    print(f"  Heap Size: {config.heap_size_gb}GB")
    print(f"  Page Cache: {config.page_cache_gb}GB")
    
    # Create data directory
    config.create_data_directory()
    
    # JVM arguments for reference
    jvm_args = config.get_jvm_args()
    print(f"  JVM Configuration: {jvm_args}")
    
    print("\nNeo4j configuration ready for server installation")