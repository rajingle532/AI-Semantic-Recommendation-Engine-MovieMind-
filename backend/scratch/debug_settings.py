import sys
import os

# Add the project root to sys.path to allow importing from app
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from backend.app.config import settings

print(f"TMDB_API_KEY: {'SET' if settings.TMDB_API_KEY else 'MISSING'}")
print(f"YOUTUBE_API_KEY: {'SET' if settings.YOUTUBE_API_KEY else 'MISSING'}")
print(f"SPOTIFY_CLIENT_ID: {'SET' if settings.SPOTIFY_CLIENT_ID else 'MISSING'}")
print(f"SPOTIFY_CLIENT_SECRET: {'SET' if settings.SPOTIFY_CLIENT_SECRET else 'MISSING'}")
print(f"GEMINI_API_KEY: {'SET' if settings.GEMINI_API_KEY else 'MISSING'}")

if settings.YOUTUBE_API_KEY:
    print(f"YouTube Key starts with: {settings.YOUTUBE_API_KEY[:5]}")
