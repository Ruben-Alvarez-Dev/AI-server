"""
Lazy Graph Query Engine
Query engine for LazyGraphRAG with community-aware retrieval
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

from .community_detection import CommunityDetector

logger = logging.getLogger(__name__)

@dataclass
class QueryResult:
    """Query result from LazyGraph"""
    content: str
    relevance_score: float
    community_id: Optional[str]
    source_nodes: List[str]
    metadata: Dict[str, Any]

class LazyGraphQueryEngine:
    """
    Query engine for LazyGraphRAG with community-aware retrieval
    """
    
    def __init__(self, community_detector: CommunityDetector):
        self.community_detector = community_detector
        self.query_cache: Dict[str, List[QueryResult]] = {}
        
    def query(self, query_text: str, top_k: int = 5) -> List[QueryResult]:
        """Execute query against lazy graph"""
        
        try:
            # Check cache first
            cache_key = f"{query_text}:{top_k}"
            if cache_key in self.query_cache:
                logger.debug(f"Cache hit for query: {query_text}")
                return self.query_cache[cache_key]
            
            # Extract query keywords (simplified)
            query_keywords = self._extract_query_keywords(query_text)
            
            # Get relevant communities
            relevant_communities = self.community_detector.get_relevant_communities(
                query_keywords, top_k=min(3, top_k)
            )
            
            results = []
            
            # Generate results from communities
            for community in relevant_communities:
                result = QueryResult(
                    content=f"Community {community.id}: {community.description}",
                    relevance_score=community.centrality_score,
                    community_id=community.id,
                    source_nodes=list(community.nodes)[:5],  # Limit to 5 nodes
                    metadata={
                        "keywords": community.keywords,
                        "density": community.density,
                        "size": len(community.nodes)
                    }
                )
                results.append(result)
            
            # Sort by relevance
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            results = results[:top_k]
            
            # Cache results
            self.query_cache[cache_key] = results
            
            logger.info(f"Query executed: {query_text} -> {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return []
    
    def _extract_query_keywords(self, query_text: str) -> List[str]:
        """Extract keywords from query text"""
        
        try:
            # Simple keyword extraction
            words = query_text.lower().split()
            # Filter out common stop words
            stop_words = {'the', 'is', 'at', 'which', 'on', 'and', 'a', 'to', 'for', 'of', 'with'}
            keywords = [word for word in words if len(word) > 3 and word not in stop_words]
            
            return keywords[:5]  # Limit to 5 keywords
            
        except Exception as e:
            logger.error(f"Keyword extraction failed: {e}")
            return []
    
    def clear_cache(self):
        """Clear query cache"""
        self.query_cache.clear()
        logger.info("Query cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get query cache statistics"""
        return {
            "cached_queries": len(self.query_cache),
            "total_results": sum(len(results) for results in self.query_cache.values())
        }