#!/usr/bin/env python3
"""
Neo4j Database Initialization

Initialize Neo4j graph database with optimized storage engine,
schema constraints, and seed data for AI server operations.
Creates initial database structure and validates functionality.
"""

import logging
import time
import subprocess
import os
import signal
import psutil
from typing import Dict, Any, List, Optional, Tuple
import json

from neo4j_config import get_neo4j_config
from neo4j_client import get_neo4j_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Neo4jDatabaseInitializer:
    """Initialize and configure Neo4j graph database."""
    
    def __init__(self):
        self.config = get_neo4j_config()
        self.client = get_neo4j_client()
        self.neo4j_home = "/Users/server/Code/AI-projects/AI-server/services/storage/neo4j/neo4j-community-5.23.0"
        self.neo4j_process = None
        
    def start_neo4j_server(self) -> bool:
        """Start Neo4j server if not already running."""
        logger.info("Starting Neo4j server...")
        
        try:
            # Check if Neo4j is already running
            if self._is_neo4j_running():
                logger.info("Neo4j server is already running")
                return True
            
            # Set Java environment
            env = os.environ.copy()
            env["JAVA_HOME"] = "/opt/homebrew/opt/openjdk@21"
            env["PATH"] = f"/opt/homebrew/opt/openjdk@21/bin:{env.get('PATH', '')}"
            
            # Start Neo4j server
            start_command = f"{self.neo4j_home}/bin/neo4j start"
            
            result = subprocess.run(
                start_command,
                shell=True,
                capture_output=True,
                text=True,
                env=env
            )
            
            if result.returncode == 0:
                logger.info("Neo4j server start command executed successfully")
                
                # Wait for server to be ready
                if self._wait_for_server_ready():
                    logger.info("Neo4j server is ready and responding")
                    return True
                else:
                    logger.error("Neo4j server failed to become ready")
                    return False
            else:
                logger.error(f"Failed to start Neo4j server: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Exception starting Neo4j server: {e}")
            return False
    
    def _is_neo4j_running(self) -> bool:
        """Check if Neo4j server is running."""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'java' in proc.info['name'].lower():
                        cmdline = ' '.join(proc.info['cmdline'])
                        if 'neo4j' in cmdline.lower():
                            return True
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            return False
        except Exception:
            return False
    
    def _wait_for_server_ready(self, timeout: int = 60) -> bool:
        """Wait for Neo4j server to be ready."""
        logger.info("Waiting for Neo4j server to be ready...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                if self.client.connect():
                    # Test basic connectivity
                    with self.client.session() as session:
                        result = session.run("RETURN 1 as test")
                        if result.single()["test"] == 1:
                            return True
                    
            except Exception as e:
                logger.debug(f"Server not ready yet: {e}")
                
            time.sleep(2)
        
        logger.error(f"Neo4j server not ready after {timeout} seconds")
        return False
    
    def stop_neo4j_server(self) -> bool:
        """Stop Neo4j server."""
        logger.info("Stopping Neo4j server...")
        
        try:
            # Set Java environment
            env = os.environ.copy()
            env["JAVA_HOME"] = "/opt/homebrew/opt/openjdk@21"
            env["PATH"] = f"/opt/homebrew/opt/openjdk@21/bin:{env.get('PATH', '')}"
            
            stop_command = f"{self.neo4j_home}/bin/neo4j stop"
            
            result = subprocess.run(
                stop_command,
                shell=True,
                capture_output=True,
                text=True,
                env=env
            )
            
            if result.returncode == 0:
                logger.info("Neo4j server stopped successfully")
                return True
            else:
                logger.warning(f"Neo4j stop command returned: {result.stderr}")
                return True  # May already be stopped
                
        except Exception as e:
            logger.error(f"Exception stopping Neo4j server: {e}")
            return False
    
    def set_initial_password(self) -> bool:
        """Set initial Neo4j password."""
        logger.info("Setting initial Neo4j password...")
        
        try:
            # Set Java environment
            env = os.environ.copy()
            env["JAVA_HOME"] = "/opt/homebrew/opt/openjdk@21"
            env["PATH"] = f"/opt/homebrew/opt/openjdk@21/bin:{env.get('PATH', '')}"
            
            # Set password using neo4j-admin
            password_command = f"{self.neo4j_home}/bin/neo4j-admin dbms set-initial-password {self.config.password}"
            
            result = subprocess.run(
                password_command,
                shell=True,
                capture_output=True,
                text=True,
                env=env
            )
            
            if result.returncode == 0:
                logger.info("Initial password set successfully")
                return True
            else:
                # May already be set
                if "already has an initial password" in result.stderr:
                    logger.info("Initial password already set")
                    return True
                else:
                    logger.warning(f"Password setting returned: {result.stderr}")
                    return True
                    
        except Exception as e:
            logger.error(f"Exception setting initial password: {e}")
            return False
    
    def create_database_constraints(self) -> bool:
        """Create database constraints and schema."""
        logger.info("Creating database constraints...")
        
        try:
            constraints = [
                # Node constraints
                "CREATE CONSTRAINT entity_id_unique IF NOT EXISTS FOR (n:Entity) REQUIRE n.id IS UNIQUE",
                "CREATE CONSTRAINT concept_id_unique IF NOT EXISTS FOR (n:Concept) REQUIRE n.id IS UNIQUE", 
                "CREATE CONSTRAINT document_id_unique IF NOT EXISTS FOR (n:Document) REQUIRE n.id IS UNIQUE",
                "CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (n:User) REQUIRE n.id IS UNIQUE",
                
                # Property constraints  
                "CREATE CONSTRAINT entity_name_exists IF NOT EXISTS FOR (n:Entity) REQUIRE n.name IS NOT NULL",
                "CREATE CONSTRAINT concept_name_exists IF NOT EXISTS FOR (n:Concept) REQUIRE n.name IS NOT NULL",
                
                # Index constraints for performance
                "CREATE INDEX entity_type_index IF NOT EXISTS FOR (n:Entity) ON (n.type)",
                "CREATE INDEX concept_category_index IF NOT EXISTS FOR (n:Concept) ON (n.category)",
                "CREATE INDEX document_timestamp_index IF NOT EXISTS FOR (n:Document) ON (n.created_at)",
                "CREATE INDEX relationship_strength_index IF NOT EXISTS FOR ()-[r:RELATED]->() ON (r.strength)"
            ]
            
            constraints_created = 0
            for constraint in constraints:
                try:
                    result = self.client.execute_write_query(constraint)
                    constraints_created += 1
                    logger.debug(f"Created constraint: {constraint[:50]}...")
                except Exception as e:
                    logger.warning(f"Constraint creation failed (may already exist): {e}")
            
            logger.info(f"Database constraints processed: {constraints_created}/{len(constraints)}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create database constraints: {e}")
            return False
    
    def create_seed_data(self) -> bool:
        """Create initial seed data for AI server operations."""
        logger.info("Creating seed data...")
        
        try:
            # System entities
            system_nodes = [
                {
                    "labels": ["System", "Entity"],
                    "properties": {
                        "id": "ai-server-system",
                        "name": "AI Server System",
                        "type": "system",
                        "version": "1.0.0",
                        "created_at": time.time(),
                        "description": "Core AI server system entity"
                    }
                },
                {
                    "labels": ["Memory", "System"],  
                    "properties": {
                        "id": "memory-system",
                        "name": "Memory System",
                        "type": "memory",
                        "capacity": "unlimited",
                        "created_at": time.time(),
                        "description": "AI server memory management system"
                    }
                },
                {
                    "labels": ["LLM", "System"],
                    "properties": {
                        "id": "llm-system", 
                        "name": "LLM System",
                        "type": "llm",
                        "models": ["llama", "openai"],
                        "created_at": time.time(),
                        "description": "Large Language Model orchestration system"
                    }
                }
            ]
            
            # Create system nodes
            created_nodes = []
            for node_def in system_nodes:
                node = self.client.create_node(
                    labels=node_def["labels"],
                    properties=node_def["properties"]
                )
                created_nodes.append(node)
                logger.debug(f"Created node: {node_def['properties']['name']}")
            
            # Create relationships between system components
            if len(created_nodes) >= 2:
                # AI Server System manages Memory System
                self.client.execute_write_query("""
                    MATCH (system:System {id: 'ai-server-system'})
                    MATCH (memory:Memory {id: 'memory-system'})
                    CREATE (system)-[r:MANAGES {
                        relationship_type: 'system_management',
                        created_at: $timestamp,
                        strength: 1.0
                    }]->(memory)
                """, {"timestamp": time.time()})
                
                # AI Server System orchestrates LLM System
                self.client.execute_write_query("""
                    MATCH (system:System {id: 'ai-server-system'})  
                    MATCH (llm:LLM {id: 'llm-system'})
                    CREATE (system)-[r:ORCHESTRATES {
                        relationship_type: 'system_orchestration',
                        created_at: $timestamp,
                        strength: 1.0
                    }]->(llm)
                """, {"timestamp": time.time()})
                
                # Memory System supports LLM System
                self.client.execute_write_query("""
                    MATCH (memory:Memory {id: 'memory-system'})
                    MATCH (llm:LLM {id: 'llm-system'})
                    CREATE (memory)-[r:SUPPORTS {
                        relationship_type: 'system_support',
                        created_at: $timestamp,
                        strength: 0.8
                    }]->(llm)
                """, {"timestamp": time.time()})
            
            logger.info(f"Seed data created: {len(system_nodes)} nodes with relationships")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create seed data: {e}")
            return False
    
    def validate_database_initialization(self) -> Dict[str, Any]:
        """Validate database initialization was successful."""
        logger.info("Validating database initialization...")
        
        validation_results = {
            "connectivity": False,
            "constraints": 0,
            "indexes": 0,
            "nodes": 0,
            "relationships": 0,
            "seed_data": False,
            "performance_test": {}
        }
        
        try:
            # Test connectivity
            if self.client.connect():
                validation_results["connectivity"] = True
                
                # Count constraints
                constraints_result = self.client.execute_query("SHOW CONSTRAINTS")
                validation_results["constraints"] = len(constraints_result)
                
                # Count indexes
                indexes_result = self.client.execute_query("SHOW INDEXES")
                validation_results["indexes"] = len(indexes_result)
                
                # Count nodes and relationships
                stats = self.client.get_database_stats()
                validation_results["nodes"] = stats.get("nodes", 0)
                validation_results["relationships"] = stats.get("relationships", 0)
                
                # Validate seed data
                system_nodes = self.client.find_nodes("System")
                if len(system_nodes) >= 1:
                    validation_results["seed_data"] = True
                
                # Performance test
                start_time = time.time()
                test_result = self.client.execute_query("MATCH (n) RETURN count(n) as total_nodes")
                query_time = time.time() - start_time
                
                validation_results["performance_test"] = {
                    "simple_query_ms": round(query_time * 1000, 2),
                    "total_nodes": test_result[0]["total_nodes"] if test_result else 0
                }
                
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            validation_results["error"] = str(e)
        
        return validation_results
    
    def initialize_database(self) -> bool:
        """Complete database initialization process."""
        logger.info("Starting Neo4j database initialization...")
        
        try:
            # Step 1: Set initial password (server must be stopped)
            if not self.set_initial_password():
                logger.warning("Password setting may have failed")
            
            # Step 2: Start Neo4j server  
            if not self.start_neo4j_server():
                logger.error("Failed to start Neo4j server")
                return False
            
            # Step 3: Wait a bit for server to fully initialize
            time.sleep(5)
            
            # Step 4: Connect client
            if not self.client.connect():
                logger.error("Failed to connect to Neo4j database")
                return False
            
            # Step 5: Create constraints and schema
            if not self.create_database_constraints():
                logger.warning("Some constraints may not have been created")
            
            # Step 6: Create seed data
            if not self.create_seed_data():
                logger.warning("Seed data creation may have failed")
            
            # Step 7: Validate initialization
            validation = self.validate_database_initialization()
            
            if validation["connectivity"] and validation["nodes"] > 0:
                logger.info("Database initialization completed successfully")
                return True
            else:
                logger.error(f"Database initialization validation failed: {validation}")
                return False
                
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            return False
        
        finally:
            # Always disconnect client
            self.client.disconnect()


def main():
    """Main function to initialize Neo4j database."""
    initializer = Neo4jDatabaseInitializer()
    
    print("="*60)
    print("NEO4J DATABASE INITIALIZATION")
    print("="*60)
    
    try:
        # Initialize database
        if initializer.initialize_database():
            print("✅ Neo4j database initialized successfully!")
            
            # Get final validation
            validation = initializer.validate_database_initialization()
            
            print(f"\nDatabase Status:")
            print(f"  Connectivity: {'✅' if validation['connectivity'] else '❌'}")
            print(f"  Constraints: {validation['constraints']}")
            print(f"  Indexes: {validation['indexes']}")
            print(f"  Nodes: {validation['nodes']}")  
            print(f"  Relationships: {validation['relationships']}")
            print(f"  Seed Data: {'✅' if validation['seed_data'] else '❌'}")
            
            if "performance_test" in validation:
                perf = validation["performance_test"]
                print(f"  Query Performance: {perf.get('simple_query_ms', 0)}ms")
            
            # Save initialization report
            report_path = "/Users/server/Code/AI-projects/AI-server/services/storage/data/neo4j/initialization_report.json"
            with open(report_path, 'w') as f:
                json.dump(validation, f, indent=2, default=str)
            
            print(f"\n📄 Initialization report saved to: {report_path}")
            
        else:
            print("❌ Neo4j database initialization failed!")
            return False
    
    except KeyboardInterrupt:
        print("\n⏹️ Initialization interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        return False
    
    print("="*60)
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)