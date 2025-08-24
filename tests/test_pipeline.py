# tests/test_pipeline.py
from models.translator import Translator
from models.intent_classifier import classify_intent
from models.slot_filler import extract_slots
from models.summarizer import generate_summary_text

def test_translator():
    t = Translator()
    lang, en = t.detect_and_translate("There is a water pipeline broken near Rajiv Chowk and it's urgent.")
    assert lang.startswith("en")
    assert "water" in en.lower()

def test_intent_and_slots():
    text = "There is a water pipeline broken near Rajiv Chowk and it's urgent."
    intent, conf = classify_intent(text)
    assert intent in ["Water Supply", "Other"]
    slots = extract_slots(text, intent_label=intent)
    assert "location" in slots
    assert slots["severity"] in ["high", "medium", "low"]

def test_summarizer():
    s = generate_summary_text("There is a water pipeline broken near Rajiv Chowk and it's urgent.", "Water Supply", "Rajiv Chowk", "high")
    assert isinstance(s, str)
    assert len(s) > 10

def test_getstatus_extraction():
    text = "Check status of complaint MUN-2025-000234"
    # reuse translator (will return english)
    t = Translator()
    lang, en = t.detect_and_translate(text)
    intent, conf = classify_intent(en)
    assert intent == "GetStatus"
    slots = extract_slots(en, intent_label=intent)
    assert slots.get("complaint_id") is not None
