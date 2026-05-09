from fastapi import APIRouter, Depends, Query
from app.services.recommender import get_semantic_search_results, _load_bert_model
from app.services import tmdb
from typing import List, Optional
import random

router = APIRouter(prefix="/api/chat", tags=["AI Chat"])

# Simple templates for conversational feel
GREETINGS = ["Hello! I'm your MovieMind AI Assistant. How can I help you find a movie today?", 
             "Hi there! Looking for something specific to watch?", 
             "Hey! Tell me what kind of mood you're in, and I'll find the perfect movie for you."]

MOOD_RESPONSES = {
    "happy": "That's great! Here are some feel-good movies to keep that smile going:",
    "sad": "I'm sorry to hear that. Maybe a touching drama or an uplifting story will help?",
    "bored": "Let's spice things up with some high-octane action or a mind-bending mystery!",
    "excited": "Awesome! You'll love these high-energy blockbusters:"
}

@router.get("/")
def chat_response(message: str = Query(..., min_length=1)):
    """
    Main Chat API that processes user messages and returns conversational responses
    along with movie suggestions.
    """
    msg = message.lower()
    
    # 1. Simple Greeting Check
    if any(word in msg for word in ["hi", "hello", "hey", "hola"]):
        return {
            "response": random.choice(GREETINGS),
            "movies": [],
            "intent": "greeting"
        }

    # 2. Mood Check
    found_mood = None
    for mood in MOOD_RESPONSES:
        if mood in msg:
            found_mood = mood
            break
    
    # 3. Use Semantic Search to find movies based on the user's message
    # This uses the BERT-powered logic (which we will refine)
    movies = get_semantic_search_results(message, n=5)
    
    # 4. Construct conversational response
    if found_mood:
        ai_response = MOOD_RESPONSES[found_mood]
    elif len(movies) > 0:
        ai_response = f"I found a few movies that match your description: '{message}'. Hope you like them!"
    else:
        ai_response = "I couldn't find exact matches, but here are some trending titles you might enjoy:"
        movies = tmdb.get_trending_movies()[:5]

    return {
        "response": ai_response,
        "movies": movies,
        "intent": "recommendation" if movies else "fallback"
    }
