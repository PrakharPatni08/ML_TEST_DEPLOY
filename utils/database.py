# from pymongo import MongoClient
# from utils.preprocessing import clean_text

# from config.settings import (
#     SOURCE_MONGO_URI, SOURCE_DB, SOURCE_COLLECTION,
#     DEST_MONGO_URI, DEST_DB, DEST_COLLECTION
# )

# def fetch_raw_analysis():
#     """
#     Fetches all raw_analysis fields from the source MongoDB collection.
#     Returns a list of raw transcript strings.
#     """
#     client = MongoClient(SOURCE_MONGO_URI)
#     db = client[SOURCE_DB]
#     collection = db[SOURCE_COLLECTION]
#     results = collection.find({}, {"raw_analysis": 1, "_id": 0})
#     return [doc["raw_analysis"] for doc in results if "raw_analysis" in doc]

# def transfer_documents(query=None):
#     src_client = MongoClient(SOURCE_MONGO_URI)
#     src_db = src_client[SOURCE_DB]
#     src_col = src_db[SOURCE_COLLECTION]

#     dest_client = MongoClient(DEST_MONGO_URI)
#     dest_db = dest_client[DEST_DB]
#     dest_col = dest_db[DEST_COLLECTION]

#     docs = src_col.find(query or {})
#     count = 0
#     for doc in docs:
#         doc.pop('_id', None)
#         if "transcript" in doc:
#             doc["transcript"] = clean_text(doc["transcript"])
#         dest_col.insert_one(doc)
#         count += 1
#     return count

# def insert_complaint(doc):
#     client = MongoClient(DEST_MONGO_URI)
#     db = client[DEST_DB]
#     collection = db[DEST_COLLECTION]
#     result = collection.insert_one(doc)
#     return result.inserted_id

from pymongo import MongoClient
from utils.preprocessing import clean_text
from utils.logger import get_logger
from datetime import datetime, timedelta  # Add timedelta import

# ...rest of existing code...
from config.settings import (
    SOURCE_MONGO_URI, SOURCE_DB, SOURCE_COLLECTION,
    DEST_MONGO_URI, DEST_DB, DEST_COLLECTION
)

logger = get_logger()

def fetch_raw_analysis():
    """
    Fetches all raw_analysis fields from the source MongoDB collection.
    Returns a list of raw transcript strings.
    """
    client = None
    try:
        client = MongoClient(SOURCE_MONGO_URI)
        db = client[SOURCE_DB]
        collection = db[SOURCE_COLLECTION]
        results = collection.find({}, {"raw_analysis": 1, "_id": 0})
        data = [doc["raw_analysis"] for doc in results if "raw_analysis" in doc]
        logger.info(f"Fetched {len(data)} raw analysis documents")
        return data
    except Exception as e:
        logger.error(f"Error fetching raw analysis: {e}")
        return []
    finally:
        if client:
            client.close()

def fetch_unprocessed_documents(limit=50):
    """
    Fetches unprocessed documents from the source collection.
    Returns a list of documents that haven't been processed yet.
    """
    client = None
    try:
        client = MongoClient(SOURCE_MONGO_URI)
        db = client[SOURCE_DB]
        collection = db[SOURCE_COLLECTION]
        
        # Query for unprocessed documents
        query = {"$or": [{"processed": {"$ne": True}}, {"processed": {"$exists": False}}]}
        documents = list(collection.find(query).limit(limit))
        
        logger.info(f"Found {len(documents)} unprocessed documents")
        return documents
    except Exception as e:
        logger.error(f"Error fetching unprocessed documents: {e}")
        return []
    finally:
        if client:
            client.close()

def transfer_documents(query=None):
    """Transfer documents from source to destination collection"""
    src_client = None
    dest_client = None
    try:
        src_client = MongoClient(SOURCE_MONGO_URI)
        src_db = src_client[SOURCE_DB]
        src_col = src_db[SOURCE_COLLECTION]

        dest_client = MongoClient(DEST_MONGO_URI)
        dest_db = dest_client[DEST_DB]
        dest_col = dest_db[DEST_COLLECTION]

        docs = src_col.find(query or {})
        count = 0
        for doc in docs:
            try:
                # Remove MongoDB ObjectId to avoid conflicts
                doc.pop('_id', None)
                
                # Clean transcript if present
                if "transcript" in doc:
                    doc["transcript"] = clean_text(doc["transcript"])
                
                # Add transfer metadata
                doc["transferred_at"] = datetime.utcnow()
                
                dest_col.insert_one(doc)
                count += 1
                
            except Exception as e:
                logger.error(f"Error transferring individual document: {e}")
                continue
        
        logger.info(f"Successfully transferred {count} documents")
        return count
        
    except Exception as e:
        logger.error(f"Error transferring documents: {e}")
        return 0
    finally:
        if src_client:
            src_client.close()
        if dest_client:
            dest_client.close()

def insert_complaint(doc):
    """Insert a single processed complaint document."""
    client = None
    try:
        client = MongoClient(DEST_MONGO_URI)
        db = client[DEST_DB]
        collection = db[DEST_COLLECTION]
        
        # Add insertion timestamp
        doc["inserted_at"] = datetime.utcnow()
        
        result = collection.insert_one(doc)
        logger.info(f"✅ Inserted processed complaint with ID: {result.inserted_id}")
        return result.inserted_id
        
    except Exception as e:
        logger.error(f"❌ Error inserting complaint: {e}")
        raise e
    finally:
        if client:
            client.close()

def mark_document_processed(document_id, source_client=None):
    """Mark a document as processed in the source collection"""
    client = None
    should_close_client = False
    
    try:
        if source_client is None:
            client = MongoClient(SOURCE_MONGO_URI)
            should_close_client = True
        else:
            client = source_client
            
        db = client[SOURCE_DB]
        collection = db[SOURCE_COLLECTION]
        
        result = collection.update_one(
            {"_id": document_id},
            {"$set": {
                "processed": True, 
                "processed_at": datetime.utcnow(),
                "processing_status": "completed"
            }}
        )
        
        if result.modified_count > 0:
            logger.info(f"✅ Marked document {document_id} as processed")
        else:
            logger.warning(f"⚠️ Document {document_id} was not found or already processed")
            
    except Exception as e:
        logger.error(f"❌ Error marking document as processed: {e}")
    finally:
        if should_close_client and client:
            client.close()

def check_document_exists_in_destination(source_document_id):
    """Check if a document has already been processed and exists in destination"""
    client = None
    try:
        client = MongoClient(DEST_MONGO_URI)
        db = client[DEST_DB]
        collection = db[DEST_COLLECTION]
        
        existing_doc = collection.find_one({"source_document_id": str(source_document_id)})
        return existing_doc is not None
        
    except Exception as e:
        logger.error(f"Error checking document existence: {e}")
        return False
    finally:
        if client:
            client.close()

def get_processing_stats():
    """Get statistics about processed vs unprocessed documents"""
    src_client = None
    dest_client = None
    try:
        # Connect to source database
        src_client = MongoClient(SOURCE_MONGO_URI)
        src_db = src_client[SOURCE_DB]
        src_collection = src_db[SOURCE_COLLECTION]
        
        # Connect to destination database
        dest_client = MongoClient(DEST_MONGO_URI)
        dest_db = dest_client[DEST_DB]
        dest_collection = dest_db[DEST_COLLECTION]
        
        # Count documents
        total_source_docs = src_collection.count_documents({})
        processed_source_docs = src_collection.count_documents({"processed": True})
        unprocessed_source_docs = src_collection.count_documents({
            "$or": [{"processed": {"$ne": True}}, {"processed": {"$exists": False}}]
        })
        total_dest_docs = dest_collection.count_documents({})
        
        stats = {
            "total_source_documents": total_source_docs,
            "processed_source_documents": processed_source_docs,
            "unprocessed_source_documents": unprocessed_source_docs,
            "total_processed_complaints": total_dest_docs,
            "processing_rate": round((processed_source_docs / total_source_docs * 100), 2) if total_source_docs > 0 else 0
        }
        
        logger.info(f"📊 Processing Stats: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Error getting processing stats: {e}")
        return {}
    finally:
        if src_client:
            src_client.close()
        if dest_client:
            dest_client.close()

def bulk_insert_complaints(docs):
    """Insert multiple processed complaint documents in bulk"""
    client = None
    try:
        client = MongoClient(DEST_MONGO_URI)
        db = client[DEST_DB]
        collection = db[DEST_COLLECTION]
        
        # Add insertion timestamp to all documents
        timestamp = datetime.utcnow()
        for doc in docs:
            doc["inserted_at"] = timestamp
        
        result = collection.insert_many(docs)
        logger.info(f"✅ Bulk inserted {len(result.inserted_ids)} processed complaints")
        return result.inserted_ids
        
    except Exception as e:
        logger.error(f"❌ Error bulk inserting complaints: {e}")
        raise e
    finally:
        if client:
            client.close()

def test_database_connections():
    """Test connections to both source and destination databases"""
    connections = {
        "source": False,
        "destination": False,
        "errors": []
    }
    
    # Test source connection
    src_client = None
    try:
        src_client = MongoClient(SOURCE_MONGO_URI, serverSelectionTimeoutMS=5000)
        src_client.admin.command('ping')
        connections["source"] = True
        logger.info("✅ Source database connection successful")
    except Exception as e:
        connections["errors"].append(f"Source DB error: {str(e)}")
        logger.error(f"❌ Source database connection failed: {e}")
    finally:
        if src_client:
            src_client.close()
    
    # Test destination connection
    dest_client = None
    try:
        dest_client = MongoClient(DEST_MONGO_URI, serverSelectionTimeoutMS=5000)
        dest_client.admin.command('ping')
        connections["destination"] = True
        logger.info("✅ Destination database connection successful")
    except Exception as e:
        connections["errors"].append(f"Destination DB error: {str(e)}")
        logger.error(f"❌ Destination database connection failed: {e}")
    finally:
        if dest_client:
            dest_client.close()
    
    return connections

def cleanup_old_processed_flags(days=30):
    """Clean up old processed flags from source collection (optional maintenance)"""
    client = None
    try:
        client = MongoClient(SOURCE_MONGO_URI)
        db = client[SOURCE_DB]
        collection = db[SOURCE_COLLECTION]
        
        # Remove processed flags older than specified days
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        result = collection.update_many(
            {
                "processed": True,
                "processed_at": {"$lt": cutoff_date}
            },
            {
                "$unset": {
                    "processed": "",
                    "processed_at": "",
                    "processing_status": ""
                }
            }
        )
        
        logger.info(f"🧹 Cleaned up processed flags for {result.modified_count} old documents")
        return result.modified_count
        
    except Exception as e:
        logger.error(f"❌ Error cleaning up processed flags: {e}")
        return 0
    finally:
        if client:
            client.close()