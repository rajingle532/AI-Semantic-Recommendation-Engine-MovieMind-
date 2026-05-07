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
        ca = certifi.where()
        _client = MongoClient(
            settings.MONGODB_URI, 
            tlsCAFile=ca,
            tlsAllowInvalidCertificates=True,
            serverSelectionTimeoutMS=5000
        )
        _db = _client[settings.DB_NAME]
        print(f"Connected to MongoDB: {settings.DB_NAME}")

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
