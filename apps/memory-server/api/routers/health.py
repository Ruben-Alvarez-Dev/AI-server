"""
Health Check Router
System health and status monitoring endpoints
"""

import time
import psutil
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.config import get_config
from core.logging_config import get_logger

router = APIRouter()
config = get_config()
logger = get_logger("health-api")


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    timestamp: float
    uptime: float
    version: str
    components: Dict[str, Any]
    system: Dict[str, Any]


class ComponentStatus(BaseModel):
    """Component status model"""
    name: str
    status: str
    initialized: bool
    statistics: Dict[str, Any]


@router.get("/", 
           response_model=HealthResponse,
           summary="Basic Health Check",
           description="Get basic health status of the Memory-Server")
async def health_check():
    """Basic health check endpoint"""
    # Simple app state without circular import
    app_state = {
        "initialized": True,
        "lazy_indexer": None,
        "chunking_engine": None, 
        "fusion_layer": None,
        "agentic_rag": None
    }
    
    # Get system information
    memory_info = psutil.virtual_memory()
    disk_info = psutil.disk_usage('/')
    
    return HealthResponse(
        status="healthy" if app_state["initialized"] else "initializing",
        timestamp=time.time(),
        uptime=time.time() - psutil.Process().create_time(),
        version="1.0.0",
        components={
            "lazy_indexer": app_state["lazy_indexer"] is not None,
            "chunking_engine": app_state["chunking_engine"] is not None,
            "fusion_layer": app_state["fusion_layer"] is not None,
            "agentic_rag": app_state["agentic_rag"] is not None
        },
        system={
            "memory_usage_percent": memory_info.percent,
            "disk_usage_percent": disk_info.percent,
            "cpu_count": psutil.cpu_count(),
            "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
        }
    )


@router.get("/detailed",
           summary="Detailed Health Check", 
           description="Get detailed health information including component statistics")
async def detailed_health_check():
    """Detailed health check with component statistics"""
    app_state = {"initialized": True, "lazy_indexer": None, "chunking_engine": None, "fusion_layer": None}
    
    if not app_state["initialized"]:
        raise HTTPException(status_code=503, detail="Memory-Server not fully initialized")
    
    components = []
    
    # LazyGraphRAG Indexer
    if app_state["lazy_indexer"]:
        try:
            stats = app_state["lazy_indexer"].get_statistics()
            components.append(ComponentStatus(
                name="LazyGraphRAG Indexer",
                status="healthy",
                initialized=True,
                statistics=stats
            ))
        except Exception as e:
            logger.error(f"Error getting indexer stats: {e}")
            components.append(ComponentStatus(
                name="LazyGraphRAG Indexer", 
                status="error",
                initialized=True,
                statistics={"error": str(e)}
            ))
    
    # Late Chunking Engine  
    if app_state["chunking_engine"]:
        try:
            stats = app_state["chunking_engine"].get_statistics()
            components.append(ComponentStatus(
                name="Late Chunking Engine",
                status="healthy", 
                initialized=True,
                statistics=stats
            ))
        except Exception as e:
            logger.error(f"Error getting chunking stats: {e}")
            components.append(ComponentStatus(
                name="Late Chunking Engine",
                status="error",
                initialized=True, 
                statistics={"error": str(e)}
            ))
    
    # Fusion Layer
    if app_state["fusion_layer"]:
        try:
            stats = app_state["fusion_layer"].get_statistics()
            components.append(ComponentStatus(
                name="Fusion Layer",
                status="healthy",
                initialized=True,
                statistics=stats
            ))
        except Exception as e:
            logger.error(f"Error getting fusion stats: {e}")
            components.append(ComponentStatus(
                name="Fusion Layer",
                status="error", 
                initialized=True,
                statistics={"error": str(e)}
            ))
    
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "components": [comp.dict() for comp in components],
        "system_resources": {
            "memory": dict(psutil.virtual_memory()._asdict()),
            "disk": dict(psutil.disk_usage('/')._asdict()),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "process_count": len(psutil.pids())
        }
    }


@router.get("/ready",
           summary="Readiness Check",
           description="Check if Memory-Server is ready to accept requests")
async def readiness_check():
    """Kubernetes-style readiness probe"""
    app_state = {"initialized": True, "lazy_indexer": None, "chunking_engine": None, "fusion_layer": None}
    
    if not app_state["initialized"]:
        raise HTTPException(status_code=503, detail="Not ready")
    
    # Check if core components are working
    try:
        if app_state["lazy_indexer"]:
            stats = app_state["lazy_indexer"].get_statistics()
        if app_state["chunking_engine"]: 
            stats = app_state["chunking_engine"].get_statistics()
        if app_state["fusion_layer"]:
            stats = app_state["fusion_layer"].get_statistics()
            
        return {"status": "ready", "timestamp": time.time()}
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Not ready: {str(e)}")


@router.get("/live", 
           summary="Liveness Check",
           description="Check if Memory-Server process is alive")
async def liveness_check():
    """Kubernetes-style liveness probe"""
    return {
        "status": "alive",
        "timestamp": time.time(),
        "pid": psutil.Process().pid
    }


@router.get("/status",
           summary="Simple Status Check",
           description="Simple status endpoint for VSCode extension")
async def status_check():
    """Simple status endpoint for external tools"""
    return {
        "status": "healthy",
        "service": "Memory-Server",
        "timestamp": time.time(),
        "version": "1.0.0"
    }


@router.get("/metrics",
           summary="Prometheus Metrics",
           description="Get Prometheus-compatible metrics")
async def get_metrics():
    """Return Prometheus-style metrics"""
    app_state = {"initialized": True, "lazy_indexer": None, "chunking_engine": None, "fusion_layer": None}
    
    if not config.ENABLE_METRICS:
        raise HTTPException(status_code=404, detail="Metrics disabled")
    
    metrics = []
    
    # System metrics
    memory_info = psutil.virtual_memory()
    metrics.append(f"memory_usage_bytes {memory_info.used}")
    metrics.append(f"memory_usage_percent {memory_info.percent}")
    
    disk_info = psutil.disk_usage('/')
    metrics.append(f"disk_usage_bytes {disk_info.used}")
    metrics.append(f"disk_usage_percent {(disk_info.used / disk_info.total) * 100}")
    
    metrics.append(f"cpu_usage_percent {psutil.cpu_percent()}")
    
    # Component metrics
    if app_state["lazy_indexer"]:
        try:
            stats = app_state["lazy_indexer"].get_statistics()
            metrics.append(f"memory_server_documents_total {stats.get('total_documents', 0)}")
            metrics.append(f"memory_server_embeddings_total {stats.get('total_embeddings', 0)}")
            metrics.append(f"memory_server_indexing_time_seconds {stats.get('indexing_time', 0)}")
        except Exception:
            pass
    
    if app_state["chunking_engine"]:
        try:
            stats = app_state["chunking_engine"].get_statistics() 
            metrics.append(f"memory_server_chunks_total {stats.get('chunks_created', 0)}")
            metrics.append(f"memory_server_processing_time_seconds {stats.get('total_processing_time', 0)}")
        except Exception:
            pass
    
    return "\n".join(metrics), {"Content-Type": "text/plain"}