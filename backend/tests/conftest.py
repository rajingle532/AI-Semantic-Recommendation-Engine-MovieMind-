import pytest
import mongomock
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_database
import unittest.mock as mock

@pytest.fixture(scope="session", autouse=True)
def mock_db():
    """Mock the MongoDB database."""
    client = mongomock.MongoClient()
    db = client["test_db"]
    
    with mock.patch("app.database._db", db):
        with mock.patch("app.database.get_database", return_value=db):
            yield db

@pytest.fixture
def client():
    """FastAPI test client."""
    with TestClient(app) as c:
        yield c

@pytest.fixture
def test_user_data():
    return {
        "name": "Test User",
        "email": "test@example.com",
        "password": "password123",
        "phone": "1234567890"
    }

@pytest.fixture
def auth_token(client, test_user_data):
    """Create a user and return an auth token."""
    # Register user
    client.post("/api/auth/signup", json=test_user_data)
    
    # Login to get token
    response = client.post("/api/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    return response.json()["access_token"]

@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}
