#!/usr/bin/env python3
"""
Test Web Search Endpoints for Memory-Server
Tests the new web search functionality with real API calls
"""

import os
import sys
import requests
import json
import time

# Test configuration
BASE_URL = "http://localhost:8001"

def test_server_health():
    """Test if server is running and healthy"""
    try:
        response = requests.get(f"{BASE_URL}/health/status", timeout=5)
        if response.status_code == 200:
            print("✅ Server is healthy and responding")
            return True
        else:
            print(f"⚠️  Server responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server - is it running?")
        print(f"   Make sure Memory-Server is running on {BASE_URL}")
        return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_search_config():
    """Test web search configuration endpoint"""
    try:
        print("\n🔧 Testing search configuration...")
        response = requests.get(f"{BASE_URL}/api/v1/search/config")
        
        if response.status_code == 200:
            config = response.json()
            print("✅ Search configuration retrieved:")
            print(f"   Services: {config['services']}")
            print(f"   Max results per query: {config['limits']['max_results_per_query']}")
            print(f"   Supported forums: {config['supported_forums']}")
            return True
        else:
            print(f"❌ Config request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Search config test failed: {e}")
        return False

def test_basic_web_search():
    """Test basic web search functionality"""
    try:
        print("\n🔍 Testing basic web search...")
        
        request_data = {
            "query": "artificial intelligence 2025",
            "num_results": 3,
            "search_type": "search",
            "include_content": False
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/search/web",
            json=request_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Web search completed!")
            print(f"   Query: {result['query']}")
            print(f"   Results found: {result['total_results']}")
            print(f"   Execution time: {result.get('execution_time', 0):.2f}s")
            print(f"   Search type: {result['search_type']}")
            
            for i, res in enumerate(result['results'][:2], 1):
                print(f"   Result {i}: {res['title']}")
                print(f"   URL: {res['url']}")
                print(f"   Snippet: {res['snippet'][:100]}...")
                
            return True
        else:
            print(f"❌ Web search failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Web search test failed: {e}")
        return False

def test_documentation_search():
    """Test documentation search functionality"""
    try:
        print("\n📚 Testing documentation search...")
        
        request_data = {
            "topic": "fastapi tutorial",
            "num_results": 2,
            "workspace": "research",
            "auto_ingest": False
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/search/documentation",
            json=request_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Documentation search completed!")
            print(f"   Topic: {result['topic']}")
            print(f"   Documentation found: {result['documentation_found']}")
            print(f"   Workspace: {result['workspace']}")
            return result['documentation_found'] > 0
        else:
            print(f"❌ Documentation search failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Documentation search test failed: {e}")
        return False

def test_code_search():
    """Test code examples search"""
    try:
        print("\n💻 Testing code examples search...")
        
        request_data = {
            "topic": "python async await",
            "language": "python",
            "num_results": 2,
            "workspace": "code",
            "auto_ingest": False
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/search/code",
            json=request_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Code search completed!")
            print(f"   Topic: {result['topic']}")
            print(f"   Language: {result['language']}")
            print(f"   Examples found: {result['examples_found']}")
            return result['examples_found'] > 0
        else:
            print(f"❌ Code search failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Code search test failed: {e}")
        return False

def test_forum_search():
    """Test forum search functionality"""
    try:
        print("\n💬 Testing forum search...")
        
        request_data = {
            "topic": "python performance optimization",
            "forum": "reddit",
            "num_results": 2,
            "workspace": "research",
            "auto_ingest": False
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/search/forums",
            json=request_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Forum search completed!")
            print(f"   Topic: {result['topic']}")
            print(f"   Forum: {result['forum']}")
            print(f"   Discussions found: {result['discussions_found']}")
            return result['discussions_found'] > 0
        else:
            print(f"❌ Forum search failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Forum search test failed: {e}")
        return False

def test_api_keys_warning():
    """Test behavior when API keys are not configured"""
    print("\n⚠️  API Keys Status:")
    
    # Check environment variables
    serper_key = os.getenv("SERPER_API_KEY")
    firecrawl_key = os.getenv("FIRECRAWL_API_KEY")
    
    if not serper_key:
        print("   ⚠️  SERPER_API_KEY not found in environment")
        print("   → Set SERPER_API_KEY for web search functionality")
        print("   → Get API key from: https://serper.dev")
    else:
        print("   ✅ SERPER_API_KEY configured")
    
    if not firecrawl_key:
        print("   ⚠️  FIRECRAWL_API_KEY not found in environment")
        print("   → Set FIRECRAWL_API_KEY for enhanced content scraping")
        print("   → Get API key from: https://firecrawl.dev")
    else:
        print("   ✅ FIRECRAWL_API_KEY configured")
    
    return bool(serper_key or firecrawl_key)

def main():
    """Run all web search endpoint tests"""
    print("🔍 Memory-Server Web Search Tests")
    print("=" * 50)
    
    # Check API keys first
    has_keys = test_api_keys_warning()
    if not has_keys:
        print("\n⚠️  No API keys configured.")
        print("   Tests will run but may fail without proper API keys.")
        print("   Configure SERPER_API_KEY and FIRECRAWL_API_KEY for full functionality.")
    
    tests = [
        ("Server Health", test_server_health),
        ("Search Configuration", test_search_config),
        ("Basic Web Search", test_basic_web_search),
        ("Documentation Search", test_documentation_search),
        ("Code Examples Search", test_code_search),
        ("Forum Search", test_forum_search)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                failed += 1
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            failed += 1
            print(f"💥 {test_name} CRASHED: {e}")
        
        time.sleep(1)  # Brief pause between tests
    
    print("\n" + "=" * 50)
    print(f"📊 WEB SEARCH TEST RESULTS:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL WEB SEARCH TESTS PASSED! 🎉")
        print("✨ Memory-Server web search system is working correctly!")
        return True
    else:
        print(f"\n⚠️  {failed} tests failed.")
        if not has_keys:
            print("💡 Most failures are likely due to missing API keys.")
            print("   Configure SERPER_API_KEY and FIRECRAWL_API_KEY to resolve.")
        print("💡 Check server logs for more details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)