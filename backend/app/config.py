"""
Cogent Configuration Module
Loads settings from environment variables with Pydantic validation.
"""

# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # ---- Application Metadata ----
    APP_NAME: str = "Cogent"

    # ---- Database ----
    DATABASE_URL: str = "postgresql+psycopg://cogent_user:cogent_secret_2024@localhost:5432/cogent_db"

    # ---- JWT Authentication ----
    JWT_SECRET: str = "cogent-jwt-secret-key-change-in-production-2024"
    JWT_SECRET_KEY: str = "cogent-jwt-secret-key-change-in-production-2024"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440  # 24 hours
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # ---- LLM Configuration (Gemini / Groq / OpenAI / Offline) ----
    LLM_PROVIDER: str = "auto"  # "gemini", "groq", "openai", "offline", or "auto"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.8-flash"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    OPENAI_API_KEY: str = "sk-placeholder"
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_BASE_URL: str = ""

    # ---- Embedding Model ----
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"

    # ---- Web Search / Acquisition ----
    TAVILY_API_KEY: str = ""

    # ---- Application ----
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # ---- Storage Paths ----
    FAISS_INDEX_PATH: str = "/app/data/faiss/cogent.index"
    UPLOAD_DIR: str = "/app/data/uploads"

    # ---- Layer 1: User Interaction Config ----
    SUFFICIENCY_THRESHOLD: float = 0.70
    MAX_CLARIFICATION_ROUNDS: int = 2
    ENTROPY_VALIDATION_SAMPLES: int = 3
    ENTROPY_PENALTY_THRESHOLD: float = 0.4

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


# Singleton settings instance
settings = Settings()
