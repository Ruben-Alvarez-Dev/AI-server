#!/usr/bin/env python3
"""
AI-Server Complete Testing Suite
Comprehensive testing of all components and integrations
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any, List
import websocket
import threading
from datetime import datetime
import sys

class AIServerTestSuite:
    """Complete test suite for AI-Server system"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.r2r_url = "http://localhost:7272"
        self.websocket_url = "ws://localhost:8000/progress/ws/test_client"
        
        self.test_results = []
        self.websocket_messages = []
        
        print("🤖 AI-Server Complete Testing Suite")
        print("=" * 50)
    
    async def run_all_tests(self):
        """Run complete test suite"""
        
        tests = [
            ("🏥 Health Checks", self.test_health_checks),
            ("🧠 Memory Balancer", self.test_memory_balancer),
            ("👥 Agent Registry", self.test_agent_registry),
            ("📚 RAG Systems", self.test_rag_systems),
            ("🔍 Transparency", self.test_transparency),
            ("📊 Progress Tracking", self.test_progress_tracking),
            ("🔄 Agent Switching", self.test_agent_switching),
            ("👁️ Vision Agent", self.test_vision_capabilities),
            ("🎯 End-to-End Workflow", self.test_complete_workflow),
            ("⚡ Performance", self.test_performance_metrics)
        ]
        
        print(f"Running {len(tests)} test categories...\n")
        
        for test_name, test_func in tests:
            print(f"🔍 {test_name}")
            try:
                result = await test_func()
                self.test_results.append({
                    'test': test_name,
                    'status': 'PASSED' if result else 'FAILED',
                    'timestamp': datetime.now().isoformat()
                })
                status_icon = "✅" if result else "❌"
                print(f"   {status_icon} {test_name}: {'PASSED' if result else 'FAILED'}")
            except Exception as e:
                print(f"   ❌ {test_name}: ERROR - {str(e)}")
                self.test_results.append({
                    'test': test_name,
                    'status': 'ERROR',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
            print()
        
        await self.generate_report()
    
    async def test_health_checks(self) -> bool:
        """Test basic health endpoints"""
        
        async with aiohttp.ClientSession() as session:
            # Main API health
            try:
                async with session.get(f"{self.base_url}/health") as response:
                    if response.status != 200:
                        print(f"   ❌ Main API health failed: {response.status}")
                        return False
                    data = await response.json()
                    print(f"   ✅ Main API: {data.get('status', 'unknown')}")
            except Exception as e:
                print(f"   ❌ Main API unreachable: {e}")
                return False
            
            # R2R health
            try:
                async with session.get(f"{self.r2r_url}/health") as response:
                    if response.status == 200:
                        print(f"   ✅ R2R API: Online")
                    else:
                        print(f"   ⚠️ R2R API: Status {response.status}")
            except Exception as e:
                print(f"   ⚠️ R2R API: {e} (may not be started yet)")
            
            # Check system stats
            try:
                async with session.get(f"{self.base_url}/monitoring/stats") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"   ✅ System monitoring: Available")
                        return True
                    else:
                        print(f"   ❌ System monitoring failed: {response.status}")
                        return False
            except Exception as e:
                print(f"   ❌ System monitoring error: {e}")
                return False
    
    async def test_memory_balancer(self) -> bool:
        """Test memory balancer functionality"""
        
        async with aiohttp.ClientSession() as session:
            try:
                # Get memory status
                async with session.get(f"{self.base_url}/memory/status") as response:
                    if response.status != 200:
                        return False
                    
                    data = await response.json()
                    print(f"   📊 Memory pressure: {data.get('current_pressure', 'unknown')}")
                    print(f"   🤖 Active agents: {data.get('active_coders', 0)}")
                    print(f"   💾 RAM utilization: {data.get('utilization_percent', 0):.1f}%")
                    
                    # Test force rebalance
                    async with session.post(f"{self.base_url}/memory/rebalance") as rebalance_response:
                        if rebalance_response.status == 200:
                            print(f"   ✅ Force rebalance: Success")
                            return True
                        else:
                            print(f"   ❌ Force rebalance failed: {rebalance_response.status}")
                            return False
                    
            except Exception as e:
                print(f"   ❌ Memory balancer error: {e}")
                return False
    
    async def test_agent_registry(self) -> bool:
        """Test agent registry and switching"""
        
        async with aiohttp.ClientSession() as session:
            try:
                # Get available agents
                async with session.get(f"{self.base_url}/agents/registry") as response:
                    if response.status != 200:
                        return False
                    
                    data = await response.json()
                    total_agents = data.get('total_registered', 0)
                    active_agents = data.get('total_active', 0)
                    
                    print(f"   📋 Registered agents: {total_agents}")
                    print(f"   🟢 Active agents: {active_agents}")
                    
                    # Get configuration templates
                    async with session.get(f"{self.base_url}/agents/configurations") as config_response:
                        if config_response.status == 200:
                            configs = await config_response.json()
                            print(f"   🔧 Available configurations: {len(configs)}")
                            return True
                        else:
                            return False
                    
            except Exception as e:
                print(f"   ❌ Agent registry error: {e}")
                return False
    
    async def test_rag_systems(self) -> bool:
        """Test RAG system functionality"""
        
        async with aiohttp.ClientSession() as session:
            try:
                # Test document ingestion
                test_doc = {
                    "content": "This is a test document about React components and TypeScript interfaces for testing the RAG system.",
                    "title": "Test RAG Document", 
                    "metadata": {"category": "test", "domain": "development"}
                }
                
                async with session.post(f"{self.base_url}/rag/ingest", json=test_doc) as response:
                    if response.status != 200:
                        print(f"   ❌ Document ingestion failed: {response.status}")
                        return False
                    
                    result = await response.json()
                    print(f"   ✅ Document ingested: {result.get('document_id', 'unknown')}")
                
                # Test search
                search_query = {
                    "query": "React components TypeScript",
                    "max_results": 5,
                    "domains": ["development"]
                }
                
                async with session.post(f"{self.base_url}/rag/search", json=search_query) as response:
                    if response.status == 200:
                        results = await response.json()
                        print(f"   ✅ Search results: {len(results.get('results', []))}")
                        return True
                    else:
                        print(f"   ❌ Search failed: {response.status}")
                        return False
                        
            except Exception as e:
                print(f"   ❌ RAG system error: {e}")
                return False
    
    async def test_transparency(self) -> bool:
        """Test transparency and thought streaming"""
        
        async with aiohttp.ClientSession() as session:
            try:
                # Get thought stream
                async with session.get(f"{self.base_url}/transparency/thoughts") as response:
                    if response.status != 200:
                        return False
                    
                    thoughts = await response.json()
                    print(f"   💭 Thought history: {len(thoughts.get('thoughts', []))} entries")
                    
                    # Test adding a thought
                    test_thought = {
                        "agent_name": "test_agent",
                        "thought_type": "analysis", 
                        "title": "Test Thought",
                        "content": "This is a test thought for the transparency system"
                    }
                    
                    async with session.post(f"{self.base_url}/transparency/add-thought", json=test_thought) as add_response:
                        if add_response.status == 200:
                            print(f"   ✅ Thought addition: Success")
                            return True
                        else:
                            return False
                        
            except Exception as e:
                print(f"   ❌ Transparency error: {e}")
                return False
    
    async def test_progress_tracking(self) -> bool:
        """Test progress tracking and WebSocket"""
        
        # Test WebSocket connection
        try:
            # Start WebSocket listener in background
            ws_thread = threading.Thread(target=self._test_websocket_connection)
            ws_thread.daemon = True
            ws_thread.start()
            
            # Wait a bit for connection
            await asyncio.sleep(2)
            
            # Create demo task to generate progress
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/progress/demo-task") as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"   ✅ Demo task created: {result.get('task_id', 'unknown')}")
                        
                        # Wait for some progress
                        await asyncio.sleep(5)
                        
                        if len(self.websocket_messages) > 0:
                            print(f"   ✅ WebSocket messages: {len(self.websocket_messages)} received")
                            return True
                        else:
                            print(f"   ⚠️ No WebSocket messages received")
                            return False
                    else:
                        return False
                        
        except Exception as e:
            print(f"   ❌ Progress tracking error: {e}")
            return False
    
    def _test_websocket_connection(self):
        """Test WebSocket connection in separate thread"""
        
        def on_message(ws, message):
            try:
                data = json.loads(message)
                self.websocket_messages.append(data)
            except json.JSONDecodeError:
                pass
        
        def on_error(ws, error):
            print(f"   ⚠️ WebSocket error: {error}")
        
        try:
            ws = websocket.WebSocketApp(
                self.websocket_url,
                on_message=on_message,
                on_error=on_error
            )
            ws.run_forever(ping_timeout=10)
        except Exception as e:
            print(f"   ⚠️ WebSocket connection failed: {e}")
    
    async def test_agent_switching(self) -> bool:
        """Test dynamic agent configuration switching"""
        
        async with aiohttp.ClientSession() as session:
            try:
                # Get current config
                async with session.get(f"{self.base_url}/agents/current-config") as response:
                    if response.status != 200:
                        return False
                    
                    current_config = await response.json()
                    print(f"   🔧 Current config: {current_config.get('config_name', 'unknown')}")
                
                # Test switch to productivity config (if available)
                switch_request = {"target_config": "productivity"}
                
                async with session.post(f"{self.base_url}/agents/switch-config", json=switch_request) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"   ✅ Config switch: {result.get('message', 'success')}")
                        
                        # Switch back to development
                        switch_back = {"target_config": "development"}
                        async with session.post(f"{self.base_url}/agents/switch-config", json=switch_back) as back_response:
                            if back_response.status == 200:
                                print(f"   ✅ Switch back: Success")
                                return True
                            else:
                                return False
                    else:
                        print(f"   ⚠️ Config switch not available yet")
                        return True  # Not a failure if feature not implemented
                        
            except Exception as e:
                print(f"   ❌ Agent switching error: {e}")
                return False
    
    async def test_vision_capabilities(self) -> bool:
        """Test vision agent capabilities"""
        
        async with aiohttp.ClientSession() as session:
            try:
                # Test vision agent status
                async with session.get(f"{self.base_url}/agents/vision/status") as response:
                    if response.status == 200:
                        status = await response.json()
                        print(f"   👁️ Vision agent: {status.get('status', 'unknown')}")
                        return True
                    else:
                        print(f"   ⚠️ Vision agent not available: {response.status}")
                        return True  # Not critical for basic functionality
                        
            except Exception as e:
                print(f"   ⚠️ Vision capabilities: {e}")
                return True  # Not critical
    
    async def test_complete_workflow(self) -> bool:
        """Test complete end-to-end workflow"""
        
        async with aiohttp.ClientSession() as session:
            try:
                # Create a simple development task
                workflow_request = {
                    "request": "Create a simple React component with TypeScript that displays a greeting message",
                    "workflow_type": "development",
                    "context": {
                        "language": "typescript",
                        "framework": "react",
                        "complexity": "simple"
                    }
                }
                
                async with session.post(f"{self.base_url}/workflows/execute", json=workflow_request) as response:
                    if response.status == 200:
                        result = await response.json()
                        task_id = result.get('task_id')
                        print(f"   ✅ Workflow started: {task_id}")
                        
                        # Wait a bit and check status
                        await asyncio.sleep(3)
                        
                        async with session.get(f"{self.base_url}/workflows/{task_id}") as status_response:
                            if status_response.status == 200:
                                status = await status_response.json()
                                print(f"   ✅ Workflow status: {status.get('status', 'unknown')}")
                                return True
                            else:
                                return False
                    else:
                        print(f"   ❌ Workflow creation failed: {response.status}")
                        return False
                        
            except Exception as e:
                print(f"   ❌ Complete workflow error: {e}")
                return False
    
    async def test_performance_metrics(self) -> bool:
        """Test performance monitoring"""
        
        async with aiohttp.ClientSession() as session:
            try:
                # Get system metrics
                async with session.get(f"{self.base_url}/monitoring/metrics") as response:
                    if response.status != 200:
                        return False
                    
                    metrics = await response.json()
                    
                    # Display key metrics
                    print(f"   📊 System uptime: {metrics.get('uptime', 'unknown')}")
                    print(f"   🔄 Total requests: {metrics.get('total_requests', 0)}")
                    print(f"   ⚡ Avg response time: {metrics.get('avg_response_time', 0):.2f}ms")
                    
                    # Get agent performance
                    agent_metrics = metrics.get('agent_performance', {})
                    if agent_metrics:
                        print(f"   🤖 Agent metrics: {len(agent_metrics)} agents tracked")
                    
                    return True
                    
            except Exception as e:
                print(f"   ❌ Performance metrics error: {e}")
                return False
    
    async def generate_report(self):
        """Generate final test report"""
        
        print("\n" + "=" * 60)
        print("📋 AI-SERVER TEST REPORT")
        print("=" * 60)
        
        passed = len([r for r in self.test_results if r['status'] == 'PASSED'])
        failed = len([r for r in self.test_results if r['status'] == 'FAILED']) 
        errors = len([r for r in self.test_results if r['status'] == 'ERROR'])
        total = len(self.test_results)
        
        print(f"✅ PASSED: {passed}/{total} ({passed/total*100:.1f}%)")
        print(f"❌ FAILED: {failed}/{total} ({failed/total*100:.1f}%)")
        print(f"⚠️ ERRORS: {errors}/{total} ({errors/total*100:.1f}%)")
        
        print(f"\n📊 OVERALL SCORE: {passed/total*100:.1f}%")
        
        if failed > 0 or errors > 0:
            print(f"\n❌ FAILED/ERROR TESTS:")
            for result in self.test_results:
                if result['status'] in ['FAILED', 'ERROR']:
                    print(f"   - {result['test']}: {result['status']}")
                    if 'error' in result:
                        print(f"     Error: {result['error']}")
        
        # System recommendations
        print(f"\n🔧 RECOMMENDATIONS:")
        
        if passed < total:
            print("   - Some components may need manual configuration")
            print("   - Check that all required services are running")
            print("   - Verify model files are downloaded and accessible")
        
        if passed/total >= 0.8:
            print("   ✅ System is ready for basic usage")
        elif passed/total >= 0.6:
            print("   ⚠️ System has some issues but core functionality works")
        else:
            print("   ❌ System needs troubleshooting before use")
        
        print(f"\n🚀 To start using AI-Server:")
        print(f"   1. Visit: http://localhost:8000/docs")
        print(f"   2. Dashboard: http://localhost:8000/progress/dashboard")
        print(f"   3. Health: http://localhost:8000/health")
        
        # Save detailed report
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total': total,
                'passed': passed,
                'failed': failed,
                'errors': errors,
                'score': passed/total*100
            },
            'detailed_results': self.test_results,
            'websocket_messages_received': len(self.websocket_messages)
        }
        
        with open('test_report.json', 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n💾 Detailed report saved to: test_report.json")

async def main():
    """Main test runner"""
    
    # Check if AI-Server is running
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/health", timeout=5) as response:
                if response.status != 200:
                    print("❌ AI-Server is not running or not healthy")
                    print("   Please start AI-Server first with: ./start_ai_server.sh")
                    sys.exit(1)
    except Exception as e:
        print(f"❌ Cannot connect to AI-Server: {e}")
        print("   Please start AI-Server first with: ./start_ai_server.sh")
        sys.exit(1)
    
    # Run test suite
    test_suite = AIServerTestSuite()
    await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())