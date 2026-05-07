import requests
import json

BASE_URL = "http://localhost:8000/api"
TEST_USER = {
    "name": "Final Check User",
    "email": "final_check@example.com",
    "password": "password123"
}

results = []

def log_result(name, status, detail=""):
    results.append({"name": name, "status": status, "detail": detail})
    print(f"{'✅' if status == 'OK' else '❌'} {name}: {detail}")

def test_backend():
    print("\n--- STARTING BACKEND TESTS ---\n")
    
    # 1. Trending
    try:
        resp = requests.get(f"{BASE_URL}/movies/trending")
        if resp.status_code == 200:
            log_result("GET /api/movies/trending", "OK", f"Found {len(resp.json())} movies")
        else:
            log_result("GET /api/movies/trending", "FAIL", f"Status {resp.status_code}")
    except Exception as e:
        log_result("GET /api/movies/trending", "FAIL", str(e))

    # 2. Search
    try:
        resp = requests.get(f"{BASE_URL}/movies/search?q=inception")
        if resp.status_code == 200:
            log_result("GET /api/movies/search?q=inception", "OK", f"Found {len(resp.json())} results")
        else:
            log_result("GET /api/movies/search?q=inception", "FAIL", f"Status {resp.status_code}")
    except Exception as e:
        log_result("GET /api/movies/search?q=inception", "FAIL", str(e))

    # 3. Genres
    try:
        resp = requests.get(f"{BASE_URL}/movies/genres")
        if resp.status_code == 200:
            log_result("GET /api/movies/genres", "OK", f"Found {len(resp.json())} genres")
        else:
            log_result("GET /api/movies/genres", "FAIL", f"Status {resp.status_code}")
    except Exception as e:
        log_result("GET /api/movies/genres", "FAIL", str(e))

    # 4. Language Filter (Hindi)
    try:
        resp = requests.get(f"{BASE_URL}/movies/language/hi")
        if resp.status_code == 200:
            log_result("GET /api/movies/language/hi", "OK", f"Found {len(resp.json())} Hindi movies")
        else:
            log_result("GET /api/movies/language/hi", "FAIL", f"Status {resp.status_code}")
    except Exception as e:
        log_result("GET /api/movies/language/hi", "FAIL", str(e))

    # 5. Genre Filter (Action - 28)
    try:
        resp = requests.get(f"{BASE_URL}/movies/genre/28")
        if resp.status_code == 200:
            log_result("GET /api/movies/genre/28", "OK", f"Found {len(resp.json())} Action movies")
        else:
            log_result("GET /api/movies/genre/28", "FAIL", f"Status {resp.status_code}")
    except Exception as e:
        log_result("GET /api/movies/genre/28", "FAIL", str(e))

    # 6. Recommendation (Inception - 27205)
    try:
        resp = requests.get(f"{BASE_URL}/recommend/27205")
        if resp.status_code == 200:
            log_result("GET /api/recommend/27205", "OK", f"Found {len(resp.json())} recommendations")
        else:
            log_result("GET /api/recommend/27205", "FAIL", f"Status {resp.status_code}")
    except Exception as e:
        log_result("GET /api/recommend/27205", "FAIL", str(e))

    # 7 & 8. Auth Signup/Login
    token = None
    try:
        # Try signup first
        resp = requests.post(f"{BASE_URL}/auth/signup", json=TEST_USER)
        if resp.status_code == 201:
            log_result("POST /api/auth/signup", "OK", "User created")
            token = resp.json().get("access_token")
        elif resp.status_code == 400: # Already exists
            log_result("POST /api/auth/signup", "OK", "User already exists (proceeding to login)")
            # Try login
            resp = requests.post(f"{BASE_URL}/auth/login", json={"email": TEST_USER["email"], "password": TEST_USER["password"]})
            if resp.status_code == 200:
                log_result("POST /api/auth/login", "OK", "Login successful")
                token = resp.json().get("access_token")
            else:
                log_result("POST /api/auth/login", "FAIL", f"Status {resp.status_code}")
        else:
            log_result("POST /api/auth/signup", "FAIL", f"Status {resp.status_code}")
    except Exception as e:
        log_result("Auth Tests", "FAIL", str(e))

    if not token:
        print("Skipping token-based tests due to login failure.")
        return

    headers = {"Authorization": f"Bearer {token}"}

    # 9. Rate a movie (Inception - 27205)
    try:
        resp = requests.post(f"{BASE_URL}/ratings/", headers=headers, json={"movie_id": 27205, "rating": 5})
        if resp.status_code in [200, 201]:
            log_result("POST /api/ratings/", "OK", "Rated movie successfully")
        else:
            log_result("POST /api/ratings/", "FAIL", f"Status {resp.status_code} - {resp.text}")
    except Exception as e:
        log_result("POST /api/ratings/", "FAIL", str(e))

    # 10. Get user ratings
    try:
        resp = requests.get(f"{BASE_URL}/ratings/my", headers=headers)
        if resp.status_code == 200:
            log_result("GET /api/ratings/my", "OK", f"Found {len(resp.json())} ratings")
        else:
            log_result("GET /api/ratings/my", "FAIL", f"Status {resp.status_code}")
    except Exception as e:
        log_result("GET /api/ratings/my", "FAIL", str(e))

    # 11. Add to watchlist
    try:
        resp = requests.post(f"{BASE_URL}/watchlist/", headers=headers, json={"movie_id": 27205})
        if resp.status_code in [200, 201]:
            log_result("POST /api/watchlist/", "OK", "Added to watchlist")
        else:
            log_result("POST /api/watchlist/", "FAIL", f"Status {resp.status_code} - {resp.text}")
    except Exception as e:
        log_result("POST /api/watchlist/", "FAIL", str(e))

    # 12. Get watchlist
    try:
        resp = requests.get(f"{BASE_URL}/watchlist/my", headers=headers)
        if resp.status_code == 200:
            log_result("GET /api/watchlist/my", "OK", f"Found {len(resp.json())} watchlist items")
        else:
            log_result("GET /api/watchlist/my", "FAIL", f"Status {resp.status_code}")
    except Exception as e:
        log_result("GET /api/watchlist/my", "FAIL", str(e))

    # Save results to file for reporting
    with open("backend_test_results.json", "w") as f:
        json.dump(results, f)

if __name__ == "__main__":
    test_backend()
