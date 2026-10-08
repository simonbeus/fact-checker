import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import settings

# Configure structured logging
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("fact_check_api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup and shutdown hooks."""
    logger.info("Initializing %s (version %s)...", settings.app_name, settings.app_version)
    if not settings.mistral_api_key:
        logger.warning("MISTRAL_API_KEY is not configured. Live LLM agent calls will fail.")
    if not settings.tavily_api_key:
        logger.warning("TAVILY_API_KEY is not configured. Web searches will return empty results.")
    yield
    logger.info("Terminating %s services...", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Scalable Fact-Checking API powered by FastAPI, Pydantic-AI, Mistral LLM, "
        "Tavily Search, and BeautifulSoup4 for automated claim extraction and evidence-backed verification."
    ),
    lifespan=lifespan,
)

# Cross-Origin Resource Sharing (CORS) middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(router)


@app.get("/", tags=["System"])
async def root():
    """Root metadata endpoint with pointers to OpenAPI documentation."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "documentation": "/docs",
        "health_check": "/api/v1/health",
    }
