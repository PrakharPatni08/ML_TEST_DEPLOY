import re
import unicodedata

def combine_json_documents(json_list):
    """
    Concatenates all 'transcript' fields from a list of JSON objects into one string.
    Returns a dict with the combined transcript.
    """
    combined_transcript = " ".join(doc["transcript"] for doc in json_list if "transcript" in doc)
    return {"transcript": combined_transcript}

def clean_text(text: str) -> str:
    """Basic cleaning: normalize unicode and whitespace."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text
