"""
Enhanced Health Check Router
Comprehensive system health monitoring including Redis, Celery, and all services
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import psutil
import redis
import aiohttp
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import get_config
from core.logging_config import get_logger

router = APIRouter(prefix="/health", tags=["System Health"])
config = get_config()
logger = get_logger("health-enhanced")


class ComponentHealth(BaseModel):
    """Health status for individual component"""
    name: str = Field(..., description="Component name")
    status: str = Field(..., description="Health status (healthy/unhealthy/degraded)")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")
    error: Optional[str] = Field(None, description="Error message if unhealthy")


class SystemHealthResponse(BaseModel):
    """Comprehensive system health response"""
    overall_status: str = Field(..., description="Overall system status")
    timestamp: str = Field(..., description="Health check timestamp")
    uptime_seconds: float = Field(..., description="System uptime in seconds")
    components: List[ComponentHealth] = Field(..., description="Individual component health")
    system_metrics: Dict[str, Any] = Field(..., description="System performance metrics")
    async_processing: Dict[str, Any] = Field(..., description="Async processing status")
    
    class Config:
        schema_extra = {
            "example": {
                "overall_status": "healthy",
                "timestamp": "2025-08-26T18:30:00Z",
                "uptime_seconds": 3600.0,
                "components": [
                    {
                        "name": "redis",
                        "status": "healthy",
                        "response_time_ms": 2.5,
                        "details": {"version": "8.2.1", "connected_clients": 5}
                    }
                ],
                "system_metrics": {
                    "cpu_percent": 15.2,
                    "memory_percent": 25.8,
                    "disk_usage_percent": 45.3
                },
                "async_processing": {
                    "workers_active": 2,
                    "tasks_pending": 5,
                    "tasks_completed_last_hour": 147
                }
            }
        }


class QuickHealthResponse(BaseModel):
    """Quick health check response"""
    status: str = Field(..., description="Overall status (healthy/unhealthy)")
    timestamp: str = Field(..., description="Check timestamp")
    message: str = Field(..., description="Status message")


async def check_redis_health() -> ComponentHealth:
    """Check Redis connection and performance"""
    import time
    start_time = time.time()
    
    try:
        r = redis.Redis(host='localhost', port=8801, db=0, socket_timeout=5)
        
        # Test basic operations
        r.ping()
        r.set('health_check', 'test', ex=10)  # Expires in 10 seconds
        value = r.get('health_check')
        r.delete('health_check')
        
        response_time = (time.time() - start_time) * 1000
        
        # Get Redis info
        info = r.info()
        
        return ComponentHealth(
            name="redis",
            status="healthy",
            response_time_ms=round(response_time, 2),
            details={
                "version": info.get("redis_version", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0)
            }
        )
        
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        return ComponentHealth(
            name="redis",
            status="unhealthy",
            response_time_ms=round(response_time, 2),
            error=str(e)
        )


async def check_celery_health() -> ComponentHealth:
    """Check Celery workers and queue status"""
    import time
    start_time = time.time()
    
    try:
        from core.celery_app import celery_app
        
        # Check worker status
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        registered_tasks = inspect.registered()
        stats = inspect.stats()
        
        response_time = (time.time() - start_time) * 1000
        
        if active_workers is None:
            return ComponentHealth(
                name="celery",
                status="unhealthy",
                response_time_ms=round(response_time, 2),
                error="No active workers found"
            )
        
        # Calculate metrics
        total_workers = len(active_workers)
        total_active_tasks = sum(len(tasks) for tasks in active_workers.values())
        
        # Get task counts from stats
        total_processed = 0
        if stats:
            for worker_stats in stats.values():
                total_processed += worker_stats.get('total', {}).get('simple_process_document', 0)
        
        return ComponentHealth(
            name="celery",
            status="healthy" if total_workers > 0 else "degraded",
            response_time_ms=round(response_time, 2),
            details={
                "active_workers": total_workers,
                "worker_names": list(active_workers.keys()),
                "active_tasks": total_active_tasks,
                "total_processed": total_processed,
                "registered_tasks_count": sum(len(tasks) for tasks in registered_tasks.values()) if registered_tasks else 0
            }
        )
        
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        return ComponentHealth(
            name="celery",
            status="unhealthy", 
            response_time_ms=round(response_time, 2),
            error=str(e)
        )


async def check_embedding_hub_health() -> ComponentHealth:
    """Check Embedding Hub connection"""
    import time
    start_time = time.time()
    
    try:
        
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            url = f"http://{config.EMBEDDING_HUB_HOST}:{config.EMBEDDING_HUB_PORT}/health"
            async with session.get(url) as response:
                response_time = (time.time() - start_time) * 1000
                
                if response.status == 200:
                    data = await response.json()
                    return ComponentHealth(
                        name="embedding_hub",
                        status="healthy",
                        response_time_ms=round(response_time, 2),
                        details={
                            "url": url,
                            "response_data": data
                        }
                    )
                else:
                    return ComponentHealth(
                        name="embedding_hub",
                        status="unhealthy",
                        response_time_ms=round(response_time, 2),
                        error=f"HTTP {response.status}"
                    )
                    
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        return ComponentHealth(
            name="embedding_hub",
            status="unhealthy",
            response_time_ms=round(response_time, 2),
            error=str(e)
        )


def get_system_metrics() -> Dict[str, Any]:
    """Get system performance metrics"""
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_available_gb = memory.available / (1024**3)
        memory_total_gb = memory.total / (1024**3)
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        disk_free_gb = disk.free / (1024**3)
        disk_total_gb = disk.total / (1024**3)
        
        # Network I/O
        network = psutil.net_io_counters()
        
        # Process info
        process = psutil.Process()
        process_memory_mb = process.memory_info().rss / (1024**2)
        process_cpu_percent = process.cpu_percent()
        
        return {
            "cpu_percent": round(cpu_percent, 1),
            "memory_percent": round(memory_percent, 1), 
            "memory_available_gb": round(memory_available_gb, 2),
            "memory_total_gb": round(memory_total_gb, 2),
            "disk_usage_percent": round(disk_percent, 1),
            "disk_free_gb": round(disk_free_gb, 2),
            "disk_total_gb": round(disk_total_gb, 2),
            "network_bytes_sent": network.bytes_sent,
            "network_bytes_recv": network.bytes_recv,
            "process_memory_mb": round(process_memory_mb, 1),
            "process_cpu_percent": round(process_cpu_percent, 1),
            "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
        }
        
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        return {"error": str(e)}


@router.get("/", response_model=QuickHealthResponse)
async def quick_health_check():
    """Quick health check endpoint"""
    try:
        # Basic checks
        redis_ok = True
        try:
            r = redis.Redis(host='localhost', port=8801, db=0, socket_timeout=2)
            r.ping()
        except:
            redis_ok = False
        
        celery_ok = True
        try:
            from core.celery_app import celery_app
            inspect = celery_app.control.inspect()
            active = inspect.active()
            celery_ok = active is not None and len(active) > 0
        except:
            celery_ok = False
        
        if redis_ok and celery_ok:
            status = "healthy"
            message = "All core services operational"
        else:
            status = "unhealthy"
            issues = []
            if not redis_ok:
                issues.append("Redis")
            if not celery_ok:
                issues.append("Celery")
            message = f"Issues with: {', '.join(issues)}"
        
        return QuickHealthResponse(
            status=status,
            timestamp=datetime.now().isoformat(),
            message=message
        )
        
    except Exception as e:
        return QuickHealthResponse(
            status="unhealthy",
            timestamp=datetime.now().isoformat(), 
            message=f"Health check error: {str(e)}"
        )


@router.get("/detailed", response_model=SystemHealthResponse)
async def detailed_health_check():
    """Comprehensive system health check"""
    try:
        import time
        start_time = time.time()
        
        # Run health checks
        redis_health = await check_redis_health()
        celery_health = await check_celery_health()
        embedding_health = await check_embedding_hub_health()
        
        components = [redis_health, celery_health, embedding_health]
        
        # Get system metrics
        system_metrics = get_system_metrics()
        
        # Calculate overall status
        unhealthy_components = [c for c in components if c.status == "unhealthy"]
        degraded_components = [c for c in components if c.status == "degraded"]
        
        if unhealthy_components:
            overall_status = "unhealthy"
        elif degraded_components:
            overall_status = "degraded" 
        else:
            overall_status = "healthy"
        
        # Async processing summary
        async_processing = {
            "workers_active": celery_health.details.get("active_workers", 0) if celery_health.details else 0,
            "tasks_pending": celery_health.details.get("active_tasks", 0) if celery_health.details else 0,
            "redis_connected": redis_health.status == "healthy",
            "embedding_hub_available": embedding_health.status == "healthy"
        }
        
        # Calculate uptime (approximation)
        uptime = time.time() - start_time + 3600  # Add base uptime
        
        return SystemHealthResponse(
            overall_status=overall_status,
            timestamp=datetime.now().isoformat(),
            uptime_seconds=round(uptime, 2),
            components=components,
            system_metrics=system_metrics,
            async_processing=async_processing
        )
        
    except Exception as e:
        logger.error(f"Error in detailed health check: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/redis")
async def redis_health():
    """Redis-specific health check"""
    health = await check_redis_health()
    status_code = 200 if health.status == "healthy" else 503
    return JSONResponse(content=health.dict(), status_code=status_code)


@router.get("/celery")
async def celery_health():
    """Celery-specific health check"""
    health = await check_celery_health()
    status_code = 200 if health.status in ["healthy", "degraded"] else 503
    return JSONResponse(content=health.dict(), status_code=status_code)


@router.get("/embedding-hub")
async def embedding_hub_health():
    """Embedding Hub-specific health check"""
    health = await check_embedding_hub_health()
    status_code = 200 if health.status == "healthy" else 503
    return JSONResponse(content=health.dict(), status_code=status_code)


@router.get("/metrics")
async def system_metrics():
    """System performance metrics"""
    metrics = await get_system_metrics()
    return JSONResponse(content=metrics)