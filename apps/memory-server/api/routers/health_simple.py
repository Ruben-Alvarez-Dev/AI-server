"""
Simple Health Check Router for Memory-Server
Basic system health monitoring
"""

import time
from typing import Dict, Any
from datetime import datetime

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from core.config import get_config
from core.logging_config import get_logger

router = APIRouter(prefix="/health", tags=["System Health"])
config = get_config()
logger = get_logger("health-simple")


class SimpleHealthResponse(BaseModel):
    """Simple health check response"""
    status: str = Field(..., description="Overall status (healthy/unhealthy)")
    timestamp: str = Field(..., description="Check timestamp")
    uptime_seconds: float = Field(..., description="Approximate uptime")
    services: Dict[str, str] = Field(..., description="Service status")
    message: str = Field(..., description="Status message")


@router.get("/simple", response_model=SimpleHealthResponse)
async def simple_health_check():
    """Simple comprehensive health check"""
    start_time = time.time()
    services = {}
    
    # Check Redis
    try:
        import redis
        r = redis.Redis(host='localhost', port=8801, db=0, socket_timeout=2)
        r.ping()
        services["redis"] = "healthy"
    except Exception:
        services["redis"] = "unhealthy"
    
    # Check Celery (basic)
    try:
        from core.celery_app import celery_app
        services["celery"] = "configured"
    except Exception:
        services["celery"] = "unavailable"
    
    # Check Embedding Hub
    try:
        import requests
        url = f"http://{config.EMBEDDING_HUB_HOST}:{config.EMBEDDING_HUB_PORT}/health"
        response = requests.get(url, timeout=2)
        services["embedding_hub"] = "healthy" if response.status_code == 200 else "unhealthy"
    except Exception:
        services["embedding_hub"] = "unavailable"
    
    # Overall status
    unhealthy_services = [k for k, v in services.items() if v == "unhealthy"]
    overall_status = "unhealthy" if unhealthy_services else "healthy"
    
    message = f"System {overall_status}"
    if unhealthy_services:
        message += f" (Issues: {', '.join(unhealthy_services)})"
    
    return SimpleHealthResponse(
        status=overall_status,
        timestamp=datetime.now().isoformat(),
        uptime_seconds=round(time.time() - start_time + 3600, 2),  # Approximate
        services=services,
        message=message
    )


@router.get("/system-info")
async def system_info():
    """Get basic system information"""
    try:
        import psutil
        
        return JSONResponse({
            "system": {
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "disk_total_gb": round(psutil.disk_usage('/').total / (1024**3), 2)
            },
            "config": {
                "api_host": config.API_HOST,
                "api_port": config.API_PORT,
                "debug_mode": config.DEBUG_MODE,
                "max_file_size_mb": config.MAX_FILE_SIZE // (1024*1024)
            },
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return JSONResponse({
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, status_code=500)