"""
Application Configuration
==========================

Centralises all environment-based settings using ``pydantic-settings``.
Values are loaded from environment variables (or from a ``.env`` file in the
backend directory) at import time.

Required environment variables (no defaults):
    - ``DATABASE_URL``  — SQLAlchemy-compatible PostgreSQL connection string.
    - ``SECRET_KEY``    — Secret used to sign JWT tokens (HS256).

Optional / defaulted variables:
    - ``ALGORITHM``                 — JWT signing algorithm (default: HS256).
    - ``ACCESS_TOKEN_EXPIRE_MINUTES`` — Token lifetime in minutes (default: 60).
    - ``ALLOWED_ORIGINS``           — Comma-separated CORS origins (default: localhost:5173).
    - ``ENVIRONMENT``               — ``development`` or ``production`` (default: development).
    - ``OPENWEATHERMAP_API_KEY``    — Key for OpenWeatherMap integration.
    - ``GOOGLE_MAPS_API_KEY``       — Key for Google Maps integration.
    - ``APP_NAME`` / ``VERSION``    — Metadata shown in OpenAPI docs.
"""

from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Pydantic Settings model that reads configuration from environment
    variables and/or ``.env`` files.

    Attributes are grouped by concern: database, security, CORS,
    environment, external API keys, and application metadata.
    """

    APP_NAME: str = "AgriFlow"

    # -- Database -------------------------------------------------------
    # Full SQLAlchemy connection URL, e.g.
    # ``postgresql+psycopg://user:pass@localhost:5432/agriflow``
    DATABASE_URL: str

    # -- Security / JWT -------------------------------------------------
    # SECRET_KEY must be a strong random string in production; it is used
    # by python-jose to sign and verify HS256 JWT tokens.
    SECRET_KEY: str
    ALGORITHM: str = "HS256"  # JWT signing algorithm
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # Token validity window

    # -- CORS -----------------------------------------------------------
    # Comma-separated origins string; parsed into a list via the
    # ``cors_origins`` property (see below).
    ALLOWED_ORIGINS: str

    # -- Environment ----------------------------------------------------
    # Controls behaviour like SQLAlchemy SQL echo and uvicorn hot-reload.
    ENVIRONMENT: str = "development"

    # -- File uploads ---------------------------------------------------
    # Root directory for uploaded files. Use an absolute path in production.
    UPLOAD_DIR: str = "uploads"

    # -- External API keys ----------------------------------------------
    OPENWEATHERMAP_API_KEY: str = ""  # Optional — weather data integration
    GOOGLE_MAPS_API_KEY: str = ""  # Optional — maps / geocoding

    # -- Application metadata -------------------------------------------
    # NOTE: APP_NAME is declared twice (above and here). The second
    # declaration overrides the first due to Python class body semantics.
    APP_NAME: str = "FastAPI Backend"
    VERSION: str = "1.0.0"

    @property
    def cors_origins(self) -> List[str]:
        """Split the comma-separated ``ALLOWED_ORIGINS`` string into a list
        suitable for FastAPI's ``CORSMiddleware``."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    class Config:
        env_file = ".env"  # Auto-load .env file from working directory
        case_sensitive = True  # Env var names must match attribute names exactly


# Module-level singleton — imported throughout the app as ``settings``.
settings = Settings()
