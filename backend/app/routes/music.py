from fastapi import APIRouter, HTTPException
from typing import List, Dict
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import base64
from app.config import settings

# Configure a robust requests session with retries for unstable networks
session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[ 500, 502, 503, 504 ])
session.mount('http://', HTTPAdapter(max_retries=retries))
session.mount('https://', HTTPAdapter(max_retries=retries))

router = APIRouter(prefix="/api/music", tags=["Music"])

YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/search"
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE = "https://api.spotify.com/v1"

ITUNES_API_URL = "https://itunes.apple.com/search"
ITUNES_LOOKUP_URL = "https://itunes.apple.com/lookup"

@router.get("/spotify/album")
async def get_movie_soundtrack(title: str):
    """Search for a movie soundtrack on iTunes (replaces Spotify due to Premium restrictions)."""
    movie_title = title
    
    queries = [
        f"{movie_title} original motion picture soundtrack",
        f"{movie_title} soundtrack",
        f"{movie_title} ost"
    ]
    
    for q in queries:
        try:
            params = {"term": q, "entity": "album", "limit": 1}
            search_res = session.get(ITUNES_API_URL, params=params, timeout=15)
            if search_res.status_code == 200:
                data = search_res.json()
                if data.get("resultCount", 0) > 0:
                    album = data["results"][0]
                    collection_id = album["collectionId"]
                    
                    # Fetch tracks
                    lookup_params = {"id": collection_id, "entity": "song"}
                    tracks_res = session.get(ITUNES_LOOKUP_URL, params=lookup_params, timeout=15)
                    if tracks_res.status_code == 200:
                        tracks_data = tracks_res.json()
                        tracks = [item for item in tracks_data.get("results", []) if item.get("wrapperType") == "track"]
                        
                        return {
                            "album_name": album.get("collectionName"),
                            "album_image": album.get("artworkUrl100", "").replace("100x100bb", "600x600bb"), # Get high-res
                            "spotify_url": album.get("collectionViewUrl"), # Link to Apple Music
                            "tracks": [{
                                "id": str(t.get("trackId")),
                                "name": t.get("trackName"),
                                "preview_url": t.get("previewUrl"),
                                "duration_ms": t.get("trackTimeMillis", 0)
                            } for t in tracks]
                        }
        except Exception as e:
            print(f"iTunes Query Error for '{q}': {e}")
            
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
        f"{base_query} official soundtrack lyric video",
        f"{base_query} main theme audio only",
        f"{base_query} music video lyrics"
    ]
    
    for q in queries:
        try:
            params = {
                "part": "snippet",
                "q": q,
                "type": "video",
                "videoEmbeddable": "true",
                "videoSyndicated": "true",
                "maxResults": 3,
                "key": settings.YOUTUBE_API_KEY
            }
            response = session.get(YOUTUBE_API_URL, params=params, timeout=15)
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
