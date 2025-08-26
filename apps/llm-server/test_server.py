#!/usr/bin/env python3
"""
Simple test server to verify FastAPI and models work
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
import os
from pathlib import Path

# Create FastAPI app
app = FastAPI(
    title="LLM Test Server",
    description="Simple test server for AI models",
    version="0.1.0"
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "LLM Test Server Running",
        "status": "ok", 
        "models_available": check_models()
    }

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "server": "running"}

@app.post("/v1/chat/completions")
async def openai_chat_completions(request: dict):
    """OpenAI-compatible chat completions endpoint"""
    return JSONResponse({
        "id": "test-response",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "qwen2.5-coder-7b",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant", 
                "content": "Hello! This is a test response from the LLM server."
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 15,
            "total_tokens": 25
        }
    })

def check_models():
    """Check which models are available"""
    models_dir = Path("./models")
    available_models = []
    
    if models_dir.exists():
        for model_file in models_dir.glob("*.gguf"):
            available_models.append(model_file.name)
    
    return available_models

if __name__ == "__main__":
    print("🚀 Starting LLM Test Server...")
    uvicorn.run(
        app,
        host="localhost",
        port=8000,
        log_level="info"
    )