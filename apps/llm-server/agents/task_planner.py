"""
Task Planner Agent - Intelligent Task Distribution and Planning
Works with the Architect to break down complex tasks and distribute them optimally
"""

import asyncio
import logging
import time
import uuid
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class TaskPriority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

class TaskStatus(Enum):
    PENDING = "pending"
    PLANNING = "planning"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    TESTING = "testing"
    REVIEW = "review"
    INTEGRATION = "integration"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskType(Enum):
    FEATURE = "feature"
    BUG_FIX = "bug_fix"
    REFACTOR = "refactor"
    OPTIMIZATION = "optimization"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    DEPLOYMENT = "deployment"

@dataclass
class SubTask:
    """Individual subtask within a larger task"""
    id: str
    title: str
    description: str
    assigned_coder: str
    estimated_hours: float
    dependencies: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    test_cases: List[Dict[str, Any]] = field(default_factory=list)
    verification_criteria: List[str] = field(default_factory=list)
    actual_hours: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'assigned_coder': self.assigned_coder,
            'estimated_hours': self.estimated_hours,
            'dependencies': self.dependencies,
            'status': self.status.value,
            'priority': self.priority.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'test_cases': self.test_cases,
            'verification_criteria': self.verification_criteria,
            'actual_hours': self.actual_hours
        }

@dataclass
class TaskPlan:
    """Complete task plan with subtasks and coordination"""
    id: str
    title: str
    description: str
    task_type: TaskType
    priority: TaskPriority
    subtasks: List[SubTask] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    estimated_total_hours: float = 0.0
    actual_total_hours: float = 0.0
    success_criteria: List[str] = field(default_factory=list)
    integration_tests: List[Dict[str, Any]] = field(default_factory=list)
    risk_assessment: Dict[str, Any] = field(default_factory=dict)
    
    def get_progress_percentage(self) -> float:
        """Calculate overall progress percentage"""
        if not self.subtasks:
            return 0.0
        
        completed_tasks = sum(1 for task in self.subtasks if task.status == TaskStatus.COMPLETED)
        return (completed_tasks / len(self.subtasks)) * 100
    
    def get_critical_path(self) -> List[str]:
        """Calculate critical path through subtasks"""
        # Simplified critical path calculation
        # In production, would use proper scheduling algorithms
        dependent_tasks = []
        
        for task in self.subtasks:
            if task.dependencies:
                dependent_tasks.append(task.id)
        
        return dependent_tasks
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'task_type': self.task_type.value,
            'priority': self.priority.value,
            'subtasks': [task.to_dict() for task in self.subtasks],
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'estimated_total_hours': self.estimated_total_hours,
            'actual_total_hours': self.actual_total_hours,
            'success_criteria': self.success_criteria,
            'integration_tests': self.integration_tests,
            'risk_assessment': self.risk_assessment,
            'progress_percentage': self.get_progress_percentage(),
            'critical_path': self.get_critical_path()
        }

class TaskPlanner:
    """
    Intelligent Task Planner for Complex Development Projects
    
    Responsibilities:
    - Break down complex tasks into manageable subtasks
    - Assign tasks to appropriate coders based on specialization
    - Create TDD test plans for each subtask
    - Manage dependencies and critical path
    - Monitor progress and adjust plans
    - Coordinate parallel execution
    """
    
    def __init__(self, architect_model, specialized_coders_config):
        self.architect_model = architect_model
        self.coders_config = specialized_coders_config
        
        # Active plans and tasks
        self.active_plans: Dict[str, TaskPlan] = {}
        self.task_queue: List[SubTask] = []
        self.completed_plans: Dict[str, TaskPlan] = {}
        
        # Planning templates and prompts
        self.planning_prompts = {
            'task_breakdown': """
            You are an expert software architect. Break down this complex task into manageable subtasks.

            Task: {task_description}
            Task Type: {task_type}
            Priority: {priority}
            Available Coders: {available_coders}

            For each subtask, provide:
            1. Clear title and description
            2. Estimated hours (be realistic)
            3. Required coder specialization
            4. Dependencies on other subtasks
            5. Verification criteria (how to know it's complete)
            6. Test cases needed (TDD approach)

            Focus on:
            - Parallel execution where possible
            - Clear boundaries between tasks
            - Testable deliverables
            - Risk mitigation

            Respond in structured format with clear subtask definitions.
            """,
            
            'risk_assessment': """
            Analyze potential risks for this development plan:

            Task: {task_description}
            Subtasks: {subtasks_summary}

            Identify:
            1. Technical risks and mitigation strategies
            2. Resource constraints and solutions
            3. Dependency bottlenecks
            4. Testing challenges
            5. Integration risks

            Provide actionable risk mitigation strategies.
            """,
            
            'test_plan_generation': """
            Create comprehensive test cases for this subtask using TDD approach:

            Subtask: {subtask_description}
            Assigned Coder: {coder_specialization}
            Success Criteria: {success_criteria}

            Generate:
            1. Unit test cases (test first approach)
            2. Integration test scenarios
            3. Edge cases to consider
            4. Performance benchmarks
            5. Security considerations

            Format as executable test specifications.
            """
        }
        
        # Performance tracking
        self.planning_stats = {
            'plans_created': 0,
            'tasks_completed': 0,
            'average_accuracy': 0.0,
            'planning_time_avg': 0.0
        }
        
        logger.info("TaskPlanner initialized with intelligent task distribution")
    
    async def create_task_plan(
        self,
        task_description: str,
        task_type: TaskType,
        priority: TaskPriority = TaskPriority.MEDIUM,
        deadline: Optional[datetime] = None
    ) -> TaskPlan:
        """
        Create a comprehensive task plan with subtasks and assignments
        """
        start_time = time.time()
        
        logger.info(f"Creating task plan: {task_description[:100]}...")
        
        # Generate unique plan ID
        plan_id = str(uuid.uuid4())[:8]
        
        # Create initial task plan
        task_plan = TaskPlan(
            id=plan_id,
            title=self._extract_title(task_description),
            description=task_description,
            task_type=task_type,
            priority=priority,
            status=TaskStatus.PLANNING
        )
        
        try:
            # Step 1: Break down task into subtasks using architect
            subtasks = await self._generate_subtasks(task_description, task_type, priority)
            
            # Step 2: Assign coders to subtasks
            for subtask in subtasks:
                subtask.assigned_coder = self._assign_optimal_coder(subtask)
            
            # Step 3: Generate TDD test cases for each subtask
            for subtask in subtasks:
                subtask.test_cases = await self._generate_test_cases(subtask)
            
            # Step 4: Analyze dependencies and create execution order
            subtasks = self._optimize_dependencies(subtasks)
            
            # Step 5: Perform risk assessment
            risk_assessment = await self._assess_risks(task_description, subtasks)
            
            # Step 6: Calculate estimates and critical path
            task_plan.subtasks = subtasks
            task_plan.estimated_total_hours = sum(task.estimated_hours for task in subtasks)
            task_plan.risk_assessment = risk_assessment
            task_plan.status = TaskStatus.ASSIGNED
            
            # Step 7: Generate integration tests
            task_plan.integration_tests = await self._generate_integration_tests(task_plan)
            
            # Store the plan
            self.active_plans[plan_id] = task_plan
            
            # Update statistics
            planning_time = time.time() - start_time
            self._update_planning_stats(planning_time)
            
            logger.info(f"Task plan created: {plan_id} with {len(subtasks)} subtasks ({planning_time:.2f}s)")
            
            return task_plan
            
        except Exception as e:
            logger.error(f"Task planning failed: {e}")
            task_plan.status = TaskStatus.FAILED
            return task_plan
    
    async def _generate_subtasks(
        self,
        task_description: str,
        task_type: TaskType,
        priority: TaskPriority
    ) -> List[SubTask]:
        """Generate subtasks using the architect model"""
        
        # Get available coders and their specializations
        available_coders = {
            name: profile.specialization.value 
            for name, profile in self.coders_config.items()
        }
        
        prompt = self.planning_prompts['task_breakdown'].format(
            task_description=task_description,
            task_type=task_type.value,
            priority=priority.value,
            available_coders=json.dumps(available_coders, indent=2)
        )
        
        try:
            # Generate breakdown using architect model
            response = await self._query_architect_model(prompt)
            
            # Parse response into subtasks
            subtasks = self._parse_subtasks_response(response)
            
            return subtasks
            
        except Exception as e:
            logger.error(f"Subtask generation failed: {e}")
            # Fallback to simple task breakdown
            return self._create_fallback_subtasks(task_description, task_type)
    
    def _assign_optimal_coder(self, subtask: SubTask) -> str:
        """Assign the most suitable coder for a subtask"""
        
        task_desc_lower = subtask.description.lower()
        
        # Simple keyword-based assignment (can be enhanced with ML)
        if any(keyword in task_desc_lower for keyword in ['frontend', 'ui', 'component', 'react', 'vue']):
            return 'alpha_frontend'
        elif any(keyword in task_desc_lower for keyword in ['backend', 'api', 'database', 'server']):
            return 'beta_backend'
        elif any(keyword in task_desc_lower for keyword in ['devops', 'deploy', 'infrastructure', 'docker']):
            return 'gamma_systems'
        elif any(keyword in task_desc_lower for keyword in ['ai', 'ml', 'model', 'algorithm', 'data']):
            return 'delta_ai'
        elif any(keyword in task_desc_lower for keyword in ['mobile', 'ios', 'android', 'app']):
            return 'epsilon_mobile'
        else:
            return 'zeta_fullstack'
    
    async def _generate_test_cases(self, subtask: SubTask) -> List[Dict[str, Any]]:
        """Generate TDD test cases for a subtask"""
        
        prompt = self.planning_prompts['test_plan_generation'].format(
            subtask_description=subtask.description,
            coder_specialization=subtask.assigned_coder,
            success_criteria='; '.join(subtask.verification_criteria)
        )
        
        try:
            response = await self._query_architect_model(prompt)
            test_cases = self._parse_test_cases_response(response)
            
            return test_cases
            
        except Exception as e:
            logger.error(f"Test case generation failed: {e}")
            return self._create_default_test_cases(subtask)
    
    def _optimize_dependencies(self, subtasks: List[SubTask]) -> List[SubTask]:
        """Optimize task dependencies for parallel execution"""
        
        # Simple dependency optimization
        # In production, use proper topological sorting and critical path analysis
        
        optimized_tasks = []
        independent_tasks = []
        dependent_tasks = []
        
        for task in subtasks:
            if not task.dependencies:
                independent_tasks.append(task)
            else:
                dependent_tasks.append(task)
        
        # Put independent tasks first for parallel execution
        optimized_tasks.extend(independent_tasks)
        optimized_tasks.extend(dependent_tasks)
        
        return optimized_tasks
    
    async def _assess_risks(
        self,
        task_description: str,
        subtasks: List[SubTask]
    ) -> Dict[str, Any]:
        """Assess risks for the task plan"""
        
        subtasks_summary = [
            f"{task.title}: {task.estimated_hours}h ({task.assigned_coder})"
            for task in subtasks
        ]
        
        prompt = self.planning_prompts['risk_assessment'].format(
            task_description=task_description,
            subtasks_summary='\n'.join(subtasks_summary)
        )
        
        try:
            response = await self._query_architect_model(prompt)
            risk_assessment = self._parse_risk_assessment_response(response)
            
            return risk_assessment
            
        except Exception as e:
            logger.error(f"Risk assessment failed: {e}")
            return {'risks': [], 'mitigation_strategies': []}
    
    async def _generate_integration_tests(self, task_plan: TaskPlan) -> List[Dict[str, Any]]:
        """Generate integration tests for the complete task"""
        
        integration_tests = []
        
        # Create basic integration test framework
        integration_tests.append({
            'name': f"Integration test for {task_plan.title}",
            'description': "Verify all components work together",
            'test_type': 'integration',
            'automated': True,
            'success_criteria': task_plan.success_criteria
        })
        
        return integration_tests
    
    async def _query_architect_model(self, prompt: str) -> str:
        """Query the architect model with a prompt"""
        
        try:
            if self.architect_model:
                # Use actual model
                response = self.architect_model(
                    prompt,
                    max_tokens=2048,
                    temperature=0.3
                )
                return response.get('choices', [{}])[0].get('text', '')
            else:
                # Fallback for testing
                return "Architect model response placeholder"
                
        except Exception as e:
            logger.error(f"Architect model query failed: {e}")
            return ""
    
    def _parse_subtasks_response(self, response: str) -> List[SubTask]:
        """Parse architect model response into subtasks"""
        
        # Simplified parsing - in production use structured output
        subtasks = []
        
        lines = response.split('\n')
        current_task = None
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('##') or line.startswith('Task'):
                # New subtask
                if current_task:
                    subtasks.append(current_task)
                
                task_id = str(uuid.uuid4())[:8]
                current_task = SubTask(
                    id=task_id,
                    title=line.replace('#', '').replace('Task', '').strip(),
                    description="",
                    assigned_coder="",
                    estimated_hours=2.0  # Default estimate
                )
            
            elif current_task and line:
                # Add to description
                if 'hours:' in line.lower():
                    try:
                        hours = float(line.split(':')[1].strip())
                        current_task.estimated_hours = hours
                    except:
                        pass
                else:
                    current_task.description += line + " "
        
        # Add last task
        if current_task:
            subtasks.append(current_task)
        
        return subtasks
    
    def _parse_test_cases_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse test cases from response"""
        
        # Simplified test case parsing
        test_cases = []
        
        lines = response.split('\n')
        for line in lines:
            if 'test' in line.lower() and len(line.strip()) > 10:
                test_cases.append({
                    'name': line.strip(),
                    'type': 'unit',
                    'automated': True,
                    'description': line.strip()
                })
        
        return test_cases[:5]  # Limit to 5 test cases per subtask
    
    def _parse_risk_assessment_response(self, response: str) -> Dict[str, Any]:
        """Parse risk assessment from response"""
        
        return {
            'risks': [line.strip() for line in response.split('\n') if 'risk' in line.lower()],
            'mitigation_strategies': [line.strip() for line in response.split('\n') if 'mitigation' in line.lower()],
            'risk_level': 'medium'  # Default
        }
    
    def _create_fallback_subtasks(
        self,
        task_description: str,
        task_type: TaskType
    ) -> List[SubTask]:
        """Create fallback subtasks when AI generation fails"""
        
        task_id = str(uuid.uuid4())[:8]
        
        fallback_task = SubTask(
            id=task_id,
            title="Primary Implementation",
            description=task_description,
            assigned_coder="zeta_fullstack",
            estimated_hours=4.0,
            verification_criteria=["Implementation complete", "Tests passing"]
        )
        
        return [fallback_task]
    
    def _create_default_test_cases(self, subtask: SubTask) -> List[Dict[str, Any]]:
        """Create default test cases when generation fails"""
        
        return [
            {
                'name': f"Test {subtask.title}",
                'type': 'unit',
                'automated': True,
                'description': f"Verify {subtask.title} works correctly"
            }
        ]
    
    def _extract_title(self, description: str) -> str:
        """Extract a concise title from task description"""
        
        # Simple title extraction
        first_sentence = description.split('.')[0]
        if len(first_sentence) > 50:
            return first_sentence[:47] + "..."
        return first_sentence
    
    def _update_planning_stats(self, planning_time: float):
        """Update planning performance statistics"""
        
        self.planning_stats['plans_created'] += 1
        
        # Update average planning time
        total_time = self.planning_stats['planning_time_avg'] * (self.planning_stats['plans_created'] - 1)
        self.planning_stats['planning_time_avg'] = (total_time + planning_time) / self.planning_stats['plans_created']
    
    def get_active_plans(self) -> Dict[str, Dict[str, Any]]:
        """Get all active task plans"""
        
        return {
            plan_id: plan.to_dict() 
            for plan_id, plan in self.active_plans.items()
        }
    
    def get_plan_status(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific plan"""
        
        if plan_id in self.active_plans:
            return self.active_plans[plan_id].to_dict()
        elif plan_id in self.completed_plans:
            return self.completed_plans[plan_id].to_dict()
        else:
            return None
    
    async def update_task_status(
        self,
        plan_id: str,
        subtask_id: str,
        new_status: TaskStatus,
        actual_hours: float = None
    ) -> bool:
        """Update status of a subtask"""
        
        if plan_id not in self.active_plans:
            return False
        
        plan = self.active_plans[plan_id]
        
        for subtask in plan.subtasks:
            if subtask.id == subtask_id:
                subtask.status = new_status
                
                if new_status == TaskStatus.IN_PROGRESS:
                    subtask.started_at = datetime.now()
                elif new_status == TaskStatus.COMPLETED:
                    subtask.completed_at = datetime.now()
                    if actual_hours:
                        subtask.actual_hours = actual_hours
                
                # Update plan status if all tasks complete
                if all(task.status == TaskStatus.COMPLETED for task in plan.subtasks):
                    plan.status = TaskStatus.COMPLETED
                    self.completed_plans[plan_id] = plan
                    del self.active_plans[plan_id]
                
                logger.info(f"Updated task {subtask_id} to {new_status.value}")
                return True
        
        return False
    
    def get_planning_statistics(self) -> Dict[str, Any]:
        """Get comprehensive planning statistics"""
        
        active_count = len(self.active_plans)
        completed_count = len(self.completed_plans)
        
        return {
            'active_plans': active_count,
            'completed_plans': completed_count,
            'total_plans': active_count + completed_count,
            'performance_stats': self.planning_stats,
            'current_load': sum(
                len(plan.subtasks) for plan in self.active_plans.values()
            )
        }

# Export
__all__ = ['TaskPlanner', 'TaskPlan', 'SubTask', 'TaskPriority', 'TaskStatus', 'TaskType']