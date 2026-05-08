import requests
api_key = "10e41e2a0017057f445fe9ba08c5ca24"
url = f"https://api.themoviedb.org/3/genre/movie/list?api_key={api_key}"
headers = {"User-Agent": "Mozilla/5.0"}
try:
    response = requests.get(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:200]}")
except Exception as e:
    print(f"Error: {e}")
