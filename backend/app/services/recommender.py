"""
Recommender Service — loads trained ML models and serves recommendations.
Works with both content-based and hybrid approaches.
"""
import os
import pickle
import numpy as np
from typing import List
from app.config import settings
from app.services.tmdb import get_movie_poster, get_movie_details, get_similar_movies
from app.database import get_collection

# Path to saved models
MODELS_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'saved_models')

# Global model cache
_movies_df = None
_similarity_matrix = None


def _load_models():
    """Load pickle models into memory (lazy loading)."""
    global _movies_df, _similarity_matrix

    if _movies_df is not None:
        return  # Already loaded

    movie_list_path = os.path.join(MODELS_DIR, 'movie_list.pkl')
    similarity_path = os.path.join(MODELS_DIR, 'similarity.pkl')

    if not os.path.exists(movie_list_path) or not os.path.exists(similarity_path):
        print("ML models not found. Run 'python -m backend.ml.train_model' first.")
        return

    with open(movie_list_path, 'rb') as f:
        _movies_df = pickle.load(f)

    with open(similarity_path, 'rb') as f:
        _similarity_matrix = pickle.load(f)

    print(f"ML models loaded: {len(_movies_df)} movies, similarity matrix shape: {_similarity_matrix.shape}")


def get_content_recommendations(movie_id: int, n: int = 10) -> list:
    """
    Get top-N similar movies using content-based filtering (cosine similarity).
    """
    _load_models()

    if _movies_df is None or _similarity_matrix is None:
        return []

    # Find movie index by movie_id
    matches = _movies_df[_movies_df['movie_id'] == movie_id]
    if matches.empty:
        # Fallback to TMDB API for newer movies not in our static dataset
        print(f"Movie ID {movie_id} not in local model, falling back to TMDB recommendations")
        return get_similar_movies(movie_id)

    idx = matches.index[0]
    distances = sorted(
        list(enumerate(_similarity_matrix[idx])),
        reverse=True,
        key=lambda x: x[1]
    )

    recommendations = []
    for i in distances[1:n + 1]:
        rec_movie = _movies_df.iloc[i[0]]
        rec_movie_id = int(rec_movie['movie_id'])

        # Fetch poster from TMDB
        poster = get_movie_poster(rec_movie_id)

        recommendations.append({
            "id": rec_movie_id,
            "movie_id": rec_movie_id,
            "title": rec_movie['title'],
            "similarity_score": round(float(i[1]), 4),
            "poster_path": poster,
        })

    return recommendations


def get_hybrid_recommendations(user_id: str, n: int = 10) -> list:
    """
    Get personalized recommendations using hybrid approach.
    Combines content-based scores with user's rating history.
    """
    _load_models()

    if _movies_df is None:
        return []

    # Get user's rated movies
    ratings_col = get_collection("ratings")
    user_ratings = list(ratings_col.find({"user_id": user_id}))

    if not user_ratings:
        # No ratings yet — fall back to trending/popular
        return get_content_recommendations(
            int(_movies_df.iloc[0]['movie_id']), n=n
        )

    # Aggregate recommendations from all rated movies, weighted by rating
    score_map = {}
    rated_ids = set()

    for rating in user_ratings:
        movie_id = rating["movie_id"]
        user_score = rating["rating"]
        rated_ids.add(movie_id)

        # Get content-based recommendations for each rated movie
        recs = get_content_recommendations(movie_id, n=20)
        for rec in recs:
            rec_id = rec["movie_id"]
            if rec_id not in rated_ids:
                # Weight by user's rating (higher rated = more influence)
                weighted = rec["similarity_score"] * (user_score / 5.0)
                if rec_id in score_map:
                    score_map[rec_id]["score"] += weighted
                    score_map[rec_id]["count"] += 1
                else:
                    score_map[rec_id] = {
                        "movie_id": rec_id,
                        "title": rec["title"],
                        "poster_path": rec["poster_path"],
                        "score": weighted,
                        "count": 1,
                    }

    # Average scores and sort
    results = []
    for item in score_map.values():
        item["score"] = round(item["score"] / item["count"], 4)
        results.append(item)

    results.sort(key=lambda x: x["score"], reverse=True)

    return [
        {
            "id": r["movie_id"],
            "movie_id": r["movie_id"],
            "title": r["title"],
            "poster_path": r["poster_path"],
            "relevance_score": r["score"],
        }
        for r in results[:n]
    ]
