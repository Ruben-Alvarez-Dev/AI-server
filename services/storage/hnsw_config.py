#!/usr/bin/env python3
"""
HNSW Index Configuration for Qdrant

Configures HNSW (Hierarchical Navigable Small World) index parameters for optimal
vector search performance with accuracy/speed trade-offs.
"""

from typing import Dict, Any
from qdrant_client.models import HnswConfigDiff


class HnswConfig:
    """HNSW index configuration manager."""
    
    # Optimized HNSW parameters based on plan specifications
    DEFAULT_PARAMS = {
        "m": 16,              # Connectivity - number of connections per layer
        "ef_construct": 100,  # Index quality - size of dynamic candidate list
        "ef": 50,             # Search quality - size of dynamic candidate list during search
        "max_indexing_threads": 4,  # Limit threads for model compatibility
        "full_scan_threshold": 10000  # Use full scan for small collections
    }
    
    @classmethod
    def get_hnsw_config(cls, 
                       m: int = None,
                       ef_construct: int = None, 
                       ef: int = None,
                       max_indexing_threads: int = None,
                       full_scan_threshold: int = None) -> HnswConfigDiff:
        """
        Get HNSW configuration with custom or default parameters.
        
        Args:
            m: Number of connections per layer (default: 16)
               - Higher values = better accuracy, more memory
               - Lower values = faster search, less memory
            ef_construct: Size of dynamic candidate list during index construction (default: 100)
               - Higher values = better accuracy, slower indexing
               - Lower values = faster indexing, potentially lower accuracy
            ef: Size of dynamic candidate list during search (default: 50)
               - Higher values = better accuracy, slower search
               - Lower values = faster search, potentially lower accuracy
            max_indexing_threads: Maximum threads for indexing (default: 4)
            full_scan_threshold: Use brute force for collections smaller than this (default: 10000)
        
        Returns:
            HnswConfigDiff object for Qdrant collection creation
        """
        
        params = cls.DEFAULT_PARAMS.copy()
        
        # Override with custom parameters if provided
        if m is not None:
            params["m"] = m
        if ef_construct is not None:
            params["ef_construct"] = ef_construct
        if ef is not None:
            params["ef"] = ef
        if max_indexing_threads is not None:
            params["max_indexing_threads"] = max_indexing_threads
        if full_scan_threshold is not None:
            params["full_scan_threshold"] = full_scan_threshold
            
        return HnswConfigDiff(
            m=params["m"],
            ef_construct=params["ef_construct"],
            max_indexing_threads=params["max_indexing_threads"],
            full_scan_threshold=params["full_scan_threshold"]
        )
    
    @classmethod
    def get_search_params(cls, ef: int = None) -> Dict[str, Any]:
        """
        Get search parameters for query operations.
        
        Args:
            ef: Size of dynamic candidate list during search
            
        Returns:
            Search parameters dictionary
        """
        search_ef = ef if ef is not None else cls.DEFAULT_PARAMS["ef"]
        
        return {
            "hnsw_ef": search_ef,
            "exact": False  # Use HNSW approximation for speed
        }
    
    @classmethod
    def get_config_presets(cls) -> Dict[str, Dict[str, Any]]:
        """
        Get predefined configuration presets for different use cases.
        
        Returns:
            Dictionary of preset configurations
        """
        return {
            "high_accuracy": {
                "m": 32,
                "ef_construct": 200,
                "ef": 128,
                "description": "Maximum accuracy, slower search"
            },
            
            "balanced": {
                "m": 16,
                "ef_construct": 100,
                "ef": 50,
                "description": "Balanced accuracy/speed (default)"
            },
            
            "high_speed": {
                "m": 8,
                "ef_construct": 64,
                "ef": 16,
                "description": "Maximum speed, lower accuracy"
            },
            
            "memory_efficient": {
                "m": 8,
                "ef_construct": 80,
                "ef": 32,
                "description": "Lower memory usage"
            },
            
            "large_scale": {
                "m": 24,
                "ef_construct": 128,
                "ef": 64,
                "description": "Optimized for large collections (>1M vectors)"
            }
        }
    
    @classmethod
    def estimate_memory_usage(cls, 
                            num_vectors: int,
                            vector_dimension: int,
                            m: int = None) -> Dict[str, float]:
        """
        Estimate memory usage for HNSW index.
        
        Args:
            num_vectors: Number of vectors in collection
            vector_dimension: Dimension of vectors
            m: HNSW connectivity parameter
            
        Returns:
            Memory usage estimates in MB
        """
        m = m or cls.DEFAULT_PARAMS["m"]
        
        # Approximate memory calculations
        vector_memory_mb = (num_vectors * vector_dimension * 4) / (1024 * 1024)  # 4 bytes per float
        
        # HNSW graph memory (approximate)
        avg_connections = m * 1.5  # Account for layer 0 having more connections
        graph_memory_mb = (num_vectors * avg_connections * 8) / (1024 * 1024)  # 8 bytes per connection
        
        # Metadata and overhead
        metadata_memory_mb = num_vectors * 0.1 / 1024  # ~100 bytes per vector
        
        total_memory_mb = vector_memory_mb + graph_memory_mb + metadata_memory_mb
        
        return {
            "vectors_mb": round(vector_memory_mb, 2),
            "graph_mb": round(graph_memory_mb, 2),
            "metadata_mb": round(metadata_memory_mb, 2),
            "total_mb": round(total_memory_mb, 2),
            "total_gb": round(total_memory_mb / 1024, 2)
        }


def get_optimized_config_for_use_case(use_case: str) -> HnswConfigDiff:
    """
    Get optimized HNSW configuration for specific AI-Server use cases.
    
    Args:
        use_case: One of 'code', 'documents', 'summaries', 'embeddings'
        
    Returns:
        Optimized HnswConfigDiff for the use case
    """
    
    use_case_configs = {
        "code": {
            "m": 20,           # Higher connectivity for code similarity
            "ef_construct": 120,
            "ef": 60,
            "description": "Optimized for code embedding similarity"
        },
        
        "documents": {
            "m": 16,           # Balanced for document retrieval
            "ef_construct": 100,
            "ef": 50,
            "description": "Optimized for document embedding similarity"  
        },
        
        "summaries": {
            "m": 12,           # Lower connectivity for summary embeddings
            "ef_construct": 80,
            "ef": 40,
            "description": "Optimized for summary embedding similarity"
        },
        
        "embeddings": {
            "m": 24,           # High connectivity for general embeddings
            "ef_construct": 150,
            "ef": 75,
            "description": "Optimized for general purpose embeddings"
        }
    }
    
    config = use_case_configs.get(use_case, HnswConfig.DEFAULT_PARAMS)
    
    return HnswConfig.get_hnsw_config(
        m=config.get("m"),
        ef_construct=config.get("ef_construct"),
        ef=config.get("ef")
    )


if __name__ == "__main__":
    # Test HNSW configuration
    hnsw = HnswConfig()
    
    print("HNSW Configuration Test")
    print("=" * 40)
    
    # Test default configuration
    default_config = hnsw.get_hnsw_config()
    print(f"Default HNSW Config: {default_config}")
    
    # Test presets
    print("\nAvailable Presets:")
    presets = hnsw.get_config_presets()
    for name, config in presets.items():
        print(f"  {name}: {config['description']}")
        print(f"    m={config['m']}, ef_construct={config['ef_construct']}, ef={config['ef']}")
    
    # Test memory estimation
    print("\nMemory Usage Estimation (100K vectors, 768 dimensions):")
    memory_est = hnsw.estimate_memory_usage(100000, 768)
    for key, value in memory_est.items():
        print(f"  {key}: {value}")
    
    # Test use case configurations
    print("\nUse Case Configurations:")
    for use_case in ["code", "documents", "summaries", "embeddings"]:
        config = get_optimized_config_for_use_case(use_case)
        print(f"  {use_case}: m={config.m}, ef_construct={config.ef_construct}")
    
    print("\n✅ HNSW configuration test completed!")