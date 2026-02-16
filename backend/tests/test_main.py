import sys
from unittest import mock
import pytest

# --- STEP 1: DEFINE LIGHTWEIGHT STUBS ---
# These real classes prevent the "issubclass() arg 2 must be a class" error
class StubTensor: pass
class StubModule: pass

# --- STEP 2: BUILD THE SOVEREIGN MOCK ---
# We create a fake 'torch' module that actually contains our StubTensor class
mock_torch = mock.MagicMock()
mock_torch.Tensor = StubTensor
mock_torch.nn.Module = StubModule
mock_torch.cuda.is_available.return_value = False

# Define all modules that cause "Resolution Too Deep" or "Kernel" crashes
mock_modules = {
    'torch': mock_torch,
    'torch.nn': mock_torch.nn,
    'torchvision': mock.MagicMock(),
    'torchvision.transforms': mock.MagicMock(),
    'torchvision.ops': mock.MagicMock(),
    'sklearn': mock.MagicMock(),
    'sklearn.preprocessing': mock.MagicMock(),
    'scipy': mock.MagicMock(),
    'scipy.stats': mock.MagicMock(),
    'langchain_milvus': mock.MagicMock(),
    'langchain_huggingface': mock.MagicMock(),
    'pymilvus': mock.MagicMock(),
    'crewai': mock.MagicMock(),
    'crewai.tools': mock.MagicMock(),
    'transformers': mock.MagicMock(),
}

# Apply the global patch BEFORE importing the app
patcher = mock.patch.dict('sys.modules', mock_modules)
patcher.start()

# --- STEP 3: SAFE IMPORTS ---
try:
    from app.main import app
    from fastapi.testclient import TestClient
except ImportError:
    # Ensure backend is in path for GitHub Actions
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from app.main import app
    from fastapi.testclient import TestClient

client = TestClient(app)

# --- STEP 4: ERROR-FREE TESTS ---

def test_read_main():
    """Verifies API root is operational."""
    response = client.get("/", follow_redirects=True)
    assert response.status_code == 200

def test_health_check():
    """Verifies Neural Engine status WITHOUT loading real weights."""
    # Mock the specific DB clients used in the endpoint
    with mock.patch('app.db.milvus_client.store_in_vault'), \
         mock.patch('app.db.milvus_client.search_vault'):
        
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ONLINE"

# Clean up after all tests are done
def teardown_module(module):
    patcher.stop()