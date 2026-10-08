from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.claim import Claim, ClaimExtractionResponse
from app.models.verification import FactCheckRequest, VerificationResult
from app.services.fact_checker import FactCheckerWorkflow


@pytest.mark.asyncio
async def test_workflow_process_transcript_success():
    """Verify end-to-end workflow orchestration with mocked agents."""
    sample_claims = [
        Claim(
            id="c1",
            claim_text="The GDP grew by 2.8% in Q3 2024.",
            original_quote="Our GDP grew by 2.8% in Q3 2024.",
            speaker="Governor",
            category="Economy",
        )
    ]
    mock_extractor_agent = MagicMock()
    mock_extractor_run = MagicMock()
    mock_extractor_run.output = ClaimExtractionResponse(
        claims=sample_claims,
        summary_of_speech="Speech addressing state economic growth numbers.",
    )
    mock_extractor_agent.run = AsyncMock(return_value=mock_extractor_run)

    mock_verifier_agent = MagicMock()
    mock_verifier_run = MagicMock()
    mock_verifier_run.output = VerificationResult(
        claim_id="c1",
        claim_text="The GDP grew by 2.8% in Q3 2024.",
        verdict=True,
        verdict_label="True",
        confidence=0.96,
        reasoning="Bureau of Economic Analysis confirmed 2.8% annualized growth rate.",
        sources=["https://bea.gov/news/gdp-q3"],
    )
    mock_verifier_agent.run = AsyncMock(return_value=mock_verifier_run)

    mock_tavily_service = MagicMock()

    workflow = FactCheckerWorkflow(
        tavily_service=mock_tavily_service,
        extractor_agent=mock_extractor_agent,
        verifier_agent=mock_verifier_agent,
    )

    request = FactCheckRequest(
        transcript="Our GDP grew by 2.8% in Q3 2024 according to official reports.",
        speaker_name="Governor",
        max_claims=3,
    )

    response = await workflow.process_transcript(request)

    assert response.total_claims_extracted == 1
    assert len(response.verifications) == 1
    assert response.verifications[0].verdict is True
    assert response.verifications[0].claim_id == "c1"
    assert response.verifications[0].sources == ["https://bea.gov/news/gdp-q3"]
    assert response.processing_time_seconds >= 0.0


@pytest.mark.asyncio
async def test_workflow_process_transcript_no_claims():
    """Verify that workflow gracefully handles transcripts with no falsifiable claims."""
    mock_extractor_agent = MagicMock()
    mock_extractor_run = MagicMock()
    mock_extractor_run.output = ClaimExtractionResponse(
        claims=[],
        summary_of_speech="Inspirational speech with no empirical or falsifiable claims.",
    )
    mock_extractor_agent.run = AsyncMock(return_value=mock_extractor_run)

    workflow = FactCheckerWorkflow(
        extractor_agent=mock_extractor_agent,
        verifier_agent=MagicMock(),
    )

    request = FactCheckRequest(
        transcript="We must believe in our dreams and reach for the brightest stars.",
    )

    response = await workflow.process_transcript(request)
    assert response.total_claims_extracted == 0
    assert len(response.verifications) == 0
    assert "Inspirational speech" in (response.transcript_summary or "")


@pytest.mark.asyncio
async def test_workflow_verifier_error_fallback():
    """Verify that an exception in verifier agent produces an unverified fallback result."""
    claim = Claim(id="c-err", claim_text="Erroneous claim to verify.")

    mock_verifier_agent = MagicMock()
    mock_verifier_agent.run = AsyncMock(side_effect=RuntimeError("External LLM timeout"))

    workflow = FactCheckerWorkflow(
        verifier_agent=mock_verifier_agent,
    )

    result = await workflow.verify_single_claim(claim)
    assert result.claim_id == "c-err"
    assert result.verdict is False
    assert result.verdict_label == "Unverified (Error)"
    assert "External LLM timeout" in result.reasoning
