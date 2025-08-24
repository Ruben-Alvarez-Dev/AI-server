"""
QA Checker Agent - Quality assurance and testing using Qwen2.5-14B
Specializes in code review, testing, validation, and quality assurance
"""

import asyncio
import logging
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from ..configs.llama_cpp.optimized_llama import OptimizedLlama, MODEL_POOL


logger = logging.getLogger(__name__)


class QualityLevel(Enum):
    """Quality assessment levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    NEEDS_IMPROVEMENT = "needs_improvement"
    POOR = "poor"


class TestType(Enum):
    """Types of tests"""
    UNIT = "unit"
    INTEGRATION = "integration"
    FUNCTIONAL = "functional"
    PERFORMANCE = "performance"
    SECURITY = "security"
    ACCEPTANCE = "acceptance"
    REGRESSION = "regression"
    SMOKE = "smoke"


class ReviewCategory(Enum):
    """Code review categories"""
    FUNCTIONALITY = "functionality"
    PERFORMANCE = "performance"
    SECURITY = "security"
    MAINTAINABILITY = "maintainability"
    READABILITY = "readability"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    ARCHITECTURE = "architecture"


@dataclass
class QualityAssessment:
    """Result of quality assessment"""
    overall_quality: QualityLevel
    quality_score: int  # 1-10 scale
    issues_found: List[Dict[str, Any]]
    recommendations: List[str]
    test_coverage_assessment: Dict[str, Any]
    security_review: Dict[str, Any]
    performance_analysis: Dict[str, Any]
    maintainability_score: int
    automated_test_suggestions: List[Dict[str, Any]]


class QACheckerAgent:
    """Quality assurance agent for comprehensive code review and testing"""
    
    def __init__(self, model_path: str):
        self.model_id = "qa_checker"
        self.model_path = model_path
        self.model: Optional[OptimizedLlama] = None
        
        # Comprehensive review template
        self.code_review_template = """You are a senior QA engineer and code reviewer with expertise in software quality, testing, and best practices. Conduct a thorough review of the provided code.

Code to Review:
```{language}
{code}
```

Context:
{context}

Review Requirements:
{requirements}

Provide a comprehensive quality assessment in JSON format:

{{
    "overall_quality": "excellent|good|acceptable|needs_improvement|poor",
    "quality_score": 8,
    "detailed_analysis": {{
        "functionality": {{
            "score": 8,
            "assessment": "Functionality analysis",
            "issues": ["Issue 1", "Issue 2"],
            "recommendations": ["Fix 1", "Fix 2"]
        }},
        "performance": {{
            "score": 7,
            "assessment": "Performance analysis",
            "bottlenecks": ["Bottleneck 1", "Bottleneck 2"],
            "optimizations": ["Optimization 1", "Optimization 2"]
        }},
        "security": {{
            "score": 6,
            "vulnerabilities": ["Vuln 1", "Vuln 2"],
            "recommendations": ["Security fix 1", "Security fix 2"],
            "compliance": "Security standards compliance assessment"
        }},
        "maintainability": {{
            "score": 9,
            "code_complexity": "Low|Medium|High",
            "readability": "Excellent|Good|Fair|Poor",
            "modularity": "Well modularized|Needs improvement",
            "documentation": "Well documented|Needs documentation"
        }}
    }},
    "critical_issues": [
        {{
            "severity": "critical|high|medium|low",
            "category": "bug|security|performance|style|architecture",
            "description": "Detailed issue description",
            "location": "File/line information",
            "impact": "Impact on system/users",
            "fix_priority": "immediate|high|medium|low",
            "suggested_fix": "Specific fix recommendation"
        }}
    ],
    "test_coverage_assessment": {{
        "estimated_coverage": "85%",
        "missing_test_areas": ["Area 1", "Area 2"],
        "test_quality": "Good|Fair|Poor",
        "edge_cases_covered": true,
        "test_recommendations": ["Add test 1", "Add test 2"]
    }},
    "automated_tests_needed": [
        {{
            "test_type": "unit|integration|functional",
            "description": "What to test",
            "priority": "high|medium|low",
            "test_cases": ["Test case 1", "Test case 2"]
        }}
    ],
    "refactoring_suggestions": [
        "Refactoring suggestion 1 with benefits",
        "Refactoring suggestion 2 with benefits"
    ],
    "best_practices_compliance": {{
        "follows_conventions": true,
        "uses_design_patterns": true,
        "error_handling": "Comprehensive|Adequate|Insufficient",
        "logging": "Well implemented|Needs improvement|Missing"
    }},
    "deployment_readiness": {{
        "production_ready": true,
        "blockers": ["Blocker 1", "Blocker 2"],
        "pre_deployment_tasks": ["Task 1", "Task 2"]
    }}
}}

Conduct a thorough, professional review focusing on quality, security, performance, and maintainability."""
        
        # Test generation template
        self.test_generation_template = """You are a test automation specialist. Generate comprehensive test suites for the provided code.

Code to Test:
```{language}
{code}
```

Test Requirements:
- Test types needed: {test_types}
- Coverage target: {coverage_target}
- Framework preference: {framework}

Context: {context}

Generate a complete test strategy in JSON format:

{{
    "test_strategy": {{
        "approach": "TDD|BDD|Traditional testing approach",
        "test_pyramid": {{
            "unit_tests": "70%",
            "integration_tests": "20%", 
            "e2e_tests": "10%"
        }},
        "testing_framework": "Recommended framework and tools"
    }},
    "test_suites": [
        {{
            "test_type": "unit|integration|functional",
            "test_file": "test_filename.ext",
            "test_code": "// Complete test implementation",
            "test_cases": [
                {{
                    "name": "test_case_name",
                    "description": "What this test verifies", 
                    "input": "Test input data",
                    "expected_output": "Expected result",
                    "edge_case": true
                }}
            ]
        }}
    ],
    "test_data": {{
        "fixtures": ["fixture1.json", "fixture2.json"],
        "mocks": [
            {{
                "service": "ServiceName",
                "mock_implementation": "// Mock code",
                "scenarios": ["success", "failure", "timeout"]
            }}
        ],
        "test_databases": ["test_schema.sql", "test_data.sql"]
    }},
    "coverage_analysis": {{
        "line_coverage_target": "90%",
        "branch_coverage_target": "85%",
        "function_coverage_target": "100%",
        "critical_paths": ["Path 1", "Path 2"]
    }},
    "performance_tests": [
        {{
            "test_name": "load_test_endpoint",
            "description": "Load testing for API endpoint",
            "test_implementation": "// Performance test code",
            "success_criteria": "Response time < 200ms, 99.9% success rate"
        }}
    ],
    "security_tests": [
        {{
            "test_name": "input_validation_test",
            "description": "Verify input sanitization",
            "test_implementation": "// Security test code",
            "attack_vectors": ["SQL injection", "XSS", "CSRF"]
        }}
    ],
    "ci_cd_integration": {{
        "pre_commit_hooks": ["linting", "unit tests"],
        "pipeline_stages": ["test", "security scan", "coverage report"],
        "quality_gates": ["80% coverage", "0 critical issues"]
    }},
    "maintenance_strategy": "How to maintain and extend the test suite"
}}

Create comprehensive tests that ensure reliability, catch regressions, and support continuous development."""
        
        # Quality metrics and standards
        self.quality_standards = {
            "code_coverage": {"minimum": 80, "target": 90, "excellent": 95},
            "complexity": {"low": 5, "medium": 10, "high": 15},
            "maintainability": {"excellent": 9, "good": 7, "acceptable": 5},
            "security": {"critical_threshold": 0, "high_threshold": 2, "medium_threshold": 5}
        }
    
    async def initialize(self):
        """Initialize the QA checker model"""
        logger.info(f"Initializing QA Checker agent with model: {self.model_path}")
        
        self.model = await MODEL_POOL.get_model(
            model_id=self.model_id,
            model_path=self.model_path,
            model_type="qa_checker"
        )
        
        logger.info("QA Checker agent initialized successfully")
    
    async def conduct_code_review(
        self,
        code: str,
        language: str,
        context: Optional[Dict] = None,
        requirements: Optional[List[str]] = None
    ) -> QualityAssessment:
        """Conduct comprehensive code review"""
        if not self.model:
            await self.initialize()
        
        context_str = json.dumps(context or {}, indent=2)
        requirements_str = "\n".join(requirements or ["General code review"])
        
        prompt = self.code_review_template.format(
            language=language,
            code=code,
            context=context_str,
            requirements=requirements_str
        )
        
        try:
            async for response in self.model.generate_async(
                prompt=prompt,
                max_tokens=2000,  # Comprehensive reviews need space
                temperature=0.2,  # Low temperature for consistent, thorough analysis
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
                    review_data = json.loads(json_text)
                    return self._create_quality_assessment(review_data)
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse code review JSON: {e}")
                    return self._create_fallback_assessment(code)
        
        except Exception as e:
            logger.error(f"Code review error: {e}")
            return self._create_fallback_assessment(code)
    
    async def generate_test_suite(
        self,
        code: str,
        language: str,
        test_types: List[str],
        coverage_target: int = 90,
        framework: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive test suites"""
        if not self.model:
            await self.initialize()
        
        test_types_str = ", ".join(test_types)
        context_str = json.dumps(context or {}, indent=2)
        framework = framework or "pytest" if "python" in language.lower() else "jest"
        
        prompt = self.test_generation_template.format(
            language=language,
            code=code,
            test_types=test_types_str,
            coverage_target=coverage_target,
            framework=framework,
            context=context_str
        )
        
        try:
            async for response in self.model.generate_async(
                prompt=prompt,
                max_tokens=2500,  # Comprehensive test suites need more tokens
                temperature=0.3,  # Slightly higher for creative test scenarios
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
                    return {"error": "Failed to parse test suite generation results"}
        
        except Exception as e:
            logger.error(f"Test generation error: {e}")
            return {"error": f"Test generation failed: {str(e)}"}
    
    async def validate_code_quality(
        self,
        code: str,
        language: str,
        quality_gates: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Validate code against quality gates"""
        if not self.model:
            await self.initialize()
        
        # Use provided quality gates or defaults
        gates = quality_gates or self.quality_standards
        
        validation_prompt = f"""You are validating {language} code against quality standards.

Code to Validate:
```{language}
{code}
```

Quality Gates:
{json.dumps(gates, indent=2)}

Provide detailed validation results in JSON format:

{{
    "validation_passed": true,
    "quality_score": 85,
    "gate_results": {{
        "code_coverage": {{"status": "passed", "actual": 92, "required": 80}},
        "complexity": {{"status": "passed", "actual": "low", "threshold": "medium"}},
        "security": {{"status": "failed", "critical_issues": 1, "threshold": 0}},
        "maintainability": {{"status": "passed", "score": 8, "threshold": 7}}
    }},
    "failed_gates": [
        {{
            "gate": "security",
            "reason": "1 critical security issue found",
            "required_action": "Fix critical security vulnerability before deployment"
        }}
    ],
    "recommendations": [
        "Address security vulnerability in line 42",
        "Consider refactoring complex function for better maintainability"
    ],
    "next_steps": [
        "Immediate: Fix security issue",
        "Short-term: Improve test coverage", 
        "Long-term: Refactor for better maintainability"
    ],
    "deployment_approval": false,
    "approval_blockers": ["Critical security issue"]
}}

Thoroughly validate against all quality standards."""
        
        try:
            async for response in self.model.generate_async(
                prompt=validation_prompt,
                max_tokens=1500,
                temperature=0.1,  # Very low temperature for consistent validation
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
                    return {"error": "Failed to parse validation results"}
        
        except Exception as e:
            logger.error(f"Quality validation error: {e}")
            return {"error": f"Quality validation failed: {str(e)}"}
    
    def _create_quality_assessment(self, data: Dict) -> QualityAssessment:
        """Create QualityAssessment from parsed review data"""
        try:
            return QualityAssessment(
                overall_quality=QualityLevel(data.get("overall_quality", "acceptable")),
                quality_score=data.get("quality_score", 5),
                issues_found=data.get("critical_issues", []),
                recommendations=data.get("refactoring_suggestions", []),
                test_coverage_assessment=data.get("test_coverage_assessment", {}),
                security_review=data.get("detailed_analysis", {}).get("security", {}),
                performance_analysis=data.get("detailed_analysis", {}).get("performance", {}),
                maintainability_score=data.get("detailed_analysis", {}).get("maintainability", {}).get("score", 5),
                automated_test_suggestions=data.get("automated_tests_needed", [])
            )
        except Exception as e:
            logger.error(f"Error creating quality assessment: {e}")
            return self._create_fallback_assessment("Unknown code")
    
    def _create_fallback_assessment(self, code: str) -> QualityAssessment:
        """Create fallback quality assessment"""
        return QualityAssessment(
            overall_quality=QualityLevel.NEEDS_IMPROVEMENT,
            quality_score=5,
            issues_found=[{
                "severity": "medium",
                "category": "analysis",
                "description": "Unable to perform automated review",
                "suggested_fix": "Manual review required"
            }],
            recommendations=["Conduct manual code review"],
            test_coverage_assessment={"status": "unknown", "recommendation": "Manual testing assessment needed"},
            security_review={"status": "unknown", "recommendation": "Manual security review needed"},
            performance_analysis={"status": "unknown", "recommendation": "Manual performance review needed"},
            maintainability_score=5,
            automated_test_suggestions=[{
                "test_type": "manual",
                "description": "Manual testing required",
                "priority": "high"
            }]
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for QA checker agent"""
        try:
            if not self.model:
                return {"status": "unhealthy", "reason": "Model not loaded"}
            
            # Quick QA test
            test_code = "def add(a, b): return a + b"
            assessment = await self.conduct_code_review(test_code, "python")
            
            return {
                "status": "healthy",
                "model_id": self.model_id,
                "model_loaded": self.model.is_loaded,
                "test_assessment": {
                    "overall_quality": assessment.overall_quality.value,
                    "quality_score": assessment.quality_score
                },
                "quality_standards": self.quality_standards
            }
            
        except Exception as e:
            return {"status": "unhealthy", "reason": str(e)}


# Global QA checker instance
qa_checker_agent: Optional[QACheckerAgent] = None


async def get_qa_checker_agent(model_path: str) -> QACheckerAgent:
    """Get or create QA checker agent instance"""
    global qa_checker_agent
    
    if qa_checker_agent is None:
        qa_checker_agent = QACheckerAgent(model_path)
        await qa_checker_agent.initialize()
    
    return qa_checker_agent