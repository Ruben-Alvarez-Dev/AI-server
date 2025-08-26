"""
Data models for reranking operations.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from dataclasses import dataclass


class RerankRequest(BaseModel):
    """Request for reranking operation."""
    query: str = Field(..., description="Search query")
    documents: List[str] = Field(..., description="Documents to rerank")
    top_k: Optional[int] = Field(default=10, description="Number of top results to return")
    metadata: Optional[List[Dict[str, Any]]] = Field(default=None, description="Document metadata")


class RerankResult(BaseModel):
    """Result from reranking operation."""
    document: str = Field(..., description="Reranked document text")
    score: float = Field(..., description="Reranking score")
    original_index: int = Field(..., description="Original position in input list")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Document metadata")


@dataclass
class RerankerConfig:
    """Configuration for reranker model."""
    model_name: str = "BAAI/bge-reranker-v2-m3"
    device: str = "cpu"
    max_length: int = 512
    batch_size: int = 16
    cache_dir: Optional[str] = None
    trust_remote_code: bool = True