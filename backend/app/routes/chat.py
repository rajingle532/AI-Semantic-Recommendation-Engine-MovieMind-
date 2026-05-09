from fastapi import APIRouter, Depends, Query, Body
from app.services.recommender import get_semantic_search_results
from app.services import tmdb, ai_assistant
from typing import List, Optional, Dict, Any
import random
import re

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

# Keyword to Genre Mapping for better intent detection
GENRE_KEYWORDS = {
    "action": 28, "dhishoom": 28, "ladayi": 28,
    "comedy": 35, "hasao": 35, "funny": 35, "majak": 35,
    "horror": 27, "daravani": 27, "bhoot": 27, "darr": 27,
    "romance": 10749, "love": 10749, "pyaar": 10749, "prem": 10749, "romantic": 10749,
    "thriller": 53, "suspense": 53, "mystery": 9648,
    "sci-fi": 878, "science": 878, "space": 878,
    "animation": 16, "cartoon": 16, "bachon": 16,
    "drama": 18, "emotional": 18, "ronu": 18,
    "crime": 80, "police": 80, "chor": 80
}

HINDI_FILLERS = ["muze", "mujhe", "batao", "dikhao", "film", "movie", "movies", "recommend", "suggest", "karo", "sang", "dakhva", "hai", "kaun", "acha", "achhi", "dikha", "do", "kuch", "vibe"]

# Detailed Info Keywords
INFO_KEYWORDS = ["actor", "cast", "hero", "heroine", "star", "budget", "paisa", "kamaya", "revenue", "box office", "release", "kab aayi", "director", "producer", "role"]

def clean_query(query: str) -> str:
    """Remove common fillers to isolate keywords."""
    words = query.lower().split()
    cleaned = [w for w in words if w not in HINDI_FILLERS]
    return " ".join(cleaned)

@router.post("/")
async def chat_response(payload: Dict[str, Any]):
    """
    Enhanced Chat API with context awareness, Multilingual support, and AI Brain.
    """
    raw_message = payload.get("message", "").lower()
    history = payload.get("history", [])
    
    # 1. Language Detection
    is_hindi = any(word in raw_message for word in ["kaun", "hai", "dikhao", "batao", "acha", "film", "movie dikhao", "pyaar", "prem", "kisne", "karke"])
    is_marathi = any(word in raw_message for word in ["konta", "aahe", "dakhva", "sang", "changla", "pahije", "awadel"])
    is_greeting = any(word in raw_message for word in ["hi", "hello", "hey", "hola", "namaste", "namaskar"])
    is_asking_info = any(word in raw_message for word in INFO_KEYWORDS)
    is_theater_query = any(word in raw_message for word in ["theater", "cinema", "showtime", "ticket", "bookmyshow", "pass ka"])

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

    # 3. Theater Query Handling
    if is_theater_query:
        # Simple location extraction (can be improved with Gemini)
        location = "me" # Default
        words = raw_message.split()
        if "in" in words:
            idx = words.index("in")
            if idx + 1 < len(words):
                location = words[idx + 1]
        elif "near" in words:
            idx = words.index("near")
            if idx + 1 < len(words):
                location = words[idx + 1]
        
        resp = ai_assistant.search_nearby_theaters(location)
        return {
            "response": resp,
            "movies": [],
            "suggestions": ["Find theaters near me", "Theaters in Pune", "Book tickets"],
            "intent": "theater_search"
        }

    # 4. Detailed Info / QA Handling (Gemini)
    if is_asking_info:
        # Try to extract movie title
        cleaned_search = clean_query(raw_message)
        movies = tmdb.search_movies_tmdb(cleaned_search)
        if movies:
            target_movie = tmdb.get_movie_details(movies[0]['id'])
            ai_resp = await ai_assistant.get_ai_movie_info(raw_message, target_movie)
            return {
                "response": ai_resp,
                "movies": [movies[0]],
                "suggestions": ["Tell me more", "Budget details", "Cast roles"],
                "intent": "detailed_info"
            }

    # 5. Regular Recommendation Logic
    detected_genre_id = None
    for kw, gid in GENRE_KEYWORDS.items():
        if kw in raw_message:
            detected_genre_id = gid
            break
            
    cleaned_msg = clean_query(raw_message)
    
    if detected_genre_id and (not cleaned_msg or cleaned_msg in GENRE_KEYWORDS):
        movies = tmdb.get_movies_by_genre(detected_genre_id)
        intent = "genre_discovery"
    else:
        movies = await get_semantic_search_results(raw_message, n=5)
        if not movies and cleaned_msg:
            movies = tmdb.search_movies_tmdb(cleaned_msg)
        intent = "recommendation"
    
    # 6. Build Dynamic Response
    if len(movies) > 0:
        top_movie = movies[0]
        if is_marathi:
            ai_response = f"Tumchya '{raw_message}' pasanti nusar, mala watte tumhala **{top_movie['title']}** nakki awadel!"
        elif is_hindi:
            ai_response = f"Aapki '{raw_message}' ki pasand ke hisab se, mujhe lagta hai aapko **{top_movie['title']}** bahut pasand aayegi!"
        else:
            ai_response = f"Based on your interest in '{raw_message}', I think you'd really enjoy **{top_movie['title']}**."
        
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
        "suggestions": ["Show more", "Kuch aur dikhao", "Video trailers", "Action movies", "Romantic hits"],
        "intent": intent
    }
