"""
Router Agent - Ultra-fast request routing using Qwen2-1.5B
Routes incoming requests to appropriate specialized agents
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from ..configs.llama_cpp.optimized_llama import OptimizedLlama, MODEL_POOL


logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Types of tasks the system can handle"""
    ARCHITECTURE = "architecture"
    CODING = "coding"
    CODE_REVIEW = "code_review"  
    DEBUGGING = "debugging"
    TESTING = "testing"
    REFACTORING = "refactoring"
    DOCUMENTATION = "documentation"
    PLANNING = "planning"
    QUICK_FIX = "quick_fix"
    COMPLEX_PROJECT = "complex_project"


class Priority(Enum):
    """Task priority levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


@dataclass
class RoutingDecision:
    """Result of routing analysis"""
    task_type: TaskType
    priority: Priority
    primary_agent: str
    secondary_agents: List[str]
    estimated_tokens: int
    requires_architect: bool
    can_parallelize: bool
    reasoning: str


class RouterAgent:
    """Ultra-fast router for directing requests to specialized agents"""
    
    def __init__(self, model_path: str):
        self.model_id = "router"
        self.model_path = model_path
        self.model: Optional[OptimizedLlama] = None
        
        # Agent specializations mapping
        self.agent_specializations = {
            "architect": [
                TaskType.ARCHITECTURE, 
                TaskType.PLANNING, 
                TaskType.COMPLEX_PROJECT
            ],
            "coder_primary": [
                TaskType.CODING,
                TaskType.REFACTORING,
                TaskType.QUICK_FIX
            ],
            "coder_secondary": [
                TaskType.CODING,  # Backup coding
                TaskType.REFACTORING
            ],
            "qa_checker": [
                TaskType.CODE_REVIEW,
                TaskType.TESTING,
                TaskType.DOCUMENTATION
            ],
            "debugger": [
                TaskType.DEBUGGING,
                TaskType.QUICK_FIX
            ]
        }
        
        # Routing templates for consistent analysis
        self.routing_prompt_template = """You are a lightning-fast routing system for a development team AI. Analyze the request and provide routing decisions.

Request: {request}

Respond ONLY with valid JSON in this exact format:
{{
    "task_type": "coding|architecture|code_review|debugging|testing|refactoring|documentation|planning|quick_fix|complex_project",
    "priority": "low|medium|high|urgent",
    "primary_agent": "architect|coder_primary|coder_secondary|qa_checker|debugger",
    "secondary_agents": ["agent1", "agent2"],
    "estimated_tokens": 500,
    "requires_architect": true|false,
    "can_parallelize": true|false,
    "reasoning": "Brief explanation"
}}

Analysis guidelines:
- architecture: System design, high-level planning
- coding: Implementation, writing new code
- code_review: Quality checks, testing, validation
- debugging: Error analysis, bug fixes
- refactoring: Code improvements, optimization
- quick_fix: Simple, immediate solutions
- complex_project: Multi-step, requires planning

Choose the most appropriate agent:
- architect: System design, complex planning
- coder_primary: Primary implementation
- coder_secondary: Backup coding, simpler tasks
- qa_checker: Testing, validation, reviews
- debugger: Error analysis, debugging

Be decisive and fast. JSON only."""
    
    async def initialize(self):
        """Initialize the router model"""
        logger.info(f"Initializing Router agent with model: {self.model_path}")
        
        self.model = await MODEL_POOL.get_model(
            model_id=self.model_id,
            model_path=self.model_path,
            model_type="router"
        )
        
        logger.info("Router agent initialized successfully")
    
    async def route_request(self, request: str, context: Optional[Dict] = None) -> RoutingDecision:
        """Route a request to appropriate agents"""
        if not self.model:
            await self.initialize()
        
        # Prepare routing prompt
        prompt = self.routing_prompt_template.format(request=request)
        
        try:
            # Generate routing decision (should be very fast with Qwen2-1.5B)
            async for response in self.model.generate_async(
                prompt=prompt,
                max_tokens=300,
                temperature=0.1,  # Low temperature for consistent routing
                top_p=0.9,
                stop=["}\n", "}\n\n"]
            ):
                # Parse JSON response
                json_text = response.get("choices", [{}])[0].get("text", "").strip()
                
                # Clean up JSON (remove any extra text)
                if "{" in json_text:
                    json_start = json_text.find("{")
                    json_end = json_text.rfind("}") + 1
                    json_text = json_text[json_start:json_end]
                
                try:
                    routing_data = json.loads(json_text)
                    return self._create_routing_decision(routing_data, request)
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse routing JSON: {e}")
                    logger.warning(f"Raw response: {json_text}")
                    # Fallback to heuristic routing
                    return self._fallback_routing(request)
        
        except Exception as e:
            logger.error(f"Router error: {e}")
            return self._fallback_routing(request)
    
    def _create_routing_decision(self, data: Dict, request: str) -> RoutingDecision:
        """Create RoutingDecision from parsed JSON"""
        try:
            return RoutingDecision(
                task_type=TaskType(data["task_type"]),
                priority=Priority[data["priority"].upper()],
                primary_agent=data["primary_agent"],
                secondary_agents=data.get("secondary_agents", []),
                estimated_tokens=data.get("estimated_tokens", 500),
                requires_architect=data.get("requires_architect", False),
                can_parallelize=data.get("can_parallelize", False),
                reasoning=data.get("reasoning", "Router decision")
            )
        except (KeyError, ValueError) as e:
            logger.warning(f"Invalid routing data: {e}")
            return self._fallback_routing(request)
    
    def _fallback_routing(self, request: str) -> RoutingDecision:
        """Fallback heuristic routing when LLM routing fails"""
        request_lower = request.lower()
        
        # Simple heuristics based on keywords
        if any(word in request_lower for word in ["architecture", "design", "plan", "structure"]):
            return RoutingDecision(
                task_type=TaskType.ARCHITECTURE,
                priority=Priority.MEDIUM,
                primary_agent="architect",
                secondary_agents=["coder_primary"],
                estimated_tokens=800,
                requires_architect=True,
                can_parallelize=False,
                reasoning="Fallback: Architecture keywords detected"
            )
        
        elif any(word in request_lower for word in ["debug", "error", "fix", "bug", "broken"]):
            return RoutingDecision(
                task_type=TaskType.DEBUGGING,
                priority=Priority.HIGH,
                primary_agent="debugger",
                secondary_agents=["coder_primary"],
                estimated_tokens=600,
                requires_architect=False,
                can_parallelize=False,
                reasoning="Fallback: Debugging keywords detected"
            )
        
        elif any(word in request_lower for word in ["test", "validate", "check", "review"]):
            return RoutingDecision(
                task_type=TaskType.CODE_REVIEW,
                priority=Priority.MEDIUM,
                primary_agent="qa_checker",
                secondary_agents=["debugger"],
                estimated_tokens=500,
                requires_architect=False,
                can_parallelize=True,
                reasoning="Fallback: QA keywords detected"
            )
        
        else:
            # Default to coding task
            return RoutingDecision(
                task_type=TaskType.CODING,
                priority=Priority.MEDIUM,
                primary_agent="coder_primary",
                secondary_agents=["qa_checker"],
                estimated_tokens=700,
                requires_architect=False,
                can_parallelize=True,
                reasoning="Fallback: Default coding task"
            )
    
    async def get_workflow_sequence(self, routing: RoutingDecision) -> List[Dict[str, Any]]:
        """Generate optimal workflow sequence based on routing decision"""
        workflow_steps = []
        
        # Add architect if needed
        if routing.requires_architect:
            workflow_steps.append({
                "agent": "architect",
                "stage": "planning",
                "parallel": False,
                "dependencies": []
            })
        
        # Add primary agent
        dependencies = ["architect"] if routing.requires_architect else []
        workflow_steps.append({
            "agent": routing.primary_agent,
            "stage": "implementation",
            "parallel": routing.can_parallelize,
            "dependencies": dependencies
        })
        
        # Add secondary agents
        for i, agent in enumerate(routing.secondary_agents):
            workflow_steps.append({
                "agent": agent,
                "stage": "support" if i == 0 else f"support_{i}",
                "parallel": routing.can_parallelize,
                "dependencies": [routing.primary_agent] if not routing.can_parallelize else dependencies
            })
        
        return workflow_steps
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for router agent"""
        try:
            if not self.model:
                return {"status": "unhealthy", "reason": "Model not loaded"}
            
            # Quick test
            test_request = "Write a hello world function"
            routing = await self.route_request(test_request)
            
            return {
                "status": "healthy",
                "model_id": self.model_id,
                "model_loaded": self.model.is_loaded,
                "test_routing": {
                    "task_type": routing.task_type.value,
                    "primary_agent": routing.primary_agent
                }
            }
            
        except Exception as e:
            return {"status": "unhealthy", "reason": str(e)}


# Global router instance
router_agent: Optional[RouterAgent] = None


async def get_router_agent(model_path: str) -> RouterAgent:
    """Get or create router agent instance"""
    global router_agent
    
    if router_agent is None:
        router_agent = RouterAgent(model_path)
        await router_agent.initialize()
    
    return router_agent