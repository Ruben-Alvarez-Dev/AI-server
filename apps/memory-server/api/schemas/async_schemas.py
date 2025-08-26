"""
OpenAPI Schemas for Async Processing Endpoints
Enterprise-grade API documentation schemas
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class TaskStatus(str, Enum):
    """Task processing status enumeration"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RETRY = "RETRY"
    REVOKED = "REVOKED"


class AsyncDocumentUploadResponse(BaseModel):
    """Response schema for async document upload"""
    success: bool = Field(..., description="Upload success status")
    task_id: str = Field(..., description="Unique task identifier for tracking")
    workspace: str = Field(..., description="Target workspace name")
    processing_status: str = Field(..., description="Initial processing status")
    message: str = Field(..., description="Human-readable status message")
    estimated_completion: str = Field(..., description="Estimated completion time (ISO format)")
    check_status_url: str = Field(..., description="URL to check task status")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "task_id": "abc123-def456-ghi789",
                "workspace": "research",
                "processing_status": "queued",
                "message": "Document 'report.pdf' queued for processing",
                "estimated_completion": "2025-08-26T18:30:00Z",
                "check_status_url": "/api/v1/async/status/abc123-def456-ghi789"
            }
        }


class AsyncBatchUploadResponse(BaseModel):
    """Response schema for async batch upload"""
    success: bool = Field(..., description="Batch upload success status")
    batch_id: str = Field(..., description="Unique batch identifier")
    total_files: int = Field(..., description="Total number of files in batch")
    workspace: str = Field(..., description="Target workspace name")
    task_ids: List[str] = Field(..., description="List of individual task IDs")
    message: str = Field(..., description="Human-readable status message")
    check_status_url: str = Field(..., description="URL to check batch status")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "batch_id": "batch_20250826_183000_5",
                "total_files": 5,
                "workspace": "research", 
                "task_ids": [
                    "abc123-def456-ghi789",
                    "abc124-def457-ghi790",
                    "abc125-def458-ghi791"
                ],
                "message": "Batch processing started for 5 documents",
                "check_status_url": "/api/v1/async/batch-status/batch_20250826_183000_5"
            }
        }


class TaskProgressMeta(BaseModel):
    """Task progress metadata"""
    current: Optional[str] = Field(None, description="Current processing step")
    progress: Optional[int] = Field(None, ge=0, le=100, description="Progress percentage (0-100)")
    filename: Optional[str] = Field(None, description="File being processed")
    workspace: Optional[str] = Field(None, description="Target workspace")
    document_id: Optional[str] = Field(None, description="Generated document ID")
    error_type: Optional[str] = Field(None, description="Error type if failed")


class TaskResultData(BaseModel):
    """Successful task result data"""
    status: str = Field(..., description="Completion status")
    document_id: str = Field(..., description="Generated document ID")
    filename: str = Field(..., description="Original filename")
    workspace: str = Field(..., description="Target workspace")
    message: str = Field(..., description="Success message")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional processing metadata")


class TaskStatusResponse(BaseModel):
    """Response schema for task status check"""
    task_id: str = Field(..., description="Task identifier")
    status: TaskStatus = Field(..., description="Current task status")
    ready: bool = Field(..., description="Whether task is completed (success or failure)")
    progress: Optional[int] = Field(None, ge=0, le=100, description="Progress percentage")
    current: Optional[str] = Field(None, description="Current processing step")
    result: Optional[TaskResultData] = Field(None, description="Task result if completed successfully")
    error: Optional[str] = Field(None, description="Error message if failed")
    meta: Optional[TaskProgressMeta] = Field(None, description="Additional task metadata")
    
    class Config:
        schema_extra = {
            "example": {
                "task_id": "abc123-def456-ghi789",
                "status": "PROCESSING",
                "ready": False,
                "progress": 65,
                "current": "Generating embeddings",
                "meta": {
                    "filename": "report.pdf",
                    "workspace": "research",
                    "progress": 65
                }
            }
        }


class AsyncHealthResponse(BaseModel):
    """Response schema for async system health check"""
    async_processing: bool = Field(..., description="Async processing availability")
    workers_available: bool = Field(..., description="Worker availability status")
    active_workers: List[str] = Field(..., description="List of active worker names")
    redis_connection: bool = Field(..., description="Redis connection status")
    timestamp: str = Field(..., description="Health check timestamp")
    error: Optional[str] = Field(None, description="Error message if unhealthy")
    
    class Config:
        schema_extra = {
            "example": {
                "async_processing": True,
                "workers_available": True,
                "active_workers": ["documents@server.local", "embeddings@server.local"],
                "redis_connection": True,
                "timestamp": "2025-08-26T18:30:00Z"
            }
        }


class AsyncStatsResponse(BaseModel):
    """Response schema for async processing statistics"""
    workers: int = Field(..., description="Number of active workers")
    total_processed: int = Field(..., description="Total tasks processed")
    active_tasks: int = Field(..., description="Currently active tasks")
    celery_available: bool = Field(..., description="Celery system availability")
    timestamp: str = Field(..., description="Statistics timestamp")
    error: Optional[str] = Field(None, description="Error message if unavailable")
    
    class Config:
        schema_extra = {
            "example": {
                "workers": 2,
                "total_processed": 1247,
                "active_tasks": 3,
                "celery_available": True,
                "timestamp": "2025-08-26T18:30:00Z"
            }
        }


class TaskCancelResponse(BaseModel):
    """Response schema for task cancellation"""
    success: bool = Field(..., description="Cancellation success status")
    task_id: str = Field(..., description="Task identifier")
    status: Optional[str] = Field(None, description="Task status at cancellation")
    message: str = Field(..., description="Cancellation result message")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "task_id": "abc123-def456-ghi789",
                "message": "Task cancelled successfully"
            }
        }


class BatchStatusResponse(BaseModel):
    """Response schema for batch status check"""
    batch_id: str = Field(..., description="Batch identifier")
    total_tasks: int = Field(..., description="Total tasks in batch")
    completed: int = Field(..., description="Completed tasks")
    failed: int = Field(..., description="Failed tasks")
    pending: int = Field(..., description="Pending tasks")
    processing: int = Field(..., description="Currently processing tasks")
    overall_progress: int = Field(..., ge=0, le=100, description="Overall batch progress percentage")
    task_statuses: List[TaskStatusResponse] = Field(..., description="Individual task statuses")
    
    class Config:
        schema_extra = {
            "example": {
                "batch_id": "batch_20250826_183000_5",
                "total_tasks": 5,
                "completed": 3,
                "failed": 0,
                "pending": 1,
                "processing": 1,
                "overall_progress": 70,
                "task_statuses": [
                    {
                        "task_id": "abc123",
                        "status": "SUCCESS",
                        "ready": True,
                        "progress": 100
                    }
                ]
            }
        }


class RedirectResponse(BaseModel):
    """Response schema for endpoint redirects"""
    message: str = Field(..., description="Redirect explanation message")
    redirect_to: str = Field(..., description="Target endpoint URL")
    reason: str = Field(..., description="Reason for redirect")
    documentation: str = Field(..., description="Usage documentation")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "Upload endpoint has moved to async processing",
                "redirect_to": "/api/v1/async/upload",
                "reason": "Better performance and no blocking",
                "documentation": "Use POST /api/v1/async/upload for uploading documents"
            }
        }


# Request schemas
class DocumentUploadRequest(BaseModel):
    """Schema for document upload parameters"""
    workspace: str = Field("research", description="Target workspace name")
    auto_summarize: bool = Field(True, description="Generate automatic summary")
    tags: Optional[str] = Field(None, description="Comma-separated tags")
    
    class Config:
        schema_extra = {
            "example": {
                "workspace": "research",
                "auto_summarize": True,
                "tags": "report,analysis,quarterly"
            }
        }


class BatchUploadRequest(BaseModel):
    """Schema for batch upload parameters"""
    workspace: str = Field("research", description="Target workspace name")
    auto_summarize: bool = Field(True, description="Generate automatic summary")
    tags: Optional[str] = Field(None, description="Comma-separated tags for all files")
    
    class Config:
        schema_extra = {
            "example": {
                "workspace": "research",
                "auto_summarize": True,
                "tags": "batch,documents,quarterly"
            }
        }