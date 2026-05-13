import requests
import pandas as pd
import os
import time
import urllib3

# Simple fetch without complex SSL if possible
urllib3.disable_warnings()

# Configuration
API_KEY = "8265bd1679663a7ea12ac168da84d2e8"
BASE_URL = "https://api.themoviedb.org/3"
OUTPUT_FILE = "backend/data/tmdb_indian_movies.csv"

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
            # Try with verify=False for simple bypass
            response = requests.get(url, params=params, verify=False, timeout=10)
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
    if not os.path.exists("backend/data"):
        os.makedirs("backend/data")
        
    movies = fetch_hindi_movies(15) # Fetch ~300 movies
    if movies:
        df = pd.DataFrame(movies)
        df.to_csv(OUTPUT_FILE, index=False)
        print(f"Successfully saved {len(df)} movies to {OUTPUT_FILE}")
    else:
        print("No movies fetched.")
