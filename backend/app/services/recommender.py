"""
Recommender Service — loads trained ML models and serves recommendations.
Works with both content-based and hybrid approaches.
"""
import os
import pickle
import numpy as np
from typing import List
from app.config import settings
from app.services.tmdb import get_movie_poster, get_movie_details, get_similar_movies, search_movies_tmdb
from app.database import get_collection
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_ML_LIBS = True
except ImportError:
    print("WARNING: ML libraries (sentence-transformers/sklearn) not found. Semantic search will be disabled.")
    HAS_ML_LIBS = False

# Path to saved models
MODELS_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'saved_models')

# Global model cache
_movies_df = None
_similarity_matrix = None
_bert_model = None
_bert_embeddings = None


def _load_models():
    """Load pickle models into memory (lazy loading)."""
    global _movies_df, _similarity_matrix

    if _movies_df is not None:
        return  # Already loaded

    movie_list_path = os.path.join(MODELS_DIR, 'movie_list.pkl')
    similarity_path = os.path.join(MODELS_DIR, 'similarity.pkl')

    print(f"Attempting to load models from: {MODELS_DIR}")
    print(f"Checking if files exist: movie_list={os.path.exists(movie_list_path)}, similarity={os.path.exists(similarity_path)}")

    if not os.path.exists(movie_list_path) or not os.path.exists(similarity_path):
        print(f"CRITICAL: ML models NOT found at {MODELS_DIR}")
        return

    try:
        if _movies_df is None:
            with open(movie_list_path, 'rb') as f:
                _movies_df = pickle.load(f)
            print("Successfully loaded movie_list.pkl")

        if _similarity_matrix is None:
            with open(similarity_path, 'rb') as f:
                _similarity_matrix = pickle.load(f)
            print(f"Successfully loaded similarity.pkl. Shape: {_similarity_matrix.shape}")
        
    except Exception as e:
        print(f"ERROR loading models: {str(e)}")


def reload_models():
    """Force clear cache and reload all models from disk."""
    global _movies_df, _similarity_matrix, _bert_model, _bert_embeddings
    _movies_df = None
    _similarity_matrix = None
    _bert_model = None
    _bert_embeddings = None
    print("RECOMMANDER: Cache cleared. Models will reload on next request.")
    _load_models()
    _load_bert_model()


def _load_bert_model():
    """Load BERT model and embeddings (lazy loading)."""
    global _bert_model, _bert_embeddings, _movies_df

    if not HAS_ML_LIBS:
        print("RECOMMANDER: Skipping BERT load — ML libraries missing.")
        return

    if _bert_model is not None:
        return

    _load_models() # Ensure movies_df is loaded

    embeddings_path = os.path.join(MODELS_DIR, 'bert_embeddings.pkl')
    
    try:
        print("Loading SentenceTransformer (all-MiniLM-L6-v2)...")
        _bert_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        if os.path.exists(embeddings_path):
            with open(embeddings_path, 'rb') as f:
                _bert_embeddings = pickle.load(f)
            print("Loaded pre-computed BERT embeddings")
        else:
            print("Generating BERT embeddings (first time)...")
            # Generate embeddings for all movies in DF
            overviews = _movies_df['tags'].tolist() # Using 'tags' which has overview + keywords
            _bert_embeddings = _bert_model.encode(overviews, show_progress_bar=True)
            
            with open(embeddings_path, 'wb') as f:
                pickle.dump(_bert_embeddings, f)
            print("Saved BERT embeddings")
            
    except Exception as e:
        print(f"ERROR loading BERT model: {str(e)}")


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


def get_semantic_search_results(query: str, n: int = 15) -> list:
    """
    Find movies based on natural language description using BERT embeddings.
    """
    if not HAS_ML_LIBS:
        return search_movies_tmdb(query)

    _load_bert_model()

    if _bert_model is None or _bert_embeddings is None or _movies_df is None:
        # Fallback to basic search
        return search_movies_tmdb(query)

    # Encode user query
    query_vector = _bert_model.encode([query])
    
    # Calculate cosine similarity between query and all movies
    similarities = cosine_similarity(query_vector, _bert_embeddings)[0]
    
    # Get top N indices
    top_indices = np.argsort(similarities)[::-1][:n]
    
    results = []
    for idx in top_indices:
        movie = _movies_df.iloc[idx]
        movie_id = int(movie['movie_id'])
        
        results.append({
            "id": movie_id,
            "movie_id": movie_id,
            "title": movie['title'],
            "poster_path": get_movie_poster(movie_id),
            "similarity_score": round(float(similarities[idx]), 4),
            "overview": movie.get('overview', '')[:120] + "..."
        })
        
    return results
