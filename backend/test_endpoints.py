import requests
import json

base_url = "http://127.0.0.1:8000"

print("--- Testing /health ---")
try:
    resp = requests.get(f"{base_url}/api/health")
    print(f"Status: {resp.status_code}")
    print(f"Body: {resp.json()}")
except Exception as e:
    print(f"Error: {e}")

print("\n--- Testing /api/auth/signup ---")
signup_data = {
    "name": "Test User",
    "email": "test@moviemind.com",
    "password": "test123456"
}
try:
    resp = requests.post(f"{base_url}/api/auth/signup", json=signup_data)
    print(f"Status: {resp.status_code}")
    print(f"Body: {resp.json()}")
except Exception as e:
    print(f"Error: {e}")

print("\n--- Testing /api/auth/login ---")
login_data = {
    "email": "test@moviemind.com",
    "password": "test123456"
}
try:
    resp = requests.post(f"{base_url}/api/auth/login", json=login_data)
    print(f"Status: {resp.status_code}")
    print(f"Body: {resp.json()}")
except Exception as e:
    print(f"Error: {e}")
