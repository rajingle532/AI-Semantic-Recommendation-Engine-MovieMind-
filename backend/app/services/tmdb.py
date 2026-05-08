import requests
from typing import Optional
from app.config import settings

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Persistent session for connection pooling and retries
_session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
_session.mount('https://', HTTPAdapter(max_retries=retries))

# Real browser User-Agent to avoid blocks
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# In-memory caches to avoid redundant API calls
_poster_cache = {}
_details_cache = {}
_fallback_movies = []

# Force IPv4 preference for TMDB as some ISPs/regions have broken IPv6 routing to their API
try:
    import socket
    import requests.packages.urllib3.util.connection as urllib3_cn
    urllib3_cn.allowed_gai_family = lambda: socket.AF_INET
    print("TMDB_SERVICE: Forced IPv4 preference for API connectivity.")
except Exception as e:
    print(f"TMDB_SERVICE: Could not force IPv4 preference: {e}")


def _make_request(endpoint: str, params: dict = None) -> dict:
    """Make a GET request to TMDB API with automatic API key injection and retries."""
    url = f"{settings.TMDB_BASE_URL}{endpoint}"
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json"
    }
    
    if not settings.TMDB_API_KEY:
        print("TMDB_API_ERROR: TMDB_API_KEY is not set in environment variables!")
        return {}

    max_retries = 3
    for attempt in range(max_retries):
        try:
            full_params = {"api_key": settings.TMDB_API_KEY, **(params or {})}
            response = _session.get(url, params=full_params, headers=headers, timeout=10)
            
            if response.status_code != 200:
                print(f"TMDB_API_ERROR: {endpoint} returned {response.status_code}. Response: {response.text}")
                return {}
                
            return response.json()
        except (requests.RequestException, ConnectionResetError) as e:
            if attempt == max_retries - 1:
                print(f"TMDB API Error after {max_retries} attempts: {e}")
                return {}
            print(f"TMDB API attempt {attempt + 1} failed, retrying...")
            continue
    return {}


def get_movie_details(movie_id: int) -> dict:
    """Fetch full movie details from TMDB by movie ID."""
    if movie_id in _details_cache:
        return _details_cache[movie_id]

    data = _make_request(f"/movie/{movie_id}", {"append_to_response": "credits,videos"})
    if not data:
        return {}

    # Format cast data
    cast = []
    if "credits" in data:
        for member in data["credits"].get("cast", [])[:10]: # Top 10 actors
            cast.append({
                "id": member["id"],
                "name": member["name"],
                "character": member["character"],
                "profile_path": f"{settings.TMDB_IMAGE_URL}{member['profile_path']}" if member.get("profile_path") else None
            })

    details = {
        "id": data.get("id"),
        "title": data.get("title"),
        "overview": data.get("overview"),
        "poster_path": f"{settings.TMDB_IMAGE_URL}{data['poster_path']}" if data.get("poster_path") else None,
        "backdrop_path": f"https://image.tmdb.org/t/p/original{data['backdrop_path']}" if data.get("backdrop_path") else None,
        "release_date": data.get("release_date"),
        "vote_average": data.get("vote_average"),
        "vote_count": data.get("vote_count"),
        "runtime": data.get("runtime"),
        "genres": [g["name"] for g in data.get("genres", [])],
        "cast": cast,
        "tagline": data.get("tagline"),
        "trailer_key": get_movie_videos(movie_id),
        "watch_providers": get_watch_providers(movie_id)
    }
    
    print(f"DEBUG: Fetched details for movie {movie_id}. Providers: {bool(details['watch_providers'])}")
    
    _details_cache[movie_id] = details
    return details


def get_movie_videos(movie_id: int) -> Optional[str]:
    """Fetch YouTube trailer key for a movie."""
    data = _make_request(f"/movie/{movie_id}/videos")
    if not data or not data.get("results"):
        return None

    videos = data.get("results", [])
    # Prioritize official YouTube trailers
    for video in videos:
        if video.get("site") == "YouTube" and video.get("type") == "Trailer":
            return video.get("key")
    
    # Fallback to Teasers
    for video in videos:
        if video.get("site") == "YouTube" and video.get("type") == "Teaser":
            return video.get("key")
    
    # Fallback to any YouTube video (Clips, Featurettes, etc.)
    for video in videos:
        if video.get("site") == "YouTube":
            return video.get("key")
            
    return None


def get_watch_providers(movie_id: int):
    """Fetch streaming providers (Netflix, Prime, etc.) for a movie."""
    try:
        data = _make_request(f"/movie/{movie_id}/watch/providers")
        results = data.get("results", {})
        
        # Get providers for India (IN) - fallback to US if not available
        country_data = results.get("IN") or results.get("US") or {}
        
        # Format logos with full URL
        def format_logos(items):
            return [{
                "provider_id": item.get("provider_id"),
                "provider_name": item.get("provider_name"),
                "logo_path": f"{settings.TMDB_IMAGE_URL}{item['logo_path']}" if item.get("logo_path") else None
            } for item in items]

        providers = {
            "flatrate": format_logos(country_data.get("flatrate", [])), # Streaming
            "rent": format_logos(country_data.get("rent", [])),
            "buy": format_logos(country_data.get("buy", [])),
            "link": country_data.get("link", "") + f"?tag={settings.AFFILIATE_TAG}" # TMDB Link with Affiliate Tag
        }
        return providers
    except Exception as e:
        print(f"Error fetching watch providers: {e}")
        return None


def get_movie_poster(movie_id: int) -> Optional[str]:
    """Fetch only the poster URL for a movie."""
    if movie_id in _poster_cache:
        return _poster_cache[movie_id]

    data = _make_request(f"/movie/{movie_id}")
    poster = None
    if data and data.get("poster_path"):
        poster = f"{settings.TMDB_IMAGE_URL}{data['poster_path']}"
    
    _poster_cache[movie_id] = poster
    return poster


def get_trending_movies(page: int = 1) -> list:
    """Get a mix of global trending movies and popular Hindi (Bollywood) movies."""
    # 1. Fetch Global Trending (Hollywood/International)
    global_data = _make_request("/trending/movie/week", {"page": page})
    global_results = global_data.get("results", [])

    # 2. Fetch Popular Hindi Movies (Bollywood)
    hindi_data = _make_request("/discover/movie", {
        "page": page,
        "sort_by": "popularity.desc",
        "with_original_language": "hi",
        "region": "IN",
        "with_origin_country": "IN"
    })
    hindi_results = hindi_data.get("results", [])

    # Format helper
    def format_movie(m):
        return {
            "id": m.get("id"),
            "title": m.get("title"),
            "overview": m.get("overview", "")[:150],
            "poster_path": f"{settings.TMDB_IMAGE_URL}{m['poster_path']}" if m.get("poster_path") else None,
            "vote_average": m.get("vote_average"),
            "release_date": m.get("release_date"),
        }

    # Interleave results with random start (sometimes Bollywood first, sometimes Hollywood)
    import random
    start_with_hindi = random.choice([True, False])
    
    mixed_results = []
    max_len = max(len(global_results), len(hindi_results))
    
    for i in range(max_len):
        if start_with_hindi:
            if i < len(hindi_results):
                mixed_results.append(format_movie(hindi_results[i]))
            if i < len(global_results):
                mixed_results.append(format_movie(global_results[i]))
        else:
            if i < len(global_results):
                mixed_results.append(format_movie(global_results[i]))
            if i < len(hindi_results):
                mixed_results.append(format_movie(hindi_results[i]))

    # If both fail, use local fallback data
    if not mixed_results:
        print("TMDB_API_ERROR: All TMDB requests failed. Using local fallback dataset.")
        return _get_fallback_movies()

    # Return top 20 mixed results
    return mixed_results[:20]


def _get_fallback_movies() -> list:
    """Fetch movies from the local CSV dataset as a fallback when API is down."""
    global _fallback_movies
    if _fallback_movies:
        return _fallback_movies

    try:
        import pandas as pd
        import os
        
        # Paths to local data
        data_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
        movies_path = os.path.join(data_dir, 'tmdb_5000_movies.csv')
        
        if not os.path.exists(movies_path):
            return []
            
        df = pd.read_csv(movies_path)
        # Sort by popularity or just take top 20
        top_movies = df.sort_values('popularity', ascending=False).head(20)
        
        fallback = []
        for _, row in top_movies.iterrows():
            fallback.append({
                "id": int(row['id']),
                "title": row['title'],
                "overview": row['overview'][:150] if isinstance(row['overview'], str) else "",
                "poster_path": None, # CSV doesn't have posters, but UI will handle it
                "vote_average": row['vote_average'],
                "release_date": row['release_date'],
            })
        
        _fallback_movies = fallback
        return fallback
    except Exception as e:
        print(f"FALLBACK ERROR: {e}")
        return []




def get_genres() -> list:
    """Get list of all movie genres from TMDB."""
    data = _make_request("/genre/movie/list")
    return data.get("genres", [])


def get_person_details(person_id: int) -> dict:
    """Fetch person biography and details from TMDB."""
    return _make_request(f"/person/{person_id}")

def get_person_movie_credits(person_id: int) -> list:
    """Fetch all movies a person has worked on."""
    data = _make_request(f"/person/{person_id}/movie_credits")
    if not data:
        return []
    
    # Combine cast and crew credits
    cast = data.get("cast", [])
    crew = data.get("crew", [])
    combined = cast + crew
    
    # Sort by popularity and remove duplicates
    seen = set()
    unique_movies = []
    for m in sorted(combined, key=lambda x: x.get("popularity", 0), reverse=True):
        if m["id"] not in seen:
            seen.add(m["id"])
            unique_movies.append({
                "id": m["id"],
                "title": m.get("title") or m.get("name"),
                "poster_path": f"{settings.TMDB_IMAGE_URL}{m['poster_path']}" if m.get("poster_path") else None,
                "character": m.get("character", ""),
                "job": m.get("job", ""),
                "release_date": m.get("release_date", ""),
                "vote_average": m.get("vote_average", 0)
            })
    
    return unique_movies[:40] # Return top 40 movies


def search_movies_tmdb(query: str, page: int = 1) -> list:
    """Search movies on TMDB by title query."""
    data = _make_request("/search/movie", {"query": query, "page": page})
    results = data.get("results", [])

    return [
        {
            "id": m.get("id"),
            "title": m.get("title"),
            "overview": m.get("overview", "")[:150],
            "poster_path": f"{settings.TMDB_IMAGE_URL}{m['poster_path']}" if m.get("poster_path") else None,
            "vote_average": m.get("vote_average"),
            "release_date": m.get("release_date"),
        }
        for m in results[:20]
    ]


def get_movies_by_language(language_code: str, page: int = 1) -> list[dict]:
    data = _make_request("/discover/movie", {
        "with_original_language": language_code,
        "sort_by": "popularity.desc",
        "page": page
    })
    results = data.get("results", [])

    return [
        {
            "id": m.get("id"),
            "title": m.get("title"),
            "overview": m.get("overview", "")[:150],
            "poster_path": f"{settings.TMDB_IMAGE_URL}{m['poster_path']}" if m.get("poster_path") else None,
            "vote_average": m.get("vote_average"),
            "release_date": m.get("release_date"),
        }
        for m in results[:20]
    ]


def get_all_languages_movies(page: int = 1, language: str = None, year: str = None, min_rating: float = None) -> list[dict]:
    """Discover movies with strict advanced combined filters and regional targeting."""
    params = {
        "api_key": settings.TMDB_API_KEY,
        "sort_by": "popularity.desc",
        "page": page,
        "vote_count.gte": 2, # Lowered even more for fresh regional content
        "include_adult": "false"
    }
    
    # Map of Indian languages to force IN region
    indian_langs = ['hi', 'mr', 'ta', 'te', 'kn', 'ml', 'bn', 'gu', 'pa']
    
    if language and language != 'all' and language != 'null':
        params["with_original_language"] = language
        # If it's an Indian language, force India as origin country to filter out international mis-matches
        if language in indian_langs:
            params["with_origin_country"] = "IN"
            params["region"] = "IN"
    else:
        params["language"] = "en-US"
    
    if year and year != '' and year != 'null':
        params["primary_release_year"] = year
        
    if min_rating and float(min_rating) > 0:
        params["vote_average.gte"] = float(min_rating)

    print(f"DEBUG: Strict Discover with params: {params}")
    
    try:
        headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
        response = _session.get(f"{settings.TMDB_BASE_URL}/discover/movie", params=params, headers=headers, timeout=10)
        data = response.json()
        results = data.get("results", [])
        print(f"DEBUG: TMDB returned {len(results)} movies for this filter.")
    except Exception as e:
        print(f"DISCOVER ERROR: {e}")
        return []

    return [
        {
            "id": m.get("id"),
            "title": m.get("title"),
            "overview": m.get("overview", "")[:150],
            "poster_path": f"{settings.TMDB_IMAGE_URL}{m['poster_path']}" if m.get("poster_path") else None,
            "vote_average": m.get("vote_average"),
            "release_date": m.get("release_date"),
        }
        for m in results
    ]


def get_movies_by_genre(genre_id: int, page: int = 1) -> list[dict]:
    """Fetch movies for a specific genre ID from TMDB."""
    data = _make_request("/discover/movie", {
        "with_genres": genre_id,
        "sort_by": "popularity.desc",
        "page": page
    })
    results = data.get("results", [])

    return [
        {
            "id": m.get("id"),
            "title": m.get("title"),
            "overview": m.get("overview", "")[:150],
            "poster_path": f"{settings.TMDB_IMAGE_URL}{m['poster_path']}" if m.get("poster_path") else None,
            "vote_average": m.get("vote_average"),
            "release_date": m.get("release_date"),
        }
        for m in results[:20]
    ]


def get_similar_movies(movie_id: int) -> list:
    """Fetch similar movies from TMDB for a given movie ID."""
    data = _make_request(f"/movie/{movie_id}/recommendations")
    if not data or not data.get("results"):
        return []

    return [
        {
            "id": m["id"],
            "movie_id": m["id"],
            "title": m["title"],
            "poster_path": f"{settings.TMDB_IMAGE_URL}{m['poster_path']}" if m.get("poster_path") else None,
            "vote_average": m.get("vote_average"),
            "release_date": m.get("release_date"),
            "similarity_score": 0.8  # Default score for TMDB recommendations
        }
        for m in data["results"][:15]
    ]
