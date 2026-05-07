"""
Rating routes — rate movies and view rating history.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.models.rating import RatingCreate, RatingResponse
from app.utils.security import get_current_user
from app.database import get_collection
from app.services.tmdb import get_movie_details

router = APIRouter(prefix="/api/ratings", tags=["Ratings"])


@router.post("", status_code=status.HTTP_201_CREATED)
def rate_movie(rating_data: RatingCreate, current_user: dict = Depends(get_current_user)):
    """Rate a movie (1-5 stars). Updates existing rating if already rated."""
    if not 1.0 <= rating_data.rating <= 5.0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating must be between 1.0 and 5.0"
        )

    ratings = get_collection("ratings")
    user_id = current_user["user_id"]

    # Upsert — create or update existing rating
    ratings.update_one(
        {"user_id": user_id, "movie_id": rating_data.movie_id},
        {"$set": {
            "user_id": user_id,
            "movie_id": rating_data.movie_id,
            "rating": rating_data.rating,
            "movie_title": rating_data.movie_title,
            "poster_path": rating_data.poster_path,
            "release_date": rating_data.release_date,
            "vote_average": rating_data.vote_average,
        }},
        upsert=True
    )
    return {"message": "Rating saved", "movie_id": rating_data.movie_id, "rating": rating_data.rating}


@router.get("/my")
def get_my_ratings(current_user: dict = Depends(get_current_user)):
    """Get all ratings by the current user."""
    ratings = get_collection("ratings")
    user_id = current_user["user_id"]
    
    user_ratings = list(ratings.find(
        {"user_id": user_id},
        {"_id": 0, "user_id": 0}
    ))
    
    # Alias movie_id to id for frontend compatibility
    for r in user_ratings:
        r["id"] = r["movie_id"]
        # Fallback for old records missing metadata
        if not r.get("movie_title") or not r.get("poster_path"):
            details = get_movie_details(r["movie_id"])
            if details:
                r["movie_title"] = r.get("movie_title") or details.get("title")
                r["poster_path"] = r.get("poster_path") or details.get("poster_path")
                r["release_date"] = r.get("release_date") or details.get("release_date")
                r["vote_average"] = r.get("vote_average") or details.get("vote_average")
        
        r["title"] = r.get("movie_title")
        
    return {"ratings": user_ratings, "count": len(user_ratings)}


@router.delete("/{movie_id}")
def delete_rating(movie_id: int, current_user: dict = Depends(get_current_user)):
    """Remove a rating for a movie."""
    ratings = get_collection("ratings")
    result = ratings.delete_one({
        "user_id": current_user["user_id"],
        "movie_id": movie_id
    })

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rating not found"
        )

    return {"message": "Rating deleted", "movie_id": movie_id}
