import requests
import base64
import os
from dotenv import load_dotenv

load_dotenv()
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

auth_string = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
auth_base64 = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")
headers = {
    "Authorization": f"Basic {auth_base64}",
    "Content-Type": "application/x-www-form-urlencoded"
}
data = {"grant_type": "client_credentials"}

res = requests.post("https://accounts.spotify.com/api/token", headers=headers, data=data)
token = res.json().get("access_token")

headers = {"Authorization": f"Bearer {token}"}
params = {"q": "Interstellar", "type": "track", "limit": 1}
search_res = requests.get("https://api.spotify.com/v1/search", headers=headers, params=params)

print(f"Status: {search_res.status_code}")
print(f"Body: {search_res.text}")
