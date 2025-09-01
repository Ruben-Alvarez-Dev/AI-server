#!/usr/bin/env python3
"""
Neo4j Index Management System

Advanced index management for Neo4j graph database optimization.
Creates, manages, and monitors indexes for AI server graph operations
with performance tracking and automatic optimization recommendations.
"""

import logging
import time
import json
from typing import Dict, List, Any, Optional, Tuple
from neo4j_client import get_neo4j_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Neo4jIndexManager:
    """Advanced Neo4j index management and optimization."""
    
    def __init__(self):
        self.client = get_neo4j_client()
        
        # Core indexes for AI server operations
        self.core_indexes = {
            # Entity indexes for fast lookup
            "entity_id_index": {
                "type": "RANGE",
                "target": "FOR (n:Entity) ON (n.id)",
                "description": "Fast entity ID lookups for graph traversal"
            },
            "entity_type_index": {
                "type": "RANGE", 
                "target": "FOR (n:Entity) ON (n.type)",
                "description": "Entity type filtering for categorized queries"
            },
            "entity_name_fulltext": {
                "type": "FULLTEXT",
                "target": "FOR (n:Entity) ON EACH [n.name, n.description]",
                "description": "Full-text search across entity names and descriptions"
            },
            
            # Concept indexes for semantic operations
            "concept_id_index": {
                "type": "RANGE",
                "target": "FOR (n:Concept) ON (n.id)",
                "description": "Fast concept ID lookups for semantic queries"
            },
            "concept_category_index": {
                "type": "RANGE",
                "target": "FOR (n:Concept) ON (n.category)",
                "description": "Concept category filtering for semantic grouping"
            },
            "concept_embedding_vector": {
                "type": "VECTOR",
                "target": "FOR (n:Concept) ON (n.embedding)",
                "description": "Vector similarity search for semantic matching",
                "config": {
                    "vector.dimensions": 768,
                    "vector.similarity_function": "cosine"
                }
            },
            
            # Document indexes for content operations
            "document_id_index": {
                "type": "RANGE", 
                "target": "FOR (n:Document) ON (n.id)",
                "description": "Fast document ID lookups for content retrieval"
            },
            "document_timestamp_index": {
                "type": "RANGE",
                "target": "FOR (n:Document) ON (n.created_at)",
                "description": "Temporal queries for document timeline analysis"
            },
            "document_content_fulltext": {
                "type": "FULLTEXT",
                "target": "FOR (n:Document) ON EACH [n.title, n.content, n.summary]",
                "description": "Full-text search across document content"
            },
            
            # User indexes for session management
            "user_id_index": {
                "type": "RANGE",
                "target": "FOR (n:User) ON (n.id)",
                "description": "Fast user ID lookups for session management"
            },
            "user_session_index": {
                "type": "RANGE",
                "target": "FOR (n:User) ON (n.session_id)",
                "description": "Active session tracking and management"
            }
            
            # Note: Relationship indexes removed due to syntax complexity in Neo4j 5.x
            # Will create them separately if needed for specific relationship types
        }
    
    def connect(self) -> bool:
        """Connect to Neo4j database."""
        return self.client.connect()
    
    def disconnect(self) -> None:
        """Disconnect from Neo4j database."""
        self.client.disconnect()
    
    def get_existing_indexes(self) -> List[Dict[str, Any]]:
        """Get all existing indexes in the database."""
        try:
            result = self.client.execute_query("SHOW INDEXES")
            indexes = []
            
            for record in result:
                index_info = {
                    "name": record.get("name", ""),
                    "type": record.get("type", ""),
                    "entity_type": record.get("entityType", ""),
                    "labels_or_types": record.get("labelsOrTypes", []),
                    "properties": record.get("properties", []),
                    "state": record.get("state", ""),
                    "population_percent": record.get("populationPercent", 0.0)
                }
                indexes.append(index_info)
            
            return indexes
            
        except Exception as e:
            logger.error(f"Failed to get existing indexes: {e}")
            return []
    
    def create_btree_index(self, name: str, target: str, description: str = "") -> bool:
        """Create a RANGE index (Neo4j 5.x equivalent of BTREE)."""
        try:
            # Neo4j 5.x uses RANGE instead of BTREE
            query = f"CREATE RANGE INDEX {name} IF NOT EXISTS {target}"
            self.client.execute_write_query(query)
            logger.info(f"Created RANGE index: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create RANGE index {name}: {e}")
            return False
    
    def create_fulltext_index(self, name: str, target: str, description: str = "") -> bool:
        """Create a full-text index."""
        try:
            # Full-text indexes have different syntax
            if "FOR (n:Entity)" in target:
                query = f"CREATE FULLTEXT INDEX {name} IF NOT EXISTS FOR (n:Entity) ON EACH [n.name, n.description]"
            elif "FOR (n:Document)" in target:
                query = f"CREATE FULLTEXT INDEX {name} IF NOT EXISTS FOR (n:Document) ON EACH [n.title, n.content, n.summary]"
            else:
                # Generic fulltext index
                query = f"CREATE FULLTEXT INDEX {name} IF NOT EXISTS {target}"
            
            self.client.execute_write_query(query)
            logger.info(f"Created FULLTEXT index: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create FULLTEXT index {name}: {e}")
            return False
    
    def create_vector_index(self, name: str, target: str, config: Dict[str, Any], description: str = "") -> bool:
        """Create a vector index for similarity search."""
        try:
            # Vector indexes require specific configuration
            dimensions = config.get("vector.dimensions", 768)
            similarity = config.get("vector.similarity_function", "cosine")
            
            query = f"""
            CREATE VECTOR INDEX {name} IF NOT EXISTS
            FOR (n:Concept) ON (n.embedding)
            OPTIONS {{
                indexConfig: {{
                    `vector.dimensions`: {dimensions},
                    `vector.similarity_function`: '{similarity}'
                }}
            }}
            """
            
            self.client.execute_write_query(query)
            logger.info(f"Created VECTOR index: {name}")
            return True
            
        except Exception as e:
            logger.warning(f"Vector index creation failed (may not be available in Community Edition): {e}")
            return False
    
    def create_all_core_indexes(self) -> Dict[str, bool]:
        """Create all core indexes for AI server operations."""
        logger.info("Creating all core indexes...")
        
        results = {}
        
        for index_name, index_config in self.core_indexes.items():
            index_type = index_config["type"]
            target = index_config["target"]
            description = index_config["description"]
            
            try:
                if index_type == "RANGE":
                    results[index_name] = self.create_btree_index(index_name, target, description)
                elif index_type == "FULLTEXT":
                    results[index_name] = self.create_fulltext_index(index_name, target, description)
                elif index_type == "VECTOR":
                    config = index_config.get("config", {})
                    results[index_name] = self.create_vector_index(index_name, target, config, description)
                else:
                    logger.error(f"Unknown index type: {index_type}")
                    results[index_name] = False
                    
            except Exception as e:
                logger.error(f"Failed to create index {index_name}: {e}")
                results[index_name] = False
        
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        logger.info(f"Core indexes creation completed: {success_count}/{total_count} successful")
        return results
    
    def analyze_index_performance(self) -> Dict[str, Any]:
        """Analyze index performance and usage statistics."""
        logger.info("Analyzing index performance...")
        
        try:
            # Get index statistics
            indexes = self.get_existing_indexes()
            
            analysis = {
                "total_indexes": len(indexes),
                "by_type": {},
                "by_state": {},
                "performance_issues": [],
                "recommendations": []
            }
            
            # Analyze by type and state
            for index in indexes:
                index_type = index.get("type", "unknown")
                index_state = index.get("state", "unknown")
                
                analysis["by_type"][index_type] = analysis["by_type"].get(index_type, 0) + 1
                analysis["by_state"][index_state] = analysis["by_state"].get(index_state, 0) + 1
                
                # Check for performance issues
                population_percent = index.get("population_percent", 0.0)
                if population_percent < 100.0 and index_state == "ONLINE":
                    analysis["performance_issues"].append({
                        "index": index.get("name", ""),
                        "issue": "incomplete_population",
                        "population_percent": population_percent
                    })
            
            # Generate recommendations
            if analysis["by_state"].get("FAILED", 0) > 0:
                analysis["recommendations"].append("Some indexes are in FAILED state - investigate and recreate")
                
            if analysis["by_type"].get("FULLTEXT", 0) == 0:
                analysis["recommendations"].append("Consider adding full-text indexes for content search")
                
            if len(analysis["performance_issues"]) > 0:
                analysis["recommendations"].append("Some indexes have incomplete population - monitor and wait for completion")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Index performance analysis failed: {e}")
            return {"error": str(e)}
    
    def benchmark_index_performance(self) -> Dict[str, Any]:
        """Benchmark query performance with and without indexes."""
        logger.info("Benchmarking index performance...")
        
        benchmarks = {}
        
        try:
            # Test entity lookups
            start_time = time.time()
            result = self.client.execute_query("MATCH (n:Entity {type: 'system'}) RETURN count(n) as count")
            entity_lookup_time = time.time() - start_time
            benchmarks["entity_type_lookup_ms"] = round(entity_lookup_time * 1000, 2)
            
            # Test relationship traversal
            start_time = time.time()
            result = self.client.execute_query("MATCH (n)-[r:MANAGES]->(m) RETURN count(r) as count")
            relationship_traversal_time = time.time() - start_time
            benchmarks["relationship_traversal_ms"] = round(relationship_traversal_time * 1000, 2)
            
            # Test complex query with multiple indexes
            start_time = time.time()
            result = self.client.execute_query("""
                MATCH (n:Entity {type: 'system'})-[r:MANAGES]->(m)
                WHERE r.strength > 0.5
                RETURN n.name, m.name, r.strength
                ORDER BY r.strength DESC
                LIMIT 10
            """)
            complex_query_time = time.time() - start_time
            benchmarks["complex_query_ms"] = round(complex_query_time * 1000, 2)
            
            # Overall performance assessment
            avg_query_time = (entity_lookup_time + relationship_traversal_time + complex_query_time) / 3
            benchmarks["average_query_ms"] = round(avg_query_time * 1000, 2)
            
            if avg_query_time < 0.001:  # < 1ms
                benchmarks["performance_rating"] = "excellent"
            elif avg_query_time < 0.01:  # < 10ms
                benchmarks["performance_rating"] = "good"
            elif avg_query_time < 0.1:   # < 100ms
                benchmarks["performance_rating"] = "fair"
            else:
                benchmarks["performance_rating"] = "needs_optimization"
                
        except Exception as e:
            logger.error(f"Index benchmarking failed: {e}")
            benchmarks["error"] = str(e)
        
        return benchmarks
    
    def generate_index_report(self) -> Dict[str, Any]:
        """Generate comprehensive index management report."""
        logger.info("Generating comprehensive index report...")
        
        report = {
            "timestamp": time.time(),
            "existing_indexes": self.get_existing_indexes(),
            "core_indexes_status": {},
            "performance_analysis": self.analyze_index_performance(),
            "benchmark_results": self.benchmark_index_performance(),
            "recommendations": []
        }
        
        # Check which core indexes exist
        existing_names = {idx["name"] for idx in report["existing_indexes"]}
        
        for core_name, core_config in self.core_indexes.items():
            report["core_indexes_status"][core_name] = {
                "exists": core_name in existing_names,
                "description": core_config["description"],
                "type": core_config["type"]
            }
        
        # Generate high-level recommendations
        missing_core = [name for name, status in report["core_indexes_status"].items() if not status["exists"]]
        
        if missing_core:
            report["recommendations"].append(f"Missing core indexes: {', '.join(missing_core[:3])}")
            
        if report["benchmark_results"].get("performance_rating") in ["fair", "needs_optimization"]:
            report["recommendations"].append("Query performance could be improved with index optimization")
            
        if len(report["existing_indexes"]) < 10:
            report["recommendations"].append("Consider adding more specialized indexes for AI server operations")
        
        return report


def main():
    """Main function for Neo4j index management."""
    manager = Neo4jIndexManager()
    
    print("="*60)
    print("NEO4J INDEX MANAGEMENT SYSTEM") 
    print("="*60)
    
    try:
        # Connect to database
        if not manager.connect():
            print("❌ Failed to connect to Neo4j database")
            return False
        
        print("✅ Connected to Neo4j database")
        
        # Create all core indexes
        print("\n📊 Creating core indexes for AI server...")
        creation_results = manager.create_all_core_indexes()
        
        successful = sum(1 for success in creation_results.values() if success)
        total = len(creation_results)
        
        print(f"Index creation results: {successful}/{total} successful")
        
        for index_name, success in creation_results.items():
            status = "✅" if success else "❌"
            print(f"  {status} {index_name}")
        
        # Wait a moment for indexes to be created
        time.sleep(2)
        
        # Generate comprehensive report
        print("\n📈 Generating index performance report...")
        report = manager.generate_index_report()
        
        print(f"\nIndex Status:")
        print(f"  Total indexes: {len(report['existing_indexes'])}")
        print(f"  Core indexes: {sum(1 for s in report['core_indexes_status'].values() if s['exists'])}/{len(report['core_indexes_status'])}")
        
        # Performance results
        if "benchmark_results" in report and "error" not in report["benchmark_results"]:
            perf = report["benchmark_results"]
            print(f"  Performance rating: {perf.get('performance_rating', 'unknown')}")
            print(f"  Average query time: {perf.get('average_query_ms', 0)}ms")
        
        # Recommendations
        if report.get("recommendations"):
            print(f"\nRecommendations:")
            for rec in report["recommendations"]:
                print(f"  • {rec}")
        
        # Save detailed report
        report_path = "/Users/server/Code/AI-projects/AI-server/services/storage/data/neo4j/index_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to: {report_path}")
        print("✅ Index management completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Index management failed: {e}")
        return False
        
    finally:
        manager.disconnect()
        print("="*60)


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)