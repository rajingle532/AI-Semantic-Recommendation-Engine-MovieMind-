"""
Semantic Search Service — NLP-powered movie search using TF-IDF.
Users can describe a plot/mood and get matching movies.
"""
import os
import pickle
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.services.tmdb import get_movie_poster

# Path to saved models
MODELS_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'saved_models')

# Global cache
_tfidf_vectorizer = None
_tfidf_matrix = None
_movies_df = None


def _load_search_models():
    """Load the movie list and build TF-IDF matrix for semantic search."""
    global _tfidf_vectorizer, _tfidf_matrix, _movies_df

    if _tfidf_matrix is not None:
        return  # Already loaded

    movie_list_path = os.path.join(MODELS_DIR, 'movie_list.pkl')

    if not os.path.exists(movie_list_path):
        print("Movie list not found for semantic search.")
        return

    with open(movie_list_path, 'rb') as f:
        _movies_df = pickle.load(f)

    # Build TF-IDF matrix on movie tags (or overviews if available)
    # Use the 'tags' column if it exists (from training), otherwise fall back to title
    if 'tags' in _movies_df.columns:
        corpus = _movies_df['tags'].fillna('').values
    else:
        corpus = _movies_df['title'].fillna('').values

    _tfidf_vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
    _tfidf_matrix = _tfidf_vectorizer.fit_transform(corpus)

    print(f"Semantic search ready: TF-IDF matrix shape {_tfidf_matrix.shape}")


def semantic_search(query: str, n: int = 10) -> list:
    """
    Search movies by natural language description.
    Example: "a superhero who fights crime at night in a dark city"
    """
    _load_search_models()

    if _tfidf_vectorizer is None or _tfidf_matrix is None:
        return []

    # Vectorize the query
    query_vec = _tfidf_vectorizer.transform([query])

    # Compute cosine similarity between query and all movies
    similarities = cosine_similarity(query_vec, _tfidf_matrix).flatten()

    # Get top-N indices
    top_indices = similarities.argsort()[-n:][::-1]

    results = []
    for idx in top_indices:
        if similarities[idx] > 0:  # Only include if there's some match
            movie = _movies_df.iloc[idx]
            movie_id = int(movie['movie_id'])
            poster = get_movie_poster(movie_id)

            results.append({
                "id": movie_id,
                "movie_id": movie_id,
                "title": movie['title'],
                "similarity_score": round(float(similarities[idx]), 4),
                "poster_path": poster,
            })

    return results
