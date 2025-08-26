"""
Memory-Server Integration for Open Interpreter
Provides seamless integration between Open Interpreter and Memory-Server
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import os

class MemoryServerIntegration:
    """Handles all Memory-Server interactions for Open Interpreter"""
    
    def __init__(self, base_url: str = "http://localhost:8001", default_workspace: str = "code"):
        self.base_url = base_url.rstrip('/')
        self.api_url = f"{self.base_url}/api/v1"
        self.default_workspace = default_workspace
        self.session = None
    
    async def _get_session(self):
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def search_memory(self, query: str, workspace: Optional[str] = None, limit: int = 5) -> Dict[str, Any]:
        """Search documents in Memory-Server"""
        try:
            session = await self._get_session()
            params = {
                "query": query,
                "limit": limit,
                "semantic": True
            }
            if workspace:
                params["workspace"] = workspace
            
            async with session.get(f"{self.api_url}/documents/search", params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"Search failed with status {response.status}"}
        except Exception as e:
            return {"error": f"Search failed: {str(e)}"}
    
    async def upload_content(
        self, 
        content: str, 
        filename: str, 
        workspace: Optional[str] = None,
        tags: Optional[List[str]] = None,
        auto_summarize: bool = True
    ) -> Dict[str, Any]:
        """Upload content to Memory-Server"""
        try:
            session = await self._get_session()
            
            # Create form data
            data = aiohttp.FormData()
            data.add_field('file', content, filename=filename, content_type='text/plain')
            data.add_field('workspace', workspace or self.default_workspace)
            data.add_field('auto_summarize', str(auto_summarize).lower())
            
            if tags:
                data.add_field('tags', ','.join(tags))
            
            async with session.post(f"{self.api_url}/documents/upload", data=data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    return {"error": f"Upload failed with status {response.status}: {error_text}"}
        except Exception as e:
            return {"error": f"Upload failed: {str(e)}"}
    
    async def summarize_content(
        self, 
        content: str, 
        summary_type: str = "technical",
        workspace: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate summary using Memory-Server"""
        try:
            session = await self._get_session()
            
            data = {
                "content": content,
                "summary_type": summary_type,
                "workspace": workspace or self.default_workspace
            }
            
            async with session.post(f"{self.api_url}/documents/summarize/content", json=data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    return {"error": f"Summarization failed with status {response.status}: {error_text}"}
        except Exception as e:
            return {"error": f"Summarization failed: {str(e)}"}
    
    async def list_workspaces(self) -> Dict[str, Any]:
        """List all available workspaces"""
        try:
            session = await self._get_session()
            
            async with session.get(f"{self.api_url}/documents/workspaces") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"Failed to list workspaces: status {response.status}"}
        except Exception as e:
            return {"error": f"Failed to list workspaces: {str(e)}"}
    
    async def track_activity(
        self, 
        activity_type: str, 
        content: str, 
        metadata: Optional[Dict[str, Any]] = None,
        workspace: Optional[str] = None
    ) -> Dict[str, Any]:
        """Track development activity"""
        try:
            session = await self._get_session()
            
            event = {
                "type": activity_type,
                "timestamp": int(datetime.now().timestamp() * 1000),
                "content": content,
                "source": "open-interpreter",
                **(metadata or {})
            }
            
            data = {
                "workspace": workspace or self.default_workspace,
                "events": [event],
                "source": "open-interpreter",
                "auto_tag": True
            }
            
            async with session.post(f"{self.api_url}/documents/activity", json=data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    return {"error": f"Activity tracking failed: status {response.status}: {error_text}"}
        except Exception as e:
            return {"error": f"Activity tracking failed: {str(e)}"}
    
    async def web_search(
        self, 
        query: str, 
        search_type: str = "code",
        workspace: Optional[str] = None,
        auto_ingest: bool = False
    ) -> Dict[str, Any]:
        """Perform web search via Memory-Server"""
        try:
            session = await self._get_session()
            
            data = {
                "query": query,
                "search_type": search_type,
                "workspace": workspace or "research",
                "auto_ingest": auto_ingest,
                "num_results": 5
            }
            
            async with session.post(f"{self.api_url}/search/web", json=data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    return {"error": f"Web search failed: status {response.status}: {error_text}"}
        except Exception as e:
            return {"error": f"Web search failed: {str(e)}"}

# Singleton instance for Open Interpreter
memory_server = MemoryServerIntegration()

# Wrapper functions for easy integration
def search_memory(query: str, workspace: Optional[str] = None, limit: int = 5) -> Dict[str, Any]:
    """Synchronous wrapper for memory search"""
    return asyncio.run(memory_server.search_memory(query, workspace, limit))

def upload_content(content: str, filename: str, workspace: Optional[str] = None, tags: Optional[List[str]] = None) -> Dict[str, Any]:
    """Synchronous wrapper for content upload"""
    return asyncio.run(memory_server.upload_content(content, filename, workspace, tags))

def summarize_content(content: str, summary_type: str = "technical", workspace: Optional[str] = None) -> Dict[str, Any]:
    """Synchronous wrapper for content summarization"""
    return asyncio.run(memory_server.summarize_content(content, summary_type, workspace))

def list_workspaces() -> Dict[str, Any]:
    """Synchronous wrapper for listing workspaces"""
    return asyncio.run(memory_server.list_workspaces())

def track_activity(activity_type: str, content: str, metadata: Optional[Dict[str, Any]] = None, workspace: Optional[str] = None) -> Dict[str, Any]:
    """Synchronous wrapper for activity tracking"""
    return asyncio.run(memory_server.track_activity(activity_type, content, metadata, workspace))

def web_search(query: str, search_type: str = "code", workspace: Optional[str] = None, auto_ingest: bool = False) -> Dict[str, Any]:
    """Synchronous wrapper for web search"""
    return asyncio.run(memory_server.web_search(query, search_type, workspace, auto_ingest))