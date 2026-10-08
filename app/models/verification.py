from datetime import UTC, datetime

from pydantic import BaseModel, Field


class VerificationResult(BaseModel):
    """Structured evaluation of a claim for human editorial review."""

    claim_id: str = Field(
        ...,
        description="ID of the corresponding extracted claim",
    )
    claim_text: str = Field(
        ...,
        description="The falsifiable claim text being evaluated",
    )
    verdict: bool = Field(
        ...,
        description="Boolean verdict: True if factually true/supported, False if false/unsupported/misleading",
    )
    verdict_label: str = Field(
        default="Verified",
        description="Editorial badge: 'True', 'Mostly True', 'False', 'Misleading', or 'Unverified'",
    )
    confidence: float = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
        description="Model confidence score between 0.0 and 1.0",
    )
    reasoning: str = Field(
        ...,
        description="Detailed analytical reasoning synthesizing search evidence and explaining the verdict",
    )
    sources: list[str] = Field(
        default_factory=list,
        description="List of authoritative source URLs consulted and cited as evidence",
    )
    verified_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="UTC timestamp of when the verification was executed",
    )


class FactCheckRequest(BaseModel):
    """Payload for submitting a speech transcript for fact checking."""

    transcript: str = Field(
        ...,
        min_length=15,
        description="Raw speech transcript string to extract and fact-check",
        examples=[
            "Our administration created 15 million new jobs in the last two years, which is the fastest job growth in American history. Furthermore, inflation dropped to exactly 1.2% in June 2024."
        ],
    )
    speaker_name: str | None = Field(
        None,
        description="Name of the speaker or public figure (provides context for searching)",
    )
    max_claims: int | None = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of claims to extract and verify",
    )


class FactCheckResponse(BaseModel):
    """Complete structured response returned for human review."""

    transcript_summary: str | None = Field(
        None,
        description="Summary of the analyzed speech transcript",
    )
    total_claims_extracted: int = Field(
        ...,
        description="Total number of falsifiable claims identified",
    )
    verifications: list[VerificationResult] = Field(
        default_factory=list,
        description="Verification results for human review",
    )
    processing_time_seconds: float = Field(
        ...,
        description="Execution duration in seconds",
    )
