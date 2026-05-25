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


def search_nearby_theaters(location: str, movie_name: str = None) -> str:
    """
    Smart theater & showtime search.
    - Phase 1: Try SerpApi google_showtimes engine (rich data)
    - Phase 2: Fallback to google local_results engine
    - Always: Append BookMyShow deep link + smart offers
    """
    from app.services.offers import format_offers_response, get_bms_deep_link, get_paytm_deep_link

    city = location.strip() if location and location != "me" else "Pune"
    bms_link = get_bms_deep_link(city, movie_name)
    paytm_link = get_paytm_deep_link(city)
    google_link = f"https://www.google.com/search?q={(movie_name or 'movies').replace(' ', '+')}+showtimes+{city.replace(' ', '+')}"

    if not settings.SERP_API_KEY:
        return _fallback_booking_response(city, movie_name, bms_link, paytm_link)

    # ── Phase 1: Try google_showtimes engine (best data) ─────────────────
    try:
        showtime_params = {
            "engine": "google_showtimes",
            "q": f"{movie_name or 'movies'} in {city}",
            "api_key": settings.SERP_API_KEY,
            "hl": "en",
            "gl": "in",
            "location": city + ", India"
        }
        st_resp = requests.get("https://serpapi.com/search", params=showtime_params, timeout=10)
        st_data = st_resp.json()
        showtimes = st_data.get("showtimes", [])

        if showtimes:
            return _format_showtimes_response(showtimes, movie_name, city, bms_link, paytm_link)

    except Exception as e:
        print(f"SERP_SHOWTIMES_ERROR: {e}")

    # ── Phase 2: Fallback to google local_results (theater list) ─────────
    try:
        search_query = f"{movie_name} showtimes near {city}" if movie_name else f"movie theaters near {city}"
        local_params = {
            "engine": "google",
            "q": search_query,
            "api_key": settings.SERP_API_KEY,
            "hl": "en",
            "gl": "in"
        }
        local_resp = requests.get("https://serpapi.com/search", params=local_params, timeout=10)
        local_data = local_resp.json()
        theaters = local_data.get("local_results", [])

        if theaters:
            return _format_local_theaters_response(theaters, movie_name, city, bms_link, paytm_link)

    except Exception as e:
        print(f"SERP_LOCAL_ERROR: {e}")

    # ── Phase 3: Static fallback ─────────────────────────────────────────
    return _fallback_booking_response(city, movie_name, bms_link, paytm_link)


def _format_showtimes_response(showtimes: list, movie_name: str, city: str,
                               bms_link: str, paytm_link: str) -> str:
    """Format SerpApi google_showtimes data into a premium chat response."""
    title = movie_name or "Movies"
    resp = f"🎬 **{title} — Showtimes near {city.title()}:**\n\n"

    shown = 0
    for day_block in showtimes[:2]:                     # up to 2 days
        day_label = day_block.get("day", "Today")
        for theater in day_block.get("theaters", [])[:5]:   # up to 5 theaters
            t_name = theater.get("name", "Theater")
            t_link = theater.get("link", bms_link)
            shows = theater.get("showing", [])

            if not shows:
                continue

            resp += f"🏛️ **{t_name}**\n"

            for show in shows[:1]:   # first showing variant (e.g., Hindi 2D)
                show_type = show.get("type", "")
                times = show.get("time", [])

                # Availability detection
                available_times = []
                filling_times = []
                sold_out_times = []
                for t in times:
                    t_str = t.get("time", "")
                    seats = t.get("seat_status", "").lower() if isinstance(t, dict) else ""
                    if "sold" in seats or "houseful" in seats:
                        sold_out_times.append(t_str)
                    elif "fast" in seats or "filling" in seats:
                        filling_times.append(f"{t_str} 🔴")
                    else:
                        available_times.append(f"{t_str} 🟢")

                all_display = available_times + filling_times + [f"{t} ⚫" for t in sold_out_times]
                if all_display:
                    if show_type:
                        resp += f"   🎭 {show_type}\n"
                    resp += f"   ⏰ {' | '.join(all_display[:6])}\n"

            resp += f"   🔗 [Book Now]({t_link})\n\n"
            shown += 1
            if shown >= 5:
                break
        if shown >= 5:
            break

    resp += f"\n💡 *🟢 Available  🔴 Filling Fast  ⚫ Sold Out*\n\n"
    resp += f"📱 **Quick Book:** [BookMyShow]({bms_link}) | [Paytm Movies]({paytm_link})"
    return resp


def _format_local_theaters_response(theaters: list, movie_name: str, city: str,
                                    bms_link: str, paytm_link: str) -> str:
    """Format google local_results theater list into chat response."""
    title = movie_name or "Movies"
    resp = f"🎬 **{title} — Theaters near {city.title()}:**\n\n"

    for t in theaters[:5]:
        name = t.get("title", "Unknown Theater")
        rating = t.get("rating", "")
        address = t.get("address", "")
        rating_str = f" ⭐ {rating}" if rating else ""

        # Generate BMS deeplink per theater
        theater_bms = get_theater_bms_link(name, city, movie_name)
        resp += f"🏛️ **{name}**{rating_str}\n"
        if address:
            resp += f"   📍 {address}\n"
        resp += f"   🎟️ Availability: Check on [BookMyShow]({theater_bms})\n"
        resp += f"   🔗 [Book Tickets]({theater_bms})\n\n"

    resp += f"📱 **All Shows:** [BookMyShow {city.title()}]({bms_link}) | [Paytm Movies]({paytm_link})"
    return resp


def _fallback_booking_response(city: str, movie_name: str, bms_link: str, paytm_link: str) -> str:
    """Static fallback response when all APIs fail."""
    title = movie_name or "Movies"
    city_t = city.title()
    google_link = f"https://www.google.com/search?q={title.replace(' ', '+')}+showtimes+{city.replace(' ', '+')}"

    resp = f"🎬 **{title} in {city_t}:**\n\n"
    resp += f"Abhi live showtime data nahi hai, lekin yahan se seedha book kar sakte ho:\n\n"
    resp += f"🔗 [BookMyShow — {city_t}]({bms_link})\n"
    resp += f"🔗 [Paytm Movies — {city_t}]({paytm_link})\n"
    resp += f"🔗 [Google Showtimes]({google_link})\n"
    return resp


def get_theater_bms_link(theater_name: str, city: str, movie_name: str = None) -> str:
    """Generate a theater-specific BookMyShow search link."""
    from app.services.offers import get_city_slug
    slug = get_city_slug(city)
    if movie_name:
        clean_movie = movie_name.lower().replace(" ", "-").replace(":", "").replace("'", "")
        return f"https://in.bookmyshow.com/buytickets/{clean_movie}/{slug}"
    clean_theater = theater_name.lower().replace(" ", "+")
    return f"https://in.bookmyshow.com/explore/movies-{slug}?q={clean_theater}"


def analyze_theater_vibe(theaters: list) -> str:
    """Use Gemini to classify theaters by vibe from their review snippets."""
    if not theaters:
        return ""
    theater_texts = []
    for t in theaters[:5]:
        name = t.get("title", "")
        reviews = t.get("reviews", [])
        snippet = reviews[0].get("snippet", "") if reviews else t.get("description", "")
        if name and snippet:
            theater_texts.append(f"{name}: {snippet[:150]}")

    if not theater_texts:
        return ""

    # Return raw data for Gemini to process (called from chat route)
    return "\n".join(theater_texts)


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


async def get_music_suggestions_for_movie(movie_details: dict) -> list:
    """Suggest Spotify playlists based on movie vibe."""
    title = movie_details.get('title')
    genres = movie_details.get('genres', [])
    overview = movie_details.get('overview', '')
    
    prompt = f"""
    The user liked the movie '{title}' (Genres: {', '.join(genres)}).
    Overview: {overview[:300]}...
    
    Suggest 5 distinct types of Spotify playlists/genres that match the 'vibe' or 'tone' of this movie.
    For each suggestion, provide:
    1. A catchy title (e.g., 'Since you liked the dark tone of {title}...')
    2. A brief description (max 15 words)
    3. A search query to find this on Spotify (e.g., 'dark synth-wave')
    
    Return the response as a JSON list of objects with keys: title, description, query.
    Do not include any other text.
    """
    
    response = await _call_gemini_with_circuit_breaker(prompt)
    if not response:
        # Fallback based on genres
        genres = movie_details.get('genres', [])
        if any(g in genres for g in ['Action', 'Adventure', 'Sci-Fi']):
            return [{"title": "Epic Hero Soundscapes", "description": "Powerful orchestral and synth tracks for a grand adventure.", "query": "Epic Movie Scores"}]
        if any(g in genres for g in ['Horror', 'Thriller', 'Mystery']):
            return [{"title": "Dark Suspense Vibes", "description": "Eerie and atmospheric sounds for a tense night.", "query": "Dark Ambient Movie Music"}]
        if any(g in genres for g in ['Comedy', 'Animation', 'Family']):
            return [{"title": "Feel-Good Cinematic Hits", "description": "Upbeat and joyful melodies to brighten your day.", "query": "Happy Movie Soundtracks"}]
        return [{"title": "Cinematic Essentials", "description": "Classic and modern masterpieces of film music.", "query": "Movie Soundtracks"}]
    
    try:
        # Simple JSON cleaning
        json_str = response.strip()
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()
            
        return json.loads(json_str)
    except:
        return []
