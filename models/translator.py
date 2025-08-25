import requests
from langdetect import detect, DetectorFactory
from utils.logger import get_logger

DetectorFactory.seed = 0
logger = get_logger()

GEMINI_API_KEY = "AIzaSyDcp0X3yeLFxEu6F-hfqIQ8W9IEc6xSbxM"
GEMINI_TRANSLATE_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"

class Translator:
    def __init__(self, default_target_lang="en"):
        self.default_target_lang = default_target_lang

    def detect_language(self, text: str) -> str:
        try:
            lang = detect(text)
            return lang
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
            return "unknown"

    def gemini_translate(self, text: str, target_lang: str) -> str:
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"Translate this to {target_lang}: {text}"}
                    ]
                }
            ]
        }
        params = {"key": GEMINI_API_KEY}
        try:
            response = requests.post(GEMINI_TRANSLATE_URL, json=payload, params=params, headers=headers)
            response.raise_for_status()
            result = response.json()
            translated = result["candidates"][0]["content"]["parts"][0]["text"]
            return translated
        except Exception as e:
            logger.warning(f"Gemini translation failed: {e}")
            return text

    def detect_and_translate(self, text: str):
        lang = self.detect_language(text)
        translated = self.gemini_translate(text, "English") if lang != "en" else text
        return lang, translated

    def translate_back(self, text: str, original_lang: str) -> str:
        if original_lang == "en":
            return text
        return self.gemini_translate(text, original_lang)