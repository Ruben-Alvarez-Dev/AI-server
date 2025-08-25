"""
Web Search Service for Memory-Server
Integrates Serper API and Firecrawl API for enhanced web search and scraping
"""

import os
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from urllib.parse import urlparse

from core.config import get_config
from core.logging_config import get_logger

logger = get_logger("web-search")
config = get_config()

@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    content: Optional[str] = None
    metadata: Dict[str, Any] = None

@dataclass
class SearchResponse:
    success: bool
    query: str
    results: List[SearchResult]
    total_results: int
    error: Optional[str] = None

class WebSearchService:
    """Enhanced web search using Serper API and Firecrawl API"""
    
    def __init__(self):
        self.serper_api_key = os.getenv("SERPER_API_KEY")
        self.firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
        
        if not self.serper_api_key:
            logger.warning("SERPER_API_KEY not found in environment variables")
            
        if not self.firecrawl_api_key:
            logger.warning("FIRECRAWL_API_KEY not found in environment variables")
    
    async def search_web(
        self, 
        query: str, 
        num_results: int = 10,
        search_type: str = "search",  # "search", "news", "images"
        include_content: bool = False
    ) -> SearchResponse:
        """
        Search the web using Serper API
        
        Args:
            query: Search query
            num_results: Number of results to return
            search_type: Type of search (search, news, images)
            include_content: Whether to fetch full content for each result
        """
        try:
            if not self.serper_api_key:
                return SearchResponse(
                    success=False,
                    query=query,
                    results=[],
                    total_results=0,
                    error="Serper API key not configured"
                )
            
            logger.info(f"Searching web for: {query}")
            
            # Serper API endpoint
            url = f"https://google.serper.dev/{search_type}"
            
            headers = {
                "X-API-KEY": self.serper_api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "q": query,
                "num": min(num_results, 100),  # Serper API limit
                "gl": "us",  # Country
                "hl": "en"   # Language
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Serper API error: {response.status} - {error_text}")
                        return SearchResponse(
                            success=False,
                            query=query,
                            results=[],
                            total_results=0,
                            error=f"Serper API error: {response.status}"
                        )
                    
                    data = await response.json()
                    
                    # Parse results
                    results = []
                    serper_results = data.get("organic", [])
                    
                    for result in serper_results[:num_results]:
                        search_result = SearchResult(
                            title=result.get("title", ""),
                            url=result.get("link", ""),
                            snippet=result.get("snippet", ""),
                            metadata={
                                "position": result.get("position"),
                                "date": result.get("date"),
                                "source": "serper"
                            }
                        )
                        
                        # Fetch full content if requested
                        if include_content:
                            content = await self._fetch_page_content(search_result.url)
                            search_result.content = content
                        
                        results.append(search_result)
                    
                    return SearchResponse(
                        success=True,
                        query=query,
                        results=results,
                        total_results=len(results),
                        error=None
                    )
                    
        except Exception as e:
            logger.error(f"Error in web search: {e}")
            return SearchResponse(
                success=False,
                query=query,
                results=[],
                total_results=0,
                error=str(e)
            )
    
    async def search_and_scrape(
        self,
        query: str,
        num_results: int = 5,
        scrape_content: bool = True
    ) -> SearchResponse:
        """Search web and automatically scrape content from results"""
        try:
            # First, search for results
            search_response = await self.search_web(
                query=query,
                num_results=num_results,
                include_content=False
            )
            
            if not search_response.success:
                return search_response
            
            # Then scrape content for each result
            if scrape_content:
                scraped_results = []
                
                for result in search_response.results:
                    try:
                        # Use Firecrawl for better content extraction
                        content = await self._scrape_with_firecrawl(result.url)
                        if not content:
                            # Fallback to simple fetch
                            content = await self._fetch_page_content(result.url)
                        
                        result.content = content
                        scraped_results.append(result)
                        
                        # Add delay to be respectful
                        await asyncio.sleep(1)
                        
                    except Exception as e:
                        logger.warning(f"Failed to scrape {result.url}: {e}")
                        scraped_results.append(result)  # Include without content
                
                search_response.results = scraped_results
            
            logger.info(f"Search and scrape completed: {len(search_response.results)} results")
            return search_response
            
        except Exception as e:
            logger.error(f"Error in search and scrape: {e}")
            return SearchResponse(
                success=False,
                query=query,
                results=[],
                total_results=0,
                error=str(e)
            )
    
    async def _scrape_with_firecrawl(self, url: str) -> Optional[str]:
        """Scrape content using Firecrawl API"""
        try:
            if not self.firecrawl_api_key:
                return None
                
            firecrawl_url = "https://api.firecrawl.dev/v0/scrape"
            
            headers = {
                "Authorization": f"Bearer {self.firecrawl_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "url": url,
                "formats": ["markdown", "html"],
                "includeTags": ["title", "meta", "article", "main", "content"],
                "excludeTags": ["nav", "footer", "aside", "header"],
                "onlyMainContent": True,
                "timeout": 30000
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(firecrawl_url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get("success"):
                            # Get markdown content if available
                            content = data.get("data", {}).get("markdown", "")
                            if not content:
                                # Fallback to HTML
                                content = data.get("data", {}).get("html", "")
                            
                            logger.debug(f"Firecrawl scraped content from {url}: {len(content)} chars")
                            return content
                        else:
                            logger.warning(f"Firecrawl failed for {url}: {data.get('error')}")
                    else:
                        logger.warning(f"Firecrawl API error for {url}: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error scraping with Firecrawl {url}: {e}")
        
        return None
    
    async def _fetch_page_content(self, url: str) -> Optional[str]:
        """Simple content fetching fallback"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # Basic content cleaning
                        import re
                        # Remove script and style tags
                        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
                        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
                        
                        # Convert to basic text
                        content = re.sub(r'<[^>]+>', ' ', content)
                        content = re.sub(r'\s+', ' ', content).strip()
                        
                        return content[:10000]  # Limit to 10K chars
                        
        except Exception as e:
            logger.error(f"Error fetching content from {url}: {e}")
        
        return None
    
    async def search_for_documentation(self, topic: str, num_results: int = 5) -> SearchResponse:
        """Search specifically for documentation about a topic"""
        
        # Enhance query for documentation
        enhanced_query = f"{topic} documentation tutorial guide api reference"
        
        return await self.search_and_scrape(
            query=enhanced_query,
            num_results=num_results,
            scrape_content=True
        )
    
    async def search_for_code_examples(self, topic: str, language: str = "", num_results: int = 5) -> SearchResponse:
        """Search for code examples"""
        
        # Enhance query for code examples
        if language:
            enhanced_query = f"{topic} {language} code example tutorial github"
        else:
            enhanced_query = f"{topic} code example tutorial github"
        
        return await self.search_and_scrape(
            query=enhanced_query,
            num_results=num_results,
            scrape_content=True
        )
    
    async def search_forums(self, topic: str, forum: str = "", num_results: int = 5) -> SearchResponse:
        """Search forums and community sites"""
        
        # Common forums and community sites
        forum_sites = {
            "reddit": "site:reddit.com",
            "stackoverflow": "site:stackoverflow.com",
            "github": "site:github.com",
            "discord": "site:discord.com",
            "hackernews": "site:news.ycombinator.com"
        }
        
        site_filter = forum_sites.get(forum.lower(), forum if forum else "")
        
        if site_filter:
            enhanced_query = f"{topic} {site_filter}"
        else:
            enhanced_query = f"{topic} forum discussion community reddit stackoverflow"
        
        return await self.search_and_scrape(
            query=enhanced_query,
            num_results=num_results,
            scrape_content=True
        )
    
    def is_configured(self) -> Dict[str, bool]:
        """Check which APIs are configured"""
        return {
            "serper": bool(self.serper_api_key),
            "firecrawl": bool(self.firecrawl_api_key)
        }