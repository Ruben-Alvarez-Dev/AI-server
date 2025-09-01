#!/usr/bin/env python3
"""
Qdrant Vector Operations Testing

Comprehensive testing of Qdrant vector operations: insert, search, update, delete.
Tests all collections with different vector dimensions and verifies performance.
"""

import numpy as np
import time
from typing import List, Dict, Any
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue
from qdrant_config import get_qdrant_client
from qdrant_collections import QdrantCollections


class QdrantTester:
    """Test Qdrant vector operations and performance."""
    
    def __init__(self):
        self.client = get_qdrant_client()
        self.collections_mgr = QdrantCollections()
        self.test_results = {}
    
    def generate_random_vectors(self, dimension: int, count: int = 100) -> np.ndarray:
        """Generate random normalized vectors for testing."""
        vectors = np.random.randn(count, dimension).astype(np.float32)
        # Normalize vectors for cosine similarity
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        return vectors / norms
    
    def test_vector_insertion(self, collection_name: str, vector_size: int) -> Dict[str, Any]:
        """Test vector insertion performance."""
        
        print(f"\n🔧 Testing vector insertion for {collection_name} ({vector_size}D)")
        
        try:
            # Generate test vectors
            test_vectors = self.generate_random_vectors(vector_size, 50)
            
            # Create points with metadata
            points = []
            for i, vector in enumerate(test_vectors):
                points.append(PointStruct(
                    id=i + 1,
                    vector=vector.tolist(),
                    payload={
                        "test_id": i,
                        "content_type": "test_data",
                        "timestamp": time.time(),
                        "category": f"test_category_{i % 5}",
                        "importance": float(i % 10) / 10.0
                    }
                ))
            
            # Insert vectors and measure performance
            start_time = time.time()
            
            operation_info = self.client.upsert(
                collection_name=collection_name,
                points=points
            )
            
            insert_time = time.time() - start_time
            
            return {
                "status": "SUCCESS",
                "vectors_inserted": len(points),
                "insert_time_ms": round(insert_time * 1000, 2),
                "vectors_per_second": round(len(points) / insert_time, 2),
                "operation_id": operation_info.operation_id,
                "vector_dimension": vector_size
            }
            
        except Exception as e:
            return {
                "status": "FAILED",
                "error": str(e),
                "vector_dimension": vector_size
            }
    
    def test_vector_search(self, collection_name: str, vector_size: int) -> Dict[str, Any]:
        """Test vector similarity search."""
        
        print(f"🔍 Testing vector search for {collection_name}")
        
        try:
            # Generate query vector
            query_vector = self.generate_random_vectors(vector_size, 1)[0]
            
            # Test basic search
            start_time = time.time()
            
            search_result = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector.tolist(),
                limit=10,
                with_payload=True,
                with_vectors=False
            )
            
            search_time = time.time() - start_time
            
            # Test filtered search
            filter_start_time = time.time()
            
            filtered_result = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector.tolist(),
                limit=5,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="category",
                            match=MatchValue(value="test_category_1")
                        )
                    ]
                ),
                with_payload=True
            )
            
            filter_search_time = time.time() - filter_start_time
            
            return {
                "status": "SUCCESS",
                "basic_search": {
                    "results_found": len(search_result),
                    "search_time_ms": round(search_time * 1000, 2),
                    "top_score": round(search_result[0].score, 4) if search_result else None
                },
                "filtered_search": {
                    "results_found": len(filtered_result),
                    "search_time_ms": round(filter_search_time * 1000, 2),
                    "top_score": round(filtered_result[0].score, 4) if filtered_result else None
                },
                "vector_dimension": vector_size
            }
            
        except Exception as e:
            return {
                "status": "FAILED",
                "error": str(e),
                "vector_dimension": vector_size
            }
    
    def test_vector_update(self, collection_name: str, vector_size: int) -> Dict[str, Any]:
        """Test vector update operations."""
        
        print(f"✏️ Testing vector updates for {collection_name}")
        
        try:
            # Update some existing points
            update_vectors = self.generate_random_vectors(vector_size, 5)
            
            points = []
            for i, vector in enumerate(update_vectors):
                points.append(PointStruct(
                    id=i + 1,  # Update first 5 points
                    vector=vector.tolist(),
                    payload={
                        "test_id": i,
                        "content_type": "updated_test_data",
                        "timestamp": time.time(),
                        "category": f"updated_category_{i}",
                        "updated": True
                    }
                ))
            
            start_time = time.time()
            
            operation_info = self.client.upsert(
                collection_name=collection_name,
                points=points
            )
            
            update_time = time.time() - start_time
            
            return {
                "status": "SUCCESS",
                "vectors_updated": len(points),
                "update_time_ms": round(update_time * 1000, 2),
                "operation_id": operation_info.operation_id,
                "vector_dimension": vector_size
            }
            
        except Exception as e:
            return {
                "status": "FAILED",
                "error": str(e),
                "vector_dimension": vector_size
            }
    
    def test_vector_delete(self, collection_name: str) -> Dict[str, Any]:
        """Test vector deletion operations."""
        
        print(f"🗑️ Testing vector deletion for {collection_name}")
        
        try:
            # Delete some points by ID
            points_to_delete = [46, 47, 48, 49, 50]  # Delete last 5 points
            
            start_time = time.time()
            
            operation_info = self.client.delete(
                collection_name=collection_name,
                points_selector=points_to_delete
            )
            
            delete_time = time.time() - start_time
            
            return {
                "status": "SUCCESS",
                "vectors_deleted": len(points_to_delete),
                "delete_time_ms": round(delete_time * 1000, 2),
                "operation_id": operation_info.operation_id
            }
            
        except Exception as e:
            return {
                "status": "FAILED",
                "error": str(e)
            }
    
    def test_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get collection statistics after operations."""
        
        try:
            info = self.client.get_collection(collection_name)
            
            return {
                "status": "SUCCESS",
                "vectors_count": info.vectors_count,
                "indexed_vectors_count": info.indexed_vectors_count,
                "points_count": info.points_count,
                "segments_count": info.segments_count,
                "collection_status": info.status.value,
                "disk_data_size": getattr(info, 'disk_data_size', None),
                "ram_data_size": getattr(info, 'ram_data_size', None)
            }
            
        except Exception as e:
            return {
                "status": "FAILED",
                "error": str(e)
            }
    
    def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run all vector operation tests on all collections."""
        
        print("Starting Comprehensive Qdrant Vector Operations Test")
        print("=" * 60)
        
        # Get collection definitions
        collections = self.collections_mgr.COLLECTION_DEFINITIONS
        
        all_results = {}
        
        for collection_name, config in collections.items():
            print(f"\n📦 Testing Collection: {collection_name}")
            print(f"   Vector Size: {config['vector_size']}")
            print(f"   Use Case: {config['use_case']}")
            
            collection_results = {
                "collection_info": config,
                "tests": {}
            }
            
            vector_size = config['vector_size']
            
            # Test 1: Vector Insertion
            collection_results["tests"]["insertion"] = self.test_vector_insertion(
                collection_name, vector_size
            )
            
            # Test 2: Vector Search
            collection_results["tests"]["search"] = self.test_vector_search(
                collection_name, vector_size
            )
            
            # Test 3: Vector Update
            collection_results["tests"]["update"] = self.test_vector_update(
                collection_name, vector_size
            )
            
            # Test 4: Vector Delete
            collection_results["tests"]["delete"] = self.test_vector_delete(
                collection_name
            )
            
            # Test 5: Collection Stats
            collection_results["stats"] = self.test_collection_stats(collection_name)
            
            all_results[collection_name] = collection_results
        
        return all_results
    
    def print_test_summary(self, results: Dict[str, Any]) -> None:
        """Print formatted test results summary."""
        
        print("\n" + "=" * 70)
        print("QDRANT VECTOR OPERATIONS TEST SUMMARY")
        print("=" * 70)
        
        total_tests = 0
        passed_tests = 0
        
        for collection_name, collection_data in results.items():
            print(f"\n📦 {collection_name.upper()}")
            print(f"   Vector Dimension: {collection_data['collection_info']['vector_size']}")
            
            tests = collection_data["tests"]
            stats = collection_data["stats"]
            
            # Test results
            for test_name, test_result in tests.items():
                total_tests += 1
                status_icon = "✅" if test_result["status"] == "SUCCESS" else "❌"
                
                if test_result["status"] == "SUCCESS":
                    passed_tests += 1
                    
                    if test_name == "insertion":
                        print(f"   {status_icon} Insertion: {test_result['vectors_inserted']} vectors in {test_result['insert_time_ms']}ms")
                        print(f"      Performance: {test_result['vectors_per_second']} vectors/sec")
                        
                    elif test_name == "search":
                        basic = test_result["basic_search"]
                        filtered = test_result["filtered_search"]
                        print(f"   {status_icon} Search: {basic['results_found']} results in {basic['search_time_ms']}ms")
                        print(f"      Filtered: {filtered['results_found']} results in {filtered['search_time_ms']}ms")
                        
                    elif test_name == "update":
                        print(f"   {status_icon} Update: {test_result['vectors_updated']} vectors in {test_result['update_time_ms']}ms")
                        
                    elif test_name == "delete":
                        print(f"   {status_icon} Delete: {test_result['vectors_deleted']} vectors in {test_result['delete_time_ms']}ms")
                        
                else:
                    print(f"   {status_icon} {test_name.title()}: {test_result['error']}")
            
            # Collection stats
            if stats["status"] == "SUCCESS":
                print(f"   📊 Final Stats: {stats['points_count']} points, {stats['segments_count']} segments, {stats['collection_status']}")
            
        print(f"\n🎯 OVERALL RESULTS")
        print(f"   Tests Passed: {passed_tests}/{total_tests}")
        print(f"   Success Rate: {round(passed_tests/total_tests*100, 1)}%")
        
        if passed_tests == total_tests:
            print(f"   🎉 All vector operations working perfectly!")
        
        print("=" * 70)
    
    def close_client(self):
        """Close client connections."""
        if self.client:
            self.client.close()
        if self.collections_mgr:
            self.collections_mgr.close_client()


if __name__ == "__main__":
    # Run comprehensive Qdrant tests
    tester = QdrantTester()
    
    try:
        # Run all tests
        results = tester.run_comprehensive_tests()
        
        # Print summary
        tester.print_test_summary(results)
        
        # Save detailed results
        import json
        with open("services/storage/data/qdrant/test_results.json", "w") as f:
            # Convert numpy types to Python types for JSON serialization
            json_results = json.loads(json.dumps(results, default=str))
            json.dump(json_results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: services/storage/data/qdrant/test_results.json")
        print("✅ All Qdrant vector operations tests completed!")
        
    finally:
        tester.close_client()