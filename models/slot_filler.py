# import re
# import spacy
# import os
# from datetime import datetime
# from config.settings import INTENT_TO_DEPT
# from utils.logger import get_logger

# logger = get_logger(__name__)

# # Load spaCy model (for NER)
# nlp = spacy.load("en_core_web_sm")

# # Load gazetteer for known locations (from data/gazetteer.csv)
# GAZETTEER_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "gazetteer.csv")
# KNOWN_LOCATIONS = set()
# if os.path.exists(GAZETTEER_PATH):
#     with open(GAZETTEER_PATH, "r", encoding="utf-8") as f:
#         for line in f:
#             KNOWN_LOCATIONS.add(line.strip().lower())  # Use .lower() for case-insensitive matching

# # ...rest of your code...

# def extract_complaint_id(text: str):
#     """
#     Tries to find a complaint/ticket id in free text.
#     Matches patterns like: MUN-2025-000234, ABC12345, or plain digits 12345 (4-8 digits).
#     Returns the matched string or None.
#     """
#     if not text:
#         return None

#     patterns = [
#         r"\b[A-Z]{1,5}-\d{3,8}\b",  # e.g., MUN-2025-000234
#         r"\b[A-Z]{2,6}\d{3,6}\b",   # e.g., ABC12345
#         r"\b\d{4,8}\b"              # plain numeric id 12345
#     ]
#     for p in patterns:
#         m = re.search(p, text, flags=re.IGNORECASE)
#         if m:
#             return m.group(0)
#     return None

# def extract_slots(text: str, intent_label: str):
#     """
#     Extracts structured slots from raw text transcript.
#     Returns a dict with department, location, severity, name, date, missing_fields, complaint_id.
#     """

#     doc = nlp(text)
#     missing = []

#     # --- Map intent → department ---
#     department = INTENT_TO_DEPT.get(intent_label, "General")

#     # --- Extract location ---
#     location = None
#     # Gazetteer match (case-insensitive, multi-word)
#     lowered_text = text.lower()
#     for loc in KNOWN_LOCATIONS:
#         if loc in lowered_text:
#             location = loc.title()  # Return with title case for readability
#             break

#     # If not found, fallback to NER
#     if not location:
#         for ent in doc.ents:
#             if ent.label_ in ["GPE", "LOC", "FACILITY"]:
#                 location = ent.text
#                 break

#     if not location:
#         missing.append("location")

#     # --- Extract severity ---
#     severity = None
#     if any(word in lowered_text for word in ["urgent", "immediately", "serious", "critical", "danger"]):
#         severity = "High"
#     elif any(word in lowered_text for word in ["soon", "moderate", "normal"]):
#         severity = "Medium"
#     else:
#         severity = "Low"

#     # --- Extract name (PERSON entity) ---
#     name = None
#     for ent in doc.ents:
#         if ent.label_ == "PERSON":
#             name = ent.text
#             break
#     if not name:
#         missing.append("name")

#     # --- Extract date ---
#     date = None
#     for ent in doc.ents:
#         if ent.label_ == "DATE":
#             date = ent.text
#             break
#     if not date:
#         date = datetime.now().strftime("%Y-%m-%d")

#     # --- Handle GetStatus intent (look for complaint ID) ---
#     complaint_id = None
#     if intent_label == "GetStatus":
#         complaint_id = extract_complaint_id(text)
#         if not complaint_id:
#             if "complaint_id" not in missing:
#                 missing.append("complaint_id")

#     logger.info(
#         "Extracted slots -> dept: %s, location: %s, severity: %s, name: %s, date: %s, complaint_id: %s, missing: %s",
#         department, location, severity, name, date, complaint_id, missing
#     )

#     return {
#         "department": department,
#         "location": location,
#         "severity": severity,
#         "name": name,
#         "date": date,
#         "missing_fields": missing,
#         "complaint_id": complaint_id
#     }
import re
import os
import csv
from datetime import datetime
from config.settings import INTENT_TO_DEPT
from utils.logger import get_logger

logger = get_logger(__name__)

# Load gazetteer for known locations
GAZETTEER_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "gazetteer.csv")
KNOWN_LOCATIONS = set()

if os.path.exists(GAZETTEER_PATH):
    try:
        with open(GAZETTEER_PATH, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)  # Skip header
            for row in reader:
                if row:
                    KNOWN_LOCATIONS.add(row[0].lower())
        logger.info(f"✅ Loaded {len(KNOWN_LOCATIONS)} known locations")
    except Exception as e:
        logger.warning(f"⚠️ Could not load gazetteer: {e}")

# Severity keywords
SEVERITY_KEYWORDS = {
    "high": ["urgent", "emergency", "critical", "severe", "major", "serious"],
    "medium": ["moderate", "regular", "normal", "standard"],
    "low": ["minor", "small", "slight", "little"]
}

def extract_slots(text: str, intent_label: str = None) -> dict:
    """Lightweight slot extraction using regex patterns"""
    try:
        text_lower = text.lower()
        slots = {}
        
        # Extract location using gazetteer and common patterns
        location = extract_location(text_lower)
        if location:
            slots["location"] = location
        
        # Extract severity
        severity = extract_severity(text_lower)
        slots["severity"] = severity
        
        # Extract name (simple pattern)
        name = extract_name(text)
        if name:
            slots["name"] = name
        
        # Extract date/time references
        date_ref = extract_date_reference(text_lower)
        if date_ref:
            slots["date"] = date_ref
        
        # Set department based on intent
        if intent_label:
            slots["department"] = INTENT_TO_DEPT.get(intent_label, "General")
        
        # Identify missing critical fields
        missing_fields = []
        if not slots.get("location"):
            missing_fields.append("location")
        if not slots.get("name"):
            missing_fields.append("name")
        
        slots["missing_fields"] = missing_fields
        
        logger.info(f"📊 Extracted slots: {slots}")
        return slots
        
    except Exception as e:
        logger.error(f"❌ Slot extraction error: {e}")
        return {"severity": "medium", "missing_fields": ["location", "name"]}

def extract_location(text_lower: str) -> str:
    """Extract location using gazetteer and patterns"""
    # Check gazetteer first
    for location in KNOWN_LOCATIONS:
        if location in text_lower:
            return location.title()
    
    # Common location patterns
    location_patterns = [
        r'(?:near|at|in|around|by)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:area|road|street|colony|sector)',
        r'(?:sector|block|phase)\s+([A-Z0-9]+)'
    ]
    
    for pattern in location_patterns:
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            return match.group(1).title()
    
    return None

def extract_severity(text_lower: str) -> str:
    """Extract severity level"""
    for severity, keywords in SEVERITY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                return severity
    return "medium"  # Default

def extract_name(text: str) -> str:
    """Extract person name using simple patterns"""
    # Look for "my name is" or "I am" patterns
    name_patterns = [
        r'(?:my name is|i am|this is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'([A-Z][a-z]+)\s+(?:here|speaking|calling)'
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).title()
    
    return None

def extract_date_reference(text_lower: str) -> str:
    """Extract date/time references"""
    time_patterns = [
        r'(today|yesterday|tomorrow)',
        r'(this morning|this evening|this afternoon)',
        r'(\d{1,2}:\d{2}\s*(?:am|pm)?)'
    ]
    
    for pattern in time_patterns:
        match = re.search(pattern, text_lower)
        if match:
            return match.group(1)
    
    return datetime.now().strftime("%Y-%m-%d %H:%M")