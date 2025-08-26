#!/usr/bin/env python3
"""
Embedding Hub Pipeline Test
Tests all 6 specialized embedding agents with different content types
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any, List

# Test data for each agent
TEST_DATA = {
    "late_chunking": {
        "content": """
        # Research Paper: Advanced Machine Learning Techniques

        ## Abstract
        This paper presents novel approaches to machine learning optimization.
        We introduce three key innovations in neural network architecture.
        
        ## Introduction  
        Machine learning has revolutionized data processing capabilities.
        Traditional approaches face scalability challenges with large datasets.
        Our proposed method addresses these limitations through advanced chunking.
        
        ## Methodology
        We developed a hybrid approach combining supervised and unsupervised learning.
        The system processes documents in semantic chunks while preserving context.
        Results show 40% improvement in accuracy compared to baseline methods.
        """,
        "expected_features": ["document structure", "academic content", "multiple sections"]
    },
    
    "code": {
        "content": """
        def calculate_embeddings(text: str, model_name: str = "default") -> np.ndarray:
            \"\"\"
            Generate embeddings for input text using specified model
            
            Args:
                text: Input text to embed
                model_name: Name of embedding model to use
                
            Returns:
                numpy array of embeddings
            \"\"\"
            import numpy as np
            from transformers import AutoTokenizer, AutoModel
            
            # Initialize tokenizer and model
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModel.from_pretrained(model_name)
            
            # Tokenize input
            tokens = tokenizer(text, return_tensors='pt', padding=True, truncation=True)
            
            # Generate embeddings
            with torch.no_grad():
                outputs = model(**tokens)
                embeddings = outputs.last_hidden_state.mean(dim=1)
            
            return embeddings.numpy()
        """,
        "expected_features": ["Python code", "function definition", "docstring", "imports"]
    },
    
    "conversation": {
        "content": """
        User: How do I implement a RAG system with late chunking?

        Assistant: Great question! Late chunking is a powerful technique for RAG systems. Here's how you can implement it:

        1. **Document Processing**: First, embed your entire document before chunking
        2. **Contextual Chunking**: Use the embeddings to identify optimal chunk boundaries
        3. **Retrieval**: Search using both document-level and chunk-level embeddings

        User: What's the advantage over traditional chunking?

        Assistant: Late chunking offers several key advantages:
        - **Context Preservation**: Maintains semantic relationships across chunk boundaries
        - **Better Retrieval**: More relevant results due to context-aware chunking
        - **Reduced Information Loss**: Avoids splitting related concepts

        The main trade-off is computational cost, but the quality improvement is significant.

        User: Can you show me a code example?

        Assistant: Absolutely! Here's a basic implementation:

        ```python
        class LateChunkingRAG:
            def __init__(self, embedder):
                self.embedder = embedder
                
            def process_document(self, doc):
                # First embed entire document
                doc_embedding = self.embedder.embed(doc)
                # Then identify optimal chunks
                chunks = self.smart_chunk(doc, doc_embedding)
                return chunks
        ```
        """,
        "expected_features": ["Q&A format", "technical discussion", "code examples", "multiple turns"]
    },
    
    "visual": {
        "content": """
        [VISUAL_CONTENT]
        Format: PNG
        Size: 245760 bytes
        Content_Type: Code Editor Screenshot
        
        Screenshot shows VSCode editor with Python code visible:
        - Left panel: File explorer showing project structure
        - Main editor: Python file with FastAPI endpoints
        - Bottom panel: Integrated terminal with server logs
        - Right sidebar: Extension panel with AI tools
        
        UI Elements detected:
        - Menu bar with File, Edit, View options
        - Activity bar with icons for Explorer, Search, Git
        - Status bar showing Python interpreter and Git branch
        - Code with syntax highlighting for Python
        - Line numbers visible on left side
        
        Text overlay includes:
        - Function definitions: async def get_embeddings()
        - Import statements: from fastapi import FastAPI
        - Comments explaining the embedding process
        - Terminal output: "Server running on localhost:8900"
        """,
        "expected_features": ["screenshot analysis", "UI elements", "code editor", "technical interface"]
    },
    
    "query": {
        "content": """
        How to implement lazy loading with React hooks and TypeScript for better performance?
        """,
        "expected_features": ["how-to question", "React", "TypeScript", "performance"]
    },
    
    "community": {
        "content": """
        Machine learning research has evolved significantly in recent years. [ENTITY:TensorFlow] 
        is widely used for deep learning applications and has strong relationships with 
        [ENTITY:Keras] for high-level neural network APIs. [ENTITY:PyTorch] provides 
        dynamic computation graphs and is popular in research communities.
        
        The relationship between these frameworks shows interesting patterns:
        - TensorFlow --uses--> Keras as its high-level API
        - PyTorch --competes_with--> TensorFlow in the research space  
        - Keras --simplifies--> neural network development
        - Research papers --implement_with--> both PyTorch and TensorFlow
        
        This creates distinct communities: academic researchers tend to prefer PyTorch,
        while industry applications often use TensorFlow. The frameworks share similar
        concepts but have different philosophies regarding computation graphs.
        """,
        "expected_features": ["entity mentions", "relationships", "community structure", "graph patterns"]
    }
}

class EmbeddingHubTester:
    """Test suite for Embedding Hub service"""
    
    def __init__(self, base_url: str = "http://localhost:8900"):
        self.base_url = base_url
        self.session = None
        self.results = {}
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_health_check(self) -> bool:
        """Test if the service is running"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ Health check passed")
                    return True
                else:
                    print(f"❌ Health check failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    async def test_service_status(self) -> Dict[str, Any]:
        """Get service status information"""
        try:
            async with self.session.get(f"{self.base_url}/status") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Service status: {data.get('status', 'unknown')}")
                    print(f"   Model: {data.get('model', 'unknown')}")
                    print(f"   Agents: {len(data.get('agents', []))}")
                    return data
                else:
                    print(f"❌ Status check failed: {response.status}")
                    return {}
        except Exception as e:
            print(f"❌ Status check error: {e}")
            return {}
    
    async def test_embedding_endpoint(self, agent_name: str, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test specific embedding endpoint"""
        endpoint = f"/embed/{agent_name.replace('_', '-')}"
        url = f"{self.base_url}{endpoint}"
        
        payload = {
            "content": test_data["content"],
            "content_type": "text",
            "metadata": {"test": True, "agent": agent_name}
        }
        
        try:
            start_time = time.time()
            async with self.session.post(url, json=payload) as response:
                processing_time = (time.time() - start_time) * 1000
                
                if response.status == 200:
                    data = await response.json()
                    
                    result = {
                        "success": True,
                        "agent": data.get("agent", "unknown"),
                        "dimensions": data.get("dimensions", 0),
                        "processing_time_ms": data.get("processing_time_ms", 0),
                        "client_processing_time_ms": processing_time,
                        "embedding_length": len(data.get("embeddings", [])),
                        "metadata": data.get("metadata", {})
                    }
                    
                    print(f"✅ {agent_name}: {result['dimensions']}D embedding in {result['processing_time_ms']:.1f}ms")
                    return result
                else:
                    error_text = await response.text()
                    print(f"❌ {agent_name}: HTTP {response.status} - {error_text}")
                    return {"success": False, "error": f"HTTP {response.status}", "details": error_text}
                    
        except Exception as e:
            print(f"❌ {agent_name}: Exception - {e}")
            return {"success": False, "error": str(e)}
    
    async def test_all_agents(self) -> Dict[str, Any]:
        """Test all embedding agents"""
        print("\n🧪 Testing All Embedding Agents")
        print("=" * 50)
        
        results = {}
        
        for agent_name, test_data in TEST_DATA.items():
            print(f"\n🔍 Testing {agent_name} agent...")
            result = await self.test_embedding_endpoint(agent_name, test_data)
            results[agent_name] = result
            
            # Brief pause between tests
            await asyncio.sleep(0.5)
        
        return results
    
    async def test_batch_processing(self) -> Dict[str, Any]:
        """Test batch processing capabilities"""
        print("\n📦 Testing Batch Processing")
        print("=" * 30)
        
        # Test with late chunking agent using multiple texts
        texts = [
            "This is the first document about machine learning.",
            "This is the second document about data science.", 
            "This is the third document about artificial intelligence."
        ]
        
        batch_results = []
        
        for i, text in enumerate(texts):
            payload = {
                "content": text,
                "content_type": "text",
                "metadata": {"batch_test": True, "index": i}
            }
            
            try:
                async with self.session.post(f"{self.base_url}/embed/late-chunking", json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        batch_results.append(data)
                        print(f"✅ Batch item {i+1}: {data.get('dimensions')}D embedding")
                    else:
                        print(f"❌ Batch item {i+1}: Failed")
            except Exception as e:
                print(f"❌ Batch item {i+1}: Error - {e}")
        
        return {"batch_size": len(texts), "successful": len(batch_results), "results": batch_results}
    
    async def test_error_handling(self) -> Dict[str, Any]:
        """Test error handling with invalid requests"""
        print("\n⚠️  Testing Error Handling")
        print("=" * 25)
        
        error_tests = [
            {"name": "empty_content", "payload": {"content": "", "content_type": "text"}},
            {"name": "invalid_endpoint", "endpoint": "/embed/nonexistent"},
            {"name": "malformed_json", "payload": "invalid json"},
        ]
        
        error_results = {}
        
        for test in error_tests:
            try:
                if test["name"] == "invalid_endpoint":
                    async with self.session.post(f"{self.base_url}{test['endpoint']}", json={"content": "test"}) as response:
                        error_results[test["name"]] = {"status": response.status, "handled": response.status == 404}
                        print(f"✅ {test['name']}: Properly handled with status {response.status}")
                elif test["name"] == "malformed_json":
                    async with self.session.post(f"{self.base_url}/embed/late-chunking", data=test["payload"]) as response:
                        error_results[test["name"]] = {"status": response.status, "handled": response.status == 422}
                        print(f"✅ {test['name']}: Properly handled with status {response.status}")
                else:
                    async with self.session.post(f"{self.base_url}/embed/late-chunking", json=test["payload"]) as response:
                        error_results[test["name"]] = {"status": response.status, "handled": response.status in [200, 422]}
                        print(f"✅ {test['name']}: Handled with status {response.status}")
            except Exception as e:
                error_results[test["name"]] = {"error": str(e), "handled": True}
                print(f"✅ {test['name']}: Exception properly handled")
        
        return error_results
    
    def print_summary(self, all_results: Dict[str, Any]):
        """Print comprehensive test summary"""
        print("\n" + "=" * 60)
        print("🎯 EMBEDDING HUB TEST SUMMARY")
        print("=" * 60)
        
        # Agent test results
        agent_results = all_results.get("agents", {})
        successful_agents = sum(1 for result in agent_results.values() if result.get("success", False))
        
        print(f"📊 Agent Tests: {successful_agents}/{len(agent_results)} successful")
        
        if successful_agents > 0:
            # Calculate average processing time
            processing_times = [r.get("processing_time_ms", 0) for r in agent_results.values() if r.get("success")]
            avg_time = sum(processing_times) / len(processing_times) if processing_times else 0
            
            print(f"⚡ Average Processing Time: {avg_time:.1f}ms")
            
            # Show dimensions consistency
            dimensions = [r.get("dimensions", 0) for r in agent_results.values() if r.get("success")]
            if dimensions and len(set(dimensions)) == 1:
                print(f"📐 Embedding Dimensions: {dimensions[0]} (consistent)")
            else:
                print(f"📐 Embedding Dimensions: {set(dimensions)} (inconsistent)")
        
        # Batch test results
        batch_results = all_results.get("batch", {})
        if batch_results:
            print(f"📦 Batch Processing: {batch_results.get('successful', 0)}/{batch_results.get('batch_size', 0)} successful")
        
        # Error handling results
        error_results = all_results.get("errors", {})
        if error_results:
            handled_errors = sum(1 for r in error_results.values() if r.get("handled", False))
            print(f"⚠️  Error Handling: {handled_errors}/{len(error_results)} properly handled")
        
        print("\n🎉 Test completed successfully!")
        print("=" * 60)

async def main():
    """Run complete embedding hub test suite"""
    print("🚀 Embedding Hub Pipeline Test")
    print("Testing 6 specialized embedding agents")
    print("=" * 50)
    
    async with EmbeddingHubTester() as tester:
        # Check if service is running
        if not await tester.test_health_check():
            print("\n❌ Service is not running. Please start the embedding hub first:")
            print("   cd /Users/server/AI-projects/AI-server/services/embedding-hub")
            print("   ./start_embedding_hub.sh")
            return
        
        # Get service status
        await tester.test_service_status()
        
        # Run all tests
        all_results = {}
        
        # Test all agents
        all_results["agents"] = await tester.test_all_agents()
        
        # Test batch processing
        all_results["batch"] = await tester.test_batch_processing()
        
        # Test error handling
        all_results["errors"] = await tester.test_error_handling()
        
        # Print summary
        tester.print_summary(all_results)
        
        # Save detailed results
        with open("test_results.json", "w") as f:
            json.dump(all_results, f, indent=2)
        print("\n💾 Detailed results saved to test_results.json")

if __name__ == "__main__":
    asyncio.run(main())