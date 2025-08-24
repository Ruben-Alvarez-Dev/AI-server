"""
Request Manager - Manages request lifecycle and execution
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class RequestManager:
    """Manages request processing and workflow execution"""
    
    def __init__(self, agent_manager=None, workflow_manager=None, max_concurrent=10, timeout=600):
        self.agent_manager = agent_manager
        self.workflow_manager = workflow_manager
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.active_requests: Dict[str, Any] = {}
    
    async def execute_workflow(self, request: str, workflow_type: Optional[str] = None, context: Dict[str, Any] = None):
        """Execute a workflow request"""
        # Auto-detect workflow type if not specified
        if not workflow_type:
            workflow_type = self._detect_workflow_type(request, context)
        
        # Generate request ID
        request_id = f"req_{datetime.now().isoformat()}"
        
        # Execute workflow
        try:
            result = await self.workflow_manager.execute_workflow(
                workflow_type=workflow_type,
                request=request,
                context=context or {}
            )
            
            return {
                "request_id": request_id,
                "workflow_type": workflow_type,
                "status": "completed",
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return {
                "request_id": request_id,
                "workflow_type": workflow_type,
                "status": "failed",
                "error": str(e)
            }
    
    def _detect_workflow_type(self, request: str, context: Dict[str, Any] = None) -> str:
        """Auto-detect appropriate workflow type"""
        from ...workflows import recommend_workflow
        return recommend_workflow(request, context)
    
    async def shutdown(self):
        """Shutdown request manager"""
        logger.info("Request Manager shutdown")