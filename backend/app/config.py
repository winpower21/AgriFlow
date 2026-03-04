from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings and configuration."""

    APP_NAME: str = "AgriFlow"
    # Database
    DATABASE_URL: str

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:5173"

    # Environment
    ENVIRONMENT: str = "development"

    # API
    OPENWEATHERMAP_API_KEY: str = ""
    GOOGLE_MAPS_API_KEY: str = ""

    # Application
    APP_NAME: str = "FastAPI Backend"
    VERSION: str = "1.0.0"

    @property
    def cors_origins(self) -> List[str]:
        """Parse ALLOWED_ORIGINS into a list."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
