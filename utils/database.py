from pymongo import MongoClient
from utils.preprocessing import clean_text
from config.settings import (
    SOURCE_MONGO_URI, SOURCE_DB, SOURCE_COLLECTION,
    DEST_MONGO_URI, DEST_DB, DEST_COLLECTION
)

def transfer_documents(query=None):
    """
    Transfers documents from the source MongoDB collection to the destination collection.
    Preprocesses the transcript field using clean_text before saving.
    Removes the _id field to avoid duplicate key errors.
    Optionally accepts a query to filter documents.
    Returns the number of documents copied.
    """
    # Connect to source
    src_client = MongoClient(SOURCE_MONGO_URI)
    src_db = src_client[SOURCE_DB]
    src_col = src_db[SOURCE_COLLECTION]

    # Connect to destination
    dest_client = MongoClient(DEST_MONGO_URI)
    dest_db = dest_client[DEST_DB]
    dest_col = dest_db[DEST_COLLECTION]

    # Fetch documents
    docs = src_col.find(query or {})
    count = 0
    for doc in docs:
        doc.pop('_id', None)  # Remove _id to avoid duplicate key error
        if "transcript" in doc:
            doc["transcript"] = clean_text(doc["transcript"])
        dest_col.insert_one(doc)
        count += 1
    return count

def insert_complaint(doc):
    """
    Inserts a complaint document into the destination MongoDB collection.
    Returns the inserted document's ID.
    """
    client = MongoClient(DEST_MONGO_URI)
    db = client[DEST_DB]
    collection = db[DEST_COLLECTION]
    result = collection.insert_one(doc)
    return result.inserted_id