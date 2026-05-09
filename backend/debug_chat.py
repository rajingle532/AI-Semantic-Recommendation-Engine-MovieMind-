
import asyncio
import sys
import os

# Add the parent directory to sys.path to import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.routes.chat import chat_response

async def test_error():
    print("Running Internal Chat Test for 'Dhurandhar'...")
    payload = {
        "message": "Dhurandhar movie ki strry batao",
        "history": []
    }
    try:
        response = await chat_response(payload)
        print("Response received successfully!")
        print(f"AI: {response['response']}")
    except Exception as e:
        print(f"CRASH DETECTED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_error())
