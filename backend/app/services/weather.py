"""
Weather Service — OpenWeatherMap free API integration.
Provides context-aware movie genre suggestions based on real-time weather.
"""
import requests
from app.config import settings

WEATHER_API_BASE = "https://api.openweathermap.org/data/2.5/weather"

# Weather condition → best movie genres mapping
WEATHER_GENRE_MAP = {
    "Rain": {
        "emoji": "☔",
        "mood": "cozy indoor",
        "genres": [53, 18, 10749],       # Thriller, Drama, Romance
        "genre_names": ["Thriller", "Drama", "Romance"],
        "message": "Baarish ka mausam hai! Perfect time for a cozy indoor thriller or romance."
    },
    "Thunderstorm": {
        "emoji": "⛈️",
        "mood": "thrilling",
        "genres": [27, 53, 9648],        # Horror, Thriller, Mystery
        "genre_names": ["Horror", "Thriller", "Mystery"],
        "message": "Aandhi-toofan chal raha hai! Perfect time for a spine-chilling horror movie."
    },
    "Snow": {
        "emoji": "❄️",
        "mood": "magical",
        "genres": [14, 10751, 16],       # Fantasy, Family, Animation
        "genre_names": ["Fantasy", "Family", "Animation"],
        "message": "Barf pad rahi hai! Ek magical fantasy ya family movie perfect rahegi."
    },
    "Clear": {
        "emoji": "☀️",
        "mood": "energetic",
        "genres": [28, 12, 35],          # Action, Adventure, Comedy
        "genre_names": ["Action", "Adventure", "Comedy"],
        "message": "Mausam ekdum sahi hai! Action ya Adventure movie enjoy karo."
    },
    "Clouds": {
        "emoji": "☁️",
        "mood": "contemplative",
        "genres": [18, 9648, 80],        # Drama, Mystery, Crime
        "genre_names": ["Drama", "Mystery", "Crime"],
        "message": "Badal chaye hain — ek gripping drama ya mystery try karo!"
    },
    "Haze": {
        "emoji": "🌫️",
        "mood": "mysterious",
        "genres": [9648, 878, 80],       # Mystery, Sci-Fi, Crime
        "genre_names": ["Mystery", "Sci-Fi", "Crime"],
        "message": "Dhundh jaisi mahaul hai — koi dark sci-fi ya mystery film try karo!"
    },
    "Hot": {
        "emoji": "🔥",
        "mood": "intense",
        "genres": [28, 878, 53],         # Action, Sci-Fi, Thriller
        "genre_names": ["Action", "Sci-Fi", "Thriller"],
        "message": "Garmi bahut hai! AC mein baith ke ek high-octane action film dekho."
    },
}

DEFAULT_WEATHER = {
    "emoji": "🎬",
    "mood": "chill",
    "genres": [35, 28, 18],
    "genre_names": ["Comedy", "Action", "Drama"],
    "message": "Perfect movie time! Aaj kya dekhna chahenge?"
}


def get_weather_context(city: str) -> dict:
    """
    Fetch real-time weather for a city and return genre/mood recommendations.
    Falls back gracefully if API key missing or city not found.
    """
    api_key = settings.OPENWEATHER_API_KEY if hasattr(settings, 'OPENWEATHER_API_KEY') else ""

    if not api_key:
        return {"available": False, **DEFAULT_WEATHER}

    try:
        resp = requests.get(
            WEATHER_API_BASE,
            params={"q": city, "appid": api_key, "units": "metric"},
            timeout=5
        )
        if resp.status_code != 200:
            return {"available": False, **DEFAULT_WEATHER}

        data = resp.json()
        condition = data["weather"][0]["main"]   # e.g. "Rain", "Clear"
        temp = data["main"]["temp"]
        description = data["weather"][0]["description"]
        city_name = data.get("name", city)

        # Override for extreme heat
        if temp > 38 and condition == "Clear":
            condition = "Hot"

        weather_info = WEATHER_GENRE_MAP.get(condition, DEFAULT_WEATHER)

        return {
            "available": True,
            "city": city_name,
            "condition": condition,
            "description": description,
            "temp": round(temp),
            **weather_info
        }

    except Exception as e:
        print(f"WEATHER_ERROR: {e}")
        return {"available": False, **DEFAULT_WEATHER}


def format_weather_chat_response(weather: dict, movie_title: str = None) -> str:
    """Generate a natural language weather-aware recommendation message."""
    if not weather.get("available"):
        return ""

    emoji = weather.get("emoji", "🎬")
    city = weather.get("city", "")
    condition = weather.get("condition", "")
    temp = weather.get("temp", "")
    message = weather.get("message", "")
    genres = weather.get("genre_names", [])

    resp = f"{emoji} **{city} mein abhi {condition} ({temp}°C)** hai!\n\n"
    resp += f"{message}\n\n"
    resp += f"🎭 Recommended genres: **{', '.join(genres)}**\n"

    return resp
