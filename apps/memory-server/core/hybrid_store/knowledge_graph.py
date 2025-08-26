"""
Knowledge Graph Implementation
Graph-based knowledge storage for hybrid retrieval
"""

import networkx as nx
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

@dataclass
class Node:
    """Knowledge graph node"""
    id: str
    content: str
    node_type: str
    metadata: Dict[str, Any]
    embedding: Optional[np.ndarray] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

@dataclass
class Edge:
    """Knowledge graph edge"""
    source: str
    target: str
    relation_type: str
    weight: float = 1.0
    metadata: Dict[str, Any] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.now()

class KnowledgeGraph:
    """
    Knowledge graph for hybrid storage and retrieval
    """
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.nodes: Dict[str, Node] = {}
        self.edges: Dict[Tuple[str, str], Edge] = {}
        self.node_embeddings: Dict[str, np.ndarray] = {}
        
    def add_node(self, node: Node) -> bool:
        """Add node to knowledge graph"""
        
        try:
            self.nodes[node.id] = node
            
            # Add to NetworkX graph
            self.graph.add_node(
                node.id,
                content=node.content,
                node_type=node.node_type,
                metadata=node.metadata,
                created_at=node.created_at,
                updated_at=node.updated_at
            )
            
            # Store embedding if available
            if node.embedding is not None:
                self.node_embeddings[node.id] = node.embedding
            
            logger.debug(f"Added node: {node.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add node {node.id}: {e}")
            return False
    
    def add_edge(self, edge: Edge) -> bool:
        """Add edge to knowledge graph"""
        
        try:
            # Check if both nodes exist
            if edge.source not in self.nodes or edge.target not in self.nodes:
                logger.warning(f"Cannot add edge: missing nodes {edge.source} or {edge.target}")
                return False
            
            edge_key = (edge.source, edge.target)
            self.edges[edge_key] = edge
            
            # Add to NetworkX graph
            self.graph.add_edge(
                edge.source,
                edge.target,
                relation_type=edge.relation_type,
                weight=edge.weight,
                metadata=edge.metadata,
                created_at=edge.created_at
            )
            
            logger.debug(f"Added edge: {edge.source} -> {edge.target}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add edge {edge.source} -> {edge.target}: {e}")
            return False
    
    def get_node(self, node_id: str) -> Optional[Node]:
        """Get node by ID"""
        return self.nodes.get(node_id)
    
    def get_neighbors(self, node_id: str, hop_count: int = 1) -> List[Node]:
        """Get neighboring nodes within hop count"""
        
        try:
            if node_id not in self.graph:
                return []
            
            neighbors = set()
            
            # Use BFS to find neighbors within hop count
            queue = [(node_id, 0)]
            visited = {node_id}
            
            while queue:
                current_node, current_hop = queue.pop(0)
                
                if current_hop < hop_count:
                    # Get direct neighbors
                    for neighbor in self.graph.neighbors(current_node):
                        if neighbor not in visited:
                            neighbors.add(neighbor)
                            visited.add(neighbor)
                            queue.append((neighbor, current_hop + 1))
            
            return [self.nodes[nid] for nid in neighbors if nid in self.nodes]
            
        except Exception as e:
            logger.error(f"Failed to get neighbors for {node_id}: {e}")
            return []
    
    def find_path(self, source: str, target: str, max_length: int = 5) -> List[str]:
        """Find shortest path between nodes"""
        
        try:
            if source not in self.graph or target not in self.graph:
                return []
            
            path = nx.shortest_path(self.graph, source, target)
            
            if len(path) <= max_length + 1:  # +1 because path includes both endpoints
                return path
            else:
                return []
                
        except nx.NetworkXNoPath:
            logger.debug(f"No path found between {source} and {target}")
            return []
        except Exception as e:
            logger.error(f"Path finding failed: {e}")
            return []
    
    def search_nodes_by_content(self, query: str, limit: int = 10) -> List[Node]:
        """Search nodes by content similarity"""
        
        try:
            matching_nodes = []
            
            query_lower = query.lower()
            
            for node in self.nodes.values():
                if query_lower in node.content.lower():
                    matching_nodes.append(node)
            
            # Sort by content length (shorter matches first)
            matching_nodes.sort(key=lambda x: len(x.content))
            
            return matching_nodes[:limit]
            
        except Exception as e:
            logger.error(f"Content search failed: {e}")
            return []
    
    def search_nodes_by_embedding(self, query_embedding: np.ndarray, 
                                 limit: int = 10) -> List[Tuple[Node, float]]:
        """Search nodes by embedding similarity"""
        
        try:
            similarities = []
            
            for node_id, node_embedding in self.node_embeddings.items():
                if node_id in self.nodes:
                    # Calculate cosine similarity
                    similarity = np.dot(query_embedding, node_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(node_embedding)
                    )
                    similarities.append((self.nodes[node_id], float(similarity)))
            
            # Sort by similarity
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            return similarities[:limit]
            
        except Exception as e:
            logger.error(f"Embedding search failed: {e}")
            return []
    
    def get_subgraph(self, node_ids: List[str], include_edges: bool = True) -> Dict[str, Any]:
        """Extract subgraph containing specified nodes"""
        
        try:
            subgraph_nodes = {}
            subgraph_edges = {}
            
            # Include specified nodes
            for node_id in node_ids:
                if node_id in self.nodes:
                    subgraph_nodes[node_id] = self.nodes[node_id]
            
            # Include edges if requested
            if include_edges:
                for edge_key, edge in self.edges.items():
                    source, target = edge_key
                    if source in subgraph_nodes and target in subgraph_nodes:
                        subgraph_edges[edge_key] = edge
            
            return {
                "nodes": subgraph_nodes,
                "edges": subgraph_edges,
                "node_count": len(subgraph_nodes),
                "edge_count": len(subgraph_edges)
            }
            
        except Exception as e:
            logger.error(f"Subgraph extraction failed: {e}")
            return {"nodes": {}, "edges": {}, "node_count": 0, "edge_count": 0}
    
    def get_centrality_scores(self, centrality_type: str = "degree") -> Dict[str, float]:
        """Calculate centrality scores for nodes"""
        
        try:
            if centrality_type == "degree":
                return nx.degree_centrality(self.graph)
            elif centrality_type == "betweenness":
                return nx.betweenness_centrality(self.graph)
            elif centrality_type == "closeness":
                return nx.closeness_centrality(self.graph)
            elif centrality_type == "pagerank":
                return nx.pagerank(self.graph)
            else:
                logger.warning(f"Unknown centrality type: {centrality_type}")
                return nx.degree_centrality(self.graph)
                
        except Exception as e:
            logger.error(f"Centrality calculation failed: {e}")
            return {}
    
    def remove_node(self, node_id: str) -> bool:
        """Remove node from graph"""
        
        try:
            if node_id not in self.nodes:
                return False
            
            # Remove from NetworkX graph
            self.graph.remove_node(node_id)
            
            # Remove from internal structures
            del self.nodes[node_id]
            
            if node_id in self.node_embeddings:
                del self.node_embeddings[node_id]
            
            # Remove associated edges
            edges_to_remove = [
                edge_key for edge_key in self.edges
                if edge_key[0] == node_id or edge_key[1] == node_id
            ]
            
            for edge_key in edges_to_remove:
                del self.edges[edge_key]
            
            logger.debug(f"Removed node: {node_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove node {node_id}: {e}")
            return False
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """Get graph statistics"""
        
        try:
            stats = {
                "node_count": len(self.nodes),
                "edge_count": len(self.edges),
                "density": nx.density(self.graph),
                "is_connected": nx.is_connected(self.graph.to_undirected()),
                "avg_clustering": nx.average_clustering(self.graph.to_undirected()),
                "node_types": {},
                "embedding_coverage": len(self.node_embeddings) / len(self.nodes) if self.nodes else 0
            }
            
            # Count node types
            for node in self.nodes.values():
                node_type = node.node_type
                stats["node_types"][node_type] = stats["node_types"].get(node_type, 0) + 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to calculate graph stats: {e}")
            return {"error": str(e)}
    
    def export_to_dict(self) -> Dict[str, Any]:
        """Export graph to dictionary format"""
        
        try:
            export_data = {
                "nodes": {},
                "edges": {},
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "node_count": len(self.nodes),
                    "edge_count": len(self.edges)
                }
            }
            
            # Export nodes
            for node_id, node in self.nodes.items():
                node_dict = asdict(node)
                # Convert datetime to ISO format
                node_dict["created_at"] = node.created_at.isoformat()
                node_dict["updated_at"] = node.updated_at.isoformat()
                # Remove embedding (not JSON serializable)
                node_dict.pop("embedding", None)
                export_data["nodes"][node_id] = node_dict
            
            # Export edges
            for edge_key, edge in self.edges.items():
                edge_dict = asdict(edge)
                edge_dict["created_at"] = edge.created_at.isoformat()
                key_str = f"{edge_key[0]}->{edge_key[1]}"
                export_data["edges"][key_str] = edge_dict
            
            return export_data
            
        except Exception as e:
            logger.error(f"Graph export failed: {e}")
            return {"error": str(e)}