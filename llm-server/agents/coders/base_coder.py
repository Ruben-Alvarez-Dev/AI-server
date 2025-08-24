"""
Base Coder Agent - Common functionality for all coding agents
Provides shared code generation, analysis, and refactoring capabilities
"""

import asyncio
import logging
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod

from ...configs.llama_cpp.optimized_llama import OptimizedLlama, MODEL_POOL


logger = logging.getLogger(__name__)


class CodeLanguage(Enum):
    """Supported programming languages"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CPP = "cpp"
    C = "c"
    RUST = "rust"
    GO = "go"
    SWIFT = "swift"
    KOTLIN = "kotlin"
    RUBY = "ruby"
    PHP = "php"
    CSHARP = "csharp"
    SQL = "sql"
    HTML = "html"
    CSS = "css"
    SHELL = "shell"
    YAML = "yaml"
    JSON = "json"
    DOCKERFILE = "dockerfile"


class CodeTaskType(Enum):
    """Types of coding tasks"""
    IMPLEMENTATION = "implementation"
    REFACTORING = "refactoring"
    OPTIMIZATION = "optimization"
    BUG_FIX = "bug_fix"
    FEATURE_ADD = "feature_add"
    CODE_REVIEW = "code_review"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    MIGRATION = "migration"


@dataclass
class CodeRequest:
    """Request for code generation or modification"""
    task_type: CodeTaskType
    language: CodeLanguage
    description: str
    existing_code: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    constraints: Optional[List[str]] = None
    quality_requirements: Optional[Dict[str, Any]] = None


@dataclass
class CodeResponse:
    """Response from code generation"""
    generated_code: str
    language: CodeLanguage
    explanation: str
    file_changes: List[Dict[str, Any]]
    dependencies: List[str]
    testing_notes: str
    performance_notes: str
    security_considerations: str
    estimated_effort: str


class BaseCoderAgent(ABC):
    """Base class for all coder agents"""
    
    def __init__(self, model_path: str, model_type: str, agent_name: str):
        self.model_path = model_path
        self.model_type = model_type
        self.agent_name = agent_name
        self.model_id = f"coder_{agent_name}"
        self.model: Optional[OptimizedLlama] = None
        
        # Language-specific templates and configurations
        self.language_configs = {
            CodeLanguage.PYTHON: {
                "extension": ".py",
                "comment_style": "#",
                "indent": "    ",
                "framework_suggestions": ["FastAPI", "Django", "Flask"],
                "quality_tools": ["black", "flake8", "mypy", "pytest"]
            },
            CodeLanguage.JAVASCRIPT: {
                "extension": ".js",
                "comment_style": "//",
                "indent": "  ",
                "framework_suggestions": ["React", "Vue", "Node.js"],
                "quality_tools": ["eslint", "prettier", "jest"]
            },
            CodeLanguage.TYPESCRIPT: {
                "extension": ".ts",
                "comment_style": "//",
                "indent": "  ",
                "framework_suggestions": ["React", "Vue", "NestJS"],
                "quality_tools": ["eslint", "prettier", "jest", "tsc"]
            },
            CodeLanguage.RUST: {
                "extension": ".rs",
                "comment_style": "//",
                "indent": "    ",
                "framework_suggestions": ["tokio", "actix-web", "serde"],
                "quality_tools": ["cargo fmt", "cargo clippy", "cargo test"]
            },
            CodeLanguage.GO: {
                "extension": ".go",
                "comment_style": "//",
                "indent": "\t",
                "framework_suggestions": ["gin", "echo", "fiber"],
                "quality_tools": ["gofmt", "golint", "go test"]
            }
        }
        
        self.code_generation_template = """You are an expert {language} developer. {context}

Task: {task_description}

Requirements:
{requirements}

{existing_code_section}

Please provide a comprehensive solution in the following JSON format:

{{
    "generated_code": "// Your complete, production-ready code here",
    "explanation": "Clear explanation of the implementation approach and key decisions",
    "file_changes": [
        {{"file_path": "path/to/file.ext", "change_type": "create|modify|delete", "description": "What this change does"}}
    ],
    "dependencies": ["dependency1", "dependency2"],
    "testing_notes": "How to test this code and what test cases to consider",
    "performance_notes": "Performance characteristics and optimization opportunities",
    "security_considerations": "Security implications and best practices applied",
    "estimated_effort": "Time estimate for implementation and testing"
}}

Focus on:
1. Clean, maintainable, and well-documented code
2. Following language-specific best practices and idioms
3. Error handling and edge cases
4. Performance and security considerations
5. Testability and modularity
6. Code that integrates well with existing systems

Generate production-quality code that follows industry standards."""
    
    async def initialize(self):
        """Initialize the coder model"""
        logger.info(f"Initializing {self.agent_name} coder with model: {self.model_path}")
        
        self.model = await MODEL_POOL.get_model(
            model_id=self.model_id,
            model_path=self.model_path,
            model_type=self.model_type
        )
        
        logger.info(f"{self.agent_name} coder initialized successfully")
    
    async def generate_code(self, request: CodeRequest) -> CodeResponse:
        """Generate code based on the request"""
        if not self.model:
            await self.initialize()
        
        # Prepare the prompt
        prompt = self._prepare_generation_prompt(request)
        
        try:
            # Generate code with appropriate parameters for coding tasks
            async for response in self.model.generate_async(
                prompt=prompt,
                max_tokens=2000,  # More tokens for complete implementations
                temperature=0.3,  # Low temperature for consistent, reliable code
                top_p=0.9,
                top_k=40,
                repeat_penalty=1.1,
                stop=["}\n\n\n", "\n\n---", "\n\nHuman:"]
            ):
                json_text = response.get("choices", [{}])[0].get("text", "").strip()
                
                # Clean and parse JSON
                if "{" in json_text:
                    json_start = json_text.find("{")
                    json_end = json_text.rfind("}") + 1
                    json_text = json_text[json_start:json_end]
                
                try:
                    code_data = json.loads(json_text)
                    return self._create_code_response(code_data, request.language)
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse code generation JSON: {e}")
                    return self._create_fallback_response(request)
        
        except Exception as e:
            logger.error(f"Code generation error: {e}")
            return self._create_fallback_response(request)
    
    async def review_code(self, code: str, language: CodeLanguage, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Review existing code for quality, security, and performance"""
        if not self.model:
            await self.initialize()
        
        review_prompt = f"""You are conducting a comprehensive code review for {language.value} code.

Code to Review:
```{language.value}
{code}
```

Context: {json.dumps(context or {}, indent=2)}

Provide a detailed code review in JSON format:

{{
    "overall_quality": "excellent|good|fair|poor",
    "quality_score": 8,
    "issues": [
        {{
            "severity": "critical|high|medium|low",
            "category": "bug|performance|security|style|maintainability",
            "description": "Issue description",
            "line_number": 42,
            "suggestion": "Specific fix recommendation"
        }}
    ],
    "strengths": [
        "Strength 1 with explanation",
        "Strength 2 with explanation"
    ],
    "improvements": [
        "Improvement 1 with specific guidance",
        "Improvement 2 with specific guidance"
    ],
    "security_analysis": [
        "Security consideration 1",
        "Security consideration 2"
    ],
    "performance_analysis": [
        "Performance aspect 1",
        "Performance aspect 2"
    ],
    "maintainability_score": 7,
    "readability_score": 8,
    "test_coverage_assessment": "Good test coverage needed for edge cases",
    "refactoring_suggestions": [
        "Refactoring suggestion 1",
        "Refactoring suggestion 2"
    ]
}}

Be thorough, constructive, and specific in your feedback."""
        
        try:
            async for response in self.model.generate_async(
                prompt=review_prompt,
                max_tokens=1500,
                temperature=0.2,  # Lower temperature for consistent reviews
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
                    return self._create_fallback_review()
        
        except Exception as e:
            logger.error(f"Code review error: {e}")
            return self._create_fallback_review()
    
    async def optimize_code(self, code: str, language: CodeLanguage, optimization_goals: List[str]) -> Dict[str, Any]:
        """Optimize code for specific goals (performance, memory, readability, etc.)"""
        if not self.model:
            await self.initialize()
        
        goals_str = ", ".join(optimization_goals)
        
        optimize_prompt = f"""You are optimizing {language.value} code for: {goals_str}

Original Code:
```{language.value}
{code}
```

Provide optimized code and analysis in JSON format:

{{
    "optimized_code": "// Your optimized code here",
    "optimization_summary": "Summary of optimizations applied",
    "performance_improvements": [
        "Improvement 1 with expected impact",
        "Improvement 2 with expected impact"
    ],
    "trade_offs": [
        "Trade-off 1: benefit vs cost",
        "Trade-off 2: benefit vs cost"
    ],
    "before_after_metrics": {{
        "complexity": {{"before": "O(n²)", "after": "O(n log n)"}},
        "memory": {{"before": "High", "after": "Moderate"}},
        "readability": {{"before": 7, "after": 8}}
    }},
    "testing_impact": "How optimization affects testing strategy",
    "deployment_considerations": "What to consider when deploying optimized code"
}}

Focus on the requested optimization goals while maintaining code correctness and readability."""
        
        try:
            async for response in self.model.generate_async(
                prompt=optimize_prompt,
                max_tokens=1500,
                temperature=0.3,
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
                    return {"error": "Failed to parse optimization results"}
        
        except Exception as e:
            logger.error(f"Code optimization error: {e}")
            return {"error": f"Optimization failed: {str(e)}"}
    
    def _prepare_generation_prompt(self, request: CodeRequest) -> str:
        """Prepare the code generation prompt"""
        context_str = "You are a senior software engineer."
        if request.context:
            context_str += f" Context: {json.dumps(request.context, indent=2)}"
        
        requirements = [request.description]
        if request.constraints:
            requirements.extend(f"Constraint: {c}" for c in request.constraints)
        if request.quality_requirements:
            requirements.extend(f"Quality: {k} = {v}" for k, v in request.quality_requirements.items())
        
        requirements_str = "\n".join(f"- {req}" for req in requirements)
        
        existing_code_section = ""
        if request.existing_code:
            existing_code_section = f"""
Existing Code to Modify:
```{request.language.value}
{request.existing_code}
```"""
        
        return self.code_generation_template.format(
            language=request.language.value,
            context=context_str,
            task_description=request.task_type.value,
            requirements=requirements_str,
            existing_code_section=existing_code_section
        )
    
    def _create_code_response(self, data: Dict, language: CodeLanguage) -> CodeResponse:
        """Create CodeResponse from parsed data"""
        return CodeResponse(
            generated_code=data.get("generated_code", "// Code generation failed"),
            language=language,
            explanation=data.get("explanation", "No explanation provided"),
            file_changes=data.get("file_changes", []),
            dependencies=data.get("dependencies", []),
            testing_notes=data.get("testing_notes", "No testing notes"),
            performance_notes=data.get("performance_notes", "No performance notes"),
            security_considerations=data.get("security_considerations", "No security notes"),
            estimated_effort=data.get("estimated_effort", "Unknown")
        )
    
    def _create_fallback_response(self, request: CodeRequest) -> CodeResponse:
        """Create fallback response when generation fails"""
        return CodeResponse(
            generated_code=f"// TODO: Implement {request.description}\n// Code generation failed, manual implementation required",
            language=request.language,
            explanation="Code generation failed, fallback response provided",
            file_changes=[],
            dependencies=[],
            testing_notes="Manual testing required",
            performance_notes="Performance analysis needed",
            security_considerations="Security review required",
            estimated_effort="Manual estimation needed"
        )
    
    def _create_fallback_review(self) -> Dict[str, Any]:
        """Create fallback code review"""
        return {
            "overall_quality": "needs_review",
            "quality_score": 5,
            "issues": [],
            "strengths": ["Code structure appears logical"],
            "improvements": ["Manual review recommended"],
            "security_analysis": ["Manual security review needed"],
            "performance_analysis": ["Manual performance review needed"],
            "maintainability_score": 5,
            "readability_score": 5,
            "test_coverage_assessment": "Test coverage assessment needed",
            "refactoring_suggestions": ["Manual refactoring analysis recommended"]
        }
    
    @abstractmethod
    async def get_specialization_info(self) -> Dict[str, Any]:
        """Get information about this coder's specializations"""
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for coder agent"""
        try:
            if not self.model:
                return {"status": "unhealthy", "reason": "Model not loaded"}
            
            # Quick test
            test_request = CodeRequest(
                task_type=CodeTaskType.IMPLEMENTATION,
                language=CodeLanguage.PYTHON,
                description="Create a simple hello world function"
            )
            
            response = await self.generate_code(test_request)
            
            return {
                "status": "healthy",
                "agent_name": self.agent_name,
                "model_id": self.model_id,
                "model_loaded": self.model.is_loaded,
                "test_generation": {
                    "language": response.language.value,
                    "code_length": len(response.generated_code)
                },
                "specialization": await self.get_specialization_info()
            }
            
        except Exception as e:
            return {"status": "unhealthy", "reason": str(e)}