import os

from pydantic_ai import Agent
from pydantic_ai.models import Model
from pydantic_ai.models.mistral import MistralModel
from pydantic_ai.providers.mistral import MistralProvider

from app.config import settings
from app.models.claim import ClaimExtractionResponse

CLAIM_EXTRACTOR_SYSTEM_PROMPT = """You are an elite investigative fact-checker and linguistic analyst.
Your mission is to read raw, unstructured speech transcripts and extract distinct, falsifiable factual claims.

Rules for claim extraction:
1. ONLY extract claims that can be proven True or False using objective facts, official data, or empirical evidence.
   - Examples of valid claims: "Unemployment hit 3.4% last quarter", "Country X signed Treaty Y in 2021", "State funding decreased by 12%".
   - Examples to IGNORE: Opinions, moral value judgments, hyperbole, subjective predictions, figurative speech, or generic praise.
2. Formulate each claim into a concise, unambiguous, and standalone declarative sentence.
3. Keep the original quote from the transcript in `original_quote`.
4. Categorize each claim (e.g., Economics, Healthcare, Climate & Science, Foreign Policy, Crime, History).
5. Provide a concise 1-2 sentence summary of the speech transcript in `summary_of_speech`.
"""


def create_claim_extractor_agent(
    model: str | Model | None = None,
    api_key: str | None = None,
) -> Agent[None, ClaimExtractionResponse]:
    """Initialize the Pydantic-AI agent responsible for extracting claims from speech."""
    if model is None:
        key = api_key or settings.mistral_api_key or os.environ.get("MISTRAL_API_KEY", "")
        provider = MistralProvider(api_key=key if key else "placeholder-key")
        model_name = settings.mistral_model or "mistral-large-latest"
        model_instance = MistralModel(model_name, provider=provider)
    elif isinstance(model, str):
        key = api_key or settings.mistral_api_key or os.environ.get("MISTRAL_API_KEY", "")
        provider = MistralProvider(api_key=key if key else "placeholder-key")
        model_instance = MistralModel(model, provider=provider)
    else:
        model_instance = model

    return Agent(
        model_instance,
        output_type=ClaimExtractionResponse,
        system_prompt=CLAIM_EXTRACTOR_SYSTEM_PROMPT,
    )

