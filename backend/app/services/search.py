"""
Semantic Search Service — NLP-powered movie search using BERT.
Upgraded from TF-IDF to Sentence Transformers for better context matching.
"""
from app.services.recommender import get_semantic_search_results

def semantic_search(query: str, n: int = 15) -> list:
    """
    Search movies by natural language description using BERT.
    """
    return get_semantic_search_results(query, n)
