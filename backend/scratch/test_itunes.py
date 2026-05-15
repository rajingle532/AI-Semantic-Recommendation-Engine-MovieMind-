import requests

def search_itunes_soundtrack(movie_title):
    print(f"Searching iTunes for {movie_title} Soundtrack...")
    
    # 1. Search for the album
    url = "https://itunes.apple.com/search"
    params = {
        "term": f"{movie_title} soundtrack",
        "entity": "album",
        "limit": 1
    }
    
    res = requests.get(url, params=params, timeout=10)
    data = res.json()
    
    if data['resultCount'] == 0:
        print("No album found.")
        return
        
    album = data['results'][0]
    collection_id = album['collectionId']
    print(f"Found Album: {album['collectionName']}")
    print(f"Image: {album['artworkUrl100']}")
    
    # 2. Get tracks for the album
    lookup_url = "https://itunes.apple.com/lookup"
    lookup_params = {
        "id": collection_id,
        "entity": "song"
    }
    
    res2 = requests.get(lookup_url, params=lookup_params, timeout=10)
    data2 = res2.json()
    
    tracks = [item for item in data2['results'] if item['wrapperType'] == 'track']
    print(f"Found {len(tracks)} tracks.")
    
    if tracks:
        print(f"Track 1: {tracks[0]['trackName']} - Preview: {tracks[0].get('previewUrl', 'None')}")

search_itunes_soundtrack("Interstellar")
