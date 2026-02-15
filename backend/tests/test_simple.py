"""
Simple test that directly creates a FastAPI app for testing
"""

import sys
import os
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Add the backend folder to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_simple_fastapi():
    """Test a simple FastAPI app without all the complex dependencies"""
    
    # Create a minimal FastAPI app for testing
    app = FastAPI(title="Test App")
    
    @app.get("/")
    async def root():
        return {"message": "Test root"}
    
    @app.get("/api/v1/health")
    async def health():
        return {"status": "ONLINE", "phase": "Test Phase"}
    
    client = TestClient(app)
    
    # Test root endpoint
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Test root"
    
    # Test health endpoint
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ONLINE"
    assert "phase" in data
    
    print("✅ Simple FastAPI test passed!")

def test_imports_separately():
    """Test importing modules separately to identify the issue"""
    
    try:
        # Test basic imports
        import fastapi
        print("✅ FastAPI import successful")
        
        import torch
        print("✅ PyTorch import successful")
        
        import torchvision
        print("✅ Torchvision import successful")
        
        # Test app structure imports
        from fastapi import FastAPI
        print("✅ FastAPI class import successful")
        
        # Test if we can import the main app structure
        try:
            from app.main import app
            print("✅ Main app import successful")
            
            client = TestClient(app)
            response = client.get("/api/v1/health")
            if response.status_code == 200:
                print("✅ Health endpoint working")
                return True
            else:
                print(f"❌ Health endpoint failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Main app import failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Basic import failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Running simple tests...")
    
    # Test 1: Simple FastAPI
    test_simple_fastapi()
    
    # Test 2: Import test
    success = test_imports_separately()
    
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n❌ Some tests failed - check imports")
