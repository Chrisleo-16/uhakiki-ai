"""
Minimal test for FastAPI app - bypasses all problematic imports
"""

import unittest.mock as mock
import sys
import os

# Add the backend folder to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_minimal_app():
    """Test the FastAPI app with minimal dependencies"""
    
    # Create a completely mocked version of the problematic modules
    mock_council = mock.MagicMock()
    mock_council.SecurityCouncil = mock.MagicMock()
    mock_council.run_security_audit = mock.MagicMock(return_value={'approved': True, 'reasoning': 'Test'})
    
    mock_mbic = mock.MagicMock()
    mock_qr = mock.MagicMock()
    mock_qr.generate_student_qr = mock.MagicMock(return_value="test_qr.png")
    mock_xai = mock.MagicMock()
    mock_xai.generate_audit_report = mock.MagicMock(return_value={'human_readable_explanation': 'Test', 'metadata': {'student_id': 'test'}})
    mock_face = mock.MagicMock()
    mock_face.get_reference_encoding = mock.MagicMock(return_value=None)
    
    # Mock all external dependencies at the module level
    with mock.patch.dict('sys.modules', {
        'langchain_milvus': mock.MagicMock(),
        'langchain_huggingface': mock.MagicMock(),
        'pymilvus': mock.MagicMock(),
        'crewai': mock.MagicMock(),
        'crewai.tools': mock.MagicMock(),
        'transformers': mock.MagicMock(),
        'torch': mock.MagicMock(),
        'torchvision': mock.MagicMock(),
        'PIL': mock.MagicMock(),
        'cv2': mock.MagicMock(),
        'numpy': mock.MagicMock(),
        'app.logic.council': mock_council,
        'app.logic.liveness_detector': mock.MagicMock(),
        'app.logic.face_extractor': mock.MagicMock(),
        'app.logic.qr_system': mock_qr,
        'app.logic.xai': mock_xai,
        'app.db.milvus_client': mock.MagicMock(),
    }):
        # Mock torch.cuda
        with mock.patch('torch.cuda.is_available', return_value=False):
            # Mock the specific functions
            with mock.patch('app.db.milvus_client.store_in_vault', return_value=True), \
                 mock.patch('app.db.milvus_client.search_vault', return_value=[]):
                
                # Import the app
                from app.main import app
                from fastapi.testclient import TestClient
                
                client = TestClient(app)
                
                # Test basic endpoints
                response = client.get("/", follow_redirects=True)
                assert response.status_code == 200, f"Root endpoint failed: {response.status_code}"
                
                response = client.get("/api/v1/health")
                assert response.status_code == 200, f"Health endpoint failed: {response.status_code}"
                
                data = response.json()
                assert "status" in data, "Health response missing 'status' field"
                assert "phase" in data, "Health response missing 'phase' field"
                assert data["status"] == "ONLINE", f"Expected 'ONLINE', got {data['status']}"
                
                print("✅ Minimal app test passed!")
                return True

if __name__ == "__main__":
    try:
        test_minimal_app()
        print("🎉 All tests passed successfully!")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
