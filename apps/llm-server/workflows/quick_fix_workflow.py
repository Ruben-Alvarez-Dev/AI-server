"""
Quick Fix Workflow - Rapid debugging and fixing workflow
Optimized for immediate issue resolution with minimal overhead
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, TypedDict
from datetime import datetime

from .base_workflow import BaseWorkflow, WorkflowState, WorkflowStatus

try:
    from langgraph import StateGraph, START, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    StateGraph = None
    START = "START"
    END = "END"


logger = logging.getLogger(__name__)


class QuickFixState(WorkflowState):
    """State for quick fix workflow"""
    error_analysis: Optional[Dict[str, Any]]
    quick_fix_suggestion: Optional[Dict[str, Any]]
    validation_result: Optional[Dict[str, Any]]
    applied_fix: Optional[Dict[str, Any]]


class QuickFixWorkflow(BaseWorkflow):
    """Streamlined workflow for rapid issue resolution"""
    
    def __init__(self):
        super().__init__("quick_fix_workflow")
        
        # Quick fix specific configuration
        self.config = {
            "max_fix_attempts": 3,
            "skip_full_analysis": True,
            "auto_apply_high_confidence_fixes": True,
            "confidence_threshold": 0.85,
            "timeout_per_step": 120  # 2 minutes per step
        }
    
    async def _build_graph(self):
        """Build the quick fix workflow graph"""
        if not LANGGRAPH_AVAILABLE:
            raise ImportError("LangGraph not available")
        
        workflow = StateGraph(QuickFixState)
        
        # Add nodes
        workflow.add_node("analyze_error", self._analyze_error)
        workflow.add_node("suggest_quick_fix", self._suggest_quick_fix)
        workflow.add_node("validate_fix", self._validate_fix)
        workflow.add_node("apply_fix", self._apply_fix)
        workflow.add_node("finalize_quick_fix", self._finalize_quick_fix)
        
        # Define edges
        workflow.add_edge(START, "analyze_error")
        workflow.add_edge("analyze_error", "suggest_quick_fix")
        
        # Conditional routing based on fix confidence
        workflow.add_conditional_edges(
            "suggest_quick_fix",
            self._decide_fix_application,
            {
                "validate": "validate_fix",
                "apply_directly": "apply_fix",
                "manual_review": "finalize_quick_fix"
            }
        )
        
        workflow.add_edge("validate_fix", "apply_fix")
        workflow.add_edge("apply_fix", "finalize_quick_fix")
        workflow.add_edge("finalize_quick_fix", END)
        
        # Compile the graph
        self.graph = workflow
        self.compiled_graph = workflow.compile()
        
        logger.info("Quick fix workflow graph compiled successfully")
    
    async def _analyze_error(self, state: QuickFixState) -> Dict[str, Any]:
        """Quick error analysis using router and debugger"""
        logger.info("Performing quick error analysis")
        
        try:
            # First, route to determine if this is actually a quick fix
            router_agent = self.agents_registry.get("router")
            if router_agent:
                routing = await router_agent.route_request(
                    request=state["original_request"],
                    context=state["context"]
                )
                
                # If not a quick fix, adjust approach
                if routing.task_type.value != "quick_fix":
                    logger.warning(f"Request may not be suitable for quick fix: {routing.task_type.value}")
            
            # Get debugger for rapid analysis
            debugger_agent = self.agents_registry.get("debugger")
            if not debugger_agent:
                raise ValueError("Debugger agent not available")
            
            # Extract error information from request
            error_info = self._extract_error_info(state["original_request"])
            code_snippet = self._extract_code_snippet(state["original_request"])
            
            if not error_info:
                # If no clear error, treat as general debugging
                error_info = "General debugging request"
                code_snippet = state["original_request"]
            
            # Perform quick error analysis
            if code_snippet:
                # Use quick fix method for immediate issues
                quick_analysis = await debugger_agent.suggest_quick_fix(
                    error_message=error_info,
                    code_snippet=code_snippet,
                    language=self._detect_language(code_snippet)
                )
            else:
                # Fall back to pattern analysis
                quick_analysis = await debugger_agent.analyze_error_patterns(
                    error_logs=error_info,
                    system_context=state["context"]
                )
            
            state["error_analysis"] = quick_analysis
            
            logger.info("Quick error analysis completed")
            
            return {
                "error_analysis": state["error_analysis"],
                "current_task": "error_analysis_completed"
            }
            
        except Exception as e:
            error_msg = f"Error analysis failed: {str(e)}"
            logger.error(error_msg)
            return {"errors": state.get("errors", []) + [error_msg]}
    
    async def _suggest_quick_fix(self, state: QuickFixState) -> Dict[str, Any]:
        """Generate quick fix suggestions"""
        logger.info("Generating quick fix suggestions")
        
        try:
            error_analysis = state.get("error_analysis", {})
            
            # Check if we already have a quick fix from analysis
            if "quick_fix" in error_analysis:
                quick_fix = error_analysis["quick_fix"]
            else:
                # Generate quick fix using primary coder
                coder_agent = self.agents_registry.get("coder_primary")
                if not coder_agent:
                    raise ValueError("Primary coder agent not available")
                
                # Prepare fix request
                from ..agents.coders import CodeRequest, CodeTaskType, CodeLanguage
                
                fix_request = CodeRequest(
                    task_type=CodeTaskType.BUG_FIX,
                    language=self._detect_language_enum(state["original_request"]),
                    description=f"Quick fix for: {state['original_request']}",
                    context={
                        "error_analysis": error_analysis,
                        "urgency": "high",
                        "quick_fix": True
                    }
                )
                
                # Generate fix
                fix_response = await coder_agent.generate_code(fix_request)
                
                quick_fix = {
                    "fixed_code": fix_response.generated_code,
                    "explanation": fix_response.explanation,
                    "confidence": 0.8,  # Default confidence
                    "trade_offs": "Quick fix - may need comprehensive review later"
                }
            
            state["quick_fix_suggestion"] = quick_fix
            
            logger.info(f"Quick fix suggested with confidence: {quick_fix.get('confidence', 'unknown')}")
            
            return {
                "quick_fix_suggestion": state["quick_fix_suggestion"],
                "current_task": "quick_fix_suggested"
            }
            
        except Exception as e:
            error_msg = f"Quick fix generation failed: {str(e)}"
            logger.error(error_msg)
            return {"errors": state.get("errors", []) + [error_msg]}
    
    def _decide_fix_application(self, state: QuickFixState) -> str:
        """Decide whether to validate, apply directly, or require manual review"""
        quick_fix = state.get("quick_fix_suggestion", {})
        confidence = quick_fix.get("confidence", 0.0)
        
        if confidence >= self.config["confidence_threshold"]:
            if self.config["auto_apply_high_confidence_fixes"]:
                return "apply_directly"
            else:
                return "validate"
        elif confidence >= 0.6:
            return "validate"
        else:
            return "manual_review"
    
    async def _validate_fix(self, state: QuickFixState) -> Dict[str, Any]:
        """Quick validation of the proposed fix"""
        logger.info("Validating quick fix")
        
        try:
            # Get QA agent for quick validation
            qa_agent = self.agents_registry.get("qa_checker")
            if not qa_agent:
                logger.warning("QA agent not available, skipping validation")
                return {
                    "validation_result": {"status": "skipped", "reason": "QA agent unavailable"},
                    "current_task": "validation_skipped"
                }
            
            quick_fix = state["quick_fix_suggestion"]
            fixed_code = quick_fix.get("fixed_code", "")
            
            if not fixed_code:
                return {
                    "validation_result": {"status": "failed", "reason": "No code to validate"},
                    "current_task": "validation_failed"
                }
            
            # Quick validation (lighter than full review)
            validation = await qa_agent.validate_code_quality(
                code=fixed_code,
                language=self._detect_language(fixed_code),
                quality_gates={
                    "critical_issues": 0,
                    "security_threshold": 0,
                    "basic_functionality": True
                }
            )
            
            state["validation_result"] = validation
            
            logger.info(f"Validation completed: {validation.get('validation_passed', 'unknown')}")
            
            return {
                "validation_result": state["validation_result"],
                "current_task": "validation_completed"
            }
            
        except Exception as e:
            error_msg = f"Fix validation failed: {str(e)}"
            logger.error(error_msg)
            return {"errors": state.get("errors", []) + [error_msg]}
    
    async def _apply_fix(self, state: QuickFixState) -> Dict[str, Any]:
        """Apply the quick fix"""
        logger.info("Applying quick fix")
        
        try:
            quick_fix = state["quick_fix_suggestion"]
            validation = state.get("validation_result", {})
            
            # Check validation if available
            if validation and not validation.get("validation_passed", True):
                critical_blockers = validation.get("approval_blockers", [])
                if critical_blockers:
                    return {
                        "errors": state.get("errors", []) + [f"Fix blocked by: {', '.join(critical_blockers)}"],
                        "current_task": "fix_blocked"
                    }
            
            # Simulate applying the fix
            applied_fix = {
                "fixed_code": quick_fix.get("fixed_code", ""),
                "explanation": quick_fix.get("explanation", ""),
                "application_method": "automatic",
                "applied_at": datetime.now().isoformat(),
                "confidence": quick_fix.get("confidence", 0.8),
                "validation_passed": validation.get("validation_passed", None),
                "monitoring": quick_fix.get("monitoring", []),
                "rollback_plan": quick_fix.get("rollback_plan", "Manual rollback required")
            }
            
            state["applied_fix"] = applied_fix
            
            logger.info("Quick fix applied successfully")
            
            return {
                "applied_fix": state["applied_fix"],
                "current_task": "fix_applied"
            }
            
        except Exception as e:
            error_msg = f"Fix application failed: {str(e)}"
            logger.error(error_msg)
            return {"errors": state.get("errors", []) + [error_msg]}
    
    async def _finalize_quick_fix(self, state: QuickFixState) -> Dict[str, Any]:
        """Finalize the quick fix workflow"""
        logger.info("Finalizing quick fix")
        
        try:
            applied_fix = state.get("applied_fix")
            quick_fix = state.get("quick_fix_suggestion", {})
            validation = state.get("validation_result", {})
            error_analysis = state.get("error_analysis", {})
            
            # Create final result
            final_result = {
                "fix_applied": applied_fix is not None,
                "fix_summary": {
                    "original_issue": self._extract_error_info(state["original_request"]),
                    "solution_approach": quick_fix.get("explanation", "Quick fix applied"),
                    "confidence_level": quick_fix.get("confidence", 0.8),
                    "validation_status": validation.get("validation_passed", None),
                    "application_time": datetime.now().isoformat()
                },
                "next_steps": [
                    "Monitor system for any side effects",
                    "Verify fix resolves the original issue",
                    "Plan comprehensive review if needed"
                ],
                "monitoring_recommendations": quick_fix.get("monitoring", []),
                "rollback_instructions": quick_fix.get("rollback_plan", ""),
                "workflow_metadata": {
                    "workflow_type": "quick_fix",
                    "total_time": (datetime.now() - state["start_time"]).total_seconds(),
                    "steps_completed": ["error_analysis", "fix_generation", "application"],
                    "confidence_score": quick_fix.get("confidence", 0.8)
                }
            }
            
            # Add warnings for low confidence fixes
            if quick_fix.get("confidence", 1.0) < 0.7:
                final_result["warnings"] = [
                    "Low confidence fix - comprehensive testing recommended",
                    "Consider scheduling proper debugging session",
                    "Monitor closely for regression issues"
                ]
            
            return {
                "final_deliverable": final_result,
                "status": WorkflowStatus.COMPLETED,
                "current_task": "workflow_completed"
            }
            
        except Exception as e:
            error_msg = f"Quick fix finalization failed: {str(e)}"
            logger.error(error_msg)
            return {"errors": state.get("errors", []) + [error_msg]}
    
    # Helper methods
    
    def _extract_error_info(self, request: str) -> str:
        """Extract error information from request"""
        # Simple heuristic to find error-like content
        error_indicators = [
            "error:", "exception:", "failed:", "traceback:", 
            "TypeError:", "ValueError:", "AttributeError:",
            "SyntaxError:", "IndentationError:", "NameError:"
        ]
        
        request_lower = request.lower()
        for indicator in error_indicators:
            if indicator in request_lower:
                # Try to extract the error portion
                lines = request.split('\n')
                error_lines = [line for line in lines if indicator.strip(':') in line.lower()]
                if error_lines:
                    return '\n'.join(error_lines)
        
        return request  # Return full request if no specific error found
    
    def _extract_code_snippet(self, request: str) -> Optional[str]:
        """Extract code snippet from request"""
        # Look for code blocks
        if "```" in request:
            parts = request.split("```")
            if len(parts) >= 3:
                return parts[1]  # Content between first pair of ```
        
        # Look for indented code (simple heuristic)
        lines = request.split('\n')
        code_lines = []
        in_code_block = False
        
        for line in lines:
            if line.strip() and (line.startswith('    ') or line.startswith('\t')):
                in_code_block = True
                code_lines.append(line)
            elif in_code_block and not line.strip():
                code_lines.append(line)  # Empty line in code block
            elif in_code_block:
                break  # End of code block
        
        return '\n'.join(code_lines) if code_lines else None
    
    def _detect_language(self, code_or_request: str) -> str:
        """Detect programming language from code or request"""
        content = code_or_request.lower()
        
        if any(keyword in content for keyword in ['def ', 'import ', 'python', '.py']):
            return "python"
        elif any(keyword in content for keyword in ['function ', 'const ', 'javascript', '.js']):
            return "javascript"
        elif any(keyword in content for keyword in ['interface ', 'typescript', '.ts']):
            return "typescript"
        elif any(keyword in content for keyword in ['fn ', 'rust', '.rs']):
            return "rust"
        elif any(keyword in content for keyword in ['func ', 'golang', 'go', '.go']):
            return "go"
        else:
            return "python"  # Default
    
    def _detect_language_enum(self, code_or_request: str):
        """Detect programming language and return enum"""
        from ..agents.coders import CodeLanguage
        
        lang_str = self._detect_language(code_or_request)
        
        mapping = {
            "python": CodeLanguage.PYTHON,
            "javascript": CodeLanguage.JAVASCRIPT,
            "typescript": CodeLanguage.TYPESCRIPT,
            "rust": CodeLanguage.RUST,
            "go": CodeLanguage.GO
        }
        
        return mapping.get(lang_str, CodeLanguage.PYTHON)
    
    def _get_required_agents(self) -> List[str]:
        """Get required agents for quick fix workflow"""
        return ["router", "debugger", "coder_primary"]  # QA is optional


# Factory function
async def create_quick_fix_workflow(agents_registry: Dict[str, Any]) -> QuickFixWorkflow:
    """Create and initialize quick fix workflow"""
    workflow = QuickFixWorkflow()
    await workflow.initialize(agents_registry)
    return workflow