import pytest

def test_rate_movie_authenticated(client, auth_headers):
    rating_data = {
        "movie_id": 123,
        "rating": 4.5,
        "movie_title": "Test Movie",
        "poster_path": "/path.jpg",
        "release_date": "2024-01-01",
        "vote_average": 8.0
    }
    response = client.post("/api/ratings", json=rating_data, headers=auth_headers)
    assert response.status_code == 201
    assert response.json()["message"] == "Rating saved"

def test_get_my_ratings(client, auth_headers):
    # Add a rating first
    client.post("/api/ratings", json={
        "movie_id": 123,
        "rating": 4.5,
        "movie_title": "Test Movie",
        "poster_path": "/path.jpg"
    }, headers=auth_headers)
    
    response = client.get("/api/ratings/my", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()["ratings"]) > 0

def test_delete_rating(client, auth_headers):
    # Add
    client.post("/api/ratings", json={
        "movie_id": 123,
        "rating": 4.5,
        "movie_title": "Test Movie",
        "poster_path": "/path.jpg"
    }, headers=auth_headers)
    
    # Delete
    response = client.delete("/api/ratings/123", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Rating deleted"

def test_rating_unauthenticated(client):
    response = client.post("/api/ratings", json={"movie_id": 123, "rating": 5})
    assert response.status_code == 403
