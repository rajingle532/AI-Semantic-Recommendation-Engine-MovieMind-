import pytest
from unittest.mock import patch

@patch("app.routes.recommend.get_content_recommendations")
def test_recommend_similar(mock_recommend, client):
    mock_recommend.return_value = [{"id": 2, "title": "Similar Movie"}]
    response = client.get("/api/recommend/123")
    assert response.status_code == 200
    assert "recommendations" in response.json()
    assert len(response.json()["recommendations"]) > 0

@patch("app.routes.recommend.get_content_recommendations")
def test_recommend_invalid_id(mock_recommend, client):
    mock_recommend.return_value = []
    response = client.get("/api/recommend/999999")
    assert response.status_code == 200
    assert response.json()["recommendations"] == []
