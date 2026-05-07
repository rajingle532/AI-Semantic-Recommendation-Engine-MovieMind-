import requests
import json

base_url = "http://127.0.0.1:8000"
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNjlmODYxMjI4ZjYxYWVhOWMxYWFiNGJhIiwiZW1haWwiOiJpbmdsZXJhajc5QGdtYWlsLmNvbSIsImV4cCI6MTc3ODIyNDE2NiwiaWF0IjoxNzc4MTM3NzY2fQ.e5e_sFO__DQrK3DCBoRVSzb5IH1AVNuYNYpDBOMrO6w"
headers = {"Authorization": f"Bearer {token}"}

def fetch_data(endpoint):
    url = f"{base_url}{endpoint}"
    print(f"Fetching {endpoint}...")
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            return resp.json()
        else:
            print(f"Error: {resp.status_code} - {resp.text}")
            return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

print("--- USER DATA VERIFICATION ---")
profile = fetch_data("/api/ratings/my")
watchlist = fetch_data("/api/watchlist/my")
personal_recs = fetch_data("/api/recommend/personal/me")

print("\n--- RESULTS ---")
if profile:
    print(f"Ratings Count: {profile.get('count')}")
    for r in profile.get('ratings', [])[:3]:
        print(f"- Rated {r.get('title')}: {r.get('rating')} stars")

if watchlist:
    print(f"Watchlist Count: {watchlist.get('count')}")
    for w in watchlist.get('watchlist', [])[:3]:
        print(f"- In Watchlist: {w.get('title')}")

if personal_recs:
    print(f"AI Recommendations Count: {personal_recs.get('count')}")
    for rec in personal_recs.get('recommendations', [])[:3]:
        print(f"- Recommended: {rec.get('title')}")
