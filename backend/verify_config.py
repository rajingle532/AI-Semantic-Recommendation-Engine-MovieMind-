from app.config import settings
print(f"TMDB_API_KEY: {settings.TMDB_API_KEY[:5]}...")
print(f"MONGODB_URI: {settings.MONGODB_URI[:20]}...")
print(f"FRONTEND_URL: {settings.FRONTEND_URL}")
