"""
Chat Route — MovieMind AI Chatbot endpoint.
Handles all user interactions: movie Q&A, recommendations, theater booking.
Uses Gemini AI for intelligent responses with TMDB data as context.
"""
from fastapi import APIRouter
from app.services.recommender import get_semantic_search_results
from app.services import tmdb, ai_assistant
from app.services.offers import format_offers_response, get_bms_deep_link, get_paytm_deep_link
from app.services.weather import get_weather_context, format_weather_chat_response
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
    "na", "yaar", "bhai", "please", "pls", "karo", "de", "dedo",
    "strory", "stroy", "snga", "sanga", "chi", "baddal", "kadhi", "aahe"
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
    # Marathi patterns (Improved for slang and typos)
    r"(.*?)(?:\s+chi\s+(?:story|katha|kahani|mahitii|mahiti|acting|role|strory|stroy|snga|sanga))",
    r"(.*?)(?:\s+baddal\s+(?:sanga|mahitii|mahiti|snga))",
    r"(.*?)(?:\s+kadhi\s+(?:aali|ali|suri\s+zhali|release\s+zhali))",
    r"(?:story|sanga|snga|mahitii|mahiti|katha|kahani|strory|stroy)\s+(.*?)(?:\s+chi)?$",
    r"(.*?)\s+chi\s+(?:story|sanga|snga|mahitii|mahiti|katha|kahani|strory|stroy)",
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
    for filler in sorted(ENGLISH_FILLERS, key=len, reverse=True):
        q = q.replace(filler, " ")
    words = q.split()
    cleaned = [w for w in words if w not in HINDI_FILLERS]
    result = re.sub(r'\s+', ' ', " ".join(cleaned)).strip()
    return result


def detect_intent(query: str) -> str:
    """Detect the user's intent from their query."""
    q = query.lower()
    greet_words = ["hi", "hello", "hey", "hola", "namaste", "namaskar", "sup", "yo"]
    if any(q.strip() == g or q.startswith(g + " ") or q.startswith(g + ",") for g in greet_words):
        if len(q.split()) <= 4:
            return "greeting"

    offer_words = ["offer", "discount", "coupon", "deal", "cheap", "sasta", "saving",
                   "bank offer", "icici", "sbi", "hdfc", "paytm offer", "cashback",
                   "price", "kitne ka", "kitna ticket", "ticket price", "rate"]
    if any(w in q for w in offer_words):
        return "offers"

    weather_words = ["mausam", "barish", "baarish", "rain", "weather", "garmi", "sardi",
                     "hot", "cold", "aaj kaisa", "rainy day", "mood movie", "aaj kya"]
    if any(w in q for w in weather_words):
        return "weather_recommend"
    
    theater_words = ["theater", "theatre", "cinema", "showtime", "show time", "ticket",
                     "bookmyshow", "book ticket", "booking", "screen", "multiplex",
                     "pvr", "inox", "cinepolis", "kuthe", "lavlay", "chal rha", "kab se",
                     "kab hai", "kab aayegi", "dekh sakte", "available hai"]
    if any(w in q for w in theater_words):
        return "theater"
    
    movie_question_triggers = [
        "tell me", "what is", "about", "movie", "film", "kya", "kaun", "kab", "kaisa", "kaisi",
        "story", "plot", "cast", "hero", "heroine", "director", "rating", "review", "paisa", "kamaya",
        "sanga", "batao", "dikhao", "dakhva", "bhari", "acha", "achhi", "suggest", "recommend",
        "who", "when", "how", "where", "can you", "please", "help"
    ]
    if any(t in q for t in movie_question_triggers):
        return "movie_chat"
    return "movie_chat"


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
    raw_message = payload.get("message", "").strip()
    raw_lower = raw_message.lower()
    history = payload.get("history", [])
    
    try:
        # Detect intent and language
        intent = detect_intent(raw_lower)
        lang = detect_language(raw_lower)
        print(f"CHAT: Query='{raw_message}' | Intent={intent} | Lang={lang}")

        # 1. GREETING
        if intent == "greeting":
            if lang == "marathi":
                resp = "Namaskar! 🎬 Me tumcha MovieMind AI aahe. Tumhala kontyahi movie baddal mahiti pahije? Nahi tar mood sanga, mi movie suggest karto!"
            elif lang == "hindi":
                resp = "Namaste! 🎬 Main aapka MovieMind AI hoon. Kisi bhi movie ke baare mein pucho — ya mood batao, main perfect movie dhundh dunga!"
            else:
                resp = random.choice(GREETINGS)
            return {"response": resp, "movies": [], "suggestions": QUICK_PROMPTS, "intent": "greeting"}

        # 2. OFFERS / PRICE / DISCOUNT
        if intent == "offers":
            # Extract city from query
            city = _extract_city(raw_lower) or "Pune"
            movie_name = _extract_movie_from_history(history)
            resp = format_offers_response(city, movie_name)
            return {
                "response": resp,
                "movies": [],
                "suggestions": [
                    f"Showtimes in {city}",
                    "Best theaters near me",
                    "Theater vibe analysis"
                ],
                "intent": "offers"
            }

        # 3. WEATHER-BASED RECOMMENDATION
        if intent == "weather_recommend":
            city = _extract_city(raw_lower) or "Mumbai"
            weather = get_weather_context(city)
            weather_msg = format_weather_chat_response(weather)

            genre_ids = weather.get("genres", [35, 28, 18])
            movies = []
            for gid in genre_ids[:2]:
                try:
                    genre_movies = tmdb.get_movies_by_genre(gid, page=1)
                    movies.extend(genre_movies[:3])
                except Exception:
                    pass

            if not weather_msg:
                weather_msg = "🎬 Perfect movie time! Yeh movies try karo:"

            return {
                "response": weather_msg,
                "movies": movies[:6],
                "suggestions": [
                    f"Showtimes in {city}",
                    f"Offers in {city}",
                    "Best thriller movies"
                ],
                "intent": "weather_recommend",
                "weather": {
                    "city": weather.get("city", city),
                    "condition": weather.get("condition", ""),
                    "emoji": weather.get("emoji", "🎬")
                }
            }

        # 4. THEATER / TICKET BOOKING
        if intent == "theater":
            city = _extract_city(raw_lower) or "Pune"
            movie_name = _extract_movie_from_query(raw_lower) or _extract_movie_from_history(history)
            resp = ai_assistant.search_nearby_theaters(city, movie_name)

            bms_link = get_bms_deep_link(city, movie_name)
            paytm_link = get_paytm_deep_link(city)

            return {
                "response": resp,
                "movies": [],
                "suggestions": [
                    f"Offers in {city}",
                    f"Theater vibe in {city}",
                    "Group booking help"
                ],
                "intent": "theater_search",
                "booking": {
                    "city": city,
                    "movie": movie_name,
                    "bms_link": bms_link,
                    "paytm_link": paytm_link,
                }
            }

        # 3. MOVIE CHAT (PHASE 2: KNOWLEDGE AUGMENTED)
        if intent == "movie_chat":
            # get_semantic_search_results already performs Knowledge Augmentation (fetches details for top 3)
            movies = await get_semantic_search_results(raw_message, n=5)
            
            # Pass all movies (with their rich metadata) to Gemini
            ai_response = await ai_assistant.smart_movie_answer(raw_message, movies, history)
            
            if ("database" in ai_response or "longer than usual" in ai_response) and movies:
                top_title = movies[0].get('title', 'this movie')
                if lang == "hindi":
                    ai_response = f"Mujhe **{top_title}** ke baare mein ye jaankari mili hai. Kya aap iske baare mein aur jaanna chahte hain?"
                elif lang == "marathi":
                    ai_response = f"Mala **{top_title}** baddal hi mahiti milali aahe. Tumhala azun kai janun ghyaycha aahe ka?"
                else:
                    ai_response = f"I found some info about **{top_title}**. Would you like to know more about it?"

            return {
                "response": ai_response,
                "movies": movies[:8],
                "suggestions": _get_movie_suggestions(movies[0], lang) if movies else QUICK_PROMPTS,
                "intent": "movie_chat"
            }

    except Exception as e:
        print(f"CHAT_GLOBAL_ERROR: {e}")
        import traceback
        traceback.print_exc()
        
        # Determine fallback message
        fallback_msg = "I'm having a bit of trouble reaching my AI brain. But here's what I found in the database!"
        if lang == "hindi":
            fallback_msg = "Maaf kijiye, abhi servers par thoda load hai. Mujhe ye movies mili hain:"
        elif lang == "marathi":
            fallback_msg = "Kshamasva, server var thoda load aahe. Mala ya movies milalya aahet:"
            
        # Extract movies from locals if they exist
        found_movies = locals().get('movies', [])
        
        return {
            "response": fallback_msg, 
            "movies": found_movies[:8], 
            "suggestions": QUICK_PROMPTS, 
            "intent": "error_fallback"
        }


def _extract_city(query: str) -> str:
    """Extract Indian city name from a query string."""
    INDIAN_CITIES = [
        "mumbai", "delhi", "bangalore", "bengaluru", "hyderabad", "chennai",
        "kolkata", "pune", "ahmedabad", "jaipur", "lucknow", "nagpur",
        "surat", "indore", "bhopal", "patna", "chandigarh", "kochi", "goa",
        "noida", "gurgaon", "gurugram", "navi mumbai", "thane",
    ]
    q = query.lower()
    for city in sorted(INDIAN_CITIES, key=len, reverse=True):
        if city in q:
            return city.title()
    # Check for "in <word>" / "near <word>" / "at <word>" pattern
    m = re.search(r'(?:in|near|at|mein)\s+([a-z]+(?:\s[a-z]+)?)', q)
    if m:
        candidate = m.group(1).strip()
        if len(candidate) >= 3 and candidate not in ["the", "my", "me", "a"]:
            return candidate.title()
    return ""


def _extract_movie_from_query(query: str) -> str:
    """Try to extract a movie name embedded in a showtime/booking query."""
    q = query.lower()
    # Patterns like "pushpa 2 ticket", "show for pushpa 2"
    for pattern in [
        r'(?:ticket|show|showtime|booking)\s+(?:for|of)?\s*(.+?)\s*(?:in|near|at|city|theater|$)',
        r'(.+?)\s+(?:ka ticket|ki show|showtime|chal rha|available|book karo)',
    ]:
        m = re.search(pattern, q)
        if m:
            title = m.group(1).strip()
            if 2 <= len(title) <= 40:
                return title.title()
    return ""


def _extract_movie_from_history(history: list) -> Optional[str]:
    """Extract last mentioned movie title from conversation history."""
    for msg in reversed(history or []):
        content = msg.get('content', '')
        match = re.search(r'\*\*([^*]{2,40})\*\*', content)
        if match:
            candidate = match.group(1).strip()
            # Avoid matching things like "Book Now", "Quick Book", etc.
            skip = {"book now", "quick book", "nearby theaters", "showtimes", "all shows"}
            if candidate.lower() not in skip:
                return candidate
    return None


def _get_movie_suggestions(details: dict, lang: str) -> list:
    """Generate contextual follow-up suggestions based on movie details."""
    title = details.get('title', '')
    if lang == "hindi":
        return [f"{title} ka plot batao", f"{title} mein hero kaun hai"]
    elif lang == "marathi":
        return [f"{title} chi story sanga", f"{title} madhe kaun aahe"]
    return [f"Tell me about {title}'s plot", f"Who is in {title}?"]
