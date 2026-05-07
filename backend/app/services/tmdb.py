import requests
from typing import Optional
from app.config import settings

# Persistent session for connection pooling
_session = requests.Session()

# In-memory caches to avoid redundant API calls
_poster_cache = {}
_details_cache = {}


def _make_request(endpoint: str, params: dict = None) -> dict:
    """Make a GET request to TMDB API with automatic API key injection and retries."""
    url = f"{settings.TMDB_BASE_URL}{endpoint}"
    default_params = {
        "api_key": settings.TMDB_API_KEY,
        "language": "en-US"
    }
    if params:
        default_params.update(params)

    max_retries = 3
    if not settings.TMDB_API_KEY:
        print("TMDB_API_ERROR: TMDB_API_KEY is not set in environment variables!")
        return {}

    for attempt in range(max_retries):
        try:
            full_params = {"api_key": settings.TMDB_API_KEY, **(params or {})}
            response = requests.get(f"{settings.TMDB_BASE_URL}{endpoint}", params=full_params, timeout=10)
            
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

    data = _make_request(f"/movie/{movie_id}", {"append_to_response": "credits"})
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

    # Filter for official YouTube trailers
    videos = data.get("results", [])
    for video in videos:
        if video.get("site") == "YouTube" and video.get("type") == "Trailer":
            return video.get("key")
    
    # Fallback to any YouTube video if no official trailer
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
    """Get trending movies for the week."""
    data = _make_request("/trending/movie/week", {"page": page})
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


def get_all_languages_movies(page: int = 1) -> list[dict]:
    data = _make_request("/discover/movie", {
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
