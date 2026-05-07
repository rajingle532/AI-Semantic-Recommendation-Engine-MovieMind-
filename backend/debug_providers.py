import sys
import os

# Add the backend directory to sys.path
sys.path.append(os.getcwd())

from app.services.tmdb import get_watch_providers
from app.config import settings

def test():
    movie_id = 27205 # Inception
    print(f"Testing Watch Providers for Inception (ID: {movie_id})...")
    providers = get_watch_providers(movie_id)
    print("Result:", providers)

if __name__ == "__main__":
    test()
