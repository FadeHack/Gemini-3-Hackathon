"""
Application settings using Pydantic Settings
Loads configuration from environment variables (.env file)
"""

from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment"""

    # Gemini API
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.0-flash-exp"
    GEMINI_TIMEOUT: int = 30
    GEMINI_MAX_RETRIES: int = 3

    # Weather API
    WEATHER_API_KEY: str
    WEATHER_API_URL: str = "https://api.openweathermap.org/data/2.5/weather"

    # Application Settings
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Demo Mode (for hackathon fallback)
    DEMO_MODE: bool = False

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:3001"

    # Rate Limiting
    MAX_REQUESTS_PER_MINUTE: int = 60
    RATE_LIMIT_ENABLED: bool = False

    # WebSocket
    WEBSOCKET_PING_INTERVAL: int = 20
    WEBSOCKET_PING_TIMEOUT: int = 30

    # Data Paths
    STORE_DATA_PATH: str = "./data/stores"
    PRODUCT_CATALOG_PATH: str = "./data/products.json"
    FESTIVAL_CALENDAR_PATH: str = "./data/festivals.json"
    DISTRIBUTOR_PRICING_PATH: str = "./data/distributors.json"
    ABBREVIATIONS_PATH: str = "./data/abbreviations.json"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse ALLOWED_ORIGINS string into list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return not self.DEBUG

    def get_store_path(self, store_id: str) -> Path:
        """Get path to store data file"""
        return Path(self.STORE_DATA_PATH) / f"{store_id}.json"

    def __repr__(self) -> str:
        """Safe repr that doesn't expose API keys"""
        return (
            f"Settings("
            f"DEBUG={self.DEBUG}, "
            f"PORT={self.PORT}, "
            f"DEMO_MODE={self.DEMO_MODE}, "
            f"GEMINI_API_KEY={'***' if self.GEMINI_API_KEY else 'NOT_SET'}, "
            f"WEATHER_API_KEY={'***' if self.WEATHER_API_KEY else 'NOT_SET'}"
            f")"
        )


# Global settings instance
settings = Settings()
