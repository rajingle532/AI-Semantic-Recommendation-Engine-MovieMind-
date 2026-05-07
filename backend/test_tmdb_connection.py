import sys
import os
import requests

# Add the backend directory to sys.path
sys.path.append(os.getcwd())

from app.config import settings

def test_tmdb():
    api_key = settings.TMDB_API_KEY
    print(f"Testing TMDB API Key: {api_key[:5]}... (hidden)")
    
    url = "https://api.themoviedb.org/3/trending/movie/week"
    params = {"api_key": api_key, "language": "en-US"}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            results = response.json().get("results", [])
            print(f"Successfully fetched {len(results)} movies!")
        else:
            print(f"Error Response: {response.text}")
    except Exception as e:
        print(f"Exception during API call: {e}")

if __name__ == "__main__":
    test_tmdb()
