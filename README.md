# Scalable Fact-Checking API

An asynchronous, AI-powered fact-checking service built with **FastAPI**, **Pydantic-AI**, **Mistral**, **Tavily Search**, and **BeautifulSoup4**. The system ingests raw speech transcripts, isolates objective and falsifiable claims, fetches authoritative source evidence from the web, and synthesizes structured verification reports tailored for human editorial review.

---

## Tech Stack

| Technology | Role |
| :--- | :--- |
| **Python 3.11+ / 3.12** | Core language runtime |
| **[uv](https://github.com/astral-sh/uv)** | Next-generation Python package manager and virtual environment tool |
| **[FastAPI](https://fastapi.tiangolo.com/)** | High-performance asynchronous web framework & OpenAPI documentation |
| **[Pydantic v2](https://docs.pydantic.dev/)** | Data validation, schemas, and typed serialization |
| **[Pydantic-AI](https://ai.pydantic.dev/)** | Type-safe agent framework for structured LLM workflows and tool calling |
| **[Mistral AI](https://mistral.ai/)** | State-of-the-art LLMs (`mistral-large-latest`, `mistral-small-latest`) |
| **[Tavily Search](https://tavily.com/)** | Search engine optimized for LLMs and trusted factual retrieval |
| **[BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/)** | HTML parsing and content sanitization for deep webpage inspection |

---

## Project Structure

```text
fact-check-api/
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules for Python, uv, and env files
├── .python-version           # Pinned Python version (3.12)
├── pyproject.toml            # Project dependencies and tool configurations
├── README.md                 # Project documentation and quickstart guide
├── app/
│   ├── __init__.py
│   ├── config.py             # App configuration via pydantic-settings
│   ├── main.py               # FastAPI entrypoint, middleware, and lifespan
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py         # API endpoints (/fact-check, /extract-claims, /health)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── claim.py          # Claim & ClaimExtractionResponse schemas
│   │   └── verification.py   # VerificationResult & FactCheckRequest/Response schemas
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── dependencies.py   # AgentDependencies for tool dependency injection
│   │   ├── claim_extractor.py# Pydantic-AI agent for claim identification
│   │   └── claim_verifier.py # Pydantic-AI agent with search & scraping tools
│   └── services/
│       ├── __init__.py
│       ├── tavily_service.py # Tavily API search client & BeautifulSoup scraper
│       └── fact_checker.py   # Asynchronous orchestration pipeline
└── tests/
    ├── __init__.py
    ├── test_api.py           # FastAPI endpoint integration tests
    ├── test_models.py        # Pydantic model validation tests
    ├── test_tavily_service.py# Search and HTML parsing tests
    └── test_workflow.py      # End-to-end agent workflow tests
```

---

## Environment Setup with `uv`

### 1. Initialize Project & Environment

```bash
# Initialize a new project (if starting from scratch)
uv init fact-check-api
cd fact-check-api

# Pin Python version
uv python pin 3.12
```

### 2. Add Dependencies

```bash
# Core dependencies
uv add fastapi "uvicorn[standard]" pydantic pydantic-settings pydantic-ai mistralai tavily-python beautifulsoup4 httpx python-dotenv

# Development & test dependencies
uv add --dev pytest pytest-asyncio ruff
```

### 3. Configure Environment Variables

Create your local `.env` file from the provided example:

```bash
cp .env.example .env
```

Configure the following API keys inside `.env`:

```env
# Mistral AI API Key
MISTRAL_API_KEY=your_mistral_api_key_here

# Tavily Search API Key
TAVILY_API_KEY=tvly-your_tavily_api_key_here

# Model selection (default: mistral-large-latest)
MISTRAL_MODEL_NAME=mistral-large-latest
```

---

## Running the Application

### Start the FastAPI Server

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Once running:
- **Interactive OpenAPI Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative ReDoc UI**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

## API Usage Examples

### End-to-End Fact-Check (`POST /api/v1/fact-check`)

Submits a raw speech transcript, isolates claims, searches evidence via Tavily, and returns verification verdicts.

```bash
curl -X POST "http://localhost:8000/api/v1/fact-check" \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Our administration created 15 million new jobs in the last two years, which is the fastest job growth in American history. Furthermore, inflation dropped to exactly 1.2% in June 2024.",
    "speaker_name": "President",
    "max_claims": 3
  }'
```

#### Example Response

```json
{
  "transcript_summary": "Remarks claiming historic job growth figures and specific inflation rates for June 2024.",
  "total_claims_extracted": 2,
  "verifications": [
    {
      "claim_id": "7b58e21a",
      "claim_text": "The administration created 15 million new jobs in the last two years.",
      "verdict": true,
      "verdict_label": "Mostly True",
      "confidence": 0.91,
      "reasoning": "BLS nonfarm payroll data indicates approximately 14.8 to 15.2 million cumulative net jobs were created over the specified 24-month window, reflecting post-pandemic economic recovery.",
      "sources": [
        "https://www.bls.gov/news.release/empsit.nr0.htm"
      ],
      "verified_at": "2026-10-08T09:40:00Z"
    },
    {
      "claim_id": "9c12a4f0",
      "claim_text": "Inflation dropped to exactly 1.2% in June 2024.",
      "verdict": false,
      "verdict_label": "False",
      "confidence": 0.96,
      "reasoning": "According to the Consumer Price Index report from the Bureau of Labor Statistics, the 12-month CPI inflation rate for June 2024 was 3.0%, not 1.2%.",
      "sources": [
        "https://www.bls.gov/cpi/"
      ],
      "verified_at": "2026-10-08T09:40:01Z"
    }
  ],
  "processing_time_seconds": 4.12
}
```

---

## Testing & Quality Assurance

Run the test suite:

```bash
uv run --extra dev pytest -v
```

Run code formatting and lint checks:

```bash
uv run --extra dev ruff check .
```
