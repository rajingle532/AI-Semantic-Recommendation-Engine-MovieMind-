from fastapi import APIRouter, HTTPException, Query
from app.services import tmdb
from app.config import settings

router = APIRouter(prefix="/api/tv", tags=["TV Shows"])

@router.get("/trending")
def get_trending_tv(page: int = 1):
    data = tmdb.get_trending_tv(page)
    results = data.get("results", [])
    
    formatted = []
    for t in results:
        formatted.append({
            "id": t.get("id"),
            "title": t.get("name"), # Use name as title for compatibility
            "overview": t.get("overview", ""),
            "poster_path": f"{settings.TMDB_IMAGE_URL}{t['poster_path']}" if t.get("poster_path") else None,
            "vote_average": t.get("vote_average", 0),
            "release_date": t.get("first_air_date", ""),
            "media_type": "tv"
        })
    return {"results": formatted}

@router.get("/search")
def search_tv(q: str = Query(..., description="Search query"), page: int = 1):
    data = tmdb.search_tv(q, page)
    results = data.get("results", [])
    
    formatted = []
    for t in results:
        formatted.append({
            "id": t.get("id"),
            "title": t.get("name"),
            "overview": t.get("overview", ""),
            "poster_path": f"{settings.TMDB_IMAGE_URL}{t['poster_path']}" if t.get("poster_path") else None,
            "vote_average": t.get("vote_average", 0),
            "release_date": t.get("first_air_date", ""),
            "media_type": "tv"
        })
    return {"results": formatted}

@router.get("/language/{code}")
def get_tv_by_language(code: str, page: int = 1):
    results = tmdb.get_trending_tv_language(code, page)
    
    formatted = []
    for t in results:
        formatted.append({
            "id": t.get("id"),
            "title": t.get("name"),
            "overview": t.get("overview", ""),
            "poster_path": f"{settings.TMDB_IMAGE_URL}{t['poster_path']}" if t.get("poster_path") else None,
            "vote_average": t.get("vote_average", 0),
            "release_date": t.get("first_air_date", ""),
            "media_type": "tv"
        })
    return {"results": formatted}

@router.get("/{tv_id}")
def get_tv_details(tv_id: int):
    data = tmdb.get_tv_details(tv_id)
    if not data or "id" not in data:
        raise HTTPException(status_code=404, detail="TV Show not found")

    similar = []
    for s in data.get("similar", {}).get("results", [])[:10]:
        similar.append({
            "id": s.get("id"),
            "title": s.get("name"),
            "poster_path": f"{settings.TMDB_IMAGE_URL}{s['poster_path']}" if s.get("poster_path") else None,
            "vote_average": s.get("vote_average", 0),
            "release_date": s.get("first_air_date", ""),
            "media_type": "tv"
        })

    raw_providers = data.get("watch/providers", {}).get("results", {})
    country_data = raw_providers.get("IN") or raw_providers.get("US") or {}
    
    def format_logos(items):
        return [{
            "provider_id": item.get("provider_id"),
            "provider_name": item.get("provider_name"),
            "logo_path": f"{settings.TMDB_IMAGE_URL}{item['logo_path']}" if item.get("logo_path") else None
        } for item in items]

    watch_providers = {
        "flatrate": format_logos(country_data.get("flatrate", [])),
        "rent": format_logos(country_data.get("rent", [])),
        "buy": format_logos(country_data.get("buy", [])),
        "link": country_data.get("link", "")
    }

    return {
        "id": data.get("id"),
        "title": data.get("name"),
        "overview": data.get("overview"),
        "poster_path": f"{settings.TMDB_IMAGE_URL}{data['poster_path']}" if data.get("poster_path") else None,
        "backdrop_path": f"https://image.tmdb.org/t/p/original{data['backdrop_path']}" if data.get("backdrop_path") else None,
        "vote_average": data.get("vote_average"),
        "release_date": data.get("first_air_date"),
        "genres": [g["name"] for g in data.get("genres", [])],
        "number_of_seasons": data.get("number_of_seasons"),
        "number_of_episodes": data.get("number_of_episodes"),
        "status": data.get("status"),
        "seasons": data.get("seasons", []),
        "similar": similar,
        "watch_providers": watch_providers,
        "media_type": "tv"
    }

@router.get("/{tv_id}/season/{season_number}")
def get_tv_season(tv_id: int, season_number: int):
    data = tmdb.get_tv_season(tv_id, season_number)
    if not data or "id" not in data:
        raise HTTPException(status_code=404, detail="Season not found")
    
    episodes = []
    for ep in data.get("episodes", []):
        episodes.append({
            "id": ep.get("id"),
            "episode_number": ep.get("episode_number"),
            "name": ep.get("name"),
            "overview": ep.get("overview"),
            "still_path": f"{settings.TMDB_IMAGE_URL}{ep['still_path']}" if ep.get("still_path") else None,
            "air_date": ep.get("air_date"),
            "runtime": ep.get("runtime")
        })
        
    return {
        "id": data.get("id"),
        "season_number": data.get("season_number"),
        "name": data.get("name"),
        "overview": data.get("overview"),
        "poster_path": f"{settings.TMDB_IMAGE_URL}{data['poster_path']}" if data.get("poster_path") else None,
        "episodes": episodes
    }
