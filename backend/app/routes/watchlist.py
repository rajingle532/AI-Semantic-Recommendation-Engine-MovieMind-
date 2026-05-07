"""
Watchlist routes — save/remove movies to personal watchlist.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.models.rating import WatchlistCreate
from app.utils.security import get_current_user
from app.database import get_collection
from app.services.tmdb import get_movie_details

router = APIRouter(prefix="/api/watchlist", tags=["Watchlist"])


@router.post("", status_code=status.HTTP_201_CREATED)
def add_to_watchlist(item: WatchlistCreate, current_user: dict = Depends(get_current_user)):
    """Add a movie to the user's watchlist."""
    watchlist = get_collection("watchlist")
    user_id = current_user["user_id"]

    # Check if already in watchlist
    existing = watchlist.find_one({"user_id": user_id, "movie_id": item.movie_id})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Movie already in watchlist"
        )

    watchlist.insert_one({
        "user_id": user_id,
        "movie_id": item.movie_id,
        "movie_title": item.movie_title,
        "poster_path": item.poster_path,
        "release_date": item.release_date,
        "vote_average": item.vote_average,
    })

    return {"message": "Added to watchlist", "movie_id": item.movie_id}


@router.get("/my")
def get_my_watchlist(current_user: dict = Depends(get_current_user)):
    """Get all movies in the current user's watchlist."""
    watchlist = get_collection("watchlist")
    user_id = current_user["user_id"]
    items = list(watchlist.find(
        {"user_id": user_id},
        {"_id": 0, "user_id": 0}
    ))
    # Alias movie_id to id for frontend compatibility
    for item in items:
        item["id"] = item["movie_id"]
        # Fallback for old records missing metadata
        if not item.get("movie_title") or not item.get("poster_path"):
            details = get_movie_details(item["movie_id"])
            if details:
                item["movie_title"] = item.get("movie_title") or details.get("title")
                item["poster_path"] = item.get("poster_path") or details.get("poster_path")
                item["release_date"] = item.get("release_date") or details.get("release_date")
                item["vote_average"] = item.get("vote_average") or details.get("vote_average")

        item["title"] = item.get("movie_title") # Also alias movie_title to title

    return {"watchlist": items, "count": len(items)}


@router.delete("/{movie_id}")
def remove_from_watchlist(movie_id: int, current_user: dict = Depends(get_current_user)):
    """Remove a movie from the user's watchlist."""
    watchlist = get_collection("watchlist")
    result = watchlist.delete_one({
        "user_id": current_user["user_id"],
        "movie_id": movie_id
    })

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not in watchlist"
        )

    return {"message": "Removed from watchlist", "movie_id": movie_id}
