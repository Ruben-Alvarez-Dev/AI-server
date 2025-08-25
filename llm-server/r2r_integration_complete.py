#!/usr/bin/env python3
"""
R2R Integration for LLM Server
Connects our LLM Server with R2R RAG system for enhanced knowledge retrieval
"""

import asyncio
import aiohttp
import json
import logging
from typing import List, Dict, Optional, Any
from pathlib import Path
import time

logger = logging.getLogger(__name__)

class R2RClient:
    """Client to interact with R2R API"""
    
    def __init__(self, base_url: str = "http://localhost:7272", api_key: str = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    async def health_check(self) -> bool:
        """Check if R2R server is healthy"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"R2R health check failed: {e}")
            return False
    
    async def search_documents(
        self, 
        query: str, 
        limit: int = 10,
        collection_name: str = "Default"
    ) -> List[Dict[str, Any]]:
        """Search documents using vector similarity"""
        try:
            payload = {
                "query": query,
                "limit": limit,
                "collection_name": collection_name
            }
            
            async with self.session.post(
                f"{self.base_url}/v3/search",
                json=payload,
                headers=self._get_headers()
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("results", [])
                else:
                    logger.error(f"R2R search failed: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"R2R search error: {e}")
            return []
    
    async def ingest_text(
        self, 
        text: str, 
        document_id: str = None,
        metadata: Dict[str, Any] = None,
        collection_name: str = "Default"
    ) -> bool:
        """Ingest text content into R2R"""
        try:
            payload = {
                "text": text,
                "document_id": document_id,
                "metadata": metadata or {},
                "collection_name": collection_name
            }
            
            async with self.session.post(
                f"{self.base_url}/v3/ingest_text",
                json=payload,
                headers=self._get_headers()
            ) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"R2R ingest error: {e}")
            return False

class R2REnhancedLLMServer:
    """Enhanced LLM Server with R2R RAG capabilities"""
    
    def __init__(self, r2r_url: str = "http://localhost:7272"):
        self.r2r_url = r2r_url
        self.r2r_available = False
    
    async def check_r2r_availability(self) -> bool:
        """Check if R2R is available"""
        try:
            async with R2RClient(self.r2r_url) as r2r:
                self.r2r_available = await r2r.health_check()
                return self.r2r_available
        except Exception as e:
            logger.error(f"R2R availability check failed: {e}")
            self.r2r_available = False
            return False
    
    async def enhance_prompt_with_rag(
        self, 
        user_query: str, 
        context_limit: int = 5,
        collection_name: str = "Default"
    ) -> str:
        """Enhance user prompt with RAG context from R2R"""
        
        if not self.r2r_available:
            await self.check_r2r_availability()
        
        if not self.r2r_available:
            logger.warning("R2R not available, proceeding without RAG context")
            return user_query
        
        try:
            async with R2RClient(self.r2r_url) as r2r:
                # Search for relevant documents
                search_results = await r2r.search_documents(
                    query=user_query,
                    limit=context_limit,
                    collection_name=collection_name
                )
                
                if not search_results:
                    return user_query
                
                # Build enhanced prompt with context
                context_sections = []
                for i, result in enumerate(search_results[:context_limit]):
                    score = result.get('score', 0.0)
                    text = result.get('text', '')
                    metadata = result.get('metadata', {})
                    
                    if text and score > 0.3:  # Only include relevant results
                        context_sections.append(f"""
**Context {i+1}** (Relevance: {score:.2f})
Source: {metadata.get('filename', 'Unknown')}
---
{text[:1000]}{'...' if len(text) > 1000 else ''}
""")
                
                if context_sections:
                    enhanced_prompt = f"""Based on the following relevant information from your knowledge base:

{chr(10).join(context_sections)}

---

Now, please answer this question: {user_query}

Use the context above to provide a more accurate and detailed response. If the context doesn't contain relevant information, please indicate that and answer based on your general knowledge."""

                    return enhanced_prompt
                
        except Exception as e:
            logger.error(f"RAG enhancement failed: {e}")
        
        return user_query
    
    async def ingest_conversation_to_r2r(
        self, 
        user_message: str, 
        assistant_response: str,
        session_id: str = None,
        collection_name: str = "Conversations"
    ) -> bool:
        """Store conversation in R2R for future reference"""
        
        if not self.r2r_available:
            return False
        
        try:
            async with R2RClient(self.r2r_url) as r2r:
                conversation_text = f"""User: {user_message}