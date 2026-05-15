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

@router.get("/spotify/album")
async def get_movie_soundtrack(title: str):
    """Search for a movie soundtrack on Spotify with multiple fallbacks."""
    movie_title = title
    """Search for a movie soundtrack on Spotify with multiple fallbacks."""
    token = get_spotify_token()
    if not token:
        print("SPOTIFY_ERROR: No token available")
        return {"results": None}

    headers = {"Authorization": f"Bearer {token}"}
    queries = [
        f"{movie_title} soundtrack",
        f"{movie_title} original motion picture soundtrack",
        f"{movie_title} OST",
        movie_title # Extreme fallback
    ]
    
    for q in queries:
        try:
            params = {"q": q, "type": "album", "limit": 1}
            search_res = requests.get(f"{SPOTIFY_API_BASE}/search", headers=headers, params=params, timeout=15)
            if search_res.status_code == 200:
                data = search_res.json()
                albums = data.get("albums", {}).get("items", [])
                if albums:
                    album_id = albums[0]["id"]
                    tracks_res = requests.get(f"{SPOTIFY_API_BASE}/albums/{album_id}/tracks", headers=headers, timeout=15)
                    if tracks_res.status_code == 200:
                        tracks_data = tracks_res.json()
                        return {
                            "album_name": albums[0]["name"],
                            "album_image": albums[0]["images"][0]["url"] if albums[0]["images"] else None,
                            "tracks": [{
                                "id": t["id"],
                                "name": t["name"],
                                "preview_url": t.get("preview_url"),
                                "duration_ms": t["duration_ms"]
                            } for t in tracks_data.get("items", [])]
                        }
        except Exception as e:
            print(f"Spotify Query Error for '{q}': {e}")
            
    return {"results": None}

@router.get("/youtube")
async def search_youtube_videos(q: str) -> Dict[str, List[Dict[str, str]]]:
    """Search YouTube with aggressive fallbacks."""
    query = q
    """Search YouTube with aggressive fallbacks."""
    if not settings.YOUTUBE_API_KEY:
        print("YOUTUBE_ERROR: Missing API Key")
        return {"results": []}

    base_query = query.replace("official song", "").replace("movie", "").strip()
    queries = [
        f"{base_query} official audio",
        f"{base_query} theme song",
        f"{base_query} soundtrack",
        f"{base_query} music video"
    ]
    
    for q in queries:
        try:
            params = {
                "part": "snippet",
                "q": q,
                "type": "video",
                "videoEmbeddable": "true",
                "maxResults": 5,
                "key": settings.YOUTUBE_API_KEY
            }
            response = requests.get(YOUTUBE_API_URL, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                if items:
                    return {"results": [{
                        "id": item["id"]["videoId"],
                        "title": item["snippet"]["title"],
                        "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"]
                    } for item in items]}
            elif response.status_code == 403:
                print(f"YouTube API Error 403: Quota exceeded or invalid key.")
                break # Don't keep trying if key is bad
        except Exception as e:
            print(f"YouTube Error for '{q}': {e}")
            
    return {"results": []}
