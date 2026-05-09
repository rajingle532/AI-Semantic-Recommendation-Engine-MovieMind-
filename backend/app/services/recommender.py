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
from app.services import ai_assistant
from app.database import get_collection
from sklearn.metrics.pairwise import cosine_similarity
import asyncio

try:
    from sentence_transformers import SentenceTransformer
    HAS_ML_LIBS = True
except (ImportError, OSError, Exception):
    HAS_ML_LIBS = False
    print("RECOMMANDER: ML libraries (torch/sentence-transformers) not available. BERT features disabled.")

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
            if hasattr(_similarity_matrix, 'astype'):
                _similarity_matrix = _similarity_matrix.astype('float32') # Save 50% RAM
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


def _load_bert_model():
    """Load Multilingual BERT model and embeddings (lazy loading)."""
    global _bert_model, _bert_embeddings, _movies_df

    if not HAS_ML_LIBS:
        print("RECOMMANDER: Skipping BERT load — ML libraries missing.")
        return

    if _bert_model is not None:
        return

    _load_models() # Ensure movies_df is loaded

    # Use a multilingual model to support Hindi, Marathi, etc.
    model_name = 'paraphrase-multilingual-MiniLM-L12-v2'
    embeddings_path = os.path.join(MODELS_DIR, f'bert_embeddings_{model_name.replace("-", "_")}.pkl')
    
    try:
        print(f"Loading Multilingual SentenceTransformer ({model_name})...")
        _bert_model = SentenceTransformer(model_name, device='cpu')
        _bert_model.max_seq_length = 128
        
        if os.path.exists(embeddings_path):
            with open(embeddings_path, 'rb') as f:
                _bert_embeddings = pickle.load(f)
            print("Loaded pre-computed Multilingual BERT embeddings")
        else:
            print(f"Generating Multilingual embeddings (first time) for {_movies_df.shape[0] if _movies_df is not None else 0} movies...")
            if _movies_df is not None:
                overviews = _movies_df['tags'].tolist()
                _bert_embeddings = _bert_model.encode(overviews, show_progress_bar=True, batch_size=32)
                
                with open(embeddings_path, 'wb') as f:
                    pickle.dump(_bert_embeddings, f)
                print("Saved Multilingual BERT embeddings")
            
    except Exception as e:
        print(f"ERROR loading Multilingual BERT model: {str(e)}")


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


async def get_semantic_search_results(query: str, n: int = 15) -> list:
    """
    Find movies based on natural language description.
    Uses BERT embeddings for true semantic matching.
    """
    global _bert_model, _bert_embeddings, _movies_df
    
    # Fallback to Gemini-powered TMDB Search if ML libs are missing (Render optimized)
    if not HAS_ML_LIBS:
        print("RECOMMANDER: BERT disabled, using Gemini-TMDB Hybrid Search")
        ai_titles = await ai_assistant.get_movie_suggestions_by_vibe(query)
        
        results = []
        seen_ids = set()
        
        # 1. Search for titles suggested by AI
        for title in ai_titles:
            tmdb_res = await asyncio.to_thread(search_movies_tmdb, title)
            if tmdb_res:
                m = tmdb_res[0] # Take first match
                if m['id'] not in seen_ids:
                    results.append(m)
                    seen_ids.add(m['id'])
        
        # 2. Add keyword-based matches if we don't have enough
        if len(results) < n:
            keyword_res = await asyncio.to_thread(search_movies_tmdb, query)
            for m in keyword_res:
                if m['id'] not in seen_ids:
                    results.append(m)
                    seen_ids.add(m['id'])
                    
        return results[:n]
        
    _load_bert_model() # Ensure model and embeddings are loaded (lazy)
    
    if _bert_model is None or _bert_embeddings is None or _movies_df is None:
        print("RECOMMANDER: BERT data not ready, falling back to TMDB Search")
        return await asyncio.to_thread(search_movies_tmdb, query)

    try:
        # Encode user query into a vector
        query_vec = _bert_model.encode([query])
        
        # Calculate cosine similarity against all movies
        sim_scores = cosine_similarity(query_vec, _bert_embeddings)[0]
        
        # Get top-N highest score indices
        top_indices = sim_scores.argsort()[-n:][::-1]
        
        semantic_results = []
        for idx in top_indices:
            movie = _movies_df.iloc[idx]
            score = float(sim_scores[idx])
            
            # Threshold to avoid random results for irrelevant queries
            if score > 0.15: 
                movie_id = int(movie['movie_id'])
                semantic_results.append({
                    "id": movie_id,
                    "movie_id": movie_id,
                    "title": movie['title'],
                    "poster_path": get_movie_poster(movie_id),
                    "relevance_score": round(score, 4),
                    "source": "semantic"
                })
        
        # Hybrid Merge: Prioritize TMDB if score is low, or merge them
        tmdb_results = await asyncio.to_thread(search_movies_tmdb, query)
        final_results = []
        seen_ids = set()

        # Add TMDB results first (likely a direct title/song match)
        for m in tmdb_results:
            if m['id'] not in seen_ids:
                final_results.append(m)
                seen_ids.add(m['id'])

        # Add Semantic results if not already present
        for m in semantic_results:
            if m['id'] not in seen_ids:
                final_results.append(m)
                seen_ids.add(m['id'])
                
        return final_results[:n]
        
    except Exception as e:
        print(f"ERROR in BERT Search: {e}")
        return await asyncio.to_thread(search_movies_tmdb, query)
