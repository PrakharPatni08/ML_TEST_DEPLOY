from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
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
# Health Check
# ----------------------------
@app.get("/health")
def health():
    return {"status": "ok"}

# ----------------------------
# Main Processing Endpoint
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
        logger.info(f"Intent={intent} conf={intent_conf}")

        # Step 3: Slot extraction
        slots = extract_slots(translated, intent_label=intent)
        logger.info(f"Extracted slots={slots}")

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

        # Step 6: Build document
        doc = {
            "department": slots.get("department", INTENT_TO_DEPT.get(intent, "General")),
            "intent": intent,
            "summary": short_summary,
            "severity": slots.get("severity", "medium"),
            "location": slots.get("location"),
            "name": slots.get("name"),
            "date": slots.get("date"),
            "language": language,
            "confidence_score": final_conf,
            "missing_fields": slots.get("missing_fields", []),
            "final_summary": final_summary_text,
            "raw_transcript": raw,
            "translated_text": translated if language != "en" else None,
        }

        # Step 7: Handle low confidence + missing fields
        if final_conf < CONFIDENCE_THRESHOLD and doc["missing_fields"]:
            logger.info("Low confidence & missing fields -> returning doc with clarification needed.")

        # Step 8: Insert into DB
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

# ----------------------------
# Multiple Transcripts Endpoint
# ----------------------------
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

        doc = {
            "department": slots.get("department", INTENT_TO_DEPT.get(intent, "General")),
            "intent": intent,
            "summary": short_summary,
            "severity": slots.get("severity", "medium"),
            "location": slots.get("location"),
            "name": slots.get("name"),
            "date": slots.get("date"),
            "language": language,
            "confidence_score": final_conf,
            "missing_fields": slots.get("missing_fields", []),
            "final_summary": final_summary_text,
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