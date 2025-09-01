#!/usr/bin/env python3
"""
DuckDB Configuration and Connection Management

Handles DuckDB memory limits, connection pooling, and optimization settings.
"""

import os
import psutil
import duckdb
from pathlib import Path
from typing import Optional, Dict, Any


class DuckDBConfig:
    """DuckDB configuration and connection manager."""
    
    def __init__(self, data_dir: str = "services/storage/data/duckdb"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Calculate 20% of available RAM for DuckDB
        self.total_memory_gb = psutil.virtual_memory().total / (1024**3)
        self.duckdb_memory_gb = round(self.total_memory_gb * 0.20, 1)
        self.duckdb_memory_setting = f"{self.duckdb_memory_gb}GB"
        
    def get_connection(self, database_name: str = "analytics") -> duckdb.DuckDBPyConnection:
        """
        Get a DuckDB connection with optimized settings.
        
        Args:
            database_name: Name of the database file
            
        Returns:
            Configured DuckDB connection
        """
        db_path = self.data_dir / f"{database_name}.db"
        conn = duckdb.connect(str(db_path))
        
        # Configure memory limits and optimization
        self._configure_connection(conn)
        
        return conn
    
    def _configure_connection(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Apply configuration settings to a connection."""
        
        # Memory configuration (20% of available RAM)
        conn.execute(f"SET memory_limit='{self.duckdb_memory_setting}'")
        
        # Performance optimizations
        conn.execute("SET threads=4")  # Limit threads to preserve CPU for models
        conn.execute("SET temp_directory='/tmp/duckdb'")
        
        # Optimization settings  
        conn.execute("SET preserve_insertion_order=false")  # Better performance
        
    def create_temp_directory(self) -> None:
        """Create temporary directory for DuckDB spill operations."""
        temp_dir = Path("/tmp/duckdb")
        temp_dir.mkdir(exist_ok=True)
        
    def get_memory_info(self) -> Dict[str, Any]:
        """Get memory configuration information."""
        return {
            "total_system_memory_gb": self.total_memory_gb,
            "duckdb_memory_limit_gb": self.duckdb_memory_gb,
            "duckdb_memory_setting": self.duckdb_memory_setting,
            "memory_percentage": 20.0
        }


# Global configuration instance
duckdb_config = DuckDBConfig()


def get_duckdb_connection(database_name: str = "analytics") -> duckdb.DuckDBPyConnection:
    """
    Convenience function to get a configured DuckDB connection.
    
    Args:
        database_name: Name of the database file
        
    Returns:
        Configured DuckDB connection
    """
    return duckdb_config.get_connection(database_name)


if __name__ == "__main__":
    # Test configuration
    config = DuckDBConfig()
    config.create_temp_directory()
    
    print("DuckDB Configuration:")
    memory_info = config.get_memory_info()
    for key, value in memory_info.items():
        print(f"  {key}: {value}")
    
    # Test connection
    conn = config.get_connection("test")
    result = conn.execute("SELECT 'DuckDB configuration test successful' as message").fetchone()
    print(f"\nTest result: {result[0]}")
    conn.close()