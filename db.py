import os
from pymongo import MongoClient

def get_db():
    MONGO_URI = os.getenv("MONGO_URI")
    if not MONGO_URI:
        raise Exception("MONGO_URI environment variable not set.")
    client = MongoClient(MONGO_URI)
    return client["chatbot"]

def get_users_collection(db):
    return db["users"]
