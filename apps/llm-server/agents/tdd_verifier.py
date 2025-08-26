"""
TDD Verifier Agent - Test-Driven Development and Quality Assurance
Ensures code quality through comprehensive testing and verification
"""

import asyncio
import logging
import time
import uuid
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import subprocess
import tempfile
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class TestResult(Enum):
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"

class TestType(Enum):
    UNIT = "unit"
    INTEGRATION = "integration"
    END_TO_END = "e2e"
    PERFORMANCE = "performance"
    SECURITY = "security"

@dataclass
class TestCase:
    """Individual test case with results"""
    id: str
    name: str
    test_type: TestType
    description: str
    code: str
    expected_outcome: str
    actual_outcome: str = ""
    result: TestResult = TestResult.SKIPPED
    execution_time: float = 0.0
    error_message: str = ""
    coverage_impact: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'test_type': self.test_type.value,
            'description': self.description,
            'expected_outcome': self.expected_outcome,
            'actual_outcome': self.actual_outcome,
            'result': self.result.value,
            'execution_time': self.execution_time,
            'error_message': self.error_message,
            'coverage_impact': self.coverage_impact
        }

@dataclass
class CodeVerificationResult:
    """Complete verification result for a code submission"""
    submission_id: str
    coder_name: str
    task_id: str
    code_files: List[str]
    test_results: List[TestCase] = field(default_factory=list)
    coverage_percentage: float = 0.0
    quality_score: float = 0.0
    security_score: float = 0.0
    performance_score: float = 0.0
    overall_score: float = 0.0
    passed: bool = False
    feedback: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    verification_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'submission_id': self.submission_id,
            'coder_name': self.coder_name,
            'task_id': self.task_id,
            'code_files': self.code_files,
            'test_results': [test.to_dict() for test in self.test_results],
            'coverage_percentage': self.coverage_percentage,
            'quality_score': self.quality_score,
            'security_score': self.security_score,
            'performance_score': self.performance_score,
            'overall_score': self.overall_score,
            'passed': self.passed,
            'feedback': self.feedback,
            'suggestions': self.suggestions,
            'verification_time': self.verification_time
        }

class TDDVerifier:
    """
    Test-Driven Development Verifier
    
    Responsibilities:
    - Generate comprehensive test cases before coding
    - Execute unit, integration, and e2e tests
    - Measure code coverage
    - Perform security and performance analysis
    - Provide detailed feedback and suggestions
    - Ensure TDD compliance
    """
    
    def __init__(self, qa_model, test_frameworks_config: Dict[str, Any] = None):
        self.qa_model = qa_model
        self.test_frameworks = test_frameworks_config or self._default_test_frameworks()
        
        # Test generation templates
        self.test_generation_prompts = {
            'unit_tests': """
            Generate comprehensive unit tests for this code using TDD principles:

            Code Description: {code_description}
            Programming Language: {language}
            Framework: {framework}
            Function/Class: {target_element}

            Generate tests that:
            1. Test happy path scenarios
            2. Test edge cases and error conditions
            3. Test boundary values
            4. Validate input/output contracts
            5. Check error handling

            Use {test_framework} framework and follow TDD best practices.
            Include setup, execution, and assertion phases clearly.
            """,

            'integration_tests': """
            Create integration tests for these components:

            Components: {components}
            Integration Points: {integration_points}
            Dependencies: {dependencies}

            Generate tests that verify:
            1. Component interactions work correctly
            2. Data flows properly between components
            3. API contracts are maintained
            4. Error propagation is handled
            5. Performance under load

            Focus on real-world usage scenarios.
            """,

            'security_tests': """
            Generate security-focused tests for:

            Code: {code_description}
            Security Concerns: {security_risks}

            Create tests for:
            1. Input validation and sanitization
            2. Authentication and authorization
            3. SQL injection prevention
            4. XSS prevention
            5. Data encryption/decryption
            6. Rate limiting
            7. Access control

            Use security testing best practices.
            """,

            'performance_tests': """
            Create performance tests for:

            Code: {code_description}
            Expected Load: {expected_load}
            Performance Targets: {performance_targets}

            Generate tests that measure:
            1. Response time under normal load
            2. Throughput capacity
            3. Memory usage patterns
            4. CPU utilization
            5. Database query performance
            6. Concurrent user handling

            Include realistic load scenarios and benchmarks.
            """
        }
        
        # Code quality analysis prompts
        self.quality_analysis_prompts = {
            'code_review': """
            Perform a comprehensive code review:

            Code: {code_content}
            Language: {language}
            Context: {context}

            Analyze:
            1. Code correctness and logic
            2. Best practices adherence
            3. Performance implications
            4. Security vulnerabilities
            5. Maintainability and readability
            6. Test coverage adequacy

            Provide specific, actionable feedback with severity levels.
            """,

            'architecture_review': """
            Review the architectural aspects of this code:

            Code: {code_content}
            Architecture Pattern: {pattern}
            Integration Context: {context}

            Evaluate:
            1. Architectural consistency
            2. Separation of concerns
            3. Coupling and cohesion
            4. Scalability considerations
            5. Error handling strategy
            6. Logging and monitoring

            Suggest improvements for better architecture.
            """
        }
        
        # Statistics and metrics
        self.verification_stats = {
            'total_verifications': 0,
            'passed_verifications': 0,
            'average_coverage': 0.0,
            'average_quality_score': 0.0,
            'common_issues': {},
            'framework_usage': {}
        }
        
        # Create temp directory for test execution
        self.temp_dir = Path(tempfile.mkdtemp(prefix="tdd_verifier_"))
        
        logger.info("TDDVerifier initialized for comprehensive code verification")
    
    async def verify_code_submission(
        self,
        submission_id: str,
        coder_name: str,
        task_id: str,
        code_files: Dict[str, str],  # filename -> content
        test_requirements: List[Dict[str, Any]],
        language: str = "python"
    ) -> CodeVerificationResult:
        """
        Complete verification of a code submission with TDD approach
        """
        start_time = time.time()
        
        logger.info(f"Starting TDD verification for submission {submission_id} by {coder_name}")
        
        result = CodeVerificationResult(
            submission_id=submission_id,
            coder_name=coder_name,
            task_id=task_id,
            code_files=list(code_files.keys())
        )
        
        try:
            # Step 1: Pre-code test generation (TDD Red phase)
            generated_tests = await self._generate_comprehensive_tests(
                code_files, test_requirements, language
            )
            
            # Step 2: Execute tests against code (TDD Green phase)
            test_results = await self._execute_test_suite(
                code_files, generated_tests, language
            )
            result.test_results = test_results
            
            # Step 3: Measure code coverage
            result.coverage_percentage = await self._measure_code_coverage(
                code_files, generated_tests, language
            )
            
            # Step 4: Quality analysis
            result.quality_score = await self._analyze_code_quality(
                code_files, language
            )
            
            # Step 5: Security analysis
            result.security_score = await self._analyze_security(
                code_files, language
            )
            
            # Step 6: Performance analysis
            result.performance_score = await self._analyze_performance(
                code_files, test_results, language
            )
            
            # Step 7: Calculate overall score and pass/fail
            result.overall_score = self._calculate_overall_score(result)
            result.passed = self._determine_pass_fail(result)
            
            # Step 8: Generate feedback and suggestions
            result.feedback = await self._generate_feedback(result, code_files)
            result.suggestions = await self._generate_suggestions(result, code_files)
            
            # Update statistics
            verification_time = time.time() - start_time
            result.verification_time = verification_time
            self._update_stats(result)
            
            logger.info(f"TDD verification completed: {submission_id} - {'PASSED' if result.passed else 'FAILED'} ({verification_time:.2f}s)")
            
            return result
            
        except Exception as e:
            logger.error(f"TDD verification failed for {submission_id}: {e}")
            result.feedback.append(f"Verification error: {str(e)}")
            result.overall_score = 0.0
            result.passed = False
            return result
    
    async def _generate_comprehensive_tests(
        self,
        code_files: Dict[str, str],
        test_requirements: List[Dict[str, Any]],
        language: str
    ) -> List[TestCase]:
        """Generate comprehensive test suite using TDD principles"""
        
        all_tests = []
        
        # Analyze code to understand structure
        code_analysis = await self._analyze_code_structure(code_files, language)
        
        # Generate unit tests
        unit_tests = await self._generate_unit_tests(
            code_files, code_analysis, language
        )
        all_tests.extend(unit_tests)
        
        # Generate integration tests
        if len(code_files) > 1:
            integration_tests = await self._generate_integration_tests(
                code_files, code_analysis, language
            )
            all_tests.extend(integration_tests)
        
        # Generate security tests
        security_tests = await self._generate_security_tests(
            code_files, code_analysis, language
        )
        all_tests.extend(security_tests)
        
        # Generate performance tests
        performance_tests = await self._generate_performance_tests(
            code_files, code_analysis, language
        )
        all_tests.extend(performance_tests)
        
        logger.info(f"Generated {len(all_tests)} comprehensive tests")
        
        return all_tests
    
    async def _generate_unit_tests(
        self,
        code_files: Dict[str, str],
        code_analysis: Dict[str, Any],
        language: str
    ) -> List[TestCase]:
        """Generate unit tests for individual functions/methods"""
        
        unit_tests = []
        
        for filename, content in code_files.items():
            # Extract functions/classes to test
            testable_elements = code_analysis.get('testable_elements', {}).get(filename, [])
            
            for element in testable_elements:
                prompt = self.test_generation_prompts['unit_tests'].format(
                    code_description=f"File: {filename}, Element: {element['name']}",
                    language=language,
                    framework=self.test_frameworks[language]['unit'],
                    target_element=element['name'],
                    test_framework=self.test_frameworks[language]['unit']
                )
                
                try:
                    test_code = await self._query_qa_model(prompt)
                    
                    test_case = TestCase(
                        id=str(uuid.uuid4())[:8],
                        name=f"Unit test for {element['name']}",
                        test_type=TestType.UNIT,
                        description=f"Test functionality of {element['name']}",
                        code=test_code,
                        expected_outcome="All assertions pass"
                    )
                    
                    unit_tests.append(test_case)
                    
                except Exception as e:
                    logger.error(f"Failed to generate unit test for {element['name']}: {e}")
        
        return unit_tests
    
    async def _generate_integration_tests(
        self,
        code_files: Dict[str, str],
        code_analysis: Dict[str, Any],
        language: str
    ) -> List[TestCase]:
        """Generate integration tests for component interactions"""
        
        integration_tests = []
        
        # Identify integration points
        integration_points = code_analysis.get('integration_points', [])
        
        if integration_points:
            prompt = self.test_generation_prompts['integration_tests'].format(
                components=', '.join(code_files.keys()),
                integration_points=', '.join(integration_points),
                dependencies=code_analysis.get('dependencies', [])
            )
            
            try:
                test_code = await self._query_qa_model(prompt)
                
                test_case = TestCase(
                    id=str(uuid.uuid4())[:8],
                    name="Integration test suite",
                    test_type=TestType.INTEGRATION,
                    description="Test component interactions and data flow",
                    code=test_code,
                    expected_outcome="All integration points work correctly"
                )
                
                integration_tests.append(test_case)
                
            except Exception as e:
                logger.error(f"Failed to generate integration tests: {e}")
        
        return integration_tests
    
    async def _generate_security_tests(
        self,
        code_files: Dict[str, str],
        code_analysis: Dict[str, Any],
        language: str
    ) -> List[TestCase]:
        """Generate security-focused tests"""
        
        security_tests = []
        
        security_risks = code_analysis.get('security_risks', [
            'input_validation', 'authentication', 'authorization'
        ])
        
        prompt = self.test_generation_prompts['security_tests'].format(
            code_description=f"Files: {', '.join(code_files.keys())}",
            security_risks=', '.join(security_risks)
        )
        
        try:
            test_code = await self._query_qa_model(prompt)
            
            test_case = TestCase(
                id=str(uuid.uuid4())[:8],
                name="Security test suite",
                test_type=TestType.SECURITY,
                description="Test security vulnerabilities and protections",
                code=test_code,
                expected_outcome="No security vulnerabilities found"
            )
            
            security_tests.append(test_case)
            
        except Exception as e:
            logger.error(f"Failed to generate security tests: {e}")
        
        return security_tests
    
    async def _generate_performance_tests(
        self,
        code_files: Dict[str, str],
        code_analysis: Dict[str, Any],
        language: str
    ) -> List[TestCase]:
        """Generate performance tests"""
        
        performance_tests = []
        
        performance_targets = code_analysis.get('performance_targets', {
            'response_time': '< 100ms',
            'memory_usage': '< 100MB',
            'cpu_usage': '< 80%'
        })
        
        prompt = self.test_generation_prompts['performance_tests'].format(
            code_description=f"Files: {', '.join(code_files.keys())}",
            expected_load="moderate",
            performance_targets=json.dumps(performance_targets)
        )
        
        try:
            test_code = await self._query_qa_model(prompt)
            
            test_case = TestCase(
                id=str(uuid.uuid4())[:8],
                name="Performance test suite",
                test_type=TestType.PERFORMANCE,
                description="Test performance under various conditions",
                code=test_code,
                expected_outcome="Performance targets met"
            )
            
            performance_tests.append(test_case)
            
        except Exception as e:
            logger.error(f"Failed to generate performance tests: {e}")
        
        return performance_tests
    
    async def _execute_test_suite(
        self,
        code_files: Dict[str, str],
        test_cases: List[TestCase],
        language: str
    ) -> List[TestCase]:
        """Execute all test cases and record results"""
        
        logger.info(f"Executing {len(test_cases)} test cases")
        
        # Create temporary project structure
        project_dir = self.temp_dir / f"project_{int(time.time())}"
        project_dir.mkdir(exist_ok=True)
        
        try:
            # Write code files to disk
            for filename, content in code_files.items():
                file_path = project_dir / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content)
            
            # Execute each test case
            for test_case in test_cases:
                await self._execute_single_test(test_case, project_dir, language)
            
            return test_cases
            
        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            return test_cases
        finally:
            # Cleanup
            import shutil
            try:
                shutil.rmtree(project_dir)
            except:
                pass
    
    async def _execute_single_test(
        self,
        test_case: TestCase,
        project_dir: Path,
        language: str
    ):
        """Execute a single test case"""
        
        start_time = time.time()
        
        try:
            # Write test file
            test_file = project_dir / f"test_{test_case.id}.py"  # Assuming Python for now
            test_file.write_text(test_case.code)
            
            # Run test based on language
            if language == "python":
                cmd = ["python", "-m", "pytest", str(test_file), "-v"]
            elif language == "javascript":
                cmd = ["npm", "test"]
            else:
                # Fallback
                cmd = ["echo", "Test framework not implemented"]
            
            # Execute test
            result = subprocess.run(
                cmd,
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            execution_time = time.time() - start_time
            test_case.execution_time = execution_time
            
            if result.returncode == 0:
                test_case.result = TestResult.PASSED
                test_case.actual_outcome = "Test passed successfully"
            else:
                test_case.result = TestResult.FAILED
                test_case.actual_outcome = result.stdout + result.stderr
                test_case.error_message = result.stderr
            
        except subprocess.TimeoutExpired:
            test_case.result = TestResult.ERROR
            test_case.error_message = "Test execution timeout"
        except Exception as e:
            test_case.result = TestResult.ERROR
            test_case.error_message = str(e)
    
    async def _measure_code_coverage(
        self,
        code_files: Dict[str, str],
        test_cases: List[TestCase],
        language: str
    ) -> float:
        """Measure code coverage from test execution"""
        
        # Simplified coverage calculation
        # In production, use actual coverage tools like pytest-cov
        
        passed_tests = sum(1 for test in test_cases if test.result == TestResult.PASSED)
        total_tests = len(test_cases)
        
        if total_tests == 0:
            return 0.0
        
        # Basic coverage estimation
        coverage = (passed_tests / total_tests) * 100
        
        return min(coverage, 100.0)
    
    async def _analyze_code_quality(
        self,
        code_files: Dict[str, str],
        language: str
    ) -> float:
        """Analyze overall code quality"""
        
        quality_scores = []
        
        for filename, content in code_files.items():
            prompt = self.quality_analysis_prompts['code_review'].format(
                code_content=content[:2000],  # Limit for prompt
                language=language,
                context=f"File: {filename}"
            )
            
            try:
                analysis = await self._query_qa_model(prompt)
                score = self._extract_quality_score_from_analysis(analysis)
                quality_scores.append(score)
                
            except Exception as e:
                logger.error(f"Quality analysis failed for {filename}: {e}")
                quality_scores.append(0.5)  # Default score
        
        return sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
    
    async def _analyze_security(
        self,
        code_files: Dict[str, str],
        language: str
    ) -> float:
        """Analyze security aspects of the code"""
        
        # Simple security score based on common patterns
        security_score = 0.8  # Base score
        
        for filename, content in code_files.items():
            content_lower = content.lower()
            
            # Check for security anti-patterns
            if 'password' in content_lower and 'plain' in content_lower:
                security_score -= 0.2
            if 'sql' in content_lower and '+' in content:
                security_score -= 0.3  # Potential SQL injection
            if 'eval(' in content:
                security_score -= 0.4  # Code injection risk
            
            # Check for security good practices
            if 'bcrypt' in content_lower or 'hash' in content_lower:
                security_score += 0.1
            if 'sanitize' in content_lower:
                security_score += 0.1
        
        return max(0.0, min(1.0, security_score))
    
    async def _analyze_performance(
        self,
        code_files: Dict[str, str],
        test_results: List[TestCase],
        language: str
    ) -> float:
        """Analyze performance characteristics"""
        
        # Calculate performance score based on test execution times
        performance_tests = [t for t in test_results if t.test_type == TestType.PERFORMANCE]
        
        if not performance_tests:
            return 0.7  # Default score when no performance tests
        
        avg_execution_time = sum(t.execution_time for t in performance_tests) / len(performance_tests)
        
        # Score based on execution time (lower is better)
        if avg_execution_time < 0.1:
            return 1.0
        elif avg_execution_time < 0.5:
            return 0.8
        elif avg_execution_time < 1.0:
            return 0.6
        elif avg_execution_time < 2.0:
            return 0.4
        else:
            return 0.2
    
    def _calculate_overall_score(self, result: CodeVerificationResult) -> float:
        """Calculate weighted overall score"""
        
        # Weights for different aspects
        weights = {
            'coverage': 0.25,
            'quality': 0.30,
            'security': 0.25,
            'performance': 0.20
        }
        
        overall_score = (
            result.coverage_percentage / 100 * weights['coverage'] +
            result.quality_score * weights['quality'] +
            result.security_score * weights['security'] +
            result.performance_score * weights['performance']
        )
        
        return round(overall_score, 2)
    
    def _determine_pass_fail(self, result: CodeVerificationResult) -> bool:
        """Determine if verification passes based on thresholds"""
        
        thresholds = {
            'overall_score': 0.7,
            'coverage': 70.0,
            'quality': 0.6,
            'security': 0.7
        }
        
        return (
            result.overall_score >= thresholds['overall_score'] and
            result.coverage_percentage >= thresholds['coverage'] and
            result.quality_score >= thresholds['quality'] and
            result.security_score >= thresholds['security']
        )
    
    async def _generate_feedback(
        self,
        result: CodeVerificationResult,
        code_files: Dict[str, str]
    ) -> List[str]:
        """Generate detailed feedback for the coder"""
        
        feedback = []
        
        # Coverage feedback
        if result.coverage_percentage < 70:
            feedback.append(f"Low test coverage: {result.coverage_percentage:.1f}% (target: 70%+)")
        
        # Quality feedback
        if result.quality_score < 0.7:
            feedback.append(f"Code quality needs improvement: {result.quality_score:.2f} (target: 0.7+)")
        
        # Security feedback
        if result.security_score < 0.7:
            feedback.append(f"Security concerns detected: {result.security_score:.2f} (target: 0.7+)")
        
        # Test results feedback
        failed_tests = [t for t in result.test_results if t.result == TestResult.FAILED]
        if failed_tests:
            feedback.append(f"{len(failed_tests)} tests failed - review and fix issues")
        
        return feedback
    
    async def _generate_suggestions(
        self,
        result: CodeVerificationResult,
        code_files: Dict[str, str]
    ) -> List[str]:
        """Generate improvement suggestions"""
        
        suggestions = []
        
        # Coverage suggestions
        if result.coverage_percentage < 80:
            suggestions.append("Add more test cases to improve coverage")
            suggestions.append("Focus on testing edge cases and error conditions")
        
        # Quality suggestions
        if result.quality_score < 0.8:
            suggestions.append("Improve code documentation and comments")
            suggestions.append("Consider refactoring complex functions")
            suggestions.append("Add input validation and error handling")
        
        # Performance suggestions
        if result.performance_score < 0.7:
            suggestions.append("Optimize algorithm complexity")
            suggestions.append("Consider caching frequently accessed data")
            suggestions.append("Profile code to identify bottlenecks")
        
        return suggestions
    
    async def _analyze_code_structure(
        self,
        code_files: Dict[str, str],
        language: str
    ) -> Dict[str, Any]:
        """Analyze code structure to understand testable elements"""
        
        analysis = {
            'testable_elements': {},
            'integration_points': [],
            'dependencies': [],
            'security_risks': [],
            'performance_targets': {}
        }
        
        for filename, content in code_files.items():
            elements = []
            
            # Simple pattern matching for functions/classes
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                
                if language == "python":
                    if line.startswith('def ') and '(' in line:
                        func_name = line.split('def ')[1].split('(')[0].strip()
                        elements.append({'name': func_name, 'type': 'function'})
                    elif line.startswith('class '):
                        class_name = line.split('class ')[1].split(':')[0].strip()
                        elements.append({'name': class_name, 'type': 'class'})
                
                # Add more language support as needed
            
            analysis['testable_elements'][filename] = elements
            
            # Detect potential integration points
            if 'import' in content or 'require' in content:
                analysis['integration_points'].append(f"{filename} dependencies")
        
        return analysis
    
    async def _query_qa_model(self, prompt: str) -> str:
        """Query the QA model for analysis"""
        
        try:
            if self.qa_model:
                response = self.qa_model(
                    prompt,
                    max_tokens=1024,
                    temperature=0.1  # Low temperature for consistent analysis
                )
                return response.get('choices', [{}])[0].get('text', '')
            else:
                return "QA model response placeholder"
                
        except Exception as e:
            logger.error(f"QA model query failed: {e}")
            return ""
    
    def _extract_quality_score_from_analysis(self, analysis: str) -> float:
        """Extract quality score from analysis text"""
        
        # Simple heuristic scoring based on keywords
        score = 0.7  # Base score
        
        analysis_lower = analysis.lower()
        
        # Positive indicators
        if 'excellent' in analysis_lower:
            score += 0.2
        elif 'good' in analysis_lower:
            score += 0.1
        elif 'well' in analysis_lower:
            score += 0.1
        
        # Negative indicators
        if 'poor' in analysis_lower:
            score -= 0.3
        elif 'bad' in analysis_lower:
            score -= 0.2
        elif 'issue' in analysis_lower:
            score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    def _default_test_frameworks(self) -> Dict[str, Dict[str, str]]:
        """Default test framework configurations"""
        
        return {
            'python': {
                'unit': 'pytest',
                'integration': 'pytest',
                'e2e': 'selenium',
                'performance': 'pytest-benchmark'
            },
            'javascript': {
                'unit': 'jest',
                'integration': 'supertest',
                'e2e': 'cypress',
                'performance': 'artillery'
            },
            'java': {
                'unit': 'junit',
                'integration': 'testng',
                'e2e': 'selenium',
                'performance': 'jmeter'
            }
        }
    
    def _update_stats(self, result: CodeVerificationResult):
        """Update verification statistics"""
        
        self.verification_stats['total_verifications'] += 1
        
        if result.passed:
            self.verification_stats['passed_verifications'] += 1
        
        # Update averages
        total = self.verification_stats['total_verifications']
        
        self.verification_stats['average_coverage'] = (
            (self.verification_stats['average_coverage'] * (total - 1) + result.coverage_percentage) / total
        )
        
        self.verification_stats['average_quality_score'] = (
            (self.verification_stats['average_quality_score'] * (total - 1) + result.quality_score) / total
        )
    
    def get_verification_statistics(self) -> Dict[str, Any]:
        """Get comprehensive verification statistics"""
        
        stats = self.verification_stats.copy()
        
        if stats['total_verifications'] > 0:
            stats['pass_rate'] = stats['passed_verifications'] / stats['total_verifications']
        else:
            stats['pass_rate'] = 0.0
        
        return stats

# Export
__all__ = ['TDDVerifier', 'CodeVerificationResult', 'TestCase', 'TestResult', 'TestType']