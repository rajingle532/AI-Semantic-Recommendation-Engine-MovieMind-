from google import genai
import os
from app.config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)
print("Available Models:")
for model in client.models.list():
    print(f"- {model.name}")
