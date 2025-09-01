#!/usr/bin/env python3
"""
Neo4j Cypher Query Testing System

Comprehensive testing of Cypher queries for AI server graph operations.
Tests query performance, optimization techniques, and validates functionality
for expected query patterns in production workloads.
"""

import logging
import time
import json
import statistics
from typing import Dict, List, Any, Optional, Tuple
from neo4j_client import get_neo4j_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CypherQueryTester:
    """Test and benchmark Cypher queries for Neo4j graph operations."""
    
    def __init__(self):
        self.client = get_neo4j_client()
        
        # Test queries for AI server operations
        self.test_queries = {
            # Basic CRUD operations
            "node_creation": {
                "query": """
                    CREATE (n:TestEntity {
                        id: $id,
                        name: $name,
                        type: 'test',
                        created_at: timestamp(),
                        properties: $properties
                    })
                    RETURN n.id as created_id
                """,
                "params": {
                    "id": "test_entity_1",
                    "name": "Test Entity 1",
                    "properties": {"category": "test", "score": 0.85}
                },
                "description": "Basic node creation with properties",
                "expected_results": 1
            },
            
            "node_lookup_by_id": {
                "query": """
                    MATCH (n:Entity {id: $entity_id})
                    RETURN n.id, n.name, n.type, n.created_at
                """,
                "params": {"entity_id": "ai-server-system"},
                "description": "Fast node lookup by indexed ID",
                "expected_results": 1
            },
            
            "node_filtering_by_type": {
                "query": """
                    MATCH (n:Entity)
                    WHERE n.type = $type
                    RETURN n.id, n.name, n.type
                    ORDER BY n.name
                """,
                "params": {"type": "system"},
                "description": "Node filtering with indexed type field",
                "expected_results": ">= 1"
            },
            
            # Relationship operations
            "relationship_creation": {
                "query": """
                    MATCH (a:Entity {id: $from_id})
                    MATCH (b:Entity {id: $to_id})
                    CREATE (a)-[r:TEST_RELATION {
                        created_at: timestamp(),
                        strength: $strength,
                        metadata: $metadata
                    }]->(b)
                    RETURN r.strength as relationship_strength
                """,
                "params": {
                    "from_id": "ai-server-system",
                    "to_id": "memory-system", 
                    "strength": 0.95,
                    "metadata": {"test": True, "temporary": True}
                },
                "description": "Relationship creation between existing nodes",
                "expected_results": 1
            },
            
            "relationship_traversal": {
                "query": """
                    MATCH (a:System)-[r:MANAGES]->(b)
                    RETURN a.name as from_node, 
                           type(r) as relationship_type,
                           b.name as to_node,
                           r.strength as strength
                    ORDER BY r.strength DESC
                """,
                "params": {},
                "description": "Basic relationship traversal with ordering",
                "expected_results": ">= 1"
            },
            
            # Complex graph operations
            "multi_hop_traversal": {
                "query": """
                    MATCH path = (start:System {id: 'ai-server-system'})-[*1..3]->(end)
                    RETURN start.name as start_node,
                           length(path) as hops,
                           end.name as end_node,
                           [rel in relationships(path) | type(rel)] as relationship_types
                    ORDER BY length(path), end.name
                """,
                "params": {},
                "description": "Multi-hop graph traversal with path analysis",
                "expected_results": ">= 1"
            },
            
            "weighted_traversal": {
                "query": """
                    MATCH (start)-[r]->(end)
                    WHERE r.strength > $min_strength
                    RETURN start.name, end.name, r.strength, type(r)
                    ORDER BY r.strength DESC
                    LIMIT $limit
                """,
                "params": {"min_strength": 0.7, "limit": 10},
                "description": "Weighted relationship traversal with filtering",
                "expected_results": ">= 0"
            },
            
            # Aggregation and analytical queries
            "node_statistics": {
                "query": """
                    MATCH (n)
                    RETURN labels(n) as node_labels,
                           count(n) as node_count
                    ORDER BY node_count DESC
                """,
                "params": {},
                "description": "Node count statistics by label",
                "expected_results": ">= 1"
            },
            
            "relationship_statistics": {
                "query": """
                    MATCH ()-[r]->()
                    RETURN type(r) as relationship_type,
                           count(r) as count,
                           avg(r.strength) as avg_strength,
                           min(r.strength) as min_strength,
                           max(r.strength) as max_strength
                    ORDER BY count DESC
                """,
                "params": {},
                "description": "Relationship statistics with aggregations",
                "expected_results": ">= 1"
            },
            
            # Full-text search operations
            "fulltext_entity_search": {
                "query": """
                    CALL db.index.fulltext.queryNodes('entity_name_fulltext', $search_term)
                    YIELD node, score
                    RETURN node.name as name, 
                           node.description as description,
                           score
                    ORDER BY score DESC
                    LIMIT $limit
                """,
                "params": {"search_term": "System", "limit": 5},
                "description": "Full-text search across entity names and descriptions",
                "expected_results": ">= 0"
            },
            
            # Advanced analytical queries
            "centrality_analysis": {
                "query": """
                    MATCH (n)
                    OPTIONAL MATCH (n)-[r]-()
                    RETURN n.name as node_name,
                           count(r) as degree_centrality,
                           labels(n) as labels
                    ORDER BY degree_centrality DESC
                    LIMIT $limit
                """,
                "params": {"limit": 10},
                "description": "Simple degree centrality analysis",
                "expected_results": ">= 1"
            },
            
            "temporal_analysis": {
                "query": """
                    MATCH (n)
                    WHERE n.created_at IS NOT NULL
                    RETURN datetime({epochSeconds: toInteger(n.created_at)}) as creation_date,
                           labels(n) as node_type,
                           count(n) as nodes_created
                    ORDER BY creation_date DESC
                """,
                "params": {},
                "description": "Temporal analysis of node creation patterns",
                "expected_results": ">= 0"
            },
            
            # Performance stress tests
            "complex_join_query": {
                "query": """
                    MATCH (a:System)
                    MATCH (b:System)
                    WHERE a.id <> b.id
                    OPTIONAL MATCH path = (a)-[*1..2]-(b)
                    RETURN a.name as node_a,
                           b.name as node_b,
                           CASE WHEN path IS NULL THEN 0 ELSE length(path) END as connection_distance
                    ORDER BY connection_distance, a.name, b.name
                """,
                "params": {},
                "description": "Complex join query with optional path matching",
                "expected_results": ">= 0"
            }
        }
        
        # Cleanup queries to run after testing
        self.cleanup_queries = [
            "MATCH ()-[r:TEST_RELATION]->() DELETE r",
            "MATCH (n:TestEntity) DELETE n"
        ]
    
    def connect(self) -> bool:
        """Connect to Neo4j database."""
        return self.client.connect()
    
    def disconnect(self) -> None:
        """Disconnect from Neo4j database."""
        self.client.disconnect()
    
    def execute_query_with_timing(self, 
                                  query: str, 
                                  params: Dict[str, Any],
                                  runs: int = 3) -> Dict[str, Any]:
        """Execute query multiple times and measure performance."""
        
        execution_times = []
        results = None
        error = None
        
        for run in range(runs):
            try:
                start_time = time.time()
                result = self.client.execute_query(query, params)
                execution_time = time.time() - start_time
                
                execution_times.append(execution_time * 1000)  # Convert to ms
                
                if results is None:
                    results = result
                    
            except Exception as e:
                error = str(e)
                break
        
        if error:
            return {
                "status": "ERROR",
                "error": error,
                "execution_times_ms": []
            }
        
        return {
            "status": "SUCCESS",
            "results_count": len(results) if results else 0,
            "execution_times_ms": execution_times,
            "avg_time_ms": round(statistics.mean(execution_times), 2),
            "min_time_ms": round(min(execution_times), 2),
            "max_time_ms": round(max(execution_times), 2),
            "std_dev_ms": round(statistics.stdev(execution_times), 2) if len(execution_times) > 1 else 0
        }
    
    def validate_query_results(self, 
                             result: Dict[str, Any], 
                             expected_results: Any) -> bool:
        """Validate query results meet expectations."""
        
        if result["status"] != "SUCCESS":
            return False
        
        results_count = result["results_count"]
        
        if isinstance(expected_results, int):
            return results_count == expected_results
        elif isinstance(expected_results, str) and expected_results.startswith(">="):
            min_expected = int(expected_results.split(">=")[1].strip())
            return results_count >= min_expected
        
        return True
    
    def run_single_query_test(self, 
                            query_name: str, 
                            query_info: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single query test with performance measurement."""
        
        logger.info(f"Testing query: {query_name}")
        
        query = query_info["query"]
        params = query_info["params"]
        description = query_info["description"]
        expected_results = query_info["expected_results"]
        
        # Execute query with timing
        result = self.execute_query_with_timing(query, params)
        
        # Validate results
        validation_passed = self.validate_query_results(result, expected_results)
        
        test_result = {
            "query_name": query_name,
            "description": description,
            "status": result["status"],
            "validation_passed": validation_passed,
            "performance": {
                "avg_time_ms": result.get("avg_time_ms", 0),
                "min_time_ms": result.get("min_time_ms", 0),
                "max_time_ms": result.get("max_time_ms", 0),
                "std_dev_ms": result.get("std_dev_ms", 0)
            },
            "results_count": result.get("results_count", 0),
            "expected_results": expected_results
        }
        
        if result["status"] == "ERROR":
            test_result["error"] = result["error"]
        
        return test_result
    
    def run_all_query_tests(self) -> Dict[str, Any]:
        """Run all Cypher query tests."""
        
        logger.info("Starting comprehensive Cypher query tests...")
        
        test_results = {
            "timestamp": time.time(),
            "total_queries": len(self.test_queries),
            "successful_queries": 0,
            "failed_queries": 0,
            "validation_passed": 0,
            "validation_failed": 0,
            "query_results": {},
            "performance_summary": {
                "fastest_query": None,
                "slowest_query": None,
                "average_query_time_ms": 0
            }
        }
        
        all_times = []
        
        for query_name, query_info in self.test_queries.items():
            try:
                result = self.run_single_query_test(query_name, query_info)
                test_results["query_results"][query_name] = result
                
                if result["status"] == "SUCCESS":
                    test_results["successful_queries"] += 1
                    all_times.append(result["performance"]["avg_time_ms"])
                else:
                    test_results["failed_queries"] += 1
                
                if result["validation_passed"]:
                    test_results["validation_passed"] += 1
                else:
                    test_results["validation_failed"] += 1
                    
            except Exception as e:
                logger.error(f"Test execution failed for {query_name}: {e}")
                test_results["failed_queries"] += 1
        
        # Calculate performance summary
        if all_times:
            test_results["performance_summary"]["average_query_time_ms"] = round(statistics.mean(all_times), 2)
            
            fastest_time = min(all_times)
            slowest_time = max(all_times)
            
            for query_name, result in test_results["query_results"].items():
                if result["status"] == "SUCCESS":
                    if result["performance"]["avg_time_ms"] == fastest_time:
                        test_results["performance_summary"]["fastest_query"] = {
                            "name": query_name,
                            "time_ms": fastest_time
                        }
                    if result["performance"]["avg_time_ms"] == slowest_time:
                        test_results["performance_summary"]["slowest_query"] = {
                            "name": query_name,
                            "time_ms": slowest_time
                        }
        
        return test_results
    
    def cleanup_test_data(self) -> Dict[str, Any]:
        """Clean up test data created during query testing."""
        
        logger.info("Cleaning up test data...")
        
        cleanup_results = {
            "status": "SUCCESS",
            "cleaned_items": 0,
            "errors": []
        }
        
        for cleanup_query in self.cleanup_queries:
            try:
                result = self.client.execute_write_query(cleanup_query)
                cleanup_results["cleaned_items"] += 1
            except Exception as e:
                cleanup_results["errors"].append({
                    "query": cleanup_query,
                    "error": str(e)
                })
        
        if cleanup_results["errors"]:
            cleanup_results["status"] = "PARTIAL"
        
        return cleanup_results
    
    def generate_performance_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed performance analysis report."""
        
        report = {
            "overall_performance": "excellent" if results["performance_summary"]["average_query_time_ms"] < 5 else
                                  "good" if results["performance_summary"]["average_query_time_ms"] < 20 else
                                  "fair" if results["performance_summary"]["average_query_time_ms"] < 100 else "needs_optimization",
            "success_rate": round((results["successful_queries"] / results["total_queries"]) * 100, 1),
            "validation_rate": round((results["validation_passed"] / results["total_queries"]) * 100, 1),
            "performance_analysis": {},
            "recommendations": []
        }
        
        # Analyze query performance by category
        basic_queries = ["node_creation", "node_lookup_by_id", "node_filtering_by_type"]
        relationship_queries = ["relationship_creation", "relationship_traversal"]
        complex_queries = ["multi_hop_traversal", "weighted_traversal", "complex_join_query"]
        
        for category, query_list in [
            ("basic", basic_queries),
            ("relationship", relationship_queries), 
            ("complex", complex_queries)
        ]:
            times = [results["query_results"][q]["performance"]["avg_time_ms"] 
                    for q in query_list 
                    if q in results["query_results"] and results["query_results"][q]["status"] == "SUCCESS"]
            
            if times:
                report["performance_analysis"][category] = {
                    "avg_time_ms": round(statistics.mean(times), 2),
                    "query_count": len(times)
                }
        
        # Generate recommendations
        if results["failed_queries"] > 0:
            report["recommendations"].append("Some queries failed - investigate error causes")
        
        if results["performance_summary"]["average_query_time_ms"] > 50:
            report["recommendations"].append("Query performance could be improved - consider index optimization")
        
        if results["validation_failed"] > 0:
            report["recommendations"].append("Some result validations failed - review expected results")
        
        return report


def main():
    """Main function for Cypher query testing."""
    
    tester = CypherQueryTester()
    
    print("="*70)
    print("NEO4J CYPHER QUERY TESTING SYSTEM")
    print("="*70)
    
    try:
        # Connect to database
        if not tester.connect():
            print("❌ Failed to connect to Neo4j database")
            return False
        
        print("✅ Connected to Neo4j database")
        
        # Run all query tests
        print(f"\n🔧 Running {len(tester.test_queries)} Cypher query tests...")
        results = tester.run_all_query_tests()
        
        # Generate performance report
        performance_report = tester.generate_performance_report(results)
        
        # Print summary
        print(f"\nQuery Test Results:")
        print(f"  Total queries: {results['total_queries']}")
        print(f"  Successful: {results['successful_queries']}")
        print(f"  Failed: {results['failed_queries']}")
        print(f"  Success rate: {performance_report['success_rate']}%")
        print(f"  Validation rate: {performance_report['validation_rate']}%")
        
        print(f"\nPerformance Summary:")
        print(f"  Average query time: {results['performance_summary']['average_query_time_ms']}ms")
        print(f"  Overall performance: {performance_report['overall_performance']}")
        
        if results["performance_summary"]["fastest_query"]:
            fastest = results["performance_summary"]["fastest_query"]
            print(f"  Fastest query: {fastest['name']} ({fastest['time_ms']}ms)")
            
        if results["performance_summary"]["slowest_query"]:
            slowest = results["performance_summary"]["slowest_query"]
            print(f"  Slowest query: {slowest['name']} ({slowest['time_ms']}ms)")
        
        # Performance analysis by category
        if performance_report["performance_analysis"]:
            print(f"\nPerformance by Category:")
            for category, analysis in performance_report["performance_analysis"].items():
                print(f"  {category.title()} queries: {analysis['avg_time_ms']}ms average ({analysis['query_count']} queries)")
        
        # Recommendations
        if performance_report["recommendations"]:
            print(f"\nRecommendations:")
            for rec in performance_report["recommendations"]:
                print(f"  • {rec}")
        
        # Clean up test data
        print(f"\n🧹 Cleaning up test data...")
        cleanup_result = tester.cleanup_test_data()
        if cleanup_result["status"] == "SUCCESS":
            print(f"✅ Test data cleaned successfully")
        else:
            print(f"⚠️ Partial cleanup completed with {len(cleanup_result['errors'])} errors")
        
        # Save detailed results
        full_results = {
            "test_results": results,
            "performance_report": performance_report,
            "cleanup_result": cleanup_result
        }
        
        report_path = "/Users/server/Code/AI-projects/AI-server/services/storage/data/neo4j/cypher_test_results.json"
        with open(report_path, 'w') as f:
            json.dump(full_results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed results saved to: {report_path}")
        
        if results["successful_queries"] == results["total_queries"]:
            print("✅ All Cypher query tests completed successfully!")
            return True
        else:
            print("⚠️ Some query tests failed - review detailed results")
            return False
            
    except Exception as e:
        print(f"❌ Query testing failed: {e}")
        return False
        
    finally:
        tester.disconnect()
        print("="*70)


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)