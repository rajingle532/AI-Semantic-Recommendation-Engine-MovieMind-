import pytest
from unittest.mock import patch

@patch("app.routes.movies.get_trending_movies")
def test_get_trending(mock_trending, client):
    mock_trending.return_value = [{"id": 1, "title": "Trending Movie"}]
    response = client.get("/api/movies/trending")
    assert response.status_code == 200
    assert len(response.json()["results"]) > 0

@patch("app.routes.movies.search_movies_tmdb")
def test_search_movies(mock_search, client):
    mock_search.return_value = [{"id": 1, "title": "Inception"}]
    response = client.get("/api/movies/search?q=inception")
    assert response.status_code == 200
    assert response.json()["results"][0]["title"] == "Inception"

@patch("app.routes.movies.get_genres")
def test_get_genres(mock_genres, client):
    mock_genres.return_value = [{"id": 28, "name": "Action"}]
    response = client.get("/api/movies/genres")
    assert response.status_code == 200
    assert "genres" in response.json()

@patch("app.routes.movies.get_movies_by_language")
def test_get_movies_by_language(mock_lang, client):
    mock_lang.return_value = {"results": [{"id": 1, "title": "Hindi Movie"}]}
    response = client.get("/api/movies/language/hi")
    assert response.status_code == 200
    assert "results" in response.json()
