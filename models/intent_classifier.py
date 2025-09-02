# # models/intent_classifier.py
# from transformers import pipeline
# from config.settings import INTENT_LABELS
# from utils.logger import get_logger

# logger = get_logger(__name__)

# # Ensure GetStatus is part of intent labels
# if "GetStatus" not in INTENT_LABELS:
#     INTENT_LABELS.append("GetStatus")

# try:
#     classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
#     logger.info("Zero-shot intent classifier loaded successfully.")
# except Exception as e:
#     logger.error(f"Failed to load zero-shot classifier: {e}")
#     classifier = None


# def classify_intent(text: str):
#     """
#     Classify user text into an intent.
#     Returns: (intent_label, confidence_score)
#     """
#     if not text:
#         return "Other", 0.0

#     txt = text.lower()

#     # -------------------
#     # Fallback rules if model not available
#     # -------------------
#     if classifier is None:
#         if any(word in txt for word in ["status", "track", "complaint id", "ticket", "application number"]):
#             return "GetStatus", 0.9
#         if any(word in txt for word in ["water", "pipeline", "paani"]):
#             return "Water Supply", 0.9
#         if any(word in txt for word in ["garbage", "safai", "trash", "kachra"]):
#             return "Garbage", 0.9
#         if any(word in txt for word in ["pothole", "road", "gaddha"]):
#             return "Road", 0.9
#         if any(word in txt for word in ["light", "streetlight", "bijli", "lamp"]):
#             return "Streetlight", 0.9
#         if any(word in txt for word in ["electric", "power", "current"]):
#             return "Electricity", 0.9
#         return "Other", 0.4

#     # -------------------
#     # Transformer model classification
#     # -------------------
#     try:
#         res = classifier(text, candidate_labels=INTENT_LABELS)
#         label = res["labels"][0]
#         score = float(res["scores"][0])
#         logger.info(f"Intent classified as {label} with confidence {score:.2f}")
#         return label, score
#     except Exception as e:
#         logger.error(f"Intent classification failed: {e}")
#         return "Other", 0.0

# # ...existing code...

# class IntentClassifier:
#     @staticmethod
#     def classify(text: str):
#         return classify_intent(text)
# # ...existing code...
import re
from config.settings import INTENT_LABELS
from utils.logger import get_logger

logger = get_logger(__name__)

# Lightweight keyword-based intent classification
INTENT_KEYWORDS = {
    "WaterSupply": ["water", "tap", "pipeline", "leak", "pressure", "supply", "shortage", "contamination"],
    "Drainage": ["drain", "sewage", "overflow", "blockage", "manhole", "waste", "flood"],
    "RoadMaintenance": ["road", "pothole", "crack", "traffic", "street", "signal", "repair"],
    "Electricity": ["power", "electricity", "light", "pole", "wire", "outage", "meter"],
    "GarbageCollection": ["garbage", "waste", "trash", "collection", "bin", "disposal", "cleaning"],
    "GetStatus": ["status", "update", "progress", "when", "completed", "check", "follow up"]
}

def classify_intent(text: str):
    """Lightweight intent classification using keyword matching"""
    try:
        text_lower = text.lower()
        intent_scores = {}
        
        for intent, keywords in INTENT_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                # Count keyword occurrences with word boundaries
                matches = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text_lower))
                score += matches
            
            if score > 0:
                intent_scores[intent] = score
        
        if intent_scores:
            # Get intent with highest score
            best_intent = max(intent_scores, key=intent_scores.get)
            max_score = intent_scores[best_intent]
            
            # Calculate confidence (normalize score)
            confidence = min(max_score / 3.0, 1.0)  # Cap at 1.0
            
            logger.info(f"🎯 Intent: {best_intent} (confidence: {confidence:.3f})")
            return best_intent, confidence
        else:
            # Default fallback
            logger.info("🎯 No specific intent found, defaulting to General")
            return "General", 0.5
            
    except Exception as e:
        logger.error(f"❌ Intent classification error: {e}")
        return "General", 0.3

class IntentClassifier:
    """Lightweight intent classifier class"""
    def __init__(self):
        self.model_name = "keyword_based"
        logger.info("✅ Lightweight Intent Classifier initialized")
    
    def predict(self, text):
        return classify_intent(text)