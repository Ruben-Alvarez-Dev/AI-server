"""
LazyGraphRAG Core Module
Microsoft's LazyGraphRAG implementation with zero-cost indexing
"""

from .lazy_indexer import LazyGraphIndexer, Document
from .dynamic_subgraph import DynamicSubgraphBuilder
from .community_detection import CommunityDetector
from .query_engine import LazyGraphQueryEngine

__all__ = [
    "LazyGraphIndexer",
    "Document", 
    "DynamicSubgraphBuilder",
    "CommunityDetector",
    "LazyGraphQueryEngine"
]