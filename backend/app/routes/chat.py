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
    
    theater_words = ["theater", "theatre", "cinema", "showtime", "ticket", "bookmyshow", 
                     "book ticket", "pass ka", "booking", "screen", "multiplex", "pvr", "inox", "kuthe", "lavlay"]
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

        # 2. THEATER / TICKET BOOKING
        if intent == "theater":
            location = "me"
            movie_name = None
            words = raw_lower.split()
            for keyword in ["in", "near", "at"]:
                if keyword in words:
                    idx = words.index(keyword)
                    if idx + 1 < len(words):
                        location = " ".join(words[idx + 1:])
                        break
            if history:
                for msg in reversed(history):
                    if msg.get('role') == 'assistant' and '**' in msg.get('content', ''):
                        bold_match = re.search(r'\*\*(.*?)\*\*', msg['content'])
                        if bold_match:
                            movie_name = bold_match.group(1)
                            break
            resp = ai_assistant.search_nearby_theaters(location, movie_name)
            return {"response": resp, "movies": [], "suggestions": ["Theaters in Mumbai", "Theaters in Pune"], "intent": "theater_search"}

        # 3. MOVIE CHAT (PHASE 1: SEMANTIC-FIRST)
        if intent == "movie_chat":
            movies = await get_semantic_search_results(raw_message, n=5)
            details = None
            if movies:
                target = movies[0]
                details = await asyncio.to_thread(tmdb.get_movie_details, target['id'])
            
            ai_response = await ai_assistant.smart_movie_answer(raw_message, details, history)
            
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
                "suggestions": _get_movie_suggestions(details, lang) if details else QUICK_PROMPTS,
                "intent": "movie_chat"
            }

    except Exception as e:
        print(f"CHAT_GLOBAL_ERROR: {e}")
        import traceback
        traceback.print_exc()
        fallback_msg = "I'm having a bit of trouble reaching my movie database. Please try asking about a specific movie title!"
        if lang == "hindi":
            fallback_msg = "Maaf kijiye, abhi servers par thoda load hai. Kya aap movie ka naam dobara bata sakte hain?"
        elif lang == "marathi":
            fallback_msg = "Kshamasva, server var thoda load aahe. Krupay movie che naav punha sanga."
        return {"response": fallback_msg, "movies": [], "suggestions": QUICK_PROMPTS, "intent": "error_fallback"}


def _get_movie_suggestions(details: dict, lang: str) -> list:
    """Generate contextual follow-up suggestions based on movie details."""
    title = details.get('title', '')
    if lang == "hindi":
        return [f"{title} ka plot batao", f"{title} mein hero kaun hai"]
    elif lang == "marathi":
        return [f"{title} chi story sanga", f"{title} madhe kaun aahe"]
    return [f"Tell me about {title}'s plot", f"Who is in {title}?"]
