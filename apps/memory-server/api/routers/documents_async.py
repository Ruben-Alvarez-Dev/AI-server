"""
Async Document Ingestion Router for Memory-Server
Uses Celery for true async processing
"""

import os
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from ..schemas.async_schemas import (
    AsyncDocumentUploadResponse,
    AsyncBatchUploadResponse,
    TaskStatusResponse,
    AsyncHealthResponse,
    AsyncStatsResponse,
    TaskCancelResponse,
    RedirectResponse
)

from core.config import get_config
from core.logging_config import get_logger

router = APIRouter(prefix="/async", tags=["Async Document Processing"])
config = get_config()
logger = get_logger("async-documents-router")

# Import Celery tasks
try:
    from workers.simple_document_worker import simple_process_document
    from core.celery_app import celery_app
    CELERY_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Celery workers not available: {e}")
    CELERY_AVAILABLE = False
    celery_app = None

@router.post("/upload", response_model=AsyncDocumentUploadResponse)
async def upload_document_async(
    file: UploadFile = File(...),
    workspace: str = Form("research"),
    auto_summarize: bool = Form(True),
    tags: Optional[str] = Form(None)
):
    """
    Upload a document for async processing
    Returns immediately with task ID for status checking
    """
    if not CELERY_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Async processing service is not available"
        )
    
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Read and validate file size
        content = await file.read()
        file_size = len(content)
        
        if file_size > config.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large: {file_size} bytes (max: {config.MAX_FILE_SIZE})"
            )
        
        if file_size == 0:
            raise HTTPException(status_code=400, detail="Empty file not allowed")
        
        # Process tags
        tag_list = []
        if tags:
            tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        
        # Create temporary file (workers will clean up)
        with tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=Path(file.filename).suffix,
            prefix="memory_server_"
        ) as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        logger.info(f"Created temporary file for {file.filename}: {tmp_path}")
        
        # Queue document for processing
        task = simple_process_document.apply_async(
            args=[tmp_path, file.filename],
            kwargs={
                'workspace': workspace,
                'auto_summarize': auto_summarize,
                'tags': tag_list
            },
            queue='documents'
        )
        
        # Estimate completion time (rough estimate)
        estimated_time = datetime.now().isoformat()
        
        logger.info(f"Queued document {file.filename} for async processing: {task.id}")
        
        return AsyncDocumentUploadResponse(
            success=True,
            task_id=task.id,
            workspace=workspace,
            processing_status="queued",
            message=f"Document '{file.filename}' queued for processing",
            estimated_completion=estimated_time,
            check_status_url=f"/async/status/{task.id}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error queuing document {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-batch", response_model=AsyncBatchUploadResponse)
async def upload_batch_documents_async(
    files: List[UploadFile] = File(...),
    workspace: str = Form("research"),
    auto_summarize: bool = Form(True),
    tags: Optional[str] = Form(None)
):
    """
    Upload multiple documents for async batch processing
    """
    if not CELERY_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Async processing service is not available"
        )
    
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        if len(files) > 100:  # Reasonable batch limit
            raise HTTPException(status_code=413, detail="Too many files in batch (max: 100)")
        
        # Process tags
        tag_list = []
        if tags:
            tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        
        # Prepare file paths
        file_paths = []
        task_ids = []
        
        for file in files:
            if not file.filename:
                continue
            
            # Read and validate
            content = await file.read()
            file_size = len(content)
            
            if file_size > config.MAX_FILE_SIZE:
                logger.warning(f"Skipping large file: {file.filename} ({file_size} bytes)")
                continue
            
            if file_size == 0:
                logger.warning(f"Skipping empty file: {file.filename}")
                continue
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=Path(file.filename).suffix,
                prefix="memory_server_batch_"
            ) as tmp_file:
                tmp_file.write(content)
                tmp_path = tmp_file.name
            
            file_paths.append((tmp_path, file.filename))
        
        if not file_paths:
            raise HTTPException(status_code=400, detail="No valid files to process")
        
        # Queue all files for processing
        for tmp_path, original_name in file_paths:
            task = process_document.apply_async(
                args=[tmp_path, original_name],
                kwargs={
                    'workspace': workspace,
                    'auto_summarize': auto_summarize,
                    'tags': tag_list
                },
                queue='documents'
            )
            task_ids.append(task.id)
        
        # Generate batch ID for tracking
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(task_ids)}"
        
        logger.info(f"Queued {len(task_ids)} documents for batch processing: {batch_id}")
        
        return AsyncBatchUploadResponse(
            success=True,
            batch_id=batch_id,
            total_files=len(file_paths),
            workspace=workspace,
            task_ids=task_ids,
            message=f"Batch processing started for {len(file_paths)} documents",
            check_status_url=f"/async/batch-status/{batch_id}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in async batch upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Check the status of a processing task
    """
    if not CELERY_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Async processing service is not available"
        )
    
    try:
        from celery.result import AsyncResult
        from ...workers.document_worker import celery_app
        
        result = AsyncResult(task_id, app=celery_app)
        
        response = TaskStatusResponse(
            task_id=task_id,
            status=result.status,
            ready=result.ready()
        )
        
        if result.status == 'PENDING':
            response.current = 'Task is waiting to be processed'
        elif result.status == 'PROCESSING':
            if result.info and isinstance(result.info, dict):
                response.current = result.info.get('current', 'Processing...')
                response.progress = result.info.get('progress', 0)
                response.meta = result.info
        elif result.status == 'SUCCESS':
            response.result = result.result
            response.progress = 100
            response.current = 'Completed'
        elif result.status == 'FAILURE':
            response.error = str(result.info) if result.info else 'Unknown error'
            response.current = 'Failed'
        elif result.status == 'RETRY':
            response.current = 'Retrying after error'
            response.meta = result.info if isinstance(result.info, dict) else {}
        
        return response
        
    except Exception as e:
        logger.error(f"Error checking task status {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/batch-status/{batch_id}")
async def get_batch_status(batch_id: str):
    """
    Get status of all tasks in a batch
    Note: This is a simplified implementation. 
    In production, you'd store batch metadata in Redis or database.
    """
    return JSONResponse({
        "batch_id": batch_id,
        "message": "Batch status tracking requires batch metadata storage",
        "recommendation": "Use individual task IDs to check status of each document"
    })

@router.delete("/task/{task_id}", response_model=TaskCancelResponse)
async def cancel_task(task_id: str):
    """
    Cancel a processing task (if still pending)
    """
    if not CELERY_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Async processing service is not available"
        )
    
    try:
        from celery.result import AsyncResult
        from ...workers.document_worker import celery_app
        
        result = AsyncResult(task_id, app=celery_app)
        
        if result.status == 'PENDING':
            result.revoke(terminate=True)
            return JSONResponse({
                "success": True,
                "task_id": task_id,
                "message": "Task cancelled"
            })
        else:
            return JSONResponse({
                "success": False,
                "task_id": task_id,
                "status": result.status,
                "message": f"Cannot cancel task with status: {result.status}"
            })
        
    except Exception as e:
        logger.error(f"Error cancelling task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", response_model=AsyncHealthResponse)
async def async_health_check():
    """
    Health check for async processing system
    """
    health_status = {
        "async_processing": CELERY_AVAILABLE,
        "timestamp": datetime.now().isoformat()
    }
    
    if CELERY_AVAILABLE:
        try:
            from ...workers.document_worker import celery_app
            
            # Check if workers are available
            inspect = celery_app.control.inspect()
            active_workers = inspect.active()
            
            health_status.update({
                "workers_available": active_workers is not None and len(active_workers) > 0,
                "active_workers": list(active_workers.keys()) if active_workers else [],
                "redis_connection": True  # If we got this far, Redis is working
            })
            
        except Exception as e:
            health_status.update({
                "workers_available": False,
                "error": str(e)
            })
    
    return JSONResponse(health_status)

@router.get("/stats", response_model=AsyncStatsResponse)
async def get_async_stats():
    """
    Get async processing statistics
    """
    if not CELERY_AVAILABLE:
        return JSONResponse({
            "error": "Async processing not available"
        })
    
    try:
        from ...workers.document_worker import celery_app
        
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        
        # Aggregate stats
        total_processed = 0
        total_active = 0
        
        if stats:
            for worker_stats in stats.values():
                total_processed += worker_stats.get('total', {}).get('tasks.document_worker.process_document', 0)
            
            active_tasks = inspect.active()
            if active_tasks:
                total_active = sum(len(tasks) for tasks in active_tasks.values())
        
        return JSONResponse({
            "workers": len(stats) if stats else 0,
            "total_processed": total_processed,
            "active_tasks": total_active,
            "celery_available": True,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting async stats: {e}")
        return JSONResponse({
            "error": str(e),
            "celery_available": False
        })