import pytest
from app.utils.security import create_token, verify_password, hash_password
import jwt
from app.config import settings

def test_signup_success(client):
    response = client.post("/api/auth/signup", json={
        "name": "New User",
        "email": "new@example.com",
        "password": "password123",
        "phone": "9876543210"
    })
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "new@example.com"

def test_signup_duplicate_email(client, test_user_data):
    # First signup
    client.post("/api/auth/signup", json=test_user_data)
    
    # Second signup with same email
    response = client.post("/api/auth/signup", json=test_user_data)
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"

def test_login_success(client, test_user_data):
    # Ensure user exists
    client.post("/api/auth/signup", json=test_user_data)
    
    response = client.post("/api/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_wrong_password(client, test_user_data):
    # Ensure user exists
    client.post("/api/auth/signup", json=test_user_data)
    
    response = client.post("/api/auth/login", json={
        "email": test_user_data["email"],
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"

def test_jwt_token_generation_and_verification():
    user_id = "12345"
    email = "test@example.com"
    token = create_token(user_id, email)
    
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    assert payload["user_id"] == user_id
    assert payload["email"] == email
