"""
Primary Coder Agent - High-performance coding using Qwen2.5-Coder-7B
Leader in code generation with 88.4% HumanEval performance
Specializes in complex implementations and high-quality code generation
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any

from .base_coder import BaseCoderAgent, CodeRequest, CodeResponse, CodeLanguage, CodeTaskType


logger = logging.getLogger(__name__)


class PrimaryCoderAgent(BaseCoderAgent):
    """Primary coder agent using Qwen2.5-Coder-7B for high-performance code generation"""
    
    def __init__(self, model_path: str):
        super().__init__(
            model_path=model_path,
            model_type="coder_primary",
            agent_name="primary"
        )
        
        # Specialized prompts for high-performance code generation
        self.advanced_implementation_template = """You are the lead software engineer with expertise in {language} and modern development practices. You excel at creating production-ready, scalable, and maintainable code.

Advanced Implementation Task:
{description}

Technical Requirements:
{requirements}

Architecture Context:
{context}

{existing_code_section}

Create a comprehensive, production-ready solution in JSON format:

{{
    "generated_code": "// Complete, thoroughly tested implementation",
    "explanation": "Detailed technical explanation of design decisions and implementation strategy",
    "file_changes": [
        {{"file_path": "src/main.{ext}", "change_type": "create", "description": "Main implementation file"}},
        {{"file_path": "tests/test_main.{ext}", "change_type": "create", "description": "Comprehensive test suite"}}
    ],
    "dependencies": ["production-grade-library-1", "testing-framework"],
    "testing_notes": "Complete testing strategy including unit, integration, and edge case tests",
    "performance_notes": "Performance characteristics, benchmarks, and optimization opportunities",
    "security_considerations": "Comprehensive security analysis and implemented safeguards",
    "estimated_effort": "Detailed time breakdown for implementation, testing, and deployment",
    "api_documentation": "API documentation if applicable",
    "deployment_notes": "Production deployment considerations and requirements",
    "monitoring_suggestions": "Logging and monitoring recommendations"
}}

Excellence Standards:
1. Code that passes all linting and type checking
2. Comprehensive error handling and input validation
3. Performance optimized for production workloads
4. Security-first implementation with proper sanitization
5. Extensive documentation and type hints
6. Modular, testable architecture
7. Following language-specific best practices and idioms
8. Considering scalability and maintainability from the start

Generate code that exemplifies software engineering excellence."""
        
        # Specializations of the primary coder
        self.specializations = {
            "complex_algorithms": "Advanced algorithm implementation and optimization",
            "system_design": "Large-scale system architecture and implementation",
            "performance_critical": "High-performance code requiring optimization",
            "api_development": "RESTful and GraphQL API development",
            "data_processing": "ETL pipelines and data processing systems",
            "concurrent_programming": "Multi-threaded and async programming",
            "framework_integration": "Integration with complex frameworks and libraries",
            "production_deployment": "Production-ready code with proper error handling"
        }
    
    async def generate_advanced_implementation(
        self,
        description: str,
        language: CodeLanguage,
        requirements: List[str],
        context: Optional[Dict] = None,
        existing_code: Optional[str] = None
    ) -> CodeResponse:
        """Generate advanced, production-ready implementations"""
        if not self.model:
            await self.initialize()
        
        # Prepare advanced prompt
        lang_config = self.language_configs.get(language, {})
        ext = lang_config.get("extension", ".txt")[1:]  # Remove the dot
        
        context_str = ""
        if context:
            context_str = "\n".join(f"- {k}: {v}" for k, v in context.items())
        
        requirements_str = "\n".join(f"- {req}" for req in requirements)
        
        existing_code_section = ""
        if existing_code:
            existing_code_section = f"""
Existing Code to Enhance:
```{language.value}
{existing_code}
```"""
        
        prompt = self.advanced_implementation_template.format(
            language=language.value,
            description=description,
            requirements=requirements_str,
            context=context_str,
            existing_code_section=existing_code_section,
            ext=ext
        )
        
        try:
            # Use higher token limit and optimized parameters for complex tasks
            async for response in self.model.generate_async(
                prompt=prompt,
                max_tokens=2500,  # More tokens for comprehensive implementations
                temperature=0.2,  # Low temperature for reliable, production code
                top_p=0.9,
                top_k=40,
                repeat_penalty=1.1,
                stop=["}\n\n\n", "\n\n---"]
            ):
                json_text = response.get("choices", [{}])[0].get("text", "").strip()
                
                # Clean and parse JSON
                if "{" in json_text:
                    json_start = json_text.find("{")
                    json_end = json_text.rfind("}") + 1
                    json_text = json_text[json_start:json_end]
                
                try:
                    import json
                    code_data = json.loads(json_text)
                    return self._create_advanced_response(code_data, language)
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse advanced implementation JSON: {e}")
                    return self._create_fallback_response(
                        CodeRequest(
                            task_type=CodeTaskType.IMPLEMENTATION,
                            language=language,
                            description=description
                        )
                    )
        
        except Exception as e:
            logger.error(f"Advanced implementation error: {e}")
            return self._create_fallback_response(
                CodeRequest(
                    task_type=CodeTaskType.IMPLEMENTATION,
                    language=language,
                    description=description
                )
            )
    
    async def refactor_for_performance(
        self,
        code: str,
        language: CodeLanguage,
        performance_goals: List[str]
    ) -> Dict[str, Any]:
        """Specialized performance refactoring"""
        if not self.model:
            await self.initialize()
        
        goals_str = ", ".join(performance_goals)
        
        perf_prompt = f"""You are a performance optimization specialist working with {language.value} code.

Performance Goals: {goals_str}

Original Code:
```{language.value}
{code}
```

Provide comprehensive performance optimization in JSON format:

{{
    "optimized_code": "// Heavily optimized code with detailed comments explaining optimizations",
    "optimization_analysis": {{
        "algorithmic_improvements": ["O(n²) → O(n log n) sorting optimization", "Caching frequently computed values"],
        "memory_optimizations": ["Reduced memory allocations", "Better data structures"],
        "cpu_optimizations": ["Loop unrolling", "Vectorization opportunities"],
        "io_optimizations": ["Batch operations", "Async I/O usage"]
    }},
    "performance_benchmarks": {{
        "before": {{"execution_time": "100ms", "memory_usage": "50MB", "cpu_utilization": "80%"}},
        "after": {{"execution_time": "25ms", "memory_usage": "30MB", "cpu_utilization": "45%"}},
        "improvement_factor": {{"speed": "4x", "memory": "1.7x", "efficiency": "1.8x"}}
    }},
    "profiling_recommendations": [
        "Profile hotspots with tool X",
        "Monitor memory allocations with tool Y"
    ],
    "testing_strategy": "How to verify performance improvements without breaking functionality",
    "scalability_analysis": "How optimizations affect scaling characteristics",
    "maintenance_considerations": "Impact on code maintainability and readability"
}}

Focus on measurable performance improvements while maintaining code correctness."""
        
        try:
            async for response in self.model.generate_async(
                prompt=perf_prompt,
                max_tokens=2000,
                temperature=0.3,
                top_p=0.9
            ):
                json_text = response.get("choices", [{}])[0].get("text", "").strip()
                
                if "{" in json_text:
                    json_start = json_text.find("{")
                    json_end = json_text.rfind("}") + 1
                    json_text = json_text[json_start:json_end]
                
                try:
                    import json
                    return json.loads(json_text)
                except json.JSONDecodeError:
                    return {"error": "Failed to parse performance optimization results"}
        
        except Exception as e:
            logger.error(f"Performance refactoring error: {e}")
            return {"error": f"Performance optimization failed: {str(e)}"}
    
    async def generate_test_suite(
        self,
        code: str,
        language: CodeLanguage,
        test_requirements: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive test suites for code"""
        if not self.model:
            await self.initialize()
        
        test_req_str = ""
        if test_requirements:
            test_req_str = "\n".join(f"- {k}: {v}" for k, v in test_requirements.items())
        
        test_prompt = f"""You are a test automation expert creating comprehensive test suites for {language.value} code.

Code to Test:
```{language.value}
{code}
```

Test Requirements:
{test_req_str}

Generate a complete test strategy in JSON format:

{{
    "test_code": "// Complete test suite with unit, integration, and edge case tests",
    "test_structure": {{
        "unit_tests": ["test_function_1", "test_function_2"],
        "integration_tests": ["test_integration_1", "test_integration_2"],
        "edge_case_tests": ["test_edge_case_1", "test_edge_case_2"],
        "performance_tests": ["test_performance_1", "test_performance_2"]
    }},
    "coverage_analysis": {{
        "line_coverage": "95%",
        "branch_coverage": "90%",
        "function_coverage": "100%"
    }},
    "test_data": {{
        "fixtures": ["fixture_1.json", "fixture_2.json"],
        "mocks": ["mock_service_1", "mock_database"],
        "test_databases": ["test_db_setup.sql"]
    }},
    "testing_strategy": [
        "Test-driven development approach",
        "Property-based testing for complex algorithms",
        "Mutation testing for critical paths"
    ],
    "ci_cd_integration": [
        "Pre-commit hooks configuration",
        "CI pipeline test stages",
        "Coverage reporting setup"
    ],
    "maintenance_notes": "How to maintain and extend the test suite"
}}

Create tests that ensure reliability, catch regressions, and support refactoring."""
        
        try:
            async for response in self.model.generate_async(
                prompt=test_prompt,
                max_tokens=2000,
                temperature=0.3,
                top_p=0.9
            ):
                json_text = response.get("choices", [{}])[0].get("text", "").strip()
                
                if "{" in json_text:
                    json_start = json_text.find("{")
                    json_end = json_text.rfind("}") + 1
                    json_text = json_text[json_start:json_end]
                
                try:
                    import json
                    return json.loads(json_text)
                except json.JSONDecodeError:
                    return {"error": "Failed to parse test suite generation results"}
        
        except Exception as e:
            logger.error(f"Test suite generation error: {e}")
            return {"error": f"Test generation failed: {str(e)}"}
    
    def _create_advanced_response(self, data: Dict, language: CodeLanguage) -> CodeResponse:
        """Create enhanced CodeResponse with additional fields"""
        base_response = self._create_code_response(data, language)
        
        # Add advanced fields if available
        if "api_documentation" in data:
            base_response.explanation += f"\n\nAPI Documentation:\n{data['api_documentation']}"
        
        if "deployment_notes" in data:
            base_response.estimated_effort += f"\n\nDeployment Notes:\n{data['deployment_notes']}"
        
        if "monitoring_suggestions" in data:
            base_response.performance_notes += f"\n\nMonitoring:\n{data['monitoring_suggestions']}"
        
        return base_response
    
    async def get_specialization_info(self) -> Dict[str, Any]:
        """Get primary coder specialization information"""
        return {
            "agent_type": "primary_coder",
            "model": "Qwen2.5-Coder-7B",
            "performance_rating": "88.4% HumanEval",
            "specializations": self.specializations,
            "optimal_tasks": [
                "Complex algorithm implementation",
                "Production-ready system development",
                "Performance-critical applications",
                "API and service development",
                "Large-scale refactoring projects"
            ],
            "strengths": [
                "Highest code quality and correctness",
                "Excellent at complex problem solving",
                "Strong architectural awareness",
                "Comprehensive error handling",
                "Production-ready implementations"
            ]
        }


# Global primary coder instance
primary_coder_agent: Optional[PrimaryCoderAgent] = None


async def get_primary_coder_agent(model_path: str) -> PrimaryCoderAgent:
    """Get or create primary coder agent instance"""
    global primary_coder_agent
    
    if primary_coder_agent is None:
        primary_coder_agent = PrimaryCoderAgent(model_path)
        await primary_coder_agent.initialize()
    
    return primary_coder_agent