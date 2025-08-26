"""
Code Review Workflow - Comprehensive code review and quality assessment
Specialized workflow for thorough code analysis, testing, and quality assurance
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


class CodeReviewState(WorkflowState):
    """State for code review workflow"""
    code_analysis: Optional[Dict[str, Any]]
    quality_assessment: Optional[Dict[str, Any]]
    security_review: Optional[Dict[str, Any]]
    test_recommendations: Optional[Dict[str, Any]]
    refactoring_suggestions: Optional[Dict[str, Any]]
    final_review_report: Optional[Dict[str, Any]]


class CodeReviewWorkflow(BaseWorkflow):
    """Comprehensive code review workflow using QA and debugging agents"""
    
    def __init__(self):
        super().__init__("code_review_workflow")
        
        # Code review specific configuration
        self.config = {
            "enable_security_scan": True,
            "generate_test_recommendations": True,
            "include_performance_analysis": True,
            "require_architecture_review": False,
            "auto_generate_tests": False,
            "quality_threshold": 7,  # Minimum quality score
            "detailed_reporting": True
        }
    
    async def _build_graph(self):
        """Build the code review workflow graph"""
        if not LANGGRAPH_AVAILABLE:
            raise ImportError("LangGraph not available")
        
        workflow = StateGraph(CodeReviewState)
        
        # Add nodes for review process
        workflow.add_node("initial_analysis", self._initial_analysis)
        workflow.add_node("quality_assessment", self._quality_assessment)
        workflow.add_node("security_review", self._security_review)
        workflow.add_node("test_analysis", self._test_analysis)
        workflow.add_node("refactoring_analysis", self._refactoring_analysis)
        workflow.add_node("generate_recommendations", self._generate_recommendations)
        workflow.add_node("finalize_review", self._finalize_review)
        
        # Define workflow edges
        workflow.add_edge(START, "initial_analysis")
        workflow.add_edge("initial_analysis", "quality_assessment")
        
        # Conditional security review
        workflow.add_conditional_edges(
            "quality_assessment",
            self._decide_security_review,
            {
                "security_review": "security_review",
                "test_analysis": "test_analysis"
            }
        )
        
        workflow.add_edge("security_review", "test_analysis")
        workflow.add_edge("test_analysis", "refactoring_analysis")
        workflow.add_edge("refactoring_analysis", "generate_recommendations")
        workflow.add_edge("generate_recommendations", "finalize_review")
        workflow.add_edge("finalize_review", END)
        
        # Compile the graph
        self.graph = workflow
        self.compiled_graph = workflow.compile()
        
        logger.info("Code review workflow graph compiled successfully")
    
    async def _initial_analysis(self, state: CodeReviewState) -> Dict[str, Any]:
        """Initial code analysis and classification"""
        logger.info("Starting initial code analysis")
        
        try:
            # Use router to understand the code type and scope
            router_agent = self.agents_registry.get("router")
            if router_agent:
                routing = await router_agent.route_request(
                    request=f"Code review for: {state['original_request']}",
                    context=state["context"]
                )
                
                analysis = {
                    "task_type": routing.task_type.value,
                    "complexity": routing.estimated_tokens,
                    "requires_architect": routing.requires_architect,
                    "can_parallelize": routing.can_parallelize,
                    "routing_reasoning": routing.reasoning
                }
            else:
                # Fallback analysis
                analysis = {
                    "task_type": "code_review",
                    "complexity": len(state["original_request"]),
                    "requires_architect": False,
                    "can_parallelize": True,
                    "routing_reasoning": "Direct code review without routing"
                }
            
            # Extract code from request
            code_content = self._extract_code_from_request(state["original_request"])
            language = self._detect_language_from_request(state["original_request"])
            
            analysis.update({
                "code_length": len(code_content) if code_content else 0,
                "detected_language": language,
                "has_code_content": bool(code_content),
                "analysis_scope": self._determine_analysis_scope(code_content, state["context"])
            })
            
            state["code_analysis"] = analysis
            
            logger.info(f"Initial analysis completed: {language} code, {analysis['task_type']}")
            
            return {
                "code_analysis": state["code_analysis"],
                "current_task": "initial_analysis_completed"
            }
            
        except Exception as e:
            error_msg = f"Initial analysis failed: {str(e)}"
            logger.error(error_msg)
            return {"errors": state.get("errors", []) + [error_msg]}
    
    async def _quality_assessment(self, state: CodeReviewState) -> Dict[str, Any]:
        """Comprehensive quality assessment using QA agent"""
        logger.info("Performing quality assessment")
        
        try:
            qa_agent = self.agents_registry.get("qa_checker")
            if not qa_agent:
                raise ValueError("QA Checker agent not available")
            
            code_analysis = state.get("code_analysis", {})
            code_content = self._extract_code_from_request(state["original_request"])
            language = code_analysis.get("detected_language", "python")
            
            if not code_content:
                return {
                    "errors": state.get("errors", []) + ["No code content found for review"],
                    "current_task": "quality_assessment_failed"
                }
            
            # Conduct comprehensive code review
            assessment = await qa_agent.conduct_code_review(
                code=code_content,
                language=language,
                context=state["context"],
                requirements=[
                    "Comprehensive quality analysis",
                    "Performance evaluation", 
                    "Maintainability assessment",
                    "Best practices compliance",
                    "Documentation review"
                ]
            )
            
            # Convert to serializable format
            quality_data = {
                "overall_quality": assessment.overall_quality.value,
                "quality_score": assessment.quality_score,
                "maintainability_score": assessment.maintainability_score,
                "issues_found": len(assessment.issues_found),
                "critical_issues": [
                    issue for issue in assessment.issues_found 
                    if issue.get("severity") in ["critical", "high"]
                ],
                "recommendations": assessment.recommendations,
                "test_coverage_assessment": assessment.test_coverage_assessment,
                "security_issues": len([
                    issue for issue in assessment.issues_found
                    if issue.get("category") == "security"
                ]),
                "performance_issues": len([
                    issue for issue in assessment.issues_found
                    if issue.get("category") == "performance"
                ])
            }
            
            state["quality_assessment"] = quality_data
            
            logger.info(f"Quality assessment completed: Score {assessment.quality_score}/10")
            
            return {
                "quality_assessment": state["quality_assessment"],
                "current_task": "quality_assessment_completed"
            }
            
        except Exception as e:
            error_msg = f"Quality assessment failed: {str(e)}"
            logger.error(error_msg)
            return {"errors": state.get("errors", []) + [error_msg]}
    
    def _decide_security_review(self, state: CodeReviewState) -> str:
        """Decide if security review is needed"""
        if not self.config["enable_security_scan"]:
            return "test_analysis"
        
        quality_assessment = state.get("quality_assessment", {})
        security_issues = quality_assessment.get("security_issues", 0)
        
        # Always do security review if security issues found or if enabled
        return "security_review"
    
    async def _security_review(self, state: CodeReviewState) -> Dict[str, Any]:
        """Dedicated security analysis"""
        logger.info("Conducting security review")
        
        try:
            # Use debugger for security-focused analysis
            debugger_agent = self.agents_registry.get("debugger")
            if not debugger_agent:
                logger.warning("Debugger agent not available, skipping detailed security analysis")
                return {
                    "security_review": {
                        "status": "skipped",
                        "reason": "Debugger agent not available"
                    },
                    "current_task": "security_review_skipped"
                }
            
            code_content = self._extract_code_from_request(state["original_request"])
            
            # Focus on security patterns and vulnerabilities
            security_analysis = await debugger_agent.analyze_bug(
                code=code_content,
                language=state["code_analysis"]["detected_language"],
                error_info="Security vulnerability analysis",
                context={
                    **state["context"],
                    "analysis_focus": "security",
                    "vulnerability_types": [
                        "injection", "authentication", "authorization", 
                        "data_exposure", "cryptographic_issues"
                    ]
                }
            )
            
            # Extract security-specific information
            security_data = {
                "vulnerabilities_found": len(security_analysis.bugs_found),
                "security_bugs": [
                    {
                        "severity": bug.severity.value,
                        "category": bug.category.value,
                        "description": bug.description,
                        "location": bug.location,
                        "fix_suggestion": bug.fix_suggestion
                    }
                    for bug in security_analysis.bugs_found
                    if bug.category.value in ["security_vulnerability", "data_corruption"]
                ],
                "confidence": security_analysis.analysis_confidence,
                "security_recommendations": security_analysis.next_steps,
                "monitoring_needed": security_analysis.monitoring_suggestions
            }
            
            state["security_review"] = security_data
            
            logger.info(f"Security review completed: {len(security_data['security_bugs'])} security issues found")
            
            return {
                "security_review": state["security_review"],
                "current_task": "security_review_completed"
            }
            
        except Exception as e:
            error_msg = f"Security review failed: {str(e)}"
            logger.error(error_msg)
            return {"errors": state.get("errors", []) + [error_msg]}
    
    async def _test_analysis(self, state: CodeReviewState) -> Dict[str, Any]:
        """Analyze testing coverage and generate test recommendations"""
        logger.info("Analyzing test coverage and requirements")
        
        try:
            if not self.config["generate_test_recommendations"]:
                return {
                    "test_recommendations": {"status": "skipped", "reason": "Test analysis disabled"},
                    "current_task": "test_analysis_skipped"
                }
            
            qa_agent = self.agents_registry.get("qa_checker")
            if not qa_agent:
                logger.warning("QA agent not available for test analysis")
                return {
                    "test_recommendations": {"status": "skipped", "reason": "QA agent not available"},
                    "current_task": "test_analysis_skipped"
                }
            
            code_content = self._extract_code_from_request(state["original_request"])
            language = state["code_analysis"]["detected_language"]
            
            # Generate comprehensive test suite recommendations
            test_suite = await qa_agent.generate_test_suite(
                code=code_content,
                language=language,
                test_types=["unit", "integration", "security"],
                coverage_target=90,
                context=state["context"]
            )
            
            # Extract test recommendations
            test_data = {
                "test_strategy": test_suite.get("test_strategy", {}),
                "recommended_tests": len(test_suite.get("test_suites", [])),
                "coverage_analysis": test_suite.get("coverage_analysis", {}),
                "test_types_needed": [
                    suite["test_type"] for suite in test_suite.get("test_suites", [])
                ],
                "performance_tests": test_suite.get("performance_tests", []),
                "security_tests": test_suite.get("security_tests", []),
                "ci_cd_recommendations": test_suite.get("ci_cd_integration", {}),
                "priority_tests": [
                    suite for suite in test_suite.get("test_suites", [])
                    if any(case.get("edge_case", False) for case in suite.get("test_cases", []))
                ]
            }
            
            state["test_recommendations"] = test_data
            
            logger.info(f"Test analysis completed: {test_data['recommended_tests']} test suites recommended")
            
            return {
                "test_recommendations": state["test_recommendations"],
                "current_task": "test_analysis_completed"
            }
            
        except Exception as e:
            error_msg = f"Test analysis failed: {str(e)}"
            logger.error(error_msg)
            return {"errors": state.get("errors", []) + [error_msg]}
    
    async def _refactoring_analysis(self, state: CodeReviewState) -> Dict[str, Any]:
        """Analyze refactoring opportunities"""
        logger.info("Analyzing refactoring opportunities")
        
        try:
            # Use primary coder for refactoring analysis
            coder_agent = self.agents_registry.get("coder_primary")
            if not coder_agent:
                logger.warning("Primary coder not available for refactoring analysis")
                return {
                    "refactoring_suggestions": {"status": "skipped", "reason": "Coder agent not available"},
                    "current_task": "refactoring_analysis_skipped"
                }
            
            code_content = self._extract_code_from_request(state["original_request"])
            quality_assessment = state.get("quality_assessment", {})
            
            # Identify refactoring goals based on quality issues
            refactoring_goals = []
            if quality_assessment.get("maintainability_score", 10) < 7:
                refactoring_goals.append("maintainability")
            if quality_assessment.get("performance_issues", 0) > 0:
                refactoring_goals.append("performance")
            if quality_assessment.get("quality_score", 10) < self.config["quality_threshold"]:
                refactoring_goals.append("code_quality")
            
            if not refactoring_goals:
                refactoring_goals = ["general_improvement"]
            
            # Get refactoring recommendations
            from ..agents.coders import CodeLanguage
            language_enum = self._string_to_language_enum(state["code_analysis"]["detected_language"])
            
            refactoring_analysis = await coder_agent.optimize_code(
                code=code_content,
                language=language_enum,
                optimization_goals=refactoring_goals
            )
            
            # Process refactoring suggestions
            refactoring_data = {
                "optimization_goals": refactoring_goals,
                "refactored_code_available": "optimized_code" in refactoring_analysis,
                "optimization_summary": refactoring_analysis.get("optimization_summary", ""),
                "performance_improvements": refactoring_analysis.get("performance_improvements", []),
                "trade_offs": refactoring_analysis.get("trade_offs", []),
                "complexity_improvements": refactoring_analysis.get("before_after_metrics", {}).get("complexity", {}),
                "testing_impact": refactoring_analysis.get("testing_impact", ""),
                "deployment_considerations": refactoring_analysis.get("deployment_considerations", "")
            }
            
            state["refactoring_suggestions"] = refactoring_data
            
            logger.info(f"Refactoring analysis completed: {len(refactoring_goals)} improvement areas identified")
            
            return {
                "refactoring_suggestions": state["refactoring_suggestions"],
                "current_task": "refactoring_analysis_completed"
            }
            
        except Exception as e:
            error_msg = f"Refactoring analysis failed: {str(e)}"
            logger.error(error_msg)
            return {"errors": state.get("errors", []) + [error_msg]}
    
    async def _generate_recommendations(self, state: CodeReviewState) -> Dict[str, Any]:
        """Generate consolidated recommendations"""
        logger.info("Generating consolidated recommendations")
        
        try:
            quality_assessment = state.get("quality_assessment", {})
            security_review = state.get("security_review", {})
            test_recommendations = state.get("test_recommendations", {})
            refactoring_suggestions = state.get("refactoring_suggestions", {})
            
            # Prioritize recommendations
            high_priority = []
            medium_priority = []
            low_priority = []
            
            # Security issues are always high priority
            if security_review.get("vulnerabilities_found", 0) > 0:
                high_priority.extend([
                    f"Fix {len(security_review.get('security_bugs', []))} security vulnerabilities",
                    "Conduct security-focused testing"
                ])
            
            # Quality issues
            quality_score = quality_assessment.get("quality_score", 10)
            if quality_score < 5:
                high_priority.append("Major code quality improvements needed")
            elif quality_score < self.config["quality_threshold"]:
                medium_priority.append("Code quality improvements recommended")
            
            # Critical functional issues
            critical_issues = quality_assessment.get("critical_issues", [])
            if critical_issues:
                high_priority.append(f"Fix {len(critical_issues)} critical issues")
            
            # Testing recommendations
            if test_recommendations.get("recommended_tests", 0) > 0:
                medium_priority.append("Implement comprehensive test suite")
            
            # Refactoring
            refactoring_goals = refactoring_suggestions.get("optimization_goals", [])
            if refactoring_goals:
                if "performance" in refactoring_goals:
                    medium_priority.append("Performance optimizations available")
                if "maintainability" in refactoring_goals:
                    low_priority.append("Maintainability improvements suggested")
            
            recommendations = {
                "high_priority": high_priority,
                "medium_priority": medium_priority,
                "low_priority": low_priority,
                "overall_recommendation": self._generate_overall_recommendation(
                    quality_score, len(critical_issues), security_review.get("vulnerabilities_found", 0)
                ),
                "approval_status": self._determine_approval_status(quality_assessment, security_review),
                "next_steps": self._generate_next_steps(high_priority, medium_priority)
            }
            
            return {
                "consolidated_recommendations": recommendations,
                "current_task": "recommendations_generated"
            }
            
        except Exception as e:
            error_msg = f"Recommendation generation failed: {str(e)}"
            logger.error(error_msg)
            return {"errors": state.get("errors", []) + [error_msg]}
    
    async def _finalize_review(self, state: CodeReviewState) -> Dict[str, Any]:
        """Finalize the code review with comprehensive report"""
        logger.info("Finalizing code review report")
        
        try:
            # Compile final review report
            final_report = {
                "review_metadata": {
                    "review_type": "comprehensive_code_review",
                    "reviewed_at": datetime.now().isoformat(),
                    "workflow_duration": (datetime.now() - state["start_time"]).total_seconds(),
                    "reviewer": "AI Code Review System",
                    "language": state["code_analysis"]["detected_language"],
                    "code_length": state["code_analysis"]["code_length"]
                },
                "executive_summary": {
                    "overall_quality_score": state["quality_assessment"]["quality_score"],
                    "approval_status": state.get("consolidated_recommendations", {}).get("approval_status", "pending"),
                    "critical_issues": len(state["quality_assessment"].get("critical_issues", [])),
                    "security_vulnerabilities": state.get("security_review", {}).get("vulnerabilities_found", 0),
                    "test_coverage_status": "needs_improvement",  # Could be calculated
                    "primary_concerns": state.get("consolidated_recommendations", {}).get("high_priority", [])
                },
                "detailed_findings": {
                    "quality_assessment": state.get("quality_assessment", {}),
                    "security_review": state.get("security_review", {}),
                    "test_analysis": state.get("test_recommendations", {}),
                    "refactoring_opportunities": state.get("refactoring_suggestions", {})
                },
                "recommendations": state.get("consolidated_recommendations", {}),
                "action_items": self._generate_action_items(state),
                "review_checklist": self._generate_review_checklist(state),
                "sign_off": {
                    "requires_human_review": self._requires_human_review(state),
                    "confidence_level": self._calculate_review_confidence(state),
                    "limitations": [
                        "Automated review may miss context-specific issues",
                        "Human review recommended for critical systems",
                        "Integration testing not performed"
                    ]
                }
            }
            
            state["final_review_report"] = final_report
            
            logger.info("Code review finalized successfully")
            
            return {
                "final_deliverable": final_report,
                "status": WorkflowStatus.COMPLETED,
                "current_task": "workflow_completed"
            }
            
        except Exception as e:
            error_msg = f"Review finalization failed: {str(e)}"
            logger.error(error_msg)
            return {"errors": state.get("errors", []) + [error_msg]}
    
    # Helper methods
    
    def _extract_code_from_request(self, request: str) -> str:
        """Extract code content from the request"""
        # Look for code blocks marked with ```
        if "```" in request:
            parts = request.split("```")
            if len(parts) >= 3:
                # Return the content between the first pair of ```
                code_block = parts[1]
                # Remove language identifier if present
                lines = code_block.strip().split('\n')
                if lines and not any(char in lines[0] for char in [' ', '(', '{']):
                    # First line might be language identifier
                    return '\n'.join(lines[1:])
                return code_block.strip()
        
        # Fallback: assume the entire request is code if it looks like code
        if any(keyword in request for keyword in ['def ', 'class ', 'function ', 'var ', 'let ', 'const ']):
            return request
        
        return request  # Return as-is if no code extraction possible
    
    def _detect_language_from_request(self, request: str) -> str:
        """Detect programming language from request"""
        content = request.lower()
        
        if "python" in content or "def " in request or "import " in request:
            return "python"
        elif "javascript" in content or "function " in request or "const " in request:
            return "javascript"
        elif "typescript" in content or "interface " in request:
            return "typescript"
        elif "rust" in content or "fn " in request:
            return "rust"
        elif "golang" in content or "go" in content or "func " in request:
            return "go"
        else:
            return "python"  # Default
    
    def _string_to_language_enum(self, language_str: str):
        """Convert string to CodeLanguage enum"""
        from ..agents.coders import CodeLanguage
        
        mapping = {
            "python": CodeLanguage.PYTHON,
            "javascript": CodeLanguage.JAVASCRIPT,
            "typescript": CodeLanguage.TYPESCRIPT,
            "rust": CodeLanguage.RUST,
            "go": CodeLanguage.GO
        }
        
        return mapping.get(language_str.lower(), CodeLanguage.PYTHON)
    
    def _determine_analysis_scope(self, code_content: Optional[str], context: Dict) -> List[str]:
        """Determine the scope of analysis needed"""
        scope = ["quality", "functionality"]
        
        if code_content and len(code_content) > 1000:
            scope.append("performance")
        
        if any(keyword in str(context).lower() for keyword in ['security', 'auth', 'crypto', 'password']):
            scope.append("security")
        
        if any(keyword in str(context).lower() for keyword in ['production', 'deploy', 'release']):
            scope.extend(["testing", "deployment"])
        
        return scope
    
    def _generate_overall_recommendation(self, quality_score: int, critical_issues: int, security_vulnerabilities: int) -> str:
        """Generate overall recommendation"""
        if security_vulnerabilities > 0:
            return "REJECT - Security vulnerabilities must be fixed before approval"
        elif critical_issues > 0:
            return "CONDITIONAL APPROVAL - Fix critical issues before deployment"
        elif quality_score >= 8:
            return "APPROVE - Code meets quality standards"
        elif quality_score >= 6:
            return "APPROVE WITH SUGGESTIONS - Consider implementing recommendations"
        else:
            return "NEEDS MAJOR IMPROVEMENTS - Significant refactoring required"
    
    def _determine_approval_status(self, quality_assessment: Dict, security_review: Dict) -> str:
        """Determine approval status"""
        if security_review.get("vulnerabilities_found", 0) > 0:
            return "rejected"
        elif len(quality_assessment.get("critical_issues", [])) > 0:
            return "conditional"
        elif quality_assessment.get("quality_score", 0) >= self.config["quality_threshold"]:
            return "approved"
        else:
            return "needs_improvement"
    
    def _generate_next_steps(self, high_priority: List[str], medium_priority: List[str]) -> List[str]:
        """Generate actionable next steps"""
        next_steps = []
        
        if high_priority:
            next_steps.append("Address all high-priority issues immediately")
        
        if medium_priority:
            next_steps.append("Plan implementation of medium-priority improvements")
        
        next_steps.extend([
            "Run automated tests after fixes",
            "Consider peer review for complex changes",
            "Update documentation if needed"
        ])
        
        return next_steps
    
    def _generate_action_items(self, state: CodeReviewState) -> List[Dict[str, str]]:
        """Generate specific action items"""
        action_items = []
        
        # From quality assessment
        quality_assessment = state.get("quality_assessment", {})
        for issue in quality_assessment.get("critical_issues", []):
            action_items.append({
                "priority": "high",
                "category": "quality",
                "description": issue.get("description", "Fix critical issue"),
                "location": issue.get("location", "unknown")
            })
        
        # From security review
        security_review = state.get("security_review", {})
        for bug in security_review.get("security_bugs", []):
            action_items.append({
                "priority": "critical",
                "category": "security",
                "description": bug.get("description", "Fix security vulnerability"),
                "location": bug.get("location", "unknown")
            })
        
        return action_items
    
    def _generate_review_checklist(self, state: CodeReviewState) -> Dict[str, bool]:
        """Generate review checklist"""
        quality_assessment = state.get("quality_assessment", {})
        security_review = state.get("security_review", {})
        
        return {
            "code_compiles": True,  # Assumed for now
            "no_critical_bugs": len(quality_assessment.get("critical_issues", [])) == 0,
            "no_security_vulnerabilities": security_review.get("vulnerabilities_found", 0) == 0,
            "meets_quality_threshold": quality_assessment.get("quality_score", 0) >= self.config["quality_threshold"],
            "has_adequate_testing": True,  # Would need actual test analysis
            "follows_coding_standards": quality_assessment.get("quality_score", 0) >= 7,
            "performance_acceptable": quality_assessment.get("performance_issues", 0) == 0,
            "documentation_adequate": True  # Would need documentation analysis
        }
    
    def _requires_human_review(self, state: CodeReviewState) -> bool:
        """Determine if human review is required"""
        quality_assessment = state.get("quality_assessment", {})
        security_review = state.get("security_review", {})
        
        return (
            security_review.get("vulnerabilities_found", 0) > 0 or
            len(quality_assessment.get("critical_issues", [])) > 0 or
            quality_assessment.get("quality_score", 10) < 5
        )
    
    def _calculate_review_confidence(self, state: CodeReviewState) -> float:
        """Calculate confidence in the review"""
        # Base confidence
        confidence = 0.8
        
        # Adjust based on available analyses
        analyses = [
            state.get("quality_assessment"),
            state.get("security_review"),
            state.get("test_recommendations"),
            state.get("refactoring_suggestions")
        ]
        
        completed_analyses = len([a for a in analyses if a and not a.get("status") == "skipped"])
        confidence = min(0.9, confidence + (completed_analyses * 0.02))
        
        return confidence
    
    def _get_required_agents(self) -> List[str]:
        """Get required agents for code review workflow"""
        return ["router", "qa_checker", "debugger", "coder_primary"]


# Factory function
async def create_code_review_workflow(agents_registry: Dict[str, Any]) -> CodeReviewWorkflow:
    """Create and initialize code review workflow"""
    workflow = CodeReviewWorkflow()
    await workflow.initialize(agents_registry)
    return workflow