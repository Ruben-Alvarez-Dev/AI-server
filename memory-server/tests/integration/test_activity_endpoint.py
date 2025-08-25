#!/usr/bin/env python3
"""
Test Activity Endpoint for Memory-Server
Tests the new VSCode extension activity tracking functionality
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8001"

def test_activity_endpoint():
    """Test the activity tracking endpoint"""
    print("🧪 Testing Memory-Server Activity Endpoint")
    print("=" * 50)
    
    # Sample activity events that would come from VSCode extension
    sample_events = [
        {
            "type": "openFile",
            "file": "/Users/test/project/main.py",
            "language": "python",
            "timestamp": int(time.time() * 1000)
        },
        {
            "type": "edit",
            "file": "/Users/test/project/main.py", 
            "language": "python",
            "changes": 5,
            "timestamp": int(time.time() * 1000) + 1000
        },
        {
            "type": "activeEditor",
            "file": "/Users/test/project/utils.js",
            "language": "javascript", 
            "timestamp": int(time.time() * 1000) + 2000
        },
        {
            "type": "startDebug",
            "name": "Python: Current File",
            "type": "python",
            "timestamp": int(time.time() * 1000) + 3000
        },
        {
            "type": "commit",
            "hash": "abc123def456",
            "message": "Add new feature for user authentication",
            "author": "Developer",
            "timestamp": int(time.time() * 1000) + 4000
        }
    ]
    
    # Test payload
    test_payload = {
        "workspace": "code",
        "events": sample_events,
        "source": "vscode-extension-test",
        "auto_tag": True,
        "metadata": {
            "vscode_version": "1.85.0",
            "extension_version": "1.0.0",
            "test_run": True,
            "timestamp": datetime.now().isoformat()
        }
    }
    
    try:
        print(f"📤 Sending {len(sample_events)} activity events to Memory-Server...")
        
        response = requests.post(
            f"{BASE_URL}/api/v1/documents/activity",
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Activity tracking successful!")
            print(f"   Events Processed: {result['events_processed']}")
            print(f"   Workspace: {result['workspace']}")
            print(f"   Document ID: {result.get('document_id', 'N/A')}")
            print(f"   Processing Time: {result['processing_time']:.3f}s")
            print(f"   Message: {result['message']}")
            return True
        else:
            print(f"❌ Activity tracking failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Memory-Server")
        print("   Make sure Memory-Server is running on http://localhost:8001")
        return False
    except Exception as e:
        print(f"❌ Activity tracking test failed: {e}")
        return False

def test_server_health():
    """Test if Memory-Server is healthy"""
    try:
        response = requests.get(f"{BASE_URL}/health/status", timeout=5)
        if response.status_code == 200:
            print("✅ Memory-Server is healthy")
            return True
        else:
            print(f"⚠️  Memory-Server health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_workspaces_endpoint():
    """Test if workspaces endpoint is working"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/documents/workspaces", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Workspaces endpoint working - found {len(data['workspaces'])} workspaces")
            return True
        else:
            print(f"⚠️  Workspaces endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Workspaces test failed: {e}")
        return False

def main():
    """Run activity endpoint tests"""
    print("🔍 Memory-Server Activity Endpoint Tests")
    print("=" * 60)
    
    tests = [
        ("Server Health Check", test_server_health),
        ("Workspaces Endpoint", test_workspaces_endpoint), 
        ("Activity Tracking Endpoint", test_activity_endpoint)
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
    
    print("\n" + "=" * 60)
    print(f"📊 ACTIVITY ENDPOINT TEST RESULTS:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL ACTIVITY ENDPOINT TESTS PASSED! 🎉")
        print("✨ VSCode extension integration is ready!")
        print("\n📝 Next Steps:")
        print("   1. Install the VSCode extension")
        print("   2. Configure the workspace in extension settings")
        print("   3. Start coding to see activity tracking in action")
        return True
    else:
        print(f"\n⚠️  {failed} tests failed.")
        print("💡 Check Memory-Server logs and ensure all endpoints are working properly.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)