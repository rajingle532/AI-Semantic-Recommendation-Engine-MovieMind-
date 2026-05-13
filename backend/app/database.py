"""
Database module — MongoDB connection using PyMongo.
"""
import certifi
from pymongo import MongoClient
from pymongo.database import Database
from app.config import settings

# Global MongoDB client and database instance
_client: MongoClient = None
_db: Database = None


def get_database() -> Database:
    """Get the MongoDB database instance. Creates connection on first call."""
    global _client, _db

    if _db is None:
        # Safety check for empty URI
        uri = settings.MONGODB_URI or "mongodb://localhost:27017/movie_recommender"
        is_atlas = "mongodb+srv://" in uri
        
        client_kwargs = {
            "host": uri,
            "serverSelectionTimeoutMS": 5000
        }
        
        if is_atlas:
            client_kwargs["tlsCAFile"] = certifi.where()
            client_kwargs["tlsAllowInvalidCertificates"] = True
            
        _client = MongoClient(**client_kwargs)
        _db = _client[settings.DB_NAME]
        print(f"Connected to MongoDB: {settings.DB_NAME} (Atlas Mode: {is_atlas})")

    return _db


def get_collection(name: str):
    """Get a MongoDB collection by name."""
    db = get_database()
    return db[name]


def close_database():
    """Close the MongoDB connection."""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        print("MongoDB connection closed")
