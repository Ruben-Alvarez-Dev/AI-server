#!/usr/bin/env python3
"""
Benchmark script to test performance of all LLM server modes
Measures tokens per second (t/s) for each operation mode
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Tuple

# Test configurations for each mode
BENCHMARK_CONFIGS = {
    "chat": {
        "endpoint": "/v1/chat/completions",
        "data": {
            "model": "qwen2.5-coder-7b",
            "messages": [{"role": "user", "content": "Explain how machine learning works in simple terms"}],
            "mode": "chat",
            "max_tokens": 500,
            "temperature": 0.7
        }
    },
    "plan": {
        "endpoint": "/v1/chat/completions", 
        "data": {
            "model": "qwen2.5-coder-7b",
            "messages": [{"role": "user", "content": "Plan the development of a microservices architecture for an e-commerce platform"}],
            "mode": "plan",
            "reasoning": True,
            "max_tokens": 800,
            "temperature": 0.1
        }
    },
    "act": {
        "endpoint": "/v1/chat/completions",
        "data": {
            "model": "qwen2.5-coder-7b", 
            "messages": [{"role": "user", "content": "Create a REST API endpoint for user authentication with JWT tokens"}],
            "mode": "act",
            "max_tokens": 600,
            "temperature": 0.2
        }
    },
    "agent": {
        "endpoint": "/v1/chat/completions",
        "data": {
            "model": "qwen2.5-coder-7b",
            "messages": [{"role": "user", "content": "Analyze the codebase structure and recommend architectural improvements"}],
            "mode": "agent",
            "reasoning": True,
            "project_root": "/Users/server/AI-projects/AI-server/llm-server",
            "max_tokens": 700,
            "temperature": 0.3
        }
    },
    "edit": {
        "endpoint": "/v1/chat/completions",
        "data": {
            "model": "qwen2.5-coder-7b",
            "messages": [{"role": "user", "content": "Review this code and suggest performance optimizations"}],
            "mode": "edit",
            "context_files": ["./real_server.py"],
            "max_tokens": 600, 
            "temperature": 0.2
        }
    },
    "reasoning": {
        "endpoint": "/v1/chat/completions",
        "data": {
            "model": "qwen2.5-coder-7b",
            "messages": [{"role": "user", "content": "Solve this complex problem: Design an algorithm to find the shortest path in a weighted graph with negative edges"}],
            "reasoning": True,
            "max_tokens": 800,
            "temperature": 0.1
        }
    }
}

class BenchmarkRunner:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: Dict[str, Dict] = {}
    
    async def benchmark_mode(self, session: aiohttp.ClientSession, mode: str, config: Dict) -> Dict:
        """Benchmark a specific mode"""
        print(f"🔄 Testing {mode.upper()} mode...")
        
        url = f"{self.base_url}{config['endpoint']}"
        headers = {"Content-Type": "application/json"}
        
        try:
            # Warm-up request
            async with session.post(url, json=config['data'], headers=headers) as response:
                await response.json()
            
            # Benchmark request
            start_time = time.time()
            async with session.post(url, json=config['data'], headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    end_time = time.time()
                    
                    # Extract metrics
                    generation_time = end_time - start_time
                    usage = result.get('usage', {})
                    completion_tokens = usage.get('completion_tokens', 0)
                    prompt_tokens = usage.get('prompt_tokens', 0)
                    total_tokens = usage.get('total_tokens', 0)
                    
                    # Calculate tokens per second
                    tokens_per_second = completion_tokens / generation_time if generation_time > 0 else 0
                    
                    # Get system info if available
                    system_info = result.get('system_info', {})
                    reported_tps = system_info.get('tokens_per_second', tokens_per_second)
                    
                    return {
                        'status': 'success',
                        'generation_time': round(generation_time, 3),
                        'completion_tokens': completion_tokens,
                        'prompt_tokens': prompt_tokens,
                        'total_tokens': total_tokens,
                        'tokens_per_second': round(tokens_per_second, 1),
                        'reported_tps': reported_tps,
                        'response_length': len(result.get('choices', [{}])[0].get('message', {}).get('content', '')),
                        'reasoning_enabled': config['data'].get('reasoning', False),
                        'context_provided': 'context_files' in config['data'] or 'project_root' in config['data']
                    }
                else:
                    return {
                        'status': 'error',
                        'error': f"HTTP {response.status}",
                        'message': await response.text()
                    }
                    
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def run_all_benchmarks(self) -> Dict[str, Dict]:
        """Run benchmarks for all modes"""
        print("🚀 Starting LLM Server Performance Benchmark")
        print("=" * 60)
        
        async with aiohttp.ClientSession() as session:
            for mode, config in BENCHMARK_CONFIGS.items():
                result = await self.benchmark_mode(session, mode, config)
                self.results[mode] = result
                
                if result['status'] == 'success':
                    print(f"✅ {mode.upper()}: {result['tokens_per_second']} t/s ({result['completion_tokens']} tokens in {result['generation_time']}s)")
                else:
                    print(f"❌ {mode.upper()}: {result.get('error', 'Unknown error')}")
                
                # Wait between requests to avoid overloading
                await asyncio.sleep(1)
        
        return self.results
    
    def print_detailed_report(self):
        """Print detailed performance report"""
        print("\n" + "=" * 80)
        print("📊 DETAILED PERFORMANCE REPORT")
        print("=" * 80)
        
        # Summary table
        print(f"{'Mode':<12} {'Status':<8} {'T/S':<8} {'Tokens':<8} {'Time(s)':<8} {'Features':<20}")
        print("-" * 80)
        
        for mode, result in self.results.items():
            if result['status'] == 'success':
                features = []
                if result.get('reasoning_enabled'):
                    features.append("Reasoning")
                if result.get('context_provided'):
                    features.append("Context")
                
                features_str = ", ".join(features) if features else "Standard"
                
                print(f"{mode.upper():<12} {'✅':<8} {result['tokens_per_second']:<8} "
                      f"{result['completion_tokens']:<8} {result['generation_time']:<8} {features_str:<20}")
            else:
                print(f"{mode.upper():<12} {'❌':<8} {'N/A':<8} {'N/A':<8} {'N/A':<8} {result.get('error', ''):<20}")
        
        print("-" * 80)
        
        # Performance analysis
        successful_results = {k: v for k, v in self.results.items() if v['status'] == 'success'}
        
        if successful_results:
            tps_values = [r['tokens_per_second'] for r in successful_results.values()]
            avg_tps = sum(tps_values) / len(tps_values)
            max_tps = max(tps_values)
            min_tps = min(tps_values)
            
            print(f"\n📈 PERFORMANCE SUMMARY:")
            print(f"   Average T/S: {avg_tps:.1f}")
            print(f"   Maximum T/S: {max_tps:.1f}")
            print(f"   Minimum T/S: {min_tps:.1f}")
            
            # Find best and worst performing modes
            best_mode = max(successful_results.items(), key=lambda x: x[1]['tokens_per_second'])
            worst_mode = min(successful_results.items(), key=lambda x: x[1]['tokens_per_second'])
            
            print(f"   Best Mode: {best_mode[0].upper()} ({best_mode[1]['tokens_per_second']} t/s)")
            print(f"   Worst Mode: {worst_mode[0].upper()} ({worst_mode[1]['tokens_per_second']} t/s)")
        
        print("\n🎯 MODE CHARACTERISTICS:")
        for mode, result in self.results.items():
            if result['status'] == 'success':
                complexity = "High" if result.get('reasoning_enabled') else "Medium" if result.get('context_provided') else "Low"
                efficiency = "Excellent" if result['tokens_per_second'] > 50 else "Good" if result['tokens_per_second'] > 40 else "Fair"
                
                print(f"   {mode.upper()}: Complexity={complexity}, Efficiency={efficiency}")
        
        print("\n" + "=" * 80)

async def main():
    """Main benchmark execution"""
    benchmark = BenchmarkRunner()
    
    # Check server health first
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/health") as response:
                if response.status != 200:
                    print("❌ Server not healthy. Please start the server first.")
                    return
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return
    
    # Run benchmarks
    await benchmark.run_all_benchmarks()
    benchmark.print_detailed_report()

if __name__ == "__main__":
    asyncio.run(main())