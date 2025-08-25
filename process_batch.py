from utils.database import fetch_raw_analysis, insert_complaint
from models.translator import Translator
from models.intent_classifier import classify_intent
from models.slot_filler import extract_slots
from models.summarizer import generate_summary_text
from utils.preprocessing import clean_text
from config.settings import INTENT_TO_DEPT, CONFIDENCE_THRESHOLD

translator = Translator()

def process_and_store(transcript):
    raw = clean_text(transcript)
    if not raw:
        return None

    language, translated = translator.detect_and_translate(raw)
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
        "raw_transcript": raw,
        "translated_text": translated if language != "en" else None,
    }
    inserted_id = insert_complaint(doc)
    return inserted_id

def main():
    transcripts = fetch_raw_analysis()
    for transcript in transcripts:
        result = process_and_store(transcript)
        print(f"Processed and stored complaint with ID: {result}")

if __name__ == "__main__":
    main()