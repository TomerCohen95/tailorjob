import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock
import json

# You will need to import your app and the dependency provider functions
# The path might need adjustment based on your project structure.
from app.main import app
from app.core.container import container
from app.services.cv_extractor import CVExtractor
from app.services.cv_tailor import CVTailor
import redis

# Mock data for our tests
MOCK_CV_TEXT = "This is a CV."
MOCK_ANALYSIS = {
    "job_data": {"title": "Software Engineer"},
    "recommendations": ["Improve skills section."]
}
MOCK_EXTRACTED_FACTS = {"name": "Jane Doe", "email": "jane@test.com"}
MOCK_TAILORED_CV = {"summary": "A tailored summary.", "experience": []}

@pytest.fixture
def mock_services():
    """Fixture to create mock CVExtractor and CVTailor services."""
    mock_extractor = MagicMock(spec=CVExtractor)
    mock_tailor = MagicMock(spec=CVTailor)
    mock_extractor.extract_facts = AsyncMock(return_value=MOCK_EXTRACTED_FACTS)
    mock_tailor.tailor_cv = AsyncMock(return_value=MOCK_TAILORED_CV)
    return mock_extractor, mock_tailor

@pytest.fixture
def mock_redis():
    """Fixture to create a mock Redis client."""
    mock_redis_client = MagicMock(spec=redis.Redis)
    mock_redis_client.get.return_value = None  # Default to cache miss
    mock_redis_client.set = MagicMock()
    return mock_redis_client

@pytest.fixture
def client(mock_services, mock_redis, monkeypatch):
    """
    Provides a TestClient with mocked dependencies for the tailoring endpoint.
    """
    mock_extractor, mock_tailor = mock_services

    # Use monkeypatch to replace the real service providers in the container
    # with our mocks for the duration of the test.
    monkeypatch.setattr(container, "cv_extractor", lambda: mock_extractor)
    monkeypatch.setattr(container, "cv_tailor", lambda: mock_tailor)
    monkeypatch.setattr(container, "redis_client", lambda: mock_redis)

    with TestClient(app) as c:
        yield c

def test_tailor_cv_cache_miss(client, mock_services, mock_redis):
    """
    Tests the 'happy path' for a cache miss, ensuring the AI service is called
    and the result is cached.
    """
    mock_extractor, mock_tailor = mock_services
    payload = {
        "cv_text": MOCK_CV_TEXT,
        "analysis": MOCK_ANALYSIS,
        "template_name": "modern"  # Use the enum member name
    }

    response = client.post("/api/v1/tailor-cv", json=payload)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"] == "attachment; filename=Tailored_CV.pdf"
    assert response.content.startswith(b'%PDF-')

    # Verify that our mock services were called with the correct data
    mock_extractor.extract_facts.assert_called_once_with(MOCK_CV_TEXT)
    mock_tailor.tailor_cv.assert_called_once_with(
        cv_facts=MOCK_EXTRACTED_FACTS,
        job_data=MOCK_ANALYSIS["job_data"],
        analysis=MOCK_ANALYSIS
    )
    # Verify that the result was stored in the cache
    mock_redis.set.assert_called_once()

def test_tailor_cv_cache_hit(client, mock_services, mock_redis):
    """
    Tests the path for a cache hit, ensuring the AI service is NOT called.
    """
    mock_extractor, mock_tailor = mock_services

    # --- Setup the cache hit ---
    # Simulate that Redis returns a cached result
    cached_data = json.dumps(MOCK_TAILORED_CV)
    mock_redis.get.return_value = cached_data

    payload = {
        "cv_text": MOCK_CV_TEXT,
        "analysis": MOCK_ANALYSIS,
        "template_name": "classic"
    }

    response = client.post("/api/v1/tailor-cv", json=payload)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"

    # --- Verify the core cache logic ---
    mock_redis.get.assert_called_once()
    # Crucially, assert the expensive AI service was NOT called
    mock_tailor.tailor_cv.assert_not_called()

def test_tailor_cv_missing_job_data(client):
    """
    Tests the endpoint's 400 error response when 'job_data' is missing.
    """
    payload = {
        "cv_text": MOCK_CV_TEXT,
        "analysis": {"recommendations": []},  # 'job_data' is missing
        "template_name": "classic"
    }
    response = client.post("/api/v1/tailor-cv", json=payload)
    assert response.status_code == 400
    assert response.json() == {"detail": "Analysis object must contain 'job_data'."}

def test_tailor_cv_invalid_template_name(client):
    """
    Tests the 422 validation error for an invalid template name.
    """
    payload = {"cv_text": "...", "analysis": MOCK_ANALYSIS, "template_name": "invalid-style"}
    response = client.post("/api/v1/tailor-cv", json=payload)
    assert response.status_code == 422  # Unprocessable Entity
    assert "value is not a valid enumeration member" in response.text