import sys
import unittest.mock as mock
from fastapi.testclient import TestClient

# --- STEP 1: GLOBAL SOVEREIGN MOCK ---
# We block these libraries at the process level before anything else loads.
mock_modules = {
    'torch': mock.MagicMock(),
    'torchvision': mock.MagicMock(),
    'torchvision.transforms': mock.MagicMock(),
    'langchain_milvus': mock.MagicMock(),
    'langchain_huggingface': mock.MagicMock(),
    'pymilvus': mock.MagicMock(),
    'crewai': mock.MagicMock(),
    'crewai.tools': mock.MagicMock(),
    'transformers': mock.MagicMock(),
    'face_recognition': mock.MagicMock(),
    # Mocking internal app logic that depends on heavy ML
    'app.logic.council': mock.MagicMock(),
    'app.logic.liveness_detector': mock.MagicMock(),
    'app.logic.face_extractor': mock.MagicMock(),
    'app.logic.qr_system': mock.MagicMock(),
    'app.logic.xai': mock.MagicMock(),
    'app.db.milvus_client': mock.MagicMock(),
}

# Apply the global patch
patcher = mock.patch.dict('sys.modules', mock_modules)
patcher.start()

# --- STEP 2: SAFE IMPORTS ---
# Now that sys.modules is "poisoned" with mocks, importing the app is safe.
try:
    from app.main import app
except ImportError:
    # Fallback for different pathing structures in CI
    sys.path.append('backend')
    from app.main import app

client = TestClient(app)

# --- STEP 3: CONFIGURED TESTS ---

def test_read_main():
    """Verifies the API redirects or loads the root."""
    # We use follow_redirects because "/" usually goes to "/docs"
    response = client.get("/", follow_redirects=True)
    assert response.status_code == 200

def test_health_check():
    """Verifies the Neural Engine is in Phase 2 status."""
    
    # We mock specific internal methods to return expected "Healthy" values
    with mock.patch('app.db.milvus_client.store_in_vault'), \
         mock.patch('app.db.milvus_client.search_vault'):
        
        response = client.get("/api/v1/health")
        
        # Validation
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ONLINE"
        # Optional: Verify Phase 2 indicator if present in your JSON
        if "phase" in data:
            assert data["phase"] == 2

# Stop the patcher when the module is destroyed (clean up)
def teardown_module(module):
    patcher.stop()