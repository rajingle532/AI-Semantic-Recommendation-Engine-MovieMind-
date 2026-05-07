"""
Movie routes — search, details, trending, and genre endpoints.
"""
from fastapi import APIRouter, Query
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

router = APIRouter(prefix="/api/movies", tags=["Movies"])


@router.get("/search")
def search_movies(q: str = Query(..., min_length=1, description="Search query")):
    """Search movies by title using TMDB API."""
    results = search_movies_tmdb(q)
    return {"results": results, "count": len(results)}


@router.get("/semantic")
def search_movies_nlp(q: str = Query(..., min_length=3, description="Describe the movie you want")):
    """
    NLP-powered semantic search — describe a plot, mood, or theme
    and get matching movies. Example: 'a hero who saves the world from aliens'
    """
    results = semantic_search(q)
    return {"results": results, "count": len(results)}


@router.get("/trending")
def trending_movies():
    """Get trending movies this week from TMDB."""
    movies = get_trending_movies()
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
def all_languages_movies(page: int = 1, language: str = None):
    if language and language != 'all':
        return get_movies_by_language(language, page)
    return get_all_languages_movies(page)
