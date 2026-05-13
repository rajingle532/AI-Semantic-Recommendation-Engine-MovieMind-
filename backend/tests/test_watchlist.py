import pytest

def test_add_to_watchlist(client, auth_headers):
    watchlist_data = {
        "movie_id": 456,
        "movie_title": "Watchlist Movie",
        "poster_path": "/path2.jpg",
        "release_date": "2024-02-02",
        "vote_average": 7.5
    }
    response = client.post("/api/watchlist", json=watchlist_data, headers=auth_headers)
    assert response.status_code == 201
    assert response.json()["message"] == "Added to watchlist"

def test_get_my_watchlist(client, auth_headers):
    response = client.get("/api/watchlist/my", headers=auth_headers)
    assert response.status_code == 200
    assert "watchlist" in response.json()

def test_remove_from_watchlist(client, auth_headers):
    # Add
    client.post("/api/watchlist", json={
        "movie_id": 456,
        "movie_title": "Watchlist Movie",
        "poster_path": "/path2.jpg"
    }, headers=auth_headers)
    
    # Remove
    response = client.delete("/api/watchlist/456", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Removed from watchlist"

def test_watchlist_unauthenticated(client):
    response = client.post("/api/watchlist", json={"movie_id": 456})
    assert response.status_code == 403
