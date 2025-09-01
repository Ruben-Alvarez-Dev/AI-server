#!/usr/bin/env python3
"""
Neo4j Client Implementation

High-level Neo4j client using official Python driver.
Provides Pythonic interface for graph operations with connection pooling,
transaction management, and optimized performance for AI server workload.
"""

import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from contextlib import contextmanager
from neo4j import GraphDatabase, Driver, Session, Transaction, Record
from neo4j.exceptions import ServiceUnavailable, TransientError
import time
import json

from neo4j_config import get_neo4j_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Neo4jClient:
    """High-level Neo4j client with Pythonic interface."""
    
    def __init__(self):
        self.config = get_neo4j_config()
        self.driver: Optional[Driver] = None
        self.connected = False
    
    def connect(self) -> bool:
        """Connect to Neo4j database."""
        try:
            self.driver = self.config.get_driver()
            
            # Test connection
            if self.config.test_connection():
                self.connected = True
                logger.info("Neo4j client connected successfully")
                return True
            else:
                logger.error("Neo4j connection test failed")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from Neo4j database."""
        if self.driver:
            self.config.close_driver()
            self.connected = False
            logger.info("Neo4j client disconnected")
    
    @contextmanager
    def session(self, database: Optional[str] = None):
        """Context manager for Neo4j sessions."""
        if not self.connected:
            if not self.connect():
                raise RuntimeError("Cannot connect to Neo4j database")
        
        session = self.driver.session(database=database or self.config.database)
        try:
            yield session
        finally:
            session.close()
    
    @contextmanager
    def transaction(self, database: Optional[str] = None):
        """Context manager for Neo4j transactions."""
        with self.session(database=database) as session:
            tx = session.begin_transaction()
            try:
                yield tx
                tx.commit()
            except Exception as e:
                tx.rollback()
                raise e
    
    def execute_query(self, 
                     query: str, 
                     parameters: Optional[Dict[str, Any]] = None,
                     database: Optional[str] = None) -> List[Record]:
        """Execute Cypher query and return results."""
        try:
            with self.session(database=database) as session:
                result = session.run(query, parameters or {})
                return list(result)
                
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Parameters: {parameters}")
            raise
    
    def execute_write_query(self,
                           query: str,
                           parameters: Optional[Dict[str, Any]] = None,
                           database: Optional[str] = None) -> List[Record]:
        """Execute write query with transaction."""
        try:
            with self.transaction(database=database) as tx:
                result = tx.run(query, parameters or {})
                return list(result)
                
        except Exception as e:
            logger.error(f"Write query execution failed: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Parameters: {parameters}")
            raise
    
    def create_node(self,
                   labels: Union[str, List[str]],
                   properties: Dict[str, Any],
                   database: Optional[str] = None) -> Record:
        """Create a node with labels and properties."""
        if isinstance(labels, str):
            labels = [labels]
        
        labels_str = ":".join(labels)
        properties_str = ", ".join([f"{k}: ${k}" for k in properties.keys()])
        
        query = f"CREATE (n:{labels_str} {{ {properties_str} }}) RETURN n"
        
        result = self.execute_write_query(query, properties, database)
        return result[0] if result else None
    
    def find_nodes(self,
                  label: str,
                  properties: Optional[Dict[str, Any]] = None,
                  limit: Optional[int] = None,
                  database: Optional[str] = None) -> List[Record]:
        """Find nodes by label and properties."""
        query = f"MATCH (n:{label})"
        
        params = {}
        if properties:
            where_conditions = []
            for key, value in properties.items():
                where_conditions.append(f"n.{key} = ${key}")
                params[key] = value
            query += f" WHERE {' AND '.join(where_conditions)}"
        
        query += " RETURN n"
        
        if limit:
            query += f" LIMIT {limit}"
        
        return self.execute_query(query, params, database)
    
    def create_relationship(self,
                          from_node_id: int,
                          to_node_id: int,
                          relationship_type: str,
                          properties: Optional[Dict[str, Any]] = None,
                          database: Optional[str] = None) -> Record:
        """Create relationship between nodes."""
        props_str = ""
        params = {
            "from_id": from_node_id,
            "to_id": to_node_id
        }
        
        if properties:
            props_str = "{ " + ", ".join([f"{k}: ${k}" for k in properties.keys()]) + " }"
            params.update(properties)
        
        query = f"""
        MATCH (a), (b)
        WHERE id(a) = $from_id AND id(b) = $to_id
        CREATE (a)-[r:{relationship_type} {props_str}]->(b)
        RETURN r
        """
        
        result = self.execute_write_query(query, params, database)
        return result[0] if result else None
    
    def find_relationships(self,
                          relationship_type: Optional[str] = None,
                          properties: Optional[Dict[str, Any]] = None,
                          limit: Optional[int] = None,
                          database: Optional[str] = None) -> List[Record]:
        """Find relationships by type and properties."""
        rel_pattern = f"[r:{relationship_type}]" if relationship_type else "[r]"
        query = f"MATCH ()-{rel_pattern}-()"
        
        params = {}
        if properties:
            where_conditions = []
            for key, value in properties.items():
                where_conditions.append(f"r.{key} = ${key}")
                params[key] = value
            query += f" WHERE {' AND '.join(where_conditions)}"
        
        query += " RETURN r"
        
        if limit:
            query += f" LIMIT {limit}"
        
        return self.execute_query(query, params, database)
    
    def traverse_graph(self,
                      start_node_id: int,
                      relationship_types: Optional[List[str]] = None,
                      direction: str = "BOTH",
                      max_depth: int = 3,
                      database: Optional[str] = None) -> List[Record]:
        """Traverse graph from starting node."""
        direction_map = {
            "OUT": "->",
            "IN": "<-", 
            "BOTH": "-"
        }
        
        dir_symbol = direction_map.get(direction.upper(), "-")
        
        if relationship_types:
            rel_pattern = f"[r:{':'.join(relationship_types)}*1..{max_depth}]"
        else:
            rel_pattern = f"[r*1..{max_depth}]"
        
        query = f"""
        MATCH (start)
        WHERE id(start) = $start_id
        MATCH path = (start){dir_symbol}{rel_pattern}{dir_symbol}(end)
        RETURN path, start, end, relationships(path) as rels
        """
        
        params = {"start_id": start_node_id}
        return self.execute_query(query, params, database)
    
    def get_node_count(self, label: Optional[str] = None, database: Optional[str] = None) -> int:
        """Get count of nodes, optionally by label."""
        if label:
            query = f"MATCH (n:{label}) RETURN count(n) as count"
        else:
            query = "MATCH (n) RETURN count(n) as count"
        
        result = self.execute_query(query, database=database)
        return result[0]["count"] if result else 0
    
    def get_relationship_count(self, 
                             relationship_type: Optional[str] = None,
                             database: Optional[str] = None) -> int:
        """Get count of relationships, optionally by type."""
        if relationship_type:
            query = f"MATCH ()-[r:{relationship_type}]-() RETURN count(r) as count"
        else:
            query = "MATCH ()-[r]-() RETURN count(r) as count"
        
        result = self.execute_query(query, database=database)
        return result[0]["count"] if result else 0
    
    def delete_all_data(self, database: Optional[str] = None) -> bool:
        """Delete all nodes and relationships (USE WITH CAUTION)."""
        try:
            logger.warning("Deleting all data from Neo4j database")
            self.execute_write_query("MATCH (n) DETACH DELETE n", database=database)
            logger.info("All data deleted successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to delete all data: {e}")
            return False
    
    def get_database_stats(self, database: Optional[str] = None) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            stats = {}
            
            # Node count
            stats["nodes"] = self.get_node_count(database=database)
            
            # Relationship count
            stats["relationships"] = self.get_relationship_count(database=database)
            
            # Label counts
            result = self.execute_query("CALL db.labels()", database=database)
            labels = [record["label"] for record in result]
            
            stats["labels"] = {}
            for label in labels:
                stats["labels"][label] = self.get_node_count(label, database=database)
            
            # Relationship type counts
            result = self.execute_query("CALL db.relationshipTypes()", database=database)
            rel_types = [record["relationshipType"] for record in result]
            
            stats["relationship_types"] = {}
            for rel_type in rel_types:
                stats["relationship_types"][rel_type] = self.get_relationship_count(rel_type, database=database)
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}


def get_neo4j_client() -> Neo4jClient:
    """Get configured Neo4j client instance."""
    return Neo4jClient()


if __name__ == "__main__":
    # Test Neo4j client
    client = get_neo4j_client()
    
    try:
        # Connect to database
        if client.connect():
            print("✅ Neo4j client connected successfully")
            
            # Get database stats
            stats = client.get_database_stats()
            print(f"📊 Database stats: {json.dumps(stats, indent=2)}")
            
        else:
            print("❌ Failed to connect to Neo4j")
            
    except Exception as e:
        print(f"❌ Neo4j client test failed: {e}")
        
    finally:
        client.disconnect()
        print("Neo4j client test completed")