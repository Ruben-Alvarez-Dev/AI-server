"""
Monitoring Router - System monitoring and metrics endpoints
"""

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/stats")
async def get_system_stats(request: Request):
    """Get system statistics"""
    try:
        agent_manager = getattr(request.app.state, 'agent_manager', None)
        
        stats = {}
        
        if agent_manager:
            stats["agents"] = await agent_manager.get_system_stats()
        
        return {"system_stats": stats}
        
    except Exception as e:
        return {"error": str(e)}


@router.get("/metrics")  
async def get_metrics():
    """Get system metrics"""
    return {"message": "Metrics endpoint - to be implemented"}