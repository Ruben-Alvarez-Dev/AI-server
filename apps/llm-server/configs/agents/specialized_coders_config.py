"""
Specialized Coders Configuration - 6 Expert Coders with Varied LLMs
Optimized for M1 Ultra with parallel processing and specialization
"""

from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum

class CoderSpecialization(Enum):
    """Coder specialization types"""
    FRONTEND_SPECIALIST = "frontend_specialist"      # React, Vue, Angular, CSS, JS/TS
    BACKEND_SPECIALIST = "backend_specialist"        # APIs, databases, microservices
    SYSTEMS_ARCHITECT = "systems_architect"         # Architecture, DevOps, cloud
    AI_ML_ENGINEER = "ai_ml_engineer"              # AI/ML, data science, algorithms
    MOBILE_DEVELOPER = "mobile_developer"           # iOS, Android, React Native
    FULLSTACK_GENERALIST = "fullstack_generalist"   # Full-stack, rapid prototyping

@dataclass
class CoderProfile:
    """Individual coder profile with LLM and specialization"""
    name: str
    specialization: CoderSpecialization
    llm_model: str
    model_size: str
    ram_allocation_gb: int
    expected_tokens_per_sec: int
    avg_response_time_ms: int
    context_length_tokens: int
    memory_bandwidth_gbps: float
    cpu_cores_utilized: int
    strengths: List[str]
    supported_languages: List[str]
    preferred_frameworks: List[str]
    expertise_areas: List[str]

# M1 Ultra Optimized Coder Team Configuration
SPECIALIZED_CODERS_TEAM = {
    "alpha_frontend": CoderProfile(
        name="Alpha Frontend",
        specialization=CoderSpecialization.FRONTEND_SPECIALIST,
        llm_model="qwen2.5-coder-7b-instruct-q6_k",
        model_size="5.8GB",
        ram_allocation_gb=8,
        expected_tokens_per_sec=45,
        avg_response_time_ms=850,
        context_length_tokens=32768,
        memory_bandwidth_gbps=380.2,
        cpu_cores_utilized=6,
        strengths=[
            "React/Vue component architecture",
            "CSS animations and responsive design",
            "TypeScript optimization",
            "UI/UX implementation",
            "Frontend performance optimization"
        ],
        supported_languages=["JavaScript", "TypeScript", "HTML", "CSS", "SCSS", "JSX", "TSX"],
        preferred_frameworks=["React", "Vue.js", "Angular", "Svelte", "Next.js", "Nuxt.js"],
        expertise_areas=[
            "Component-based architecture",
            "State management (Redux, Vuex, Pinia)",
            "Modern CSS (Grid, Flexbox, Container queries)",
            "Build tools (Webpack, Vite, Rollup)",
            "Testing (Jest, Cypress, Playwright)"
        ]
    ),
    
    "beta_backend": CoderProfile(
        name="Beta Backend",
        specialization=CoderSpecialization.BACKEND_SPECIALIST,
        llm_model="deepseek-coder-v2-lite-instruct-q6_k",
        model_size="10.5GB",
        ram_allocation_gb=12,
        expected_tokens_per_sec=35,
        avg_response_time_ms=1200,
        context_length_tokens=65536,
        memory_bandwidth_gbps=360.8,
        cpu_cores_utilized=8,
        strengths=[
            "API design and implementation",
            "Database optimization",
            "Microservices architecture",
            "Authentication and security",
            "Performance scaling"
        ],
        supported_languages=["Python", "Node.js", "Go", "Rust", "Java", "C#", "SQL"],
        preferred_frameworks=["FastAPI", "Django", "Express.js", "Gin", "Spring Boot", ".NET"],
        expertise_areas=[
            "RESTful and GraphQL APIs",
            "Database design (PostgreSQL, MongoDB, Redis)",
            "Message queues (RabbitMQ, Kafka)",
            "Caching strategies",
            "Security best practices"
        ]
    ),
    
    "gamma_systems": CoderProfile(
        name="Gamma Systems",
        specialization=CoderSpecialization.SYSTEMS_ARCHITECT,
        llm_model="qwen2.5-32b-instruct-q6_k",
        model_size="22GB",
        ram_allocation_gb=25,
        expected_tokens_per_sec=20,
        avg_response_time_ms=2100,
        context_length_tokens=131072,
        memory_bandwidth_gbps=285.4,
        cpu_cores_utilized=12,
        strengths=[
            "System architecture design",
            "DevOps and CI/CD pipelines",
            "Cloud infrastructure",
            "Containerization and orchestration",
            "Scalability planning"
        ],
        supported_languages=["Python", "Go", "Bash", "YAML", "Terraform", "Docker", "Kubernetes"],
        preferred_frameworks=["Terraform", "Ansible", "Docker", "Kubernetes", "AWS CDK"],
        expertise_areas=[
            "Cloud platforms (AWS, GCP, Azure)",
            "Infrastructure as Code",
            "Monitoring and logging",
            "Load balancing and auto-scaling",
            "Security architecture"
        ]
    ),
    
    "delta_ai": CoderProfile(
        name="Delta AI",
        specialization=CoderSpecialization.AI_ML_ENGINEER,
        llm_model="qwen2.5-coder-14b-instruct-q6_k",
        model_size="10.2GB",
        ram_allocation_gb=13,
        expected_tokens_per_sec=25,
        avg_response_time_ms=1650,
        context_length_tokens=65536,
        memory_bandwidth_gbps=325.7,
        cpu_cores_utilized=10,
        strengths=[
            "Machine learning algorithms",
            "Deep learning architectures",
            "Data pipeline optimization",
            "Model deployment and MLOps",
            "AI research implementation"
        ],
        supported_languages=["Python", "R", "Julia", "CUDA", "SQL", "Jupyter"],
        preferred_frameworks=["PyTorch", "TensorFlow", "scikit-learn", "Hugging Face", "MLflow"],
        expertise_areas=[
            "Neural networks and transformers",
            "Computer vision and NLP",
            "Data preprocessing and feature engineering",
            "Model optimization and quantization",
            "Distributed training"
        ]
    ),
    
    "epsilon_mobile": CoderProfile(
        name="Epsilon Mobile",
        specialization=CoderSpecialization.MOBILE_DEVELOPER,
        llm_model="codestral-22b-v0.1-q6_k",
        model_size="15GB",
        ram_allocation_gb=18,
        expected_tokens_per_sec=30,
        avg_response_time_ms=1450,
        context_length_tokens=32768,
        memory_bandwidth_gbps=310.5,
        cpu_cores_utilized=8,
        strengths=[
            "Native mobile development",
            "Cross-platform frameworks",
            "Mobile UI/UX optimization",
            "Performance optimization",
            "App store deployment"
        ],
        supported_languages=["Swift", "Kotlin", "JavaScript", "TypeScript", "Dart", "Objective-C", "Java"],
        preferred_frameworks=["SwiftUI", "Jetpack Compose", "React Native", "Flutter", "Expo"],
        expertise_areas=[
            "iOS and Android native development",
            "Mobile architecture patterns (MVVM, MVI)",
            "Push notifications and deep linking",
            "Offline-first applications",
            "Mobile security best practices"
        ]
    ),
    
    "zeta_fullstack": CoderProfile(
        name="Zeta Fullstack",
        specialization=CoderSpecialization.FULLSTACK_GENERALIST,
        llm_model="llama-3.1-8b-instruct-q6_k",
        model_size="6GB",
        ram_allocation_gb=8,
        expected_tokens_per_sec=50,
        avg_response_time_ms=720,
        context_length_tokens=131072,
        memory_bandwidth_gbps=395.1,
        cpu_cores_utilized=4,
        strengths=[
            "Rapid prototyping",
            "Full-stack integration",
            "Problem-solving versatility",
            "Technology adaptation",
            "End-to-end implementation"
        ],
        supported_languages=["JavaScript", "TypeScript", "Python", "HTML", "CSS", "SQL", "Bash"],
        preferred_frameworks=["Next.js", "FastAPI", "Express.js", "Prisma", "Tailwind CSS"],
        expertise_areas=[
            "Full-stack application development",
            "Database to frontend integration",
            "API development and consumption",
            "Authentication and authorization",
            "Deployment and hosting"
        ]
    )
}

# Team coordination and load balancing configuration
TEAM_COORDINATION_CONFIG = {
    "parallel_execution": {
        "max_concurrent_tasks": 6,  # All coders can work simultaneously
        "task_distribution_strategy": "specialization_first",  # Route by specialization
        "load_balancing": "round_robin_within_specialization",
        "failover_enabled": True
    },
    
    "resource_management": {
        "total_ram_budget_gb": 84,  # 84GB allocated for coders (out of 128GB total)
        "dynamic_allocation": True,  # Allow RAM reallocation based on demand
        "priority_levels": {
            "critical_bug_fix": 1,
            "feature_development": 2,
            "code_review": 3,
            "refactoring": 4,
            "documentation": 5
        }
    },
    
    "collaboration_patterns": {
        "pair_programming": {
            "frontend_backend": ["alpha_frontend", "beta_backend"],
            "ai_systems": ["delta_ai", "gamma_systems"],
            "mobile_fullstack": ["epsilon_mobile", "zeta_fullstack"]
        },
        "code_review_rotation": [
            "beta_backend",    # Reviews frontend code
            "gamma_systems",   # Reviews backend code
            "delta_ai",        # Reviews systems code
            "epsilon_mobile",  # Reviews AI code
            "zeta_fullstack",  # Reviews mobile code
            "alpha_frontend"   # Reviews fullstack code
        ]
    },
    
    "specialization_routing": {
        "web_development": ["alpha_frontend", "beta_backend", "zeta_fullstack"],
        "mobile_development": ["epsilon_mobile", "alpha_frontend", "zeta_fullstack"],
        "ai_ml_projects": ["delta_ai", "beta_backend", "gamma_systems"],
        "devops_infrastructure": ["gamma_systems", "beta_backend", "zeta_fullstack"],
        "data_engineering": ["delta_ai", "beta_backend", "gamma_systems"],
        "api_development": ["beta_backend", "gamma_systems", "zeta_fullstack"]
    },
    
    "performance_monitoring": {
        "track_tokens_per_second": True,
        "measure_task_completion_time": True,
        "monitor_ram_usage": True,
        "quality_metrics": ["code_correctness", "test_coverage", "documentation_quality"],
        "efficiency_metrics": ["lines_per_minute", "bugs_per_kloc", "review_turnaround_time"]
    }
}

# Task complexity and routing rules
TASK_ROUTING_RULES = {
    "simple_tasks": {
        "description": "Single-file changes, bug fixes, minor features",
        "preferred_coders": ["zeta_fullstack"],
        "fallback_coders": "any_available",
        "max_context_tokens": 4096
    },
    
    "medium_tasks": {
        "description": "Multi-file features, refactoring, API implementations",
        "preferred_coders": "specialization_match",
        "fallback_coders": ["zeta_fullstack", "beta_backend"],
        "max_context_tokens": 8192
    },
    
    "complex_tasks": {
        "description": "Architecture changes, new systems, complex algorithms",
        "preferred_coders": ["gamma_systems", "delta_ai"],
        "collaboration_required": True,
        "max_context_tokens": 16384
    },
    
    "critical_tasks": {
        "description": "Production bugs, security issues, performance problems",
        "preferred_coders": "all_available",
        "priority": "highest",
        "parallel_execution": True,
        "max_context_tokens": 32768
    }
}

# Quality assurance and testing configuration
QUALITY_ASSURANCE_CONFIG = {
    "code_review_requirements": {
        "mandatory_review": True,
        "minimum_reviewers": 1,
        "cross_specialization_review": True,
        "automated_checks": [
            "syntax_validation",
            "security_scan",
            "performance_analysis",
            "test_coverage_check"
        ]
    },
    
    "testing_strategies": {
        "unit_tests": {
            "required": True,
            "coverage_threshold": 80,
            "responsible_coder": "task_author"
        },
        "integration_tests": {
            "required_for": ["api_changes", "database_changes"],
            "responsible_coder": "backend_specialist"
        },
        "end_to_end_tests": {
            "required_for": ["ui_changes", "workflow_changes"],
            "responsible_coder": "frontend_specialist"
        }
    },
    
    "documentation_requirements": {
        "code_comments": "inline",
        "api_documentation": "openapi_spec",
        "architecture_decisions": "adr_format",
        "readme_updates": "automatic"
    }
}

def get_coder_for_task(task_description: str, task_complexity: str, preferred_languages: List[str] = None) -> str:
    """
    Route task to the most appropriate coder based on requirements
    """
    
    # Analyze task description for keywords
    task_lower = task_description.lower()
    
    # Frontend keywords
    if any(keyword in task_lower for keyword in ['react', 'vue', 'angular', 'css', 'html', 'frontend', 'ui', 'component']):
        return "alpha_frontend"
    
    # Backend keywords
    elif any(keyword in task_lower for keyword in ['api', 'database', 'server', 'backend', 'microservice', 'authentication']):
        return "beta_backend"
    
    # Systems/DevOps keywords
    elif any(keyword in task_lower for keyword in ['deploy', 'docker', 'kubernetes', 'infrastructure', 'devops', 'ci/cd']):
        return "gamma_systems"
    
    # AI/ML keywords
    elif any(keyword in task_lower for keyword in ['machine learning', 'ai', 'model', 'neural', 'data science', 'algorithm']):
        return "delta_ai"
    
    # Mobile keywords
    elif any(keyword in task_lower for keyword in ['ios', 'android', 'mobile', 'app', 'swift', 'kotlin', 'react native']):
        return "epsilon_mobile"
    
    # Default to fullstack generalist
    else:
        return "zeta_fullstack"

def get_team_statistics() -> Dict[str, Any]:
    """Get comprehensive team statistics"""
    
    total_ram = sum(coder.ram_allocation_gb for coder in SPECIALIZED_CODERS_TEAM.values())
    total_expected_tps = sum(coder.expected_tokens_per_sec for coder in SPECIALIZED_CODERS_TEAM.values())
    
    return {
        "team_size": len(SPECIALIZED_CODERS_TEAM),
        "total_ram_allocation_gb": total_ram,
        "total_expected_tokens_per_sec": total_expected_tps,
        "specializations": [coder.specialization.value for coder in SPECIALIZED_CODERS_TEAM.values()],
        "model_diversity": len(set(coder.llm_model for coder in SPECIALIZED_CODERS_TEAM.values())),
        "supported_languages": list(set(
            lang for coder in SPECIALIZED_CODERS_TEAM.values() 
            for lang in coder.supported_languages
        )),
        "coverage_areas": [
            "Frontend Development",
            "Backend Development", 
            "Systems Architecture",
            "AI/ML Engineering",
            "Mobile Development",
            "Full-stack Development"
        ]
    }

# Export configuration
__all__ = [
    'SPECIALIZED_CODERS_TEAM',
    'TEAM_COORDINATION_CONFIG', 
    'TASK_ROUTING_RULES',
    'QUALITY_ASSURANCE_CONFIG',
    'CoderSpecialization',
    'CoderProfile',
    'get_coder_for_task',
    'get_team_statistics'
]