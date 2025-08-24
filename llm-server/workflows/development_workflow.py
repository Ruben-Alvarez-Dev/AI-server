"""
Development Workflow - Main orchestration workflow for development tasks
Coordinates all agents (Router, Architect, Coders, QA, Debugger) based on task requirements
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, TypedDict
from datetime import datetime

from .base_workflow import BaseWorkflow, WorkflowState, WorkflowStatus, TaskPriority, WorkflowTask

try:
    from langgraph import StateGraph, START, END
    from langchain_core.messages import HumanMessage, AIMessage
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    StateGraph = None
    START = "START"
    END = "END"

from ..agents import (
    get_router_agent,
    get_architect_agent,
    get_primary_coder_agent,
    get_secondary_coder_agent,
    get_qa_checker_agent,
    get_debugger_agent,
    TaskType,
    Priority,
    RoutingDecision
)


logger = logging.getLogger(__name__)


class DevelopmentState(WorkflowState):
    """Extended state for development workflow"""
    routing_decision: Optional[Dict[str, Any]]
    architectural_plan: Optional[Dict[str, Any]]
    code_implementations: Dict[str, Any]
    qa_reports: Dict[str, Any]
    debug_analyses: Dict[str, Any]
    final_deliverable: Optional[Dict[str, Any]]


class DevelopmentWorkflow(BaseWorkflow):
    """Main development workflow orchestrating all specialized agents"""
    
    def __init__(self):
        super().__init__("development_workflow")
        
        # Workflow configuration
        self.config = {
            "enable_parallel_coding": True,
            "require_qa_approval": True,
            "auto_debug_on_failure": True,
            "architect_threshold_complexity": "complex",
            "max_retry_attempts": 3,
            "timeout_per_stage": 600  # 10 minutes per stage
        }
    
    async def _build_graph(self):
        """Build the development workflow graph"""
        if not LANGGRAPH_AVAILABLE:
            raise ImportError("LangGraph not available")
        
        # Create the state graph
        workflow = StateGraph(DevelopmentState)
        
        # Add nodes for each stage
        workflow.add_node("route_request", self._route_request)
        workflow.add_node("plan_architecture", self._plan_architecture)
        workflow.add_node("implement_code", self._implement_code)
        workflow.add_node("parallel_implementation", self._parallel_implementation)
        workflow.add_node("quality_assurance", self._quality_assurance)
        workflow.add_node("debug_issues", self._debug_issues)
        workflow.add_node("finalize_deliverable", self._finalize_deliverable)
        
        # Define the workflow edges
        workflow.add_edge(START, "route_request")
        
        # Conditional routing based on task complexity
        workflow.add_conditional_edges(
            "route_request",
            self._decide_next_step_after_routing,
            {
                "architecture": "plan_architecture",
                "coding": "implement_code",
                "debugging": "debug_issues",
                "qa": "quality_assurance"
            }
        )
        
        # Architecture planning flows to implementation
        workflow.add_edge("plan_architecture", "implement_code")
        
        # Implementation can go to parallel or QA
        workflow.add_conditional_edges(
            "implement_code",
            self._decide_implementation_flow,
            {
                "parallel": "parallel_implementation",
                "qa": "quality_assurance",
                "debug": "debug_issues"
            }
        )
        
        # Parallel implementation goes to QA
        workflow.add_edge("parallel_implementation", "quality_assurance")
        
        # QA can approve or send to debug
        workflow.add_conditional_edges(
            "quality_assurance",
            self._decide_qa_outcome,
            {
                "approved": "finalize_deliverable",
                "needs_fixes": "debug_issues",
                "needs_refactoring": "implement_code"
            }
        )
        
        # Debug can go back to implementation or finalize
        workflow.add_conditional_edges(
            "debug_issues",
            self._decide_debug_outcome,
            {
                "fixed": "quality_assurance",
                "needs_reimplementation": "implement_code",
                "completed": "finalize_deliverable"
            }
        )
        
        # Finalize is the end
        workflow.add_edge("finalize_deliverable", END)
        
        # Compile the graph
        self.graph = workflow
        self.compiled_graph = workflow.compile()
        
        logger.info("Development workflow graph compiled successfully")
    
    async def _route_request(self, state: DevelopmentState) -> Dict[str, Any]:
        """Route the initial request to determine workflow path"""
        logger.info("Routing development request")
        
        try:
            # Get router agent
            router_agent = self.agents_registry.get("router")
            if not router_agent:
                raise ValueError("Router agent not available")
            
            # Route the request
            routing_decision = await router_agent.route_request(
                request=state["original_request"],
                context=state["context"]
            )
            
            # Store routing decision
            state["routing_decision"] = {
                "task_type": routing_decision.task_type.value,
                "priority": routing_decision.priority.value,
                "primary_agent": routing_decision.primary_agent,
                "secondary_agents": routing_decision.secondary_agents,
                "requires_architect": routing_decision.requires_architect,
                "can_parallelize": routing_decision.can_parallelize,
                "reasoning": routing_decision.reasoning
            }
            
            logger.info(f"Request routed: {routing_decision.task_type.value} -> {routing_decision.primary_agent}")
            
            return {
                "routing_decision": state["routing_decision"],
                "current_task": "routing_completed"
            }
            
        except Exception as e:
            error_msg = f"Routing failed: {str(e)}"
            logger.error(error_msg)
            return {"errors": state.get("errors", []) + [error_msg]}
    
    def _decide_next_step_after_routing(self, state: DevelopmentState) -> str:
        """Decide next step based on routing decision"""
        routing = state.get("routing_decision", {})
        
        if routing.get("requires_architect"):
            return "architecture"
        elif routing.get("task_type") == "debugging":
            return "debugging"
        elif routing.get("task_type") in ["code_review", "testing"]:
            return "qa"
        else:
            return "coding"
    
    async def _plan_architecture(self, state: DevelopmentState) -> Dict[str, Any]:
        """Create architectural plan for complex tasks"""
        logger.info("Planning system architecture")
        
        try:
            # Get architect agent
            architect_agent = self.agents_registry.get("architect")
            if not architect_agent:
                raise ValueError("Architect agent not available")
            
            # Create architectural plan
            architectural_plan = await architect_agent.create_architectural_plan(
                requirements=state["original_request"],
                context=state["context"]
            )
            
            # Store architectural plan
            state["architectural_plan"] = {
                "project_type": architectural_plan.project_type,
                "complexity_level": architectural_plan.complexity_level.name,
                "recommended_patterns": [p.value for p in architectural_plan.recommended_patterns],
                "technology_stack": architectural_plan.technology_stack,
                "directory_structure": architectural_plan.directory_structure,
                "implementation_phases": architectural_plan.implementation_phases,
                "estimated_effort": architectural_plan.estimated_effort,
                "key_considerations": architectural_plan.key_considerations
            }
            
            logger.info(f"Architecture planned: {architectural_plan.project_type} ({architectural_plan.complexity_level.name})")
            
            return {
                "architectural_plan": state["architectural_plan"],
                "current_task": "architecture_completed"
            }
            
        except Exception as e:
            error_msg = f"Architecture planning failed: {str(e)}"
            logger.error(error_msg)
            return {"errors": state.get("errors", []) + [error_msg]}
    
    async def _implement_code(self, state: DevelopmentState) -> Dict[str, Any]:
        """Implement code using primary coder"""
        logger.info("Implementing code with primary coder")
        
        try:
            # Get primary coder agent
            coder_agent = self.agents_registry.get("coder_primary")
            if not coder_agent:
                raise ValueError("Primary coder agent not available")
            
            # Prepare implementation request
            routing = state.get("routing_decision", {})
            architecture = state.get("architectural_plan", {})
            
            # Create code request
            from ..agents.coders import CodeRequest, CodeTaskType, CodeLanguage
            
            # Determine task type and language from context
            task_type = self._map_to_code_task_type(routing.get("task_type", "implementation"))
            language = self._determine_language(state["context"], architecture)
            
            code_request = CodeRequest(
                task_type=task_type,
                language=language,
                description=state["original_request"],
                context={
                    "routing": routing,
                    "architecture": architecture,
                    **state["context"]
                }
            )
            
            # Generate code
            code_response = await coder_agent.generate_code(code_request)
            
            # Store implementation
            implementation_id = "primary_implementation"
            state["code_implementations"] = state.get("code_implementations", {})
            state["code_implementations"][implementation_id] = {
                "agent": "coder_primary",
                "generated_code": code_response.generated_code,
                "language": code_response.language.value,
                "explanation": code_response.explanation,
                "file_changes": code_response.file_changes,
                "dependencies": code_response.dependencies,
                "testing_notes": code_response.testing_notes,
                "estimated_effort": code_response.estimated_effort
            }
            
            logger.info(f"Code implemented: {len(code_response.generated_code)} characters")
            
            return {
                "code_implementations": state["code_implementations"],
                "current_task": "implementation_completed"
            }
            
        except Exception as e:
            error_msg = f"Code implementation failed: {str(e)}"
            logger.error(error_msg)
            return {"errors": state.get("errors", []) + [error_msg]}
    
    def _decide_implementation_flow(self, state: DevelopmentState) -> str:
        """Decide whether to do parallel implementation or proceed to QA"""
        routing = state.get("routing_decision", {})
        
        if (routing.get("can_parallelize") and 
            self.config["enable_parallel_coding"] and
            len(routing.get("secondary_agents", [])) > 0):
            return "parallel"
        else:
            return "qa"
    
    async def _parallel_implementation(self, state: DevelopmentState) -> Dict[str, Any]:
        """Run parallel implementations with secondary agents"""
        logger.info("Running parallel implementations")
        
        try:
            routing = state.get("routing_decision", {})
            secondary_agents = routing.get("secondary_agents", [])
            
            parallel_tasks = []
            
            # Create tasks for secondary agents
            for i, agent_type in enumerate(secondary_agents):
                if agent_type in self.agents_registry:
                    agent = self.agents_registry[agent_type]
                    
                    # Create parallel task
                    task = self._create_parallel_task(state, agent_type, f"parallel_impl_{i}")
                    parallel_tasks.append(task)
            
            # Execute parallel tasks
            if parallel_tasks:
                results = await asyncio.gather(*parallel_tasks, return_exceptions=True)
                
                # Process results
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        logger.error(f"Parallel task {i} failed: {result}")
                    else:
                        implementation_id = f"parallel_implementation_{i}"
                        state["code_implementations"][implementation_id] = result
            
            logger.info(f"Completed {len(parallel_tasks)} parallel implementations")
            
            return {
                "code_implementations": state["code_implementations"],
                "current_task": "parallel_implementation_completed"
            }
            
        except Exception as e:
            error_msg = f"Parallel implementation failed: {str(e)}"
            logger.error(error_msg)
            return {"errors": state.get("errors", []) + [error_msg]}
    
    async def _quality_assurance(self, state: DevelopmentState) -> Dict[str, Any]:
        """Perform quality assurance on implementations"""
        logger.info("Performing quality assurance")
        
        try:
            # Get QA checker agent
            qa_agent = self.agents_registry.get("qa_checker")
            if not qa_agent:
                raise ValueError("QA Checker agent not available")
            
            implementations = state.get("code_implementations", {})
            qa_reports = {}
            
            # Review each implementation
            for impl_id, implementation in implementations.items():
                code = implementation["generated_code"]
                language = implementation["language"]
                
                # Conduct code review
                assessment = await qa_agent.conduct_code_review(
                    code=code,
                    language=language,
                    context=state["context"]
                )
                
                qa_reports[impl_id] = {
                    "overall_quality": assessment.overall_quality.value,
                    "quality_score": assessment.quality_score,
                    "issues_found": len(assessment.issues_found),
                    "critical_issues": [
                        issue for issue in assessment.issues_found
                        if issue.get("severity") in ["critical", "high"]
                    ],
                    "recommendations": assessment.recommendations,
                    "maintainability_score": assessment.maintainability_score
                }
            
            state["qa_reports"] = qa_reports
            
            logger.info(f"QA completed on {len(implementations)} implementations")
            
            return {
                "qa_reports": state["qa_reports"],
                "current_task": "qa_completed"
            }
            
        except Exception as e:
            error_msg = f"Quality assurance failed: {str(e)}"
            logger.error(error_msg)
            return {"errors": state.get("errors", []) + [error_msg]}
    
    def _decide_qa_outcome(self, state: DevelopmentState) -> str:
        """Decide next step based on QA results"""
        qa_reports = state.get("qa_reports", {})
        
        # Check if any implementation has critical issues
        has_critical_issues = any(
            len(report.get("critical_issues", [])) > 0
            for report in qa_reports.values()
        )
        
        if has_critical_issues:
            return "needs_fixes"
        
        # Check overall quality scores
        avg_quality_score = sum(
            report.get("quality_score", 0)
            for report in qa_reports.values()
        ) / max(1, len(qa_reports))
        
        if avg_quality_score >= 8:
            return "approved"
        elif avg_quality_score >= 6:
            return "needs_fixes"
        else:
            return "needs_refactoring"
    
    async def _debug_issues(self, state: DevelopmentState) -> Dict[str, Any]:
        """Debug issues found in code or reported errors"""
        logger.info("Debugging identified issues")
        
        try:
            # Get debugger agent
            debugger_agent = self.agents_registry.get("debugger")
            if not debugger_agent:
                raise ValueError("Debugger agent not available")
            
            implementations = state.get("code_implementations", {})
            qa_reports = state.get("qa_reports", {})
            debug_analyses = {}
            
            # Debug each implementation with issues
            for impl_id, implementation in implementations.items():
                qa_report = qa_reports.get(impl_id, {})
                critical_issues = qa_report.get("critical_issues", [])
                
                if critical_issues:
                    # Prepare error information
                    error_info = "\n".join([
                        f"- {issue.get('description', 'Unknown issue')}"
                        for issue in critical_issues
                    ])
                    
                    # Analyze bugs
                    debug_analysis = await debugger_agent.analyze_bug(
                        code=implementation["generated_code"],
                        language=implementation["language"],
                        error_info=error_info,
                        context=state["context"]
                    )
                    
                    debug_analyses[impl_id] = {
                        "bugs_found": len(debug_analysis.bugs_found),
                        "debug_strategy": debug_analysis.debug_strategy.value,
                        "confidence": debug_analysis.analysis_confidence,
                        "next_steps": debug_analysis.next_steps,
                        "fixes_applied": []  # Would contain actual fixes
                    }
            
            state["debug_analyses"] = debug_analyses
            
            logger.info(f"Debug analysis completed on {len(debug_analyses)} implementations")
            
            return {
                "debug_analyses": state["debug_analyses"],
                "current_task": "debugging_completed"
            }
            
        except Exception as e:
            error_msg = f"Debugging failed: {str(e)}"
            logger.error(error_msg)
            return {"errors": state.get("errors", []) + [error_msg]}
    
    def _decide_debug_outcome(self, state: DevelopmentState) -> str:
        """Decide next step after debugging"""
        debug_analyses = state.get("debug_analyses", {})
        errors = state.get("errors", [])
        
        # If we have debug analyses, check if fixes were applied
        if debug_analyses:
            # For now, assume fixes need re-implementation
            return "needs_reimplementation"
        
        # If no debug analyses but no errors, we're done
        if not errors:
            return "completed"
        
        # Otherwise, try fixing
        return "fixed"
    
    async def _finalize_deliverable(self, state: DevelopmentState) -> Dict[str, Any]:
        """Finalize the development deliverable"""
        logger.info("Finalizing development deliverable")
        
        try:
            # Select best implementation based on QA scores
            implementations = state.get("code_implementations", {})
            qa_reports = state.get("qa_reports", {})
            
            best_impl_id = None
            best_score = -1
            
            for impl_id, implementation in implementations.items():
                qa_report = qa_reports.get(impl_id, {})
                score = qa_report.get("quality_score", 0)
                
                if score > best_score:
                    best_score = score
                    best_impl_id = impl_id
            
            # Create final deliverable
            if best_impl_id:
                best_implementation = implementations[best_impl_id]
                final_deliverable = {
                    "implementation_id": best_impl_id,
                    "code": best_implementation["generated_code"],
                    "language": best_implementation["language"],
                    "explanation": best_implementation["explanation"],
                    "file_changes": best_implementation["file_changes"],
                    "dependencies": best_implementation["dependencies"],
                    "quality_score": best_score,
                    "routing_decision": state.get("routing_decision"),
                    "architectural_plan": state.get("architectural_plan"),
                    "qa_summary": qa_reports.get(best_impl_id, {}),
                    "debug_summary": state.get("debug_analyses", {}).get(best_impl_id, {}),
                    "workflow_metadata": {
                        "total_implementations": len(implementations),
                        "workflow_start": state["start_time"],
                        "workflow_end": datetime.now()
                    }
                }
            else:
                final_deliverable = {
                    "error": "No valid implementation found",
                    "workflow_metadata": {
                        "workflow_start": state["start_time"],
                        "workflow_end": datetime.now()
                    }
                }
            
            state["final_deliverable"] = final_deliverable
            
            logger.info("Development deliverable finalized")
            
            return {
                "final_deliverable": state["final_deliverable"],
                "status": WorkflowStatus.COMPLETED,
                "current_task": "workflow_completed"
            }
            
        except Exception as e:
            error_msg = f"Finalization failed: {str(e)}"
            logger.error(error_msg)
            return {"errors": state.get("errors", []) + [error_msg]}
    
    # Helper methods
    
    def _map_to_code_task_type(self, task_type_str: str):
        """Map routing task type to code task type"""
        from ..agents.coders import CodeTaskType
        
        mapping = {
            "coding": CodeTaskType.IMPLEMENTATION,
            "refactoring": CodeTaskType.REFACTORING,
            "debugging": CodeTaskType.BUG_FIX,
            "quick_fix": CodeTaskType.BUG_FIX,
            "architecture": CodeTaskType.IMPLEMENTATION,
            "planning": CodeTaskType.IMPLEMENTATION
        }
        
        return mapping.get(task_type_str, CodeTaskType.IMPLEMENTATION)
    
    def _determine_language(self, context: Dict, architecture: Dict) -> 'CodeLanguage':
        """Determine programming language from context and architecture"""
        from ..agents.coders import CodeLanguage
        
        # Check context for language hints
        context_str = str(context).lower()
        arch_str = str(architecture).lower()
        combined = context_str + " " + arch_str
        
        # Language detection logic
        if "python" in combined or "fastapi" in combined or "django" in combined:
            return CodeLanguage.PYTHON
        elif "javascript" in combined or "node" in combined or "react" in combined:
            return CodeLanguage.JAVASCRIPT
        elif "typescript" in combined or "angular" in combined:
            return CodeLanguage.TYPESCRIPT
        elif "rust" in combined:
            return CodeLanguage.RUST
        elif "go" in combined or "golang" in combined:
            return CodeLanguage.GO
        else:
            # Default to Python
            return CodeLanguage.PYTHON
    
    async def _create_parallel_task(self, state: DevelopmentState, agent_type: str, task_id: str):
        """Create a parallel implementation task"""
        # This would be implemented to create appropriate tasks for each agent type
        # For now, return a placeholder
        return {
            "agent": agent_type,
            "task_id": task_id,
            "generated_code": f"// Parallel implementation by {agent_type}",
            "language": "python",
            "explanation": f"Parallel implementation using {agent_type}",
            "file_changes": [],
            "dependencies": [],
            "testing_notes": "Parallel implementation testing needed",
            "estimated_effort": "2-4 hours"
        }
    
    def _get_required_agents(self) -> List[str]:
        """Get required agents for development workflow"""
        return [
            "router",
            "architect", 
            "coder_primary",
            "coder_secondary",
            "qa_checker",
            "debugger"
        ]


# Factory function for creating development workflow
async def create_development_workflow(agents_registry: Dict[str, Any]) -> DevelopmentWorkflow:
    """Create and initialize development workflow"""
    workflow = DevelopmentWorkflow()
    await workflow.initialize(agents_registry)
    return workflow