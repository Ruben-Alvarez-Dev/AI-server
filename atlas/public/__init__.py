"""
ATLAS Public Interface Package
Provides access to ATLAS black-box system through documented public APIs.

IMPORTANT: 
- Only public interfaces are documented and accessible
- Internal implementation (/atlas/core/) is completely opaque
- All functionality provided through these public interfaces

Usage:
    from atlas.public.interfaces import atlas_process, atlas_enhance
    from atlas.public.schemas import AtlasProcessRequest
"""

from .interfaces.atlas_client import (
    atlas_process,
    atlas_enhance, 
    atlas_status,
    atlas_health,
    AtlasClient,
    AtlasError
)

from .schemas.atlas_schemas import (
    ProcessingMode,
    EnhancementType,
    AtlasProcessRequest,
    AtlasProcessResponse,
    AtlasEnhanceRequest,
    AtlasEnhanceResponse,
    AtlasStatusResponse,
    AtlasHealthResponse,
    AtlasErrorResponse
)

# Public API exports
__all__ = [
    # Client functions
    'atlas_process',
    'atlas_enhance',
    'atlas_status', 
    'atlas_health',
    'AtlasClient',
    'AtlasError',
    
    # Schema classes
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

# Version info
__version__ = "1.0.0"
__author__ = "Ruben-Alvarez-Dev"

# Note: Internal ATLAS implementation is completely opaque