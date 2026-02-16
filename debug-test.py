#!/usr/bin/env python3
"""
Debug test to identify the issue with the backend
"""

import requests
import json
import traceback

def test_health_endpoint():
    """Test the health endpoint"""
    try:
        response = requests.get("http://localhost:8000/api/v1/health")
        print(f"✅ Health endpoint: {response.status_code}")
        print(f"📊 Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Health endpoint failed: {e}")
        return False

def test_docs_endpoint():
    """Test the docs endpoint"""
    try:
        response = requests.get("http://localhost:8000/docs")
        print(f"✅ Docs endpoint: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Docs endpoint failed: {e}")
        return False

def test_simple_post():
    """Test a simple POST request"""
    try:
        response = requests.post("http://localhost:8000/api/v1/secure-ingest", 
                               data={'national_id': 'TEST-999'})
        print(f"📡 Simple POST: {response.status_code}")
        if response.status_code != 200:
            print(f"📄 Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Simple POST failed: {e}")
        traceback.print_exc()
        return False

def main():
    print("🔍 Debugging UhakikiAI Backend...")
    
    # Test 1: Health endpoint
    if not test_health_endpoint():
        print("❌ Server is not responding properly")
        return
    
    # Test 2: Docs endpoint
    if not test_docs_endpoint():
        print("❌ Documentation not accessible")
        return
    
    # Test 3: Simple POST
    if not test_simple_post():
        print("❌ POST endpoint has issues")
        return
    
    print("✅ All basic tests passed!")

if __name__ == "__main__":
    main()
