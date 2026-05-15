import requests
import os
from dotenv import load_dotenv

load_dotenv()
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

params = {
    "part": "snippet",
    "q": "Interstellar 2014 official soundtrack",
    "type": "video",
    "videoEmbeddable": "true",
    "videoSyndicated": "true",
    "maxResults": 3,
    "key": YOUTUBE_API_KEY
}
res = requests.get("https://www.googleapis.com/youtube/v3/search", params=params)
print(f"Status: {res.status_code}")
if res.status_code == 200:
    for item in res.json().get("items", []):
        print(item["snippet"]["title"])
        print(f"ID: {item['id']['videoId']}")
else:
    print(res.text)
