import requests
import json

base_url = "http://127.0.0.1:8000"

# 1. Login to get token
print("--- 1. Logging in ---")
login_data = {
    "email": "test@moviemind.com",
    "password": "test123456"
}
login_resp = requests.post(f"{base_url}/api/auth/login", json=login_data)
if login_resp.status_code != 200:
    print("Login failed. Make sure the user exists.")
    exit()

token = login_resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("Login successful!\n")

# 2. Rate a Sci-Fi movie to influence recommendations
# Inception ID is 27205
print("--- 2. Rating 'Inception' (Sci-Fi) as 5 stars ---")
rating_data = {
    "movie_id": 27205,
    "movie_title": "Inception",
    "rating": 5,
    "poster_path": "/edvWeb1B7YpSNHQw7S27J6vRWO1.jpg"
}
requests.post(f"{base_url}/api/ratings/", json=rating_data, headers=headers)
print("Rating submitted.\n")

# 3. Get Personal Recommendations (Hybrid ML)
print("--- 3. Fetching AI Recommendations (Hybrid ML) ---")
recs_resp = requests.get(f"{base_url}/api/recommend/personal/me", headers=headers)
if recs_resp.status_code == 200:
    recommendations = recs_resp.json().get("recommendations", [])
    print(f"Found {len(recommendations)} personal suggestions:")
    for i, rec in enumerate(recommendations[:5], 1):
        print(f" {i}. {rec['title']} (Relevance Score: {rec.get('relevance_score', 'N/A')})")
else:
    print(f"Error fetching recommendations: {recs_resp.text}")

print("\n--- 4. Testing Content-Based Suggestions (Similar to Inception) ---")
similar_resp = requests.get(f"{base_url}/api/recommend/27205")
if similar_resp.status_code == 200:
    similar = similar_resp.json().get("recommendations", [])
    print(f"Movies similar to Inception:")
    for i, rec in enumerate(similar[:5], 1):
        print(f" {i}. {rec['title']} (Similarity: {rec.get('similarity_score', 'N/A')})")
