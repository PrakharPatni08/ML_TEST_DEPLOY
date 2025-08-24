# config/settings.py (update the lists/mapping)
import os
from dotenv import load_dotenv

load_dotenv()

SOURCE_MONGO_URI = os.getenv("SOURCE_MONGO_URI")
SOURCE_DB = os.getenv("SOURCE_DB")
SOURCE_COLLECTION = os.getenv("SOURCE_COLLECTION")

DEST_MONGO_URI = os.getenv("DEST_MONGO_URI")
DEST_DB = os.getenv("DEST_DB")
DEST_COLLECTION = os.getenv("DEST_COLLECTION")

CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.75"))
LOG_FILE = os.getenv("LOG_FILE", "logs/app.log")

INTENT_LABELS = [
    "Water Supply", "Garbage", "Road", "Streetlight", "Electricity",
    "Drainage", "Traffic", "Other",
    "GetStatus", "Greetings", "Thanks", "ComplaintHistory"
]

LOG_FILE = "logs/app.log"

INTENT_TO_DEPT = {
    # Complaint/reporting intents
    "Water Supply": "Water Department",
    "Garbage": "Sanitation",
    "Road": "Public Works",
    "Streetlight": "Electrical",
    "Electricity": "Electrical",
    "Drainage": "Sanitation",
    "Traffic": "Traffic Department",
    "Other": "General",
    # Query/non-report intents (map to General or specific handlers)
    "GetStatus": "General",
    "Greetings": "General",
    "Thanks": "General",
    "ComplaintHistory": "General"
}
