"""
ATLAS Public Interface Client
Provides public API functions for ATLAS black-box system.
ONLY contains public interfaces - internal implementation is opaque.
"""

from typing import Dict, Any, Optional
import asyncio
import aiohttp
import logging

logger = logging.getLogger(__name__)


class AtlasClient:
    """
    ATLAS public interface client.
    All internal implementation details are completely opaque.
    """
    
    def __init__(self, base_url: str = "http://localhost:8004", timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
        self._session = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()


async def atlas_process(
    input_data: str,
    mode: str = "default",
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Process content through ATLAS black-box system.
    
    Args:
        input_data: Content to process
        mode: Processing mode ('default', 'enhance', 'analyze')
        options: Additional processing options
        
    Returns:
        Dict containing processed result and metadata
        
    Note:
        Internal processing is completely opaque - only public interface documented.
    """
    if options is None:
        options = {}
    
    async with AtlasClient() as client:
        payload = {
            "input": input_data,
            "mode": mode,
            "options": options
        }
        
        async with client._session.post(
            f"{client.base_url}/atlas/v1/process",
            json=payload
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise AtlasError(f"ATLAS processing failed: {response.status}")


async def atlas_enhance(
    content: str,
    enhancement_type: str = "quality",
    parameters: Optional[Dict[str, Any]] = None
) -> str:
    """
    Enhance content quality through ATLAS.
    
    Args:
        content: Content to enhance
        enhancement_type: Type of enhancement ('quality', 'clarity', 'structure')
        parameters: Enhancement parameters
        
    Returns:
        Enhanced content string
        
    Note:
        Enhancement algorithms are black-box - implementation not documented.
    """
    if parameters is None:
        parameters = {}
    
    result = await atlas_process(
        input_data=content,
        mode="enhance",
        options={
            "enhancement_type": enhancement_type,
            **parameters
        }
    )
    
    return result.get("enhanced_content", content)


async def atlas_status() -> Dict[str, Any]:
    """
    Get ATLAS system status.
    
    Returns:
        Dict containing public status information
        
    Note:
        Only public status exposed - internal metrics are opaque.
    """
    async with AtlasClient() as client:
        async with client._session.get(
            f"{client.base_url}/atlas/v1/status"
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise AtlasError(f"ATLAS status check failed: {response.status}")


async def atlas_health() -> bool:
    """
    Check ATLAS health status.
    
    Returns:
        True if ATLAS is healthy, False otherwise
    """
    try:
        async with AtlasClient() as client:
            async with client._session.get(
                f"{client.base_url}/atlas/health"
            ) as response:
                return response.status == 200
    except Exception:
        return False


class AtlasError(Exception):
    """Exception raised by ATLAS public interface."""
    pass


# Public interface exports
__all__ = [
    'AtlasClient',
    'atlas_process', 
    'atlas_enhance',
    'atlas_status',
    'atlas_health',
    'AtlasError'
]