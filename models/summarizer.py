from transformers import pipeline
from utils.logger import get_logger

logger = get_logger(__name__)

# Load summarizer (small & fast model)
try:
    summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
    logger.info("Summarizer model loaded successfully.")
except Exception as e:
    logger.warning(f"Summarizer model not loaded or failed: {e}")
    summarizer = None

def generate_summary_text(translated_text: str, intent: str, location: str, severity: str) -> str:
    """
    Generate a short natural confirmation summary.
    - If intent = GetStatus → summary asks user to confirm status check request.
    - If intent = Reporting → summary confirms complaint report.
    Uses summarizer model if available, else falls back to a safe template.
    """

    # Default safe values
    location = location or "your area"
    severity = severity or "moderate"

    # Template fallback (safe & fast)
    if intent == "GetStatus":
        template = "You want to check the status of your complaint. Please confirm."
    else:
        template = f"You are reporting a {severity} severity {intent} at {location}. Please confirm."

    # Use fallback if summarizer unavailable, text too short, or no translated text
    if summarizer is None or not translated_text or len(translated_text.split()) < 6:
        return template

    # Build summarizer prompt
    if intent == "GetStatus":
        prompt = (
            f"User request: {translated_text}\n"
            "Generate a short polite confirmation asking if they want to check complaint status."
        )
    else:
        prompt = (
            f"Complaint: {translated_text}\n"
            f"Intent: {intent}\n"
            f"Location: {location}\n"
            f"Severity: {severity}\n"
            f"Generate a short polite confirmation summary."
        )

    try:
        input_length = len(prompt.split())
        max_length = min(50, input_length)
        min_length = min(12, max_length - 1) if max_length > 12 else max_length

        out = summarizer(prompt, max_length=max_length, min_length=min_length, do_sample=False)
        text = out[0]["summary_text"].strip()

        # Post-processing for reporting complaints
        if intent != "GetStatus":
            if location.lower() not in text.lower():
                text = f"{text} Location: {location}."
            if severity.lower() not in text.lower():
                text = f"{text} Severity: {severity}."

        # Ensure polite confirmation
        if not text.endswith("Please confirm."):
            text = f"{text} Please confirm."

        return text

    except Exception as e:
        logger.warning(f"Summarization failed: {e}")
        return template