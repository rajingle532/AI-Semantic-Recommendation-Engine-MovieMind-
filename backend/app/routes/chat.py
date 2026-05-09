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
    Enhanced Chat API with context awareness and Multilingual support.
    """
    message = payload.get("message", "").lower()
    history = payload.get("history", [])
    
    # 1. Language Detection (Basic)
    is_hindi = any(word in message for word in ["kaun", "hai", "dikhao", "batao", "acha", "film", "movie dikhao"])
    is_marathi = any(word in message for word in ["konta", "aahe", "dakhva", "sang", "changla", "pahije"])
    is_greeting = any(word in message for word in ["hi", "hello", "hey", "hola", "namaste", "namaskar"])
    
    # 2. Greeting Handling
    if is_greeting and not history:
        if is_marathi:
            resp = "Namaskar! Me tumcha MovieMind AI aahe. Tumhala konta movie pahije?"
        elif is_hindi:
            resp = "Namaste! Main aapka MovieMind AI hoon. Aap kaunsi movie dekhna chahenge?"
        else:
            resp = random.choice(GREETINGS)
            
        return {
            "response": resp,
            "movies": [],
            "suggestions": QUICK_PROMPTS,
            "intent": "greeting"
        }

    # 3. Get Hybrid Results (Multilingual BERT + TMDB)
    movies = get_semantic_search_results(message, n=5)
    
    # 4. Build Dynamic Response
    if len(movies) > 0:
        top_movie = movies[0]
        if is_marathi:
            ai_response = f"Tumchya '{message}' pasanti nusar, mala watte tumhala **{top_movie['title']}** nakki awadel!"
        elif is_hindi:
            ai_response = f"Aapki '{message}' ki pasand ke hisab se, mujhe lagta hai aapko **{top_movie['title']}** bahut pasand aayegi!"
        else:
            ai_response = f"Based on your interest in '{message}', I think you'd really enjoy **{top_movie['title']}**. It's a perfect match for that vibe!"
        
        for m in movies:
            m["reason"] = "Matches your interest" if not is_hindi else "Aapki pasand ke mutabik"
    else:
        if is_marathi:
            ai_response = "Mala tya baddal mahiti milali nahi, pan he trending movies tumhi pahu sakta:"
        elif is_hindi:
            ai_response = "Mujhe uske baare mein exact results nahi mile, lekin ye trending movies aapko pasand aa sakti hain:"
        else:
            ai_response = "I couldn't find an exact match, but these trending titles are currently making waves:"
        
        movies = tmdb.get_trending_movies()[:5]
        for m in movies:
            m["reason"] = "Trending choice"

    return {
        "response": ai_response,
        "movies": movies,
        "suggestions": ["Show more", "Kuch aur dikhao", "Video trailers"],
        "intent": "recommendation"
    }
