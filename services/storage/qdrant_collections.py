#!/usr/bin/env python3
"""
Qdrant Collections Management

Creates and manages initial vector collections for different embedding types:
code, documents, summaries with appropriate vector dimensions and metadata.
"""

from typing import Dict, List, Any, Optional
from qdrant_client.models import Distance, VectorParams
from qdrant_config import get_qdrant_client
from hnsw_config import get_optimized_config_for_use_case


class QdrantCollections:
    """Manages Qdrant vector collections for AI-Server use cases."""
    
    # Collection definitions with vector dimensions for different embedding types
    COLLECTION_DEFINITIONS = {
        "code_embeddings": {
            "description": "Source code and programming content embeddings",
            "vector_size": 768,  # Common embedding dimension for code models
            "distance": Distance.COSINE,
            "use_case": "code",
            "metadata_fields": ["language", "repository", "file_path", "function_name", "line_number"]
        },
        
        "document_embeddings": {
            "description": "Document and text content embeddings",
            "vector_size": 1536,  # Larger dimension for document models
            "distance": Distance.COSINE,
            "use_case": "documents",
            "metadata_fields": ["title", "author", "document_type", "created_at", "tags"]
        },
        
        "summary_embeddings": {
            "description": "Summary and abstract embeddings",
            "vector_size": 512,   # Smaller dimension for summary models
            "distance": Distance.COSINE,
            "use_case": "summaries",
            "metadata_fields": ["original_length", "summary_type", "key_topics", "confidence_score"]
        },
        
        "general_embeddings": {
            "description": "General purpose embeddings storage",
            "vector_size": 1024,  # Balanced dimension for general use
            "distance": Distance.COSINE,
            "use_case": "embeddings",
            "metadata_fields": ["content_type", "source", "category", "importance", "timestamp"]
        }
    }
    
    def __init__(self):
        self.client = None
    
    def get_client(self):
        """Get Qdrant client, creating if needed."""
        if self.client is None:
            self.client = get_qdrant_client()
        return self.client
    
    def create_collection(self, 
                         collection_name: str,
                         vector_size: int,
                         distance: Distance = Distance.COSINE,
                         use_case: str = "embeddings") -> bool:
        """
        Create a vector collection with optimized settings.
        
        Args:
            collection_name: Name of the collection
            vector_size: Dimension of vectors
            distance: Distance metric (COSINE, EUCLIDEAN, DOT)
            use_case: Use case for HNSW optimization
            
        Returns:
            True if collection created successfully
        """
        try:
            client = self.get_client()
            
            # Check if collection already exists
            collections = client.get_collections()
            existing_names = [col.name for col in collections.collections]
            
            if collection_name in existing_names:
                print(f"✅ Collection '{collection_name}' already exists")
                return True
            
            # Get optimized HNSW configuration for use case
            hnsw_config = get_optimized_config_for_use_case(use_case)
            
            # Create collection with optimized settings
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=distance
                ),
                hnsw_config=hnsw_config
                # Note: Quantization will be added when we insert vectors
            )
            
            print(f"✅ Created collection '{collection_name}' ({vector_size}D, {distance.value}, {use_case})")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create collection '{collection_name}': {e}")
            return False
    
    def create_all_initial_collections(self) -> Dict[str, bool]:
        """
        Create all initial collections defined in COLLECTION_DEFINITIONS.
        
        Returns:
            Dictionary mapping collection names to creation success status
        """
        results = {}
        
        print("Creating initial Qdrant collections...")
        print("=" * 50)
        
        for collection_name, config in self.COLLECTION_DEFINITIONS.items():
            print(f"\nCreating {collection_name}:")
            print(f"  Description: {config['description']}")
            print(f"  Vector Size: {config['vector_size']}")
            print(f"  Distance: {config['distance'].value}")
            print(f"  Use Case: {config['use_case']}")
            
            success = self.create_collection(
                collection_name=collection_name,
                vector_size=config['vector_size'],
                distance=config['distance'],
                use_case=config['use_case']
            )
            
            results[collection_name] = success
            
        return results
    
    def list_collections(self) -> List[Dict[str, Any]]:
        """
        List all existing collections with their details.
        
        Returns:
            List of collection information dictionaries
        """
        try:
            client = self.get_client()
            collections = client.get_collections()
            
            collection_info = []
            
            for collection in collections.collections:
                try:
                    # Get collection info
                    info = client.get_collection(collection.name)
                    
                    collection_data = {
                        "name": collection.name,
                        "vectors_count": info.vectors_count,
                        "indexed_vectors_count": info.indexed_vectors_count,
                        "points_count": info.points_count,
                        "segments_count": info.segments_count,
                        "status": info.status.value,
                        "config": {
                            "vector_size": info.config.params.vectors.size,
                            "distance": info.config.params.vectors.distance.value,
                        }
                    }
                    
                    # Add HNSW config if available
                    if hasattr(info.config.params, 'hnsw_config') and info.config.params.hnsw_config:
                        hnsw = info.config.params.hnsw_config
                        collection_data["config"]["hnsw"] = {
                            "m": hnsw.m,
                            "ef_construct": hnsw.ef_construct,
                            "full_scan_threshold": hnsw.full_scan_threshold,
                            "max_indexing_threads": hnsw.max_indexing_threads
                        }
                    
                    collection_info.append(collection_data)
                    
                except Exception as e:
                    print(f"Warning: Could not get details for collection '{collection.name}': {e}")
                    collection_info.append({
                        "name": collection.name,
                        "error": str(e)
                    })
            
            return collection_info
            
        except Exception as e:
            print(f"❌ Failed to list collections: {e}")
            return []
    
    def get_collection_summary(self) -> Dict[str, Any]:
        """Get summary of all collections."""
        collections = self.list_collections()
        
        total_collections = len(collections)
        total_vectors = sum(col.get('vectors_count', 0) or 0 for col in collections)
        total_points = sum(col.get('points_count', 0) or 0 for col in collections)
        
        return {
            "total_collections": total_collections,
            "total_vectors": total_vectors,
            "total_points": total_points,
            "collections": [col['name'] for col in collections]
        }
    
    def close_client(self):
        """Close Qdrant client connection."""
        if self.client:
            self.client.close()
            self.client = None


if __name__ == "__main__":
    # Create and test collections
    collections_mgr = QdrantCollections()
    
    try:
        # Create all initial collections
        results = collections_mgr.create_all_initial_collections()
        
        # Show results
        print("\n" + "=" * 50)
        print("COLLECTION CREATION RESULTS")
        print("=" * 50)
        
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        print(f"✅ Successfully created: {success_count}/{total_count} collections")
        
        for collection_name, success in results.items():
            status = "✅ SUCCESS" if success else "❌ FAILED"
            print(f"  {collection_name}: {status}")
        
        # List all collections
        print("\n" + "=" * 50)
        print("COLLECTION DETAILS")
        print("=" * 50)
        
        collection_list = collections_mgr.list_collections()
        
        for collection in collection_list:
            if 'error' not in collection:
                print(f"\n📦 {collection['name']}")
                print(f"   Status: {collection['status']}")
                print(f"   Vectors: {collection['vectors_count']}")
                print(f"   Points: {collection['points_count']}")
                print(f"   Segments: {collection['segments_count']}")
                print(f"   Vector Size: {collection['config']['vector_size']}")
                print(f"   Distance: {collection['config']['distance']}")
                
                if 'hnsw' in collection['config']:
                    hnsw = collection['config']['hnsw']
                    print(f"   HNSW: m={hnsw['m']}, ef_construct={hnsw['ef_construct']}")
            else:
                print(f"\n❌ {collection['name']}: {collection['error']}")
        
        # Show summary
        print("\n" + "=" * 50)
        print("COLLECTION SUMMARY")
        print("=" * 50)
        
        summary = collections_mgr.get_collection_summary()
        print(f"Total Collections: {summary['total_collections']}")
        print(f"Total Vectors: {summary['total_vectors']}")
        print(f"Total Points: {summary['total_points']}")
        print(f"Collections: {', '.join(summary['collections'])}")
        
        print(f"\n✅ Initial collections setup completed!")
        
    finally:
        collections_mgr.close_client()