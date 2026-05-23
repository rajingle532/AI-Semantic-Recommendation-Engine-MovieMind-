import os
from pathlib import Path
import time
import urllib3

import pandas as pd
import requests

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional convenience for local runs
    load_dotenv = None

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if load_dotenv:
    load_dotenv(PROJECT_ROOT / ".env")

# Configuration
API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"
OUTPUT_FILE = PROJECT_ROOT / "backend" / "data" / "tmdb_indian_movies.csv"
VERIFY_SSL = os.getenv("TMDB_VERIFY_SSL", "true").lower() not in {"0", "false", "no"}

if not VERIFY_SSL:
    urllib3.disable_warnings()


def fetch_hindi_movies(pages=10):
    all_movies = []
    print(f"Fetching {pages} pages of Hindi movies...")
    
    for page in range(1, pages + 1):
        url = f"{BASE_URL}/discover/movie"
        params = {
            "api_key": API_KEY,
            "with_original_language": "hi",
            "region": "IN",
            "sort_by": "popularity.desc",
            "page": page
        }
        
        try:
            response = requests.get(url, params=params, verify=VERIFY_SSL, timeout=10)
            if response.status_code == 200:
                results = response.json().get("results", [])
                for m in results:
                    all_movies.append({
                        "id": m.get("id"),
                        "title": m.get("title"),
                        "overview": m.get("overview"),
                        "genres": m.get("genre_ids"), # Just IDs for now to be fast
                        "popularity": m.get("popularity"),
                        "vote_average": m.get("vote_average"),
                        "vote_count": m.get("vote_count"),
                        "release_date": m.get("release_date"),
                        "original_language": "hi"
                    })
                print(f"Page {page} done ({len(results)} movies).")
                time.sleep(1) # Be gentle
            else:
                print(f"Error on page {page}: {response.status_code}")
        except Exception as e:
            print(f"Failed page {page}: {e}")
            
    return all_movies


if __name__ == "__main__":
    if not API_KEY:
        raise RuntimeError("TMDB_API_KEY must be set in the environment before generating the dataset.")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        
    movies = fetch_hindi_movies(15)  # Fetch about 300 movies
    if movies:
        df = pd.DataFrame(movies)
        df.to_csv(OUTPUT_FILE, index=False)
        print(f"Successfully saved {len(df)} movies to {OUTPUT_FILE}")
    else:
        print("No movies fetched.")
