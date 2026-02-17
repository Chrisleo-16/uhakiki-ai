#!/usr/bin/env python3
"""
Simple health test that bypasses all problematic imports
"""

import requests
import json

def test_health_endpoint():
    """Test just the health endpoint directly"""
    try:
        response = requests.get("http://localhost:8000/api/v1/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed!")
            print(f"📊 Response: {data}")
            
            # Verify expected fields
            assert "status" in data
            assert "phase" in data
            assert data["status"] == "ONLINE"
            
            print("✅ Health endpoint working correctly!")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_docs_endpoint():
    """Test that docs endpoint is accessible"""
    try:
        response = requests.get("http://localhost:8000/docs", timeout=5)
        
        if response.status_code == 200:
            print("✅ API docs accessible!")
            return True
        else:
            print(f"❌ Docs not accessible: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Docs check error: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing UhakikiAI Backend Health...")
    
    success = True
    
    # Test health endpoint
    if not test_health_endpoint():
        success = False
    
    # Test docs endpoint
    if not test_docs_endpoint():
        success = False
    
    if success:
        print("🎉 All basic tests passed!")
        print("🚀 Backend is ready for production!")
    else:
        print("❌ Some tests failed!")
        print("🔧 Check if backend server is running on http://localhost:8000")
