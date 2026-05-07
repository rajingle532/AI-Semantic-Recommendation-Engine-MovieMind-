import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load .env from root
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

uri = os.getenv("MONGODB_URI")
print(f"URI: {uri}")

try:
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    db = client.get_database()
    print(f"Connected to DB: {db.name}")
    collections = db.list_collection_names()
    print(f"Collections: {collections}")
except Exception as e:
    print(f"Error: {e}")
