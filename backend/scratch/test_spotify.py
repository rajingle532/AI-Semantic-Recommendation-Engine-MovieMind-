import requests
import base64
import os
from dotenv import load_dotenv

load_dotenv() # Load root .env

SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

print(f"ID: {SPOTIFY_CLIENT_ID[:5]}")

auth_string = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
auth_base64 = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")
headers = {
    "Authorization": f"Basic {auth_base64}",
    "Content-Type": "application/x-www-form-urlencoded"
}
data = {"grant_type": "client_credentials"}
res = requests.post("https://accounts.spotify.com/api/token", headers=headers, data=data)
token = res.json().get("access_token")

headers = {"Authorization": f"Bearer {token}"}

# Test Album Search
movie_title = "Interstellar"
queries = [
    f"{movie_title} soundtrack",
    f"{movie_title} original motion picture soundtrack",
    f"{movie_title} OST",
    movie_title
]
for q in queries:
    params = {"q": q, "type": "album", "limit": 1}
    search_res = requests.get("https://api.spotify.com/v1/search", headers=headers, params=params)
    print(f"Query: {q} - Status: {search_res.status_code}")
    if search_res.status_code == 200:
        albums = search_res.json().get("albums", {}).get("items", [])
        print(f"  Found {len(albums)} albums")
    else:
        print(search_res.text)

# Test Track Search
params = {"q": movie_title, "type": "track", "limit": 10}
search_res = requests.get("https://api.spotify.com/v1/search", headers=headers, params=params)
print(f"Fallback Query - Status: {search_res.status_code}")
if search_res.status_code == 200:
    tracks = search_res.json().get("tracks", {}).get("items", [])
    print(f"  Found {len(tracks)} tracks")
else:
    print(search_res.text)
