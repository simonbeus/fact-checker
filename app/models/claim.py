import uuid

from pydantic import BaseModel, Field


class Claim(BaseModel):
    """Represents an extracted, falsifiable factual claim from speech transcript."""

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4())[:8],
        description="Unique identifier for the claim",
    )
    claim_text: str = Field(
        ...,
        description="The clear, objective, and falsifiable statement extracted from the transcript",
        examples=["The unemployment rate dropped to 3.4% in January 2023."],
    )
    original_quote: str | None = Field(
        None,
        description="The verbatim excerpt or sentence from the speech where the claim appeared",
    )
    speaker: str | None = Field(
        None,
        description="Speaker identified as having made the claim",
    )
    category: str | None = Field(
        None,
        description="Category domain of the statement (e.g. Economy, Health, Science, Politics, History)",
    )


class ClaimExtractionResponse(BaseModel):
    """Container schema for the output of the Claim Extractor Agent."""

    claims: list[Claim] = Field(
        default_factory=list,
        description="List of extracted falsifiable claims",
    )
    summary_of_speech: str | None = Field(
        None,
        description="Brief high-level summary of the speech transcript",
    )
