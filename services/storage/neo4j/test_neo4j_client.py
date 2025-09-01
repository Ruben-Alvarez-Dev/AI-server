#!/usr/bin/env python3
"""
Neo4j Client Testing

Comprehensive testing of Neo4j client operations.
Tests connection, CRUD operations, graph traversal, and performance.
Provides validation that the official Python driver works correctly.
"""

import json
import time
from typing import Dict, Any, List
import logging

from neo4j_client import get_neo4j_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Neo4jClientTester:
    """Test Neo4j client functionality."""
    
    def __init__(self):
        self.client = get_neo4j_client()
        self.test_results = {}
    
    def test_connection(self) -> Dict[str, Any]:
        """Test Neo4j database connection."""
        logger.info("Testing Neo4j connection...")
        
        try:
            start_time = time.time()
            success = self.client.connect()
            connection_time = time.time() - start_time
            
            if success:
                # Get server info
                server_info = self.client.config.get_server_info()
                
                return {
                    "status": "SUCCESS",
                    "connection_time_ms": round(connection_time * 1000, 2),
                    "server_info": server_info
                }
            else:
                return {
                    "status": "FAILED",
                    "error": "Connection test returned False"
                }
                
        except Exception as e:
            return {
                "status": "FAILED",
                "error": str(e)
            }
    
    def test_node_operations(self) -> Dict[str, Any]:
        """Test node creation, finding, and deletion."""
        logger.info("Testing node operations...")
        
        try:
            # Create test nodes
            start_time = time.time()
            
            test_nodes = []
            for i in range(10):
                node = self.client.create_node(
                    labels=["TestNode", "Person"],
                    properties={
                        "id": i,
                        "name": f"Test User {i}",
                        "email": f"user{i}@test.com",
                        "created_at": time.time(),
                        "category": f"category_{i % 3}"
                    }
                )
                test_nodes.append(node)
            
            creation_time = time.time() - start_time
            
            # Find nodes
            start_time = time.time()
            found_nodes = self.client.find_nodes("TestNode")
            search_time = time.time() - start_time
            
            # Find with filter
            start_time = time.time()
            filtered_nodes = self.client.find_nodes(
                "TestNode", 
                properties={"category": "category_1"}
            )
            filter_time = time.time() - start_time
            
            return {
                "status": "SUCCESS",
                "nodes_created": len(test_nodes),
                "creation_time_ms": round(creation_time * 1000, 2),
                "nodes_found": len(found_nodes),
                "search_time_ms": round(search_time * 1000, 2),
                "filtered_nodes_found": len(filtered_nodes),
                "filter_time_ms": round(filter_time * 1000, 2)
            }
            
        except Exception as e:
            return {
                "status": "FAILED",
                "error": str(e)
            }
    
    def test_relationship_operations(self) -> Dict[str, Any]:
        """Test relationship creation and querying."""
        logger.info("Testing relationship operations...")
        
        try:
            # Get existing test nodes
            nodes = self.client.find_nodes("TestNode", limit=5)
            if len(nodes) < 2:
                return {
                    "status": "FAILED",
                    "error": "Not enough test nodes for relationship testing"
                }
            
            # Create relationships
            start_time = time.time()
            relationships = []
            
            for i in range(len(nodes) - 1):
                from_node_id = nodes[i]["n"].element_id.split(":")[-1]
                to_node_id = nodes[i + 1]["n"].element_id.split(":")[-1]
                
                rel = self.client.create_relationship(
                    from_node_id=int(from_node_id),
                    to_node_id=int(to_node_id),
                    relationship_type="KNOWS",
                    properties={
                        "since": time.time(),
                        "strength": i + 1,
                        "type": "friendship"
                    }
                )
                relationships.append(rel)
            
            creation_time = time.time() - start_time
            
            # Find relationships
            start_time = time.time()
            found_rels = self.client.find_relationships("KNOWS")
            search_time = time.time() - start_time
            
            return {
                "status": "SUCCESS",
                "relationships_created": len(relationships),
                "creation_time_ms": round(creation_time * 1000, 2),
                "relationships_found": len(found_rels),
                "search_time_ms": round(search_time * 1000, 2)
            }
            
        except Exception as e:
            return {
                "status": "FAILED",
                "error": str(e)
            }
    
    def test_graph_traversal(self) -> Dict[str, Any]:
        """Test graph traversal operations."""
        logger.info("Testing graph traversal...")
        
        try:
            # Get a test node
            nodes = self.client.find_nodes("TestNode", limit=1)
            if not nodes:
                return {
                    "status": "FAILED",
                    "error": "No test nodes found for traversal"
                }
            
            start_node_id = int(nodes[0]["n"].element_id.split(":")[-1])
            
            # Traverse graph
            start_time = time.time()
            paths = self.client.traverse_graph(
                start_node_id=start_node_id,
                relationship_types=["KNOWS"],
                direction="BOTH",
                max_depth=3
            )
            traversal_time = time.time() - start_time
            
            return {
                "status": "SUCCESS",
                "start_node_id": start_node_id,
                "paths_found": len(paths),
                "traversal_time_ms": round(traversal_time * 1000, 2)
            }
            
        except Exception as e:
            return {
                "status": "FAILED",
                "error": str(e)
            }
    
    def test_cypher_queries(self) -> Dict[str, Any]:
        """Test raw Cypher query execution."""
        logger.info("Testing Cypher queries...")
        
        try:
            # Simple query
            start_time = time.time()
            result1 = self.client.execute_query("RETURN 'Hello Neo4j' as greeting")
            simple_time = time.time() - start_time
            
            # Complex query with parameters
            start_time = time.time()
            result2 = self.client.execute_query(
                """
                MATCH (n:TestNode)
                WHERE n.category = $category
                RETURN count(n) as node_count, $category as category
                """,
                parameters={"category": "category_1"}
            )
            complex_time = time.time() - start_time
            
            # Aggregation query
            start_time = time.time()
            result3 = self.client.execute_query(
                """
                MATCH (n:TestNode)-[r:KNOWS]->(m:TestNode)
                RETURN n.category as from_category, 
                       m.category as to_category,
                       count(r) as relationship_count
                ORDER BY relationship_count DESC
                """
            )
            aggregation_time = time.time() - start_time
            
            return {
                "status": "SUCCESS",
                "simple_query": {
                    "result": result1[0]["greeting"] if result1 else None,
                    "time_ms": round(simple_time * 1000, 2)
                },
                "complex_query": {
                    "result": dict(result2[0]) if result2 else None,
                    "time_ms": round(complex_time * 1000, 2)
                },
                "aggregation_query": {
                    "results_count": len(result3),
                    "time_ms": round(aggregation_time * 1000, 2)
                }
            }
            
        except Exception as e:
            return {
                "status": "FAILED",
                "error": str(e)
            }
    
    def test_database_stats(self) -> Dict[str, Any]:
        """Test database statistics retrieval."""
        logger.info("Testing database statistics...")
        
        try:
            start_time = time.time()
            stats = self.client.get_database_stats()
            stats_time = time.time() - start_time
            
            return {
                "status": "SUCCESS",
                "stats": stats,
                "retrieval_time_ms": round(stats_time * 1000, 2)
            }
            
        except Exception as e:
            return {
                "status": "FAILED",
                "error": str(e)
            }
    
    def cleanup_test_data(self) -> Dict[str, Any]:
        """Clean up test data."""
        logger.info("Cleaning up test data...")
        
        try:
            start_time = time.time()
            
            # Delete test nodes and relationships
            self.client.execute_write_query(
                "MATCH (n:TestNode) DETACH DELETE n"
            )
            
            cleanup_time = time.time() - start_time
            
            return {
                "status": "SUCCESS",
                "cleanup_time_ms": round(cleanup_time * 1000, 2)
            }
            
        except Exception as e:
            return {
                "status": "FAILED",
                "error": str(e)
            }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all Neo4j client tests."""
        logger.info("Starting comprehensive Neo4j client tests")
        
        all_results = {}
        
        # Test 1: Connection
        all_results["connection"] = self.test_connection()
        
        if all_results["connection"]["status"] == "SUCCESS":
            # Test 2: Node operations
            all_results["node_operations"] = self.test_node_operations()
            
            # Test 3: Relationship operations
            all_results["relationship_operations"] = self.test_relationship_operations()
            
            # Test 4: Graph traversal
            all_results["graph_traversal"] = self.test_graph_traversal()
            
            # Test 5: Cypher queries
            all_results["cypher_queries"] = self.test_cypher_queries()
            
            # Test 6: Database stats
            all_results["database_stats"] = self.test_database_stats()
            
            # Cleanup
            all_results["cleanup"] = self.cleanup_test_data()
        
        return all_results
    
    def print_test_summary(self, results: Dict[str, Any]) -> None:
        """Print formatted test results summary."""
        print("\n" + "="*70)
        print("NEO4J CLIENT TEST SUMMARY")
        print("="*70)
        
        total_tests = len(results)
        passed_tests = sum(1 for test in results.values() if test.get("status") == "SUCCESS")
        
        for test_name, test_result in results.items():
            status_icon = "✅" if test_result["status"] == "SUCCESS" else "❌"
            print(f"{status_icon} {test_name.replace('_', ' ').title()}")
            
            if test_result["status"] == "SUCCESS":
                if "connection_time_ms" in test_result:
                    print(f"    Connection time: {test_result['connection_time_ms']}ms")
                
                if "nodes_created" in test_result:
                    print(f"    Nodes created: {test_result['nodes_created']}")
                    print(f"    Creation time: {test_result['creation_time_ms']}ms")
                
                if "relationships_created" in test_result:
                    print(f"    Relationships created: {test_result['relationships_created']}")
                
                if "stats" in test_result:
                    stats = test_result["stats"]
                    print(f"    Total nodes: {stats.get('nodes', 0)}")
                    print(f"    Total relationships: {stats.get('relationships', 0)}")
                    
            else:
                print(f"    Error: {test_result.get('error', 'Unknown error')}")
        
        print(f"\n🎯 OVERALL RESULTS")
        print(f"   Tests Passed: {passed_tests}/{total_tests}")
        print(f"   Success Rate: {round(passed_tests/total_tests*100, 1)}%")
        
        if passed_tests == total_tests:
            print(f"   🎉 All Neo4j client operations working perfectly!")
        
        print("="*70)


if __name__ == "__main__":
    # Run comprehensive Neo4j client tests
    tester = Neo4jClientTester()
    
    try:
        # Run all tests
        results = tester.run_all_tests()
        
        # Print summary
        tester.print_test_summary(results)
        
        # Save detailed results
        with open("/Users/server/Code/AI-projects/AI-server/services/storage/data/neo4j/client_test_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed results saved to: services/storage/data/neo4j/client_test_results.json")
        print("✅ Neo4j client tests completed!")
        
    except Exception as e:
        print(f"❌ Neo4j client testing failed: {e}")
        
    finally:
        # Always disconnect
        tester.client.disconnect()