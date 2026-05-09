import asyncio
import os
import sys

# Add current dir to path
sys.path.append(os.getcwd())

from app.services.ai_assistant import get_ai_movie_info

async def test_gemini():
    query = "Who is the lead actor in Inception?"
    movie_context = {
        "title": "Inception",
        "cast": [{"name": "Leonardo DiCaprio", "character": "Cobb"}]
    }
    print("Testing Gemini...")
    response = await get_ai_movie_info(query, movie_context)
    print(f"Gemini Response: {response}")

if __name__ == "__main__":
    asyncio.run(test_gemini())
