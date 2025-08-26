#!/usr/bin/env python3
"""
Embedding Service
Independent service for text embeddings with multiple model support
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import numpy as np
import uvicorn
import os
import sys
from pathlib import Path
import hashlib
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from apps.memory_server.core.lazy_graph.local_embeddings import FastLocalEmbeddings

app = FastAPI(title="Embedding Service", version="1.0.0")

# Service configuration
class EmbeddingRequest(BaseModel):
    texts: List[str]
    model: Optional[str] = "local-fast"
    normalize: bool = True

class EmbeddingResponse(BaseModel):
    embeddings: List[List[float]]
    model: str
    dimension: int

class ServiceStatus(BaseModel):
    status: str
    models_available: List[str]
    active_model: Optional[str]
    port: int
    total_requests: int

# Global state
class EmbeddingService:
    def __init__(self):
        self.models = {}
        self.active_model = None
        self.total_requests = 0
        self.port = int(os.getenv("EMBEDDING_PORT", "8002"))
        
        # Initialize available models
        self._init_models()
    
    def _init_models(self):
        """Initialize available embedding models"""
        # Local fast model (always available, no downloads)
        self.models["local-fast"] = FastLocalEmbeddings(dimension=384)
        
        # Local TF-IDF model (for fallback)
        self.models["local-tfidf"] = FastLocalEmbeddings(dimension=768)
        
        # Set default active model
        self.active_model = "local-fast"
        
        print(f"✅ Initialized {len(self.models)} embedding models")
        print(f"📍 Active model: {self.active_model}")
    
    def get_embeddings(self, texts: List[str], model: str = None) -> tuple:
        """Generate embeddings for texts"""
        model = model or self.active_model
        
        if model not in self.models:
            raise ValueError(f"Model {model} not available")
        
        self.total_requests += 1
        
        # Generate embeddings
        embeddings = self.models[model].encode(texts)
        
        return embeddings, model
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "status": "running",
            "models_available": list(self.models.keys()),
            "active_model": self.active_model,
            "port": self.port,
            "total_requests": self.total_requests
        }
    
    def switch_model(self, model_name: str):
        """Switch active model"""
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not available")
        
        self.active_model = model_name
        return True

# Initialize service
embedding_service = EmbeddingService()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Embedding Service",
        "version": "1.0.0",
        "endpoint": f"http://localhost:{embedding_service.port}",
        "docs": f"http://localhost:{embedding_service.port}/docs"
    }

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "service": "embedding"}

@app.get("/status", response_model=ServiceStatus)
async def status():
    """Get service status"""
    return embedding_service.get_status()

@app.post("/embed", response_model=EmbeddingResponse)
async def generate_embeddings(request: EmbeddingRequest):
    """Generate embeddings for texts"""
    try:
        embeddings, model_used = embedding_service.get_embeddings(
            request.texts, 
            request.model
        )
        
        # Convert numpy to list for JSON serialization
        embeddings_list = embeddings.tolist()
        
        return EmbeddingResponse(
            embeddings=embeddings_list,
            model=model_used,
            dimension=len(embeddings_list[0]) if embeddings_list else 0
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/model/switch")
async def switch_model(model_name: str):
    """Switch active embedding model"""
    try:
        embedding_service.switch_model(model_name)
        return {"success": True, "active_model": model_name}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/models")
async def list_models():
    """List available models"""
    return {
        "models": list(embedding_service.models.keys()),
        "active": embedding_service.active_model
    }

if __name__ == "__main__":
    port = int(os.getenv("EMBEDDING_PORT", "8002"))
    print(f"""
╔══════════════════════════════════════╗
║       EMBEDDING SERVICE v1.0         ║
╠══════════════════════════════════════╣
║ Port: {port:31} ║
║ Models: local-fast, local-tfidf      ║
║ No external downloads required       ║
╚══════════════════════════════════════╝
    """)
    
    uvicorn.run(app, host="0.0.0.0", port=port)