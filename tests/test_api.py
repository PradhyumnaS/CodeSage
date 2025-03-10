from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_endpoint():
    """Test the API root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "online", "message": "CodeSage API is running"}

def test_metrics_endpoint():
    """Test the metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "codesage" in response.text

def test_review_validation():
    """Test review endpoint validation."""
    response = client.post(
        "/review",
        json={"code": "", "language": "Python"}
    )
    assert response.status_code == 200

    response = client.post(
        "/review",
        json={"code": "print('hello')", "language": ""}
    )
    assert response.status_code == 200