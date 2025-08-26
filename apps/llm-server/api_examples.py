#!/usr/bin/env python3
"""
API Examples for Enhanced LLM Server with RAG
Demonstrates all new advanced features
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_basic_chat():
    """Test basic chat functionality"""
    print("🔥 Testing Basic Chat...")
    
    response = requests.post(f"{BASE_URL}/v1/chat/completions", json={
        "model": "qwen2.5-32b-instruct",
        "messages": [
            {"role": "user", "content": "What is the capital of France?"}
        ],
        "temperature": 0.7,
        "max_tokens": 100
    })
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Response: {result['choices'][0]['message']['content']}")
        print(f"⚡ Speed: {result['system_info']['tokens_per_second']} t/s")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")

def test_rag_enhanced_chat():
    """Test RAG-enhanced chat"""
    print("\n🧠 Testing RAG-Enhanced Chat...")
    
    response = requests.post(f"{BASE_URL}/v1/chat/completions", json={
        "model": "qwen2.5-32b-instruct",
        "messages": [
            {"role": "user", "content": "Explain quantum computing and its applications"}
        ],
        "temperature": 0.7,
        "max_tokens": 300,
        "use_rag": True,
        "use_memory": True,
        "rag_k": 5
    })
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Response: {result['choices'][0]['message']['content'][:200]}...")
        print(f"🔍 RAG Used: {result['system_info']['rag_used']}")
        print(f"🧠 Memory Used: {result['system_info']['memory_used']}")
        print(f"⚡ Speed: {result['system_info']['tokens_per_second']} t/s")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")

def test_corag_chains():
    """Test CoRAG chain-of-retrieval"""
    print("\n🔗 Testing CoRAG Chain-of-Retrieval...")
    
    response = requests.post(f"{BASE_URL}/v1/chat/completions", json={
        "model": "qwen2.5-32b-instruct",
        "messages": [
            {"role": "user", "content": "How do neural networks learn and what are the latest advances in deep learning architectures?"}
        ],
        "temperature": 0.7,
        "max_tokens": 500,
        "use_rag": True,
        "use_corag": True,
        "use_memory": True
    })
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Response: {result['choices'][0]['message']['content'][:200]}...")
        print(f"🔗 CoRAG Used: {result['system_info']['corag_used']}")
        print(f"🔍 RAG Used: {result['system_info']['rag_used']}")
        print(f"⚡ Speed: {result['system_info']['tokens_per_second']} t/s")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")

def test_reasoning_mode():
    """Test reasoning mode with RAG"""
    print("\n🤔 Testing Reasoning Mode with RAG...")
    
    response = requests.post(f"{BASE_URL}/v1/chat/completions", json={
        "model": "qwen2.5-32b-instruct",
        "messages": [
            {"role": "user", "content": "Compare the efficiency of different sorting algorithms and explain when to use each one."}
        ],
        "temperature": 0.7,
        "max_tokens": 600,
        "reasoning": True,
        "use_rag": True,
        "use_memory": True
    })
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Response: {result['choices'][0]['message']['content'][:300]}...")
        print(f"🤔 Reasoning: {result['system_info']['reasoning_enabled']}")
        print(f"🔍 RAG Used: {result['system_info']['rag_used']}")
        print(f"⚡ Speed: {result['system_info']['tokens_per_second']} t/s")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")

def test_agent_mode():
    """Test agent mode with RAG"""
    print("\n🤖 Testing Agent Mode with RAG...")
    
    response = requests.post(f"{BASE_URL}/v1/chat/completions", json={
        "model": "qwen2.5-32b-instruct",
        "messages": [
            {"role": "user", "content": "Help me optimize a Python web scraper. I need to make it faster and more reliable."}
        ],
        "temperature": 0.7,
        "max_tokens": 800,
        "mode": "agent",
        "use_rag": True,
        "use_memory": True,
        "reasoning": True
    })
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Response: {result['choices'][0]['message']['content'][:300]}...")
        print(f"🤖 Mode: agent")
        print(f"🤔 Reasoning: {result['system_info']['reasoning_enabled']}")
        print(f"🔍 RAG Used: {result['system_info']['rag_used']}")
        print(f"⚡ Speed: {result['system_info']['tokens_per_second']} t/s")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")

def test_streaming():
    """Test streaming response"""
    print("\n📡 Testing Streaming Response...")
    
    response = requests.post(f"{BASE_URL}/v1/chat/completions", json={
        "model": "qwen2.5-32b-instruct",
        "messages": [
            {"role": "user", "content": "Write a short story about AI and humans working together"}
        ],
        "temperature": 0.8,
        "max_tokens": 400,
        "stream": True,
        "use_rag": True
    }, stream=True)
    
    if response.status_code == 200:
        print("✅ Streaming response:")
        for line in response.iter_lines():
            if line:
                print(line.decode('utf-8')[:100] + "...")
                break  # Just show first chunk
    else:
        print(f"❌ Error: {response.status_code}")

def test_server_status():
    """Test server status and capabilities"""
    print("\n📊 Testing Server Status...")
    
    response = requests.get(f"{BASE_URL}/")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Server Status: {result['status']}")
        print(f"🤖 Model Loaded: {result['model_loaded']}")
        print("🚀 Features:")
        for feature, enabled in result['features'].items():
            status = "✅" if enabled else "❌"
            print(f"   {status} {feature}: {enabled}")
    else:
        print(f"❌ Error: {response.status_code}")

def benchmark_rag_vs_standard():
    """Benchmark RAG vs standard responses"""
    print("\n⚡ Benchmarking RAG vs Standard...")
    
    query = "Explain machine learning model evaluation metrics"
    
    # Standard response
    start_time = time.time()
    response1 = requests.post(f"{BASE_URL}/v1/chat/completions", json={
        "model": "qwen2.5-32b-instruct",
        "messages": [{"role": "user", "content": query}],
        "temperature": 0.7,
        "max_tokens": 200,
        "use_rag": False
    })
    standard_time = time.time() - start_time
    
    # RAG-enhanced response
    start_time = time.time()
    response2 = requests.post(f"{BASE_URL}/v1/chat/completions", json={
        "model": "qwen2.5-32b-instruct",
        "messages": [{"role": "user", "content": query}],
        "temperature": 0.7,
        "max_tokens": 200,
        "use_rag": True,
        "use_memory": True
    })
    rag_time = time.time() - start_time
    
    if response1.status_code == 200 and response2.status_code == 200:
        result1 = response1.json()
        result2 = response2.json()
        
        print("📈 Performance Comparison:")
        print(f"   Standard: {result1['system_info']['tokens_per_second']:.1f} t/s ({standard_time:.2f}s total)")
        print(f"   RAG: {result2['system_info']['tokens_per_second']:.1f} t/s ({rag_time:.2f}s total)")
        print(f"   RAG overhead: {((rag_time - standard_time) / standard_time * 100):.1f}%")
        
        print("\n📝 Content Comparison:")
        print(f"   Standard: {len(result1['choices'][0]['message']['content'])} chars")
        print(f"   RAG: {len(result2['choices'][0]['message']['content'])} chars")
        print(f"   RAG enhancement: {result2['system_info']['rag_used']}")

def main():
    """Run all tests"""
    print("🚀 Enhanced LLM Server API Test Suite")
    print("=====================================")
    
    try:
        test_server_status()
        test_basic_chat()
        test_rag_enhanced_chat()
        test_corag_chains()
        test_reasoning_mode()
        test_agent_mode()
        test_streaming()
        benchmark_rag_vs_standard()
        
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        print("Make sure the server is running: ./start.sh")

if __name__ == "__main__":
    main()