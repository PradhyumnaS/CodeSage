import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app
from tests.mock_llm_service import MockLLMService

client = TestClient(app)

@pytest.fixture
def mock_llm_service():
    return MockLLMService()

@pytest.fixture
def mock_rate_limiter():
    mock = AsyncMock()
    mock.check_rate_limit.return_value = True
    return mock

@pytest.fixture
def mock_cache_manager():
    mock = AsyncMock()
    mock.get_cached_review.return_value = None
    return mock

@patch("app.main.llm_service")
@patch("app.main.rate_limiter")
@patch("app.main.cache_manager")
def test_code_review_endpoint(mock_cm, mock_rl, mock_llm, mock_llm_service, mock_rate_limiter, mock_cache_manager):
    mock_cm.get_cached_review = mock_cache_manager.get_cached_review
    mock_rl.check_rate_limit = mock_rate_limiter.check_rate_limit
    mock_llm.review_code = mock_llm_service.review_code
    
    response = client.post(
        "/review",
        json={
            "code": "def add(a, b):\n    return a + b",
            "language": "Python"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "review" in data
    assert "bugs_detected" in data
    assert "suggestions" in data
    assert "request_id" in data
    assert "timestamp" in data

@patch("app.main.rate_limiter")
def test_rate_limiting(mock_rl, mock_rate_limiter):
    mock_rate_limiter.check_rate_limit.return_value = False
    mock_rl.check_rate_limit = mock_rate_limiter.check_rate_limit
    
    response = client.post(
        "/review",
        json={
            "code": "print('hello')",
            "language": "Python"
        }
    )
    
    assert response.status_code == 429