# # # import os
# # # from fastapi import FastAPI, HTTPException, Body
# # # from pydantic import BaseModel
# # # from typing import Optional, List, Dict, Any
# # # from models.translator import Translator
# # # from models.intent_classifier import classify_intent
# # # from models.slot_filler import extract_slots
# # # from models.summarizer import generate_summary_text
# # # from utils.database import insert_complaint
# # # from utils.logger import get_logger
# # # from utils.preprocessing import clean_text, combine_json_documents
# # # from config.settings import CONFIDENCE_THRESHOLD, INTENT_TO_DEPT

# # # logger = get_logger()
# # # app = FastAPI(title="Municipal AI - Transcript Processor")

# # # translator = Translator()

# # # # ----------------------------
# # # # Request & Response Models
# # # # ----------------------------
# # # class TranscriptIn(BaseModel):
# # #     transcript: str
# # #     asr_confidence: Optional[float] = 0.9
# # #     meta: Optional[Dict[str, Any]] = None

# # # class ComplaintOut(BaseModel):
# # #     _id: Optional[str]
# # #     department: str
# # #     intent: str
# # #     summary: str
# # #     severity: str
# # #     location: Optional[str]
# # #     name: Optional[str]
# # #     date: Optional[str]
# # #     language: Optional[str]
# # #     confidence_score: Optional[float]
# # #     missing_fields: Optional[List[str]]
# # #     final_summary: Optional[str]
# # #     raw_transcript: Optional[str]
# # #     translated_text: Optional[str]

# # # # ----------------------------
# # # # Health Check
# # # # ----------------------------
# # # @app.get("/health")
# # # def health():
# # #     return {"status": "ok"}

# # # # ----------------------------
# # # # Main Processing Endpoint
# # # # ----------------------------
# # # @app.post("/process_transcript", response_model=ComplaintOut)
# # # def process_transcript(payload: TranscriptIn):
# # #     try:
# # #         raw = payload.transcript or ""
# # #         asr_conf = float(payload.asr_confidence or 0.0)

# # #         # Step 0: Clean transcript
# # #         raw = clean_text(raw)
# # #         if not raw:
# # #             logger.error("Transcript is empty after cleaning.")
# # #             raise HTTPException(status_code=400, detail="Transcript is empty.")

# # #         logger.info(f"Processing transcript: {raw[:50]}...")

# # #         # Step 1: LID + translation
# # #         language, translated = translator.detect_and_translate(raw)
# # #         logger.info(f"Detected language={language}")

# # #         # Step 2: Intent classification
# # #         intent, intent_conf = classify_intent(translated)
# # #         logger.info(f"Intent={intent} conf={intent_conf}")

# # #         # Step 3: Slot extraction
# # #         slots = extract_slots(translated, intent_label=intent)
# # #         logger.info(f"Extracted slots={slots}")

# # #         # Step 4: Confidence fusion
# # #         final_conf = round((asr_conf * 0.6 + intent_conf * 0.4), 3)

# # #         # Step 5: Summaries
# # #         short_summary = translated[:300] if translated else ""
# # #         final_summary_text = generate_summary_text(
# # #             translated,
# # #             intent,
# # #             slots.get("location", "N/A"),
# # #             slots.get("severity", "medium"),
# # #         )

# # #         # Step 6: Translate summaries back to original language if needed
# # #         summary_out = translator.translate_back(short_summary, language) if language != "en" else short_summary
# # #         final_summary_out = translator.translate_back(final_summary_text, language) if language != "en" else final_summary_text

# # #         # Step 7: Build document
# # #         doc = {
# # #             "department": slots.get("department", INTENT_TO_DEPT.get(intent, "General")),
# # #             "intent": intent,
# # #             "summary": summary_out,
# # #             "severity": slots.get("severity", "medium"),
# # #             "location": slots.get("location"),
# # #             "name": slots.get("name"),
# # #             "date": slots.get("date"),
# # #             "language": language,
# # #             "confidence_score": final_conf,
# # #             "missing_fields": slots.get("missing_fields", []),
# # #             "final_summary": final_summary_out,
# # #             "raw_transcript": raw,
# # #             "translated_text": translated if language != "en" else None,
# # #         }

# # #         # Step 8: Handle low confidence + missing fields
# # #         if final_conf < CONFIDENCE_THRESHOLD and doc["missing_fields"]:
# # #             logger.info("Low confidence & missing fields -> returning doc with clarification needed.")

# # #         # Step 9: Insert into DB
# # #         try:
# # #             inserted_id = insert_complaint(doc)
# # #             doc["_id"] = str(inserted_id)
# # #             logger.info(f"Inserted complaint id={inserted_id} intent={intent} conf={final_conf}")
# # #         except Exception as db_exc:
# # #             logger.error(f"DB insert failed: {db_exc}")
# # #             raise HTTPException(status_code=500, detail="db insert failed")

# # #         return doc

# # #     except HTTPException as http_exc:
# # #         raise http_exc
# # #     except Exception as exc:
# # #         logger.error(f"Unhandled error in process_transcript: {exc}")
# # #         raise HTTPException(status_code=500, detail="Internal server error")

# # # # ----------------------------
# # # # Multiple Transcripts Endpoint
# # # # ----------------------------
# # # @app.post("/process_multiple_transcripts", response_model=ComplaintOut)
# # # def process_multiple_transcripts(json_list: list = Body(...)):
# # #     try:
# # #         # Combine all transcripts into one
# # #         data = combine_json_documents(json_list)
# # #         cleaned = clean_text(data["transcript"])

# # #         # Run your pipeline as usual
# # #         language, translated = translator.detect_and_translate(cleaned)
# # #         intent, intent_conf = classify_intent(translated)
# # #         slots = extract_slots(translated, intent_label=intent)
# # #         final_conf = round(intent_conf, 3)
# # #         short_summary = translated[:300] if translated else ""
# # #         final_summary_text = generate_summary_text(
# # #             translated,
# # #             intent,
# # #             slots.get("location", "N/A"),
# # #             slots.get("severity", "medium"),
# # #         )

# # #         # Translate summaries back to original language if needed
# # #         summary_out = translator.translate_back(short_summary, language) if language != "en" else short_summary
# # #         final_summary_out = translator.translate_back(final_summary_text, language) if language != "en" else final_summary_text

# # #         doc = {
# # #             "department": slots.get("department", INTENT_TO_DEPT.get(intent, "General")),
# # #             "intent": intent,
# # #             "summary": summary_out,
# # #             "severity": slots.get("severity", "medium"),
# # #             "location": slots.get("location"),
# # #             "name": slots.get("name"),
# # #             "date": slots.get("date"),
# # #             "language": language,
# # #             "confidence_score": final_conf,
# # #             "missing_fields": slots.get("missing_fields", []),
# # #             "final_summary": final_summary_out,
# # #             "raw_transcript": cleaned,
# # #             "translated_text": translated if language != "en" else None,
# # #         }

# # #         # Insert into DB
# # #         try:
# # #             inserted_id = insert_complaint(doc)
# # #             doc["_id"] = str(inserted_id)
# # #             logger.info(f"Inserted complaint id={inserted_id} intent={intent} conf={final_conf}")
# # #         except Exception as db_exc:
# # #             logger.error(f"DB insert failed: {db_exc}")
# # #             raise HTTPException(status_code=500, detail="db insert failed")

# # #         return doc

# # #     except Exception as exc:
# # #         logger.error(f"Error processing multiple transcripts: {exc}")
# # #         raise HTTPException(status_code=500, detail=str(exc))
    
# # # if __name__ == "__main__":
# # #     import uvicorn
# # #     port = int(os.environ.get("PORT", 8000))
# # #     uvicorn.run("main:app", host="0.0.0.0", port=port)


# # import os
# # import asyncio
# # from fastapi import FastAPI, HTTPException, Body
# # from pydantic import BaseModel
# # from typing import Optional, List, Dict, Any
# # from threading import Thread
# # from pymongo import MongoClient
# # from models.translator import Translator
# # from models.intent_classifier import classify_intent
# # from models.slot_filler import extract_slots
# # from models.summarizer import generate_summary_text
# # from utils.database import insert_complaint
# # from utils.logger import get_logger
# # from utils.preprocessing import clean_text, combine_json_documents
# # from config.settings import CONFIDENCE_THRESHOLD, INTENT_TO_DEPT

# # logger = get_logger()
# # app = FastAPI(title="Municipal AI - Transcript Processor")

# # translator = Translator()

# # # ----------------------------
# # # Request & Response Models
# # # ----------------------------
# # class TranscriptIn(BaseModel):
# #     transcript: str
# #     asr_confidence: Optional[float] = 0.9
# #     meta: Optional[Dict[str, Any]] = None

# # class ComplaintOut(BaseModel):
# #     _id: Optional[str]
# #     department: str
# #     intent: str
# #     summary: str
# #     severity: str
# #     location: Optional[str]
# #     name: Optional[str]
# #     date: Optional[str]
# #     language: Optional[str]
# #     confidence_score: Optional[float]
# #     missing_fields: Optional[List[str]]
# #     final_summary: Optional[str]
# #     raw_transcript: Optional[str]
# #     translated_text: Optional[str]

# # # ----------------------------
# # # Auto-Processing Functions
# # # ----------------------------
# # def process_document_from_summaries(document):
# #     """Process a single document from summaries collection"""
# #     try:
# #         # Extract transcript from document (adjust field names as needed)
# #         transcript = (
# #             document.get('transcript', '') or 
# #             document.get('text', '') or 
# #             document.get('summary', '') or 
# #             document.get('content', '')
# #         )
        
# #         if not transcript:
# #             logger.warning(f"No transcript found in document {document.get('_id')}")
# #             return None

# #         # Clean transcript
# #         raw = clean_text(transcript)
# #         if not raw:
# #             logger.warning(f"Empty transcript after cleaning for document {document.get('_id')}")
# #             return None

# #         logger.info(f"Auto-processing document: {raw[:50]}...")

# #         # Step 1: LID + translation
# #         language, translated = translator.detect_and_translate(raw)

# #         # Step 2: Intent classification
# #         intent, intent_conf = classify_intent(translated)

# #         # Step 3: Slot extraction
# #         slots = extract_slots(translated, intent_label=intent)

# #         # Step 4: Confidence calculation
# #         final_conf = round(intent_conf, 3)

# #         # Step 5: Generate summaries
# #         short_summary = translated[:300] if translated else ""
# #         final_summary_text = generate_summary_text(
# #             translated,
# #             intent,
# #             slots.get("location", "N/A"),
# #             slots.get("severity", "medium"),
# #         )

# #         # Step 6: Translate summaries back if needed
# #         summary_out = translator.translate_back(short_summary, language) if language != "en" else short_summary
# #         final_summary_out = translator.translate_back(final_summary_text, language) if language != "en" else final_summary_text

# #         # Step 7: Build document
# #         processed_doc = {
# #             "department": slots.get("department", INTENT_TO_DEPT.get(intent, "General")),
# #             "intent": intent,
# #             "summary": summary_out,
# #             "severity": slots.get("severity", "medium"),
# #             "location": slots.get("location"),
# #             "name": slots.get("name"),
# #             "date": slots.get("date"),
# #             "language": language,
# #             "confidence_score": final_conf,
# #             "missing_fields": slots.get("missing_fields", []),
# #             "final_summary": final_summary_out,
# #             "raw_transcript": raw,
# #             "translated_text": translated if language != "en" else None,
# #             "source_document_id": str(document.get('_id')),  # Reference to original document
# #         }

# #         # Step 8: Insert into processed_complaints
# #         inserted_id = insert_complaint(processed_doc)
# #         logger.info(f"✅ Auto-processed: {document.get('_id')} -> {inserted_id} | Intent: {intent} | Confidence: {final_conf}")
        
# #         return inserted_id

# #     except Exception as e:
# #         logger.error(f"❌ Error auto-processing document {document.get('_id')}: {e}")
# #         return None

# # def watch_summaries_collection():
# #     """Watch for new documents in summaries collection and auto-process them"""
# #     try:
# #         # Connect to MongoDB
# #         client = MongoClient(os.getenv('SOURCE_MONGO_URI'))
# #         db = client[os.getenv('SOURCE_DB')]
# #         collection = db[os.getenv('SOURCE_COLLECTION')]
        
# #         logger.info("🎯 Auto-processing ACTIVATED! Watching summaries collection...")
        
# #         # Watch for insert operations only
# #         with collection.watch([{'$match': {'operationType': 'insert'}}]) as stream:
# #             for change in stream:
# #                 try:
# #                     # Get the new document
# #                     new_doc = change['fullDocument']
# #                     doc_id = new_doc['_id']
                    
# #                     logger.info(f"🆕 NEW DOCUMENT DETECTED in summaries: {doc_id}")
                    
# #                     # Process the document
# #                     result = process_document_from_summaries(new_doc)
                    
# #                     if result:
# #                         logger.info(f"🚀 Successfully auto-processed: {doc_id}")
# #                     else:
# #                         logger.warning(f"⚠️ Failed to process: {doc_id}")
                        
# #                 except Exception as e:
# #                     logger.error(f"❌ Error processing new document: {e}")
                    
# #     except Exception as e:
# #         logger.error(f"❌ Change stream error: {e}")
# #         # Try to reconnect after 30 seconds
# #         logger.info("🔄 Attempting to reconnect in 30 seconds...")
# #         import time
# #         time.sleep(30)
# #         watch_summaries_collection()  # Retry

# # # ----------------------------
# # # Startup Event
# # # ----------------------------
# # @app.on_event("startup")
# # async def startup_event():
# #     """Start auto-processing when the app starts"""
# #     logger.info("🚀 Starting Municipal AI - Transcript Processor...")
# #     logger.info("🔧 Initializing auto-processing service...")
    
# #     # Start the collection watcher in a separate thread
# #     watcher_thread = Thread(target=watch_summaries_collection, daemon=True)
# #     watcher_thread.start()
    
# #     logger.info("✅ AUTO-PROCESSING IS NOW LIVE!")
# #     logger.info("📊 System will automatically process new documents added to 'summaries' collection")

# # # ----------------------------
# # # Health Check & Status
# # # ----------------------------
# # @app.get("/health")
# # def health():
# #     return {"status": "ok", "auto_processing": "active"}

# # @app.get("/auto-status")
# # def auto_processing_status():
# #     return {
# #         "status": "active",
# #         "message": "Auto-processing is monitoring summaries collection",
# #         "trigger": "MongoDB Change Streams",
# #         "action": "Automatically processes new documents in real-time",
# #         "source_collection": "summaries",
# #         "destination_collection": "processed_complaints"
# #     }

# # # ----------------------------
# # # Manual Processing Endpoints
# # # ----------------------------
# # @app.post("/process-batch")
# # def process_batch():
# #     """Manually trigger batch processing from summaries collection"""
# #     try:
# #         logger.info("🔄 Manual batch processing triggered...")
        
# #         # Connect to summaries collection
# #         client = MongoClient(os.getenv('SOURCE_MONGO_URI'))
# #         db = client[os.getenv('SOURCE_DB')]
# #         collection = db[os.getenv('SOURCE_COLLECTION')]
        
# #         # Find unprocessed documents
# #         documents = collection.find({"processed": {"$ne": True}})
# #         processed_count = 0
        
# #         for doc in documents:
# #             result = process_document_from_summaries(doc)
# #             if result:
# #                 processed_count += 1
# #                 # Mark as processed
# #                 collection.update_one(
# #                     {"_id": doc["_id"]}, 
# #                     {"$set": {"processed": True}}
# #                 )
        
# #         logger.info(f"✅ Manual batch processing completed. Processed {processed_count} documents")
# #         return {
# #             "status": "success", 
# #             "message": f"Batch processing completed successfully. Processed {processed_count} documents"
# #         }
        
# #     except Exception as e:
# #         logger.error(f"❌ Manual batch processing failed: {e}")
# #         raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")

# # # ----------------------------
# # # Original Processing Endpoints
# # # ----------------------------
# # @app.post("/process_transcript", response_model=ComplaintOut)
# # def process_transcript(payload: TranscriptIn):
# #     try:
# #         raw = payload.transcript or ""
# #         asr_conf = float(payload.asr_confidence or 0.0)

# #         # Step 0: Clean transcript
# #         raw = clean_text(raw)
# #         if not raw:
# #             logger.error("Transcript is empty after cleaning.")
# #             raise HTTPException(status_code=400, detail="Transcript is empty.")

# #         logger.info(f"Processing transcript: {raw[:50]}...")

# #         # Step 1: LID + translation
# #         language, translated = translator.detect_and_translate(raw)
# #         logger.info(f"Detected language={language}")

# #         # Step 2: Intent classification
# #         intent, intent_conf = classify_intent(translated)
# #         logger.info(f"Intent classified as {intent} with confidence {intent_conf}")

# #         # Step 3: Slot extraction
# #         slots = extract_slots(translated, intent_label=intent)
# #         logger.info(f"Extracted slots -> dept: {slots.get('department', 'N/A')}, location: {slots.get('location', 'N/A')}, severity: {slots.get('severity', 'N/A')}, name: {slots.get('name', 'None')}, date: {slots.get('date', 'N/A')}, complaint_id: {slots.get('complaint_id', 'None')}, missing: {slots.get('missing_fields', [])}")

# #         # Step 4: Confidence fusion
# #         final_conf = round((asr_conf * 0.6 + intent_conf * 0.4), 3)

# #         # Step 5: Summaries
# #         short_summary = translated[:300] if translated else ""
# #         final_summary_text = generate_summary_text(
# #             translated,
# #             intent,
# #             slots.get("location", "N/A"),
# #             slots.get("severity", "medium"),
# #         )

# #         # Step 6: Translate summaries back to original language if needed
# #         summary_out = translator.translate_back(short_summary, language) if language != "en" else short_summary
# #         final_summary_out = translator.translate_back(final_summary_text, language) if language != "en" else final_summary_text

# #         # Step 7: Build document
# #         doc = {
# #             "department": slots.get("department", INTENT_TO_DEPT.get(intent, "General")),
# #             "intent": intent,
# #             "summary": summary_out,
# #             "severity": slots.get("severity", "medium"),
# #             "location": slots.get("location"),
# #             "name": slots.get("name"),
# #             "date": slots.get("date"),
# #             "language": language,
# #             "confidence_score": final_conf,
# #             "missing_fields": slots.get("missing_fields", []),
# #             "final_summary": final_summary_out,
# #             "raw_transcript": raw,
# #             "translated_text": translated if language != "en" else None,
# #         }

# #         # Step 8: Handle low confidence + missing fields
# #         if final_conf < CONFIDENCE_THRESHOLD and doc["missing_fields"]:
# #             logger.info("Low confidence & missing fields -> returning doc with clarification needed.")

# #         # Step 9: Insert into DB
# #         try:
# #             inserted_id = insert_complaint(doc)
# #             doc["_id"] = str(inserted_id)
# #             logger.info(f"Inserted complaint id={inserted_id} intent={intent} conf={final_conf}")
# #         except Exception as db_exc:
# #             logger.error(f"DB insert failed: {db_exc}")
# #             raise HTTPException(status_code=500, detail="db insert failed")

# #         return doc

# #     except HTTPException as http_exc:
# #         raise http_exc
# #     except Exception as exc:
# #         logger.error(f"Unhandled error in process_transcript: {exc}")
# #         raise HTTPException(status_code=500, detail="Internal server error")

# # @app.post("/process_multiple_transcripts", response_model=ComplaintOut)
# # def process_multiple_transcripts(json_list: list = Body(...)):
# #     try:
# #         # Combine all transcripts into one
# #         data = combine_json_documents(json_list)
# #         cleaned = clean_text(data["transcript"])

# #         # Run your pipeline as usual
# #         language, translated = translator.detect_and_translate(cleaned)
# #         intent, intent_conf = classify_intent(translated)
# #         slots = extract_slots(translated, intent_label=intent)
# #         final_conf = round(intent_conf, 3)
# #         short_summary = translated[:300] if translated else ""
# #         final_summary_text = generate_summary_text(
# #             translated,
# #             intent,
# #             slots.get("location", "N/A"),
# #             slots.get("severity", "medium"),
# #         )

# #         # Translate summaries back to original language if needed
# #         summary_out = translator.translate_back(short_summary, language) if language != "en" else short_summary
# #         final_summary_out = translator.translate_back(final_summary_text, language) if language != "en" else final_summary_text

# #         doc = {
# #             "department": slots.get("department", INTENT_TO_DEPT.get(intent, "General")),
# #             "intent": intent,
# #             "summary": summary_out,
# #             "severity": slots.get("severity", "medium"),
# #             "location": slots.get("location"),
# #             "name": slots.get("name"),
# #             "date": slots.get("date"),
# #             "language": language,
# #             "confidence_score": final_conf,
# #             "missing_fields": slots.get("missing_fields", []),
# #             "final_summary": final_summary_out,
# #             "raw_transcript": cleaned,
# #             "translated_text": translated if language != "en" else None,
# #         }

# #         # Insert into DB
# #         try:
# #             inserted_id = insert_complaint(doc)
# #             doc["_id"] = str(inserted_id)
# #             logger.info(f"Inserted complaint id={inserted_id} intent={intent} conf={final_conf}")
# #         except Exception as db_exc:
# #             logger.error(f"DB insert failed: {db_exc}")
# #             raise HTTPException(status_code=500, detail="db insert failed")

# #         return doc

# #     except Exception as exc:
# #         logger.error(f"Error processing multiple transcripts: {exc}")
# #         raise HTTPException(status_code=500, detail=str(exc))

# # # ----------------------------
# # # Application Entry Point
# # # ----------------------------
# # if __name__ == "__main__":
# #     import uvicorn
# #     port = int(os.environ.get("PORT", 8000))
# #     uvicorn.run("main:app", host="0.0.0.0", port=port)

# import os
# import asyncio
# from fastapi import FastAPI, HTTPException, Body
# from pydantic import BaseModel
# from typing import Optional, List, Dict, Any
# from threading import Thread
# from pymongo import MongoClient
# from langdetect import detect
# import logging

# # Setup logging for deployment
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger("municipal_ai")

# app = FastAPI(title="Municipal AI - Transcript Processor (Lightweight)")

# # Simple intent mapping without heavy models
# SIMPLE_INTENT_MAP = {
#     "water": "WaterSupply",
#     "electricity": "Electricity", 
#     "road": "Roads",
#     "garbage": "WasteManagement",
#     "traffic": "Traffic",
#     "noise": "NoiseComplaint",
#     "default": "General"
# }

# INTENT_TO_DEPT = {
#     "WaterSupply": "Water Department",
#     "Electricity": "Electricity Board",
#     "Roads": "Public Works Department",
#     "WasteManagement": "Sanitation Department",
#     "Traffic": "Traffic Police",
#     "NoiseComplaint": "Environmental Department",
#     "General": "Municipal Office"
# }

# def simple_classify_intent(text):
#     """Lightweight intent classification using keyword matching"""
#     text_lower = text.lower()
    
#     for keyword, intent in SIMPLE_INTENT_MAP.items():
#         if keyword != "default" and keyword in text_lower:
#             return intent, 0.85
    
#     return SIMPLE_INTENT_MAP["default"], 0.60

# def extract_simple_slots(text, intent):
#     """Extract basic information without heavy NLP models"""
#     slots = {
#         "department": INTENT_TO_DEPT.get(intent, "Municipal Office"),
#         "severity": "medium",  # Default severity
#         "location": None,
#         "name": None,
#         "date": None,
#         "missing_fields": []
#     }
    
#     # Simple location detection
#     location_keywords = ["area", "street", "road", "locality", "sector"]
#     words = text.lower().split()
#     for i, word in enumerate(words):
#         if word in location_keywords and i > 0:
#             slots["location"] = " ".join(words[max(0, i-2):i+2])
#             break
    
#     # Simple severity detection
#     if any(word in text.lower() for word in ["urgent", "emergency", "serious", "severe"]):
#         slots["severity"] = "high"
#     elif any(word in text.lower() for word in ["minor", "small", "slight"]):
#         slots["severity"] = "low"
    
#     return slots

# def process_lightweight(transcript):
#     """Lightweight processing without heavy ML models"""
#     try:
#         # Clean text
#         raw = transcript.strip()
#         if not raw:
#             return None

#         # Simple language detection
#         try:
#             language = detect(raw)
#             if language != 'en':
#                 # For now, assume English if detection fails
#                 language = 'en'
#         except:
#             language = 'en'
            
#         translated = raw  # No translation for lightweight version

#         # Simple intent classification
#         intent, confidence = simple_classify_intent(translated)
        
#         # Extract basic slots
#         slots = extract_simple_slots(translated, intent)
        
#         # Create summary
#         summary = translated[:300] if len(translated) > 300 else translated
#         final_summary = f"Complaint about {intent.lower()} issue. {summary[:200]}..."

#         # Build document
#         doc = {
#             "department": slots["department"],
#             "intent": intent,
#             "summary": summary,
#             "severity": slots["severity"],
#             "location": slots.get("location"),
#             "name": slots.get("name"),
#             "date": slots.get("date"),
#             "language": language,
#             "confidence_score": confidence,
#             "missing_fields": slots.get("missing_fields", []),
#             "final_summary": final_summary,
#             "raw_transcript": raw,
#             "translated_text": translated if language != "en" else None,
#             "processing_mode": "lightweight"
#         }

#         return doc

#     except Exception as e:
#         logger.error(f"Error in lightweight processing: {e}")
#         return None

# # Auto-processing with lightweight approach
# def watch_summaries_collection():
#     """Watch for new documents - lightweight version"""
#     try:
#         client = MongoClient(os.getenv('SOURCE_MONGO_URI'))
#         db = client[os.getenv('SOURCE_DB')]
#         collection = db[os.getenv('SOURCE_COLLECTION')]
        
#         logger.info("🎯 Lightweight auto-processing ACTIVATED!")
        
#         # Use change streams
#         with collection.watch([{'$match': {'operationType': 'insert'}}]) as stream:
#             for change in stream:
#                 try:
#                     new_doc = change['fullDocument']
#                     doc_id = new_doc['_id']
                    
#                     logger.info(f"🆕 NEW DOCUMENT: {doc_id}")
                    
#                     # Extract transcript
#                     transcript = (
#                         new_doc.get('transcript', '') or 
#                         new_doc.get('text', '') or 
#                         new_doc.get('summary', '') or
#                         str(new_doc)
#                     )
                    
#                     if transcript:
#                         # Process with lightweight method
#                         result = process_lightweight(transcript)
                        
#                         if result:
#                             # Insert into processed collection
#                             dest_client = MongoClient(os.getenv('DEST_MONGO_URI'))
#                             dest_db = dest_client[os.getenv('DEST_DB')]
#                             dest_collection = dest_db[os.getenv('DEST_COLLECTION')]
                            
#                             result["source_document_id"] = str(doc_id)
#                             inserted_id = dest_collection.insert_one(result).inserted_id
                            
#                             logger.info(f"✅ Processed: {doc_id} -> {inserted_id} | {result['intent']}")
                        
#                 except Exception as e:
#                     logger.error(f"❌ Processing error: {e}")
                    
#     except Exception as e:
#         logger.error(f"❌ Watch error: {e}")

# @app.on_event("startup")
# async def startup_event():
#     logger.info("🚀 Starting Lightweight ML Processor...")
#     watcher_thread = Thread(target=watch_summaries_collection, daemon=True)
#     watcher_thread.start()
#     logger.info("✅ Lightweight auto-processing is ACTIVE!")

# @app.get("/health")
# def health():
#     return {"status": "ok", "mode": "lightweight", "memory_optimized": True}

# @app.get("/auto-status")
# def auto_status():
#     return {
#         "status": "active",
#         "mode": "lightweight",
#         "features": ["keyword_classification", "basic_slot_extraction", "auto_processing"],
#         "memory_usage": "< 512MB"
#     }

# @app.post("/process_transcript")
# def process_transcript(payload: dict):
#     try:
#         transcript = payload.get("transcript", "")
        
#         # Process with lightweight method
#         result = process_lightweight(transcript)
        
#         if result:
#             # Insert into database
#             client = MongoClient(os.getenv('DEST_MONGO_URI'))
#             db = client[os.getenv('DEST_DB')]
#             collection = db[os.getenv('DEST_COLLECTION')]
            
#             inserted_id = collection.insert_one(result).inserted_id
#             result["_id"] = str(inserted_id)
            
#             logger.info(f"✅ Manual processing: {inserted_id} | {result['intent']}")
#             return result
#         else:
#             raise HTTPException(status_code=400, detail="Processing failed")
            
#     except Exception as e:
#         logger.error(f"❌ Error: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/process-batch")
# def process_batch():
#     """Manual batch processing"""
#     try:
#         client = MongoClient(os.getenv('SOURCE_MONGO_URI'))
#         db = client[os.getenv('SOURCE_DB')]
#         collection = db[os.getenv('SOURCE_COLLECTION')]
        
#         # Find unprocessed documents
#         documents = collection.find({"processed": {"$ne": True}}).limit(10)  # Limit for memory
#         processed_count = 0
        
#         for doc in documents:
#             transcript = doc.get('transcript', '') or doc.get('text', '') or str(doc)
#             result = process_lightweight(transcript)
            
#             if result:
#                 # Insert processed doc
#                 dest_client = MongoClient(os.getenv('DEST_MONGO_URI'))
#                 dest_db = dest_client[os.getenv('DEST_DB')]
#                 dest_collection = dest_db[os.getenv('DEST_COLLECTION')]
#                 dest_collection.insert_one(result)
                
#                 # Mark as processed
#                 collection.update_one({"_id": doc["_id"]}, {"$set": {"processed": True}})
#                 processed_count += 1
        
#         return {"status": "success", "processed": processed_count, "mode": "lightweight"}
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# if __name__ == "__main__":
#     import uvicorn
#     port = int(os.environ.get("PORT", 8000))
#     uvicorn.run("main:app", host="0.0.0.0", port=port)

import os
import asyncio
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from threading import Thread
from pymongo import MongoClient
from datetime import datetime
import copy
import logging

# Import all processing modules
from models.translator import Translator
from models.intent_classifier import classify_intent
from models.slot_filler import extract_slots
from models.summarizer import generate_summary_text
from utils.database import insert_complaint, mark_document_processed
from utils.logger import get_logger
from utils.preprocessing import clean_text, combine_json_documents
from config.settings import CONFIDENCE_THRESHOLD, INTENT_TO_DEPT
from config.schema import SCHEMA

# Initialize components
logger = get_logger()
app = FastAPI(title="Municipal AI - Auto Transcript Processor")
translator = Translator()

# ----------------------------
# Request & Response Models
# ----------------------------
class TranscriptIn(BaseModel):
    model_config = ConfigDict(extra='allow')
    
    transcript: str
    asr_confidence: Optional[float] = 0.9
    meta: Optional[Dict[str, Any]] = None

class ComplaintOut(BaseModel):
    model_config = ConfigDict(extra='allow')
    
    id: Optional[str] = None
    department: str
    intent: str
    summary: str
    severity: str
    location: Optional[str] = None
    name: Optional[str] = None
    date: Optional[str] = None
    language: Optional[str] = None
    confidence_score: Optional[float] = None
    missing_fields: Optional[List[str]] = None
    final_summary: Optional[str] = None
    raw_transcript: Optional[str] = None
    translated_text: Optional[str] = None

# ----------------------------
# Core Processing Function
# ----------------------------
def process_single_document(document):
    """Process a single document from summaries collection"""
    try:
        doc_id = document.get('_id')
        logger.info(f"🔄 Processing document: {doc_id}")
        
        # Extract transcript from various possible fields
        transcript = (
            document.get('transcript', '') or 
            document.get('raw_analysis', '') or
            document.get('text', '') or 
            document.get('summary', '') or 
            document.get('content', '')
        )
        
        if not transcript:
            logger.warning(f"❌ No transcript found in document {doc_id}")
            return None

        # Step 1: Clean the transcript
        raw = clean_text(transcript)
        if not raw:
            logger.warning(f"❌ Empty transcript after cleaning for document {doc_id}")
            return None

        logger.info(f"📝 Processing: {raw[:100]}...")

        # Step 2: Language detection and translation
        language, translated = translator.detect_and_translate(raw)
        logger.info(f"🌐 Language: {language}")

        # Step 3: Intent classification
        intent, intent_conf = classify_intent(translated)
        logger.info(f"🎯 Intent: {intent} (confidence: {intent_conf})")

        # Step 4: Slot extraction
        slots = extract_slots(translated, intent_label=intent)
        logger.info(f"📊 Slots: {slots}")

        # Step 5: Calculate final confidence
        final_conf = round(intent_conf, 3)

        # Step 6: Generate summaries
        short_summary = translated[:300] if translated else ""
        final_summary_text = generate_summary_text(
            translated,
            intent,
            slots.get("location", "N/A"),
            slots.get("severity", "medium"),
        )

        # Step 7: Translate summaries back if needed
        summary_out = translator.translate_back(short_summary, language) if language != "en" else short_summary
        final_summary_out = translator.translate_back(final_summary_text, language) if language != "en" else final_summary_text

        # Step 8: Build processed document using schema
        processed_doc = copy.deepcopy(SCHEMA)
        processed_doc.update({
            "department": slots.get("department", INTENT_TO_DEPT.get(intent, "General")),
            "intent": intent,
            "summary": summary_out,
            "severity": slots.get("severity", "medium"),
            "location": slots.get("location"),
            "name": slots.get("name"),
            "date": slots.get("date") or datetime.now().isoformat(),
            "language": language,
            "confidence_score": final_conf,
            "missing_fields": slots.get("missing_fields", []),
            "final_summary": final_summary_out,
            "raw_transcript": raw,
            "translated_text": translated if language != "en" else None,
            "source_document_id": str(doc_id),
            "processed_at": datetime.now().isoformat(),
            "processing_mode": "auto"
        })

        # Step 9: Insert into processed_complaints collection
        inserted_id = insert_complaint(processed_doc)
        
        if inserted_id:
            logger.info(f"✅ Successfully processed: {doc_id} -> {inserted_id} | Intent: {intent} | Confidence: {final_conf}")
            return inserted_id
        else:
            logger.error(f"❌ Failed to insert processed document for {doc_id}")
            return None

    except Exception as e:
        logger.error(f"❌ Error processing document {document.get('_id', 'unknown')}: {e}")
        return None

# ----------------------------
# Change Stream Watcher
# ----------------------------
def watch_summaries_collection():
    """Watch for new documents in summaries collection using MongoDB Change Streams"""
    retry_count = 0
    max_retries = 10
    
    while retry_count < max_retries:
        try:
            # Connect to source MongoDB
            client = MongoClient(os.getenv('SOURCE_MONGO_URI'))
            db = client[os.getenv('SOURCE_DB')]
            collection = db[os.getenv('SOURCE_COLLECTION')]
            
            logger.info("🎯 AUTO-PROCESSING ACTIVATED!")
            logger.info(f"👀 Watching collection: {os.getenv('SOURCE_DB')}.{os.getenv('SOURCE_COLLECTION')}")
            logger.info(f"📤 Output collection: {os.getenv('DEST_DB')}.{os.getenv('DEST_COLLECTION')}")
            
            # Create change stream pipeline (watch for inserts only)
            pipeline = [{"$match": {"operationType": "insert"}}]
            
            with collection.watch(pipeline, full_document="updateLookup") as stream:
                logger.info("✅ Change stream connected successfully!")
                retry_count = 0  # Reset retry count on successful connection
                
                for change in stream:
                    try:
                        if change["operationType"] == "insert":
                            # Get the newly inserted document
                            new_document = change["fullDocument"]
                            doc_id = new_document.get('_id')
                            
                            logger.info(f"🆕 NEW DOCUMENT DETECTED: {doc_id}")
                            
                            # Process the document in a separate thread to avoid blocking
                            processing_thread = Thread(
                                target=process_single_document,
                                args=(new_document,),
                                daemon=True
                            )
                            processing_thread.start()
                            
                    except Exception as e:
                        logger.error(f"❌ Error handling change stream event: {e}")
                        continue
                        
        except Exception as e:
            retry_count += 1
            logger.error(f"❌ Change stream error (attempt {retry_count}/{max_retries}): {e}")
            
            if retry_count < max_retries:
                wait_time = min(30 * retry_count, 300)  # Exponential backoff, max 5 minutes
                logger.info(f"🔄 Retrying in {wait_time} seconds...")
                import time
                time.sleep(wait_time)
            else:
                logger.error("❌ Max retries reached. Change stream monitoring stopped.")
                break
        finally:
            try:
                client.close()
            except:
                pass

# ----------------------------
# Startup Event
# ----------------------------
@app.on_event("startup")
async def startup_event():
    """Initialize auto-processing when the application starts"""
    logger.info("🚀 Starting Municipal AI Auto-Processing Service on Render...")
    logger.info("🔧 Initializing components...")
    
    # Download spaCy model if not available (for Render deployment)
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        logger.info("✅ spaCy model loaded successfully")
    except OSError:
        logger.info("📥 Downloading spaCy model...")
        os.system("python -m spacy download en_core_web_sm")
        logger.info("✅ spaCy model downloaded")
    
    # Verify environment variables
    required_env_vars = ['SOURCE_MONGO_URI', 'SOURCE_DB', 'SOURCE_COLLECTION', 'DEST_MONGO_URI', 'DEST_DB', 'DEST_COLLECTION']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ Missing environment variables: {missing_vars}")
        return
    
    # Start the change stream watcher in a separate daemon thread
    watcher_thread = Thread(target=watch_summaries_collection, daemon=True)
    watcher_thread.start()
    
    logger.info("✅ AUTO-PROCESSING IS NOW LIVE ON RENDER!")
    logger.info("📊 System will automatically process new documents in real-time")
    logger.info("🔄 Processing pipeline: summaries → ML processing → processed_complaints")

# ----------------------------
# Health Check & Status Endpoints
# ----------------------------
@app.get("/")
async def root():
    return {
        "service": "Municipal AI Auto-Processing Service",
        "status": "running",
        "platform": "Render",
        "features": ["auto_processing", "real_time", "ml_pipeline"],
        "version": "2.0"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "auto_processing": "active",
        "change_streams": "monitoring",
        "platform": "Render",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/status")
def detailed_status():
    return {
        "service": "Municipal AI Auto-Processing",
        "status": "active",
        "processing_mode": "automatic",
        "trigger": "MongoDB Change Streams",
        "platform": "Render",
        "source_collection": f"{os.getenv('SOURCE_DB')}.{os.getenv('SOURCE_COLLECTION')}",
        "destination_collection": f"{os.getenv('DEST_DB')}.{os.getenv('DEST_COLLECTION')}",
        "features": {
            "language_detection": "enabled",
            "translation": "enabled", 
            "intent_classification": "enabled",
            "slot_extraction": "enabled",
            "text_summarization": "enabled",
            "real_time_processing": "enabled"
        }
    }

# ----------------------------
# Manual Processing Endpoints
# ----------------------------
@app.post("/process-batch")
def manual_batch_processing():
    """Manually trigger batch processing of unprocessed documents"""
    try:
        logger.info("🔄 Manual batch processing initiated...")
        
        # Connect to source collection
        client = MongoClient(os.getenv('SOURCE_MONGO_URI'))
        db = client[os.getenv('SOURCE_DB')]
        collection = db[os.getenv('SOURCE_COLLECTION')]
        
        # Find unprocessed documents (limit to prevent memory issues on Render)
        query = {"$or": [{"processed": {"$ne": True}}, {"processed": {"$exists": False}}]}
        documents = collection.find(query).limit(20)  # Reduced limit for Render
        
        processed_count = 0
        failed_count = 0
        
        for doc in documents:
            try:
                result = process_single_document(doc)
                if result:
                    processed_count += 1
                    # Mark as processed
                    mark_document_processed(doc["_id"], client)
                else:
                    failed_count += 1
            except Exception as e:
                failed_count += 1
                logger.error(f"❌ Failed to process document {doc.get('_id')}: {e}")
        
        logger.info(f"✅ Manual batch processing completed: {processed_count} processed, {failed_count} failed")
        
        return {
            "status": "success",
            "processed": processed_count,
            "failed": failed_count,
            "message": f"Batch processing completed. {processed_count} documents processed successfully."
        }
        
    except Exception as e:
        logger.error(f"❌ Manual batch processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")
    finally:
        try:
            client.close()
        except:
            pass

@app.post("/process_transcript", response_model=ComplaintOut)
def manual_process_transcript(payload: TranscriptIn):
    """Manually process a single transcript (original endpoint)"""
    try:
        raw = payload.transcript or ""
        asr_conf = float(payload.asr_confidence or 0.0)

        # Clean transcript
        raw = clean_text(raw)
        if not raw:
            raise HTTPException(status_code=400, detail="Transcript is empty.")

        logger.info(f"📝 Manual processing: {raw[:50]}...")

        # Process with full pipeline
        language, translated = translator.detect_and_translate(raw)
        intent, intent_conf = classify_intent(translated)
        slots = extract_slots(translated, intent_label=intent)
        
        # Calculate confidence
        final_conf = round((asr_conf * 0.6 + intent_conf * 0.4), 3)
        
        # Generate summaries
        short_summary = translated[:300] if translated else ""
        final_summary_text = generate_summary_text(
            translated,
            intent,
            slots.get("location", "N/A"),
            slots.get("severity", "medium"),
        )

        # Translate back if needed
        summary_out = translator.translate_back(short_summary, language) if language != "en" else short_summary
        final_summary_out = translator.translate_back(final_summary_text, language) if language != "en" else final_summary_text

        # Build document
        doc = copy.deepcopy(SCHEMA)
        doc.update({
            "department": slots.get("department", INTENT_TO_DEPT.get(intent, "General")),
            "intent": intent,
            "summary": summary_out,
            "severity": slots.get("severity", "medium"),
            "location": slots.get("location"),
            "name": slots.get("name"),
            "date": slots.get("date") or datetime.now().isoformat(),
            "language": language,
            "confidence_score": final_conf,
            "missing_fields": slots.get("missing_fields", []),
            "final_summary": final_summary_out,
            "raw_transcript": raw,
            "translated_text": translated if language != "en" else None,
            "processing_mode": "manual"
        })

        # Insert into database
        inserted_id = insert_complaint(doc)
        doc["_id"] = str(inserted_id)
        
        logger.info(f"✅ Manual processing completed: {inserted_id} | {intent} | {final_conf}")
        return doc

    except HTTPException as http_exc:
        raise http_exc
    except Exception as exc:
        logger.error(f"❌ Manual processing error: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ----------------------------
# Application Entry Point
# ----------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"🚀 Starting server on Render, port {port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")