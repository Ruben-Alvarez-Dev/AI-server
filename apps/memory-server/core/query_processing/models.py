"""
Data models for query processing operations.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from dataclasses import dataclass
from enum import Enum


class QueryType(str, Enum):
    """Types of queries for different processing strategies."""
    FACTUAL = "factual"
    CONCEPTUAL = "conceptual"
    PROCEDURAL = "procedural"
    CODE_SEARCH = "code_search"
    DOCUMENT_SEARCH = "document_search"
    CONVERSATIONAL = "conversational"


class QueryIntent(str, Enum):
    """Query intents for routing."""
    SEARCH = "search"
    SUMMARIZE = "summarize"
    EXPLAIN = "explain"
    COMPARE = "compare"
    GENERATE = "generate"
    DEBUG = "debug"


class QueryRequest(BaseModel):
    """Request for query processing."""
    query: str = Field(..., description="Original user query")
    context: Optional[str] = Field(default=None, description="Conversation context")
    workspace: Optional[str] = Field(default=None, description="Target workspace")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class QueryResponse(BaseModel):
    """Response from query processing."""
    original_query: str = Field(..., description="Original query")
    processed_query: str = Field(..., description="Processed/enhanced query")
    query_type: QueryType = Field(..., description="Detected query type")
    intent: QueryIntent = Field(..., description="Detected intent")
    keywords: List[str] = Field(default_factory=list, description="Extracted keywords")
    entities: List[str] = Field(default_factory=list, description="Extracted entities")
    expanded_terms: List[str] = Field(default_factory=list, description="Additional search terms")
    confidence: float = Field(..., description="Processing confidence")
    processing_time: float = Field(..., description="Time taken for processing")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Processing metadata")


@dataclass
class QueryProcessorConfig:
    """Configuration for query processor."""
    enable_expansion: bool = True
    enable_entity_extraction: bool = True
    enable_intent_detection: bool = True
    max_expanded_terms: int = 10
    confidence_threshold: float = 0.5
    use_llm_processing: bool = True
    fallback_to_simple: bool = True