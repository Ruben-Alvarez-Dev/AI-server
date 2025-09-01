"""
ATLAS Public Schema Definitions
Defines request/response schemas for ATLAS public interfaces.
Internal data structures are not documented (black-box compliance).
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from enum import Enum


class ProcessingMode(str, Enum):
    """Available ATLAS processing modes."""
    DEFAULT = "default"
    ENHANCE = "enhance" 
    ANALYZE = "analyze"
    OPTIMIZE = "optimize"


class EnhancementType(str, Enum):
    """Available enhancement types."""
    QUALITY = "quality"
    CLARITY = "clarity"
    STRUCTURE = "structure"
    COHERENCE = "coherence"


class AtlasProcessRequest(BaseModel):
    """Request schema for ATLAS processing endpoint."""
    input: str = Field(..., description="Content to process")
    mode: ProcessingMode = Field(default=ProcessingMode.DEFAULT, description="Processing mode")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Processing options")
    
    class Config:
        json_encoders = {
            ProcessingMode: lambda v: v.value,
            EnhancementType: lambda v: v.value
        }


class AtlasProcessResponse(BaseModel):
    """Response schema for ATLAS processing endpoint."""
    success: bool = Field(..., description="Processing success status")
    result: str = Field(..., description="Processed content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Processing metadata")
    processing_time_ms: Optional[float] = Field(None, description="Processing duration")
    
    # Note: Internal processing details are not exposed (black-box)


class AtlasEnhanceRequest(BaseModel):
    """Request schema for ATLAS enhancement endpoint."""
    content: str = Field(..., description="Content to enhance")
    enhancement_type: EnhancementType = Field(default=EnhancementType.QUALITY, description="Enhancement type")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Enhancement parameters")
    
    class Config:
        json_encoders = {
            EnhancementType: lambda v: v.value
        }


class AtlasEnhanceResponse(BaseModel):
    """Response schema for ATLAS enhancement endpoint."""
    success: bool = Field(..., description="Enhancement success status")
    enhanced_content: str = Field(..., description="Enhanced content")
    improvements: List[str] = Field(default_factory=list, description="List of improvements applied")
    confidence_score: Optional[float] = Field(None, description="Enhancement confidence (0-1)")
    
    # Note: Enhancement algorithms are black-box - no internal details exposed


class AtlasStatusResponse(BaseModel):
    """Response schema for ATLAS status endpoint."""
    status: str = Field(..., description="System status (healthy, degraded, offline)")
    version: str = Field(..., description="ATLAS version")
    uptime_seconds: float = Field(..., description="System uptime")
    public_endpoints: List[str] = Field(..., description="Available public endpoints")
    
    # Note: Internal metrics and state are not exposed


class AtlasHealthResponse(BaseModel):
    """Response schema for ATLAS health endpoint."""
    healthy: bool = Field(..., description="Health status")
    timestamp: str = Field(..., description="Health check timestamp")
    response_time_ms: Optional[float] = Field(None, description="Health check response time")


class AtlasErrorResponse(BaseModel):
    """Error response schema for all ATLAS endpoints."""
    error: bool = Field(default=True, description="Error flag")
    message: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    timestamp: str = Field(..., description="Error timestamp")
    
    # Note: Internal error details are not exposed for security


# Schema exports
__all__ = [
    'ProcessingMode',
    'EnhancementType', 
    'AtlasProcessRequest',
    'AtlasProcessResponse',
    'AtlasEnhanceRequest',
    'AtlasEnhanceResponse',
    'AtlasStatusResponse',
    'AtlasHealthResponse',
    'AtlasErrorResponse'
]