
from fastapi import APIRouter, Depends, HTTPException, status

from app.models.claim import ClaimExtractionResponse
from app.models.verification import FactCheckRequest, FactCheckResponse
from app.services.fact_checker import FactCheckerWorkflow

router = APIRouter(prefix="/api/v1", tags=["Fact Checking"])

_workflow: FactCheckerWorkflow | None = None


def get_workflow() -> FactCheckerWorkflow:
    """Dependency provider for FactCheckerWorkflow."""
    global _workflow
    if _workflow is None:
        _workflow = FactCheckerWorkflow()
    return _workflow


@router.post(
    "/fact-check",
    response_model=FactCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="End-to-end fact checking of speech transcripts",
    description=(
        "Extracts falsifiable claims from raw speech using Mistral, searches for authoritative "
        "evidence using Tavily, and returns structured verification verdicts for human editorial review."
    ),
)
async def fact_check_transcript(
    request: FactCheckRequest,
    workflow: FactCheckerWorkflow = Depends(get_workflow),
) -> FactCheckResponse:
    """Analyze a transcript, extract falsifiable claims, search evidence, and return verified results."""
    try:
        return await workflow.process_transcript(request)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fact checking workflow failed: {exc!s}",
        )


@router.post(
    "/extract-claims",
    response_model=ClaimExtractionResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract falsifiable claims without verifying",
    description="Isolates objective, verifiable claims from the transcript without performing web searches.",
)
async def extract_claims_only(
    request: FactCheckRequest,
    workflow: FactCheckerWorkflow = Depends(get_workflow),
) -> ClaimExtractionResponse:
    """Extract claims from a speech transcript for preview or manual selection."""
    try:
        prompt = (
            f"Extract up to {request.max_claims} falsifiable claims from this speech transcript.\n"
            f"Speaker: {request.speaker_name or 'Unspecified'}\n\n"
            f"Transcript:\n\"\"\"{request.transcript}\"\"\""
        )
        extraction_run = await workflow.extractor_agent.run(prompt)
        data = getattr(extraction_run, "output", getattr(extraction_run, "data", None))
        if not data:
            return ClaimExtractionResponse(claims=[])
        return data
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Claim extraction failed: {exc!s}",
        )


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check",
    tags=["System"],
)
async def health_check():
    """Health probe indicating service availability."""
    return {"status": "ok", "service": "fact-check-api"}
