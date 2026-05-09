from google import genai
from app.config import settings
import asyncio

# Initialize Gemini Client if API Key is available
if settings.GEMINI_API_KEY:
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
else:
    client = None

async def get_ai_movie_info(query: str, movie_data: dict = None) -> str:
    """
    Use Gemini to answer specific questions about a movie using TMDB data as context.
    """
    if not client:
        return "I need a Gemini API Key to answer detailed questions. Please add it to your .env file."

    # Contextual prompt
    context = ""
    if movie_data:
        context = f"""
        Movie Details:
        Title: {movie_data.get('title')}
        Release Date: {movie_data.get('release_date')}
        Budget: ${movie_data.get('budget', 0):,}
        Revenue: ${movie_data.get('revenue', 0):,}
        Status: {movie_data.get('status')}
        Tagline: {movie_data.get('tagline')}
        Genres: {', '.join(movie_data.get('genres', []))}
        Cast: {', '.join([f"{c['name']} as {c['character']}" for c in movie_data.get('cast', [])])}
        Overview: {movie_data.get('overview')}
        """

    prompt = f"""
    You are MovieMind AI, an expert cinema assistant. 
    Use the following movie context to answer the user's question accurately. 
    If the information is not in the context, use your own knowledge but specify if it's general knowledge.
    Keep the tone helpful and cinematic. Answer in the language of the query (Hinglish/Hindi/English/Marathi).

    Context:
    {context}

    User Question: {query}
    """

    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Error connecting to Gemini: {str(e)}"

import requests

def search_nearby_theaters(location: str):
    """
    Find nearby theaters and showtimes using SerpApi.
    """
    if not settings.SERP_API_KEY:
        return "I need a SerpApi Key to find nearby theaters. Please add it to your .env file."
    
    params = {
        "engine": "google",
        "q": f"movies near {location}",
        "api_key": settings.SERP_API_KEY,
        "hl": "hi", # Hindi results
        "gl": "in"  # India region
    }

    try:
        response = requests.get("https://serpapi.com/search", params=params)
        data = response.json()
        
        knowledge_graph = data.get("knowledge_graph", {})
        theaters = data.get("local_results", [])
        
        if not theaters:
            return f"Mujhe {location} ke paas koi theaters nahi mile. Kya aapne location permissions di hain?"

        resp_text = f"Aapke paas ye theaters available hain:\n\n"
        for t in theaters[:5]:
            name = t.get("title")
            rating = t.get("rating", "No rating")
            address = t.get("address", "Address not available")
            resp_text += f"🎬 **{name}** ({rating}⭐)\n📍 {address}\n\n"
            
        resp_text += "Aap inke showtimes Google ya BookMyShow par check kar sakte hain!"
        return resp_text

    except Exception as e:
        return f"Error connecting to SerpApi: {str(e)}"

async def get_movie_suggestions_by_vibe(query: str) -> list:
    """
    Use Gemini to extract movie titles from a natural language 'vibe' or query.
    Returns a list of movie titles.
    """
    if not client:
        return []

    prompt = f"""
    The user is looking for movies with this vibe: "{query}"
    Suggest 5-8 real movie titles that match this description perfectly.
    Return ONLY the titles as a comma-separated list. No numbering, no intros, no descriptions.
    Example: Inception, Interstellar, The Matrix, Shutter Island
    """

    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        titles = [t.strip() for t in response.text.split(",") if t.strip()]
        return titles
    except:
        return []
