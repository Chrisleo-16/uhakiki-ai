from fastapi.testclient import TestClient
import unittest.mock as mock
import pytest
import sys
import os

# Add the backend folder to path so the tests can find your app code
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_read_main():
    """Verifies the API redirects or loads the root."""
    
    # Mock all external dependencies
    with mock.patch.dict('sys.modules', {
        'langchain_milvus': mock.MagicMock(),
        'langchain_huggingface': mock.MagicMock(),
        'pymilvus': mock.MagicMock(),
        'crewai': mock.MagicMock(),
        'crewai.tools': mock.MagicMock(),
        'transformers': mock.MagicMock(),
        'app.logic.council': mock.MagicMock(),
        'app.logic.liveness_detector': mock.MagicMock(),
        'app.logic.face_extractor': mock.MagicMock(),
        'app.logic.qr_system': mock.MagicMock(),
        'app.logic.xai': mock.MagicMock(),
        'app.db.milvus_client': mock.MagicMock(),
    }):
        with mock.patch('torch.cuda.is_available', return_value=False), \
             mock.patch('app.db.milvus_client.store_in_vault'), \
             mock.patch('app.db.milvus_client.search_vault'):
            
            from app.main import app
            client = TestClient(app)
            
            response = client.get("/", follow_redirects=True)
            # Since your main.py redirects to /docs, it should return 200
            assert response.status_code == 200

def test_health_check():
    """Verifies the Neural Engine is in Phase 2 status."""
    
    # Mock all external dependencies
    with mock.patch.dict('sys.modules', {
        'langchain_milvus': mock.MagicMock(),
        'langchain_huggingface': mock.MagicMock(),
        'pymilvus': mock.MagicMock(),
        'crewai': mock.MagicMock(),
        'crewai.tools': mock.MagicMock(),
        'transformers': mock.MagicMock(),
        'app.logic.council': mock.MagicMock(),
        'app.logic.liveness_detector': mock.MagicMock(),
        'app.logic.face_extractor': mock.MagicMock(),
        'app.logic.qr_system': mock.MagicMock(),
        'app.logic.xai': mock.MagicMock(),
        'app.db.milvus_client': mock.MagicMock(),
    }):
        with mock.patch('torch.cuda.is_available', return_value=False), \
             mock.patch('app.db.milvus_client.store_in_vault'), \
             mock.patch('app.db.milvus_client.search_vault'):
            
            from app.main import app
            client = TestClient(app)
            
            response = client.get("/api/v1/health")
            assert response.status_code == 200
            assert response.json()["status"] == "ONLINE"