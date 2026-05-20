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
from app.services.tmdb import get_movie_details, get_trending_movies, _make_request
try:
    from sentence_transformers import SentenceTransformer
    HAS_BERT = True
except Exception as e:
    print(f"BERT loading bypassed (falling back to standard vectorizer): {e}")
    HAS_BERT = False

# Download NLTK data
nltk.download('punkt', quiet=True)
nltk.download('wordnet', quiet=True)
nltk.download('omw-1.4', quiet=True)

# Paths
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
MODELS_DIR = os.path.join(os.path.dirname(__file__), '..', 'saved_models')

ps = PorterStemmer()


# TMDB Numeric Genre ID to Genre Name mapping
GENRE_MAP = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy", 
    80: "Crime", 99: "Documentary", 18: "Drama", 10751: "Family", 
    14: "Fantasy", 36: "History", 27: "Horror", 10402: "Music", 
    9648: "Mystery", 10749: "Romance", 878: "Science Fiction", 
    10770: "TV Movie", 53: "Thriller", 10752: "War", 37: "Western"
}


def load_local_indian_movies():
    """Loads and converts tmdb_indian_movies.csv to the standard schema as a fallback."""
    indian_path = os.path.join(DATA_DIR, 'tmdb_indian_movies.csv')
    if not os.path.exists(indian_path):
        print("Warning: tmdb_indian_movies.csv backup not found.")
        return pd.DataFrame()
        
    try:
        df = pd.read_csv(indian_path)
        
        # Convert genre IDs list "[35, 18]" to list of [{"name": "Comedy"}, {"name": "Drama"}]
        def parse_and_map_genres(genre_str):
            try:
                import ast
                ids = ast.literal_eval(genre_str)
                return str([{"name": GENRE_MAP.get(gid, "Unknown")} for gid in ids])
            except Exception:
                return str([])

        processed = pd.DataFrame()
        processed['movie_id'] = df['id']
        processed['title'] = df['title']
        processed['overview'] = df['overview'].fillna("")
        processed['genres'] = df['genres'].apply(parse_and_map_genres)
        processed['keywords'] = str([])
        processed['cast'] = str([])
        processed['crew'] = str([])
        
        print(f"Loaded {len(processed)} Indian movies from local CSV backup")
        return processed
    except Exception as e:
        print(f"Warning: Failed to load local Indian movies backup: {e}")
        return pd.DataFrame()


def get_live_movie_data(num_pages=50):
    """Fetch popular Indian movies across multiple languages from TMDB API to build a rich dataset."""
    print("Starting TMDB Live Indian Movies Discover...")
    all_movies = []
    
    # We fetch popular Indian movies for the following languages:
    # Hindi (hi), Telugu (te), Tamil (ta), Malayalam (ml), Kannada (kn)
    languages = {
        "hi": 25,  # 500 movies
        "te": 15,  # 300 movies
        "ta": 15,  # 300 movies
        "ml": 10,  # 200 movies
        "kn": 5    # 100 movies
    }
    
    for lang, pages in languages.items():
        print(f"   Fetching popular {lang.upper()} movies ({pages} pages)...")
        fetched_for_lang = 0
        for page in range(1, pages + 1):
            try:
                # Use discover/movie to filter by original language and sort by popularity
                params = {
                    "sort_by": "popularity.desc",
                    "with_original_language": lang,
                    "page": page
                }
                data = _make_request("/discover/movie", params)
                if not data:
                    break
                    
                results = data.get("results", [])
                if not results:
                    break
                    
                for m in results:
                    genre_ids = m.get("genre_ids", [])
                    mapped_genres = [{"name": GENRE_MAP.get(gid, "Unknown")} for gid in genre_ids]
                    all_movies.append({
                        "movie_id": m.get("id"),
                        "title": m.get("title"),
                        "overview": m.get("overview", ""),
                        "genres": str(mapped_genres),
                        "keywords": str([]),
                        "cast": str([]),
                        "crew": str([])
                    })
                    fetched_for_lang += 1
            except Exception as e:
                print(f"      Error fetching {lang.upper()} page {page}: {e}")
                break
        print(f"   Finished {lang.upper()}: Fetched {fetched_for_lang} movies")
            
    df = pd.DataFrame(all_movies)
    if not df.empty:
        df.dropna(subset=['movie_id', 'title'], inplace=True)
    print(f"TMDB Live Fetch complete! Total movies fetched: {len(df)}")
    return df


def load_and_merge_data():
    """Load TMDB CSV files, fetch live Indian movies, and merge them all together."""
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
    movies.dropna(subset=['movie_id', 'title'], inplace=True)

    print(f"Loaded {len(movies)} movies from local TMDB 5000 CSV")

    # Fetch and Merge Live Indian movies
    try:
        live_indian = get_live_movie_data()
        if not live_indian.empty:
            movies = pd.concat([movies, live_indian], ignore_index=True)
            print(f"Successfully merged {len(live_indian)} live Indian movies into dataset!")
        else:
            # Fallback to local Indian movies CSV if API returned nothing
            print("Live fetch returned empty. Using local Indian CSV backup...")
            local_indian = load_local_indian_movies()
            if not local_indian.empty:
                movies = pd.concat([movies, local_indian], ignore_index=True)
    except Exception as e:
        print(f"Warning: TMDB Live API Fetch failed ({e}). Using local Indian CSV backup...")
        local_indian = load_local_indian_movies()
        if not local_indian.empty:
            movies = pd.concat([movies, local_indian], ignore_index=True)

    # Deduplicate in case a movie exists in both local CSV and API results
    movies.drop_duplicates(subset=['movie_id'], keep='first', inplace=True)
    movies['overview'] = movies['overview'].fillna("")

    print(f"Total merged dataset size: {len(movies)} movies")
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
    # Use sparse matrix directly to save RAM
    vectors = cv.fit_transform(movies_df['tags'])
    # Cast to float32 to halve the file size (176MB -> 88MB)
    similarity = cosine_similarity(vectors).astype(np.float32)

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


def train_bert_only(movies_df):
    """Specifically train and save BERT embeddings."""
    if not HAS_BERT:
        print("Skipping BERT training: Libraries not installed.")
        return

    print("Generating BERT embeddings...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode(movies_df['tags'].tolist(), show_progress_bar=True)
    
    embeddings_path = os.path.join(MODELS_DIR, 'bert_embeddings.pkl')
    with open(embeddings_path, 'wb') as f:
        pickle.dump(embeddings, f)
    print(f"BERT embeddings saved to {embeddings_path}")


def full_retrain(use_live_data=False):
    """Complete re-training pipeline (Content-based + BERT)."""
    print("Starting full re-train...")
    
    # 1. Load Data
    if use_live_data:
        movies = get_live_movie_data()
    else:
        movies = load_and_merge_data()
        
    if movies is None or movies.empty:
        print("Retrain failed: No data found")
        return False
        
    # 2. Build Features
    movies_processed = build_features(movies)
    
    # 3. Content Similarity
    similarity = compute_similarity(movies_processed)
    
    # 4. BERT Training
    if HAS_BERT:
        train_bert_only(movies_processed)
    else:
        print("Skipping BERT step in full_retrain.")
        
    print("Full re-train completed successfully!")
    
    # 5. Save everything
    save_models(movies_processed, similarity)
    return True


if __name__ == "__main__":
    train()
