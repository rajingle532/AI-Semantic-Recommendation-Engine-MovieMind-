import requests
import json
import os
import time
from typing import Optional
from app.config import settings

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Persistent session for connection pooling and retries
_session = requests.Session()
# Reduced retries and backoff for faster failure and better UX
retries = Retry(total=2, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
_session.mount('https://', HTTPAdapter(max_retries=retries))

# Real browser User-Agent to avoid blocks
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# In-memory caches to avoid redundant API calls
_poster_cache = {}
_details_cache = {}
_genres_cache = None
_trending_cache = {} # Key: page, Value: (timestamp, data)
_CACHE_TTL = 3600 # 1 hour cache for trending/genres (reduced for daily variety)
_fallback_movies = []

# Persistent Cache Directory
CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'cache')
if not os.path.exists(CACHE_DIR):
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
    except:
        pass

# Emergency Hardcoded Fallback (Last resort if everything else fails)
EMERGENCY_MOVIES = [
    {"id": 27205, "title": "Inception", "overview": "Cobb, a skilled thief who commits corporate espionage by infiltrating the subconscious of his targets is offered a chance to regain his old life.", "poster_path": "https://image.tmdb.org/t/p/w500/edv5CZv0jH9NX186hBnoivcopyO.jpg", "vote_average": 8.4, "release_date": "2010-07-15", "backdrop_path": "https://image.tmdb.org/t/p/original/8Z99vYmda69uQk6u9u5Y7976q9U.jpg"},
    {"id": 157336, "title": "Interstellar", "overview": "The adventures of a group of explorers who make use of a newly discovered wormhole to surpass the limitations on human space travel.", "poster_path": "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6vCU67oYvBPXT.jpg", "vote_average": 8.4, "release_date": "2014-11-05", "backdrop_path": "https://image.tmdb.org/t/p/original/xJHbtvMTEvR68SnedpCid97m8pS.jpg"},
    {"id": 671, "title": "Harry Potter and the Philosopher's Stone", "overview": "Harry Potter has lived under the stairs at his aunt and uncle's house his whole life. But on his 11th birthday, he learns he's a powerful wizard.", "poster_path": "https://image.tmdb.org/t/p/w500/wuMc08IPKEatv9rn9XvBfCUyWHp.jpg", "vote_average": 7.9, "release_date": "2001-11-16", "backdrop_path": "https://image.tmdb.org/t/p/original/hziiv1YVatUcYqllIoxvBr7oQC9.jpg"}
]

# Image paths for the most common local CSV fallback movies.
# These keep the UI rich even when TMDB API requests are temporarily unavailable.
FALLBACK_IMAGE_OVERRIDES = {
    211672: {"poster": "/dr02BdCNAUPVU07aOodwPYv6HCf.jpg", "backdrop": "/wKrxeY6lbu7KFBsWVcMH6M8avwr.jpg"},
    157336: {"poster": "/yQvGrMoipbRoddT0ZR8tPoR7NfX.jpg", "backdrop": "/2ssWTSVklAEc98frZUQhgtGHx7s.jpg"},
    293660: {"poster": "/3E53WEZJqP6aM84D8CckXx4pIHw.jpg", "backdrop": "/en971MEXui9diirXlogOrPKmsEn.jpg"},
    118340: {"poster": "/r7vmZjiyZw9rpJMQJdXpjgiCOk9.jpg", "backdrop": "/uLtVbjvS1O7gXL8lUOwsFOH4man.jpg"},
    76341: {"poster": "/hA2ple9q4qnwxp3hKVNhroipsir.jpg", "backdrop": "/uT895WNwm0aIJRtGizcQhrejWUo.jpg"},
    135397: {"poster": "/rhr4y79GpxQF9IsfJItRXVaoGs4.jpg", "backdrop": "/s5QfDFqRO6sjgPtKkjxD0WqXQef.jpg"},
    22: {"poster": "/kvDwL2gTf6yxujbsWbsGQB3Z9Wa.jpg", "backdrop": "/zXMGAtDqJ58P8G3W4bwKyYffPhn.jpg"},
    119450: {"poster": "/mSmAc9G25fhOHH45SLEeagR0qi7.jpg", "backdrop": "/3SozaNPOYUadcmTPgndDibMyDNC.jpg"},
    131631: {"poster": "/4FAA18ZIja70d1Tu5hr5cj2q1sB.jpg", "backdrop": "/lV1P1Q5gLDXVG1ZYCxZHStkcQC3.jpg"},
    177572: {"poster": "/2mxS4wUimwlLmI1xp6QW6NSU361.jpg", "backdrop": "/4s2d3xdyqotiVNHTlTlJjrr3q0H.jpg"},
    87101: {"poster": "/oZRVDpNtmHk8M1VYy1aeOWUXgbC.jpg", "backdrop": "/g4a5YLWwi6OCp8TcvxsUNrXMbN5.jpg"},
    271110: {"poster": "/rAGiXaUfPzY7CDEyNKUofk3Kw2e.jpg", "backdrop": "/7FWlcZq3r6525LWOcvO9kNWurN1.jpg"},
    244786: {"poster": "/7fn624j5lj3xTme2SgiLCeuedmO.jpg", "backdrop": "/wbQa0EnWUyRzQ5d1pHLNRlmsCUP.jpg"},
    155: {"poster": "/qJ2tW6WMUDux911r6m7haRef0WH.jpg", "backdrop": "/cfT29Im5VDvjE0RpyKOSdCKZal7.jpg"},
    286217: {"poster": "/3ndAx3weG6KDkJIRMCi5vXX6Dyb.jpg", "backdrop": "/lzMS0CI3FLQYC5EgJoWeIaEt0lm.jpg"},
    27205: {"poster": "/xlaY2zyzMfkhk0HSC5VUwzoZPU1.jpg", "backdrop": "/8ZTVqvKDQ8emSGUEMjsS4yHAwrp.jpg"},
    109445: {"poster": "/kgwjIb2JDHRhNk13lmSxiClFjVk.jpg", "backdrop": "/rj58WQ9ImI0mYDptXdM7euX1Wjt.jpg"},
    209112: {"poster": "/5UsK3grJvtQrtzEgqNlDljJW96w.jpg", "backdrop": "/5fX1oSGuYdKgwWmUTAN5MNSQGzr.jpg"},
    19995: {"poster": "/gKY6q7SjCkAU6FqvqWybDYgUKIF.jpg", "backdrop": "/vL5LR6WdxWPjLPFRLe133jXWsh5.jpg"},
    550: {"poster": "/jSziioSwPVrOy9Yow3XhWIBDjq1.jpg", "backdrop": "/xRyINp9KfMLVjRiO5nCsoRDdvvF.jpg"},
    58: {"poster": "/uXEqmloGyP7UXAiphJUu2v2pcuE.jpg", "backdrop": "/vr6n6ZFUZvedvIlhfYcbCWcaKyW.jpg"},
    205596: {"poster": "/zSqJ1qFq8NXFfi7JeIYMlzyR0dx.jpg", "backdrop": "/4vf5Fv6OVXXrNqEXqiJnWxnNSyV.jpg"},
    24428: {"poster": "/RYMX2wcKCBAr24UyPD7xwmjaTn.jpg", "backdrop": "/9BBTo63ANSmhC4e6r62OJFuK2GL.jpg"},
    238: {"poster": "/3bhkrj58Vtu7enYsRolD1fZdja1.jpg", "backdrop": "/tSPT36ZKlP2WVHJLM4cQPLSzv3b.jpg"},
    98566: {"poster": "/azL2ThbJMIkts3ZMt3j1YgBUeDB.jpg", "backdrop": "/eezsbzYPbYKjjh6E1XHDBNlLynh.jpg"},
    210577: {"poster": "/ts996lKsxvjkO2yiYG0ht4qAicO.jpg", "backdrop": "/iWak7wT0j6ycCc8lKr4NBz9c7n5.jpg"},
    257344: {"poster": "/d26S5EfVXLNxRXqyFy1yyl3qRq3.jpg", "backdrop": "/41Y3h2FVfoU4baFdTZwRrlD4MDM.jpg"},
    228150: {"poster": "/pfte7wdMobMF4CVHuOxyu6oqeeA.jpg", "backdrop": "/95ckrV6wQgbffurAVmETQ5YKASL.jpg"},
    246655: {"poster": "/2mtQwJKVKQrZgTz49Dizb25eOQQ.jpg", "backdrop": "/sTQNRqLbfCXolrb5CizAW1dj528.jpg"},
    285: {"poster": "/jGWpG4YhpQwVmjyHEGkxEkeRf0S.jpg", "backdrop": "/1jHxkVXMI5s3vRiyiZooUy1shB5.jpg"},
    61791: {"poster": "/oqA45qMyyo1TtrnVEBKxqmTPhbN.jpg", "backdrop": "/6cCF0KMUO2QmrVsQFujkQduREXX.jpg"},
    13: {"poster": "/Cw4hIUIAmSYfK9QfaUW5igp9La.jpg", "backdrop": "/66Kn4XWhkuPkJxOJyPEx4U2CUfN.jpg"},
    120: {"poster": "/6oom5QYQ2yQTMJIbnvbkBL9cHo6.jpg", "backdrop": "/a0lfia8tk8ifkrve0Tn8wkISUvs.jpg"},
    93456: {"poster": "/5Fh4NdoEnCjCK9wLjdJ9DJNFl2b.jpg", "backdrop": "/uD267eSiACfWLxp47t3gYymOQRj.jpg"},
    278: {"poster": "/9cqNxx0GxF0bflZmeSMuL5tnGzr.jpg", "backdrop": "/zfbjgQE1uSd9wiPTX4VzsLi0rGG.jpg"},
    1865: {"poster": "/keGfSvCmYj7CvdRx36OdVrAEibE.jpg", "backdrop": "/v1dh11Yox9uMRNtE5lTe9WkXJeR.jpg"},
    99861: {"poster": "/4ssDuvEDkSArWEdyBl2X5EHvYKU.jpg", "backdrop": "/kIBK5SKwgqIIuRKhhWrJn3XkbPq.jpg"},
    672: {"poster": "/sdEOH0992YZ0QSxgXNIGLq1ToUi.jpg", "backdrop": "/1stUIsjawROZxjiCMtqqXqgfZWC.jpg"},
    198663: {"poster": "/ode14q7WtDugFDp78fo9lCsmay9.jpg", "backdrop": "/eTlcNXGv32zkVI7ZDHhfeaKHXKQ.jpg"},
    158852: {"poster": "/kziYpr5Nfw60P0My8aj1sgCEqed.jpg", "backdrop": "/udYOmbW1JEZjVd726PWHlmptxPi.jpg"},
}

# Circuit breaker for TMDB API
_tmdb_disabled = False
_tmdb_failures = 0


# Force IPv4 preference for TMDB as some ISPs/regions have broken IPv6 routing to their API
try:
    import socket
    import requests.packages.urllib3.util.connection as urllib3_cn
    urllib3_cn.allowed_gai_family = lambda: socket.AF_INET
    print("TMDB_SERVICE: Forced IPv4 preference for API connectivity.")
except Exception as e:
    print(f"TMDB_SERVICE: Could not force IPv4 preference: {e}")


def _get_fallback_data():
    """Load the fallback CSV into a lightweight list of dicts once."""
    global _fallback_movies
    if _fallback_movies is not None:
        return _fallback_movies
        
    try:
        import csv
        import os
        data_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
        # Check for smaller, faster unified dataset first
        movies_path = os.path.join(data_dir, 'tmdb_indian_movies.csv')
        if not os.path.exists(movies_path):
            movies_path = os.path.join(data_dir, 'tmdb_5000_movies.csv')
        
        if not os.path.exists(movies_path):
            return []
            
        movies = []
        with open(movies_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    movies.append({
                        "id": int(row['id']),
                        "title": row.get('title') or row.get('original_title', 'Untitled'),
                        "overview": row.get('overview', ""),
                        "vote_average": float(row['vote_average']) if row.get('vote_average') else 0,
                        "popularity": float(row['popularity']) if row.get('popularity') else 0,
                        "release_date": row.get('release_date', ""),
                        "genres": row.get('genres', "[]"),
                        "original_language": row.get('original_language', 'en')
                    })
                except: continue
        
        # Sort by popularity once so fallbacks are always high quality
        _fallback_movies = sorted(movies, key=lambda x: x['popularity'], reverse=True)
        return _fallback_movies
    except Exception as e:
        print(f"ERROR loading fallback dataset: {e}")
        return []


def _fallback_image_urls(movie_id: int) -> dict:
    """Return full poster/backdrop URLs for curated local fallback movies."""
    image_paths = FALLBACK_IMAGE_OVERRIDES.get(int(movie_id)) if movie_id else None
    if not image_paths:
        return {"poster_path": None, "backdrop_path": None}

    return {
        "poster_path": f"{settings.TMDB_IMAGE_URL}{image_paths['poster']}" if image_paths.get("poster") else None,
        "backdrop_path": (
            f"https://image.tmdb.org/t/p/original{image_paths['backdrop']}"
            if image_paths.get("backdrop")
            else None
        ),
    }


def _format_local_movie(movie: dict, overview_limit: int = 150) -> dict:
    """Format a local CSV movie using curated images when available."""
    movie_id = int(movie["id"])
    image_urls = _fallback_image_urls(movie_id)
    overview = movie.get("overview") or ""

    return {
        "id": movie_id,
        "title": movie.get("title") or movie.get("original_title") or "Untitled",
        "overview": overview[:overview_limit],
        "poster_path": image_urls["poster_path"],
        "backdrop_path": image_urls["backdrop_path"],
        "vote_average": movie.get("vote_average", 0),
        "release_date": movie.get("release_date", ""),
    }

# Trigger background load on import
import threading
threading.Thread(target=_get_fallback_data, daemon=True).start()


def _make_request(endpoint: str, params: dict = None) -> dict:
    """Make a GET request to TMDB API with automatic API key injection, Sophos block detection, and circuit breaker."""
    global _tmdb_disabled, _tmdb_failures
    if _tmdb_disabled:
        return {}

    url = f"{settings.TMDB_BASE_URL}{endpoint}"
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json"
    }
    
    if not settings.TMDB_API_KEY:
        print("TMDB_API_ERROR: TMDB_API_KEY is not set in environment variables!")
        _tmdb_disabled = True
        return {}

    max_retries = 2
    for attempt in range(max_retries):
        try:
            full_params = {"api_key": settings.TMDB_API_KEY, **(params or {})}
            # Reduced timeout to 3.5 seconds for faster perceived performance
            # Try with verification first, fallback to verify=False if it fails due to SSL in local environments
            try:
                response = _session.get(url, params=full_params, headers=headers, timeout=3.5)
            except (requests.exceptions.SSLError, requests.exceptions.ConnectionError):
                # Fallback for environments with SSL interception or issues
                print(f"TMDB_SSL_FALLBACK: Attempting insecure request for {endpoint}")
                response = _session.get(url, params=full_params, headers=headers, timeout=5, verify=False)
            
            # Check for Sophos block page or local firewall intercept page
            if response.status_code == 403 or (response.text and any(x in response.text.lower() for x in ["sophos", "blocked site", "restricted access", "category: entertainment"])):
                print("=========================================================================")
                print("!!! CRITICAL WARNING: TMDB API is BLOCKED by Sophos Firewall/Antivirus! !!!")
                print("Reason: Network category restrictions (Entertainment).")
                print("Tripping circuit breaker: Bypassing TMDB API completely and using local dataset.")
                print("=========================================================================")
                _tmdb_disabled = True
                return {}

            if response.status_code == 429:
                print(f"TMDB_API_RATE_LIMIT: {endpoint}")
                return {}

            if response.status_code != 200:
                print(f"TMDB_API_ERROR: {endpoint} returned {response.status_code}. Response: {response.text[:200]}...")
                _tmdb_failures += 1
                if _tmdb_failures >= 3:
                    print("!!! TMDB_CIRCUIT_BREAKER: 3 consecutive failures. Disabling TMDB API requests for this session. !!!")
                    _tmdb_disabled = True
                return {}
                
            # Success! Reset failure counter
            _tmdb_failures = 0
            return response.json()
        except Exception as e:
            _tmdb_failures += 1
            if _tmdb_failures >= 3:
                print("!!! TMDB_CIRCUIT_BREAKER: 3 consecutive failures. Disabling TMDB API requests for this session. !!!")
                _tmdb_disabled = True
                return {}
            if attempt == max_retries - 1:
                print(f"TMDB API Error after {max_retries} attempts for {endpoint}: {e}")
                return {}
            print(f"TMDB API attempt {attempt + 1} failed for {endpoint}, retrying...")
            continue
    return {}


def _save_disk_cache(filename: str, data: any):
    try:
        path = os.path.join(CACHE_DIR, filename)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({"timestamp": time.time(), "data": data}, f)
    except Exception as e:
        print(f"CACHE_SAVE_ERROR: {e}")

def _load_disk_cache(filename: str):
    """Load data from a JSON file on disk."""
    try:
        path = os.path.join(CACHE_DIR, filename)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                content = json.load(f)
                return content.get("timestamp"), content.get("data")
    except Exception as e:
        print(f"CACHE_LOAD_ERROR: {e}")
    return None, None


def get_movie_details(movie_id: int) -> dict:
    """Fetch full movie details from TMDB by movie ID."""
    if movie_id in _details_cache:
        return _details_cache[movie_id]

    data = _make_request(f"/movie/{movie_id}", {"append_to_response": "credits,videos,watch/providers"})
    if not data:
        # Fallback to local CSV if TMDB fails
        try:
            movies = _get_fallback_data()
            target = next((m for m in movies if m['id'] == movie_id), None)
            if target:
                local_movie = _format_local_movie(target, overview_limit=1000)
                fallback_data = {
                    "id": target['id'],
                    "title": target['title'],
                    "overview": target['overview'],
                    "poster_path": local_movie["poster_path"],
                    "backdrop_path": local_movie["backdrop_path"],
                    "release_date": target['release_date'],
                    "vote_average": target['vote_average'],
                    "vote_count": 0,
                    "runtime": 120,
                    "budget": 0,
                    "revenue": 0,
                    "status": "Released",
                    "genres": ["Movie"],
                    "cast": [],
                    "tagline": "",
                    "trailer_key": None,
                    "watch_providers": {"IN": {}}
                }
                _details_cache[movie_id] = fallback_data
                return fallback_data
        except Exception as e:
            print(f"DETAILS FALLBACK ERROR: {e}")
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

    # Extract trailer key from appended videos
    trailer_key = None
    videos = data.get("videos", {}).get("results", [])
    for video in videos:
        if video.get("site") == "YouTube" and video.get("type") == "Trailer":
            trailer_key = video.get("key")
            break
    if not trailer_key and videos:
        # Fallback to any YouTube video
        for video in videos:
            if video.get("site") == "YouTube":
                trailer_key = video.get("key")
                break

    # Extract watch providers from appended data
    raw_providers = data.get("watch/providers", {}).get("results", {})
    country_data = raw_providers.get("IN") or raw_providers.get("US") or {}
    
    def format_logos(items):
        return [{
            "provider_id": item.get("provider_id"),
            "provider_name": item.get("provider_name"),
            "logo_path": f"{settings.TMDB_IMAGE_URL}{item['logo_path']}" if item.get("logo_path") else None
        } for item in items]

    watch_providers = {
        "flatrate": format_logos(country_data.get("flatrate", [])),
        "rent": format_logos(country_data.get("rent", [])),
        "buy": format_logos(country_data.get("buy", [])),
        "link": country_data.get("link", "") + f"?tag={settings.AFFILIATE_TAG}"
    }

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
        "budget": data.get("budget"),
        "revenue": data.get("revenue"),
        "status": data.get("status"),
        "genres": [g["name"] for g in data.get("genres", [])],
        "cast": cast,
        "tagline": data.get("tagline"),
        "trailer_key": trailer_key,
        "watch_providers": watch_providers
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
    """Fetch only the poster URL for a movie with local fallback."""
    if movie_id in _poster_cache:
        return _poster_cache[movie_id]

    data = _make_request(f"/movie/{movie_id}")
    poster = None
    if data and data.get("poster_path"):
        poster = f"{settings.TMDB_IMAGE_URL}{data['poster_path']}"
    
    _poster_cache[movie_id] = poster
    return poster


def get_trending_movies(page: int = 1) -> list:
    """Get Indian-focused trending movies (real-world popular Indian films) mixed with globally trending blockbusters for variety."""
    # Check memory cache first
    if page in _trending_cache:
        timestamp, data = _trending_cache[page]
        if time.time() - timestamp < _CACHE_TTL:
            return data

    # Check disk cache second
    disk_ts, disk_data = _load_disk_cache(f"trending_p{page}.json")
    if disk_ts and (time.time() - disk_ts < _CACHE_TTL):
        _trending_cache[page] = (disk_ts, disk_data)
        return disk_data

    import concurrent.futures
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        # 1. Global Trending — SECONDARY source (real-world trending)
        future_global = executor.submit(_make_request, "/trending/movie/day", {"page": page})
        
        # 2. Indian popular movies — PRIMARY source for Indian users
        future_indian = executor.submit(_make_request, "/discover/movie", {
            "page": page,
            "sort_by": "popularity.desc",
            "with_origin_country": "IN",
            "vote_count.gte": 5,  # Relaxed from 50 to let brand-new trending Indian releases show up
            "vote_average.gte": 4.5,
        })
        
        global_data = future_global.result()
        indian_data = future_indian.result()

    global_results = global_data.get("results", []) if global_data else []
    indian_results = indian_data.get("results", []) if indian_data else []

    # Format helper
    def format_movie(m):
        return {
            "id": m.get("id"),
            "title": m.get("title"),
            "overview": m.get("overview", "")[:150],
            "poster_path": f"{settings.TMDB_IMAGE_URL}{m['poster_path']}" if m.get("poster_path") else None,
            "backdrop_path": f"https://image.tmdb.org/t/p/original{m['backdrop_path']}" if m.get("backdrop_path") else None,
            "vote_average": m.get("vote_average"),
            "release_date": m.get("release_date"),
        }

    # Build the final list: Indian-primary, blended with global trending
    seen_ids = set()
    final_results = []

    # Blend them: alternate Indian and Global movies to make it Indian-heavy (up to 12 Indian, 8 global)
    indian_added = 0
    global_added = 0

    # Blending loop: Alternate 2 Indian movies then 1 Global movie
    for _ in range(20):
        # Add up to 2 Indian movies
        added_in_turn = 0
        while added_in_turn < 2 and indian_added < len(indian_results):
            m = indian_results[indian_added]
            indian_added += 1
            if m.get("id") not in seen_ids and m.get("poster_path"):
                seen_ids.add(m["id"])
                final_results.append(format_movie(m))
                added_in_turn += 1
        
        # Add 1 Global movie
        if global_added < len(global_results):
            m = global_results[global_added]
            global_added += 1
            if m.get("id") not in seen_ids and m.get("poster_path"):
                seen_ids.add(m["id"])
                final_results.append(format_movie(m))

    # Fill remaining slots up to 20 if we ran out of one list
    while len(final_results) < 20 and indian_added < len(indian_results):
        m = indian_results[indian_added]
        indian_added += 1
        if m.get("id") not in seen_ids and m.get("poster_path"):
            seen_ids.add(m["id"])
            final_results.append(format_movie(m))
            
    while len(final_results) < 20 and global_added < len(global_results):
        m = global_results[global_added]
        global_added += 1
        if m.get("id") not in seen_ids and m.get("poster_path"):
            seen_ids.add(m["id"])
            final_results.append(format_movie(m))

    if not final_results:
        print("TMDB_API_ERROR: All TMDB requests failed. Checking disk cache or local fallback.")
        
        if disk_data:
            print("TMDB_CACHE: Returning stale disk cache.")
            return disk_data
            
        fallback_data = _get_fallback_movies(page)
        print(f"TMDB_FALLBACK: Returning {len(fallback_data)} fallback movies.")
        return fallback_data

    results = final_results[:20]
    # Update memory and disk cache
    _trending_cache[page] = (time.time(), results)
    _save_disk_cache(f"trending_p{page}.json", results)
    return results


def _get_fallback_movies(page: int = 1) -> list:
    """Fetch movies from the local CSV dataset as a fallback when API is down."""
    try:
        movies = _get_fallback_data()
        if not movies:
            print("FALLBACK_ERROR: Local CSV is empty or failed. Using hardcoded EMERGENCY_MOVIES.")
            return EMERGENCY_MOVIES
            
        # Robust sampling based on page
        total = len(movies)
        if total <= 20:
            page_movies = movies
        else:
            start = ((page - 1) * 20) % (total - 20)
            page_movies = movies[start : start + 20]
        
        fallback = []
        for m in page_movies:
            fallback.append(_format_local_movie(m))
        
        return fallback
    except Exception as e:
        print(f"FALLBACK ERROR: {e}. Using emergency list.")
        return EMERGENCY_MOVIES




def get_genres() -> list:
    """Get list of all movie genres from TMDB with multi-level caching."""
    global _genres_cache
    
    # 1. Memory Cache
    if _genres_cache:
        timestamp, genres = _genres_cache
        if time.time() - timestamp < _CACHE_TTL * 24: # Genres rarely change
            return [g for g in genres if g.get("name", "").lower() != "documentary"]
            
    # 2. Disk Cache
    disk_ts, disk_genres = _load_disk_cache("genres.json")
    if disk_ts:
        filtered = [g for g in disk_genres if g.get("name", "").lower() != "documentary"]
        _genres_cache = (disk_ts, filtered)
        return filtered

    # 3. API Request
    data = _make_request("/genre/movie/list")
    genres = data.get("genres", [])
    if genres:
        # Filter out Documentary to keep the platform clean
        genres = [g for g in genres if g.get("name", "").lower() != "documentary"]
        
        _genres_cache = (time.time(), genres)
        _save_disk_cache("genres.json", genres)
        return genres
    # 4. Emergency Fallback Genres
    print("TMDB_API_ERROR: Using emergency fallback genres.")
    emergency_genres = [
        {"id": 28, "name": "Action"},
        {"id": 35, "name": "Comedy"},
        {"id": 18, "name": "Drama"},
        {"id": 27, "name": "Horror"},
        {"id": 10749, "name": "Romance"},
        {"id": 878, "name": "Sci-Fi"}
    ]
    return emergency_genres


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
    """Search movies on TMDB by title query with local CSV fallback."""
    data = _make_request("/search/movie", {"query": query, "page": page})
    results = data.get("results", [])

    if not results:
        print(f"SEARCH: No TMDB results for '{query}'. Trying local fallback.")
        return _search_fallback_movies(query)

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


def _search_fallback_movies(query: str) -> list:
    """Search for movies in the local CSV dataset."""
    try:
        movies = _get_fallback_data()
        if not movies:
            return []
            
        query = query.lower()
        results = []
        for m in movies:
            if query in m['title'].lower():
                results.append(_format_local_movie(m))
                if len(results) >= 20:
                    break
        return results
    except Exception as e:
        print(f"SEARCH FALLBACK ERROR: {e}")
        return []


def get_movies_by_language(language_code: str, page: int = 1) -> list[dict]:
    data = _make_request("/discover/movie", {
        "with_original_language": language_code,
        "sort_by": "popularity.desc",
        "page": page
    })
    results = data.get("results", [])

    if not results:
        # Fallback for specific language
        try:
            movies = _get_fallback_data()
            results = [m for m in movies if m['original_language'] == language_code][:20]
            return [_format_local_movie(m) for m in results]
        except: pass
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
        for m in results[:20]
    ]


def get_all_languages_movies(page: int = 1, language: str = None, year: str = None, min_rating: float = None) -> list[dict]:
    """Discover movies with strict advanced combined filters and regional targeting."""
    params = {
        "sort_by": "popularity.desc",
        "page": page,
        "vote_count.gte": 2, 
        "include_adult": "false"
    }
    
    # Map of Indian languages to force IN region
    indian_langs = ['hi', 'mr', 'ta', 'te', 'kn', 'ml', 'bn', 'gu', 'pa']
    
    if language and language != 'all' and language != 'null':
        params["with_original_language"] = language
        if language in indian_langs:
            params["region"] = "IN"
            params["with_origin_country"] = "IN"
    
    if year and year != '' and year != 'null':
        params["primary_release_year"] = year
        
    if min_rating and float(min_rating) > 0:
        params["vote_average.gte"] = float(min_rating)
        params["vote_count.gte"] = 5 

    data = _make_request("/discover/movie", params)
    results = data.get("results", [])
    
    if not results:
        # Fallback with basic filtering
        try:
            movies = _get_fallback_data()
            filtered = movies
            if language and language != 'all':
                filtered = [m for m in filtered if m['original_language'] == language]
            if year:
                year_str = str(year)
                filtered = [m for m in filtered if year_str in m['release_date']]
            if min_rating:
                mr = float(min_rating)
                filtered = [m for m in filtered if m['vote_average'] >= mr]
            
            return [_format_local_movie(m) for m in filtered[:20]]
        except: pass
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

    if not results:
        # Fallback for specific genre
        try:
            movies = _get_fallback_data()
            gid_str = f'"id": {genre_id}'
            results = [m for m in movies if gid_str in m['genres']][:20]
            return [_format_local_movie(m) for m in results]
        except: pass
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

# ═══════════════════════════════════════════
# TV Shows & Web Series Support
# ═══════════════════════════════════════════

def get_trending_tv(page=1):
    """Fetch trending TV shows."""
    return _make_request("/trending/tv/day", {"page": page})

def search_tv(query: str, page=1):
    """Search for TV shows."""
    return _make_request("/search/tv", {"query": query, "page": page})

def get_tv_details(tv_id: int):
    """Get full TV show details including seasons and providers."""
    return _make_request(f"/tv/{tv_id}", {
        "append_to_response": "credits,similar,watch/providers,videos"
    })

def get_tv_season(tv_id: int, season_number: int):
    """Get episodes for a specific TV show season."""
    return _make_request(f"/tv/{tv_id}/season/{season_number}")

def get_trending_tv_language(language_code: str, page=1):
    """Fetch trending TV shows and filter by original language."""
    # Since TMDB doesn't natively filter trending by language, fetch discover
    return _make_request("/discover/tv", {
        "with_original_language": language_code,
        "sort_by": "popularity.desc",
        "page": page
    })
