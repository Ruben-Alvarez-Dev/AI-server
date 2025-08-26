"""
Agent Router - Endpoints for agent management
"""

from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any, Optional

router = APIRouter()


@router.get("/status")
async def get_agents_status(request: Request, agent_type: Optional[str] = None):
    """Get status of agents"""
    try:
        agent_manager = getattr(request.app.state, 'agent_manager', None)
        if not agent_manager:
            raise HTTPException(status_code=503, detail="Agent manager not available")
        
        status = await agent_manager.get_agent_status(agent_type)
        return {"agents": status}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/types")
async def list_agent_types():
    """List available agent types"""
    from ...agents import AGENT_REGISTRY
    
    return {
        "agent_types": list(AGENT_REGISTRY.keys()),
        "details": {
            agent_type: info["description"]
            for agent_type, info in AGENT_REGISTRY.items()
        }
    }