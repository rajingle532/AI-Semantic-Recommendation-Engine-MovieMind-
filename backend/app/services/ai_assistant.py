"""
AI Assistant Service — Gemini-powered movie intelligence engine.
Handles all AI-powered responses: movie Q&A, vibe-based search, theater lookup.
"""
from google import genai
from app.config import settings
import asyncio
import requests
import json

# Model configuration — use gemini-2.5-flash (has free tier quota)
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_TIMEOUT = 15  # seconds — prevent server hangs

def get_gemini_client():
    if settings.GEMINI_API_KEY:
        return genai.Client(api_key=settings.GEMINI_API_KEY)
    return None


async def smart_movie_answer(query: str, movie_data: dict = None, conversation_context: list = None) -> str:
    """
    Use Gemini to intelligently answer ANY movie question.
    This is the primary brain — handles everything from "kab bani" to "who directed it".
    """
    client = get_gemini_client()
    if not client:
        return _fallback_movie_info(movie_data) if movie_data else "I need a Gemini API Key to answer detailed questions."

    # Build rich context from TMDB data
    context = ""
    if movie_data:
        # Build watch providers info
        providers_info = ""
        wp = movie_data.get('watch_providers')
        if wp:
            streaming = wp.get('flatrate', [])
            rent = wp.get('rent', [])
            buy = wp.get('buy', [])
            if streaming:
                providers_info += f"Streaming on: {', '.join([p['provider_name'] for p in streaming])}\n"
            if rent:
                providers_info += f"Rent on: {', '.join([p['provider_name'] for p in rent])}\n"
            if buy:
                providers_info += f"Buy on: {', '.join([p['provider_name'] for p in buy])}\n"

        context = f"""
        === MOVIE DATABASE (TMDB) ===
        Title: {movie_data.get('title', 'N/A')}
        Release Date: {movie_data.get('release_date', 'Unknown')}
        Runtime: {movie_data.get('runtime', 'N/A')} minutes
        Rating: {movie_data.get('vote_average', 0)}/10 ({movie_data.get('vote_count', 0)} votes)
        Budget: ${movie_data.get('budget', 0):,}
        Revenue: ${movie_data.get('revenue', 0):,}
        Status: {movie_data.get('status', 'N/A')}
        Tagline: {movie_data.get('tagline', '')}
        Genres: {', '.join(movie_data.get('genres', []))}
        Cast: {', '.join([f"{c['name']} as {c['character']}" for c in movie_data.get('cast', [])])}
        Overview: {movie_data.get('overview', '')}
        {providers_info}
        """

    # Build conversation history for context
    history_text = ""
    if conversation_context:
        recent = conversation_context[-6:]  # Last 3 exchanges
        for msg in recent:
            role = "User" if msg.get('role') == 'user' else "MovieMind"
            history_text += f"{role}: {msg.get('content', '')}\n"

    prompt = f"""You are MovieMind AI — a premium, highly knowledgeable cinema assistant. 
You know EVERYTHING about movies: plot details, behind-the-scenes trivia, box office performance, 
cast stories, director vision, cultural impact, awards, sequels, remakes, and more.

RULES:
1. Answer in the SAME LANGUAGE as the user's question. If they ask in Hindi/Hinglish, reply in Hinglish. 
   If Marathi, reply in Marathi. If English, reply in English.
2. Use the TMDB data provided as your primary source. For anything not in the data, use your own knowledge 
   but be confident — don't say "I think" or "I'm not sure".
3. Keep responses concise but informative (3-6 sentences max for simple questions, longer for "tell me everything").
4. Use emojis sparingly for visual appeal (🎬 ⭐ 🎭 📅 💰).
5. Format key data points with **bold**.
6. If the user asks about ticket booking/watching, mention available streaming platforms from the data.
7. For follow-up questions, use conversation history to understand context.
8. Never say "I couldn't find" — always provide a confident, helpful answer.
9. If a movie has $0 budget/revenue in the data, say the information is not publicly available rather than showing $0.

{f'CONVERSATION HISTORY:{chr(10)}{history_text}' if history_text else ''}

MOVIE DATA:
{context if context else 'No specific movie data available. Answer from your general cinema knowledge.'}

USER QUESTION: {query}

Respond naturally as MovieMind AI:"""

    try:
        # Run Gemini call with timeout to prevent server hangs
        response = await asyncio.wait_for(
            asyncio.to_thread(
                client.models.generate_content,
                model=GEMINI_MODEL,
                contents=prompt
            ),
            timeout=GEMINI_TIMEOUT
        )
        return response.text.strip()
    except asyncio.TimeoutError:
        print(f"GEMINI_TIMEOUT: Request took > {GEMINI_TIMEOUT}s")
        return _fallback_movie_info(movie_data) if movie_data else "I'm taking a bit longer than usual. Here's what I know from my database!"
        # Fallback to high-quality formatted TMDB data if Gemini is down
        if movie_data:
            return _fallback_movie_info(movie_data, query)
        
        return "I'm experiencing a high volume of requests, but I'm still here! Ask me about a specific movie title for the best results."


async def get_ai_movie_info(query: str, movie_data: dict = None) -> str:
    """
    Legacy wrapper — now routes to smart_movie_answer.
    """
    return await smart_movie_answer(query, movie_data)


def _fallback_movie_info(movie_data: dict, query: str = "") -> str:
    """Generate a rich, structured response from TMDB data when Gemini is unavailable."""
    if not movie_data:
        return "I couldn't find exact details for that query, but here are some popular movies you might like!"
    
    title = movie_data.get('title', 'Unknown')
    overview = movie_data.get('overview', '')
    release = movie_data.get('release_date', 'Unknown')
    rating = movie_data.get('vote_average', 0)
    genres = ', '.join(movie_data.get('genres', [])) if isinstance(movie_data.get('genres'), list) else 'Movie'
    cast_list = movie_data.get('cast', [])
    cast_names = ', '.join([c['name'] for c in cast_list[:5]]) if cast_list else 'N/A'
    runtime = movie_data.get('runtime', 'N/A')
    
    # Structure a natural sounding response even without AI
    response = f"🎬 **{title}** ({release[:4]})\n\n"
    response += f"⭐ **Rating:** {rating}/10\n"
    response += f"🎭 **Cast:** {cast_names}\n"
    response += f"🕒 **Runtime:** {runtime} min\n\n"
    response += f"📝 **Plot:** {overview}\n\n"
    
    # Add a friendly note if it was a rate limit fallback
    response += "_Note: Detailed AI analysis is currently limited due to high traffic, but I've fetched the core facts for you!_"
    
    return response
    revenue = movie_data.get('revenue', 0)
    
    response = f"🎬 **{title}**\n\n"
    response += f"📅 Release: {release}\n"
    response += f"⭐ Rating: {rating}/10\n"
    if runtime and runtime != 'N/A':
        response += f"⏱️ Runtime: {runtime} min\n"
    response += f"🎭 Genres: {genres}\n"
    response += f"🌟 Cast: {cast_names}\n"
    if budget and budget > 0:
        response += f"💰 Budget: ${budget:,}\n"
    if revenue and revenue > 0:
        response += f"📊 Revenue: ${revenue:,}\n"
    response += f"\n📖 {overview[:300]}{'...' if len(overview) > 300 else ''}"
    
    return response


def search_nearby_theaters(location: str, movie_name: str = None):
    """
    Find nearby theaters and showtimes.
    Uses SerpApi when available, otherwise provides BookMyShow/Paytm links.
    """
    # Always provide booking links
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

            response = requests.get("https://serpapi.com/search", params=params, timeout=3.0)
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
    
    # Fallback — always give useful booking links
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
    """
    Use Gemini to extract movie titles from a natural language 'vibe' or query.
    Returns a list of movie titles.
    """
    client = get_gemini_client()
    if not client:
        return []

    prompt = f"""The user is looking for movies with this vibe: "{query}"
Suggest 5-8 real movie titles that match this description perfectly.
Include both Bollywood and Hollywood movies if relevant.
Return ONLY the titles as a comma-separated list. No numbering, no intros, no descriptions.
Example: Inception, Interstellar, The Matrix, Shutter Island"""

    try:
        response = await asyncio.wait_for(
            asyncio.to_thread(
                client.models.generate_content,
                model=GEMINI_MODEL,
                contents=prompt
            ),
            timeout=GEMINI_TIMEOUT
        )
        titles = [t.strip() for t in response.text.split(",") if t.strip()]
        return titles
    except asyncio.TimeoutError:
        print(f"GEMINI_VIBE_TIMEOUT")
        return []
    except Exception as e:
        print(f"GEMINI_VIBE_ERROR: {str(e)[:100]}")
        return []


async def identify_movie_from_query(query: str) -> str:
    """
    Use Gemini to extract the movie name from ANY natural language query.
    Handles Hindi, Hinglish, Marathi, and English queries.
    """
    client = get_gemini_client()
    if not client:
        return ""

    prompt = f"""Extract the MOVIE TITLE from this user query. The user might be asking in English, Hindi, Hinglish, or Marathi.

Examples:
- "tell me about the movie dhurandhar" → Dhurandhar
- "pushpa 2 kab aayi thi" → Pushpa 2
- "who is the hero of RRR" → RRR
- "inception ka plot kya hai" → Inception
- "dangal mein kaun hai" → Dangal
- "3 idiots movie batao" → 3 Idiots
- "Inception baddal sanga" → Inception
- "suggest action movies" → NONE (this is a genre request, not a specific movie)
- "romantic movies dikhao" → NONE

If the query is about a GENRE or MOOD (not a specific movie), return NONE.
Return ONLY the movie title, nothing else. Just the title or NONE."""

    try:
        response = await asyncio.wait_for(
            asyncio.to_thread(
                client.models.generate_content,
                model=GEMINI_MODEL,
                contents=f"{prompt}\n\nQuery: {query}"
            ),
            timeout=GEMINI_TIMEOUT
        )
        result = response.text.strip()
        if result.upper() == "NONE" or len(result) > 100:
            return ""
        return result
    except asyncio.TimeoutError:
        print(f"GEMINI_IDENTIFY_TIMEOUT")
        return ""
    except Exception as e:
        print(f"GEMINI_IDENTIFY_ERROR: {str(e)[:100]}")
        return ""
