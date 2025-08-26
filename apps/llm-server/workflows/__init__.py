"""
LLM Server Workflows Module - LangGraph workflow orchestration

This module provides specialized workflows for different development scenarios:

- BaseWorkflow: Core workflow infrastructure and utilities
- DevelopmentWorkflow: Main comprehensive development workflow  
- QuickFixWorkflow: Rapid debugging and fixing workflow
- CodeReviewWorkflow: Thorough code review and quality assurance

Each workflow orchestrates multiple AI agents to handle complex multi-step tasks
efficiently using LangGraph's state management and conditional routing.
"""

from .base_workflow import (
    BaseWorkflow,
    WorkflowState,
    WorkflowStatus,
    TaskPriority,
    WorkflowTask,
    route_to_agent,
    execute_agent_task
)

from .development_workflow import (
    DevelopmentWorkflow,
    DevelopmentState,
    create_development_workflow
)

from .quick_fix_workflow import (
    QuickFixWorkflow,
    QuickFixState,
    create_quick_fix_workflow
)

from .code_review_workflow import (
    CodeReviewWorkflow,
    CodeReviewState,
    create_code_review_workflow
)

__all__ = [
    # Base workflow infrastructure
    "BaseWorkflow",
    "WorkflowState", 
    "WorkflowStatus",
    "TaskPriority",
    "WorkflowTask",
    "route_to_agent",
    "execute_agent_task",
    
    # Development workflow
    "DevelopmentWorkflow",
    "DevelopmentState",
    "create_development_workflow",
    
    # Quick fix workflow
    "QuickFixWorkflow", 
    "QuickFixState",
    "create_quick_fix_workflow",
    
    # Code review workflow
    "CodeReviewWorkflow",
    "CodeReviewState", 
    "create_code_review_workflow"
]


# Workflow registry for easy access
WORKFLOW_REGISTRY = {
    "development": {
        "class": DevelopmentWorkflow,
        "factory": create_development_workflow,
        "description": "Comprehensive development workflow with full agent orchestration",
        "suitable_for": [
            "Complex implementation tasks",
            "New feature development", 
            "Architecture-heavy projects",
            "Multi-step development workflows"
        ],
        "agents_used": ["router", "architect", "coder_primary", "coder_secondary", "qa_checker", "debugger"],
        "typical_duration": "5-30 minutes",
        "complexity": "high"
    },
    
    "quick_fix": {
        "class": QuickFixWorkflow,
        "factory": create_quick_fix_workflow,
        "description": "Rapid issue resolution with minimal overhead",
        "suitable_for": [
            "Bug fixes and quick patches",
            "Immediate issue resolution",
            "Simple debugging tasks",
            "Emergency fixes"
        ],
        "agents_used": ["router", "debugger", "coder_primary"],
        "typical_duration": "1-5 minutes", 
        "complexity": "low"
    },
    
    "code_review": {
        "class": CodeReviewWorkflow,
        "factory": create_code_review_workflow,
        "description": "Comprehensive code review and quality assessment",
        "suitable_for": [
            "Code quality assessment",
            "Pre-deployment reviews",
            "Security audits",
            "Best practices validation"
        ],
        "agents_used": ["router", "qa_checker", "debugger", "coder_primary"],
        "typical_duration": "3-15 minutes",
        "complexity": "medium"
    }
}


async def create_workflow(workflow_type: str, agents_registry: dict):
    """Create and initialize a workflow by type"""
    if workflow_type not in WORKFLOW_REGISTRY:
        available_types = ", ".join(WORKFLOW_REGISTRY.keys())
        raise ValueError(f"Unknown workflow type: {workflow_type}. Available: {available_types}")
    
    workflow_info = WORKFLOW_REGISTRY[workflow_type]
    factory = workflow_info["factory"]
    
    return await factory(agents_registry)


def get_workflow_info(workflow_type: str) -> dict:
    """Get information about a workflow type"""
    if workflow_type not in WORKFLOW_REGISTRY:
        raise ValueError(f"Unknown workflow type: {workflow_type}")
    
    return WORKFLOW_REGISTRY[workflow_type].copy()


def list_available_workflows() -> dict:
    """List all available workflow types with descriptions"""
    return {
        workflow_type: {
            "description": info["description"],
            "suitable_for": info["suitable_for"],
            "typical_duration": info["typical_duration"],
            "complexity": info["complexity"]
        }
        for workflow_type, info in WORKFLOW_REGISTRY.items()
    }


def recommend_workflow(task_description: str, context: dict = None) -> str:
    """Recommend the best workflow for a given task"""
    task_lower = task_description.lower()
    context = context or {}
    
    # Simple heuristic-based recommendation
    urgency_indicators = ["urgent", "emergency", "quick", "immediate", "hotfix", "critical"]
    review_indicators = ["review", "quality", "check", "audit", "validate", "assess"]
    complex_indicators = ["architecture", "design", "system", "complex", "large", "comprehensive"]
    
    # Check for urgency
    if any(indicator in task_lower for indicator in urgency_indicators):
        return "quick_fix"
    
    # Check for review tasks
    if any(indicator in task_lower for indicator in review_indicators):
        return "code_review"
    
    # Check for complexity
    if any(indicator in task_lower for indicator in complex_indicators):
        return "development"
    
    # Check context for hints
    if context.get("priority") == "urgent":
        return "quick_fix"
    elif context.get("task_type") in ["code_review", "quality_check"]:
        return "code_review"
    
    # Default to development workflow
    return "development"


async def get_workflow_health_status(workflow_type: str, agents_registry: dict) -> dict:
    """Get health status for a specific workflow type"""
    try:
        if workflow_type not in WORKFLOW_REGISTRY:
            return {
                "workflow_type": workflow_type,
                "status": "unknown",
                "error": f"Unknown workflow type: {workflow_type}"
            }
        
        # Create workflow instance
        workflow = await create_workflow(workflow_type, agents_registry)
        
        # Get health check
        health = await workflow.health_check()
        
        # Add workflow-specific information
        workflow_info = WORKFLOW_REGISTRY[workflow_type]
        health.update({
            "workflow_type": workflow_type,
            "description": workflow_info["description"],
            "required_agents": workflow_info["agents_used"],
            "missing_agents": [
                agent for agent in workflow_info["agents_used"]
                if agent not in agents_registry
            ]
        })
        
        return health
        
    except Exception as e:
        return {
            "workflow_type": workflow_type,
            "status": "unhealthy",
            "error": str(e)
        }


async def get_all_workflows_health(agents_registry: dict) -> dict:
    """Get health status for all available workflows"""
    health_results = {}
    
    for workflow_type in WORKFLOW_REGISTRY.keys():
        health_results[workflow_type] = await get_workflow_health_status(
            workflow_type, agents_registry
        )
    
    # Calculate overall health
    healthy_workflows = [
        w for w in health_results.values() 
        if w.get("status") == "healthy"
    ]
    
    overall_health = {
        "total_workflows": len(WORKFLOW_REGISTRY),
        "healthy_workflows": len(healthy_workflows),
        "health_percentage": (len(healthy_workflows) / len(WORKFLOW_REGISTRY)) * 100,
        "overall_status": "healthy" if len(healthy_workflows) == len(WORKFLOW_REGISTRY) else "degraded",
        "workflow_details": health_results
    }
    
    return overall_health