"""
Document Ingestion Router for Memory-Server
Handles document upload, folder processing, web scraping, and workspace management
"""

import os
import asyncio
import mimetypes
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
import tempfile
import shutil
import json
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from core.config import get_config
from core.logging_config import get_logger
from ..utils.web_scraper import WebScraperService
from ..utils.document_processor import DocumentProcessor
from ..utils.workspace_manager import WorkspaceManager

router = APIRouter(prefix="/documents", tags=["documents"])
config = get_config()
logger = get_logger("documents-router")

# Response Models
class DocumentUploadResponse(BaseModel):
    success: bool
    document_id: str
    workspace: str
    processing_status: str
    message: str
    metadata: Dict[str, Any]

class BatchUploadResponse(BaseModel):
    success: bool
    total_files: int
    processed: int
    failed: int
    workspace: str
    document_ids: List[str]
    errors: List[str]

class WebScrapingResponse(BaseModel):
    success: bool
    url: str
    workspace: str
    pages_scraped: int
    document_id: str
    message: str

class WorkspaceListResponse(BaseModel):
    workspaces: List[str]
    active_workspace: str
    total_documents: Dict[str, int]

# Activity tracking models
class ActivityEvent(BaseModel):
    type: str = Field(..., description="Type of activity event")
    timestamp: int = Field(..., description="Unix timestamp in milliseconds")
    file: Optional[str] = Field(None, description="File path if applicable")
    language: Optional[str] = Field(None, description="Programming language")
    workspace: Optional[str] = Field(None, description="Workspace context")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional event metadata")

class ActivityTrackingRequest(BaseModel):
    workspace: str = Field(default="code", description="Target workspace")
    events: List[Dict[str, Any]] = Field(..., description="List of activity events")
    source: str = Field(default="vscode-extension", description="Source of activity data")
    auto_tag: bool = Field(default=True, description="Enable auto-tagging of activities")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Request metadata")

class ActivityTrackingResponse(BaseModel):
    success: bool
    events_processed: int
    workspace: str
    document_id: Optional[str] = None
    message: str
    processing_time: float

# Request Models
class WebScrapingRequest(BaseModel):
    url: str = Field(..., description="URL to scrape")
    workspace: str = Field("research", description="Workspace to store documents")
    max_pages: int = Field(10, description="Maximum pages to scrape")
    include_pdfs: bool = Field(True, description="Include PDF links")
    include_external: bool = Field(False, description="Include external domain links")

class FolderProcessingRequest(BaseModel):
    folder_path: str = Field(..., description="Path to folder to process")
    workspace: str = Field("code", description="Workspace to store documents")
    recursive: bool = Field(True, description="Process subfolders")
    file_patterns: List[str] = Field(["*.py", "*.js", "*.ts", "*.md", "*.txt"], description="File patterns to include")
    exclude_patterns: List[str] = Field([".git", "node_modules", "__pycache__", "*.pyc"], description="Patterns to exclude")

# Initialize services
web_scraper = WebScraperService()
doc_processor = DocumentProcessor()
workspace_manager = WorkspaceManager()

@router.get("/workspaces", response_model=WorkspaceListResponse)
async def list_workspaces():
    """List all available workspaces and their document counts"""
    try:
        workspaces = await workspace_manager.list_workspaces()
        active = workspace_manager.get_active_workspace()
        counts = {}
        
        for workspace in workspaces:
            counts[workspace] = await workspace_manager.get_document_count(workspace)
            
        return WorkspaceListResponse(
            workspaces=workspaces,
            active_workspace=active,
            total_documents=counts
        )
    except Exception as e:
        logger.error(f"Error listing workspaces: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/workspace/{workspace_name}")
async def create_workspace(workspace_name: str, description: Optional[str] = None):
    """Create a new workspace"""
    try:
        await workspace_manager.create_workspace(workspace_name, description)
        logger.info(f"Created workspace: {workspace_name}")
        
        return JSONResponse({
            "success": True,
            "workspace": workspace_name,
            "message": f"Workspace '{workspace_name}' created successfully"
        })
    except Exception as e:
        logger.error(f"Error creating workspace {workspace_name}: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    workspace: str = Form("research"),
    auto_summarize: bool = Form(True),
    tags: Optional[str] = Form(None)
):
    """Upload a single document to specified workspace"""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
            
        file_size = 0
        content = await file.read()
        file_size = len(content)
        
        if file_size > config.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413, 
                detail=f"File too large: {file_size} bytes (max: {config.MAX_FILE_SIZE})"
            )
        
        # Process tags
        tag_list = []
        if tags:
            tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            # Process document
            document_id = await doc_processor.process_file(
                file_path=tmp_path,
                original_name=file.filename,
                workspace=workspace,
                auto_summarize=auto_summarize,
                tags=tag_list
            )
            
            # Get metadata
            metadata = {
                "filename": file.filename,
                "size": file_size,
                "content_type": file.content_type,
                "workspace": workspace,
                "upload_time": datetime.now().isoformat(),
                "tags": tag_list
            }
            
            logger.info(f"Document uploaded successfully: {file.filename} -> {document_id}")
            
            return DocumentUploadResponse(
                success=True,
                document_id=document_id,
                workspace=workspace,
                processing_status="completed",
                message=f"Document '{file.filename}' uploaded and processed successfully",
                metadata=metadata
            )
            
        finally:
            # Clean up temp file
            os.unlink(tmp_path)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-batch", response_model=BatchUploadResponse)
async def upload_batch_documents(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    workspace: str = Form("research"),
    auto_summarize: bool = Form(True),
    tags: Optional[str] = Form(None)
):
    """Upload multiple documents to specified workspace"""
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
            
        # Process tags
        tag_list = []
        if tags:
            tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        
        processed = 0
        failed = 0
        document_ids = []
        errors = []
        
        for file in files:
            try:
                if not file.filename:
                    continue
                    
                content = await file.read()
                file_size = len(content)
                
                if file_size > config.MAX_FILE_SIZE:
                    errors.append(f"File {file.filename}: too large ({file_size} bytes)")
                    failed += 1
                    continue
                
                # Create temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
                    tmp_file.write(content)
                    tmp_path = tmp_file.name
                
                try:
                    # Process document
                    document_id = await doc_processor.process_file(
                        file_path=tmp_path,
                        original_name=file.filename,
                        workspace=workspace,
                        auto_summarize=auto_summarize,
                        tags=tag_list
                    )
                    
                    document_ids.append(document_id)
                    processed += 1
                    
                finally:
                    os.unlink(tmp_path)
                    
            except Exception as e:
                errors.append(f"File {file.filename}: {str(e)}")
                failed += 1
        
        logger.info(f"Batch upload completed: {processed} successful, {failed} failed")
        
        return BatchUploadResponse(
            success=failed == 0,
            total_files=len(files),
            processed=processed,
            failed=failed,
            workspace=workspace,
            document_ids=document_ids,
            errors=errors
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process-folder", response_model=BatchUploadResponse)
async def process_folder(
    request: FolderProcessingRequest,
    background_tasks: BackgroundTasks
):
    """Process all files in a folder and subfolders"""
    try:
        folder_path = Path(request.folder_path)
        
        if not folder_path.exists():
            raise HTTPException(status_code=404, detail=f"Folder not found: {request.folder_path}")
            
        if not folder_path.is_dir():
            raise HTTPException(status_code=400, detail=f"Path is not a directory: {request.folder_path}")
        
        # Find files to process
        files_to_process = []
        
        def should_include_file(file_path: Path) -> bool:
            # Check exclude patterns
            for pattern in request.exclude_patterns:
                if pattern in str(file_path):
                    return False
            
            # Check include patterns
            for pattern in request.file_patterns:
                if file_path.match(pattern):
                    return True
            return False
        
        if request.recursive:
            for file_path in folder_path.rglob("*"):
                if file_path.is_file() and should_include_file(file_path):
                    files_to_process.append(file_path)
        else:
            for file_path in folder_path.glob("*"):
                if file_path.is_file() and should_include_file(file_path):
                    files_to_process.append(file_path)
        
        if not files_to_process:
            raise HTTPException(status_code=404, detail="No matching files found in folder")
        
        # Process files
        processed = 0
        failed = 0
        document_ids = []
        errors = []
        
        for file_path in files_to_process:
            try:
                # Check file size
                file_size = file_path.stat().st_size
                if file_size > config.MAX_FILE_SIZE:
                    errors.append(f"File {file_path.name}: too large ({file_size} bytes)")
                    failed += 1
                    continue
                
                # Process document
                document_id = await doc_processor.process_file(
                    file_path=str(file_path),
                    original_name=file_path.name,
                    workspace=request.workspace,
                    auto_summarize=True,
                    tags=[f"folder:{folder_path.name}"]
                )
                
                document_ids.append(document_id)
                processed += 1
                
            except Exception as e:
                errors.append(f"File {file_path.name}: {str(e)}")
                failed += 1
        
        logger.info(f"Folder processing completed: {processed} files processed from {request.folder_path}")
        
        return BatchUploadResponse(
            success=failed == 0,
            total_files=len(files_to_process),
            processed=processed,
            failed=failed,
            workspace=request.workspace,
            document_ids=document_ids,
            errors=errors
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing folder {request.folder_path}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scrape-web", response_model=WebScrapingResponse)
async def scrape_web_content(
    request: WebScrapingRequest,
    background_tasks: BackgroundTasks
):
    """Scrape web content using Playwright-based scraper"""
    try:
        # Start web scraping
        result = await web_scraper.scrape_website(
            url=request.url,
            max_pages=request.max_pages,
            include_pdfs=request.include_pdfs,
            include_external=request.include_external
        )
        
        if not result.success:
            raise HTTPException(status_code=400, detail=result.error)
        
        # Process scraped content
        document_id = await doc_processor.process_web_content(
            content=result.content,
            url=request.url,
            workspace=request.workspace,
            metadata={
                "pages_scraped": result.pages_scraped,
                "scrape_time": datetime.now().isoformat(),
                "source_url": request.url
            }
        )
        
        logger.info(f"Web scraping completed: {request.url} -> {document_id}")
        
        return WebScrapingResponse(
            success=True,
            url=request.url,
            workspace=request.workspace,
            pages_scraped=result.pages_scraped,
            document_id=document_id,
            message=f"Successfully scraped {result.pages_scraped} pages from {request.url}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scraping {request.url}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_documents(
    query: str,
    workspace: Optional[str] = None,
    limit: int = 10,
    semantic: bool = True
):
    """Search documents across workspaces"""
    try:
        # This will be implemented when we have the search functionality ready
        # For now, return a placeholder
        return JSONResponse({
            "query": query,
            "workspace": workspace,
            "results": [],
            "message": "Search functionality will be implemented in next phase"
        })
        
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/workspace/{workspace_name}/{document_id}")
async def delete_document(workspace_name: str, document_id: str):
    """Delete a document from workspace"""
    try:
        await doc_processor.delete_document(workspace_name, document_id)
        
        return JSONResponse({
            "success": True,
            "message": f"Document {document_id} deleted from workspace {workspace_name}"
        })
        
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/activity", response_model=ActivityTrackingResponse)
async def track_activity(
    request: ActivityTrackingRequest,
    background_tasks: BackgroundTasks
):
    """
    Track development activity from VSCode extension
    
    Processes activity events and stores them in the specified workspace
    with intelligent auto-tagging for enhanced searchability
    """
    start_time = datetime.now()
    
    try:
        if not request.events:
            raise HTTPException(status_code=400, detail="No events provided")
        
        logger.info(f"Processing {len(request.events)} activity events for workspace '{request.workspace}'")
        
        # Process activity events into a structured document
        activity_summary = {
            "source": request.source,
            "workspace": request.workspace,
            "event_count": len(request.events),
            "processing_timestamp": start_time.isoformat(),
            "events": request.events,
            "metadata": request.metadata or {}
        }
        
        # Generate activity content for processing
        activity_content = generate_activity_content(request.events, request.workspace, request.source)
        
        # Process as a document in Memory-Server
        document_id = await doc_processor.process_web_content(
            content=activity_content,
            url=f"vscode-activity://{request.workspace}/{start_time.isoformat()}",
            workspace=request.workspace,
            metadata={
                "content_type": "development_activity",
                "source": request.source,
                "auto_tag": request.auto_tag,
                "event_count": len(request.events),
                "activity_summary": activity_summary,
                "languages": extract_languages_from_events(request.events),
                "activity_types": extract_activity_types(request.events),
                "time_range": extract_time_range(request.events)
            }
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"Activity tracked successfully: {len(request.events)} events -> {document_id}")
        
        return ActivityTrackingResponse(
            success=True,
            events_processed=len(request.events),
            workspace=request.workspace,
            document_id=document_id,
            message=f"Successfully processed {len(request.events)} activity events",
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing activity events: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def generate_activity_content(events: List[Dict[str, Any]], workspace: str, source: str) -> str:
    """Generate structured content from activity events"""
    
    # Analyze events
    activity_types = {}
    files_accessed = set()
    languages_used = set()
    time_span = {"start": None, "end": None}
    
    for event in events:
        event_type = event.get("type", "unknown")
        activity_types[event_type] = activity_types.get(event_type, 0) + 1
        
        if event.get("file"):
            files_accessed.add(event["file"])
        
        if event.get("language"):
            languages_used.add(event["language"])
            
        timestamp = event.get("timestamp")
        if timestamp:
            if not time_span["start"] or timestamp < time_span["start"]:
                time_span["start"] = timestamp
            if not time_span["end"] or timestamp > time_span["end"]:
                time_span["end"] = timestamp
    
    # Format time span
    start_time = datetime.fromtimestamp(time_span["start"] / 1000) if time_span["start"] else None
    end_time = datetime.fromtimestamp(time_span["end"] / 1000) if time_span["end"] else None
    
    # Generate content
    content = f"""# Development Activity Report

## Session Information
- **Workspace**: {workspace}
- **Source**: {source}
- **Total Events**: {len(events)}
- **Time Span**: {start_time.strftime('%Y-%m-%d %H:%M:%S') if start_time else 'Unknown'} - {end_time.strftime('%Y-%m-%d %H:%M:%S') if end_time else 'Unknown'}

## Activity Summary

### Event Types
"""
    
    for event_type, count in sorted(activity_types.items(), key=lambda x: x[1], reverse=True):
        content += f"- **{event_type}**: {count} events\n"
    
    if languages_used:
        content += f"\n### Programming Languages\n"
        for lang in sorted(languages_used):
            content += f"- {lang}\n"
    
    if files_accessed:
        content += f"\n### Files Accessed ({len(files_accessed)})\n"
        # Show top 20 files to avoid overwhelming the content
        for file_path in sorted(list(files_accessed)[:20]):
            file_name = Path(file_path).name if file_path else "unknown"
            content += f"- {file_name}\n"
        
        if len(files_accessed) > 20:
            content += f"- ... and {len(files_accessed) - 20} more files\n"
    
    content += f"\n## Detailed Events\n\n"
    
    # Add recent events (last 10) with details
    recent_events = sorted(events, key=lambda x: x.get("timestamp", 0), reverse=True)[:10]
    for i, event in enumerate(recent_events, 1):
        timestamp = event.get("timestamp")
        time_str = datetime.fromtimestamp(timestamp / 1000).strftime('%H:%M:%S') if timestamp else 'Unknown'
        
        content += f"### Event {i} - {event.get('type', 'Unknown')} ({time_str})\n"
        
        if event.get("file"):
            content += f"- **File**: {Path(event['file']).name}\n"
        if event.get("language"):
            content += f"- **Language**: {event['language']}\n"
        
        # Add other relevant metadata
        for key, value in event.items():
            if key not in ['type', 'timestamp', 'file', 'language', '_received_at']:
                content += f"- **{key.replace('_', ' ').title()}**: {value}\n"
        
        content += "\n"
    
    content += """
## Memory-Server Integration

This activity report was automatically generated from VSCode development activity.
The data is stored in the Memory-Server for:

- **Contextual Code Assistance**: Understanding your coding patterns and preferences
- **Intelligent Suggestions**: Providing relevant documentation and examples
- **Project Insights**: Analyzing development workflows and productivity patterns
- **Smart Auto-completion**: Learning from your coding style and frequently used patterns

All activity data is processed with intelligent auto-tagging for enhanced searchability and organization.
"""
    
    return content

def extract_languages_from_events(events: List[Dict[str, Any]]) -> List[str]:
    """Extract unique programming languages from events"""
    languages = set()
    for event in events:
        if event.get("language"):
            languages.add(event["language"])
    return sorted(list(languages))

def extract_activity_types(events: List[Dict[str, Any]]) -> List[str]:
    """Extract unique activity types from events"""
    types = set()
    for event in events:
        if event.get("type"):
            types.add(event["type"])
    return sorted(list(types))

def extract_time_range(events: List[Dict[str, Any]]) -> Dict[str, str]:
    """Extract time range from events"""
    timestamps = [event.get("timestamp") for event in events if event.get("timestamp")]
    if not timestamps:
        return {"start": None, "end": None}
    
    start_ms = min(timestamps)
    end_ms = max(timestamps)
    
    start_time = datetime.fromtimestamp(start_ms / 1000)
    end_time = datetime.fromtimestamp(end_ms / 1000)
    
    return {
        "start": start_time.isoformat(),
        "end": end_time.isoformat(),
        "duration_minutes": round((end_ms - start_ms) / (1000 * 60), 2)
    }

@router.get("/stats")
async def get_ingestion_stats():
    """Get ingestion statistics"""
    try:
        stats = await doc_processor.get_statistics()
        return JSONResponse(stats)
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))