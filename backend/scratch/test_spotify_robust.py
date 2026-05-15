import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import base64
import os
from dotenv import load_dotenv

load_dotenv()
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[ 500, 502, 503, 504 ])
session.mount('https://', HTTPAdapter(max_retries=retries))

print("Fetching token...")
auth_string = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
auth_base64 = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")
headers = {
    "Authorization": f"Basic {auth_base64}",
    "Content-Type": "application/x-www-form-urlencoded"
}
data = {"grant_type": "client_credentials"}

try:
    res = session.post("https://accounts.spotify.com/api/token", headers=headers, data=data, timeout=10)
    print(f"Token status: {res.status_code}")
    if res.status_code == 200:
        token = res.json().get("access_token")
        print("Token retrieved successfully.")
        
        # Test Search
        headers = {"Authorization": f"Bearer {token}"}
        movie_title = "Interstellar"
        print(f"Searching for {movie_title}...")
        params = {"q": movie_title, "type": "track", "limit": 5}
        search_res = session.get("https://api.spotify.com/v1/search", headers=headers, params=params, timeout=15)
        print(f"Search status: {search_res.status_code}")
        if search_res.status_code == 200:
            tracks = search_res.json().get("tracks", {}).get("items", [])
            print(f"Found {len(tracks)} tracks.")
            if tracks:
                print(f"First track: {tracks[0]['name']}")
    else:
        print(res.text)
except Exception as e:
    print(f"ERROR: {type(e).__name__} - {e}")
