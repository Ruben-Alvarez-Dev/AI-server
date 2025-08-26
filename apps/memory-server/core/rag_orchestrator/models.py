"""
Data models for RAG orchestration operations.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from dataclasses import dataclass
from enum import Enum

from ..query_processing.models import QueryResponse
from ..reranker.models import RerankResult
from ..generation.models import GenerationResponse


class RAGStage(str, Enum):
    """Stages of the RAG pipeline."""
    QUERY_PROCESSING = "query_processing"
    RETRIEVAL = "retrieval"
    RERANKING = "reranking"
    GENERATION = "generation"
    COMPLETE = "complete"


class RAGMode(str, Enum):
    """RAG operation modes."""
    STANDARD = "standard"
    CONVERSATIONAL = "conversational"
    CODE_FOCUSED = "code_focused"
    DOCUMENT_FOCUSED = "document_focused"
    AGENTIC = "agentic"


class RAGRequest(BaseModel):
    """Request for RAG operation."""
    query: str = Field(..., description="User query")
    workspace: Optional[str] = Field(default=None, description="Target workspace")
    mode: RAGMode = Field(default=RAGMode.STANDARD, description="RAG mode")
    max_context_docs: int = Field(default=5, description="Maximum context documents")
    enable_reranking: bool = Field(default=True, description="Enable reranking step")
    enable_query_processing: bool = Field(default=True, description="Enable query processing")
    conversation_history: Optional[List[Dict[str, str]]] = Field(default=None, description="Conversation context")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class RAGResponse(BaseModel):
    """Response from RAG operation."""
    query: str = Field(..., description="Original query")
    answer: str = Field(..., description="Generated answer")
    confidence: float = Field(..., description="Overall confidence score")
    
    # Pipeline stages data
    query_processing: Optional[QueryResponse] = Field(default=None, description="Query processing results")
    retrieved_documents: List[str] = Field(default_factory=list, description="Retrieved documents")
    reranked_results: Optional[List[RerankResult]] = Field(default=None, description="Reranking results")
    generation_result: Optional[GenerationResponse] = Field(default=None, description="Generation results")
    
    # Metadata
    pipeline_stage: RAGStage = Field(default=RAGStage.COMPLETE, description="Final pipeline stage reached")
    total_time: float = Field(..., description="Total processing time")
    sources_used: List[Dict[str, Any]] = Field(default_factory=list, description="Sources with metadata")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


@dataclass
class RAGConfig:
    """Configuration for RAG orchestrator."""
    # Component settings
    enable_query_processing: bool = True
    enable_reranking: bool = True
    enable_conversation_memory: bool = True
    
    # Retrieval settings
    default_top_k: int = 10
    max_context_docs: int = 5
    min_similarity_threshold: float = 0.1
    
    # Processing settings
    max_total_time: float = 30.0  # seconds
    fallback_on_error: bool = True
    preserve_debug_info: bool = False
    
    # Quality settings
    min_confidence_threshold: float = 0.3
    require_sources: bool = True