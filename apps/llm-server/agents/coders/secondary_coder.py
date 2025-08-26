"""
Secondary Coder Agent - Efficient coding using DeepSeek-Coder-V2-16B (MoE)
Backup specialist with MoE efficiency, excellent for parallel processing
Handles overflow work and specialized coding tasks
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any

from .base_coder import BaseCoderAgent, CodeRequest, CodeResponse, CodeLanguage, CodeTaskType


logger = logging.getLogger(__name__)


class SecondaryCoderAgent(BaseCoderAgent):
    """Secondary coder agent using DeepSeek-Coder-V2-16B MoE for efficient backup coding"""
    
    def __init__(self, model_path: str):
        super().__init__(
            model_path=model_path,
            model_type="coder_secondary",
            agent_name="secondary"
        )
        
        # Specialized prompts for efficient backup coding
        self.efficient_implementation_template = """You are an efficient software engineer specializing in {language} development. You excel at creating clean, functional code quickly while maintaining quality standards.

Implementation Task:
{description}

Requirements:
{requirements}

{existing_code_section}

Provide a practical, efficient solution in JSON format:

{{
    "generated_code": "// Clean, functional implementation with good practices",
    "explanation": "Clear explanation focusing on practical implementation approach",
    "file_changes": [
        {{"file_path": "path/to/file.{ext}", "change_type": "create|modify", "description": "What this change accomplishes"}}
    ],
    "dependencies": ["essential-library-1", "testing-tool"],
    "testing_notes": "Practical testing approach with key test cases",
    "performance_notes": "Performance characteristics and simple optimizations",
    "security_considerations": "Essential security practices applied",
    "estimated_effort": "Realistic time estimate for completion"
}}

Focus on:
1. Clean, readable, and maintainable code
2. Efficient implementation without over-engineering
3. Proper error handling for common scenarios
4. Good documentation and comments
5. Standard practices and conventions
6. Practical solutions that work reliably

Generate code that balances quality with development speed."""
        
        # MoE-optimized specializations (efficient in different domains)
        self.specializations = {
            "rapid_prototyping": "Quick prototype development and proof of concepts",
            "utility_functions": "Helper functions and utility libraries",
            "data_transformation": "Data processing and transformation scripts",
            "integration_code": "API integrations and service connections", 
            "automation_scripts": "Build automation and deployment scripts",
            "migration_helpers": "Database migrations and data migration tools",
            "testing_utilities": "Test helpers and testing infrastructure",
            "configuration_management": "Config parsers and environment setup",
            "backup_implementations": "Alternative implementations when primary fails",
            "parallel_development": "Working on different modules simultaneously"
        }
    
    async def generate_utility_code(
        self,
        description: str,
        language: CodeLanguage,
        utility_type: str,
        context: Optional[Dict] = None
    ) -> CodeResponse:
        """Generate utility functions and helper code efficiently"""
        if not self.model:
            await self.initialize()
        
        utility_prompt = f"""You are creating a {utility_type} utility in {language.value}.

Utility Description: {description}
Context: {context or {}}

Generate a practical utility implementation in JSON format:

{{
    "generated_code": "// Complete utility implementation with usage examples",
    "explanation": "How to use this utility and its key features",
    "file_changes": [
        {{"file_path": "utils/{utility_type}.{language.value}", "change_type": "create", "description": "Main utility file"}}
    ],
    "dependencies": ["minimal-required-deps"],
    "testing_notes": "Simple but effective tests for the utility",
    "performance_notes": "Performance characteristics and usage guidelines",
    "security_considerations": "Security aspects relevant to this utility",
    "estimated_effort": "Development and testing time",
    "usage_examples": [
        "Example 1: Basic usage",
        "Example 2: Advanced usage"
    ],
    "integration_notes": "How to integrate this utility into existing projects"
}}

Create a utility that is:
1. Easy to understand and use
2. Well documented with examples
3. Handles common edge cases
4. Follows standard patterns
5. Efficient and reliable"""
        
        try:
            async for response in self.model.generate_async(
                prompt=utility_prompt,
                max_tokens=1800,  # Efficient token usage
                temperature=0.4,  # Balanced creativity and consistency
                top_p=0.9,
                top_k=40,
                repeat_penalty=1.1
            ):
                json_text = response.get("choices", [{}])[0].get("text", "").strip()
                
                if "{" in json_text:
                    json_start = json_text.find("{")
                    json_end = json_text.rfind("}") + 1
                    json_text = json_text[json_start:json_end]
                
                try:
                    import json
                    code_data = json.loads(json_text)
                    return self._create_utility_response(code_data, language)
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse utility code JSON: {e}")
                    return self._create_fallback_response(
                        CodeRequest(
                            task_type=CodeTaskType.IMPLEMENTATION,
                            language=language,
                            description=description
                        )
                    )
        
        except Exception as e:
            logger.error(f"Utility code generation error: {e}")
            return self._create_fallback_response(
                CodeRequest(
                    task_type=CodeTaskType.IMPLEMENTATION,
                    language=language,
                    description=description
                )
            )
    
    async def generate_integration_code(
        self,
        service_name: str,
        integration_type: str,
        language: CodeLanguage,
        api_specs: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Generate service integration code efficiently"""
        if not self.model:
            await self.initialize()
        
        api_specs_str = ""
        if api_specs:
            api_specs_str = f"\nAPI Specifications:\n{json.dumps(api_specs, indent=2)}"
        
        integration_prompt = f"""You are creating a {integration_type} integration for {service_name} in {language.value}.

{api_specs_str}

Generate practical integration code in JSON format:

{{
    "integration_code": "// Complete integration implementation with error handling",
    "client_wrapper": "// Service client wrapper class/module",
    "configuration": "// Configuration management for the integration",
    "error_handling": "// Robust error handling and retry logic",
    "testing_code": "// Integration tests with mocking",
    "documentation": "// Usage documentation and examples",
    "dependencies": ["required-http-client", "config-library"],
    "setup_instructions": [
        "Step 1: Install dependencies",
        "Step 2: Configure credentials",
        "Step 3: Initialize client"
    ],
    "usage_examples": [
        "Basic usage example",
        "Error handling example",
        "Batch operations example"
    ],
    "monitoring_suggestions": [
        "Key metrics to monitor",
        "Alerting recommendations"
    ]
}}

Create an integration that is:
1. Robust and handles failures gracefully
2. Easy to configure and use
3. Well-tested and mockable
4. Follows service integration best practices
5. Includes proper logging and monitoring"""
        
        try:
            async for response in self.model.generate_async(
                prompt=integration_prompt,
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
                    return {"error": "Failed to parse integration code results"}
        
        except Exception as e:
            logger.error(f"Integration code generation error: {e}")
            return {"error": f"Integration generation failed: {str(e)}"}
    
    async def generate_migration_script(
        self,
        migration_type: str,
        source_info: Dict,
        target_info: Dict,
        language: CodeLanguage
    ) -> Dict[str, Any]:
        """Generate data migration and transformation scripts"""
        if not self.model:
            await self.initialize()
        
        migration_prompt = f"""You are creating a {migration_type} migration script in {language.value}.

Source: {json.dumps(source_info, indent=2)}
Target: {json.dumps(target_info, indent=2)}

Generate a comprehensive migration solution in JSON format:

{{
    "migration_script": "// Main migration script with transaction handling",
    "validation_script": "// Data validation and integrity checking",
    "rollback_script": "// Rollback procedure in case of issues",
    "transformation_logic": "// Data transformation and mapping logic",
    "batch_processing": "// Efficient batch processing for large datasets",
    "progress_tracking": "// Progress monitoring and logging",
    "error_recovery": "// Error handling and recovery procedures",
    "pre_migration_checks": [
        "Check 1: Source data validation",
        "Check 2: Target system readiness",
        "Check 3: Backup verification"
    ],
    "migration_steps": [
        "Step 1: Pre-migration setup",
        "Step 2: Data extraction",
        "Step 3: Data transformation",
        "Step 4: Data loading",
        "Step 5: Validation and cleanup"
    ],
    "testing_strategy": "How to test the migration safely",
    "performance_considerations": "Optimization for large-scale migrations",
    "monitoring_and_alerts": "What to monitor during migration"
}}

Create a migration that is:
1. Safe with proper backups and rollback
2. Efficient for large datasets
3. Well-monitored with progress tracking
4. Thoroughly validated
5. Resumable in case of interruption"""
        
        try:
            async for response in self.model.generate_async(
                prompt=migration_prompt,
                max_tokens=2000,
                temperature=0.2,  # Low temperature for reliable migration code
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
                    return {"error": "Failed to parse migration script results"}
        
        except Exception as e:
            logger.error(f"Migration script generation error: {e}")
            return {"error": f"Migration generation failed: {str(e)}"}
    
    def _create_utility_response(self, data: Dict, language: CodeLanguage) -> CodeResponse:
        """Create CodeResponse for utility functions"""
        base_response = self._create_code_response(data, language)
        
        # Add utility-specific information
        if "usage_examples" in data:
            base_response.explanation += f"\n\nUsage Examples:\n" + "\n".join(data["usage_examples"])
        
        if "integration_notes" in data:
            base_response.testing_notes += f"\n\nIntegration Notes:\n{data['integration_notes']}"
        
        return base_response
    
    async def handle_overflow_work(
        self,
        tasks: List[CodeRequest],
        priority_order: Optional[List[int]] = None
    ) -> List[CodeResponse]:
        """Handle multiple coding tasks efficiently (MoE advantage)"""
        if not self.model:
            await self.initialize()
        
        results = []
        task_order = priority_order if priority_order else list(range(len(tasks)))
        
        logger.info(f"Secondary coder handling {len(tasks)} overflow tasks")
        
        for i in task_order:
            if i < len(tasks):
                task = tasks[i]
                try:
                    result = await self.generate_code(task)
                    results.append(result)
                    logger.info(f"Completed overflow task {i+1}/{len(tasks)}")
                except Exception as e:
                    logger.error(f"Failed overflow task {i+1}: {e}")
                    results.append(self._create_fallback_response(task))
        
        return results
    
    async def get_specialization_info(self) -> Dict[str, Any]:
        """Get secondary coder specialization information"""
        return {
            "agent_type": "secondary_coder",
            "model": "DeepSeek-Coder-V2-16B (MoE)",
            "architecture": "Mixture of Experts",
            "efficiency": "High parallel processing capability",
            "specializations": self.specializations,
            "optimal_tasks": [
                "Rapid prototyping and utility development",
                "Service integrations and API clients",
                "Data migration and transformation scripts",
                "Automation and build tools",
                "Backup implementations and overflow work",
                "Parallel development on multiple modules"
            ],
            "strengths": [
                "Efficient resource usage with MoE",
                "Fast development cycles",
                "Good at practical implementations",
                "Handles multiple tasks simultaneously",
                "Strong in utility and integration code"
            ],
            "role": "Backup specialist and parallel processor"
        }


# Global secondary coder instance
secondary_coder_agent: Optional[SecondaryCoderAgent] = None


async def get_secondary_coder_agent(model_path: str) -> SecondaryCoderAgent:
    """Get or create secondary coder agent instance"""
    global secondary_coder_agent
    
    if secondary_coder_agent is None:
        secondary_coder_agent = SecondaryCoderAgent(model_path)
        await secondary_coder_agent.initialize()
    
    return secondary_coder_agent