#!/usr/bin/env python3
"""
Embedding Hub Service
Single Nomic Multimodal 7B model with 6 specialized preprocessing agents

Architecture:
- Hub-Spoke pattern with centralized model
- 6 specialized preprocessing agents
- Queue-based request handling
- YAML-driven configuration
"""

import asyncio
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
import time
import json
import logging
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Preprocessing modules
from preprocessing.late_chunking import LatechunkingPreprocessor
from preprocessing.code import CodePreprocessor  
from preprocessing.conversation import ConversationPreprocessor
from preprocessing.visual import VisualPreprocessor
from preprocessing.query import QueryPreprocessor
from preprocessing.community import CommunityPreprocessor

# Mock embedding model (replace with actual Nomic when available)
from core.mock_nomic import MockNomicMultimodal

# =============================================================================
# CONFIGURATION AND MODELS
# =============================================================================

@dataclass
class EmbeddingRequest:
    """Request for embedding generation"""
    content: Union[str, bytes]
    content_type: str = "text"
    metadata: Dict[str, Any] = None
    
@dataclass 
class EmbeddingResponse:
    """Response from embedding generation"""
    embeddings: List[float]
    dimensions: int
    agent: str
    processing_time_ms: float
    metadata: Dict[str, Any] = None

class APIRequest(BaseModel):
    content: str = Field(..., description="Content to embed")
    content_type: str = Field(default="text", description="Type of content")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

class APIResponse(BaseModel):
    embeddings: List[float] = Field(..., description="Generated embeddings")
    dimensions: int = Field(..., description="Embedding dimensions") 
    agent: str = Field(..., description="Processing agent used")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Response metadata")

# =============================================================================
# EMBEDDING HUB SERVICE
# =============================================================================

class EmbeddingHubService:
    """Central embedding hub with specialized agents"""
    
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.model = None
        self.agents = {}
        self.request_queue = asyncio.Queue()
        self.stats = {
            "requests_processed": 0,
            "total_processing_time": 0.0,
            "agents_used": {},
            "errors": 0,
            "start_time": datetime.now()
        }
        
        # Setup logging
        self._setup_logging()
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load YAML configuration"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logging.info(f"Loaded configuration from {config_path}")
            return config
        except Exception as e:
            logging.error(f"Failed to load config: {e}")
            raise
            
    def _setup_logging(self):
        """Setup structured logging"""
        log_config = self.config.get('logging', {})
        
        logging.basicConfig(
            level=getattr(logging, log_config.get('level', 'INFO')),
            format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
        )
        
        self.logger = logging.getLogger('embedding-hub')
        
    async def initialize(self):
        """Initialize model and agents"""
        self.logger.info("Initializing Embedding Hub Service")
        
        # Initialize model
        await self._initialize_model()
        
        # Initialize specialized agents
        await self._initialize_agents()
        
        self.logger.info("Embedding Hub Service initialized successfully")
        
    async def _initialize_model(self):
        """Initialize the Nomic Multimodal 7B model"""
        model_config = self.config['model']
        
        self.logger.info(f"Loading model: {model_config['name']}")
        
        try:
            # Use mock model for now (replace with actual Nomic when available)
            self.model = MockNomicMultimodal(
                dimensions=model_config['dimensions'],
                device=model_config['device']
            )
            
            await self.model.initialize()
            
            self.logger.info(f"Model loaded successfully - {model_config['size_gb']}GB")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize model: {e}")
            raise
            
    async def _initialize_agents(self):
        """Initialize specialized preprocessing agents"""
        agents_config = self.config['agents']
        
        # Agent mappings
        agent_classes = {
            'late_chunking': LatechunkingPreprocessor,
            'code_embedding': CodePreprocessor,
            'conversation_embedding': ConversationPreprocessor, 
            'visual_embedding': VisualPreprocessor,
            'query_retrieval': QueryPreprocessor,
            'community_detection': CommunityPreprocessor
        }
        
        for agent_name, agent_config in agents_config.items():
            try:
                if agent_name in agent_classes:
                    agent_class = agent_classes[agent_name]
                    agent = agent_class(agent_config)
                    self.agents[agent_name] = agent
                    
                    self.logger.info(f"Initialized agent: {agent_name} -> {agent_config['endpoint']}")
                    
            except Exception as e:
                self.logger.error(f"Failed to initialize agent {agent_name}: {e}")
                
    async def generate_embeddings(self, request: EmbeddingRequest, agent_name: str) -> EmbeddingResponse:
        """Generate embeddings using specified agent"""
        start_time = time.time()
        
        try:
            # Get agent
            if agent_name not in self.agents:
                raise ValueError(f"Unknown agent: {agent_name}")
                
            agent = self.agents[agent_name]
            
            # Preprocess content
            preprocessed_content = await agent.preprocess(request.content, request.metadata or {})
            
            # Generate embeddings using the model
            embeddings = await self.model.embed(preprocessed_content)
            
            # Calculate processing time
            processing_time = (time.time() - start_time) * 1000
            
            # Update statistics
            self.stats["requests_processed"] += 1
            self.stats["total_processing_time"] += processing_time
            self.stats["agents_used"][agent_name] = self.stats["agents_used"].get(agent_name, 0) + 1
            
            response = EmbeddingResponse(
                embeddings=embeddings.tolist(),
                dimensions=len(embeddings),
                agent=agent_name,
                processing_time_ms=processing_time,
                metadata={"preprocessor": agent.__class__.__name__}
            )
            
            self.logger.info(f"Generated embeddings - Agent: {agent_name}, Time: {processing_time:.2f}ms")
            
            return response
            
        except Exception as e:
            self.stats["errors"] += 1
            self.logger.error(f"Error generating embeddings with {agent_name}: {e}")
            raise
            
    def get_service_status(self) -> Dict[str, Any]:
        """Get comprehensive service status"""
        uptime = (datetime.now() - self.stats["start_time"]).total_seconds()
        
        avg_processing_time = (
            self.stats["total_processing_time"] / max(self.stats["requests_processed"], 1)
        )
        
        return {
            "service": "embedding-hub",
            "status": "running",
            "model": self.config['model']['name'],
            "agents": list(self.agents.keys()),
            "uptime_seconds": uptime,
            "statistics": {
                "requests_processed": self.stats["requests_processed"],
                "average_processing_time_ms": avg_processing_time,
                "agents_usage": self.stats["agents_used"],
                "error_count": self.stats["errors"],
                "requests_per_second": self.stats["requests_processed"] / max(uptime, 1)
            }
        }

# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

# Initialize service
config_path = Path(__file__).parent / "config.yaml"
embedding_hub = EmbeddingHubService(str(config_path))

# FastAPI app
app = FastAPI(
    title="Embedding Hub Service",
    description="Centralized embedding service with specialized preprocessing agents",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8800"],  # Memory-Server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    await embedding_hub.initialize()

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Embedding Hub",
        "version": "1.0.0",
        "model": embedding_hub.config['model']['name'],
        "agents": len(embedding_hub.agents),
        "endpoints": {
            "late_chunking": "/embed/late-chunking",
            "code": "/embed/code", 
            "conversation": "/embed/conversation",
            "visual": "/embed/visual",
            "query": "/embed/query",
            "community": "/embed/community"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/status")
async def get_status():
    """Comprehensive service status"""
    return embedding_hub.get_service_status()

# =============================================================================
# SPECIALIZED AGENT ENDPOINTS
# =============================================================================

@app.post("/embed/late-chunking", response_model=APIResponse)
async def late_chunking_embeddings(request: APIRequest):
    """Late Chunking specialist - embeddings before chunking"""
    embedding_request = EmbeddingRequest(
        content=request.content,
        content_type=request.content_type,
        metadata=request.metadata
    )
    
    result = await embedding_hub.generate_embeddings(embedding_request, "late_chunking")
    
    return APIResponse(
        embeddings=result.embeddings,
        dimensions=result.dimensions,
        agent=result.agent,
        processing_time_ms=result.processing_time_ms,
        metadata=result.metadata
    )

@app.post("/embed/code", response_model=APIResponse)
async def code_embeddings(request: APIRequest):
    """Code specialist - syntax and programming concepts"""
    embedding_request = EmbeddingRequest(
        content=request.content,
        content_type=request.content_type,
        metadata=request.metadata
    )
    
    result = await embedding_hub.generate_embeddings(embedding_request, "code_embedding")
    
    return APIResponse(
        embeddings=result.embeddings,
        dimensions=result.dimensions,
        agent=result.agent,
        processing_time_ms=result.processing_time_ms,
        metadata=result.metadata
    )

@app.post("/embed/conversation", response_model=APIResponse)
async def conversation_embeddings(request: APIRequest):
    """Conversation specialist - dialogue and chat context"""
    embedding_request = EmbeddingRequest(
        content=request.content,
        content_type=request.content_type,
        metadata=request.metadata
    )
    
    result = await embedding_hub.generate_embeddings(embedding_request, "conversation_embedding")
    
    return APIResponse(
        embeddings=result.embeddings,
        dimensions=result.dimensions,
        agent=result.agent,
        processing_time_ms=result.processing_time_ms,
        metadata=result.metadata
    )

@app.post("/embed/visual", response_model=APIResponse)
async def visual_embeddings(request: APIRequest):
    """Visual specialist - screenshots and UI content"""
    embedding_request = EmbeddingRequest(
        content=request.content,
        content_type=request.content_type,
        metadata=request.metadata
    )
    
    result = await embedding_hub.generate_embeddings(embedding_request, "visual_embedding")
    
    return APIResponse(
        embeddings=result.embeddings,
        dimensions=result.dimensions,
        agent=result.agent,
        processing_time_ms=result.processing_time_ms,
        metadata=result.metadata
    )

@app.post("/embed/query", response_model=APIResponse)
async def query_embeddings(request: APIRequest):
    """Query specialist - search and retrieval optimization"""
    embedding_request = EmbeddingRequest(
        content=request.content,
        content_type=request.content_type,
        metadata=request.metadata
    )
    
    result = await embedding_hub.generate_embeddings(embedding_request, "query_retrieval")
    
    return APIResponse(
        embeddings=result.embeddings,
        dimensions=result.dimensions,
        agent=result.agent,
        processing_time_ms=result.processing_time_ms,
        metadata=result.metadata
    )

@app.post("/embed/community", response_model=APIResponse)
async def community_embeddings(request: APIRequest):
    """Community detection specialist - graph clustering"""
    embedding_request = EmbeddingRequest(
        content=request.content,
        content_type=request.content_type,
        metadata=request.metadata
    )
    
    result = await embedding_hub.generate_embeddings(embedding_request, "community_detection")
    
    return APIResponse(
        embeddings=result.embeddings,
        dimensions=result.dimensions,
        agent=result.agent,
        processing_time_ms=result.processing_time_ms,
        metadata=result.metadata
    )

# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    port = embedding_hub.config['service']['port']
    
    print(f"""
╔══════════════════════════════════════════════════╗
║            EMBEDDING HUB SERVICE v1.0            ║
╠══════════════════════════════════════════════════╣
║ Model: Nomic Multimodal 7B                       ║
║ Port: {port:42} ║
║ Agents: 6 specialized preprocessors              ║
║                                                  ║
║ Endpoints:                                       ║
║ • /embed/late-chunking (8901)                   ║
║ • /embed/code (8902)                             ║
║ • /embed/conversation (8903)                     ║
║ • /embed/visual (8904)                           ║
║ • /embed/query (8905)                            ║
║ • /embed/community (8906)                        ║
╚══════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        app, 
        host=embedding_hub.config['service']['host'],
        port=port,
        log_level="info"
    )