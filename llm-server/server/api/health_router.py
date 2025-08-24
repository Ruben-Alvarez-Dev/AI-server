"""
Health Check Router - System health and status endpoints
"""

from fastapi import APIRouter, Request
from typing import Dict, Any


router = APIRouter()


@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "llm-server",
        "version": "0.1.0"
    }


@router.get("/detailed")
async def detailed_health_check(request: Request):
    """Detailed health check with system status"""
    try:
        # Get managers from app state
        agent_manager = getattr(request.app.state, 'agent_manager', None)
        workflow_manager = getattr(request.app.state, 'workflow_manager', None)
        
        health_data = {
            "status": "healthy",
            "service": "llm-server", 
            "version": "0.1.0",
            "components": {
                "agent_manager": "unknown",
                "workflow_manager": "unknown"
            }
        }
        
        # Check agent manager
        if agent_manager:
            try:
                agent_stats = await agent_manager.get_system_stats()
                health_data["components"]["agent_manager"] = "healthy"
                health_data["agents"] = agent_stats
            except Exception as e:
                health_data["components"]["agent_manager"] = f"unhealthy: {str(e)}"
        
        # Check workflow manager  
        if workflow_manager:
            try:
                workflow_stats = await workflow_manager.get_system_stats()
                health_data["components"]["workflow_manager"] = "healthy"
                health_data["workflows"] = workflow_stats
            except Exception as e:
                health_data["components"]["workflow_manager"] = f"unhealthy: {str(e)}"
        
        # Determine overall status
        unhealthy_components = [
            comp for comp in health_data["components"].values() 
            if "unhealthy" in str(comp).lower()
        ]
        
        if unhealthy_components:
            health_data["status"] = "degraded"
        
        return health_data
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }