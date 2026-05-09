"""
Chat Route — MovieMind AI Chatbot endpoint.
Handles all user interactions: movie Q&A, recommendations, theater booking.
Uses Gemini AI for intelligent responses with TMDB data as context.
"""
from fastapi import APIRouter
from app.services.recommender import get_semantic_search_results
from app.services import tmdb, ai_assistant
from typing import Optional, Dict, Any
import random
import re
import asyncio

router = APIRouter(prefix="/api/chat", tags=["AI Chat"])

# ═══════════════════════════════════════════
# Templates & Constants
# ═══════════════════════════════════════════
GREETINGS = [
    "Hello! I'm MovieMind AI 🎬 Ask me anything about movies — cast, story, ratings, showtimes — or just tell me your mood and I'll find the perfect movie!",
    "Hi! I'm MovieMind AI, your personal cinema expert. Try asking me: 'Tell me about Pushpa 2' or 'Suggest something like Inception'!",
    "Hey! Ready to explore the world of cinema? I can answer any movie question, find showtimes, or recommend based on your vibe!"
]

QUICK_PROMPTS = [
    "Tell me about Pushpa 2",
    "Best thriller movies",
    "Romantic movies suggest karo",
    "Who directed Inception?"
]

GENRE_KEYWORDS = {
    "action": 28, "dhishoom": 28, "ladayi": 28, "fight": 28,
    "comedy": 35, "hasao": 35, "funny": 35, "majak": 35, "hasi": 35,
    "horror": 27, "daravani": 27, "bhoot": 27, "darr": 27, "scary": 27,
    "romance": 10749, "love": 10749, "pyaar": 10749, "prem": 10749, "romantic": 10749,
    "thriller": 53, "suspense": 53, "mystery": 9648,
    "sci-fi": 878, "science fiction": 878, "space": 878,
    "animation": 16, "cartoon": 16, "animated": 16,
    "drama": 18, "emotional": 18, "ronu": 18,
    "crime": 80, "police": 80, "chor": 80, "gangster": 80,
    "war": 10752, "army": 10752, "military": 10752,
    "documentary": 99, "history": 36, "family": 10751,
    "adventure": 12, "fantasy": 14, "music": 10402, "western": 37
}

HINDI_FILLERS = [
    "muze", "mujhe", "batao", "dikhao", "film", "movie", "movies", 
    "recommend", "suggest", "karo", "sang", "dakhva", "hai", "kaun", 
    "acha", "achhi", "dikha", "do", "kuch", "vibe", "bhi", "toh",
    "na", "yaar", "bhai", "please", "pls", "karo", "de", "dedo"
]

# Patterns for extracting movie titles from queries
MOVIE_TITLE_PATTERNS = [
    # English patterns
    r"(?:tell\s+(?:me\s+)?about\s+(?:the\s+)?(?:movie\s+|film\s+)?)(.*)",
    r"(?:what\s+(?:is|about|happens\s+in)\s+(?:the\s+)?(?:movie\s+|film\s+)?)(.*)",
    r"(?:information\s+(?:about|on)\s+(?:the\s+)?(?:movie\s+|film\s+)?)(.*)",
    r"(?:details\s+(?:about|of|on)\s+(?:the\s+)?(?:movie\s+|film\s+)?)(.*)",
    r"(?:who\s+(?:is|are|was|were)\s+(?:the\s+)?(?:hero|heroine|cast|director|actor|lead)\s+(?:of|in)\s+(?:the\s+)?(?:movie\s+|film\s+)?)(.*)",
    r"(?:when\s+(?:was|did)\s+(?:the\s+)?(?:movie\s+|film\s+)?)(.*?)(?:\s+(?:release|come\s+out|made|release\w*))?$",
    r"(?:how\s+much\s+did\s+(?:the\s+)?(?:movie\s+|film\s+)?)(.*?)(?:\s+(?:earn|make|cost|collect))?",
    r"(?:plot\s+(?:of|about)\s+(?:the\s+)?(?:movie\s+|film\s+)?)(.*)",
    r"(?:story\s+(?:of|about)\s+(?:the\s+)?(?:movie\s+|film\s+)?)(.*)",
    r"(?:review\s+(?:of|about|for)\s+(?:the\s+)?(?:movie\s+|film\s+)?)(.*)",
    r"(?:rating\s+(?:of|for)\s+(?:the\s+)?(?:movie\s+|film\s+)?)(.*)",
    r"(?:cast\s+(?:of|in)\s+(?:the\s+)?(?:movie\s+|film\s+)?)(.*)",
    r"(?:budget\s+(?:of|for)\s+(?:the\s+)?(?:movie\s+|film\s+)?)(.*)",
    r"(?:search\s+(?:for\s+)?(?:the\s+)?(?:movie\s+|film\s+)?)(.*)",
    r"(?:find\s+(?:the\s+)?(?:movie\s+|film\s+)?)(.*)",
    # Hindi/Hinglish patterns
    r"(.*?)(?:\s+ke\s+baare\s+mein(?:\s+batao)?)",
    r"(.*?)(?:\s+ka\s+(?:plot|story|hero|cast|budget|director|review|rating))",
    r"(.*?)(?:\s+ki\s+(?:story|kahani|kahaani|heroine|cast|rating))",
    r"(.*?)(?:\s+kab\s+(?:aayi|aai|bani|release\s+hui|nikli))",
    r"(.*?)(?:\s+mein\s+(?:kaun|kya)\s+hai)",
    r"(.*?)(?:\s+kisne\s+(?:direct|banai|banayi)\s+(?:hai|thi)?)",
    r"(.*?)(?:\s+kitna\s+(?:kamaya|earn\s+kiya|collection))",
    r"(.*?)(?:\s+kaisi\s+(?:movie|film)\s+hai)",
    r"(?:movie\s+)(.*?)(?:\s+(?:batao|dikhao|ke|ki|ka))",
    # Marathi patterns
    r"(.*?)(?:\s+chi\s+(?:story|katha|kahani|mahitii|mahiti|acting|role))",
    r"(.*?)(?:\s+baddal\s+(?:sanga|mahitii|mahiti))",
    r"(.*?)(?:\s+kadhi\s+(?:aali|ali|suri\s+zhali|release\s+zhali))",
]

# English filler phrases to strip
ENGLISH_FILLERS = [
    "tell me about the movie", "tell me about movie", "tell me about the film",
    "tell me about", "what is the movie", "what about the movie",
    "information about the movie", "details about the movie", "details of the movie",
    "know about the movie", "search for the movie", "search for movie",
    "find the movie", "find movie", "show me the movie", "show me movie",
    "what is", "who is", "how is", "can you tell me about",
    "i want to know about", "please tell me about", "please find",
    "movie called", "film called", "the movie", "the film",
    "what happens in", "plot of", "story of", "cast of", "budget of",
    "review of", "rating of",
]

# ═══════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════

def extract_movie_title(query: str) -> Optional[str]:
    """Try to extract a specific movie title from the user's query using regex."""
    q = query.lower().strip()
    
    for pattern in MOVIE_TITLE_PATTERNS:
        match = re.search(pattern, q, re.IGNORECASE)
        if match:
            title = match.group(1).strip()
            # Clean trailing fillers
            title = re.sub(r'\s*(movie|film|hai|hain|ka|ki|ke|baare|mein|batao|dikhao|thi|tha|release|kab|kaun|kya)\s*$', '', title).strip()
            # Clean leading fillers
            title = re.sub(r'^(the|a|an|movie|film)\s+', '', title).strip()
            if title and len(title) >= 2:
                return title
    
    return None


def clean_query(query: str) -> str:
    """Remove common fillers to isolate the core search term."""
    q = query.lower().strip()
    
    # Remove English filler phrases (longer ones first)
    for filler in sorted(ENGLISH_FILLERS, key=len, reverse=True):
        q = q.replace(filler, " ")
    
    # Remove Hindi filler words
    words = q.split()
    cleaned = [w for w in words if w not in HINDI_FILLERS]
    result = re.sub(r'\s+', ' ', " ".join(cleaned)).strip()
    return result


def detect_intent(query: str) -> str:
    """
    Detect the user's intent from their query.
    Returns: 'greeting', 'theater', 'movie_question', 'genre', 'recommendation', 'general_question'
    """
    q = query.lower()
    
    # Greeting
    greet_words = ["hi", "hello", "hey", "hola", "namaste", "namaskar", "sup", "yo"]
    if any(q.strip() == g or q.startswith(g + " ") or q.startswith(g + ",") for g in greet_words):
        if len(q.split()) <= 4:
            return "greeting"
    
    # Theater/Ticket
    theater_words = ["theater", "theatre", "cinema", "showtime", "ticket", "bookmyshow", 
                     "book ticket", "pass ka", "booking", "screen", "multiplex", "pvr", "inox"]
    if any(w in q for w in theater_words):
        return "theater"
    
    # Genre/mood-based request (check BEFORE movie_question to avoid false positives)
    # e.g., "romantic movies dikhao" → genre, not movie_question
    genre_only_indicators = ["suggest", "recommend", "best", "top", "good", 
                            "acha", "achhi", "latest", "new", "trending",
                            "mood", "feel like", "something like",
                            "dikhao", "batao", "dakhva", "movies", "films"]
    genre_words_found = [kw for kw in GENRE_KEYWORDS if kw in q.split() or f" {kw} " in f" {q} "]
    if genre_words_found:
        has_genre_indicator = any(gi in q for gi in genre_only_indicators)
        has_specific_title = extract_movie_title(query)
        # If it has a genre word + indicator, and no specific movie title → genre
        if has_genre_indicator and not has_specific_title:
            return "genre"
    
    # Movie-specific question indicators
    movie_question_triggers = [
        "tell me about", "what is", "about the movie", "about movie",
        "ke baare mein", "kaisi hai", "kaisi movie", "kab aayi", "kab bani",
        "kab release", "kitna kamaya", "kisne direct", "kisne banai", "kisne banayi",
        "who directed", "who acted", "who is the hero", "who is the heroine",
        "who are the actors", "cast of", "budget of", "revenue of", "plot of",
        "story of", "rating of", "review of", "when was", "how much did",
        "what happens", "ending of", "sequel of", "remake of",
        "kaun hai", "hero kaun", "heroine kaun", "director kaun",
        "details of", "information about", "know about",
        "actor", "cast", "hero", "heroine", "star", "budget", "paisa", 
        "kamaya", "revenue", "box office", "release", "kab aayi", 
        "director", "producer", "role", "plot", "story", "kahani",
        "batao", "dikhao", "dakhva", "sanga", "baddal", "kadhi", "zhali"
    ]
    if any(t in q for t in movie_question_triggers):
        return "movie_question"
    
    # General question (might still be about a specific movie)
    return "general_question"


def detect_language(query: str) -> str:
    """Detect query language: 'hindi', 'marathi', or 'english'."""
    q = query.lower()
    marathi_words = ["konta", "aahe", "dakhva", "sang", "sanga", "kadhi", "baddal", "changla", "pahije", "awadel", "mala", "tumhala", "kaay"]
    hindi_words = ["kaun", "dikhao", "batao", "acha", "pyaar", "prem", "kisne", "karke",
                   "kab", "kitna", "kaisi", "kya", "hai", "mein", "ke", "ki", "ka", "se", "mujhe"]
    
    if any(w in q.split() for w in marathi_words):
        return "marathi"
    if sum(1 for w in hindi_words if w in q.split()) >= 1:
        return "hindi"
    return "english"


# ═══════════════════════════════════════════
# Main Chat Endpoint
# ═══════════════════════════════════════════

@router.post("/")
async def chat_response(payload: Dict[str, Any]):
    """
    Intelligent Chat API — routes every query to the best handler.
    Every movie question gets a real AI-powered answer via Gemini + TMDB.
    """
    raw_message = payload.get("message", "").strip()
    raw_lower = raw_message.lower()
    history = payload.get("history", [])
    
    # Detect intent and language
    intent = detect_intent(raw_lower)
    lang = detect_language(raw_lower)
    
    print(f"CHAT: Query='{raw_message}' | Intent={intent} | Lang={lang}")

    # ─────────────────────────────────────
    # 1. GREETING
    # ─────────────────────────────────────
    if intent == "greeting":
        if lang == "marathi":
            resp = "Namaskar! 🎬 Me tumcha MovieMind AI aahe. Tumhala kontyahi movie baddal mahiti pahije? Nahi tar mood sanga, mi movie suggest karto!"
        elif lang == "hindi":
            resp = "Namaste! 🎬 Main aapka MovieMind AI hoon. Kisi bhi movie ke baare mein pucho — ya mood batao, main perfect movie dhundh dunga!"
        else:
            resp = random.choice(GREETINGS)
            
        return {
            "response": resp,
            "movies": [],
            "suggestions": QUICK_PROMPTS,
            "intent": "greeting"
        }

    # ─────────────────────────────────────
    # 2. THEATER / TICKET BOOKING
    # ─────────────────────────────────────
    if intent == "theater":
        location = "me"
        movie_name = None
        words = raw_lower.split()
        
        # Extract location
        for keyword in ["in", "near", "at"]:
            if keyword in words:
                idx = words.index(keyword)
                if idx + 1 < len(words):
                    # Take remaining words as location
                    location = " ".join(words[idx + 1:])
                    break
        
        # Try to extract movie name from context
        if history:
            for msg in reversed(history):
                if msg.get('role') == 'assistant' and '**' in msg.get('content', ''):
                    # Extract bold movie title from previous responses
                    bold_match = re.search(r'\*\*(.*?)\*\*', msg['content'])
                    if bold_match:
                        movie_name = bold_match.group(1)
                        break
        
        resp = ai_assistant.search_nearby_theaters(location, movie_name)
        return {
            "response": resp,
            "movies": [],
            "suggestions": ["Theaters in Mumbai", "Theaters in Pune", "Theaters in Delhi", "Book on BookMyShow"],
            "intent": "theater_search"
        }

    # ─────────────────────────────────────
    # 3. MOVIE-SPECIFIC QUESTION (THE MAIN BRAIN)
    # ─────────────────────────────────────
    if intent == "movie_question" or intent == "general_question":
        # Step 1: Extract movie title (regex first, then Gemini AI)
        title = extract_movie_title(raw_lower)
        
        if not title:
            # Use Gemini to intelligently extract movie name from any query
            title = await ai_assistant.identify_movie_from_query(raw_message)
        
        if not title:
            # Last resort: clean the query and use it as search term
            title = clean_query(raw_lower)
        
        print(f"CHAT: Extracted title = '{title}'")
        
        if title and len(title) >= 2:
            # Search TMDB for the movie
            movies = await asyncio.to_thread(tmdb.search_movies_tmdb, title)
            
            if movies:
                # Found the movie — get full details
                target = movies[0]
                details = await asyncio.to_thread(tmdb.get_movie_details, target['id'])
                
                # Send to Gemini for intelligent answer
                ai_response = await ai_assistant.smart_movie_answer(
                    raw_message, 
                    details, 
                    history
                )
                
                return {
                    "response": ai_response,
                    "movies": movies[:5],
                    "suggestions": _get_movie_suggestions(details, lang),
                    "intent": "movie_info"
                }
            else:
                # Movie not found on TMDB — still try Gemini with general knowledge
                ai_response = await ai_assistant.smart_movie_answer(raw_message, None, history)
                
                # Also search for similar/related movies
                related = await get_semantic_search_results(title, n=5)
                
                return {
                    "response": ai_response,
                    "movies": related[:5] if related else [],
                    "suggestions": ["Try another movie", "Suggest similar movies", "Trending movies"],
                    "intent": "movie_info"
                }
        
        # If we still have no title, it might be a follow-up question 
        # Check if there's a movie context in conversation history
        if history:
            # Look for the last movie discussed
            last_movie_title = None
            for msg in reversed(history):
                if msg.get('role') == 'assistant':
                    content = msg.get('content', '')
                    bold_match = re.search(r'\*\*(.*?)\*\*', content)
                    if bold_match:
                        last_movie_title = bold_match.group(1)
                        break
            
            if last_movie_title:
                print(f"CHAT: Follow-up detected. Context movie: '{last_movie_title}'")
                movies = await asyncio.to_thread(tmdb.search_movies_tmdb, last_movie_title)
                if movies:
                    details = await asyncio.to_thread(tmdb.get_movie_details, movies[0]['id'])
                    ai_response = await ai_assistant.smart_movie_answer(
                        raw_message, details, history
                    )
                    return {
                        "response": ai_response,
                        "movies": movies[:3],
                        "suggestions": _get_movie_suggestions(details, lang),
                        "intent": "follow_up"
                    }

    # ─────────────────────────────────────
    # 4. GENRE / MOOD-BASED RECOMMENDATION
    # ─────────────────────────────────────
    if intent == "genre":
        detected_genre_id = None
        for kw, gid in GENRE_KEYWORDS.items():
            if kw in raw_lower:
                detected_genre_id = gid
                break
        
        if detected_genre_id:
            movies = await asyncio.to_thread(tmdb.get_movies_by_genre, detected_genre_id)
            genre_name = [k for k, v in GENRE_KEYWORDS.items() if v == detected_genre_id][0].title()
            
            if lang == "hindi":
                ai_response = f"🎬 Ye rahi top **{genre_name}** movies jo aapko zaroor pasand aayengi!"
            elif lang == "marathi":
                ai_response = f"🎬 He top **{genre_name}** movies tumhala nakki awadtil!"
            else:
                ai_response = f"🎬 Here are the top **{genre_name}** movies you'll love!"
            
            for m in movies[:10]:
                m["reason"] = f"Top {genre_name}"
            
            return {
                "response": ai_response,
                "movies": movies[:10],
                "suggestions": [f"More {genre_name}", "Mix genres", "Trending now", "Bollywood hits"],
                "intent": "genre_discovery"
            }

    # ─────────────────────────────────────
    # 5. GENERAL RECOMMENDATION (Catch-all)
    # ─────────────────────────────────────
    cleaned_msg = clean_query(raw_lower)
    
    # Try TMDB search first
    movies = await asyncio.to_thread(tmdb.search_movies_tmdb, cleaned_msg) if cleaned_msg and len(cleaned_msg) >= 2 else []
    
    # If direct search fails, try AI-powered vibe search
    if not movies:
        movies = await get_semantic_search_results(raw_message, n=5)
    
    if movies:
        top = movies[0]
        if lang == "hindi":
            ai_response = f"Aapki pasand ke hisab se, ye movies aapko pasand aa sakti hain! Top pick: **{top['title']}** ⭐"
        elif lang == "marathi":
            ai_response = f"Tumchya pasantinusar, he movies tumhala awadtil! Top pick: **{top['title']}** ⭐"
        else:
            ai_response = f"Based on your query, here are some great picks! Top recommendation: **{top['title']}** ⭐"
        
        for m in movies:
            m["reason"] = "Matches your interest"
        
        return {
            "response": ai_response,
            "movies": movies[:8],
            "suggestions": ["Tell me more about the top pick", "Show more", "Different mood", "Trending"],
            "intent": "recommendation"
        }
    
    # Absolute fallback — show trending
    trending = await asyncio.to_thread(tmdb.get_trending_movies)
    trending = trending[:5] if trending else []
    
    if lang == "hindi":
        fallback_resp = "Abhi ye movies trending mein hain — zaroor dekho! 🔥"
    elif lang == "marathi":
        fallback_resp = "Saddhya he movies trending madhe aahet — nakki bagha! 🔥"
    else:
        fallback_resp = "Here's what's trending right now — check these out! 🔥"
    
    for m in trending:
        m["reason"] = "Trending 🔥"
    
    return {
        "response": fallback_resp,
        "movies": trending,
        "suggestions": QUICK_PROMPTS,
        "intent": "trending_fallback"
    }


def _get_movie_suggestions(details: dict, lang: str) -> list:
    """Generate contextual follow-up suggestions based on movie details."""
    title = details.get('title', '')
    suggestions = []
    
    if lang == "hindi":
        suggestions = [
            f"{title} ka plot batao",
            f"{title} mein hero kaun hai",
            f"Iss jaisi aur movies",
            "Ticket book karo"
        ]
    elif lang == "marathi":
        suggestions = [
            f"{title} chi story sanga",
            f"{title} madhe kaun aahe",
            f"Ashi movies dakhva",
            "Ticket book kara"
        ]
    else:
        suggestions = [
            f"Full plot of {title}",
            f"Cast & crew of {title}",
            f"Movies similar to {title}",
            "Book tickets"
        ]
    
    return suggestions
