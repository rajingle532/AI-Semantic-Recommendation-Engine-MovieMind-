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
        # SSL/TLS is required for Atlas (+srv) but fails on local non-SSL mongo
        is_atlas = "mongodb+srv://" in settings.MONGODB_URI
        
        client_kwargs = {
            "host": settings.MONGODB_URI,
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
