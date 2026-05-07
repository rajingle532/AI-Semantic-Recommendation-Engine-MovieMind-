"""
ML Model Training Script — Content-Based Recommendation Engine.
Processes TMDB dataset, builds feature vectors, and computes cosine similarity.

Usage:
    python -m backend.ml.train_model
"""
import os
import ast
import pickle
import numpy as np
import pandas as pd
import nltk
from nltk.stem.porter import PorterStemmer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Download NLTK data
nltk.download('punkt', quiet=True)
nltk.download('wordnet', quiet=True)
nltk.download('omw-1.4', quiet=True)

# Paths
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
MODELS_DIR = os.path.join(os.path.dirname(__file__), '..', 'saved_models')

ps = PorterStemmer()


def load_and_merge_data():
    """Load TMDB CSV files and merge movies + credits."""
    movies_path = os.path.join(DATA_DIR, 'tmdb_5000_movies.csv')
    credits_path = os.path.join(DATA_DIR, 'tmdb_5000_credits.csv')

    if not os.path.exists(movies_path) or not os.path.exists(credits_path):
        print("Dataset files not found!")
        print(f"   Please place the following files in: {DATA_DIR}")
        print("   - tmdb_5000_movies.csv")
        print("   - tmdb_5000_credits.csv")
        print("   Download from: https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata")
        return None

    movies = pd.read_csv(movies_path)
    credits = pd.read_csv(credits_path)

    # Merge on title
    movies = movies.merge(credits, on='title')

    # Keep only needed columns
    movies = movies[['movie_id', 'title', 'overview', 'genres', 'keywords', 'cast', 'crew']]
    movies.dropna(inplace=True)

    print(f"Loaded {len(movies)} movies")
    return movies


def extract_names(obj_str):
    """Extract 'name' values from JSON-like string list."""
    try:
        items = ast.literal_eval(obj_str)
        return [item['name'] for item in items]
    except (ValueError, KeyError):
        return []


def extract_top_cast(obj_str, n=3):
    """Extract top-N cast member names."""
    try:
        items = ast.literal_eval(obj_str)
        return [item['name'] for item in items[:n]]
    except (ValueError, KeyError):
        return []


def extract_director(obj_str):
    """Extract director name from crew data."""
    try:
        items = ast.literal_eval(obj_str)
        for item in items:
            if item.get('job') == 'Director':
                return [item['name']]
        return []
    except (ValueError, KeyError):
        return []


def stem_text(text):
    """Apply Porter stemming to text."""
    return " ".join([ps.stem(word) for word in text.split()])


def build_features(movies_df):
    """Build the 'tags' column by combining genres, keywords, cast, crew, overview."""
    print("Building feature vectors...")

    movies_df['genres'] = movies_df['genres'].apply(extract_names)
    movies_df['keywords'] = movies_df['keywords'].apply(extract_names)
    movies_df['cast'] = movies_df['cast'].apply(extract_top_cast)
    movies_df['crew'] = movies_df['crew'].apply(extract_director)
    movies_df['overview'] = movies_df['overview'].apply(lambda x: x.split())

    # Combine all features into 'tags'
    movies_df['tags'] = (
        movies_df['overview'] +
        movies_df['genres'] +
        movies_df['keywords'] +
        movies_df['cast'] +
        movies_df['crew']
    )

    # Join list into string and clean
    movies_df['tags'] = movies_df['tags'].apply(lambda x: " ".join(x).lower())

    # Remove spaces in multi-word names (e.g., "Sam Worthington" → "samworthington")
    movies_df['tags'] = movies_df['tags'].apply(
        lambda x: " ".join([word.replace(" ", "") for word in x.split()])
    )

    # Apply stemming
    movies_df['tags'] = movies_df['tags'].apply(stem_text)

    # Keep only essential columns
    result = movies_df[['movie_id', 'title', 'tags']].reset_index(drop=True)

    print(f"Features built for {len(result)} movies")
    return result


def compute_similarity(movies_df):
    """Compute cosine similarity matrix from movie tags."""
    print("Computing cosine similarity matrix...")

    cv = CountVectorizer(max_features=5000, stop_words='english')
    vectors = cv.fit_transform(movies_df['tags']).toarray()
    similarity = cosine_similarity(vectors)

    print(f"Similarity matrix shape: {similarity.shape}")
    return similarity


def save_models(movies_df, similarity):
    """Save trained models as pickle files."""
    os.makedirs(MODELS_DIR, exist_ok=True)

    movie_list_path = os.path.join(MODELS_DIR, 'movie_list.pkl')
    similarity_path = os.path.join(MODELS_DIR, 'similarity.pkl')

    with open(movie_list_path, 'wb') as f:
        pickle.dump(movies_df, f)

    with open(similarity_path, 'wb') as f:
        pickle.dump(similarity, f)

    print(f"Models saved to {MODELS_DIR}")
    print(f"   - movie_list.pkl ({os.path.getsize(movie_list_path) / 1024:.1f} KB)")
    print(f"   - similarity.pkl ({os.path.getsize(similarity_path) / (1024*1024):.1f} MB)")


def train():
    """Main training pipeline."""
    print("=" * 60)
    print("Movie Recommender - Model Training")
    print("=" * 60)

    # Step 1: Load data
    movies = load_and_merge_data()
    if movies is None:
        return

    # Step 2: Build features
    movies = build_features(movies)

    # Step 3: Compute similarity
    similarity = compute_similarity(movies)

    # Step 4: Save models
    save_models(movies, similarity)

    print("=" * 60)
    print("Training complete! Models are ready.")
    print("=" * 60)


if __name__ == "__main__":
    train()
