"""
AI Assistant Service — Gemini-powered movie intelligence engine.
Handles all AI-powered responses: movie Q&A, vibe-based search, theater lookup.
"""
from google import genai
from app.config import settings
import asyncio
import requests
import json
import time

# Model configuration — use gemini-2.5-flash (state-of-the-art for 2026)
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_TIMEOUT = 15  # seconds — prevent server hangs

# Initialize Gemini Client if API Key is available
if settings.GEMINI_API_KEY:
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
else:
    client = None

# Circuit Breaker state
_circuit_open = False
_last_failure_time = 0
_failure_count = 0
CIRCUIT_RECOVERY_TIME = 300 # 5 minutes


async def get_ai_response(prompt: str, timeout: int = GEMINI_TIMEOUT) -> str:
    """Exported helper to call Gemini with circuit breaker."""
    return await _call_gemini_with_circuit_breaker(prompt, timeout)


async def _call_gemini_with_circuit_breaker(prompt: str, timeout: int = GEMINI_TIMEOUT) -> str:
    """
    Helper to call Gemini API with Circuit Breaker protection.
    Ensures Phase 3 requirements: handle rate limits (429) gracefully.
    """
    global _circuit_open, _last_failure_time, _failure_count
    
    if _circuit_open:
        if time.time() - _last_failure_time > CIRCUIT_RECOVERY_TIME:
            print("GEMINI_CIRCUIT: Attempting recovery...")
            _circuit_open = False
            _failure_count = 0
        else:
            # Circuit is open, return empty to trigger fallbacks immediately
            return ""

    if not client:
        return ""

    try:
        response = await asyncio.wait_for(
            client.aio.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt
            ),
            timeout=timeout
        )
        # Success: reset failure count
        _failure_count = 0
        return response.text.strip()
    except Exception as e:
        error_msg = str(e)
        _failure_count += 1
        print(f"GEMINI_ERROR ({_failure_count}): {error_msg[:100]}")
        
        # If repeated failures or specific rate limit (429), open the circuit
        if _failure_count >= 3 or "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            print("GEMINI_CIRCUIT: Opening circuit.")
            _circuit_open = True
            _last_failure_time = time.time()
        return ""


async def smart_movie_answer(query: str, movies: list = None, conversation_context: list = None) -> str:
    """
    Use Gemini to intelligently answer ANY movie question.
    Can handle single movie details or a list of search results.
    """
    # Build rich context from multiple movies if provided
    context = ""
    if movies:
        context = "=== MOVIE DATABASE (TMDB) ===\n"
        for i, movie in enumerate(movies[:3]): 
            providers_info = ""
            wp = movie.get('watch_providers')
            if wp:
                streaming = wp.get('flatrate', [])
                if streaming:
                    providers_info = f"Streaming: {', '.join([p['provider_name'] for p in streaming])}"

            context += f"""
MOVIE #{i+1}: {movie.get('title', 'N/A')}
- Release: {movie.get('release_date', 'Unknown')}
- Rating: {movie.get('vote_average', 0)}/10
- Cast: {', '.join([f"{c['name']} as {c['character']}" for c in movie.get('cast', [])[:5]])}
- Overview: {movie.get('overview', '')[:500]}
- {providers_info}
"""
    
    # Build conversation history for context
    history_text = ""
    if conversation_context:
        recent = conversation_context[-6:]  # Last 3 exchanges
        for msg in recent:
            role = "User" if msg.get('role') == 'user' else "MovieMind"
            history_text += f"{role}: {msg.get('content', '')}\n"

    prompt = f"""You are MovieMind AI — a premium cinema assistant.
Answer in the SAME LANGUAGE as the user's question.
Use the TMDB data provided as your primary source.
Keep responses concise (3-6 sentences).
Use emojis (🎬 ⭐). Format with **bold**.

{f'CONVERSATION HISTORY:{chr(10)}{history_text}' if history_text else ''}

MOVIE DATA FROM DATABASE:
{context if context else 'No specific movie data available.'}

USER QUESTION: {query}

Respond naturally as MovieMind AI:"""
    
    response = await _call_gemini_with_circuit_breaker(prompt)
    if response:
        return response
        
    # Fallback to local data formatting if Gemini fails/rate-limited
    return _fallback_movie_info(movies[0] if movies else None) if movies else "I'm focusing on my database right now. How else can I help?"


async def get_ai_movie_info(query: str, movie_data: dict = None) -> str:
    """Legacy wrapper — now routes to smart_movie_answer."""
    return await smart_movie_answer(query, [movie_data] if movie_data else None)


def _fallback_movie_info(movie_data: dict) -> str:
    """Generate a formatted response from TMDB data when Gemini is unavailable."""
    if not movie_data:
        return "I'm having trouble reaching my AI brain, but I can still search for movies by title!"
    
    title = movie_data.get('title', 'Unknown')
    overview = movie_data.get('overview', '')
    release = movie_data.get('release_date', 'Unknown')
    rating = movie_data.get('vote_average', 0)
    genres = ', '.join(movie_data.get('genres', []))
    cast_list = movie_data.get('cast', [])
    cast_names = ', '.join([c['name'] for c in cast_list[:5]]) if cast_list else 'N/A'
    
    response = f"🎬 **{title}**\n\n"
    response += f"📅 Release: {release}\n"
    response += f"⭐ Rating: {rating}/10\n"
    response += f"🎭 Genres: {genres}\n"
    response += f"🌟 Cast: {cast_names}\n"
    response += f"\n📖 {overview[:300]}..."
    
    return response


def search_nearby_theaters(location: str, movie_name: str = None):
    """Find nearby theaters and showtimes."""
    booking_links = _get_booking_links(location, movie_name)
    
    if settings.SERP_API_KEY:
        try:
            search_query = f"movie theaters near {location}"
            if movie_name:
                search_query = f"{movie_name} showtimes near {location}"
            
            params = {
                "engine": "google",
                "q": search_query,
                "api_key": settings.SERP_API_KEY,
                "hl": "en",
                "gl": "in"
            }

            response = requests.get("https://serpapi.com/search", params=params, timeout=10)
            data = response.json()
            theaters = data.get("local_results", [])
            
            if theaters:
                resp_text = "🎬 **Nearby Theaters:**\n\n"
                for t in theaters[:5]:
                    name = t.get("title", "Unknown")
                    rating = t.get("rating", "N/A")
                    address = t.get("address", "")
                    resp_text += f"🏛️ **{name}** ({rating}⭐)\n📍 {address}\n\n"
                resp_text += booking_links
                return resp_text
        except Exception as e:
            print(f"SERP_ERROR: {e}")
    
    return f"🎫 **Book Tickets Online:**\n\n{booking_links}"


def _get_booking_links(location: str, movie_name: str = None) -> str:
    """Generate BookMyShow and Paytm Movies booking links."""
    bms_query = movie_name or "movies"
    city = location.replace(" ", "-").lower() if location != "me" else "pune"
    
    links = f"🔗 **Quick Booking Links:**\n"
    links += f"• [BookMyShow](https://in.bookmyshow.com/explore/movies-{city})\n"
    links += f"• [Paytm Movies](https://paytm.com/movies/{city})\n"
    links += f"• [Google Movies](https://www.google.com/search?q={bms_query.replace(' ', '+')}+tickets+{city})\n"
    return links


async def get_movie_suggestions_by_vibe(query: str) -> list:
    """Extract movie titles from vibe using Gemini."""
    prompt = f"Vibe: {query}. Suggest 5-8 real movies. CSV ONLY. Example: Inception, Interstellar"
    response = await _call_gemini_with_circuit_breaker(prompt)
    if not response:
        return []
    return [t.strip() for t in response.split(",") if t.strip()]


async def identify_movie_from_query(query: str) -> str:
    """Extract movie title from query using Gemini."""
    prompt = f"Extract movie title from: {query}. If genre/mood, return NONE. Title or NONE only."
    response = await _call_gemini_with_circuit_breaker(prompt)
    if not response or response.upper() == "NONE":
        return ""
    return response
