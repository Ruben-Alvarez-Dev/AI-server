"""
Memory-Server Integration for OpenCode
Provides seamless integration between OpenCode and Memory-Server
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import os

class OpenCodeMemoryIntegration:
    """Handles Memory-Server interactions for OpenCode"""
    
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
    
    async def search_code(
        self, 
        query: str, 
        workspace: Optional[str] = None, 
        limit: int = 10
    ) -> Dict[str, Any]:
        """Search for code in Memory-Server"""
        try:
            session = await self._get_session()
            params = {
                "query": query,
                "workspace": workspace or self.default_workspace,
                "limit": limit,
                "semantic": True
            }
            
            async with session.get(f"{self.api_url}/documents/search", params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "results": result.get("results", []),
                        "count": len(result.get("results", []))
                    }
                else:
                    return {"success": False, "error": f"Search failed with status {response.status}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def save_code_snippet(
        self,
        code: str,
        filename: str,
        language: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        workspace: Optional[str] = None
    ) -> Dict[str, Any]:
        """Save code snippet to Memory-Server"""
        try:
            session = await self._get_session()
            
            # Prepare content with metadata
            content = f"""# {filename}
Language: {language or 'unknown'}
Description: {description or 'Code snippet saved from OpenCode'}
Tags: {', '.join(tags) if tags else 'opencode, snippet'}

```{language or ''}
{code}
```

Saved from OpenCode at {datetime.now().isoformat()}
"""
            
            # Create form data
            data = aiohttp.FormData()
            data.add_field('file', content, filename=filename, content_type='text/plain')
            data.add_field('workspace', workspace or self.default_workspace)
            data.add_field('auto_summarize', 'true')
            
            if tags:
                tags.append('opencode')
                data.add_field('tags', ','.join(tags))
            else:
                data.add_field('tags', 'opencode,snippet')
            
            async with session.post(f"{self.api_url}/documents/upload", data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "document_id": result.get("document_id"),
                        "message": f"Code saved to Memory-Server: {result.get('document_id')}"
                    }
                else:
                    error_text = await response.text()
                    return {"success": False, "error": f"Upload failed: {error_text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_code_summary(
        self,
        code: str,
        summary_type: str = "technical"
    ) -> Dict[str, Any]:
        """Generate technical summary of code"""
        try:
            session = await self._get_session()
            
            data = {
                "content": code,
                "summary_type": summary_type,
                "workspace": self.default_workspace
            }
            
            async with session.post(f"{self.api_url}/documents/summarize/content", json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "summary": result.get("summary"),
                        "confidence": result.get("confidence", 0),
                        "type": result.get("summary_type")
                    }
                else:
                    error_text = await response.text()
                    return {"success": False, "error": f"Summarization failed: {error_text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def track_coding_session(
        self,
        files_edited: List[str],
        languages: List[str],
        duration_minutes: int,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Track coding session in Memory-Server"""
        try:
            session = await self._get_session()
            
            events = [{
                "type": "coding_session",
                "timestamp": int(datetime.now().timestamp() * 1000),
                "files_edited": files_edited,
                "languages": languages,
                "duration_minutes": duration_minutes,
                "description": description or "OpenCode coding session",
                "source": "opencode"
            }]
            
            data = {
                "workspace": self.default_workspace,
                "events": events,
                "source": "opencode",
                "auto_tag": True
            }
            
            async with session.post(f"{self.api_url}/documents/activity", json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "message": "Coding session tracked",
                        "document_id": result.get("document_id")
                    }
                else:
                    error_text = await response.text()
                    return {"success": False, "error": f"Activity tracking failed: {error_text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

# Singleton instance
memory = OpenCodeMemoryIntegration()

# Synchronous wrappers for OpenCode
def search_code(query: str, workspace: Optional[str] = None) -> Dict[str, Any]:
    """Search for code (sync wrapper)"""
    return asyncio.run(memory.search_code(query, workspace))

def save_snippet(code: str, filename: str, **kwargs) -> Dict[str, Any]:
    """Save code snippet (sync wrapper)"""
    return asyncio.run(memory.save_code_snippet(code, filename, **kwargs))

def summarize_code(code: str, summary_type: str = "technical") -> Dict[str, Any]:
    """Generate code summary (sync wrapper)"""
    return asyncio.run(memory.get_code_summary(code, summary_type))

def track_session(files: List[str], languages: List[str], duration: int, description: Optional[str] = None) -> Dict[str, Any]:
    """Track coding session (sync wrapper)"""
    return asyncio.run(memory.track_coding_session(files, languages, duration, description))