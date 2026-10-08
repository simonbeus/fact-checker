import logging
from typing import Any

import httpx
from bs4 import BeautifulSoup
from tavily import AsyncTavilyClient

from app.config import settings

logger = logging.getLogger(__name__)


class TavilySearchService:
    """Service wrapping Tavily search client and BeautifulSoup web scraping."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.tavily_api_key
        self._client: AsyncTavilyClient | None = None
        if self.api_key:
            self._client = AsyncTavilyClient(api_key=self.api_key)

    async def search(
        self,
        query: str,
        search_depth: str = "advanced",
        max_results: int = 5,
    ) -> list[dict[str, Any]]:
        """Search the web for trusted factual sources using Tavily."""
        if not self._client:
            logger.warning("Tavily API key is not configured. Returning empty search results.")
            return []

        try:
            response = await self._client.search(
                query=query,
                search_depth=search_depth,
                max_results=max_results,
                include_answer=False,
                include_raw_content=False,
            )
            raw_results = response.get("results", [])
            formatted = []
            for item in raw_results:
                formatted.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("content", ""),
                    "score": item.get("score", 0.0),
                })
            return formatted
        except Exception as exc:
            logger.error("Error executing Tavily search for query '%s': %s", query, exc)
            return []

    async def fetch_page_content(self, url: str, max_chars: int = 3000) -> str:
        """Fetch and scrape clean text from a source URL using BeautifulSoup."""
        headers = {
            "User-Agent": "FactCheckBot/1.0 (Trusted Evidence Collector; +https://factcheck.internal)"
        }
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(url, headers=headers)
                resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "html.parser")

            # Remove non-textual or layout elements
            for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form", "noscript"]):
                tag.decompose()

            # Extract clean body text
            text = soup.get_text(separator=" ", strip=True)
            return text[:max_chars]
        except Exception as exc:
            logger.warning("Failed to fetch page content from %s: %s", url, exc)
            return ""
