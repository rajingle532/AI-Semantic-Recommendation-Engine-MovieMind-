"""
Configuration module - loads environment variables from .env file.
"""
import os
from dotenv import load_dotenv

# Try to load .env from multiple locations
env_paths = [
    os.path.join(os.getcwd(), '.env'),
    os.path.join(os.path.dirname(__file__), '..', '..', '.env'),
    os.path.join(os.path.dirname(__file__), '..', '.env'),
]

for path in env_paths:
    if os.path.exists(path):
        load_dotenv(path)
        break
else:
    load_dotenv()  # Fallback to default


def _is_enabled(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).lower() in {"1", "true", "yes", "on"}


def _required_in_production(name: str, dev_default: str) -> str:
    value = os.getenv(name)
    environment = os.getenv("ENVIRONMENT", os.getenv("APP_ENV", "development")).lower()
    if value:
        return value
    if environment in {"production", "prod"}:
        raise RuntimeError(f"{name} must be set when ENVIRONMENT=production.")
    return dev_default


class Settings:
    """Application settings loaded from environment variables."""

    ENVIRONMENT: str = os.getenv("ENVIRONMENT", os.getenv("APP_ENV", "development")).lower()

    # TMDB API
    TMDB_API_KEY: str = os.getenv("TMDB_API_KEY", "")
    TMDB_BASE_URL: str = "https://api.tmdb.org/3"
    TMDB_IMAGE_URL: str = "https://image.tmdb.org/t/p/w500"

    # MongoDB
    MONGODB_URI: str = os.getenv("MONGODB_URI") or "mongodb://localhost:27017/movie_recommender"
    DB_NAME: str = "movie_recommender"
    MONGODB_TLS_ALLOW_INVALID_CERTIFICATES: bool = _is_enabled("MONGODB_TLS_ALLOW_INVALID_CERTIFICATES")

    # JWT Authentication
    JWT_SECRET: str = _required_in_production("JWT_SECRET", "dev-only-insecure-jwt-secret")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_HOURS: int = 24

    # Google Auth
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")

    # Affiliate Marketing
    AFFILIATE_TAG: str = os.getenv("AFFILIATE_TAG", "your-affiliate-id")

    # CORS
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

    # External AI & Search
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    SERP_API_KEY: str = os.getenv("SERP_API_KEY", "")
    YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY", "")
    SPOTIFY_CLIENT_ID: str = os.getenv("SPOTIFY_CLIENT_ID", "")
    SPOTIFY_CLIENT_SECRET: str = os.getenv("SPOTIFY_CLIENT_SECRET", "")

    # Email Settings
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")


settings = Settings()
