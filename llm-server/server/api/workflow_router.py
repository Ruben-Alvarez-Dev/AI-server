"""
Workflow Router - Endpoints for workflow execution
"""

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

router = APIRouter()


class WorkflowRequest(BaseModel):
    """Workflow execution request"""
    request: str
    workflow_type: Optional[str] = None
    context: Optional[Dict[str, Any]] = {}
    priority: Optional[str] = "medium"


class WorkflowResponse(BaseModel):
    """Workflow execution response"""
    request_id: str
    status: str
    workflow_type: str
    message: str


@router.post("/execute", response_model=WorkflowResponse)
async def execute_workflow(
    workflow_request: WorkflowRequest,
    request: Request,
    background_tasks: BackgroundTasks
):
    """Execute a development workflow"""
    try:
        request_manager = getattr(request.app.state, 'request_manager', None)
        if not request_manager:
            raise HTTPException(status_code=503, detail="Request manager not available")
        
        # Execute workflow
        result = await request_manager.execute_workflow(
            request=workflow_request.request,
            workflow_type=workflow_request.workflow_type,
            context=workflow_request.context
        )
        
        return WorkflowResponse(
            request_id=result.get("request_id", "unknown"),
            status=result.get("status", "unknown"),
            workflow_type=result.get("workflow_type", "unknown"),
            message="Workflow executed successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/types")
async def list_workflow_types():
    """List available workflow types"""
    from ...workflows import WORKFLOW_REGISTRY
    
    return {
        "workflow_types": list(WORKFLOW_REGISTRY.keys()),
        "details": {
            wf_type: {
                "description": info["description"],
                "suitable_for": info["suitable_for"]
            }
            for wf_type, info in WORKFLOW_REGISTRY.items()
        }
    }