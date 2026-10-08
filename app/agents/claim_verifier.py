import json
import os

from pydantic_ai import Agent, RunContext
from pydantic_ai.models import Model
from pydantic_ai.models.mistral import MistralModel
from pydantic_ai.providers.mistral import MistralProvider

from app.agents.dependencies import AgentDependencies
from app.config import settings
from app.models.verification import VerificationResult

CLAIM_VERIFIER_SYSTEM_PROMPT = """You are an impartial, highly rigorous investigative fact-checker.
Your job is to verify a specific claim by gathering authoritative, empirical evidence and determining its truthfulness.

Verification Process:
1. FORMULATE SEARCH QUERIES: Use `search_trusted_sources` with precise, neutral search queries (targeting primary sources, government agencies, scientific journals, statistical offices, or established news organizations).
2. DEEP INSPECTION: If the snippets lack critical data, call `deep_read_webpage` on the most relevant URL to extract the complete article text.
3. WEIGH THE EVIDENCE: Compare the claim against the facts found. Check numbers, dates, attribution, and context.
4. DETERMINE VERDICT:
   - `verdict`: Set to `True` IF AND ONLY IF the core factual assertion is substantially supported by reliable evidence.
   - `verdict`: Set to `False` IF the claim is demonstrably false, contains debunked figures, or is materially misleading.
5. LABEL & EXPLAIN:
   - `verdict_label`: Provide a clear badge ('True', 'Mostly True', 'False', 'Misleading', or 'Unverified').
   - `reasoning`: Write a thorough, objective, multi-sentence explanation detailing the evidence found and the exact rationale behind the verdict.
   - `sources`: Include every reputable HTTP/HTTPS URL that directly supports the verdict.
   - `confidence`: Assign a score from 0.0 to 1.0 based on source authority and clarity of evidence.
"""


def create_claim_verifier_agent(
    model: str | Model | None = None,
    api_key: str | None = None,
) -> Agent[AgentDependencies, VerificationResult]:
    """Initialize the Pydantic-AI agent equipped with search and scraping tools to verify claims."""
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

    agent: Agent[AgentDependencies, VerificationResult] = Agent(
        model_instance,
        deps_type=AgentDependencies,
        output_type=VerificationResult,
        system_prompt=CLAIM_VERIFIER_SYSTEM_PROMPT,
    )

    @agent.tool
    async def search_trusted_sources(
        ctx: RunContext[AgentDependencies],
        query: str,
    ) -> str:
        """Search the web for authoritative sources and evidence related to the claim.
        
        Args:
            query: Specific, objective search query (e.g. 'US unemployment rate January 2023 BLS report').
        """
        results = await ctx.deps.search_service.search(query=query, max_results=5)
        if not results:
            return "No web search results found for this query."
        return json.dumps(results, indent=2)

    @agent.tool
    async def deep_read_webpage(
        ctx: RunContext[AgentDependencies],
        url: str,
    ) -> str:
        """Fetch and extract readable body text from a webpage using BeautifulSoup for deeper evidence analysis.
        
        Args:
            url: The HTTP/HTTPS web address to scrape and parse.
        """
        content = await ctx.deps.search_service.fetch_page_content(url=url)
        if not content:
            return f"Unable to fetch or parse content from URL: {url}"
        return f"Page extract from {url}:\n{content}"

    return agent

