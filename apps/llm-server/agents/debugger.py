"""
Debugger Agent - Error analysis and debugging using DeepSeek-Coder-V2-16B
Specializes in bug detection, error analysis, and systematic debugging
"""

import asyncio
import logging
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from ..configs.llama_cpp.optimized_llama import OptimizedLlama, MODEL_POOL


logger = logging.getLogger(__name__)


class BugSeverity(Enum):
    """Bug severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    COSMETIC = "cosmetic"


class BugCategory(Enum):
    """Categories of bugs"""
    LOGIC_ERROR = "logic_error"
    RUNTIME_ERROR = "runtime_error"
    MEMORY_LEAK = "memory_leak"
    PERFORMANCE_ISSUE = "performance_issue"
    SECURITY_VULNERABILITY = "security_vulnerability"
    RACE_CONDITION = "race_condition"
    CONFIGURATION_ERROR = "configuration_error"
    INTEGRATION_ISSUE = "integration_issue"
    DATA_CORRUPTION = "data_corruption"
    UI_UX_BUG = "ui_ux_bug"


class DebugStrategy(Enum):
    """Debugging strategies"""
    SYSTEMATIC_ISOLATION = "systematic_isolation"
    BINARY_SEARCH = "binary_search"
    RUBBER_DUCK = "rubber_duck"
    PRINT_DEBUGGING = "print_debugging"
    STEP_THROUGH_DEBUGGING = "step_through_debugging"
    LOG_ANALYSIS = "log_analysis"
    UNIT_TEST_ISOLATION = "unit_test_isolation"
    PROFILING = "profiling"


@dataclass
class BugReport:
    """Structured bug analysis report"""
    bug_id: str
    severity: BugSeverity
    category: BugCategory
    description: str
    location: str
    reproduction_steps: List[str]
    root_cause: str
    fix_suggestion: str
    test_cases: List[str]
    prevention_measures: List[str]
    estimated_fix_time: str


@dataclass 
class DebugAnalysis:
    """Complete debugging analysis"""
    bugs_found: List[BugReport]
    debug_strategy: DebugStrategy
    analysis_confidence: float
    next_steps: List[str]
    monitoring_suggestions: List[str]
    additional_investigation: List[str]


class DebuggerAgent:
    """Advanced debugger agent for systematic error analysis and resolution"""
    
    def __init__(self, model_path: str):
        self.model_id = "debugger"
        self.model_path = model_path
        self.model: Optional[OptimizedLlama] = None
        
        # Comprehensive debugging analysis template
        self.debug_analysis_template = """You are a senior software engineer and debugging specialist with deep expertise in error analysis, root cause identification, and systematic debugging.

Code with Issues:
```{language}
{code}
```

Error Information:
{error_info}

Context:
{context}

Debugging Requirements:
{requirements}

Conduct a thorough debugging analysis in JSON format:

{{
    "initial_assessment": {{
        "error_type": "runtime|logic|performance|security|integration",
        "severity_level": "critical|high|medium|low",
        "immediate_impact": "Description of current impact",
        "potential_consequences": "What could happen if not fixed"
    }},
    "bugs_identified": [
        {{
            "bug_id": "BUG-001",
            "severity": "critical|high|medium|low|cosmetic",
            "category": "logic_error|runtime_error|memory_leak|performance_issue|security_vulnerability",
            "description": "Clear description of the bug",
            "location": "File:Line or function/method name", 
            "reproduction_steps": [
                "Step 1: Specific action to reproduce",
                "Step 2: Expected vs actual behavior",
                "Step 3: Consistent reproduction method"
            ],
            "root_cause": "Deep analysis of why this bug exists",
            "fix_suggestion": "Detailed, actionable fix with code examples",
            "test_cases": [
                "Test case 1: Verify fix works",
                "Test case 2: Ensure no regression",
                "Test case 3: Edge case coverage"
            ],
            "prevention_measures": [
                "How to prevent similar bugs in the future",
                "Process improvements",
                "Code review checklist additions"
            ],
            "estimated_fix_time": "2 hours|1 day|3 days|1 week"
        }}
    ],
    "debug_strategy": {{
        "recommended_approach": "systematic_isolation|binary_search|log_analysis|profiling",
        "debugging_steps": [
            "Step 1: Immediate actions to take",
            "Step 2: Systematic investigation approach",
            "Step 3: Verification and testing"
        ],
        "tools_needed": ["debugger", "profiler", "logging framework"],
        "environment_setup": "How to set up debugging environment"
    }},
    "code_fixes": [
        {{
            "bug_id": "BUG-001",
            "original_code": "// Buggy code snippet",
            "fixed_code": "// Corrected code with explanation comments",
            "explanation": "Why this fix addresses the root cause",
            "side_effects": "Potential impacts of this fix"
        }}
    ],
    "testing_strategy": {{
        "regression_tests": ["Test to ensure bug is fixed"],
        "edge_case_tests": ["Tests for boundary conditions"],
        "integration_tests": ["Tests for system interactions"],
        "performance_tests": ["Tests to verify no performance regression"]
    }},
    "monitoring_and_prevention": {{
        "logging_additions": ["What logging to add for future debugging"],
        "metrics_to_track": ["Performance/error metrics to monitor"],
        "alerting_setup": ["When and how to alert on similar issues"],
        "code_quality_improvements": ["Practices to prevent similar bugs"]
    }},
    "deployment_considerations": {{
        "rollback_plan": "How to rollback if fix causes issues",
        "deployment_timing": "Best time/method to deploy fix",
        "monitoring_post_deployment": "What to watch after deployment",
        "communication_plan": "How to communicate fix to stakeholders"
    }},
    "confidence_level": 95,
    "additional_investigation": [
        "Areas that may need further investigation",
        "Potential related issues to check"
    ]
}}

Provide systematic, thorough analysis with actionable solutions."""
        
        # Error pattern analysis template
        self.error_pattern_template = """You are analyzing error patterns and logs to identify systemic issues.

Error Logs/Patterns:
{error_logs}

System Context:
{system_context}

Analyze patterns and provide insights in JSON format:

{{
    "pattern_analysis": {{
        "error_frequency": "Pattern frequency analysis",
        "error_clustering": "Related errors that occur together",
        "temporal_patterns": "Time-based error patterns",
        "correlation_analysis": "Correlations with system events"
    }},
    "systemic_issues": [
        {{
            "issue_type": "resource_exhaustion|configuration_drift|integration_failure",
            "description": "What systemic issue is causing errors",
            "evidence": "Evidence supporting this analysis",
            "impact_scope": "How widespread the issue is",
            "urgency": "How urgently this needs to be addressed"
        }}
    ],
    "root_cause_hypothesis": [
        "Hypothesis 1 with supporting evidence",
        "Hypothesis 2 with supporting evidence"
    ],
    "investigation_plan": [
        "Step 1: Immediate data collection",
        "Step 2: Systematic testing",
        "Step 3: Root cause validation"
    ],
    "immediate_actions": [
        "Action 1: Stop the bleeding",
        "Action 2: Collect more data",
        "Action 3: Implement temporary fixes"
    ],
    "long_term_solutions": [
        "Solution 1: Address root cause",
        "Solution 2: Improve monitoring",
        "Solution 3: Prevent recurrence"
    ]
}}

Focus on finding patterns and systemic issues rather than individual bugs."""
        
        # Performance debugging template
        self.performance_debug_template = """You are debugging performance issues and bottlenecks.

Performance Problem:
{performance_issue}

Code/System:
```{language}
{code}
```

Performance Metrics:
{metrics}

Provide performance debugging analysis in JSON format:

{{
    "performance_analysis": {{
        "bottleneck_identification": [
            {{
                "location": "Function/method/system component",
                "type": "cpu|memory|io|network|database",
                "severity": "critical|high|medium|low",
                "description": "What is causing the bottleneck",
                "evidence": "Metrics/data supporting this finding"
            }}
        ],
        "resource_utilization": {{
            "cpu_analysis": "CPU usage patterns and issues",
            "memory_analysis": "Memory usage and potential leaks", 
            "io_analysis": "I/O patterns and bottlenecks",
            "network_analysis": "Network latency and throughput issues"
        }}
    }},
    "optimization_recommendations": [
        {{
            "optimization": "Specific optimization technique",
            "expected_improvement": "Quantified performance improvement",
            "implementation_effort": "Low|Medium|High effort required",
            "risk_level": "Low|Medium|High risk of introducing bugs",
            "code_changes": "// Specific code changes needed"
        }}
    ],
    "profiling_strategy": {{
        "profiling_tools": ["tool1", "tool2"],
        "key_metrics": ["metric1", "metric2"],
        "profiling_scenarios": ["scenario1", "scenario2"],
        "analysis_approach": "How to analyze profiling results"
    }},
    "testing_approach": {{
        "baseline_establishment": "How to establish performance baseline",
        "load_testing": "Load testing strategy for validation",
        "monitoring_setup": "Performance monitoring configuration"
    }},
    "implementation_plan": [
        "Phase 1: Quick wins and immediate improvements",
        "Phase 2: Moderate effort optimizations", 
        "Phase 3: Major architectural improvements"
    ]
}}

Focus on measurable performance improvements with clear implementation guidance."""
    
    async def initialize(self):
        """Initialize the debugger model"""
        logger.info(f"Initializing Debugger agent with model: {self.model_path}")
        
        self.model = await MODEL_POOL.get_model(
            model_id=self.model_id,
            model_path=self.model_path,
            model_type="debugger"
        )
        
        logger.info("Debugger agent initialized successfully")
    
    async def analyze_bug(
        self,
        code: str,
        language: str,
        error_info: str,
        context: Optional[Dict] = None,
        requirements: Optional[List[str]] = None
    ) -> DebugAnalysis:
        """Conduct comprehensive bug analysis"""
        if not self.model:
            await self.initialize()
        
        context_str = json.dumps(context or {}, indent=2)
        requirements_str = "\n".join(requirements or ["General debugging analysis"])
        
        prompt = self.debug_analysis_template.format(
            language=language,
            code=code,
            error_info=error_info,
            context=context_str,
            requirements=requirements_str
        )
        
        try:
            async for response in self.model.generate_async(
                prompt=prompt,
                max_tokens=2500,  # Complex debugging needs comprehensive analysis
                temperature=0.2,  # Low temperature for systematic, consistent analysis
                top_p=0.9,
                stop=["}\n\n\n", "\n\n---"]
            ):
                json_text = response.get("choices", [{}])[0].get("text", "").strip()
                
                # Clean and parse JSON
                if "{" in json_text:
                    json_start = json_text.find("{")
                    json_end = json_text.rfind("}") + 1
                    json_text = json_text[json_start:json_end]
                
                try:
                    debug_data = json.loads(json_text)
                    return self._create_debug_analysis(debug_data)
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse debug analysis JSON: {e}")
                    return self._create_fallback_analysis(error_info)
        
        except Exception as e:
            logger.error(f"Debug analysis error: {e}")
            return self._create_fallback_analysis(error_info)
    
    async def analyze_error_patterns(
        self,
        error_logs: str,
        system_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Analyze error patterns to identify systemic issues"""
        if not self.model:
            await self.initialize()
        
        context_str = json.dumps(system_context or {}, indent=2)
        
        prompt = self.error_pattern_template.format(
            error_logs=error_logs,
            system_context=context_str
        )
        
        try:
            async for response in self.model.generate_async(
                prompt=prompt,
                max_tokens=2000,
                temperature=0.3,  # Slightly higher for pattern recognition
                top_p=0.9
            ):
                json_text = response.get("choices", [{}])[0].get("text", "").strip()
                
                if "{" in json_text:
                    json_start = json_text.find("{")
                    json_end = json_text.rfind("}") + 1
                    json_text = json_text[json_start:json_end]
                
                try:
                    return json.loads(json_text)
                except json.JSONDecodeError:
                    return {"error": "Failed to parse error pattern analysis"}
        
        except Exception as e:
            logger.error(f"Error pattern analysis failed: {e}")
            return {"error": f"Pattern analysis failed: {str(e)}"}
    
    async def debug_performance_issue(
        self,
        performance_issue: str,
        code: str,
        language: str,
        metrics: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Debug performance issues and bottlenecks"""
        if not self.model:
            await self.initialize()
        
        metrics_str = json.dumps(metrics or {}, indent=2)
        
        prompt = self.performance_debug_template.format(
            performance_issue=performance_issue,
            code=code,
            language=language,
            metrics=metrics_str
        )
        
        try:
            async for response in self.model.generate_async(
                prompt=prompt,
                max_tokens=2000,
                temperature=0.2,  # Precise analysis for performance issues
                top_p=0.9
            ):
                json_text = response.get("choices", [{}])[0].get("text", "").strip()
                
                if "{" in json_text:
                    json_start = json_text.find("{")
                    json_end = json_text.rfind("}") + 1
                    json_text = json_text[json_start:json_end]
                
                try:
                    return json.loads(json_text)
                except json.JSONDecodeError:
                    return {"error": "Failed to parse performance analysis"}
        
        except Exception as e:
            logger.error(f"Performance debugging error: {e}")
            return {"error": f"Performance analysis failed: {str(e)}"}
    
    async def suggest_quick_fix(
        self,
        error_message: str,
        code_snippet: str,
        language: str
    ) -> Dict[str, Any]:
        """Provide quick fix suggestions for immediate issues"""
        if not self.model:
            await self.initialize()
        
        quick_fix_prompt = f"""You are providing a quick fix for an immediate issue in {language}.

Error Message: {error_message}

Code Snippet:
```{language}
{code_snippet}
```

Provide a quick fix solution in JSON format:

{{
    "quick_fix": {{
        "fixed_code": "// Corrected code snippet",
        "explanation": "Why this fixes the immediate issue",
        "confidence": 95,
        "trade_offs": "What this quick fix doesn't address"
    }},
    "immediate_actions": [
        "Action 1: Deploy this fix",
        "Action 2: Monitor for side effects",
        "Action 3: Plan proper long-term solution"
    ],
    "monitoring": [
        "What to monitor after applying fix",
        "Warning signs that fix isn't working"
    ],
    "follow_up_needed": [
        "Proper root cause analysis",
        "Comprehensive testing",
        "Long-term architectural improvements"
    ],
    "rollback_plan": "How to rollback if this fix causes issues"
}}

Focus on stopping the immediate problem while acknowledging this may not be the perfect long-term solution."""
        
        try:
            async for response in self.model.generate_async(
                prompt=quick_fix_prompt,
                max_tokens=1000,  # Quick fixes should be concise
                temperature=0.1,  # Very low temperature for reliable fixes
                top_p=0.9
            ):
                json_text = response.get("choices", [{}])[0].get("text", "").strip()
                
                if "{" in json_text:
                    json_start = json_text.find("{")
                    json_end = json_text.rfind("}") + 1
                    json_text = json_text[json_start:json_end]
                
                try:
                    return json.loads(json_text)
                except json.JSONDecodeError:
                    return {"error": "Failed to parse quick fix suggestions"}
        
        except Exception as e:
            logger.error(f"Quick fix generation error: {e}")
            return {"error": f"Quick fix failed: {str(e)}"}
    
    def _create_debug_analysis(self, data: Dict) -> DebugAnalysis:
        """Create DebugAnalysis from parsed data"""
        try:
            bugs = []
            for bug_data in data.get("bugs_identified", []):
                try:
                    bug = BugReport(
                        bug_id=bug_data.get("bug_id", "BUG-UNKNOWN"),
                        severity=BugSeverity(bug_data.get("severity", "medium")),
                        category=BugCategory(bug_data.get("category", "logic_error")),
                        description=bug_data.get("description", "Unknown bug"),
                        location=bug_data.get("location", "Unknown location"),
                        reproduction_steps=bug_data.get("reproduction_steps", []),
                        root_cause=bug_data.get("root_cause", "Unknown cause"),
                        fix_suggestion=bug_data.get("fix_suggestion", "Manual investigation needed"),
                        test_cases=bug_data.get("test_cases", []),
                        prevention_measures=bug_data.get("prevention_measures", []),
                        estimated_fix_time=bug_data.get("estimated_fix_time", "Unknown")
                    )
                    bugs.append(bug)
                except Exception as e:
                    logger.warning(f"Error parsing bug data: {e}")
            
            strategy_name = data.get("debug_strategy", {}).get("recommended_approach", "systematic_isolation")
            try:
                strategy = DebugStrategy(strategy_name)
            except ValueError:
                strategy = DebugStrategy.SYSTEMATIC_ISOLATION
            
            return DebugAnalysis(
                bugs_found=bugs,
                debug_strategy=strategy,
                analysis_confidence=data.get("confidence_level", 70) / 100.0,
                next_steps=data.get("debug_strategy", {}).get("debugging_steps", []),
                monitoring_suggestions=data.get("monitoring_and_prevention", {}).get("logging_additions", []),
                additional_investigation=data.get("additional_investigation", [])
            )
            
        except Exception as e:
            logger.error(f"Error creating debug analysis: {e}")
            return self._create_fallback_analysis("Analysis failed")
    
    def _create_fallback_analysis(self, error_info: str) -> DebugAnalysis:
        """Create fallback debug analysis when parsing fails"""
        fallback_bug = BugReport(
            bug_id="BUG-FALLBACK",
            severity=BugSeverity.MEDIUM,
            category=BugCategory.LOGIC_ERROR,
            description="Automated analysis failed - manual debugging required",
            location="Unknown",
            reproduction_steps=["Manual investigation needed"],
            root_cause="Analysis system unable to process error information",
            fix_suggestion="Conduct manual debugging session",
            test_cases=["Create minimal reproduction case"],
            prevention_measures=["Improve error reporting"],
            estimated_fix_time="Manual estimation required"
        )
        
        return DebugAnalysis(
            bugs_found=[fallback_bug],
            debug_strategy=DebugStrategy.SYSTEMATIC_ISOLATION,
            analysis_confidence=0.3,
            next_steps=["Manual code review", "Step-through debugging"],
            monitoring_suggestions=["Add detailed logging"],
            additional_investigation=["Review recent changes", "Check system logs"]
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for debugger agent"""
        try:
            if not self.model:
                return {"status": "unhealthy", "reason": "Model not loaded"}
            
            # Quick debugging test
            test_code = "def divide(a, b): return a / b"
            test_error = "ZeroDivisionError: division by zero"
            
            analysis = await self.analyze_bug(test_code, "python", test_error)
            
            return {
                "status": "healthy",
                "model_id": self.model_id,
                "model_loaded": self.model.is_loaded,
                "test_analysis": {
                    "bugs_found": len(analysis.bugs_found),
                    "strategy": analysis.debug_strategy.value,
                    "confidence": analysis.analysis_confidence
                },
                "capabilities": [
                    "Comprehensive bug analysis",
                    "Error pattern recognition", 
                    "Performance debugging",
                    "Quick fix suggestions",
                    "Systematic root cause analysis"
                ]
            }
            
        except Exception as e:
            return {"status": "unhealthy", "reason": str(e)}


# Global debugger instance
debugger_agent: Optional[DebuggerAgent] = None


async def get_debugger_agent(model_path: str) -> DebuggerAgent:
    """Get or create debugger agent instance"""
    global debugger_agent
    
    if debugger_agent is None:
        debugger_agent = DebuggerAgent(model_path)
        await debugger_agent.initialize()
    
    return debugger_agent