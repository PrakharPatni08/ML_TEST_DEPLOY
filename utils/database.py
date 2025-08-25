from pymongo import MongoClient
from utils.preprocessing import clean_text

from config.settings import (
    SOURCE_MONGO_URI, SOURCE_DB, SOURCE_COLLECTION,
    DEST_MONGO_URI, DEST_DB, DEST_COLLECTION
)

def fetch_raw_analysis():
    """
    Fetches all raw_analysis fields from the source MongoDB collection.
    Returns a list of raw transcript strings.
    """
    client = MongoClient(SOURCE_MONGO_URI)
    db = client[SOURCE_DB]
    collection = db[SOURCE_COLLECTION]
    results = collection.find({}, {"raw_analysis": 1, "_id": 0})
    return [doc["raw_analysis"] for doc in results if "raw_analysis" in doc]

def transfer_documents(query=None):
    src_client = MongoClient(SOURCE_MONGO_URI)
    src_db = src_client[SOURCE_DB]
    src_col = src_db[SOURCE_COLLECTION]

    dest_client = MongoClient(DEST_MONGO_URI)
    dest_db = dest_client[DEST_DB]
    dest_col = dest_db[DEST_COLLECTION]

    docs = src_col.find(query or {})
    count = 0
    for doc in docs:
        doc.pop('_id', None)
        if "transcript" in doc:
            doc["transcript"] = clean_text(doc["transcript"])
        dest_col.insert_one(doc)
        count += 1
    return count

def insert_complaint(doc):
    client = MongoClient(DEST_MONGO_URI)
    db = client[DEST_DB]
    collection = db[DEST_COLLECTION]
    result = collection.insert_one(doc)
    return result.inserted_id