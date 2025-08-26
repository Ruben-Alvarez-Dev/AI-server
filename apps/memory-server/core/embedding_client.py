"""
Embedding Hub Client
Client for connecting Memory-Server to the centralized Embedding Hub service
Handles 6 specialized embedding types with automatic agent selection
"""

import asyncio
import aiohttp
import logging
from typing import Dict, Any, List, Union, Optional
from dataclasses import dataclass
from enum import Enum
import time
import json

from core.config import get_config
from core.logging_config import get_logger

# Setup logger
logger = get_logger("embedding-client")

class EmbeddingAgent(str, Enum):
    """Available embedding agents"""
    LATE_CHUNKING = "late_chunking"
    CODE = "code"
    CONVERSATION = "conversation"
    VISUAL = "visual"
    QUERY = "query"
    COMMUNITY = "community"

@dataclass
class EmbeddingRequest:
    """Request to embedding hub"""
    content: str
    content_type: str = "text"
    metadata: Optional[Dict[str, Any]] = None
    agent: Optional[EmbeddingAgent] = None

@dataclass
class EmbeddingResponse:
    """Response from embedding hub"""
    embeddings: List[float]
    dimensions: int
    agent: str
    processing_time_ms: float
    metadata: Optional[Dict[str, Any]] = None

class EmbeddingHubClient:
    """
    Client for Embedding Hub service
    
    Automatically selects appropriate agent based on content type and metadata
    Provides fallback strategies and connection pooling
    """
    
    def __init__(self, hub_host: str = "localhost", hub_port: int = 8900):
        self.config = get_config()
        self.hub_base_url = f"http://{hub_host}:{hub_port}"
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Agent endpoint mappings
        self.agent_endpoints = {
            EmbeddingAgent.LATE_CHUNKING: "/embed/late-chunking",
            EmbeddingAgent.CODE: "/embed/code", 
            EmbeddingAgent.CONVERSATION: "/embed/conversation",
            EmbeddingAgent.VISUAL: "/embed/visual",
            EmbeddingAgent.QUERY: "/embed/query",
            EmbeddingAgent.COMMUNITY: "/embed/community"
        }
        
        # Connection settings
        self.timeout = aiohttp.ClientTimeout(total=30.0)
        self.max_retries = 3
        self.retry_delay = 1.0
        
        # Statistics
        self.stats = {
            "requests_sent": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_processing_time_ms": 0.0,
            "agent_usage": {}
        }
        
        logger.info(f"Embedding Hub Client initialized - Hub URL: {self.hub_base_url}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def initialize(self):
        """Initialize the client session"""
        if self.session is None:
            connector = aiohttp.TCPConnector(
                limit=100,  # Connection pool size
                limit_per_host=20,
                ttl_dns_cache=300,
                ttl_connection_cache=300
            )
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            
            # Test connection
            try:
                await self.health_check()
                logger.info("Connected to Embedding Hub successfully")
            except Exception as e:
                logger.warning(f"Could not connect to Embedding Hub: {e}")
    
    async def close(self):
        """Close the client session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Embedding Hub health"""
        if not self.session:
            await self.initialize()
        
        async with self.session.get(f"{self.hub_base_url}/health") as response:
            if response.status == 200:
                return await response.json()
            else:
                raise ConnectionError(f"Embedding Hub health check failed: {response.status}")
    
    async def get_hub_status(self) -> Dict[str, Any]:
        """Get comprehensive hub status"""
        if not self.session:
            await self.initialize()
        
        async with self.session.get(f"{self.hub_base_url}/status") as response:
            if response.status == 200:
                return await response.json()
            else:
                raise ConnectionError(f"Could not get hub status: {response.status}")
    
    async def embed(self, 
                   content: Union[str, List[str]], 
                   content_type: str = "text",
                   metadata: Optional[Dict[str, Any]] = None,
                   agent: Optional[EmbeddingAgent] = None) -> Union[List[float], List[List[float]]]:
        """
        Generate embeddings using appropriate agent
        
        Args:
            content: Text content or list of texts
            content_type: Type of content (text, code, conversation, etc.)
            metadata: Additional metadata for processing
            agent: Force specific agent (auto-select if None)
            
        Returns:
            Embeddings as list of floats or list of lists
        """
        
        if not self.session:
            await self.initialize()
        
        # Handle batch requests
        if isinstance(content, list):
            return await self._embed_batch(content, content_type, metadata, agent)
        
        # Select agent if not specified
        if agent is None:
            agent = self._select_agent(content, content_type, metadata)
        
        request = EmbeddingRequest(
            content=content,
            content_type=content_type,
            metadata=metadata or {},
            agent=agent
        )
        
        response = await self._send_embedding_request(request)
        
        # Update statistics
        self.stats["requests_sent"] += 1
        self.stats["successful_requests"] += 1
        self.stats["total_processing_time_ms"] += response.processing_time_ms
        self.stats["agent_usage"][agent.value] = self.stats["agent_usage"].get(agent.value, 0) + 1
        
        return response.embeddings
    
    async def _embed_batch(self, 
                          contents: List[str],
                          content_type: str,
                          metadata: Optional[Dict[str, Any]],
                          agent: Optional[EmbeddingAgent]) -> List[List[float]]:
        """Process multiple texts in parallel"""
        
        # Group by agent if auto-selecting
        if agent is None:
            agent_groups = {}
            for i, content in enumerate(contents):
                selected_agent = self._select_agent(content, content_type, metadata)
                if selected_agent not in agent_groups:
                    agent_groups[selected_agent] = []
                agent_groups[selected_agent].append((i, content))
            
            # Process each group
            tasks = []
            for group_agent, group_contents in agent_groups.items():
                for idx, content in group_contents:
                    task = self.embed(content, content_type, metadata, group_agent)
                    tasks.append((idx, task))
            
            # Wait for all tasks
            results = [None] * len(contents)
            for idx, task in tasks:
                results[idx] = await task
            
            return results
        else:
            # Use same agent for all
            tasks = [self.embed(content, content_type, metadata, agent) for content in contents]
            return await asyncio.gather(*tasks)
    
    def _select_agent(self, 
                     content: str, 
                     content_type: str,
                     metadata: Optional[Dict[str, Any]]) -> EmbeddingAgent:
        """
        Automatically select appropriate embedding agent
        
        Selection logic based on content analysis and metadata
        """
        
        content_lower = content.lower()
        metadata = metadata or {}
        
        # Check metadata for explicit hints
        if 'agent_hint' in metadata:
            hint = metadata['agent_hint'].lower()
            for agent in EmbeddingAgent:
                if hint == agent.value:
                    return agent
        
        # Check content type
        if content_type == "code" or 'language' in metadata:
            return EmbeddingAgent.CODE
        
        if content_type == "conversation" or content_type == "dialogue":
            return EmbeddingAgent.CONVERSATION
        
        if content_type == "visual" or content_type == "image":
            return EmbeddingAgent.VISUAL
        
        if content_type == "query" or content_type == "search":
            return EmbeddingAgent.QUERY
        
        # Content-based detection
        
        # Check for code patterns
        if any(pattern in content for pattern in ['def ', 'function ', 'class ', 'import ', 'from ']):
            return EmbeddingAgent.CODE
        
        # Check for conversation patterns  
        if any(pattern in content_lower for pattern in ['user:', 'assistant:', 'human:', 'ai:', '> ']):
            return EmbeddingAgent.CONVERSATION
        
        # Check for query patterns
        if (content.strip().endswith('?') or 
            any(pattern in content_lower for pattern in ['how to', 'what is', 'why does', 'when should'])):
            return EmbeddingAgent.QUERY
        
        # Check for visual content
        if any(pattern in content_lower for pattern in ['screenshot', 'image', 'visual', 'ui', 'interface']):
            return EmbeddingAgent.VISUAL
        
        # Check for community/graph content
        if (any(pattern in content for pattern in ['[ENTITY:', 'relationship', 'community', 'cluster']) or
            metadata.get('use_case') == 'community_detection'):
            return EmbeddingAgent.COMMUNITY
        
        # Check for document chunking
        if (len(content) > 2000 or 
            metadata.get('use_case') == 'document_chunking' or
            'paragraph' in content_lower or 'section' in content_lower):
            return EmbeddingAgent.LATE_CHUNKING
        
        # Default to late chunking for general text
        return EmbeddingAgent.LATE_CHUNKING
    
    async def _send_embedding_request(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Send request to embedding hub with retry logic"""
        
        endpoint = self.agent_endpoints[request.agent]
        url = f"{self.hub_base_url}{endpoint}"
        
        payload = {
            "content": request.content,
            "content_type": request.content_type,
            "metadata": request.metadata
        }
        
        for attempt in range(self.max_retries):
            try:
                async with self.session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return EmbeddingResponse(
                            embeddings=data["embeddings"],
                            dimensions=data["dimensions"],
                            agent=data["agent"],
                            processing_time_ms=data["processing_time_ms"],
                            metadata=data.get("metadata")
                        )
                    else:
                        error_text = await response.text()
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status,
                            message=error_text
                        )
                        
            except asyncio.TimeoutError:
                logger.warning(f"Timeout on attempt {attempt + 1}/{self.max_retries} for {request.agent}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise
            
            except aiohttp.ClientError as e:
                logger.warning(f"Client error on attempt {attempt + 1}/{self.max_retries}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                else:
                    self.stats["failed_requests"] += 1
                    raise
        
        raise RuntimeError(f"Failed to get embeddings after {self.max_retries} attempts")
    
    def get_client_stats(self) -> Dict[str, Any]:
        """Get client usage statistics"""
        
        success_rate = (
            self.stats["successful_requests"] / max(self.stats["requests_sent"], 1) * 100
        )
        
        avg_processing_time = (
            self.stats["total_processing_time_ms"] / max(self.stats["successful_requests"], 1)
        )
        
        return {
            "hub_url": self.hub_base_url,
            "requests_sent": self.stats["requests_sent"],
            "successful_requests": self.stats["successful_requests"],
            "failed_requests": self.stats["failed_requests"],
            "success_rate_percent": success_rate,
            "average_processing_time_ms": avg_processing_time,
            "agent_usage": self.stats["agent_usage"],
            "connection_active": self.session is not None and not self.session.closed
        }
    
    async def embed_for_chunking(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> List[float]:
        """Specialized method for Late Chunking operations"""
        return await self.embed(
            content=content,
            content_type="document",
            metadata={**(metadata or {}), "use_case": "document_chunking"},
            agent=EmbeddingAgent.LATE_CHUNKING
        )
    
    async def embed_code(self, code: str, language: str, metadata: Optional[Dict[str, Any]] = None) -> List[float]:
        """Specialized method for code embedding"""
        return await self.embed(
            content=code,
            content_type="code",
            metadata={**(metadata or {}), "language": language},
            agent=EmbeddingAgent.CODE
        )
    
    async def embed_conversation(self, conversation: str, metadata: Optional[Dict[str, Any]] = None) -> List[float]:
        """Specialized method for conversation embedding"""
        return await self.embed(
            content=conversation,
            content_type="conversation",
            metadata=metadata,
            agent=EmbeddingAgent.CONVERSATION
        )
    
    async def embed_query(self, query: str, metadata: Optional[Dict[str, Any]] = None) -> List[float]:
        """Specialized method for search queries"""
        return await self.embed(
            content=query,
            content_type="query", 
            metadata=metadata,
            agent=EmbeddingAgent.QUERY
        )
    
    async def embed_for_community_detection(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> List[float]:
        """Specialized method for community detection in graphs"""
        return await self.embed(
            content=content,
            content_type="text",
            metadata={**(metadata or {}), "use_case": "community_detection"},
            agent=EmbeddingAgent.COMMUNITY
        )

# Singleton instance for easy import
_embedding_client = None

async def get_embedding_client() -> EmbeddingHubClient:
    """Get singleton embedding client"""
    global _embedding_client
    
    if _embedding_client is None:
        config = get_config()
        _embedding_client = EmbeddingHubClient(
            hub_host=config.EMBEDDING_HUB_HOST,
            hub_port=config.EMBEDDING_HUB_PORT
        )
        await _embedding_client.initialize()
    
    return _embedding_client

async def close_embedding_client():
    """Close singleton embedding client"""
    global _embedding_client
    
    if _embedding_client is not None:
        await _embedding_client.close()
        _embedding_client = None