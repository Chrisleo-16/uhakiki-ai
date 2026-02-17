"""
Simplified API tests that bypass problematic imports
"""

from fastapi.testclient import TestClient
import unittest.mock as mock
import pytest
import sys
import os

# Add the backend folder to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_basic_api():
    """Test basic API functionality without importing the full app"""
    
    # Mock all of problematic imports
    with mock.patch.dict('sys.modules', {
        'langchain_milvus': mock.MagicMock(),
        'langchain_huggingface': mock.MagicMock(),
        'pymilvus': mock.MagicMock(),
        'crewai': mock.MagicMock(),
        'crewai.tools': mock.MagicMock(),
        'transformers': mock.MagicMock(),
        'torch': mock.MagicMock(),
        'torch.nn': mock.MagicMock(),
        'torch.nn.functional': mock.MagicMock(),
        'torchvision': mock.MagicMock(),
        'PIL': mock.MagicMock(),
        'cv2': mock.MagicMock(),
        'crewai.CrewAI': mock.MagicMock(),
        'crewai.Agent': mock.MagicMock(),
        'crewai.Task': mock.MagicMock(),
        'crewai.Crew': mock.MagicMock(),
        'crewai.LLM': mock.MagicMock(),
        'crewai.Process': mock.MagicMock(),
        'app.logic.council': mock.MagicMock(),
        'app.logic.council.CrewAI': mock.MagicMock(),
        'app.logic.council.Agent': mock.MagicMock(),
        'app.logic.council.Task': mock.MagicMock(),
        'app.logic.council.Crew': mock.MagicMock(),
        'app.logic.council.LLM': mock.MagicMock(),
        'app.logic.council.Process': mock.MagicMock(),
        'app.logic.liveness_detector.MBICSystem': mock.MagicMock(),
        'app.logic.liveness_detector': mock.MagicMock(),
        'app.logic.face_extractor': mock.MagicMock(),
        'app.logic.face_extraction': mock.MagicMock(),
    }):
        # Mock the specific functions that cause issues
        with mock.patch('app.db.milvus_client.store_in_vault'), \
             mock.patch('app.db.milvus_client.search_vault'), \
             mock.patch('torch.cuda.is_available', return_value=False), \
             mock.patch('app.logic.council.CrewAI'), \
             mock.patch('app.logic.council.Agent'), \
             mock.patch('app.logic.council.Task'), \
             mock.patch('app.logic.council.Crew'), \
             mock.patch('app.logic.council.LLM'), \
             mock.patch('app.logic.council.Process'), \
             mock.patch('app.logic.liveness_detector.MBICSystem'), \
             mock.patch('app.logic.face_extractor.face_extractor'), \
             mock.patch('app.logic.qr_system.generate_student_qr'), \
             mock.patch('app.logic.xai.generate_audit_report'):
            
            # Now import the app
            from app.main import app
            client = TestClient(app)
            
            # Test basic endpoints
            response = client.get("/", follow_redirects=True)
            assert response.status_code == 200
            
            response = client.get("/api/v1/health")
            assert response.status_code == 200
            assert response.json()["status"] == "ONLINE"

def test_health_endpoint_structure():
    """Test that health endpoint returns expected structure"""
    
    with mock.patch.dict('sys.modules', {
        'langchain_milvus': mock.MagicMock(),
        'langchain_huggingface': mock.MagicMock(),
        'pymilvus': mock.MagicMock(),
        'crewai': mock.MagicMock(),
        'crewai.tools': mock.MagicMock(),
        'transformers': mock.MagicMock(),
        'torch': mock.MagicMock(),
        'torchvision': mock.MagicMock(),
        'torchvision.transforms': mock.MagicMock(),
        'PIL': mock.MagicMock(),
        'cv2': mock.MagicMock(),
    }):
        with mock.patch('app.db.milvus_client.store_in_vault'), \
             mock.patch('app.db.milvus_client.search_vault'), \
             mock.patch('torch.cuda.is_available', return_value=False), \
             mock.patch('app.logic.council.CrewAI'), \
             mock.patch('app.logic.council.Agent'), \
             mock.patch('app.logic.council.Task'), \
             mock.patch('app.logic.council.Crew'), \
             mock.patch('app.logic.council.LLM'), \
             mock.patch('app.logic.council.Process'), \
             mock.patch('app.logic.liveness_detector.MBICSystem'), \
             mock.patch('app.logic.face_extractor.face_extractor'), \
             mock.patch('app.logic.qr_system.generate_student_qr'), \
             mock.patch('app.logic.xai.generate_audit_report'):
            
            from app.main import app
            client = TestClient(app)
            
            response = client.get("/api/v1/health")
            assert response.status_code == 200
            
            data = response.json()
            assert "status" in data
            assert "phase" in data
            assert data["status"] == "ONLINE"

if __name__ == "__main__":
    test_basic_api()
    test_health_endpoint_structure()
    print("✅ All API tests passed!")
