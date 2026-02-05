from fastapi.testclient import TestClient
import unittest.mock as mock
import pytest

# We mock the Milvus client BEFORE importing app to prevent connection errors
with mock.patch("app.db.milvus_client.store_in_vault"), \
     mock.patch("app.db.milvus_client.search_vault"):
    from app.main import app

client = TestClient(app)

def test_read_main():
    """Verifies the API redirects or loads the root."""
    response = client.get("/", follow_redirects=True)
    # Since your main.py redirects to /docs, it should return 200
    assert response.status_code == 200

def test_health_check():
    """Verifies the Neural Engine is in Phase 2 status."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ONLINE"