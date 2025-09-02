# from transformers import pipeline
# from utils.logger import get_logger

# logger = get_logger(__name__)

# # Load summarizer (small & fast model)
# try:
#     summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
#     logger.info("Summarizer model loaded successfully.")
# except Exception as e:
#     logger.warning(f"Summarizer model not loaded or failed: {e}")
#     summarizer = None

# def generate_summary_text(translated_text: str, intent: str, location: str, severity: str) -> str:
#     """
#     Generate a short natural confirmation summary.
#     - If intent = GetStatus → summary asks user to confirm status check request.
#     - If intent = Reporting → summary confirms complaint report.
#     Uses summarizer model if available, else falls back to a safe template.
#     """

#     # Default safe values
#     location = location or "your area"
#     severity = severity or "moderate"

#     # Template fallback (safe & fast)
#     if intent == "GetStatus":
#         template = "You want to check the status of your complaint. Please confirm."
#     else:
#         template = f"You are reporting a {severity} severity {intent} at {location}. Please confirm."

#     # Use fallback if summarizer unavailable, text too short, or no translated text
#     if summarizer is None or not translated_text or len(translated_text.split()) < 6:
#         return template

#     # Build summarizer prompt
#     if intent == "GetStatus":
#         prompt = (
#             f"User request: {translated_text}\n"
#             "Generate a short polite confirmation asking if they want to check complaint status."
#         )
#     else:
#         prompt = (
#             f"Complaint: {translated_text}\n"
#             f"Intent: {intent}\n"
#             f"Location: {location}\n"
#             f"Severity: {severity}\n"
#             f"Generate a short polite confirmation summary."
#         )

#     try:
#         input_length = len(prompt.split())
#         max_length = min(50, input_length)
#         min_length = min(12, max_length - 1) if max_length > 12 else max_length

#         out = summarizer(prompt, max_length=max_length, min_length=min_length, do_sample=False)
#         text = out[0]["summary_text"].strip()

#         # Post-processing for reporting complaints
#         if intent != "GetStatus":
#             if location.lower() not in text.lower():
#                 text = f"{text} Location: {location}."
#             if severity.lower() not in text.lower():
#                 text = f"{text} Severity: {severity}."

#         # Ensure polite confirmation
#         if not text.endswith("Please confirm."):
#             text = f"{text} Please confirm."

#         return text

#     except Exception as e:
#         logger.warning(f"Summarization failed: {e}")
#         return template

from utils.logger import get_logger

logger = get_logger(__name__)

def generate_summary_text(translated_text: str, intent: str, location: str, severity: str) -> str:
    """Generate summary using template-based approach"""
    try:
        # Clean and truncate text
        clean_text = translated_text.strip()[:500]  # Limit length
        
        # Template-based summary generation
        if location and location != "N/A":
            location_part = f" at {location}"
        else:
            location_part = ""
        
        severity_desc = {
            "high": "URGENT",
            "medium": "Standard",
            "low": "Minor"
        }.get(severity, "Standard")
        
        intent_desc = {
            "WaterSupply": "water supply issue",
            "Drainage": "drainage problem", 
            "RoadMaintenance": "road maintenance issue",
            "Electricity": "electrical problem",
            "GarbageCollection": "waste collection issue",
            "GetStatus": "status inquiry"
        }.get(intent, "general complaint")
        
        # Generate structured summary
        summary = f"[{severity_desc}] {intent_desc.title()}{location_part}. "
        
        # Add key details from original text
        key_phrases = extract_key_phrases(clean_text)
        if key_phrases:
            summary += f"Details: {key_phrases[:200]}..."
        else:
            summary += f"Details: {clean_text[:200]}..."
        
        logger.info(f"📝 Generated summary: {summary[:100]}...")
        return summary
        
    except Exception as e:
        logger.error(f"❌ Summary generation error: {e}")
        return f"[{severity}] {intent} complaint{location_part}. {translated_text[:200]}..."

def extract_key_phrases(text: str) -> str:
    """Extract key phrases using simple keyword filtering"""
    # Important keywords to highlight
    important_words = [
        "broken", "leak", "overflow", "blockage", "urgent", "emergency",
        "not working", "damaged", "repair", "fix", "problem", "issue"
    ]
    
    sentences = text.split('.')
    key_sentences = []
    
    for sentence in sentences[:3]:  # Only check first 3 sentences
        sentence = sentence.strip()
        if any(word in sentence.lower() for word in important_words):
            key_sentences.append(sentence)
    
    return '. '.join(key_sentences)