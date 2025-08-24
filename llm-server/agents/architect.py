"""
Architect Agent - High-level system design and planning using Qwen2.5-32B
Handles complex architectural decisions, project planning, and system design
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from ..configs.llama_cpp.optimized_llama import OptimizedLlama, MODEL_POOL


logger = logging.getLogger(__name__)


class ArchitecturalPattern(Enum):
    """Common architectural patterns"""
    MVC = "mvc"
    MVVM = "mvvm"
    MICROSERVICES = "microservices"
    LAYERED = "layered"
    HEXAGONAL = "hexagonal"
    EVENT_DRIVEN = "event_driven"
    PIPE_FILTER = "pipe_filter"
    REPOSITORY = "repository"
    SINGLETON = "singleton"
    FACTORY = "factory"


class ComplexityLevel(Enum):
    """Project complexity levels"""
    SIMPLE = 1
    MODERATE = 2
    COMPLEX = 3
    ENTERPRISE = 4


@dataclass
class ArchitecturalPlan:
    """Result of architectural analysis and planning"""
    project_type: str
    complexity_level: ComplexityLevel
    recommended_patterns: List[ArchitecturalPattern]
    technology_stack: Dict[str, List[str]]
    directory_structure: Dict[str, Any]
    implementation_phases: List[Dict[str, Any]]
    estimated_effort: str
    key_considerations: List[str]
    potential_challenges: List[str]
    success_metrics: List[str]


class ArchitectAgent:
    """High-capability architect for system design and planning"""
    
    def __init__(self, model_path: str):
        self.model_id = "architect"
        self.model_path = model_path
        self.model: Optional[OptimizedLlama] = None
        
        # Architecture analysis templates
        self.architecture_prompt_template = """You are a senior software architect with deep expertise in system design, scalability, and best practices. Analyze the project requirements and provide a comprehensive architectural plan.

Project Requirements:
{requirements}

Context:
{context}

Please provide a detailed architectural analysis in the following JSON format:

{{
    "project_type": "web_app|mobile_app|desktop_app|api_service|microservice|library|cli_tool|data_pipeline|ai_system",
    "complexity_level": "simple|moderate|complex|enterprise", 
    "recommended_patterns": ["pattern1", "pattern2"],
    "technology_stack": {{
        "backend": ["technology1", "technology2"],
        "frontend": ["technology1", "technology2"],
        "database": ["technology1", "technology2"],
        "infrastructure": ["technology1", "technology2"],
        "testing": ["technology1", "technology2"]
    }},
    "directory_structure": {{
        "root": ["dir1", "dir2"],
        "src": ["subdir1", "subdir2"],
        "tests": ["test_dir1", "test_dir2"]
    }},
    "implementation_phases": [
        {{
            "phase": 1,
            "name": "Foundation",
            "description": "Initial setup and core structure",
            "deliverables": ["item1", "item2"],
            "estimated_time": "1-2 weeks"
        }}
    ],
    "estimated_effort": "2-4 weeks|1-2 months|3-6 months|6+ months",
    "key_considerations": [
        "Scalability requirements",
        "Performance considerations", 
        "Security implications"
    ],
    "potential_challenges": [
        "Challenge 1 and mitigation strategy",
        "Challenge 2 and mitigation strategy"
    ],
    "success_metrics": [
        "Metric 1: Target value",
        "Metric 2: Target value"
    ]
}}

Focus on:
1. Appropriate architectural patterns for the use case
2. Technology choices that align with requirements
3. Scalable and maintainable design
4. Clear implementation roadmap
5. Risk identification and mitigation
6. Performance and security considerations

Provide thorough, actionable architectural guidance."""
    
        self.design_review_template = """You are conducting an architectural design review. Analyze the proposed design and provide expert feedback.

Proposed Design:
{design}

Context:
{context}

Provide a comprehensive review in JSON format:

{{
    "overall_assessment": "excellent|good|needs_improvement|poor",
    "strengths": [
        "Strength 1 with explanation",
        "Strength 2 with explanation"
    ],
    "weaknesses": [
        "Weakness 1 with specific improvement suggestion",
        "Weakness 2 with specific improvement suggestion"
    ],
    "recommendations": [
        "High priority recommendation 1",
        "Medium priority recommendation 2"
    ],
    "architectural_concerns": [
        "Scalability: Specific concern and solution",
        "Performance: Specific concern and solution"
    ],
    "security_review": [
        "Security consideration 1",
        "Security consideration 2"
    ],
    "maintainability_score": 8,
    "scalability_score": 7,
    "performance_score": 8,
    "security_score": 6,
    "next_steps": [
        "Immediate action 1",
        "Follow-up action 2"
    ]
}}

Be thorough, constructive, and specific in your feedback."""
    
    async def initialize(self):
        """Initialize the architect model"""
        logger.info(f"Initializing Architect agent with model: {self.model_path}")
        
        self.model = await MODEL_POOL.get_model(
            model_id=self.model_id,
            model_path=self.model_path,
            model_type="architect"
        )
        
        logger.info("Architect agent initialized successfully")
    
    async def create_architectural_plan(
        self, 
        requirements: str, 
        context: Optional[Dict] = None
    ) -> ArchitecturalPlan:
        """Create a comprehensive architectural plan"""
        if not self.model:
            await self.initialize()
        
        context_str = json.dumps(context or {}, indent=2)
        prompt = self.architecture_prompt_template.format(
            requirements=requirements,
            context=context_str
        )
        
        try:
            # Generate architectural analysis
            async for response in self.model.generate_async(
                prompt=prompt,
                max_tokens=2000,  # More tokens for detailed analysis
                temperature=0.3,  # Moderate temperature for creative but consistent solutions
                top_p=0.9,
                stop=["}\n\n", "\n\n#"]
            ):
                json_text = response.get("choices", [{}])[0].get("text", "").strip()
                
                # Clean and parse JSON
                if "{" in json_text:
                    json_start = json_text.find("{")
                    json_end = json_text.rfind("}") + 1
                    json_text = json_text[json_start:json_end]
                
                try:
                    plan_data = json.loads(json_text)
                    return self._create_architectural_plan(plan_data)
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse architectural plan JSON: {e}")
                    return self._create_fallback_plan(requirements)
        
        except Exception as e:
            logger.error(f"Architect error: {e}")
            return self._create_fallback_plan(requirements)
    
    async def review_design(
        self, 
        design: str, 
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Conduct architectural design review"""
        if not self.model:
            await self.initialize()
        
        context_str = json.dumps(context or {}, indent=2)
        prompt = self.design_review_template.format(
            design=design,
            context=context_str
        )
        
        try:
            async for response in self.model.generate_async(
                prompt=prompt,
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
            logger.error(f"Design review error: {e}")
            return self._create_fallback_review()
    
    async def optimize_for_scale(
        self, 
        current_design: str, 
        scale_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize architecture for scale requirements"""
        if not self.model:
            await self.initialize()
        
        scale_prompt = f"""As a senior architect, optimize this design for scale:

Current Design:
{current_design}

Scale Requirements:
- Expected users: {scale_requirements.get('users', 'Unknown')}
- Expected traffic: {scale_requirements.get('traffic', 'Unknown')}
- Data volume: {scale_requirements.get('data_volume', 'Unknown')}
- Geographic distribution: {scale_requirements.get('geographic', 'Unknown')}
- Performance targets: {scale_requirements.get('performance', 'Unknown')}

Provide optimization recommendations in JSON:

{{
    "scaling_strategy": "horizontal|vertical|hybrid",
    "bottleneck_analysis": [
        "Bottleneck 1: Solution",
        "Bottleneck 2: Solution"
    ],
    "infrastructure_changes": [
        "Load balancers: Configuration",
        "Caching: Strategy and tools",
        "Database: Scaling approach"
    ],
    "performance_optimizations": [
        "Optimization 1 with expected impact",
        "Optimization 2 with expected impact"
    ],
    "monitoring_strategy": [
        "Key metrics to track",
        "Alerting thresholds"
    ],
    "cost_considerations": [
        "Cost optimization 1",
        "Cost optimization 2"
    ],
    "implementation_priority": [
        "High: Critical changes",
        "Medium: Important improvements",
        "Low: Nice-to-have optimizations"
    ]
}}"""
        
        try:
            async for response in self.model.generate_async(
                prompt=scale_prompt,
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
                    return {"error": "Failed to parse scaling recommendations"}
        
        except Exception as e:
            logger.error(f"Scaling optimization error: {e}")
            return {"error": f"Scaling analysis failed: {str(e)}"}
    
    def _create_architectural_plan(self, data: Dict) -> ArchitecturalPlan:
        """Create ArchitecturalPlan from parsed data"""
        try:
            # Convert pattern strings to enums
            patterns = []
            for pattern in data.get("recommended_patterns", []):
                try:
                    patterns.append(ArchitecturalPattern(pattern.lower()))
                except ValueError:
                    logger.warning(f"Unknown architectural pattern: {pattern}")
            
            return ArchitecturalPlan(
                project_type=data.get("project_type", "web_app"),
                complexity_level=ComplexityLevel[data.get("complexity_level", "moderate").upper()],
                recommended_patterns=patterns,
                technology_stack=data.get("technology_stack", {}),
                directory_structure=data.get("directory_structure", {}),
                implementation_phases=data.get("implementation_phases", []),
                estimated_effort=data.get("estimated_effort", "Unknown"),
                key_considerations=data.get("key_considerations", []),
                potential_challenges=data.get("potential_challenges", []),
                success_metrics=data.get("success_metrics", [])
            )
        except Exception as e:
            logger.error(f"Error creating architectural plan: {e}")
            return self._create_fallback_plan("Unknown requirements")
    
    def _create_fallback_plan(self, requirements: str) -> ArchitecturalPlan:
        """Create a basic fallback plan when analysis fails"""
        return ArchitecturalPlan(
            project_type="web_app",
            complexity_level=ComplexityLevel.MODERATE,
            recommended_patterns=[ArchitecturalPattern.MVC, ArchitecturalPattern.LAYERED],
            technology_stack={
                "backend": ["Python", "FastAPI"],
                "frontend": ["React", "TypeScript"],
                "database": ["PostgreSQL"],
                "infrastructure": ["Docker"],
                "testing": ["pytest", "Jest"]
            },
            directory_structure={
                "root": ["src", "tests", "docs", "scripts"],
                "src": ["api", "models", "services", "utils"],
                "tests": ["unit", "integration", "e2e"]
            },
            implementation_phases=[
                {
                    "phase": 1,
                    "name": "Foundation",
                    "description": "Basic project setup and structure",
                    "deliverables": ["Project structure", "Basic API"],
                    "estimated_time": "1-2 weeks"
                }
            ],
            estimated_effort="2-4 weeks",
            key_considerations=["Maintainability", "Scalability", "Testing"],
            potential_challenges=["Requirements clarity", "Technology learning curve"],
            success_metrics=["Code coverage > 80%", "Response time < 200ms"]
        )
    
    def _create_fallback_review(self) -> Dict[str, Any]:
        """Create fallback design review"""
        return {
            "overall_assessment": "needs_review",
            "strengths": ["Structure appears logical"],
            "weaknesses": ["Unable to perform detailed analysis"],
            "recommendations": ["Manual review recommended"],
            "architectural_concerns": ["Analysis incomplete"],
            "security_review": ["Security review needed"],
            "maintainability_score": 5,
            "scalability_score": 5,
            "performance_score": 5,
            "security_score": 5,
            "next_steps": ["Conduct manual architectural review"]
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for architect agent"""
        try:
            if not self.model:
                return {"status": "unhealthy", "reason": "Model not loaded"}
            
            # Quick architecture test
            test_requirements = "Create a simple REST API for user management"
            plan = await self.create_architectural_plan(test_requirements)
            
            return {
                "status": "healthy",
                "model_id": self.model_id,
                "model_loaded": self.model.is_loaded,
                "test_plan": {
                    "project_type": plan.project_type,
                    "complexity": plan.complexity_level.name
                }
            }
            
        except Exception as e:
            return {"status": "unhealthy", "reason": str(e)}


# Global architect instance
architect_agent: Optional[ArchitectAgent] = None


async def get_architect_agent(model_path: str) -> ArchitectAgent:
    """Get or create architect agent instance"""
    global architect_agent
    
    if architect_agent is None:
        architect_agent = ArchitectAgent(model_path)
        await architect_agent.initialize()
    
    return architect_agent