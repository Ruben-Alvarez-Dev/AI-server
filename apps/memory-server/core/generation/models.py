"""
Data models for text generation operations.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from dataclasses import dataclass
from enum import Enum


class GenerationMode(str, Enum):
    """Generation modes for different use cases."""
    RAG_ANSWER = "rag_answer"
    SUMMARIZATION = "summarization"
    QUERY_EXPANSION = "query_expansion"
    CODE_EXPLANATION = "code_explanation"


class GenerationRequest(BaseModel):
    """Request for text generation."""
    query: str = Field(..., description="User query")
    context: Optional[List[str]] = Field(default=None, description="Retrieved context documents")
    mode: GenerationMode = Field(default=GenerationMode.RAG_ANSWER, description="Generation mode")
    max_tokens: Optional[int] = Field(default=512, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(default=0.7, description="Generation temperature")
    system_prompt: Optional[str] = Field(default=None, description="Custom system prompt")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class GenerationResponse(BaseModel):
    """Response from text generation."""
    answer: str = Field(..., description="Generated answer")
    confidence: float = Field(..., description="Confidence score")
    sources_used: List[int] = Field(default_factory=list, description="Indices of context sources used")
    token_count: int = Field(..., description="Number of tokens generated")
    generation_time: float = Field(..., description="Time taken for generation")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


@dataclass
class GeneratorConfig:
    """Configuration for text generator."""
    model_name: str = "Qwen/Qwen2.5-Coder-7B-Instruct"
    device: str = "cpu"
    max_context_length: int = 4096
    max_new_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    do_sample: bool = True
    cache_dir: Optional[str] = None
    trust_remote_code: bool = True
    torch_dtype: str = "auto"