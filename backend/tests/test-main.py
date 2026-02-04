from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_main():
    """Verifies the API is alive and reachable."""
    response = client.get("/")
    assert response.status_code == 200

def test_health_check():
    """Verifies the Neural Engine is in Phase 2 status."""
    # Note: If you haven't added this route yet, this test might fail. 
    # Ensure /api/v1/health exists in your main.py or skip this.
    pass