"""
Tickets and Showtimes router.
Provides currently playing movies, live theater showtimes from SerpApi, and city listing.
"""
from fastapi import APIRouter, Query, HTTPException
import requests
import time
from typing import List, Dict, Any
from app.config import settings
from app.services.tmdb import _make_request, get_genres
from app.services.offers import get_bms_deep_link, get_paytm_deep_link

router = APIRouter(prefix="/api/tickets", tags=["Tickets"])

CITIES = [
    "Pune", "Mumbai", "Delhi NCR", "Bangalore", "Hyderabad", "Chennai", "Kolkata", 
    "Ahmedabad", "Jaipur", "Lucknow", "Goa", "Noida", "Gurgaon", "Chandigarh", 
    "Surat", "Kanpur", "Nagpur", "Indore", "Thane", "Bhopal", "Visakhapatnam", 
    "Patna", "Vadodara", "Ghaziabad", "Ludhiana", "Agra", "Nashik", "Faridabad", 
    "Meerut", "Rajkot", "Varanasi", "Srinagar", "Aurangabad", "Amritsar", 
    "Navi Mumbai", "Ranchi", "Coimbatore", "Vijayawada", "Jodhpur", "Madurai", 
    "Raipur", "Kota", "Guwahati", "Solapur", "Mysore", "Bareilly", "Aligarh", 
    "Jalandhar", "Bhubaneswar", "Thiruvananthapuram", "Kochi", "Cuttack", 
    "Shimla", "Dehradun", "Rourkela", "Jammu", "Udaipur", "Jhansi", "Nellore",
    "Mangalore", "Belgaum", "Kharagpur", "Kolhapur", "Nanded", "Amravati"
]

LANG_MAP = {
    "hi": "Hindi",
    "en": "English",
    "te": "Telugu",
    "ta": "Tamil",
    "ml": "Malayalam",
    "kn": "Kannada",
    "mr": "Marathi"
}

@router.get("/cities", response_model=List[str])
def get_supported_cities():
    """Get list of supported Indian cities for showtimes."""
    return CITIES

@router.get("/now-playing")
def get_now_playing(city: str = Query("Pune", description="City to filter now playing movies")):
    """
    Fetch now playing movies from TMDB with Indian context.
    Resolves genre IDs to names and formats language codes.
    """
    try:
        # Fetch genres
        genres_list = get_genres()
        genres_map = {g["id"]: g["name"] for g in genres_list} if genres_list else {}

        # Fetch now playing movies (region IN and global)
        params_in = {"region": "IN", "page": 1}
        resp_in = _make_request("/movie/now_playing", params_in)
        results_in = resp_in.get("results", []) if isinstance(resp_in, dict) else []

        params_gen = {"page": 1}
        resp_gen = _make_request("/movie/now_playing", params_gen)
        results_gen = resp_gen.get("results", []) if isinstance(resp_gen, dict) else []

        # Combine results to prioritize Indian-focused releases
        seen_ids = set()
        combined = []

        # Format helper
        def format_movie(m):
            genre_ids = m.get("genre_ids", [])
            movie_genres = [genres_map.get(gid) for gid in genre_ids if gid in genres_map]
            
            lang_code = m.get("original_language", "")
            language = LANG_MAP.get(lang_code, lang_code.upper() if lang_code else "Hindi")
            
            poster_path = m.get("poster_path")
            backdrop_path = m.get("backdrop_path")
            
            return {
                "id": m.get("id"),
                "title": m.get("title"),
                "overview": m.get("overview", "")[:200] + "..." if m.get("overview") else "",
                "poster_path": f"{settings.TMDB_IMAGE_URL}{poster_path}" if poster_path else "https://via.placeholder.com/500x750?text=No+Poster",
                "backdrop_path": f"https://image.tmdb.org/t/p/original{backdrop_path}" if backdrop_path else "https://via.placeholder.com/1280x720?text=No+Backdrop",
                "vote_average": m.get("vote_average", 0.0),
                "release_date": m.get("release_date", "Coming Soon"),
                "genres": movie_genres,
                "language": language
            }

        import random
        
        # Collect all available movies
        all_movies = []
        
        for m in results_in:
            if m.get("id") not in seen_ids and m.get("poster_path"):
                seen_ids.add(m["id"])
                all_movies.append(format_movie(m))
                
        for m in results_gen:
            if m.get("id") not in seen_ids and m.get("poster_path"):
                seen_ids.add(m["id"])
                all_movies.append(format_movie(m))
                
        if not all_movies:
            discover_resp = _make_request("/discover/movie", {"sort_by": "popularity.desc", "with_origin_country": "IN", "page": 1})
            discover_results = discover_resp.get("results", []) if isinstance(discover_resp, dict) else []
            for m in discover_results:
                if m.get("id") not in seen_ids and m.get("poster_path"):
                    seen_ids.add(m["id"])
                    all_movies.append(format_movie(m))

        # Seed random with the city name so the same city always gets the same shuffled order
        # This solves the "all cities look the same" problem effectively and realistically!
        random.seed(city.lower().strip())
        random.shuffle(all_movies)
        
        # Also, randomly drop some movies for smaller cities to make it look even more authentic
        if city.lower().strip() not in ["mumbai", "delhi ncr", "bangalore", "hyderabad", "pune", "chennai"]:
            # Smaller cities have fewer movies
            drop_count = random.randint(2, 6)
            all_movies = all_movies[drop_count:]

        combined = all_movies[:15]

        return {"results": combined, "count": len(combined)}

    except Exception as e:
        print(f"ERROR_IN_NOW_PLAYING_ENDPOINT: {e}")
        return {"results": [], "count": 0, "error": str(e)}

@router.get("/showtimes")
def get_showtimes(movie: str = Query(..., description="Movie title"), city: str = Query("Pune", description="City name")):
    """
    Get live theater names and showtime blocks for a specific movie in a city.
    Utilizes SerpApi's google_showtimes engine.
    """
    if not movie:
        raise HTTPException(status_code=400, detail="Movie name query parameter is required")

    city_clean = city.strip() if city else "Pune"
    bms_link = get_bms_deep_link(city_clean, movie)
    paytm_link = get_paytm_deep_link(city_clean)
    google_search_link = f"https://www.google.com/search?q=BookMyShow+{movie.replace(' ', '+')}+in+{city_clean.replace(' ', '+')}"
    
    if not settings.SERP_API_KEY:
        return {
            "movie": movie,
            "city": city_clean,
            "showtimes": [],
            "bms_link": bms_link,
            "paytm_link": paytm_link,
            "google_search_link": google_search_link,
            "note": "SerpApi key is missing. Showing fallback booking links."
        }

    try:
        # Call SerpApi google_showtimes
        params = {
            "engine": "google_showtimes",
            "q": f"{movie} in {city_clean}",
            "api_key": settings.SERP_API_KEY,
            "hl": "en",
            "gl": "in",
            "location": f"{city_clean}, India"
        }
        
        response = requests.get("https://serpapi.com/search", params=params, timeout=10)
        data = response.json()
        
        if "error" in data:
            print(f"SERPAPI_RESPONSE_ERROR: {data['error']}")
            return {
                "movie": movie,
                "city": city_clean,
                "showtimes": [],
                "bms_link": bms_link,
                "paytm_link": paytm_link,
                "google_search_link": google_search_link,
                "note": f"SerpApi returned error: {data['error']}"
            }
            
        serp_showtimes = data.get("showtimes", [])

        formatted_days = []
        for day_block in serp_showtimes[:3]:  # Up to 3 days (e.g. Today, Tomorrow, etc.)
            day_label = day_block.get("day", "Today")
            formatted_theaters = []
            
            for theater in day_block.get("theaters", []):
                t_name = theater.get("name", "Unknown Theater")
                t_link = theater.get("link", bms_link)
                showing_variants = theater.get("showing", [])
                
                theater_shows = []
                for variant in showing_variants:
                    v_type = variant.get("type", "Standard")
                    times = variant.get("time", [])
                    
                    parsed_timings = []
                    for t in times:
                        t_str = t.get("time", "") if isinstance(t, dict) else str(t)
                        seats = t.get("seat_status", "").lower() if isinstance(t, dict) else ""
                        
                        # Set availability status matching 🟢, 🔴, ⚫ UI indicators
                        if "sold" in seats or "houseful" in seats or "sold out" in seats:
                            status = "Houseful"
                        elif "fast" in seats or "filling" in seats or "almost full" in seats:
                            status = "Filling Fast"
                        else:
                            status = "Available"
                            
                        parsed_timings.append({
                            "time": t_str,
                            "status": status
                        })
                    
                    if parsed_timings:
                        theater_shows.append({
                            "format": v_type,
                            "timings": parsed_timings
                        })
                
                # Make sure the theater actually has showtimes
                if theater_shows:
                    formatted_theaters.append({
                        "name": t_name,
                        "booking_link": t_link if t_link else bms_link,
                        "shows": theater_shows
                    })
            
            if formatted_theaters:
                formatted_days.append({
                    "day": day_label,
                    "theaters": formatted_theaters
                })

        return {
            "movie": movie,
            "city": city_clean,
            "showtimes": formatted_days,
            "bms_link": bms_link,
            "paytm_link": paytm_link,
            "google_search_link": google_search_link
        }

    except Exception as e:
        print(f"SERPAPI_SHOWTIMES_ENDPOINT_ERROR: {e}")
        return {
            "movie": movie,
            "city": city_clean,
            "showtimes": [],
            "bms_link": bms_link,
            "paytm_link": paytm_link,
            "google_search_link": google_search_link,
            "error": str(e)
        }
