# nlp/transliterator.py
# Handles Roman to Kannada script transliteration.
# Many users type Kannada phonetically in English.
# Example: 'naanu kannada maatanaaduttene' -> 'ನಾನು ಕನ್ನಡ ಮಾತನಾಡುತ್ತೇನೆ'

from loguru import logger

# ── Check IndicXlit availability ─────────────────────────────
try:
    from ai4bharat.transliteration import XlitEngine
    INDIC_XLIT_AVAILABLE = True
    logger.info("IndicXlit loaded successfully.")
except ImportError:
    INDIC_XLIT_AVAILABLE = False
    logger.warning(
        "IndicXlit not found — using manual transliteration map. "
        "For better results install: pip install ai4bharat-transliteration"
    )


# ── Manual transliteration map ───────────────────────────────
# Common Kannada legal words typed in Roman script.
# Used as fallback when IndicXlit is not available.

ROMAN_TO_KANNADA_MAP = {
    # Common words
    "naanu":          "ನಾನು",
    "neevu":          "ನೀವು",
    "avaru":          "ಅವರು",
    "ivaru":          "ಇವರು",
    "enu":            "ಏನು",
    "hege":           "ಹೇಗೆ",
    "yaake":          "ಯಾಕೆ",
    "elli":           "ಎಲ್ಲಿ",
    "yaavaga":        "ಯಾವಾಗ",
    "madabeku":       "ಮಾಡಬೇಕು",
    "madabahuda":     "ಮಾಡಬಹುದು",
    "illa":           "ಇಲ್ಲ",
    "ide":            "ಇದೆ",
    "aguttade":       "ಆಗುತ್ತದೆ",
    "hogabeku":       "ಹೋಗಬೇಕು",
    "kodabeku":       "ಕೊಡಬೇಕು",
    "tegedukondaru":  "ತೆಗೆದುಕೊಂಡರು",
    "bandaru":        "ಬಂದರು",
    "hodaru":         "ಹೋದರು",

    # Legal terms in Roman
    "section":        "ಸೆಕ್ಷನ್",
    "vibhaga":        "ವಿಭಾಗ",
    "shiksha":        "ಶಿಕ್ಷೆ",
    "danda":          "ದಂಡ",
    "jaamiinu":       "ಜಾಮೀನು",
    "jail":           "ಜೈಲು",
    "nyayalaya":      "ನ್ಯಾಯಾಲಯ",
    "vakeel":         "ವಕೀಲ",
    "police":         "ಪೊಲೀಸ್",
    "thaane":         "ಠಾಣೆ",
    "arrest":         "ಬಂಧನ",
    "bandhan":        "ಬಂಧನ",
    "hakkugalu":      "ಹಕ್ಕುಗಳು",
    "hakku":          "ಹಕ್ಕು",
    "duru":           "ದೂರು",
    "arji":           "ಅರ್ಜಿ",
    "teerpu":         "ತೀರ್ಪು",
    "saakshi":        "ಸಾಕ್ಷಿ",
    "saakshya":       "ಸಾಕ್ಷ್ಯ",
    "apradha":        "ಅಪರಾಧ",
    "aropi":          "ಆರೋಪಿ",
    "magistrate":     "ಮ್ಯಾಜಿಸ್ಟ್ರೇಟ್",
    "nyayadhesha":    "ನ್ಯಾಯಾಧೀಶ",
    "FIR":            "ಪ್ರಥಮ ಮಾಹಿತಿ ವರದಿ",
    "kolla":          "ಕೊಲೆ",
    "hatye":          "ಹತ್ಯೆ",
    "kallatana":      "ಕಳ್ಳತನ",
    "daroDE":         "ದರೋಡೆ",
    "mosa":           "ಮೋಸ",
    "vanchane":       "ವಂಚನೆ",
    "atikramana":     "ಅತಿಕ್ರಮಣ",
    "halle":          "ಹಲ್ಲೆ",
    "bedrike":        "ಬೆದರಿಕೆ",
    "aasti":          "ಆಸ್ತಿ",
    "sarkara":        "ಸರ್ಕಾರ",
    "rajya":          "ರಾಜ್ಯ",
    "RTI":            "ಮಾಹಿತಿ ಹಕ್ಕು",
    "mahiti hakku":   "ಮಾಹಿತಿ ಹಕ್ಕು",
    "grahaka":        "ಗ್ರಾಹಕ",
    "badige":         "ಬಾಡಿಗೆ",
    "maalik":         "ಮಾಲೀಕ",
    "sampatti":       "ಆಸ್ತಿ",
}


# ── IndicXlit engine (loaded once) ──────────────────────────
_xlit_engine = None


def _get_xlit_engine():
    """Load IndicXlit engine once and reuse."""
    global _xlit_engine
    if _xlit_engine is None and INDIC_XLIT_AVAILABLE:
        try:
            logger.info("Loading IndicXlit engine for Kannada...")
            _xlit_engine = XlitEngine("kn", beam_width=10)
            logger.success("IndicXlit engine ready.")
        except Exception as e:
            logger.error(f"IndicXlit engine failed to load: {e}")
    return _xlit_engine


# ── Core functions ───────────────────────────────────────────
def is_roman_script(text: str) -> bool:
    """
    Detect if text is written in Roman (ASCII) script.
    Returns True if more than 80% of alphabetic chars are ASCII.

    Args:
        text : Input text string

    Returns:
        True if text is mostly Roman script

    Example:
        >>> is_roman_script("naanu hoguttene")
        True
        >>> is_roman_script("ನಾನು ಹೋಗುತ್ತೇನೆ")
        False
        >>> is_roman_script("IPC section 302 enu")
        True
    """
    if not text:
        return False

    alpha_chars = [c for c in text if c.isalpha()]
    if not alpha_chars:
        return False

    ascii_count = sum(1 for c in alpha_chars if ord(c) < 128)
    return (ascii_count / len(alpha_chars)) > 0.8


def roman_to_kannada(text: str) -> str:
    """
    Convert Roman script Kannada input to native Kannada script.
    Uses IndicXlit if available, else falls back to manual map.

    Args:
        text : Roman script input text

    Returns:
        Kannada script text

    Example:
        >>> roman_to_kannada("naanu nyayalayakke hoguttene")
        'ನಾನು ನ್ಯಾಯಾಲಯಕ್ಕೆ ಹೋಗುತ್ತೇನೆ'
    """
    if not text or not text.strip():
        return text

    # Try IndicXlit first (best quality)
    engine = _get_xlit_engine()
    if engine:
        try:
            result = engine.translit_sentence(text)
            logger.debug(f"IndicXlit: '{text}' -> '{result}'")
            return result
        except Exception as e:
            logger.warning(f"IndicXlit failed: {e}. Using manual map.")

    # Fallback — manual word-by-word replacement
    return _manual_transliterate(text)


def _manual_transliterate(text: str) -> str:
    """
    Manual transliteration using the predefined word map.
    Replaces known Roman words with Kannada equivalents.

    Args:
        text : Roman script input

    Returns:
        Partially transliterated text
    """
    words  = text.split()
    result = []

    for word in words:
        # Check lowercase version in map
        lower = word.lower().strip(".,?!")
        if lower in ROMAN_TO_KANNADA_MAP:
            result.append(ROMAN_TO_KANNADA_MAP[lower])
            logger.debug(f"Mapped: '{word}' -> '{ROMAN_TO_KANNADA_MAP[lower]}'")
        else:
            # Keep original if not in map
            result.append(word)

    return " ".join(result)


def detect_mixed_script(text: str) -> dict:
    """
    Detect what scripts are present in the text.

    Args:
        text : Input text

    Returns:
        Dictionary with script analysis

    Example:
        >>> detect_mixed_script("Section 302 ಏನು?")
        {
            'has_roman': True,
            'has_kannada': True,
            'is_mixed': True,
            'roman_ratio': 0.6,
            'kannada_ratio': 0.4
        }
    """
    if not text:
        return {
            "has_roman":    False,
            "has_kannada":  False,
            "is_mixed":     False,
            "roman_ratio":  0.0,
            "kannada_ratio":0.0,
        }

    total_chars   = max(len(text.replace(" ", "")), 1)
    roman_chars   = sum(1 for c in text if c.isascii() and c.isalpha())
    kannada_chars = sum(1 for c in text if "\u0C80" <= c <= "\u0CFF")

    roman_ratio   = round(roman_chars   / total_chars, 2)
    kannada_ratio = round(kannada_chars / total_chars, 2)

    return {
        "has_roman":    roman_ratio   > 0.1,
        "has_kannada":  kannada_ratio > 0.1,
        "is_mixed":     roman_ratio   > 0.1 and kannada_ratio > 0.1,
        "roman_ratio":  roman_ratio,
        "kannada_ratio":kannada_ratio,
    }


def preprocess_query(text: str) -> str:
    """
    Full preprocessing for a user query.
    If text is in Roman script, convert to Kannada.
    If already in Kannada, return as-is.

    Args:
        text : Raw user input

    Returns:
        Kannada script text ready for NLP processing

    Example:
        >>> preprocess_query("section 302 enu")
        'ಸೆಕ್ಷನ್ 302 ಏನು'
        >>> preprocess_query("IPC ಸೆಕ್ಷನ್ 302 ಏನು?")
        'IPC ಸೆಕ್ಷನ್ 302 ಏನು?'
    """
    if not text:
        return text

    script_info = detect_mixed_script(text)

    # Pure Roman — fully transliterate
    if script_info["has_roman"] and not script_info["has_kannada"]:
        logger.info("Pure Roman input detected — transliterating to Kannada.")
        return roman_to_kannada(text)

    # Mixed — transliterate Roman parts only
    if script_info["is_mixed"]:
        logger.info("Mixed script detected — partial transliteration.")
        return _transliterate_mixed(text)

    # Already Kannada — return as-is
    return text


def _transliterate_mixed(text: str) -> str:
    """
    Handle mixed script text.
    Transliterates only the Roman words, keeps Kannada words intact.

    Args:
        text : Mixed Kannada + Roman text

    Returns:
        Unified Kannada text
    """
    words  = text.split()
    result = []

    for word in words:
        clean = word.strip(".,?!").lower()
        # Check if this word is Kannada
        has_kannada = any("\u0C80" <= c <= "\u0CFF" for c in word)

        if has_kannada:
            result.append(word)
        elif clean in ROMAN_TO_KANNADA_MAP:
            result.append(ROMAN_TO_KANNADA_MAP[clean])
        else:
            # Keep as-is (numbers, English legal terms like IPC, FIR)
            result.append(word)

    return " ".join(result)


# ── Quick test ───────────────────────────────────────────────
if __name__ == "__main__":
    test_inputs = [
        "naanu nyayalayakke hoguttene",
        "section 302 enu shiksha",
        "IPC ಸೆಕ್ಷನ್ 302 enu?",
        "ಪೊಲೀಸ್ arrest madidare hakku enu?",
        "FIR hege daakhalisabeku",
        "ನಾನು ಕಾನೂನು ಸಹಾಯ ಬೇಕು",
    ]

    print("── Transliterator Test ──\n")
    for text in test_inputs:
        script = detect_mixed_script(text)
        result = preprocess_query(text)
        print(f"Input  : {text}")
        print(f"Script : Roman={script['has_roman']} "
              f"Kannada={script['has_kannada']} "
              f"Mixed={script['is_mixed']}")
        print(f"Output : {result}")
        print()