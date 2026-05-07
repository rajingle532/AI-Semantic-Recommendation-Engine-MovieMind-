"""
Configuration module — loads environment variables from .env file.
"""
import os
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))


class Settings:
    """Application settings loaded from environment variables."""

    # TMDB API
    TMDB_API_KEY: str = os.getenv("TMDB_API_KEY", "")
    TMDB_BASE_URL: str = "https://api.themoviedb.org/3"
    TMDB_IMAGE_URL: str = "https://image.tmdb.org/t/p/w500"

    # MongoDB
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017/movie_recommender")
    DB_NAME: str = "movie_recommender"

    # JWT Authentication
    JWT_SECRET: str = os.getenv("JWT_SECRET", "change-this-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_HOURS: int = 24

    # Google Auth
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")

    # CORS
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")


settings = Settings()
