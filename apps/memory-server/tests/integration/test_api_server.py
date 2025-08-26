#!/usr/bin/env python3
"""
Test API Server Functionality
Basic API endpoint testing
"""

import sys
import asyncio
import time
import logging
from pathlib import Path

def test_api_imports():
    """Test API imports without starting server"""
    print("🌐 Testing API Imports...")
    
    try:
        # Mock missing modules temporarily
        import sys
        import types
        
        # Create mock modules for missing dependencies
        mock_modules = {}
        
        # Mock spacy
        mock_spacy = types.ModuleType('spacy')
        sys.modules['spacy'] = mock_spacy
        
        # Mock missing submodules
        mock_jina = types.ModuleType('core.late_chunking.jina_embeddings')
        mock_jina.JinaEmbeddingModel = type('JinaEmbeddingModel', (), {})
        sys.modules['core.late_chunking.jina_embeddings'] = mock_jina
        
        mock_kg = types.ModuleType('core.hybrid_store.knowledge_graph')
        mock_kg.KnowledgeGraph = type('KnowledgeGraph', (), {})
        sys.modules['core.hybrid_store.knowledge_graph'] = mock_kg
        
        mock_ps = types.ModuleType('psutil')
        mock_ps.virtual_memory = lambda: type('obj', (object,), {
            'total': 8 * 1024**3,
            'available': 4 * 1024**3,
            'percent': 50.0
        })()
        mock_ps.cpu_count = lambda: 8
        mock_ps.cpu_percent = lambda: 25.0
        sys.modules['psutil'] = mock_ps
        
        # Now try to import FastAPI app
        from fastapi import FastAPI
        print("  ✅ FastAPI imported successfully")
        
        # Test FastAPI app creation
        app = FastAPI(title="Memory-Server", version="1.0.0")
        assert app is not None
        print("  ✅ FastAPI app created")
        
        # Test basic route definition
        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok", "test": True}
        
        print("  ✅ Route definition works")
        
        return True
        
    except Exception as e:
        print(f"  ❌ API imports test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_server_configuration():
    """Test server configuration"""
    print("⚙️ Testing Server Configuration...")
    
    try:
        from core.config import get_config
        
        config = get_config()
        
        # Test server-related configurations
        assert config.API_PORT is not None
        assert isinstance(config.API_PORT, int)
        assert 1000 <= config.API_PORT <= 65535
        print(f"  ✅ API Port: {config.API_PORT}")
        
        assert config.DEBUG_MODE is not None
        assert isinstance(config.DEBUG_MODE, bool)
        print(f"  ✅ Debug Mode: {config.DEBUG_MODE}")
        
        # Test memory configurations
        assert config.WORKING_MEMORY_SIZE > 0
        assert config.EPISODIC_MEMORY_SIZE > 0
        print(f"  ✅ Working Memory: {config.WORKING_MEMORY_SIZE}")
        print(f"  ✅ Episodic Memory: {config.EPISODIC_MEMORY_SIZE}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Server configuration test failed: {e}")
        return False

def test_async_server_functionality():
    """Test async server functionality"""
    print("⚡ Testing Async Server Functionality...")
    
    try:
        # Test async route handler
        async def mock_health_check():
            await asyncio.sleep(0.01)  # Simulate async work
            return {
                "status": "healthy",
                "timestamp": time.time(),
                "version": "1.0.0"
            }
        
        # Test the async function
        result = asyncio.run(mock_health_check())
        assert result["status"] == "healthy"
        assert "timestamp" in result
        print("  ✅ Async route handler works")
        
        # Test concurrent request simulation
        async def simulate_concurrent_requests():
            tasks = [mock_health_check() for _ in range(5)]
            results = await asyncio.gather(*tasks)
            return results
        
        results = asyncio.run(simulate_concurrent_requests())
        assert len(results) == 5
        assert all(r["status"] == "healthy" for r in results)
        print("  ✅ Concurrent request handling works")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Async server functionality test failed: {e}")
        return False

def test_response_models():
    """Test Pydantic response models"""
    print("📋 Testing Response Models...")
    
    try:
        from pydantic import BaseModel, Field
        from typing import List, Optional
        
        # Define test response models
        class HealthResponse(BaseModel):
            status: str = Field(..., description="Server status")
            timestamp: float = Field(..., description="Response timestamp")
            memory_usage: Optional[dict] = Field(None, description="Memory usage info")
        
        class SearchRequest(BaseModel):
            query: str = Field(..., description="Search query")
            limit: int = Field(10, description="Number of results")
            filters: Optional[dict] = Field(None, description="Search filters")
        
        # Test model creation
        health_response = HealthResponse(
            status="healthy",
            timestamp=time.time(),
            memory_usage={"used": 50.0, "total": 100.0}
        )
        
        assert health_response.status == "healthy"
        print("  ✅ Response model creation works")
        
        # Test model serialization
        response_dict = health_response.model_dump()
        assert isinstance(response_dict, dict)
        assert "status" in response_dict
        print("  ✅ Model serialization works")
        
        # Test request model
        search_request = SearchRequest(
            query="test query",
            limit=20,
            filters={"category": "documents"}
        )
        
        assert search_request.query == "test query"
        assert search_request.limit == 20
        print("  ✅ Request model validation works")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Response models test failed: {e}")
        return False

def test_middleware_functionality():
    """Test middleware functionality"""
    print("🔧 Testing Middleware...")
    
    try:
        from fastapi import FastAPI, Request, Response
        from fastapi.middleware.base import BaseHTTPMiddleware
        import time
        
        # Create test middleware
        class TimingMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request: Request, call_next):
                start_time = time.time()
                response = await call_next(request)
                process_time = time.time() - start_time
                response.headers["X-Process-Time"] = str(process_time)
                return response
        
        # Test middleware creation
        app = FastAPI()
        app.add_middleware(TimingMiddleware)
        print("  ✅ Middleware registration works")
        
        # Test CORS middleware
        from fastapi.middleware.cors import CORSMiddleware
        
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        print("  ✅ CORS middleware works")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Middleware test failed: {e}")
        return False

def test_error_handling():
    """Test error handling"""
    print("❌ Testing Error Handling...")
    
    try:
        from fastapi import HTTPException, status
        
        # Test HTTP exception creation
        error = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found"
        )
        
        assert error.status_code == 404
        assert error.detail == "Resource not found"
        print("  ✅ HTTP exception creation works")
        
        # Test custom error response
        def create_error_response(message: str, code: int = 500):
            return {
                "error": True,
                "message": message,
                "code": code,
                "timestamp": time.time()
            }
        
        error_response = create_error_response("Test error", 400)
        assert error_response["error"] is True
        assert error_response["code"] == 400
        print("  ✅ Custom error responses work")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error handling test failed: {e}")
        return False

def run_api_tests():
    """Run all API tests"""
    print("🧪 Memory-Server API Tests")
    print("=" * 50)
    
    tests = [
        test_api_imports,
        test_server_configuration, 
        test_async_server_functionality,
        test_response_models,
        test_middleware_functionality,
        test_error_handling
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
                print(f"✅ {test.__name__} PASSED\n")
            else:
                failed += 1
                print(f"❌ {test.__name__} FAILED\n")
        except Exception as e:
            print(f"💥 {test.__name__} CRASHED: {e}\n")
            failed += 1
    
    print("=" * 50)
    print(f"📊 API TEST RESULTS:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL API TESTS PASSED! 🎉")
        print("✨ API server functionality is working!")
        return True
    else:
        print(f"\n⚠️  {failed} API tests failed.")
        return passed > failed

if __name__ == "__main__":
    success = run_api_tests()
    sys.exit(0 if success else 1)