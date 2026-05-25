import pickle
import streamlit as st
import requests

import os
from dotenv import load_dotenv

load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "9884f35a46281ab9e767282199095ca5")

def fetch_poster(movie_id):
    url = f"https://api.tmdb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"
    data = requests.get(url)
    data = data.json()
    poster_path = data['poster_path']
    full_path = "https://image.tmdb.org/t/p/w500/" + poster_path
    return full_path

def recommend(movie):
    index = movies[movies['title'] == movie].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    recommended_movie_names = []
    recommended_movie_posters = []
    for i in distances[1:6]:
        # fetch the movie poster
        movie_id = movies.iloc[i[0]].movie_id
        recommended_movie_posters.append(fetch_poster(movie_id))
        recommended_movie_names.append(movies.iloc[i[0]].title)

    return recommended_movie_names,recommended_movie_posters


import os

# Robust path loading for pickle files
def load_pickle(filenames):
    for fn in filenames:
        for path in [fn, os.path.join('backend', 'saved_models', fn), os.path.join('..', 'backend', 'saved_models', fn)]:
            if os.path.exists(path):
                return pickle.load(open(path, 'rb'))
    raise FileNotFoundError(f"Could not find any of the files: {filenames}")

st.header('Movie Recommender System')
movies = load_pickle(['movie_list.pkl'])
similarity = load_pickle(['similarity.pkl'])

movie_list = movies['title'].values
selected_movie = st.selectbox(
    "Type or select a movie from the dropdown",
    movie_list
)

if st.button('Show Recommendation'):
    recommended_movie_names,recommended_movie_posters = recommend(selected_movie)
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.text(recommended_movie_names[0])
        st.image(recommended_movie_posters[0])
    with col2:
        st.text(recommended_movie_names[1])
        st.image(recommended_movie_posters[1])

    with col3:
        st.text(recommended_movie_names[2])
        st.image(recommended_movie_posters[2])
    with col4:
        st.text(recommended_movie_names[3])
        st.image(recommended_movie_posters[3])
    with col5:
        st.text(recommended_movie_names[4])
        st.image(recommended_movie_posters[4])


