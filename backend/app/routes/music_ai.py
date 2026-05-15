from fastapi import APIRouter, HTTPException
from typing import List, Dict
import requests
import json
from app.config import settings
from app.services.ai_assistant import get_ai_response # Reusing existing AI service

router = APIRouter(prefix="/api/music/ai", tags=["Music AI"])

@router.get("/recommend/{mood}")
async def recommend_playlists(mood: str):
    """
    Use Gemini AI to suggest Spotify playlists based on mood.
    Returns a list of curated playlist suggestions.
    """
    prompt = f"""
    The user is feeling '{mood}'. 
    Suggest 4 distinct types of Spotify playlists that would match this mood for a movie lover.
    For each suggestion, provide:
    1. A catchy title
    2. A brief description (max 15 words)
    3. A search query to find this on Spotify
    
    Return the response as a JSON list of objects with keys: title, description, query.
    Do not include any other text.
    """
    
    try:
        # Get AI suggestions
        ai_raw = await get_ai_response(prompt)
        
        # Parse JSON from AI response (handle potential markdown formatting)
        json_str = ai_raw.strip()
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()
            
        suggestions = json.loads(json_str)
        return {"results": suggestions}
        
    except Exception as e:
        print(f"AI Music Error: {e}")
        # Fallback suggestions if AI fails
        fallbacks = {
            "joy": [{"title": "Happy Hits", "description": "Upbeat tracks to keep the good vibes going.", "query": "Happy Hits"}],
            "thrill": [{"title": "Action Score", "description": "Epic orchestral music from blockbuster hits.", "query": "Action Movie Score"}],
            "sorrow": [{"title": "Melancholy Cinema", "description": "Soft, emotive piano tracks from classic dramas.", "query": "Sad Movie Soundtracks"}],
            "mystery": [{"title": "Deep Focus Mystery", "description": "Ambient synth-wave for solving puzzles.", "query": "Mystery Ambient"}]
        }
        return {"results": fallbacks.get(mood, [{"title": "Movie Magic", "description": "General cinematic excellence.", "query": "Movie Soundtracks"}])}

@router.get("/recommend/movie/{movie_id}")
async def recommend_for_movie(movie_id: int):
    """
    Suggest music based on a specific movie's vibe.
    """
    from app.services.tmdb import get_movie_details
    from app.services.ai_assistant import get_music_suggestions_for_movie
    
    details = get_movie_details(movie_id)
    if not details:
        raise HTTPException(status_code=404, detail="Movie not found")
        
    suggestions = await get_music_suggestions_for_movie(details)
    return {"results": suggestions}
