"""
LLM Server Main Application - FastAPI server for AI development orchestration
Provides REST API endpoints for workflow execution and agent management
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

import uvicorn
from pydantic_settings import BaseSettings

# Import our modules
from .api import (
    workflow_router,
    agent_router, 
    health_router,
    monitoring_router,
    openai_adapter
)
from .core import (
    AgentManager,
    WorkflowManager,
    RequestManager,
    get_settings
)
from .utils import setup_logging, get_system_info

# Import agents and workflows
from ..agents import AGENT_REGISTRY
from ..workflows import WORKFLOW_REGISTRY
from ..monitoring import ResourceMonitor, MetricsCollector


logger = logging.getLogger(__name__)


class LLMServerSettings(BaseSettings):
    """Application settings"""
    
    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    reload: bool = False
    
    # Model paths
    models_dir: str = "./models"
    router_model_path: str = "./models/qwen2-1_5b-instruct-q6_k.gguf"
    architect_model_path: str = "./models/qwen2_5-32b-instruct-q6_k.gguf"
    coder_primary_model_path: str = "./models/qwen2_5-coder-7b-instruct-q6_k.gguf"
    coder_secondary_model_path: str = "./models/deepseek-coder-v2-lite-instruct-q6_k.gguf"
    qa_checker_model_path: str = "./models/qwen2_5-14b-instruct-q6_k.gguf"
    debugger_model_path: str = "./models/deepseek-coder-v2-lite-instruct-q6_k.gguf"
    
    # Performance settings
    max_concurrent_requests: int = 10
    request_timeout: int = 600  # 10 minutes
    enable_metrics: bool = True
    enable_monitoring: bool = True
    
    # Security
    enable_cors: bool = True
    cors_origins: List[str] = ["*"]
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = "./logs/llm-server.log"
    
    # Feature flags
    enable_swagger_ui: bool = True
    enable_background_tasks: bool = True
    
    class Config:
        env_file = ".env"
        env_prefix = "LLM_SERVER_"


# Global managers
agent_manager: Optional[AgentManager] = None
workflow_manager: Optional[WorkflowManager] = None
request_manager: Optional[RequestManager] = None
resource_monitor: Optional[ResourceMonitor] = None
metrics_collector: Optional[MetricsCollector] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global agent_manager, workflow_manager, request_manager, resource_monitor, metrics_collector
    
    settings = get_settings()
    
    try:
        logger.info("Starting LLM Server initialization...")
        
        # Initialize monitoring
        if settings.enable_monitoring:
            resource_monitor = ResourceMonitor()
            await resource_monitor.start()
            logger.info("Resource monitor started")
        
        if settings.enable_metrics:
            metrics_collector = MetricsCollector()
            await metrics_collector.start()
            logger.info("Metrics collector started")
        
        # Initialize agent manager
        agent_manager = AgentManager()
        await agent_manager.initialize({
            "router": settings.router_model_path,
            "architect": settings.architect_model_path, 
            "coder_primary": settings.coder_primary_model_path,
            "coder_secondary": settings.coder_secondary_model_path,
            "qa_checker": settings.qa_checker_model_path,
            "debugger": settings.debugger_model_path
        })
        logger.info("Agent manager initialized")
        
        # Initialize workflow manager
        workflow_manager = WorkflowManager()
        agents_registry = await agent_manager.get_agents_registry()
        await workflow_manager.initialize(agents_registry)
        logger.info("Workflow manager initialized")
        
        # Initialize request manager
        request_manager = RequestManager(
            agent_manager=agent_manager,
            workflow_manager=workflow_manager,
            max_concurrent=settings.max_concurrent_requests,
            timeout=settings.request_timeout
        )
        logger.info("Request manager initialized")
        
        # Store managers in app state
        app.state.agent_manager = agent_manager
        app.state.workflow_manager = workflow_manager
        app.state.request_manager = request_manager
        app.state.resource_monitor = resource_monitor
        app.state.metrics_collector = metrics_collector
        
        logger.info("LLM Server initialized successfully!")
        
        # Yield control to the application
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize LLM Server: {e}")
        raise
    
    finally:
        # Cleanup
        logger.info("Shutting down LLM Server...")
        
        if request_manager:
            await request_manager.shutdown()
            
        if workflow_manager:
            await workflow_manager.shutdown()
            
        if agent_manager:
            await agent_manager.shutdown()
            
        if resource_monitor:
            await resource_monitor.stop()
            
        if metrics_collector:
            await metrics_collector.stop()
            
        logger.info("LLM Server shutdown complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    settings = get_settings()
    
    # Setup logging
    setup_logging(
        level=settings.log_level,
        log_file=settings.log_file
    )
    
    # Create FastAPI app with lifespan
    app = FastAPI(
        title="LLM Server",
        description="AI Development Orchestration Server with M1 Ultra Optimization",
        version="0.1.0",
        docs_url="/docs" if settings.enable_swagger_ui else None,
        redoc_url="/redoc" if settings.enable_swagger_ui else None,
        openapi_url="/openapi.json",
        lifespan=lifespan
    )
    
    # Add middleware
    if settings.enable_cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Add request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = asyncio.get_event_loop().time()
        
        # Log request
        logger.info(f"Request: {request.method} {request.url}")
        
        # Process request
        response = await call_next(request)
        
        # Log response
        process_time = asyncio.get_event_loop().time() - start_time
        logger.info(f"Response: {response.status_code} ({process_time:.3f}s)")
        
        # Add timing header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
    
    # Include routers
    app.include_router(health_router, prefix="/health", tags=["Health"])
    app.include_router(workflow_router, prefix="/workflows", tags=["Workflows"])
    app.include_router(agent_router, prefix="/agents", tags=["Agents"])
    app.include_router(monitoring_router, prefix="/monitoring", tags=["Monitoring"])
    # OpenAI-compatible adapter (exposes /v1/* endpoints)
    app.include_router(openai_adapter.router, prefix="", tags=["OpenAI-Compat"])
    
    # Root endpoint
    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint with server information"""
        system_info = get_system_info()
        
        return {
            "message": "LLM Server - AI Development Orchestration",
            "version": "0.1.0",
            "status": "running",
            "system_info": system_info,
            "available_endpoints": {
                "health": "/health",
                "workflows": "/workflows",
                "agents": "/agents", 
                "monitoring": "/monitoring",
                "docs": "/docs",
                "openapi": "/openapi.json"
            },
            "features": {
                "agents": list(AGENT_REGISTRY.keys()),
                "workflows": list(WORKFLOW_REGISTRY.keys()),
                "monitoring": settings.enable_monitoring,
                "metrics": settings.enable_metrics
            }
        }
    
    # Custom OpenAPI schema
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        
        openapi_schema = get_openapi(
            title="LLM Server API",
            version="0.1.0",
            description="""
            # LLM Server - AI Development Orchestration
            
            High-performance AI development server optimized for M1 Ultra with specialized agents:
            
            ## Features
            - **Multi-agent orchestration** with LangGraph workflows
            - **M1 Ultra optimization** with Metal acceleration
            - **Specialized agents** for different development tasks
            - **Real-time monitoring** and resource management
            - **Concurrent request handling** with intelligent load balancing
            
            ## Agent Types
            - **Router**: Ultra-fast request routing (Qwen2-1.5B)
            - **Architect**: System design and planning (Qwen2.5-32B)
            - **Primary Coder**: High-performance coding (Qwen2.5-Coder-7B)
            - **Secondary Coder**: Backup coding with MoE efficiency (DeepSeek-Coder-V2-16B)
            - **QA Checker**: Quality assurance and testing (Qwen2.5-14B)
            - **Debugger**: Error analysis and debugging (DeepSeek-Coder-V2-16B)
            
            ## Workflow Types
            - **Development**: Comprehensive development with full orchestration
            - **Quick Fix**: Rapid debugging and issue resolution
            - **Code Review**: Thorough code analysis and quality assessment
            """,
            routes=app.routes,
        )
        
        openapi_schema["info"]["x-logo"] = {
            "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
        }
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    app.openapi = custom_openapi
    
    return app


# Create the application
app = create_app()


# Application event handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with detailed error responses"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "HTTPException",
                "status_code": exc.status_code,
                "detail": exc.detail,
                "path": str(request.url),
                "method": request.method,
                "timestamp": asyncio.get_event_loop().time()
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "type": "InternalServerError",
                "status_code": 500,
                "detail": "Internal server error occurred",
                "path": str(request.url),
                "method": request.method,
                "timestamp": asyncio.get_event_loop().time()
            }
        }
    )


def run_server():
    """Run the server with uvicorn"""
    settings = get_settings()
    
    uvicorn.run(
        "llm_server.server.main:app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
        access_log=True
    )


if __name__ == "__main__":
    run_server()
