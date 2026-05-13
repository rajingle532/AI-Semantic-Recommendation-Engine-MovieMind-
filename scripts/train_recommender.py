import pandas as pd
import numpy as np
import os
import pickle
import ast
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Configuration
DATA_DIR = "backend/data"
OUTPUT_DIR = "backend/saved_models"
MOVIES_FILE = os.path.join(DATA_DIR, "tmdb_5000_movies.csv")
INDIAN_MOVIES_FILE = os.path.join(DATA_DIR, "tmdb_indian_movies.csv")

def load_and_merge():
    print("Loading datasets...")
    # 1. Load original dataset
    df_global = pd.read_csv(MOVIES_FILE)
    df_global = df_global[['id', 'title', 'overview', 'genres', 'vote_average', 'release_date']]
    
    # 2. Load Indian dataset
    if os.path.exists(INDIAN_MOVIES_FILE):
        df_indian = pd.read_csv(INDIAN_MOVIES_FILE)
        # Rename id to match
        df_indian = df_indian[['id', 'title', 'overview', 'genres', 'vote_average', 'release_date']]
        
        # Merge
        df = pd.concat([df_global, df_indian], ignore_index=True)
        # Drop duplicates based on id
        df = df.drop_duplicates(subset='id')
    else:
        df = df_global

    return df

def clean_data(df):
    print("Cleaning data...")
    df.dropna(inplace=True)
    
    def convert_genres(obj):
        if isinstance(obj, list): return " ".join(obj)
        try:
            # Handle stringified list of dicts from original dataset
            L = []
            for i in ast.literal_eval(obj):
                L.append(i['name'])
            return " ".join(L)
        except:
            return str(obj)

    df['genres'] = df['genres'].apply(convert_genres)
    df['overview'] = df['overview'].apply(lambda x: x.split())
    df['genres'] = df['genres'].apply(lambda x: x.split())
    
    # Create tags
    df['tags'] = df['overview'] + df['genres']
    df['tags'] = df['tags'].apply(lambda x: " ".join(x))
    
    # Rename id to movie_id for consistency with existing recommender.py
    df.rename(columns={'id': 'movie_id'}, inplace=True)
    
    return df[['movie_id', 'title', 'tags', 'vote_average', 'release_date']]

def train_and_save(df):
    print(f"Training on {len(df)} movies...")
    cv = CountVectorizer(max_features=5000, stop_words='english')
    vectors = cv.fit_transform(df['tags']).toarray()
    
    similarity = cosine_similarity(vectors).astype('float32')
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    pickle.dump(df, open(os.path.join(OUTPUT_DIR, 'movie_list.pkl'), 'wb'))
    pickle.dump(similarity, open(os.path.join(OUTPUT_DIR, 'similarity.pkl'), 'wb'))
    print(f"Models saved successfully to {OUTPUT_DIR} (Size: {similarity.nbytes / 1024 / 1024:.2f} MB)")

if __name__ == "__main__":
    df = load_and_merge()
    df = clean_data(df)
    train_and_save(df)
