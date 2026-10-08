import pytest
from pydantic import ValidationError

from app.models.claim import Claim
from app.models.verification import (
    FactCheckRequest,
    FactCheckResponse,
    VerificationResult,
)


def test_claim_model_creation():
    """Verify that Claim model generates an ID and holds expected fields."""
    claim = Claim(
        claim_text="The GDP grew by 2.8% in the third quarter of 2024.",
        speaker="Finance Minister",
        category="Economy",
    )
    assert claim.id is not None
    assert len(claim.id) > 0
    assert claim.claim_text == "The GDP grew by 2.8% in the third quarter of 2024."
    assert claim.speaker == "Finance Minister"
    assert claim.category == "Economy"


def test_verification_result_model():
    """Verify that VerificationResult encapsulates boolean verdict and sources."""
    result = VerificationResult(
        claim_id="c123",
        claim_text="The GDP grew by 2.8% in the third quarter of 2024.",
        verdict=True,
        verdict_label="True",
        confidence=0.95,
        reasoning="Bureau of Economic Analysis confirmed a 2.8% annualized growth rate for Q3 2024.",
        sources=[
            "https://www.bea.gov/data/gdp/gross-domestic-product",
            "https://www.reuters.com/markets/us-q3-gdp-2024",
        ],
    )
    assert result.verdict is True
    assert result.confidence == 0.95
    assert len(result.sources) == 2
    assert "bea.gov" in result.sources[0]
    assert result.verified_at is not None


def test_verification_result_confidence_bounds():
    """Verify that confidence score must stay within [0.0, 1.0]."""
    with pytest.raises(ValidationError):
        VerificationResult(
            claim_id="c1",
            claim_text="Invalid confidence test",
            verdict=False,
            confidence=1.5,  # Exceeds max 1.0
            reasoning="Invalid confidence test",
            sources=[],
        )


def test_fact_check_request_validation():
    """Verify minimum length validation on raw transcript input."""
    with pytest.raises(ValidationError):
        FactCheckRequest(transcript="Too short")

    valid_request = FactCheckRequest(
        transcript="This speech transcript contains enough length to satisfy validation thresholds.",
        speaker_name="Senator Smith",
        max_claims=3,
    )
    assert valid_request.max_claims == 3
    assert valid_request.speaker_name == "Senator Smith"


def test_fact_check_response_serialization():
    """Verify end-to-end response serialization to dictionary and JSON."""
    response = FactCheckResponse(
        transcript_summary="A policy address discussing economic growth figures.",
        total_claims_extracted=1,
        verifications=[
            VerificationResult(
                claim_id="c999",
                claim_text="Unemployment dropped to historic lows.",
                verdict=True,
                verdict_label="True",
                reasoning="Supported by official labor statistics.",
                sources=["https://www.bls.gov/news.release/empsit.nr0.htm"],
            )
        ],
        processing_time_seconds=2.45,
    )

    data = response.model_dump()
    assert data["total_claims_extracted"] == 1
    assert data["verifications"][0]["verdict"] is True
    assert data["processing_time_seconds"] == 2.45
