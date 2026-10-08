from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.tavily_service import TavilySearchService


@pytest.mark.asyncio
async def test_tavily_service_without_api_key():
    """Verify that search returns empty list safely if API key is absent."""
    service = TavilySearchService(api_key="")
    results = await service.search("sample query")
    assert results == []


@pytest.mark.asyncio
async def test_tavily_service_with_mock_client():
    """Verify that search maps Tavily output fields properly."""
    service = TavilySearchService(api_key="tvly-mock-key")
    mock_client = MagicMock()
    mock_client.search = AsyncMock(
        return_value={
            "results": [
                {
                    "title": "Bureau of Labor Statistics",
                    "url": "https://www.bls.gov/news.release/empsit.nr0.htm",
                    "content": "Total nonfarm payroll employment increased by 253,000 in April.",
                    "score": 0.98,
                }
            ]
        }
    )
    service._client = mock_client

    results = await service.search("unemployment statistics", max_results=1)
    assert len(results) == 1
    assert results[0]["title"] == "Bureau of Labor Statistics"
    assert results[0]["url"] == "https://www.bls.gov/news.release/empsit.nr0.htm"
    assert "253,000" in results[0]["snippet"]
    assert results[0]["score"] == 0.98


@pytest.mark.asyncio
async def test_fetch_page_content_beautifulsoup_cleanup():
    """Verify that BeautifulSoup strips script, style, nav, and returns clean text."""
    service = TavilySearchService(api_key="tvly-mock-key")
    html_sample = """
    <!DOCTYPE html>
    <html>
    <head><title>Test Report</title><style>body { font-size: 14px; }</style></head>
    <body>
        <nav><a href="/home">Home</a><a href="/about">About</a></nav>
        <article>
            <h1>Economic Report</h1>
            <p>Inflation decreased to 2.1% according to the latest central bank report.</p>
        </article>
        <script>console.log("analytics tracking");</script>
        <footer><p>Copyright 2024</p></footer>
    </body>
    </html>
    """

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.text = html_sample
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        extracted_text = await service.fetch_page_content("https://example.com/report")

        assert "Economic Report" in extracted_text
        assert "Inflation decreased to 2.1%" in extracted_text
        # Stripped elements
        assert "analytics tracking" not in extracted_text
        assert "font-size" not in extracted_text
        assert "Home" not in extracted_text
        assert "Copyright" not in extracted_text
