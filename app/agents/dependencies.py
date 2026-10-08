from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.tavily_service import TavilySearchService


@dataclass
class AgentDependencies:
    """Runtime dependencies injected into Pydantic-AI agent tools via RunContext."""

    search_service: TavilySearchService
    speaker_context: str | None = None

