"""
Movie routes — search, details, trending, and genre endpoints.
"""
from fastapi import APIRouter, Query, HTTPException, Depends
from app.services import tmdb
from app.services.tmdb import (
    get_movie_details,
    get_trending_movies,
    get_genres,
    search_movies_tmdb,
    get_movies_by_language,
    get_all_languages_movies,
    get_movies_by_genre,
)
from app.services.search import semantic_search
from app.utils.security import get_current_user

router = APIRouter(prefix="/api/movies", tags=["Movies"])

MOOD_MAPPING = {
    "joy": [35, 16, 10751],      # Comedy, Animation, Family
    "thrill": [28, 53, 27],      # Action, Thriller, Horror
    "sorrow": [18, 10749],       # Drama, Romance
    "mystery": [96, 80, 878]     # Mystery, Crime, Sci-Fi
}


@router.get("/search")
def search_movies(q: str = Query(..., min_length=1, description="Search query")):
    """Search movies by title using TMDB API."""
    results = search_movies_tmdb(q)
    return {"results": results, "count": len(results)}


@router.get("/semantic")
async def search_movies_nlp(q: str = Query(..., min_length=3, description="Describe the movie you want")):
    """
    NLP-powered semantic search — describe a plot, mood, or theme
    and get matching movies. Example: 'a hero who saves the world from aliens'
    """
    results = await semantic_search(q)
    return {"results": results, "count": len(results)}


@router.get("/trending")
def trending_movies(page: int = 1):
    """Get trending movies this week from TMDB with pagination support."""
    movies = get_trending_movies(page)
    return {"results": movies, "count": len(movies)}


@router.get("/genres")
def list_genres():
    """Get all available movie genres."""
    genres = get_genres()
    return {"genres": genres}


@router.get("/genre/{genre_id}")
def movies_by_genre(genre_id: int, page: int = 1):
    """Get movies for a specific genre ID."""
    results = get_movies_by_genre(genre_id, page)
    return {"results": results, "count": len(results)}


@router.get("/mood/{mood}")
def movies_by_mood(mood: str, page: int = 1):
    """Get movies based on a specific mood."""
    mood = mood.lower()
    if mood not in MOOD_MAPPING:
        return {"error": "Invalid mood", "available_moods": list(MOOD_MAPPING.keys())}
    
    # Get movies for the first genre in the mood mapping for simplicity, 
    # or we could aggregate results from multiple genres.
    # Let's pick a random one or just the first for now.
    genre_id = MOOD_MAPPING[mood][0] 
    results = get_movies_by_genre(genre_id, page)
    return {"results": results, "mood": mood, "count": len(results)}


@router.get("/swipe-pool")
def swipe_pool(current_user: dict = Depends(get_current_user)):
    """
    Get a diverse list of movies for the Tinder-style CineMatch swiper,
    excluding movies that are already in the user's watchlist or rated.
    """
    user_id = current_user["user_id"]
    from app.database import get_collection
    
    # 1. Gather all excluded movie IDs (watchlist + ratings)
    watchlist_col = get_collection("watchlist")
    ratings_col = get_collection("ratings")
    
    watchlist_ids = {int(x["movie_id"]) for x in watchlist_col.find({"user_id": user_id}) if x.get("movie_id")}
    rating_ids = {int(x["movie_id"]) for x in ratings_col.find({"user_id": user_id}) if x.get("movie_id")}
    exclude_ids = watchlist_ids.union(rating_ids)
    
    # 2. Fetch candidates from trending movies (pages 1 to 3 to get plenty of candidates)
    candidates = []
    seen_candidates = set()
    
    for page in range(1, 4):
        try:
            trending = get_trending_movies(page=page)
            if not trending:
                break
            for m in trending:
                mid = int(m["id"])
                if mid not in exclude_ids and mid not in seen_candidates:
                    candidates.append(m)
                    seen_candidates.add(mid)
            if len(candidates) >= 20:
                break
        except Exception:
            break
            
    # 3. If we don't have enough candidates, append popular movies from some popular genres
    if len(candidates) < 15:
        # Action (28), Comedy (35), Drama (18)
        for gid in [28, 35, 18]:
            try:
                genre_movies = get_movies_by_genre(gid, page=1)
                for m in genre_movies:
                    mid = int(m["id"])
                    if mid not in exclude_ids and mid not in seen_candidates:
                        candidates.append(m)
                        seen_candidates.add(mid)
                if len(candidates) >= 20:
                    break
            except Exception:
                continue

    # Return top 20 candidates
    return {"results": candidates[:20], "count": len(candidates[:20])}


@router.get("/{movie_id}")
def movie_detail(movie_id: int):
    """Get detailed information for a specific movie."""
    details = get_movie_details(movie_id)
    if not details:
        return {"error": "Movie not found"}
    return details


@router.get("/language/{language_code}")
def movies_by_language(language_code: str, page: int = 1):
    return get_movies_by_language(language_code, page)


@router.get("/all")
def all_languages_movies(page: int = 1, language: str = None, year: str = None, min_rating: float = None):
    return get_all_languages_movies(page, language, year, min_rating)

@router.get("/person/{person_id}")
async def person_details(person_id: int):
    """Get person biography and details."""
    details = tmdb.get_person_details(person_id)
    if not details:
        raise HTTPException(status_code=404, detail="Person not found")
    return details

@router.get("/person/{person_id}/movies")
async def person_movies(person_id: int):
    """Get all movies for a person."""
    return tmdb.get_person_movie_credits(person_id)
