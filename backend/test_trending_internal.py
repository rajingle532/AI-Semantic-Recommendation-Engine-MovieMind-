import os
import sys

# Add the current directory to sys.path to allow imports from app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from app.services.tmdb import get_trending_movies

print(f"Using TMDB API KEY: {settings.TMDB_API_KEY[:5]}***")
print("Fetching trending movies...")
try:
    movies = get_trending_movies()
    print(f"Success! Found {len(movies)} movies.")
    for m in movies[:3]:
        print(f" - {m['title']}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
