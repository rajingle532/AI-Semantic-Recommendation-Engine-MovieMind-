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
import re

HINDI_FILLERS = ["batao", "sanga", "dikhao", "dakhva", "ka", "ki", "ke", "hai", "hain", "ko", "se", "mein", "me", "kaisa", "kaisi", "kaun", "kab", "story", "kya"]
ENGLISH_FILLERS = ["tell", "me", "about", "the", "movie", "film", "show", "give", "suggest", "recommend", "info", "details", "story", "plot"]
import re

HINDI_FILLERS = ["batao", "sanga", "dikhao", "dakhva", "ka", "ki", "ke", "hai", "hain", "ko", "se", "mein", "me", "kaisa", "kaisi", "kaun", "kab", "story", "kya"]
ENGLISH_FILLERS = ["tell", "me", "about", "the", "movie", "film", "show", "give", "suggest", "recommend", "info", "details", "story", "plot"]

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
    
    # Fetch posters in PARALLEL to avoid sequential 1s timeouts
    from concurrent.futures import ThreadPoolExecutor
    
    def fetch_rec(i):
        try:
            rec_movie = _movies_df.iloc[i[0]]
            rec_movie_id = int(rec_movie['movie_id'])
            poster = get_movie_poster(rec_movie_id)
            return {
                "id": rec_movie_id,
                "movie_id": rec_movie_id,
                "title": rec_movie['title'],
                "similarity_score": round(float(i[1]), 4),
                "poster_path": poster,
            }
        except:
            return None

    with ThreadPoolExecutor(max_workers=min(n, 20)) as executor:
        results = list(executor.map(fetch_rec, distances[1:n + 1]))
        recommendations = [r for r in results if r is not None]

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
    Uses Gemini-powered intent extraction followed by TMDB search.
    """
    try:
        results = []
        # --- SEARCH PHASE ---
        
        # Fallback to Gemini-powered TMDB Search if ML libs are missing (Render optimized)
        if not HAS_ML_LIBS:
            print("RECOMMANDER: Using Gemini-TMDB Hybrid Search")
            
            # Try to extract a specific movie title first
            extracted_title = await ai_assistant.identify_movie_from_query(query)
            ai_titles = await ai_assistant.get_movie_suggestions_by_vibe(query)
            
            if not isinstance(ai_titles, list):
                ai_titles = []
            
            # Prioritize extracted title
            if extracted_title and extracted_title not in ai_titles:
                ai_titles.insert(0, extracted_title)
                
            seen_ids = set()
            
            # 1. Search for titles suggested by AI in PARALLEL
            if ai_titles:
                search_tasks = [asyncio.to_thread(search_movies_tmdb, title) for title in ai_titles]
                search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
                
                for tmdb_res in search_results:
                    if isinstance(tmdb_res, list) and tmdb_res:
                        m = tmdb_res[0] # Take first match
                        if m['id'] not in seen_ids:
                            results.append(m)
                            seen_ids.add(m['id'])
            
            # 2. Add keyword-based matches if we don't have enough
            if len(results) < n:
                # Try cleaning the query first
                clean_q = query.lower()
                for f in HINDI_FILLERS + ENGLISH_FILLERS:
                    clean_q = re.sub(rf'\b{f}\b', '', clean_q)
                clean_q = re.sub(r'\s+', ' ', clean_q).strip()
                
                keyword_res = await asyncio.to_thread(search_movies_tmdb, clean_q if clean_q else query)
                for m in keyword_res:
                    if m['id'] not in seen_ids:
                        results.append(m)
                        seen_ids.add(m['id'])
        else:
            # ML-powered search (BERT)
            _load_bert_model() # Ensure model and embeddings are loaded (lazy)
            
            if _bert_model is None or _bert_embeddings is None or _movies_df is None:
                results = await asyncio.to_thread(search_movies_tmdb, query)
            else:
                # Encode user query into a vector
                query_vec = _bert_model.encode([query])
                
                # Calculate similarity with all movie embeddings
                similarities = cosine_similarity(query_vec, _bert_embeddings).flatten()
                
                # Get top N indices
                top_indices = similarities.argsort()[-n:][::-1]
                
                for idx in top_indices:
                    movie_row = _movies_df.iloc[idx]
                    results.append({
                        "id": int(movie_row['id']),
                        "title": movie_row['title'],
                        "poster_path": get_movie_poster(int(movie_row['id'])),
                        "vote_average": float(movie_row['vote_average']) if 'vote_average' in movie_row else 0.0,
                        "release_date": str(movie_row['release_date']) if 'release_date' in movie_row else ""
                    })

        # --- PHASE 2: Knowledge Augmentation ---
        # Fetch full details (Plot, Cast, Streaming) for the top 3 results to provide rich context to Gemini
        if results:
            detail_tasks = []
            top_n_to_augment = min(len(results), 3)
            
            for i in range(top_n_to_augment):
                detail_tasks.append(asyncio.to_thread(get_movie_details, results[i]['id']))
            
            detailed_data_list = await asyncio.gather(*detail_tasks, return_exceptions=True)
            
            # Map back to results
            for i, detailed_data in enumerate(detailed_data_list):
                if i < len(results) and isinstance(detailed_data, dict) and detailed_data:
                    # Merge but keep some original search metadata if needed
                    results[i].update(detailed_data)

        return results[:n]

    except Exception as e:
        print(f"SEMANTIC_SEARCH_ERROR: {e}")
        # Final fallback to simple TMDB search
        return await asyncio.to_thread(search_movies_tmdb, query)

