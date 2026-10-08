from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Fact-Checking API"
    app_version: str = "0.1.0"
    environment: str = "development"
    log_level: str = "INFO"

    # API Keys
    mistral_api_key: str = Field(default="", alias="MISTRAL_API_KEY")
    tavily_api_key: str = Field(default="", alias="TAVILY_API_KEY")

    # LLM Settings
    mistral_model: str = Field(default="mistral-large-latest", alias="MISTRAL_MODEL_NAME")

    # Evidence Search Defaults
    max_search_results: int = 5
    search_depth: str = "advanced"


settings = Settings()
