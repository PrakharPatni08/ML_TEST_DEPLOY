from pymongo import MongoClient
from config.settings import SOURCE_MONGO_URI, SOURCE_DB

try:
    client = MongoClient(SOURCE_MONGO_URI, serverSelectionTimeoutMS=3000)
    db = client[SOURCE_DB]
    # Try to get server info
    client.server_info()
    print("Source DB connected successfully!")
except Exception as e:
    print(f"Source DB connection failed: {e}")