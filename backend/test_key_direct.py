import requests
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("TMDB_API_KEY")
url = f"https://api.tmdb.org/3/movie/popular?api_key={api_key}"

print(f"Testing TMDB API Key: {api_key[:5]}...")
try:
    resp = requests.get(url, timeout=10)
    print(f"Status Code: {resp.status_code}")
    if resp.status_code == 200:
        print(f"Success! Found {len(resp.json().get('results', []))} movies.")
    else:
        print(f"Error: {resp.text}")
except Exception as e:
    print(f"Exception: {e}")
