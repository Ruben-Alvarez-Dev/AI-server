"""
Base Workflow - Core LangGraph workflow infrastructure
Provides base classes and utilities for all specialized workflows
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable, TypedDict
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json

try:
    from langgraph import StateGraph, START, END
    from langgraph.graph import Graph
    from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    StateGraph = None
    START = "START"
    END = "END"
    Graph = None
    BaseMessage = None
    HumanMessage = None
    AIMessage = None


logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


@dataclass
class WorkflowTask:
    """Individual task within a workflow"""
    task_id: str
    agent_type: str
    task_description: str
    input_data: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    priority: TaskPriority = TaskPriority.MEDIUM
    timeout: int = 300  # seconds
    retry_count: int = 3
    status: WorkflowStatus = WorkflowStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class WorkflowState(TypedDict):
    """Base workflow state structure"""
    request_id: str
    original_request: str
    context: Dict[str, Any]
    tasks: Dict[str, WorkflowTask]
    current_task: Optional[str]
    results: Dict[str, Any]
    errors: List[str]
    status: WorkflowStatus
    start_time: datetime
    end_time: Optional[datetime]
    metadata: Dict[str, Any]


class BaseWorkflow:
    """Base class for all LangGraph workflows"""
    
    def __init__(self, name: str):
        if not LANGGRAPH_AVAILABLE:
            raise ImportError("LangGraph not available. Install with: pip install langgraph")
        
        self.name = name
        self.graph: Optional[StateGraph] = None
        self.compiled_graph: Optional[Graph] = None
        self.agents_registry: Dict[str, Any] = {}
        self.active_executions: Dict[str, Dict[str, Any]] = {}
        
        # Performance tracking
        self.execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "average_execution_time": 0.0,
            "agent_usage": {}
        }
        
    async def initialize(self, agents_registry: Dict[str, Any]):
        """Initialize workflow with agent registry"""
        self.agents_registry = agents_registry
        await self._build_graph()
        logger.info(f"Workflow '{self.name}' initialized successfully")
    
    async def _build_graph(self):
        """Build the LangGraph workflow - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement _build_graph")
    
    def _create_initial_state(self, request: str, context: Optional[Dict] = None) -> WorkflowState:
        """Create initial workflow state"""
        request_id = f"{self.name}_{datetime.now().isoformat()}"
        
        return WorkflowState(
            request_id=request_id,
            original_request=request,
            context=context or {},
            tasks={},
            current_task=None,
            results={},
            errors=[],
            status=WorkflowStatus.PENDING,
            start_time=datetime.now(),
            end_time=None,
            metadata={"workflow_type": self.name}
        )
    
    async def execute(self, request: str, context: Optional[Dict] = None) -> WorkflowState:
        """Execute the workflow"""
        if not self.compiled_graph:
            raise RuntimeError("Workflow not initialized. Call initialize() first.")
        
        initial_state = self._create_initial_state(request, context)
        request_id = initial_state["request_id"]
        
        try:
            logger.info(f"Starting workflow execution: {request_id}")
            self.active_executions[request_id] = {
                "start_time": datetime.now(),
                "status": WorkflowStatus.RUNNING
            }
            
            # Execute the workflow graph
            final_state = await self._execute_workflow(initial_state)
            
            # Update statistics
            self._update_execution_stats(final_state, success=True)
            
            logger.info(f"Workflow execution completed: {request_id}")
            return final_state
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {request_id} - {str(e)}")
            
            # Create failed state
            failed_state = initial_state.copy()
            failed_state["status"] = WorkflowStatus.FAILED
            failed_state["end_time"] = datetime.now()
            failed_state["errors"].append(str(e))
            
            self._update_execution_stats(failed_state, success=False)
            
            return failed_state
            
        finally:
            # Cleanup active execution tracking
            if request_id in self.active_executions:
                del self.active_executions[request_id]
    
    async def _execute_workflow(self, initial_state: WorkflowState) -> WorkflowState:
        """Execute the compiled workflow graph"""
        try:
            # Run the LangGraph workflow
            result = await self.compiled_graph.ainvoke(initial_state)
            
            # Ensure we return a proper WorkflowState
            if isinstance(result, dict):
                # Update the state with execution results
                final_state = initial_state.copy()
                final_state.update(result)
                final_state["end_time"] = datetime.now()
                
                # Set status based on errors
                if final_state.get("errors"):
                    final_state["status"] = WorkflowStatus.FAILED
                else:
                    final_state["status"] = WorkflowStatus.COMPLETED
                
                return final_state
            else:
                # Fallback if result is not a dict
                final_state = initial_state.copy()
                final_state["results"]["workflow_result"] = result
                final_state["status"] = WorkflowStatus.COMPLETED
                final_state["end_time"] = datetime.now()
                return final_state
                
        except Exception as e:
            logger.error(f"Workflow graph execution failed: {str(e)}")
            raise
    
    async def get_execution_status(self, request_id: str) -> Dict[str, Any]:
        """Get current execution status"""
        if request_id in self.active_executions:
            execution = self.active_executions[request_id]
            runtime = datetime.now() - execution["start_time"]
            
            return {
                "request_id": request_id,
                "status": execution["status"].value,
                "runtime_seconds": runtime.total_seconds(),
                "current_task": execution.get("current_task"),
            }
        else:
            return {
                "request_id": request_id,
                "status": "not_found",
                "message": "Execution not found or completed"
            }
    
    def _update_execution_stats(self, state: WorkflowState, success: bool):
        """Update workflow execution statistics"""
        self.execution_stats["total_executions"] += 1
        
        if success:
            self.execution_stats["successful_executions"] += 1
        else:
            self.execution_stats["failed_executions"] += 1
        
        # Calculate execution time
        if state.get("start_time") and state.get("end_time"):
            execution_time = (state["end_time"] - state["start_time"]).total_seconds()
            
            # Update rolling average
            total_execs = self.execution_stats["total_executions"]
            current_avg = self.execution_stats["average_execution_time"]
            new_avg = ((current_avg * (total_execs - 1)) + execution_time) / total_execs
            self.execution_stats["average_execution_time"] = new_avg
        
        # Track agent usage
        for task in state.get("tasks", {}).values():
            agent_type = task.agent_type
            if agent_type not in self.execution_stats["agent_usage"]:
                self.execution_stats["agent_usage"][agent_type] = 0
            self.execution_stats["agent_usage"][agent_type] += 1
    
    def get_workflow_stats(self) -> Dict[str, Any]:
        """Get workflow performance statistics"""
        return {
            "workflow_name": self.name,
            "statistics": self.execution_stats.copy(),
            "active_executions": len(self.active_executions),
            "graph_compiled": self.compiled_graph is not None,
            "agents_available": list(self.agents_registry.keys())
        }
    
    async def cancel_execution(self, request_id: str) -> bool:
        """Cancel an active workflow execution"""
        if request_id in self.active_executions:
            self.active_executions[request_id]["status"] = WorkflowStatus.CANCELLED
            logger.info(f"Cancelled workflow execution: {request_id}")
            return True
        return False
    
    def validate_workflow_config(self) -> Dict[str, Any]:
        """Validate workflow configuration"""
        issues = []
        warnings = []
        
        if not self.compiled_graph:
            issues.append("Workflow graph not compiled")
        
        if not self.agents_registry:
            issues.append("No agents registered")
        
        # Check for common configuration issues
        required_agents = self._get_required_agents()
        for agent_type in required_agents:
            if agent_type not in self.agents_registry:
                issues.append(f"Required agent '{agent_type}' not available")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "required_agents": required_agents,
            "available_agents": list(self.agents_registry.keys())
        }
    
    def _get_required_agents(self) -> List[str]:
        """Get list of required agents for this workflow - override in subclasses"""
        return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the workflow"""
        try:
            validation = self.validate_workflow_config()
            
            return {
                "workflow_name": self.name,
                "status": "healthy" if validation["valid"] else "unhealthy",
                "graph_compiled": self.compiled_graph is not None,
                "agents_available": len(self.agents_registry),
                "active_executions": len(self.active_executions),
                "total_executions": self.execution_stats["total_executions"],
                "success_rate": (
                    self.execution_stats["successful_executions"] / 
                    max(1, self.execution_stats["total_executions"])
                ) * 100,
                "validation": validation
            }
            
        except Exception as e:
            return {
                "workflow_name": self.name,
                "status": "unhealthy",
                "error": str(e)
            }


# Utility functions for workflow nodes
async def route_to_agent(state: WorkflowState, agent_type: str, task_description: str) -> Dict[str, Any]:
    """Route task to specific agent"""
    logger.info(f"Routing to agent: {agent_type} - {task_description}")
    
    # Create task
    task_id = f"{agent_type}_{datetime.now().isoformat()}"
    task = WorkflowTask(
        task_id=task_id,
        agent_type=agent_type,
        task_description=task_description,
        input_data={"request": state["original_request"], "context": state["context"]}
    )
    
    # Add to state
    state["tasks"][task_id] = task
    state["current_task"] = task_id
    
    return {"current_task": task_id, "tasks": state["tasks"]}


async def execute_agent_task(state: WorkflowState, agents_registry: Dict[str, Any]) -> Dict[str, Any]:
    """Execute current agent task"""
    current_task_id = state.get("current_task")
    if not current_task_id:
        return {"errors": state["errors"] + ["No current task to execute"]}
    
    task = state["tasks"][current_task_id]
    agent_type = task.agent_type
    
    if agent_type not in agents_registry:
        error = f"Agent type '{agent_type}' not available"
        task.error = error
        task.status = WorkflowStatus.FAILED
        return {"errors": state["errors"] + [error]}
    
    try:
        # Get agent and execute task
        agent = agents_registry[agent_type]
        
        # Mark task as running
        task.status = WorkflowStatus.RUNNING
        task.start_time = datetime.now()
        
        # Execute based on agent type (this would be implemented per agent)
        result = await _execute_task_by_agent_type(agent, task)
        
        # Mark task as completed
        task.status = WorkflowStatus.COMPLETED
        task.end_time = datetime.now()
        task.result = result
        
        # Update state results
        state["results"][current_task_id] = result
        
        return {"results": state["results"], "tasks": state["tasks"]}
        
    except Exception as e:
        error_msg = f"Task execution failed: {str(e)}"
        logger.error(error_msg)
        
        task.status = WorkflowStatus.FAILED
        task.end_time = datetime.now()
        task.error = error_msg
        
        return {"errors": state["errors"] + [error_msg], "tasks": state["tasks"]}


async def _execute_task_by_agent_type(agent: Any, task: WorkflowTask) -> Dict[str, Any]:
    """Execute task based on agent type - simplified implementation"""
    # This is a simplified version - in reality each agent type would have specific methods
    
    if hasattr(agent, 'process_request'):
        return await agent.process_request(task.input_data)
    elif hasattr(agent, 'execute'):
        return await agent.execute(task.task_description, task.input_data)
    else:
        # Fallback - just return the task description as completed
        return {
            "task_completed": task.task_description,
            "agent_type": task.agent_type,
            "status": "completed"
        }