import asyncio
import logging
import time

from app.agents.claim_extractor import create_claim_extractor_agent
from app.agents.claim_verifier import create_claim_verifier_agent
from app.agents.dependencies import AgentDependencies
from app.models.claim import Claim
from app.models.verification import (
    FactCheckRequest,
    FactCheckResponse,
    VerificationResult,
)
from app.services.tavily_service import TavilySearchService

logger = logging.getLogger(__name__)


class FactCheckerWorkflow:
    """End-to-end orchestration workflow for fact checking speech transcripts."""

    def __init__(
        self,
        tavily_service: TavilySearchService | None = None,
        extractor_agent=None,
        verifier_agent=None,
    ):
        self.tavily_service = tavily_service or TavilySearchService()
        self.extractor_agent = extractor_agent or create_claim_extractor_agent()
        self.verifier_agent = verifier_agent or create_claim_verifier_agent()

    async def verify_single_claim(
        self,
        claim: Claim,
        speaker: str | None = None,
    ) -> VerificationResult:
        """Verify an individual claim using the Claim Verifier agent."""
        deps = AgentDependencies(
            search_service=self.tavily_service,
            speaker_context=speaker or claim.speaker,
        )

        prompt = (
            f"Please verify this extracted claim:\n"
            f"- Claim ID: {claim.id}\n"
            f"- Claim: \"{claim.claim_text}\"\n"
            f"- Speaker: {claim.speaker or speaker or 'Unknown'}\n"
            f"- Category: {claim.category or 'General'}\n"
            f"- Original Speech Excerpt: {claim.original_quote or 'N/A'}\n\n"
            f"Perform necessary searches, inspect relevant sources, and deliver your structured verification verdict."
        )

        try:
            run_result = await self.verifier_agent.run(prompt, deps=deps)
            verification = getattr(run_result, "output", getattr(run_result, "data", None))

            if not isinstance(verification, VerificationResult):
                raise ValueError("Verification agent output did not conform to VerificationResult model")

            # Guarantee claim ID and text consistency
            verification.claim_id = claim.id
            verification.claim_text = claim.claim_text
            return verification

        except Exception as exc:
            logger.error("Error verifying claim '%s' (%s): %s", claim.claim_text, claim.id, exc)
            return VerificationResult(
                claim_id=claim.id,
                claim_text=claim.claim_text,
                verdict=False,
                verdict_label="Unverified (Error)",
                confidence=0.0,
                reasoning=f"Automatic verification failed due to error: {exc!s}",
                sources=[],
            )

    async def process_transcript(self, request: FactCheckRequest) -> FactCheckResponse:
        """Run the end-to-end extraction and concurrent verification workflow."""
        start_time = time.perf_counter()

        # Step 1: Extract falsifiable claims using Pydantic-AI Extractor Agent
        logger.info("Extracting claims from transcript (length: %d chars)...", len(request.transcript))
        extraction_prompt = (
            f"Extract up to {request.max_claims} falsifiable claims from this speech transcript.\n"
            f"Speaker: {request.speaker_name or 'Unspecified'}\n\n"
            f"Transcript:\n\"\"\"{request.transcript}\"\"\""
        )

        extraction_run = await self.extractor_agent.run(extraction_prompt)
        extraction_data = getattr(extraction_run, "output", getattr(extraction_run, "data", None))

        claims = extraction_data.claims if extraction_data else []
        speech_summary = extraction_data.summary_of_speech if extraction_data else None

        if not claims:
            logger.info("No falsifiable claims extracted from transcript.")
            elapsed = time.perf_counter() - start_time
            return FactCheckResponse(
                transcript_summary=speech_summary or "No falsifiable claims detected in the provided transcript.",
                total_claims_extracted=0,
                verifications=[],
                processing_time_seconds=round(elapsed, 2),
            )

        # Enforce maximum claims threshold
        if request.max_claims and len(claims) > request.max_claims:
            claims = claims[: request.max_claims]

        logger.info(
            "Extracted %d claims. Starting concurrent verification pipeline with Tavily and Mistral...",
            len(claims),
        )

        # Step 2: Concurrently verify all claims using asyncio.gather
        verification_tasks = [
            self.verify_single_claim(claim=claim, speaker=request.speaker_name)
            for claim in claims
        ]
        verifications = await asyncio.gather(*verification_tasks)

        elapsed = time.perf_counter() - start_time
        logger.info("Completed verification of %d claims in %.2f seconds.", len(claims), elapsed)

        return FactCheckResponse(
            transcript_summary=speech_summary,
            total_claims_extracted=len(claims),
            verifications=list(verifications),
            processing_time_seconds=round(elapsed, 2),
        )
