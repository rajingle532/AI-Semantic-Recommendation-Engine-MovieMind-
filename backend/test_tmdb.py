import requests
api_key = "8265bd1679663a7ea12ac168da84d2e8"
url = f"https://api.themoviedb.org/3/trending/movie/week?api_key={api_key}"
try:
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:500]}")
except Exception as e:
    print(f"Error: {e}")
