"""
Web Search Router for Memory-Server API
Provides endpoints for web search, scraping, and knowledge discovery
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict, Any
from enum import Enum

from core.logging_config import get_logger
from api.utils.web_search import WebSearchService, SearchResponse, SearchResult

logger = get_logger("web-search-router")

# Initialize router
router = APIRouter(prefix="/api/v1/search", tags=["Web Search"])

# Initialize services
web_search_service = WebSearchService()

class SearchType(str, Enum):
    SEARCH = "search"
    NEWS = "news"
    IMAGES = "images"

class WebSearchRequest(BaseModel):
    query: str = Field(..., description="Search query", min_length=1)
    num_results: int = Field(default=10, ge=1, le=50, description="Number of results to return")
    search_type: SearchType = Field(default=SearchType.SEARCH, description="Type of search")
    include_content: bool = Field(default=False, description="Whether to fetch full page content")

class SearchAndScrapeRequest(BaseModel):
    query: str = Field(..., description="Search query", min_length=1)
    num_results: int = Field(default=5, ge=1, le=20, description="Number of results to scrape")
    workspace: str = Field(default="research", description="Workspace to store scraped content")
    auto_ingest: bool = Field(default=False, description="Automatically ingest scraped content")

class DocumentationSearchRequest(BaseModel):
    topic: str = Field(..., description="Topic to search documentation for", min_length=1)
    num_results: int = Field(default=5, ge=1, le=15, description="Number of results")
    workspace: str = Field(default="research", description="Workspace for results")
    auto_ingest: bool = Field(default=False, description="Auto-ingest results")

class CodeSearchRequest(BaseModel):
    topic: str = Field(..., description="Topic for code examples", min_length=1)
    language: str = Field(default="", description="Programming language filter")
    num_results: int = Field(default=5, ge=1, le=15, description="Number of results")
    workspace: str = Field(default="code", description="Workspace for code examples")
    auto_ingest: bool = Field(default=False, description="Auto-ingest results")

class ForumSearchRequest(BaseModel):
    topic: str = Field(..., description="Topic to search in forums", min_length=1)
    forum: str = Field(default="", description="Specific forum (reddit, stackoverflow, github, etc.)")
    num_results: int = Field(default=5, ge=1, le=15, description="Number of results")
    workspace: str = Field(default="research", description="Workspace for results")
    auto_ingest: bool = Field(default=False, description="Auto-ingest results")

class WebSearchResponse(BaseModel):
    success: bool
    query: str
    results: List[Dict[str, Any]]
    total_results: int
    error: Optional[str] = None
    search_type: str
    execution_time: Optional[float] = None

class SearchConfigResponse(BaseModel):
    services: Dict[str, bool]
    limits: Dict[str, int]
    supported_search_types: List[str]
    supported_forums: List[str]

@router.get("/config", response_model=SearchConfigResponse)
async def get_search_config():
    """Get web search configuration and available services"""
    try:
        config_status = web_search_service.is_configured()
        
        return SearchConfigResponse(
            services=config_status,
            limits={
                "max_results_per_query": 50,
                "max_scrape_results": 20,
                "timeout_seconds": 60
            },
            supported_search_types=["search", "news", "images"],
            supported_forums=["reddit", "stackoverflow", "github", "discord", "hackernews"]
        )
        
    except Exception as e:
        logger.error(f"Error getting search config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/web", response_model=WebSearchResponse)
async def search_web(request: WebSearchRequest):
    """
    Search the web using Serper API
    
    Returns search results with optional content fetching
    """
    import time
    start_time = time.time()
    
    try:
        logger.info(f"Web search request: {request.query}")
        
        # Perform search
        search_response = await web_search_service.search_web(
            query=request.query,
            num_results=request.num_results,
            search_type=request.search_type.value,
            include_content=request.include_content
        )
        
        execution_time = time.time() - start_time
        
        # Convert SearchResult objects to dictionaries
        results_dict = []
        for result in search_response.results:
            result_dict = {
                "title": result.title,
                "url": result.url,
                "snippet": result.snippet,
                "content": result.content,
                "metadata": result.metadata
            }
            results_dict.append(result_dict)
        
        return WebSearchResponse(
            success=search_response.success,
            query=search_response.query,
            results=results_dict,
            total_results=search_response.total_results,
            error=search_response.error,
            search_type=request.search_type.value,
            execution_time=execution_time
        )
        
    except Exception as e:
        logger.error(f"Web search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scrape", response_model=Dict[str, Any])
async def search_and_scrape(request: SearchAndScrapeRequest, background_tasks: BackgroundTasks):
    """
    Search web and scrape content from results
    
    Optionally auto-ingest scraped content into specified workspace
    """
    try:
        logger.info(f"Search and scrape request: {request.query}")
        
        # Search and scrape
        search_response = await web_search_service.search_and_scrape(
            query=request.query,
            num_results=request.num_results,
            scrape_content=True
        )
        
        if not search_response.success:
            raise HTTPException(status_code=400, detail=search_response.error)
        
        scraped_documents = []
        
        # Process scraped content
        for result in search_response.results:
            if result.content:
                doc_data = {
                    "title": result.title,
                    "url": result.url,
                    "content": result.content,
                    "snippet": result.snippet,
                    "metadata": result.metadata,
                    "content_length": len(result.content),
                    "scraped_at": result.metadata.get("scraped_at") if result.metadata else None
                }
                scraped_documents.append(doc_data)
        
        response_data = {
            "success": True,
            "query": request.query,
            "workspace": request.workspace,
            "documents_scraped": len(scraped_documents),
            "total_characters": sum(len(doc["content"]) for doc in scraped_documents),
            "documents": scraped_documents
        }
        
        # Auto-ingest if requested
        if request.auto_ingest:
            background_tasks.add_task(
                _ingest_scraped_content,
                scraped_documents,
                request.workspace,
                request.query
            )
            response_data["auto_ingest_scheduled"] = True
        
        return response_data
        
    except Exception as e:
        logger.error(f"Search and scrape error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/documentation", response_model=Dict[str, Any])
async def search_documentation(request: DocumentationSearchRequest, background_tasks: BackgroundTasks):
    """
    Search for documentation about a specific topic
    
    Optimized for finding official docs, tutorials, and guides
    """
    try:
        logger.info(f"Documentation search: {request.topic}")
        
        search_response = await web_search_service.search_for_documentation(
            topic=request.topic,
            num_results=request.num_results
        )
        
        if not search_response.success:
            raise HTTPException(status_code=400, detail=search_response.error)
        
        docs_found = []
        for result in search_response.results:
            if result.content:
                doc_info = {
                    "title": result.title,
                    "url": result.url,
                    "content": result.content,
                    "snippet": result.snippet,
                    "content_length": len(result.content),
                    "is_documentation": True
                }
                docs_found.append(doc_info)
        
        response_data = {
            "success": True,
            "topic": request.topic,
            "workspace": request.workspace,
            "documentation_found": len(docs_found),
            "total_content_length": sum(doc["content_length"] for doc in docs_found),
            "documents": docs_found
        }
        
        if request.auto_ingest:
            background_tasks.add_task(
                _ingest_scraped_content,
                docs_found,
                request.workspace,
                f"documentation: {request.topic}"
            )
            response_data["auto_ingest_scheduled"] = True
        
        return response_data
        
    except Exception as e:
        logger.error(f"Documentation search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/code", response_model=Dict[str, Any])
async def search_code_examples(request: CodeSearchRequest, background_tasks: BackgroundTasks):
    """
    Search for code examples and tutorials
    
    Optimized for finding practical code examples on GitHub, tutorials, etc.
    """
    try:
        logger.info(f"Code search: {request.topic} ({request.language})")
        
        search_response = await web_search_service.search_for_code_examples(
            topic=request.topic,
            language=request.language,
            num_results=request.num_results
        )
        
        if not search_response.success:
            raise HTTPException(status_code=400, detail=search_response.error)
        
        code_examples = []
        for result in search_response.results:
            if result.content:
                code_info = {
                    "title": result.title,
                    "url": result.url,
                    "content": result.content,
                    "snippet": result.snippet,
                    "language": request.language,
                    "content_length": len(result.content),
                    "is_code_example": True
                }
                code_examples.append(code_info)
        
        response_data = {
            "success": True,
            "topic": request.topic,
            "language": request.language or "any",
            "workspace": request.workspace,
            "examples_found": len(code_examples),
            "total_content_length": sum(ex["content_length"] for ex in code_examples),
            "examples": code_examples
        }
        
        if request.auto_ingest:
            background_tasks.add_task(
                _ingest_scraped_content,
                code_examples,
                request.workspace,
                f"code examples: {request.topic} {request.language}".strip()
            )
            response_data["auto_ingest_scheduled"] = True
        
        return response_data
        
    except Exception as e:
        logger.error(f"Code search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/forums", response_model=Dict[str, Any])
async def search_forums(request: ForumSearchRequest, background_tasks: BackgroundTasks):
    """
    Search forums and community discussions
    
    Search Reddit, StackOverflow, GitHub discussions, etc.
    """
    try:
        logger.info(f"Forum search: {request.topic} in {request.forum or 'all forums'}")
        
        search_response = await web_search_service.search_forums(
            topic=request.topic,
            forum=request.forum,
            num_results=request.num_results
        )
        
        if not search_response.success:
            raise HTTPException(status_code=400, detail=search_response.error)
        
        forum_posts = []
        for result in search_response.results:
            if result.content:
                post_info = {
                    "title": result.title,
                    "url": result.url,
                    "content": result.content,
                    "snippet": result.snippet,
                    "forum_type": request.forum or "mixed",
                    "content_length": len(result.content),
                    "is_forum_discussion": True
                }
                forum_posts.append(post_info)
        
        response_data = {
            "success": True,
            "topic": request.topic,
            "forum": request.forum or "all",
            "workspace": request.workspace,
            "discussions_found": len(forum_posts),
            "total_content_length": sum(post["content_length"] for post in forum_posts),
            "discussions": forum_posts
        }
        
        if request.auto_ingest:
            background_tasks.add_task(
                _ingest_scraped_content,
                forum_posts,
                request.workspace,
                f"forum discussions: {request.topic}"
            )
            response_data["auto_ingest_scheduled"] = True
        
        return response_data
        
    except Exception as e:
        logger.error(f"Forum search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _ingest_scraped_content(documents: List[Dict[str, Any]], workspace: str, search_query: str):
    """Background task to ingest scraped content into Memory-Server"""
    try:
        from api.utils.document_processor import DocumentProcessor
        
        processor = DocumentProcessor()
        ingested_count = 0
        
        for doc in documents:
            try:
                # Create metadata for the document
                metadata = {
                    "source": "web_search",
                    "search_query": search_query,
                    "original_url": doc["url"],
                    "title": doc["title"],
                    "snippet": doc.get("snippet", ""),
                    "scraped_content_length": doc["content_length"],
                    "content_type": "web_scraped"
                }
                
                # Process the web content
                doc_id = await processor.process_web_content(
                    content=doc["content"],
                    url=doc["url"],
                    workspace=workspace,
                    metadata=metadata
                )
                
                ingested_count += 1
                logger.info(f"Auto-ingested web content: {doc['title']} -> {doc_id}")
                
            except Exception as e:
                logger.error(f"Error auto-ingesting {doc['url']}: {e}")
        
        logger.info(f"Auto-ingestion completed: {ingested_count}/{len(documents)} documents processed")
        
    except Exception as e:
        logger.error(f"Background ingestion error: {e}")