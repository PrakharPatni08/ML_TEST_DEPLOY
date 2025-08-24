# models/intent_classifier.py
from transformers import pipeline
from config.settings import INTENT_LABELS
from utils.logger import get_logger

logger = get_logger(__name__)

# Ensure GetStatus is part of intent labels
if "GetStatus" not in INTENT_LABELS:
    INTENT_LABELS.append("GetStatus")

try:
    classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
    logger.info("Zero-shot intent classifier loaded successfully.")
except Exception as e:
    logger.error(f"Failed to load zero-shot classifier: {e}")
    classifier = None


def classify_intent(text: str):
    """
    Classify user text into an intent.
    Returns: (intent_label, confidence_score)
    """
    if not text:
        return "Other", 0.0

    txt = text.lower()

    # -------------------
    # Fallback rules if model not available
    # -------------------
    if classifier is None:
        if any(word in txt for word in ["status", "track", "complaint id", "ticket", "application number"]):
            return "GetStatus", 0.9
        if any(word in txt for word in ["water", "pipeline", "paani"]):
            return "Water Supply", 0.9
        if any(word in txt for word in ["garbage", "safai", "trash", "kachra"]):
            return "Garbage", 0.9
        if any(word in txt for word in ["pothole", "road", "gaddha"]):
            return "Road", 0.9
        if any(word in txt for word in ["light", "streetlight", "bijli", "lamp"]):
            return "Streetlight", 0.9
        if any(word in txt for word in ["electric", "power", "current"]):
            return "Electricity", 0.9
        return "Other", 0.4

    # -------------------
    # Transformer model classification
    # -------------------
    try:
        res = classifier(text, candidate_labels=INTENT_LABELS)
        label = res["labels"][0]
        score = float(res["scores"][0])
        logger.info(f"Intent classified as {label} with confidence {score:.2f}")
        return label, score
    except Exception as e:
        logger.error(f"Intent classification failed: {e}")
        return "Other", 0.0

# ...existing code...

class IntentClassifier:
    @staticmethod
    def classify(text: str):
        return classify_intent(text)
# ...existing code...