"""
Community Detection for Lazy Graph RAG
Implementation of community detection algorithms for graph-based retrieval
"""

import numpy as np
import networkx as nx
from typing import Dict, List, Set, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class Community:
    """Community structure"""
    id: str
    nodes: Set[str]
    keywords: List[str]
    description: str
    creation_time: datetime
    last_updated: datetime
    centrality_score: float
    density: float

class CommunityDetector:
    """
    Community detection for graph-based knowledge retrieval
    """
    
    def __init__(self, min_community_size: int = 3, max_communities: int = 100):
        self.min_community_size = min_community_size
        self.max_communities = max_communities
        self.communities: Dict[str, Community] = {}
        
    def detect_communities(self, graph: nx.Graph) -> Dict[str, Community]:
        """Detect communities in the graph using Louvain algorithm"""
        
        try:
            import networkx.algorithms.community as nx_comm
            
            # Use Louvain algorithm for community detection
            communities = nx_comm.louvain_communities(graph, seed=42)
            
            detected_communities = {}
            
            for i, community_nodes in enumerate(communities):
                if len(community_nodes) < self.min_community_size:
                    continue
                    
                community_id = f"community_{i}"
                
                # Calculate community metrics
                subgraph = graph.subgraph(community_nodes)
                density = nx.density(subgraph)
                
                # Calculate centrality
                centrality_scores = nx.degree_centrality(subgraph)
                avg_centrality = np.mean(list(centrality_scores.values()))
                
                # Extract keywords (simplified)
                keywords = self._extract_keywords(community_nodes, graph)
                
                # Generate description
                description = f"Community with {len(community_nodes)} nodes"
                
                community = Community(
                    id=community_id,
                    nodes=set(community_nodes),
                    keywords=keywords,
                    description=description,
                    creation_time=datetime.now(),
                    last_updated=datetime.now(),
                    centrality_score=avg_centrality,
                    density=density
                )
                
                detected_communities[community_id] = community
                
                if len(detected_communities) >= self.max_communities:
                    break
            
            self.communities.update(detected_communities)
            logger.info(f"Detected {len(detected_communities)} communities")
            
            return detected_communities
            
        except ImportError:
            logger.warning("NetworkX community detection not available, using fallback")
            return self._fallback_community_detection(graph)
        except Exception as e:
            logger.error(f"Community detection failed: {e}")
            return {}
    
    def _fallback_community_detection(self, graph: nx.Graph) -> Dict[str, Community]:
        """Fallback community detection using connected components"""
        
        communities = {}
        
        try:
            # Use connected components as communities
            for i, component in enumerate(nx.connected_components(graph)):
                if len(component) < self.min_community_size:
                    continue
                
                community_id = f"component_{i}"
                
                # Calculate basic metrics
                subgraph = graph.subgraph(component)
                density = nx.density(subgraph) if len(component) > 1 else 1.0
                
                keywords = self._extract_keywords(component, graph)
                
                community = Community(
                    id=community_id,
                    nodes=set(component),
                    keywords=keywords,
                    description=f"Connected component with {len(component)} nodes",
                    creation_time=datetime.now(),
                    last_updated=datetime.now(),
                    centrality_score=0.5,
                    density=density
                )
                
                communities[community_id] = community
            
            return communities
            
        except Exception as e:
            logger.error(f"Fallback community detection failed: {e}")
            return {}
    
    def _extract_keywords(self, nodes: Set[str], graph: nx.Graph) -> List[str]:
        """Extract keywords from community nodes"""
        
        keywords = []
        
        try:
            # Extract keywords from node attributes if available
            for node in nodes:
                node_data = graph.nodes.get(node, {})
                
                # Look for text content in various fields
                for field in ['content', 'text', 'title', 'description']:
                    if field in node_data and node_data[field]:
                        # Simple keyword extraction (first few words)
                        words = str(node_data[field]).split()[:3]
                        keywords.extend([w.lower() for w in words if len(w) > 3])
                
                if len(keywords) >= 10:  # Limit keywords
                    break
            
            # Remove duplicates and return top keywords
            unique_keywords = list(set(keywords))[:5]
            
            return unique_keywords if unique_keywords else ["unknown"]
            
        except Exception as e:
            logger.error(f"Keyword extraction failed: {e}")
            return ["unknown"]
    
    def get_community_for_node(self, node_id: str) -> Optional[Community]:
        """Get the community containing a specific node"""
        
        for community in self.communities.values():
            if node_id in community.nodes:
                return community
        
        return None
    
    def get_relevant_communities(self, query_keywords: List[str], top_k: int = 3) -> List[Community]:
        """Get communities most relevant to query keywords"""
        
        scored_communities = []
        
        for community in self.communities.values():
            # Calculate relevance score based on keyword overlap
            overlap = len(set(query_keywords) & set(community.keywords))
            keyword_score = overlap / len(community.keywords) if community.keywords else 0
            
            # Combine with community metrics
            relevance_score = (
                keyword_score * 0.6 +
                community.centrality_score * 0.2 +
                community.density * 0.2
            )
            
            scored_communities.append((relevance_score, community))
        
        # Sort by relevance and return top-k
        scored_communities.sort(key=lambda x: x[0], reverse=True)
        
        return [community for _, community in scored_communities[:top_k]]
    
    def update_communities(self, graph: nx.Graph):
        """Update existing communities with new graph data"""
        
        # Re-detect communities
        new_communities = self.detect_communities(graph)
        
        # Update timestamps for existing communities
        for community_id, community in new_communities.items():
            if community_id in self.communities:
                community.last_updated = datetime.now()
        
        logger.info(f"Updated {len(new_communities)} communities")
    
    def get_community_summary(self) -> Dict[str, Any]:
        """Get summary of all detected communities"""
        
        if not self.communities:
            return {"total_communities": 0, "communities": []}
        
        communities_info = []
        
        for community in self.communities.values():
            info = {
                "id": community.id,
                "size": len(community.nodes),
                "keywords": community.keywords,
                "description": community.description,
                "centrality_score": community.centrality_score,
                "density": community.density,
                "last_updated": community.last_updated.isoformat()
            }
            communities_info.append(info)
        
        return {
            "total_communities": len(self.communities),
            "communities": communities_info,
            "avg_size": np.mean([len(c.nodes) for c in self.communities.values()]),
            "avg_density": np.mean([c.density for c in self.communities.values()])
        }