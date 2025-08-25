"""
Agent Registry - Modular Agent System for Dynamic Specialization Swapping
Allows switching between coding agents and specialized agents (office, finance, education, etc.)
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Type, Protocol
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import importlib
import inspect

logger = logging.getLogger(__name__)

class AgentCategory(Enum):
    """Categories of agents available in the system"""
    DEVELOPMENT = "development"     # Code, architecture, testing
    PRODUCTIVITY = "productivity"   # Office, documents, automation
    FINANCE = "finance"            # Accounting, analysis, planning
    EDUCATION = "education"        # Training, documentation, learning
    CREATIVE = "creative"          # Writing, design, content
    ANALYSIS = "analysis"          # Data, research, insights
    COMMUNICATION = "communication" # Email, presentations, social
    SPECIALIZED = "specialized"    # Domain-specific experts

class AgentCapability(Enum):
    """Specific capabilities an agent can have"""
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    TESTING = "testing"
    DEBUGGING = "debugging"
    DOCUMENTATION = "documentation"
    DATA_ANALYSIS = "data_analysis"
    SPREADSHEET_AUTOMATION = "spreadsheet_automation"
    PRESENTATION_CREATION = "presentation_creation"
    FINANCIAL_MODELING = "financial_modeling"
    CONTENT_WRITING = "content_writing"
    IMAGE_ANALYSIS = "image_analysis"
    API_INTEGRATION = "api_integration"
    WORKFLOW_AUTOMATION = "workflow_automation"

@dataclass
class AgentProfile:
    """Complete profile of an available agent"""
    agent_id: str
    name: str
    description: str
    category: AgentCategory
    capabilities: List[AgentCapability]
    
    # Technical specifications
    model_name: str
    ram_requirement_gb: int
    expected_tokens_per_sec: int
    
    # Agent metadata
    version: str = "1.0.0"
    author: str = "AI Orchestra"
    tags: List[str] = field(default_factory=list)
    
    # Runtime configuration
    config_schema: Dict[str, Any] = field(default_factory=dict)
    default_config: Dict[str, Any] = field(default_factory=dict)
    
    # Performance metrics
    success_rate: float = 0.95
    average_response_time: float = 2.0
    user_satisfaction: float = 0.9
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'agent_id': self.agent_id,
            'name': self.name,
            'description': self.description,
            'category': self.category.value,
            'capabilities': [cap.value for cap in self.capabilities],
            'model_name': self.model_name,
            'ram_requirement_gb': self.ram_requirement_gb,
            'expected_tokens_per_sec': self.expected_tokens_per_sec,
            'version': self.version,
            'author': self.author,
            'tags': self.tags,
            'config_schema': self.config_schema,
            'default_config': self.default_config,
            'performance': {
                'success_rate': self.success_rate,
                'average_response_time': self.average_response_time,
                'user_satisfaction': self.user_satisfaction
            }
        }

class BaseAgent(ABC):
    """Base class for all agents in the system"""
    
    def __init__(self, agent_id: str, config: Dict[str, Any] = None):
        self.agent_id = agent_id
        self.config = config or {}
        self.is_loaded = False
        self.performance_metrics = {
            'tasks_completed': 0,
            'errors': 0,
            'average_time': 0.0
        }
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the agent (load model, setup resources)"""
        pass
    
    @abstractmethod
    async def shutdown(self) -> bool:
        """Shutdown the agent (free resources)"""
        pass
    
    @abstractmethod
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a request and return response"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[AgentCapability]:
        """Get list of capabilities this agent supports"""
        pass
    
    def get_profile(self) -> AgentProfile:
        """Get the agent's profile"""
        return AgentProfile(
            agent_id=self.agent_id,
            name=self.__class__.__name__,
            description="Base agent implementation",
            category=AgentCategory.SPECIALIZED,
            capabilities=self.get_capabilities(),
            model_name="unknown",
            ram_requirement_gb=4,
            expected_tokens_per_sec=20
        )

class AgentRegistry:
    """
    Central registry for all available agents
    
    Manages:
    - Agent discovery and registration
    - Dynamic loading/unloading
    - Capability matching
    - Resource management
    - Performance tracking
    """
    
    def __init__(self):
        self.registered_agents: Dict[str, AgentProfile] = {}
        self.active_agents: Dict[str, BaseAgent] = {}
        self.agent_classes: Dict[str, Type[BaseAgent]] = {}
        
        # Load default development agents
        self._register_default_agents()
        
        logger.info("AgentRegistry initialized")
    
    def _register_default_agents(self):
        """Register default development agents"""
        
        # Development agents (current coders)
        development_agents = [
            AgentProfile(
                agent_id="alpha_frontend",
                name="Alpha Frontend Specialist",
                description="Expert in React, Vue, Angular, and modern frontend development",
                category=AgentCategory.DEVELOPMENT,
                capabilities=[
                    AgentCapability.CODE_GENERATION,
                    AgentCapability.CODE_REVIEW,
                    AgentCapability.TESTING
                ],
                model_name="qwen2.5-coder-7b",
                ram_requirement_gb=8,
                expected_tokens_per_sec=45,
                tags=["frontend", "react", "vue", "javascript", "typescript"]
            ),
            
            AgentProfile(
                agent_id="beta_backend",
                name="Beta Backend Specialist", 
                description="Expert in APIs, databases, and backend architecture",
                category=AgentCategory.DEVELOPMENT,
                capabilities=[
                    AgentCapability.CODE_GENERATION,
                    AgentCapability.API_INTEGRATION,
                    AgentCapability.TESTING,
                    AgentCapability.DEBUGGING
                ],
                model_name="deepseek-coder-v2-lite",
                ram_requirement_gb=12,
                expected_tokens_per_sec=35,
                tags=["backend", "api", "database", "python", "node"]
            ),
            
            AgentProfile(
                agent_id="gamma_systems",
                name="Gamma Systems Architect",
                description="Expert in DevOps, cloud infrastructure, and system architecture",
                category=AgentCategory.DEVELOPMENT,
                capabilities=[
                    AgentCapability.CODE_GENERATION,
                    AgentCapability.WORKFLOW_AUTOMATION,
                    AgentCapability.DOCUMENTATION
                ],
                model_name="qwen2.5-32b",
                ram_requirement_gb=25,
                expected_tokens_per_sec=20,
                tags=["devops", "cloud", "docker", "kubernetes", "architecture"]
            ),
            
            AgentProfile(
                agent_id="delta_ai",
                name="Delta AI/ML Engineer",
                description="Expert in machine learning, data science, and AI algorithms",
                category=AgentCategory.DEVELOPMENT,
                capabilities=[
                    AgentCapability.CODE_GENERATION,
                    AgentCapability.DATA_ANALYSIS,
                    AgentCapability.TESTING
                ],
                model_name="qwen2.5-coder-14b",
                ram_requirement_gb=13,
                expected_tokens_per_sec=25,
                tags=["ai", "ml", "python", "pytorch", "data-science"]
            ),
            
            AgentProfile(
                agent_id="epsilon_mobile",
                name="Epsilon Mobile Developer",
                description="Expert in iOS, Android, and cross-platform mobile development",
                category=AgentCategory.DEVELOPMENT,
                capabilities=[
                    AgentCapability.CODE_GENERATION,
                    AgentCapability.CODE_REVIEW,
                    AgentCapability.TESTING
                ],
                model_name="codestral-22b",
                ram_requirement_gb=18,
                expected_tokens_per_sec=30,
                tags=["mobile", "ios", "android", "swift", "kotlin", "react-native"]
            ),
            
            AgentProfile(
                agent_id="zeta_fullstack", 
                name="Zeta Fullstack Generalist",
                description="Versatile full-stack developer for rapid prototyping",
                category=AgentCategory.DEVELOPMENT,
                capabilities=[
                    AgentCapability.CODE_GENERATION,
                    AgentCapability.API_INTEGRATION,
                    AgentCapability.TESTING,
                    AgentCapability.DOCUMENTATION
                ],
                model_name="llama-3.1-8b",
                ram_requirement_gb=8,
                expected_tokens_per_sec=50,
                tags=["fullstack", "javascript", "python", "rapid-prototyping"]
            )
        ]
        
        for agent in development_agents:
            self.registered_agents[agent.agent_id] = agent
    
    def register_agent_class(self, agent_class: Type[BaseAgent], profile: AgentProfile):
        """Register a new agent class with its profile"""
        
        self.agent_classes[profile.agent_id] = agent_class
        self.registered_agents[profile.agent_id] = profile
        
        logger.info(f"Registered agent class: {profile.agent_id} - {profile.name}")
    
    def register_productivity_agents(self):
        """Register productivity/office agents"""
        
        productivity_agents = [
            AgentProfile(
                agent_id="office_specialist",
                name="Office Productivity Specialist",
                description="Expert in Excel, Word, PowerPoint automation and data processing",
                category=AgentCategory.PRODUCTIVITY,
                capabilities=[
                    AgentCapability.SPREADSHEET_AUTOMATION,
                    AgentCapability.PRESENTATION_CREATION,
                    AgentCapability.DOCUMENTATION,
                    AgentCapability.WORKFLOW_AUTOMATION
                ],
                model_name="llama-3.1-8b-office",
                ram_requirement_gb=8,
                expected_tokens_per_sec=40,
                tags=["excel", "powerpoint", "word", "automation", "vba"]
            ),
            
            AgentProfile(
                agent_id="data_analyst",
                name="Business Data Analyst",
                description="Expert in data analysis, visualization, and business intelligence",
                category=AgentCategory.ANALYSIS,
                capabilities=[
                    AgentCapability.DATA_ANALYSIS,
                    AgentCapability.SPREADSHEET_AUTOMATION,
                    AgentCapability.PRESENTATION_CREATION
                ],
                model_name="qwen2.5-analyst-14b",
                ram_requirement_gb=14,
                expected_tokens_per_sec=30,
                tags=["data", "analysis", "visualization", "business-intelligence"]
            ),
            
            AgentProfile(
                agent_id="content_creator",
                name="Content Creation Specialist", 
                description="Expert in writing, marketing content, and communication",
                category=AgentCategory.CREATIVE,
                capabilities=[
                    AgentCapability.CONTENT_WRITING,
                    AgentCapability.PRESENTATION_CREATION,
                    AgentCapability.DOCUMENTATION
                ],
                model_name="llama-3.1-creative-8b",
                ram_requirement_gb=8,
                expected_tokens_per_sec=45,
                tags=["writing", "marketing", "content", "communication"]
            )
        ]
        
        for agent in productivity_agents:
            self.registered_agents[agent.agent_id] = agent
    
    def register_finance_agents(self):
        """Register finance/accounting agents"""
        
        finance_agents = [
            AgentProfile(
                agent_id="financial_analyst",
                name="Financial Analysis Specialist",
                description="Expert in financial modeling, analysis, and planning",
                category=AgentCategory.FINANCE,
                capabilities=[
                    AgentCapability.FINANCIAL_MODELING,
                    AgentCapability.DATA_ANALYSIS,
                    AgentCapability.SPREADSHEET_AUTOMATION,
                    AgentCapability.PRESENTATION_CREATION
                ],
                model_name="qwen2.5-finance-14b",
                ram_requirement_gb=14,
                expected_tokens_per_sec=35,
                tags=["finance", "modeling", "analysis", "planning", "excel"]
            ),
            
            AgentProfile(
                agent_id="accounting_specialist",
                name="Accounting & Compliance Specialist",
                description="Expert in accounting, tax preparation, and regulatory compliance",
                category=AgentCategory.FINANCE,
                capabilities=[
                    AgentCapability.SPREADSHEET_AUTOMATION,
                    AgentCapability.DOCUMENTATION,
                    AgentCapability.WORKFLOW_AUTOMATION
                ],
                model_name="llama-3.1-accounting-8b",
                ram_requirement_gb=8,
                expected_tokens_per_sec=40,
                tags=["accounting", "tax", "compliance", "bookkeeping"]
            )
        ]
        
        for agent in finance_agents:
            self.registered_agents[agent.agent_id] = agent
    
    def register_education_agents(self):
        """Register education/training agents"""
        
        education_agents = [
            AgentProfile(
                agent_id="training_specialist",
                name="Training & Education Specialist",
                description="Expert in creating educational content, courses, and training materials",
                category=AgentCategory.EDUCATION,
                capabilities=[
                    AgentCapability.CONTENT_WRITING,
                    AgentCapability.PRESENTATION_CREATION,
                    AgentCapability.DOCUMENTATION
                ],
                model_name="qwen2.5-education-14b",
                ram_requirement_gb=12,
                expected_tokens_per_sec=35,
                tags=["education", "training", "courses", "learning"]
            )
        ]
        
        for agent in education_agents:
            self.registered_agents[agent.agent_id] = agent
    
    async def load_agent(self, agent_id: str, config: Dict[str, Any] = None) -> bool:
        """Load an agent into memory"""
        
        if agent_id in self.active_agents:
            logger.info(f"Agent {agent_id} already loaded")
            return True
        
        profile = self.registered_agents.get(agent_id)
        if not profile:
            logger.error(f"Agent {agent_id} not found in registry")
            return False
        
        # Check if we have the agent class
        if agent_id not in self.agent_classes:
            logger.error(f"Agent class not found for {agent_id}")
            return False
        
        try:
            # Instantiate agent
            agent_class = self.agent_classes[agent_id]
            agent = agent_class(agent_id, config)
            
            # Initialize agent
            if await agent.initialize():
                self.active_agents[agent_id] = agent
                logger.info(f"Successfully loaded agent: {agent_id}")
                return True
            else:
                logger.error(f"Failed to initialize agent: {agent_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error loading agent {agent_id}: {e}")
            return False
    
    async def unload_agent(self, agent_id: str) -> bool:
        """Unload an agent from memory"""
        
        if agent_id not in self.active_agents:
            logger.info(f"Agent {agent_id} not currently loaded")
            return True
        
        try:
            agent = self.active_agents[agent_id]
            
            # Shutdown agent
            if await agent.shutdown():
                del self.active_agents[agent_id]
                logger.info(f"Successfully unloaded agent: {agent_id}")
                return True
            else:
                logger.error(f"Failed to shutdown agent: {agent_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error unloading agent {agent_id}: {e}")
            return False
    
    async def switch_agent_configuration(
        self, 
        current_config: Dict[str, List[str]], 
        target_config: Dict[str, List[str]]
    ) -> bool:
        """Switch from current agent configuration to target configuration"""
        
        logger.info(f"Switching agent configuration")
        
        # Determine agents to unload and load
        current_agents = set()
        target_agents = set()
        
        for category, agent_ids in current_config.items():
            current_agents.update(agent_ids)
        
        for category, agent_ids in target_config.items():
            target_agents.update(agent_ids)
        
        to_unload = current_agents - target_agents
        to_load = target_agents - current_agents
        
        # Unload agents no longer needed
        unload_success = True
        for agent_id in to_unload:
            if not await self.unload_agent(agent_id):
                unload_success = False
        
        # Load new agents
        load_success = True
        for agent_id in to_load:
            if not await self.load_agent(agent_id):
                load_success = False
        
        success = unload_success and load_success
        
        if success:
            logger.info(f"Successfully switched configuration: -{len(to_unload)} +{len(to_load)} agents")
        else:
            logger.error("Configuration switch completed with errors")
        
        return success
    
    def get_agents_by_category(self, category: AgentCategory) -> List[AgentProfile]:
        """Get all agents in a specific category"""
        
        return [
            agent for agent in self.registered_agents.values()
            if agent.category == category
        ]
    
    def get_agents_by_capability(self, capability: AgentCapability) -> List[AgentProfile]:
        """Get all agents with a specific capability"""
        
        return [
            agent for agent in self.registered_agents.values()
            if capability in agent.capabilities
        ]
    
    def find_best_agent_for_task(
        self, 
        task_description: str,
        required_capabilities: List[AgentCapability] = None,
        preferred_category: AgentCategory = None
    ) -> Optional[AgentProfile]:
        """Find the best agent for a given task"""
        
        candidates = list(self.registered_agents.values())
        
        # Filter by category if specified
        if preferred_category:
            candidates = [a for a in candidates if a.category == preferred_category]
        
        # Filter by required capabilities
        if required_capabilities:
            candidates = [
                a for a in candidates 
                if all(cap in a.capabilities for cap in required_capabilities)
            ]
        
        if not candidates:
            return None
        
        # Score candidates based on task description
        scored_candidates = []
        
        for agent in candidates:
            score = self._calculate_task_match_score(agent, task_description)
            scored_candidates.append((agent, score))
        
        # Sort by score and return best match
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        
        return scored_candidates[0][0] if scored_candidates else None
    
    def _calculate_task_match_score(self, agent: AgentProfile, task_description: str) -> float:
        """Calculate how well an agent matches a task description"""
        
        score = 0.0
        task_lower = task_description.lower()
        
        # Check tags for keyword matches
        for tag in agent.tags:
            if tag.lower() in task_lower:
                score += 0.2
        
        # Boost score based on performance metrics
        score += agent.success_rate * 0.3
        score += agent.user_satisfaction * 0.2
        
        # Penalize for high resource requirements (prefer efficient agents)
        if agent.ram_requirement_gb > 15:
            score -= 0.1
        
        return min(score, 1.0)
    
    def get_registry_status(self) -> Dict[str, Any]:
        """Get comprehensive registry status"""
        
        category_counts = {}
        capability_counts = {}
        
        for agent in self.registered_agents.values():
            category = agent.category.value
            category_counts[category] = category_counts.get(category, 0) + 1
            
            for capability in agent.capabilities:
                cap_name = capability.value
                capability_counts[cap_name] = capability_counts.get(cap_name, 0) + 1
        
        return {
            'total_registered': len(self.registered_agents),
            'total_active': len(self.active_agents),
            'categories': category_counts,
            'capabilities': capability_counts,
            'active_agents': list(self.active_agents.keys()),
            'registered_agents': list(self.registered_agents.keys())
        }
    
    def get_configuration_templates(self) -> Dict[str, Dict[str, List[str]]]:
        """Get predefined agent configuration templates"""
        
        return {
            'development': {
                'core': ['alpha_frontend', 'beta_backend', 'zeta_fullstack'],
                'advanced': ['gamma_systems', 'delta_ai', 'epsilon_mobile'],
                'vision': ['vision_agent']
            },
            
            'productivity': {
                'office': ['office_specialist', 'data_analyst'],
                'content': ['content_creator'],
                'analysis': ['data_analyst']
            },
            
            'finance': {
                'analysis': ['financial_analyst'],
                'accounting': ['accounting_specialist'],
                'planning': ['financial_analyst', 'data_analyst']
            },
            
            'education': {
                'training': ['training_specialist', 'content_creator'],
                'documentation': ['training_specialist']
            },
            
            'mixed': {
                'business': ['office_specialist', 'financial_analyst', 'content_creator'],
                'research': ['data_analyst', 'content_creator', 'training_specialist']
            }
        }

# Global agent registry instance
agent_registry = AgentRegistry()

# Export
__all__ = [
    'AgentRegistry', 'AgentProfile', 'BaseAgent', 
    'AgentCategory', 'AgentCapability', 
    'agent_registry'
]