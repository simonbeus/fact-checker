from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from app.api.routes import get_workflow
from app.main import app
from app.models.claim import Claim, ClaimExtractionResponse
from app.models.verification import FactCheckResponse, VerificationResult
from app.services.fact_checker import FactCheckerWorkflow

client = TestClient(app)


def test_root_endpoint():
    """Verify root metadata endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Fact-Checking API"
    assert "documentation" in data
    assert data["documentation"] == "/docs"


def test_health_check_endpoint():
    """Verify health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "fact-check-api"}


def test_fact_check_validation_error_short_transcript():
    """Verify 422 Unprocessable Entity when transcript is shorter than required."""
    response = client.post(
        "/api/v1/fact-check",
        json={"transcript": "Short"},
    )
    assert response.status_code == 422


def test_fact_check_endpoint_with_dependency_override():
    """Verify POST /api/v1/fact-check with mocked workflow dependency."""
    mock_workflow = MagicMock(spec=FactCheckerWorkflow)
    mock_workflow.process_transcript = AsyncMock(
        return_value=FactCheckResponse(
            transcript_summary="Transcript summary for testing.",
            total_claims_extracted=1,
            verifications=[
                VerificationResult(
                    claim_id="c-api-1",
                    claim_text="Solar energy became the cheapest energy source in 2020.",
                    verdict=True,
                    verdict_label="True",
                    confidence=0.92,
                    reasoning="IEA World Energy Outlook 2020 confirmed solar is history's cheapest electricity.",
                    sources=["https://iea.org/reports/world-energy-outlook-2020"],
                )
            ],
            processing_time_seconds=1.2,
        )
    )

    app.dependency_overrides[get_workflow] = lambda: mock_workflow
    try:
        payload = {
            "transcript": "Solar energy officially became the cheapest energy source in history in 2020.",
            "speaker_name": "Energy Analyst",
            "max_claims": 2,
        }
        response = client.post("/api/v1/fact-check", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["total_claims_extracted"] == 1
        assert len(data["verifications"]) == 1
        assert data["verifications"][0]["verdict"] is True
        assert data["verifications"][0]["sources"] == ["https://iea.org/reports/world-energy-outlook-2020"]
    finally:
        app.dependency_overrides.clear()


def test_extract_claims_endpoint_with_dependency_override():
    """Verify POST /api/v1/extract-claims endpoint."""
    mock_workflow = MagicMock(spec=FactCheckerWorkflow)
    mock_extractor = MagicMock()
    mock_run = MagicMock()
    mock_run.output = ClaimExtractionResponse(
        claims=[
            Claim(
                id="c-extract-1",
                claim_text="The bridge was constructed in 1937.",
                speaker="Tour Guide",
                category="History",
            )
        ],
        summary_of_speech="Historical facts about the bridge.",
    )
    mock_extractor.run = AsyncMock(return_value=mock_run)
    mock_workflow.extractor_agent = mock_extractor

    app.dependency_overrides[get_workflow] = lambda: mock_workflow
    try:
        payload = {
            "transcript": "The Golden Gate bridge was constructed in 1937 according to historical records.",
            "speaker_name": "Tour Guide",
        }
        response = client.post("/api/v1/extract-claims", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert len(data["claims"]) == 1
        assert data["claims"][0]["claim_text"] == "The bridge was constructed in 1937."
        assert data["summary_of_speech"] == "Historical facts about the bridge."
    finally:
        app.dependency_overrides.clear()
