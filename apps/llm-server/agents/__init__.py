"""
LLM Server Agents Module - Specialized AI agents for development tasks

This module provides a complete set of specialized agents for software development:

- RouterAgent: Ultra-fast request routing (Qwen2-1.5B)
- ArchitectAgent: High-level system design (Qwen2.5-32B) 
- PrimaryCoderAgent: High-performance coding (Qwen2.5-Coder-7B)
- SecondaryCoderAgent: Efficient backup coding (DeepSeek-Coder-V2-16B MoE)
- QACheckerAgent: Quality assurance and testing (Qwen2.5-14B)
- DebuggerAgent: Error analysis and debugging (DeepSeek-Coder-V2-16B)

Each agent is optimized for M1 Ultra hardware with specialized capabilities
and efficient resource usage through model pooling.
"""

from .router import (
    RouterAgent,
    get_router_agent,
    TaskType,
    Priority,
    RoutingDecision
)

from .architect import (
    ArchitectAgent,
    get_architect_agent,
    ArchitecturalPlan,
    ArchitecturalPattern,
    ComplexityLevel
)

from .coders import (
    PrimaryCoderAgent,
    SecondaryCoderAgent,
    get_primary_coder_agent,
    get_secondary_coder_agent,
    BaseCoderAgent,
    CodeRequest,
    CodeResponse,
    CodeLanguage,
    CodeTaskType
)

from .qa_checker import (
    QACheckerAgent,
    get_qa_checker_agent,
    QualityAssessment,
    QualityLevel,
    TestType,
    ReviewCategory
)

from .debugger import (
    DebuggerAgent,
    get_debugger_agent,
    DebugAnalysis,
    BugReport,
    BugSeverity,
    BugCategory,
    DebugStrategy
)

__all__ = [
    # Router Agent
    "RouterAgent",
    "get_router_agent", 
    "TaskType",
    "Priority",
    "RoutingDecision",
    
    # Architect Agent
    "ArchitectAgent",
    "get_architect_agent",
    "ArchitecturalPlan",
    "ArchitecturalPattern", 
    "ComplexityLevel",
    
    # Coder Agents
    "PrimaryCoderAgent",
    "SecondaryCoderAgent",
    "get_primary_coder_agent",
    "get_secondary_coder_agent",
    "BaseCoderAgent",
    "CodeRequest",
    "CodeResponse",
    "CodeLanguage",
    "CodeTaskType",
    
    # QA Checker Agent
    "QACheckerAgent",
    "get_qa_checker_agent",
    "QualityAssessment",
    "QualityLevel",
    "TestType", 
    "ReviewCategory",
    
    # Debugger Agent
    "DebuggerAgent",
    "get_debugger_agent",
    "DebugAnalysis",
    "BugReport",
    "BugSeverity",
    "BugCategory",
    "DebugStrategy"
]


# Agent registry for easy access
AGENT_REGISTRY = {
    "router": {
        "class": RouterAgent,
        "factory": get_router_agent,
        "model_type": "router",
        "description": "Ultra-fast request routing and task classification"
    },
    "architect": {
        "class": ArchitectAgent,
        "factory": get_architect_agent,
        "model_type": "architect", 
        "description": "High-level system design and architectural planning"
    },
    "coder_primary": {
        "class": PrimaryCoderAgent,
        "factory": get_primary_coder_agent,
        "model_type": "coder_primary",
        "description": "High-performance code generation and implementation"
    },
    "coder_secondary": {
        "class": SecondaryCoderAgent,
        "factory": get_secondary_coder_agent,
        "model_type": "coder_secondary",
        "description": "Efficient backup coding and utility development"
    },
    "qa_checker": {
        "class": QACheckerAgent,
        "factory": get_qa_checker_agent,
        "model_type": "qa_checker",
        "description": "Quality assurance, testing, and code review"
    },
    "debugger": {
        "class": DebuggerAgent,
        "factory": get_debugger_agent,
        "model_type": "debugger",
        "description": "Error analysis, debugging, and issue resolution"
    }
}


async def get_agent(agent_type: str, model_path: str):
    """Get agent instance by type"""
    if agent_type not in AGENT_REGISTRY:
        raise ValueError(f"Unknown agent type: {agent_type}. Available: {list(AGENT_REGISTRY.keys())}")
    
    factory = AGENT_REGISTRY[agent_type]["factory"]
    return await factory(model_path)


def get_agent_info(agent_type: str) -> Dict[str, str]:
    """Get information about an agent type"""
    if agent_type not in AGENT_REGISTRY:
        raise ValueError(f"Unknown agent type: {agent_type}")
    
    return AGENT_REGISTRY[agent_type]


def list_available_agents() -> Dict[str, Dict[str, str]]:
    """List all available agent types with descriptions"""
    return AGENT_REGISTRY