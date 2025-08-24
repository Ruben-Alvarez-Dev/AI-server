"""
Workflow Manager - Manages workflow execution and orchestration
"""

import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

from ...workflows import create_workflow, WORKFLOW_REGISTRY

logger = logging.getLogger(__name__)


class WorkflowManager:
    """Manages workflow instances and execution"""
    
    def __init__(self):
        self.workflows: Dict[str, Any] = {}
        self.agents_registry: Dict[str, Any] = {}
        self._initialized = False
    
    async def initialize(self, agents_registry: Dict[str, Any]):
        """Initialize workflow manager with agents"""
        logger.info("Initializing Workflow Manager...")
        
        self.agents_registry = agents_registry
        
        # Initialize all workflow types
        for workflow_type in WORKFLOW_REGISTRY.keys():
            try:
                workflow = await create_workflow(workflow_type, agents_registry)
                self.workflows[workflow_type] = workflow
                logger.info(f"Initialized {workflow_type} workflow")
            except Exception as e:
                logger.error(f"Failed to initialize {workflow_type} workflow: {e}")
        
        self._initialized = True
        logger.info("Workflow Manager initialized successfully")
    
    async def execute_workflow(self, workflow_type: str, request: str, context: Dict[str, Any] = None):
        """Execute a workflow"""
        if not self._initialized:
            raise RuntimeError("Workflow manager not initialized")
        
        if workflow_type not in self.workflows:
            raise ValueError(f"Workflow type '{workflow_type}' not available")
        
        workflow = self.workflows[workflow_type]
        return await workflow.execute(request, context)
    
    async def get_system_stats(self):
        """Get workflow system statistics"""
        return {
            "total_workflows": len(self.workflows),
            "available_workflows": list(self.workflows.keys()),
            "status": "operational"
        }
    
    async def shutdown(self):
        """Shutdown workflow manager"""
        logger.info("Shutting down Workflow Manager...")
        # Add cleanup logic here
        self.workflows.clear()
        logger.info("Workflow Manager shutdown complete")