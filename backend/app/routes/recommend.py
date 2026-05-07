"""
Recommendation routes — content-based, collaborative, and hybrid recommendations.
"""
from fastapi import APIRouter, Depends
from app.utils.security import get_current_user
from app.services.recommender import (
    get_content_recommendations,
    get_hybrid_recommendations,
)

router = APIRouter(prefix="/api/recommend", tags=["Recommendations"])


@router.get("/{movie_id}")
def recommend_similar(movie_id: int, count: int = 10):
    """
    Get similar movies based on content (genres, keywords, cast, overview).
    No authentication required.
    """
    recommendations = get_content_recommendations(movie_id, n=count)
    return {"movie_id": movie_id, "recommendations": recommendations, "count": len(recommendations)}


@router.get("/personal/me")
def recommend_personal(current_user: dict = Depends(get_current_user)):
    """
    Get personalized recommendations using hybrid model (content + collaborative).
    Requires authentication — uses the user's rating history.
    """
    user_id = current_user["user_id"]
    recommendations = get_hybrid_recommendations(user_id)
    return {"recommendations": recommendations, "count": len(recommendations)}
