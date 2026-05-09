from fastapi import APIRouter, Depends, Query, Body
from app.services.recommender import get_semantic_search_results
from app.services import tmdb
from typing import List, Optional, Dict, Any
import random

router = APIRouter(prefix="/api/chat", tags=["AI Chat"])

# Advanced Templates
GREETINGS = [
    "Hello! I'm MovieMind AI, your personal cinema expert. What's on your mind today?", 
    "Hi! Ready to discover your next favorite movie? Tell me what you're in the mood for.", 
    "Hey! I've been analyzing thousands of films. Want a recommendation based on a specific vibe?"
]

QUICK_PROMPTS = [
    "Suggest a mind-bending thriller",
    "Feeling sad, need something uplifting",
    "Top rated Sci-Fi movies",
    "Action movies with great stunts"
]

@router.post("/")
async def chat_response(payload: Dict[str, Any]):
    """
    Enhanced Chat API with context awareness.
    Input: { message: str, history: List[Dict] }
    """
    message = payload.get("message", "").lower()
    history = payload.get("history", [])
    
    # 1. Simple Intent Detection
    is_greeting = any(word in message for word in ["hi", "hello", "hey", "hola", "greetings"])
    
    if is_greeting and not history:
        return {
            "response": random.choice(GREETINGS),
            "movies": [],
            "suggestions": QUICK_PROMPTS,
            "intent": "greeting"
        }

    # 2. Get Semantic Results
    # We pass the message to our BERT model
    movies = get_semantic_search_results(message, n=5)
    
    # 3. Build Dynamic Response
    if len(movies) > 0:
        top_movie = movies[0]
        ai_response = f"Based on your interest in '{message}', I think you'd really enjoy **{top_movie['title']}**. It matches the vibe you're looking for!"
        
        # Add reasoning to each movie
        for m in movies:
            m["reason"] = f"Matches your interest in {message}"
    else:
        ai_response = "I couldn't find an exact match for that specific request, but these trending titles are currently making waves:"
        movies = tmdb.get_trending_movies()[:5]
        for m in movies:
            m["reason"] = "Trending choice"

    return {
        "response": ai_response,
        "movies": movies,
        "suggestions": ["Tell me more", "Something different?", "Show me trailers"],
        "intent": "recommendation"
    }
