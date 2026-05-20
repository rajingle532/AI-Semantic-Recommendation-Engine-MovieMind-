import requests
import sys

def test_itunes(movie_title):
    queries = [
        f"{movie_title} original motion picture soundtrack",
        f"{movie_title} soundtrack",
        f"{movie_title} ost"
    ]
    for q in queries:
        print(f"Searching iTunes for: {q}")
        res = requests.get("https://itunes.apple.com/search", params={"term": q, "entity": "album", "limit": 1})
        if res.status_code == 200:
            data = res.json()
            if data.get("resultCount", 0) > 0:
                print(f"Found! {data['results'][0]['collectionName']}")
                return
    print("Not found.")

test_itunes("Shiddat")
