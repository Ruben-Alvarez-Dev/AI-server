#!/usr/bin/env python3
"""
Qdrant Configuration and Connection Management

Handles Qdrant embedded mode configuration, memory limits, and vector operations.
"""

import os
import psutil
from pathlib import Path
from typing import Optional, Dict, List, Any
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams


class QdrantConfig:
    """Qdrant embedded configuration and connection manager."""
    
    def __init__(self, data_dir: str = "services/storage/data/qdrant"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Calculate 25% of available RAM for Qdrant
        self.total_memory_gb = psutil.virtual_memory().total / (1024**3)
        self.qdrant_memory_gb = round(self.total_memory_gb * 0.25, 1)
        self.qdrant_memory_mb = int(self.qdrant_memory_gb * 1024)
        
        # Embedded mode configuration
        self.client: Optional[QdrantClient] = None
        
    def get_client(self) -> QdrantClient:
        """
        Get embedded Qdrant client with optimized configuration.
        
        Returns:
            Configured Qdrant client in embedded mode
        """
        if self.client is None:
            # Create client in embedded mode
            self.client = QdrantClient(path=str(self.data_dir))
            
        return self.client
    
    def close_client(self) -> None:
        """Close the Qdrant client connection."""
        if self.client is not None:
            self.client.close()
            self.client = None
    
    def get_memory_info(self) -> Dict[str, Any]:
        """Get memory configuration information."""
        return {
            "total_system_memory_gb": self.total_memory_gb,
            "qdrant_memory_limit_gb": self.qdrant_memory_gb,
            "qdrant_memory_limit_mb": self.qdrant_memory_mb,
            "memory_percentage": 25.0,
            "data_directory": str(self.data_dir)
        }


# Global configuration instance
qdrant_config = QdrantConfig()


def get_qdrant_client() -> QdrantClient:
    """
    Convenience function to get a configured Qdrant client.
    
    Returns:
        Configured Qdrant client in embedded mode
    """
    return qdrant_config.get_client()


if __name__ == "__main__":
    # Test embedded configuration
    config = QdrantConfig()
    
    print("Qdrant Embedded Configuration:")
    memory_info = config.get_memory_info()
    for key, value in memory_info.items():
        print(f"  {key}: {value}")
    
    # Test embedded client
    try:
        client = config.get_client()
        
        # Test basic operation
        collections = client.get_collections()
        print(f"\nEmbedded client test successful!")
        print(f"Current collections: {len(collections.collections)}")
        
        config.close_client()
        print("Client closed successfully")
        
    except Exception as e:
        print(f"\nEmbedded client test failed: {e}")