import requests
import base64
import os
from dotenv import load_dotenv

load_dotenv('backend/.env')

YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

print(f"YouTube Key: {YOUTUBE_API_KEY[:5]}...")
print(f"Spotify ID: {SPOTIFY_CLIENT_ID[:5]}...")

def test_youtube():
    print("\nTesting YouTube...")
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": "Inception 2010 official song",
        "type": "video",
        "maxResults": 2,
        "key": YOUTUBE_API_KEY
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        print(f"Status: {res.status_code}")
        if res.status_code == 200:
            items = res.json().get('items', [])
            print(f"Found {len(items)} videos")
            for item in items:
                print(f" - {item['snippet']['title']}")
        else:
            print(res.text)
    except Exception as e:
        print(f"Error: {e}")

def test_spotify():
    print("\nTesting Spotify...")
    # 1. Get Token
    auth_string = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
    auth_base64 = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")
    headers = {
        "Authorization": f"Basic {auth_base64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    try:
        res = requests.post("https://accounts.spotify.com/api/token", headers=headers, data=data, timeout=10)
        if res.status_code != 200:
            print(f"Auth failed: {res.text}")
            return
        token = res.json().get('access_token')
        print("Got token")
        
        # 2. Search
        headers = {"Authorization": f"Bearer {token}"}
        params = {"q": "Inception soundtrack", "type": "album", "limit": 1}
        search_res = requests.get("https://api.spotify.com/v1/search", headers=headers, params=params, timeout=10)
        print(f"Search Status: {search_res.status_code}")
        if search_res.status_code == 200:
            albums = search_res.json().get('albums', {}).get('items', [])
            print(f"Found {len(albums)} albums")
            if albums:
                print(f" - {albums[0]['name']}")
        else:
            print(search_res.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_youtube()
    test_spotify()
