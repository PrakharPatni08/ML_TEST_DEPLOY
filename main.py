# import os
# from fastapi import FastAPI, HTTPException, Body
# from pydantic import BaseModel
# from typing import Optional, List, Dict, Any
# from models.translator import Translator
# from models.intent_classifier import classify_intent
# from models.slot_filler import extract_slots
# from models.summarizer import generate_summary_text
# from utils.database import insert_complaint
# from utils.logger import get_logger
# from utils.preprocessing import clean_text, combine_json_documents
# from config.settings import CONFIDENCE_THRESHOLD, INTENT_TO_DEPT

# logger = get_logger()
# app = FastAPI(title="Municipal AI - Transcript Processor")

# translator = Translator()

# # ----------------------------
# # Request & Response Models
# # ----------------------------
# class TranscriptIn(BaseModel):
#     transcript: str
#     asr_confidence: Optional[float] = 0.9
#     meta: Optional[Dict[str, Any]] = None

# class ComplaintOut(BaseModel):
#     _id: Optional[str]
#     department: str
#     intent: str
#     summary: str
#     severity: str
#     location: Optional[str]
#     name: Optional[str]
#     date: Optional[str]
#     language: Optional[str]
#     confidence_score: Optional[float]
#     missing_fields: Optional[List[str]]
#     final_summary: Optional[str]
#     raw_transcript: Optional[str]
#     translated_text: Optional[str]

# # ----------------------------
# # Health Check
# # ----------------------------
# @app.get("/health")
# def health():
#     return {"status": "ok"}

# # ----------------------------
# # Main Processing Endpoint
# # ----------------------------
# @app.post("/process_transcript", response_model=ComplaintOut)
# def process_transcript(payload: TranscriptIn):
#     try:
#         raw = payload.transcript or ""
#         asr_conf = float(payload.asr_confidence or 0.0)

#         # Step 0: Clean transcript
#         raw = clean_text(raw)
#         if not raw:
#             logger.error("Transcript is empty after cleaning.")
#             raise HTTPException(status_code=400, detail="Transcript is empty.")

#         logger.info(f"Processing transcript: {raw[:50]}...")

#         # Step 1: LID + translation
#         language, translated = translator.detect_and_translate(raw)
#         logger.info(f"Detected language={language}")

#         # Step 2: Intent classification
#         intent, intent_conf = classify_intent(translated)
#         logger.info(f"Intent={intent} conf={intent_conf}")

#         # Step 3: Slot extraction
#         slots = extract_slots(translated, intent_label=intent)
#         logger.info(f"Extracted slots={slots}")

#         # Step 4: Confidence fusion
#         final_conf = round((asr_conf * 0.6 + intent_conf * 0.4), 3)

#         # Step 5: Summaries
#         short_summary = translated[:300] if translated else ""
#         final_summary_text = generate_summary_text(
#             translated,
#             intent,
#             slots.get("location", "N/A"),
#             slots.get("severity", "medium"),
#         )

#         # Step 6: Translate summaries back to original language if needed
#         summary_out = translator.translate_back(short_summary, language) if language != "en" else short_summary
#         final_summary_out = translator.translate_back(final_summary_text, language) if language != "en" else final_summary_text

#         # Step 7: Build document
#         doc = {
#             "department": slots.get("department", INTENT_TO_DEPT.get(intent, "General")),
#             "intent": intent,
#             "summary": summary_out,
#             "severity": slots.get("severity", "medium"),
#             "location": slots.get("location"),
#             "name": slots.get("name"),
#             "date": slots.get("date"),
#             "language": language,
#             "confidence_score": final_conf,
#             "missing_fields": slots.get("missing_fields", []),
#             "final_summary": final_summary_out,
#             "raw_transcript": raw,
#             "translated_text": translated if language != "en" else None,
#         }

#         # Step 8: Handle low confidence + missing fields
#         if final_conf < CONFIDENCE_THRESHOLD and doc["missing_fields"]:
#             logger.info("Low confidence & missing fields -> returning doc with clarification needed.")

#         # Step 9: Insert into DB
#         try:
#             inserted_id = insert_complaint(doc)
#             doc["_id"] = str(inserted_id)
#             logger.info(f"Inserted complaint id={inserted_id} intent={intent} conf={final_conf}")
#         except Exception as db_exc:
#             logger.error(f"DB insert failed: {db_exc}")
#             raise HTTPException(status_code=500, detail="db insert failed")

#         return doc

#     except HTTPException as http_exc:
#         raise http_exc
#     except Exception as exc:
#         logger.error(f"Unhandled error in process_transcript: {exc}")
#         raise HTTPException(status_code=500, detail="Internal server error")

# # ----------------------------
# # Multiple Transcripts Endpoint
# # ----------------------------
# @app.post("/process_multiple_transcripts", response_model=ComplaintOut)
# def process_multiple_transcripts(json_list: list = Body(...)):
#     try:
#         # Combine all transcripts into one
#         data = combine_json_documents(json_list)
#         cleaned = clean_text(data["transcript"])

#         # Run your pipeline as usual
#         language, translated = translator.detect_and_translate(cleaned)
#         intent, intent_conf = classify_intent(translated)
#         slots = extract_slots(translated, intent_label=intent)
#         final_conf = round(intent_conf, 3)
#         short_summary = translated[:300] if translated else ""
#         final_summary_text = generate_summary_text(
#             translated,
#             intent,
#             slots.get("location", "N/A"),
#             slots.get("severity", "medium"),
#         )

#         # Translate summaries back to original language if needed
#         summary_out = translator.translate_back(short_summary, language) if language != "en" else short_summary
#         final_summary_out = translator.translate_back(final_summary_text, language) if language != "en" else final_summary_text

#         doc = {
#             "department": slots.get("department", INTENT_TO_DEPT.get(intent, "General")),
#             "intent": intent,
#             "summary": summary_out,
#             "severity": slots.get("severity", "medium"),
#             "location": slots.get("location"),
#             "name": slots.get("name"),
#             "date": slots.get("date"),
#             "language": language,
#             "confidence_score": final_conf,
#             "missing_fields": slots.get("missing_fields", []),
#             "final_summary": final_summary_out,
#             "raw_transcript": cleaned,
#             "translated_text": translated if language != "en" else None,
#         }

#         # Insert into DB
#         try:
#             inserted_id = insert_complaint(doc)
#             doc["_id"] = str(inserted_id)
#             logger.info(f"Inserted complaint id={inserted_id} intent={intent} conf={final_conf}")
#         except Exception as db_exc:
#             logger.error(f"DB insert failed: {db_exc}")
#             raise HTTPException(status_code=500, detail="db insert failed")

#         return doc

#     except Exception as exc:
#         logger.error(f"Error processing multiple transcripts: {exc}")
#         raise HTTPException(status_code=500, detail=str(exc))
    
# if __name__ == "__main__":
#     import uvicorn
#     port = int(os.environ.get("PORT", 8000))
#     uvicorn.run("main:app", host="0.0.0.0", port=port)


import os
import asyncio
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from threading import Thread
from pymongo import MongoClient
from models.translator import Translator
from models.intent_classifier import classify_intent
from models.slot_filler import extract_slots
from models.summarizer import generate_summary_text
from utils.database import insert_complaint
from utils.logger import get_logger
from utils.preprocessing import clean_text, combine_json_documents
from config.settings import CONFIDENCE_THRESHOLD, INTENT_TO_DEPT

logger = get_logger()
app = FastAPI(title="Municipal AI - Transcript Processor")

translator = Translator()

# ----------------------------
# Request & Response Models
# ----------------------------
class TranscriptIn(BaseModel):
    transcript: str
    asr_confidence: Optional[float] = 0.9
    meta: Optional[Dict[str, Any]] = None

class ComplaintOut(BaseModel):
    _id: Optional[str]
    department: str
    intent: str
    summary: str
    severity: str
    location: Optional[str]
    name: Optional[str]
    date: Optional[str]
    language: Optional[str]
    confidence_score: Optional[float]
    missing_fields: Optional[List[str]]
    final_summary: Optional[str]
    raw_transcript: Optional[str]
    translated_text: Optional[str]

# ----------------------------
# Auto-Processing Functions
# ----------------------------
def process_document_from_summaries(document):
    """Process a single document from summaries collection"""
    try:
        # Extract transcript from document (adjust field names as needed)
        transcript = (
            document.get('transcript', '') or 
            document.get('text', '') or 
            document.get('summary', '') or 
            document.get('content', '')
        )
        
        if not transcript:
            logger.warning(f"No transcript found in document {document.get('_id')}")
            return None

        # Clean transcript
        raw = clean_text(transcript)
        if not raw:
            logger.warning(f"Empty transcript after cleaning for document {document.get('_id')}")
            return None

        logger.info(f"Auto-processing document: {raw[:50]}...")

        # Step 1: LID + translation
        language, translated = translator.detect_and_translate(raw)

        # Step 2: Intent classification
        intent, intent_conf = classify_intent(translated)

        # Step 3: Slot extraction
        slots = extract_slots(translated, intent_label=intent)

        # Step 4: Confidence calculation
        final_conf = round(intent_conf, 3)

        # Step 5: Generate summaries
        short_summary = translated[:300] if translated else ""
        final_summary_text = generate_summary_text(
            translated,
            intent,
            slots.get("location", "N/A"),
            slots.get("severity", "medium"),
        )

        # Step 6: Translate summaries back if needed
        summary_out = translator.translate_back(short_summary, language) if language != "en" else short_summary
        final_summary_out = translator.translate_back(final_summary_text, language) if language != "en" else final_summary_text

        # Step 7: Build document
        processed_doc = {
            "department": slots.get("department", INTENT_TO_DEPT.get(intent, "General")),
            "intent": intent,
            "summary": summary_out,
            "severity": slots.get("severity", "medium"),
            "location": slots.get("location"),
            "name": slots.get("name"),
            "date": slots.get("date"),
            "language": language,
            "confidence_score": final_conf,
            "missing_fields": slots.get("missing_fields", []),
            "final_summary": final_summary_out,
            "raw_transcript": raw,
            "translated_text": translated if language != "en" else None,
            "source_document_id": str(document.get('_id')),  # Reference to original document
        }

        # Step 8: Insert into processed_complaints
        inserted_id = insert_complaint(processed_doc)
        logger.info(f"✅ Auto-processed: {document.get('_id')} -> {inserted_id} | Intent: {intent} | Confidence: {final_conf}")
        
        return inserted_id

    except Exception as e:
        logger.error(f"❌ Error auto-processing document {document.get('_id')}: {e}")
        return None

def watch_summaries_collection():
    """Watch for new documents in summaries collection and auto-process them"""
    try:
        # Connect to MongoDB
        client = MongoClient(os.getenv('SOURCE_MONGO_URI'))
        db = client[os.getenv('SOURCE_DB')]
        collection = db[os.getenv('SOURCE_COLLECTION')]
        
        logger.info("🎯 Auto-processing ACTIVATED! Watching summaries collection...")
        
        # Watch for insert operations only
        with collection.watch([{'$match': {'operationType': 'insert'}}]) as stream:
            for change in stream:
                try:
                    # Get the new document
                    new_doc = change['fullDocument']
                    doc_id = new_doc['_id']
                    
                    logger.info(f"🆕 NEW DOCUMENT DETECTED in summaries: {doc_id}")
                    
                    # Process the document
                    result = process_document_from_summaries(new_doc)
                    
                    if result:
                        logger.info(f"🚀 Successfully auto-processed: {doc_id}")
                    else:
                        logger.warning(f"⚠️ Failed to process: {doc_id}")
                        
                except Exception as e:
                    logger.error(f"❌ Error processing new document: {e}")
                    
    except Exception as e:
        logger.error(f"❌ Change stream error: {e}")
        # Try to reconnect after 30 seconds
        logger.info("🔄 Attempting to reconnect in 30 seconds...")
        import time
        time.sleep(30)
        watch_summaries_collection()  # Retry

# ----------------------------
# Startup Event
# ----------------------------
@app.on_event("startup")
async def startup_event():
    """Start auto-processing when the app starts"""
    logger.info("🚀 Starting Municipal AI - Transcript Processor...")
    logger.info("🔧 Initializing auto-processing service...")
    
    # Start the collection watcher in a separate thread
    watcher_thread = Thread(target=watch_summaries_collection, daemon=True)
    watcher_thread.start()
    
    logger.info("✅ AUTO-PROCESSING IS NOW LIVE!")
    logger.info("📊 System will automatically process new documents added to 'summaries' collection")

# ----------------------------
# Health Check & Status
# ----------------------------
@app.get("/health")
def health():
    return {"status": "ok", "auto_processing": "active"}

@app.get("/auto-status")
def auto_processing_status():
    return {
        "status": "active",
        "message": "Auto-processing is monitoring summaries collection",
        "trigger": "MongoDB Change Streams",
        "action": "Automatically processes new documents in real-time",
        "source_collection": "summaries",
        "destination_collection": "processed_complaints"
    }

# ----------------------------
# Manual Processing Endpoints
# ----------------------------
@app.post("/process-batch")
def process_batch():
    """Manually trigger batch processing from summaries collection"""
    try:
        logger.info("🔄 Manual batch processing triggered...")
        
        # Connect to summaries collection
        client = MongoClient(os.getenv('SOURCE_MONGO_URI'))
        db = client[os.getenv('SOURCE_DB')]
        collection = db[os.getenv('SOURCE_COLLECTION')]
        
        # Find unprocessed documents
        documents = collection.find({"processed": {"$ne": True}})
        processed_count = 0
        
        for doc in documents:
            result = process_document_from_summaries(doc)
            if result:
                processed_count += 1
                # Mark as processed
                collection.update_one(
                    {"_id": doc["_id"]}, 
                    {"$set": {"processed": True}}
                )
        
        logger.info(f"✅ Manual batch processing completed. Processed {processed_count} documents")
        return {
            "status": "success", 
            "message": f"Batch processing completed successfully. Processed {processed_count} documents"
        }
        
    except Exception as e:
        logger.error(f"❌ Manual batch processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")

# ----------------------------
# Original Processing Endpoints
# ----------------------------
@app.post("/process_transcript", response_model=ComplaintOut)
def process_transcript(payload: TranscriptIn):
    try:
        raw = payload.transcript or ""
        asr_conf = float(payload.asr_confidence or 0.0)

        # Step 0: Clean transcript
        raw = clean_text(raw)
        if not raw:
            logger.error("Transcript is empty after cleaning.")
            raise HTTPException(status_code=400, detail="Transcript is empty.")

        logger.info(f"Processing transcript: {raw[:50]}...")

        # Step 1: LID + translation
        language, translated = translator.detect_and_translate(raw)
        logger.info(f"Detected language={language}")

        # Step 2: Intent classification
        intent, intent_conf = classify_intent(translated)
        logger.info(f"Intent classified as {intent} with confidence {intent_conf}")

        # Step 3: Slot extraction
        slots = extract_slots(translated, intent_label=intent)
        logger.info(f"Extracted slots -> dept: {slots.get('department', 'N/A')}, location: {slots.get('location', 'N/A')}, severity: {slots.get('severity', 'N/A')}, name: {slots.get('name', 'None')}, date: {slots.get('date', 'N/A')}, complaint_id: {slots.get('complaint_id', 'None')}, missing: {slots.get('missing_fields', [])}")

        # Step 4: Confidence fusion
        final_conf = round((asr_conf * 0.6 + intent_conf * 0.4), 3)

        # Step 5: Summaries
        short_summary = translated[:300] if translated else ""
        final_summary_text = generate_summary_text(
            translated,
            intent,
            slots.get("location", "N/A"),
            slots.get("severity", "medium"),
        )

        # Step 6: Translate summaries back to original language if needed
        summary_out = translator.translate_back(short_summary, language) if language != "en" else short_summary
        final_summary_out = translator.translate_back(final_summary_text, language) if language != "en" else final_summary_text

        # Step 7: Build document
        doc = {
            "department": slots.get("department", INTENT_TO_DEPT.get(intent, "General")),
            "intent": intent,
            "summary": summary_out,
            "severity": slots.get("severity", "medium"),
            "location": slots.get("location"),
            "name": slots.get("name"),
            "date": slots.get("date"),
            "language": language,
            "confidence_score": final_conf,
            "missing_fields": slots.get("missing_fields", []),
            "final_summary": final_summary_out,
            "raw_transcript": raw,
            "translated_text": translated if language != "en" else None,
        }

        # Step 8: Handle low confidence + missing fields
        if final_conf < CONFIDENCE_THRESHOLD and doc["missing_fields"]:
            logger.info("Low confidence & missing fields -> returning doc with clarification needed.")

        # Step 9: Insert into DB
        try:
            inserted_id = insert_complaint(doc)
            doc["_id"] = str(inserted_id)
            logger.info(f"Inserted complaint id={inserted_id} intent={intent} conf={final_conf}")
        except Exception as db_exc:
            logger.error(f"DB insert failed: {db_exc}")
            raise HTTPException(status_code=500, detail="db insert failed")

        return doc

    except HTTPException as http_exc:
        raise http_exc
    except Exception as exc:
        logger.error(f"Unhandled error in process_transcript: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/process_multiple_transcripts", response_model=ComplaintOut)
def process_multiple_transcripts(json_list: list = Body(...)):
    try:
        # Combine all transcripts into one
        data = combine_json_documents(json_list)
        cleaned = clean_text(data["transcript"])

        # Run your pipeline as usual
        language, translated = translator.detect_and_translate(cleaned)
        intent, intent_conf = classify_intent(translated)
        slots = extract_slots(translated, intent_label=intent)
        final_conf = round(intent_conf, 3)
        short_summary = translated[:300] if translated else ""
        final_summary_text = generate_summary_text(
            translated,
            intent,
            slots.get("location", "N/A"),
            slots.get("severity", "medium"),
        )

        # Translate summaries back to original language if needed
        summary_out = translator.translate_back(short_summary, language) if language != "en" else short_summary
        final_summary_out = translator.translate_back(final_summary_text, language) if language != "en" else final_summary_text

        doc = {
            "department": slots.get("department", INTENT_TO_DEPT.get(intent, "General")),
            "intent": intent,
            "summary": summary_out,
            "severity": slots.get("severity", "medium"),
            "location": slots.get("location"),
            "name": slots.get("name"),
            "date": slots.get("date"),
            "language": language,
            "confidence_score": final_conf,
            "missing_fields": slots.get("missing_fields", []),
            "final_summary": final_summary_out,
            "raw_transcript": cleaned,
            "translated_text": translated if language != "en" else None,
        }

        # Insert into DB
        try:
            inserted_id = insert_complaint(doc)
            doc["_id"] = str(inserted_id)
            logger.info(f"Inserted complaint id={inserted_id} intent={intent} conf={final_conf}")
        except Exception as db_exc:
            logger.error(f"DB insert failed: {db_exc}")
            raise HTTPException(status_code=500, detail="db insert failed")

        return doc

    except Exception as exc:
        logger.error(f"Error processing multiple transcripts: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))

# ----------------------------
# Application Entry Point
# ----------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)