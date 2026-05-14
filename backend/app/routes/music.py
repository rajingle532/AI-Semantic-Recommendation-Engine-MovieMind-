from fastapi import APIRouter, HTTPException
from typing import List, Dict
import requests
import base64
from app.config import settings

router = APIRouter(prefix="/api/music", tags=["Music"])

YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/search"
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE = "https://api.spotify.com/v1"

def get_spotify_token():
    """Get Spotify access token using Client Credentials flow."""
    if not settings.SPOTIFY_CLIENT_ID or not settings.SPOTIFY_CLIENT_SECRET:
        return None
    
    auth_string = f"{settings.SPOTIFY_CLIENT_ID}:{settings.SPOTIFY_CLIENT_SECRET}"
    auth_base64 = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")
    
    headers = {
        "Authorization": f"Basic {auth_base64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    
    try:
        response = requests.post(SPOTIFY_AUTH_URL, headers=headers, data=data, timeout=5)
        if response.status_code == 200:
            return response.json().get("access_token")
    except Exception as e:
        print(f"Spotify Auth Error: {e}")
    return None

@router.get("/spotify/album/{movie_title}")
async def get_movie_soundtrack(movie_title: str):
    """Search for a movie soundtrack on Spotify."""
    token = get_spotify_token()
    if not token:
        return {"results": None}

    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # 1. Try "{movie_title} soundtrack"
        params = {"q": f"{movie_title} soundtrack", "type": "album", "limit": 1}
        search_res = requests.get(f"{SPOTIFY_API_BASE}/search", headers=headers, params=params, timeout=5)
        data = search_res.json()
        albums = data.get("albums", {}).get("items", [])
        
        # 2. Try "{movie_title} original motion picture soundtrack"
        if not albums:
            params["q"] = f"{movie_title} original motion picture soundtrack"
            search_res = requests.get(f"{SPOTIFY_API_BASE}/search", headers=headers, params=params, timeout=5)
            data = search_res.json()
            albums = data.get("albums", {}).get("items", [])

        # 3. Last resort: Just "{movie_title}" as album
        if not albums:
            params["q"] = movie_title
            search_res = requests.get(f"{SPOTIFY_API_BASE}/search", headers=headers, params=params, timeout=5)
            data = search_res.json()
            albums = data.get("albums", {}).get("items", [])

        if not albums:
            return {"results": None}

            album = albums[0]
            tracks_res = requests.get(f"{SPOTIFY_API_BASE}/albums/{album['id']}/tracks", headers=headers, timeout=5)
            tracks_data = tracks_res.json()
            
            tracks = []
            for t in tracks_data.get("items", []):
                if t.get("preview_url"):
                    tracks.append({
                        "id": t["id"],
                        "name": t["name"],
                        "preview_url": t["preview_url"],
                        "duration_ms": t["duration_ms"],
                        "track_number": t["track_number"]
                    })
            
            return {
                "album_name": album["name"],
                "album_image": album["images"][0]["url"] if album["images"] else None,
                "spotify_url": album["external_urls"]["spotify"],
                "tracks": tracks[:10]
            }
    except Exception as e:
        print(f"Spotify API Error: {e}")
    return {"results": None}

@router.get("/youtube/{query}")
async def search_youtube_videos(query: str) -> Dict[str, List[Dict[str, str]]]:
    """Search YouTube for music videos."""
    if not settings.YOUTUBE_API_KEY:
        return {"results": []}

    try:
        # Broader query for better results on common titles
        search_query = f"{query} movie song"
        params = {
            "part": "snippet",
            "q": search_query,
            "type": "video",
            "maxResults": 3,
            "key": settings.YOUTUBE_API_KEY
        }
        response = requests.get(YOUTUBE_API_URL, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            results = [{
                "id": item["id"]["videoId"],
                "title": item["snippet"]["title"],
                "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"]
            } for item in data.get("items", [])]
            return {"results": results}
    except Exception as e:
        print(f"YouTube Error: {e}")
    return {"results": []}
