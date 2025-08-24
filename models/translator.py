# models/translator.py
from langdetect import detect, DetectorFactory
from deep_translator import GoogleTranslator
from utils.logger import get_logger

DetectorFactory.seed = 0
logger = get_logger()

class Translator:
    def __init__(self, target_lang="en"):
        self.target_lang = target_lang

    def detect_language(self, text: str) -> str:
        try:
            lang = detect(text)
            return lang
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
            return "unknown"

    def translate(self, text: str, src_lang: str) -> str:
        """
        Translate to English for pipeline processing if not already English.
        Falls back to original text on failure.
        """
        if not text:
            return ""
        if src_lang and src_lang.startswith("en"):
            return text
        try:
            translated = GoogleTranslator(source=src_lang, target=self.target_lang).translate(text)
            return translated
        except Exception as e:
            logger.warning(f"Translation failed: {e} — returning original text")
            return text

    def detect_and_translate(self, text: str):
        lang = self.detect_language(text)
        en = self.translate(text, lang)
        return lang, en
