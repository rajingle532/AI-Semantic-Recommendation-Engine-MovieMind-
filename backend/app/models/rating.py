"""
Rating & Watchlist schemas — Pydantic models for movie interactions.
"""
from pydantic import BaseModel
from typing import Optional


class RatingCreate(BaseModel):
    """Schema for creating/updating a movie rating."""
    movie_id: int
    rating: float  # 1.0 to 5.0
    movie_title: Optional[str] = None
    poster_path: Optional[str] = None
    release_date: Optional[str] = None
    vote_average: Optional[float] = None
    media_type: str = "movie"


class RatingResponse(BaseModel):
    """Schema for rating data in API responses."""
    movie_id: int
    rating: float
    movie_title: Optional[str] = None
    poster_path: Optional[str] = None
    release_date: Optional[str] = None
    vote_average: Optional[float] = None
    media_type: str = "movie"


class WatchlistCreate(BaseModel):
    """Schema for adding a movie to watchlist."""
    movie_id: int
    movie_title: str
    poster_path: Optional[str] = None
    release_date: Optional[str] = None
    vote_average: Optional[float] = None
    media_type: str = "movie"


class WatchlistResponse(BaseModel):
    """Schema for watchlist item in API responses."""
    movie_id: int
    movie_title: str
    poster_path: Optional[str] = None
    release_date: Optional[str] = None
    vote_average: Optional[float] = None
    media_type: str = "movie"
