# nlp/code_switch_detector.py
# Detects code-switching between Kannada and English in user queries.
# Legal users often mix both languages.
# Example: "Section 302 ಅಡಿಯಲ್ಲಿ ಏನು ಬರುತ್ತೆ?"

import re
from dataclasses import dataclass
from loguru import logger


# ── Kannada Unicode range ────────────────────────────────────
KANNADA_PATTERN = re.compile(r"[\u0C80-\u0CFF]+")
ENGLISH_PATTERN = re.compile(r"\b[a-zA-Z]+\b")

# ── Common English legal terms used even in Kannada speech ───
# These are expected English words in Kannada legal context.
# They are NOT considered code-switching — just normal usage.
EXPECTED_ENGLISH_LEGAL_TERMS = {
    "ipc", "crpc", "cpc", "fir", "rti", "section", "act",
    "court", "police", "bail", "warrant", "magistrate",
    "judge", "lawyer", "advocate", "petition", "affidavit",
    "pwdva", "sc", "st", "obc", "sp", "kslsa",
    "high", "supreme", "district", "sessions",
}


# ── Result dataclass ─────────────────────────────────────────
@dataclass
class CodeSwitchResult:
    """
    Holds the result of code-switch detection.

    Attributes:
        has_kannada         : True if Kannada characters found
        has_english         : True if English words found
        is_mixed            : True if both scripts present
        kannada_ratio       : Fraction of chars that are Kannada
        english_ratio       : Fraction of chars that are English
        kannada_words       : List of Kannada word tokens
        english_words       : List of English word tokens
        legal_terms_found   : English legal terms detected
        non_legal_english   : English words that are NOT legal terms
        dominant_language   : 'kannada' | 'english' | 'mixed'
    """
    has_kannada:        bool
    has_english:        bool
    is_mixed:           bool
    kannada_ratio:      float
    english_ratio:      float
    kannada_words:      list
    english_words:      list
    legal_terms_found:  list
    non_legal_english:  list
    dominant_language:  str


# ── Core detection ───────────────────────────────────────────
def detect(text: str) -> CodeSwitchResult:
    """
    Analyse a query for code-switching between Kannada and English.

    Args:
        text : Raw user input string

    Returns:
        CodeSwitchResult with full analysis

    Examples:
        >>> result = detect("Section 302 ಅಡಿಯಲ್ಲಿ ಏನು ಬರುತ್ತೆ?")
        >>> result.is_mixed
        True
        >>> result.dominant_language
        'mixed'

        >>> result = detect("ಪೊಲೀಸ್ ಬಂಧಿಸಿದಾಗ ನನ್ನ ಹಕ್ಕುಗಳೇನು?")
        >>> result.has_kannada
        True
        >>> result.dominant_language
        'kannada'
    """
    if not text or not text.strip():
        return CodeSwitchResult(
            has_kannada=False, has_english=False,
            is_mixed=False, kannada_ratio=0.0,
            english_ratio=0.0, kannada_words=[],
            english_words=[], legal_terms_found=[],
            non_legal_english=[], dominant_language="unknown"
        )

    # ── Character level analysis ─────────────────────────────
    total_chars   = max(len(text.replace(" ", "")), 1)
    kannada_chars = KANNADA_PATTERN.findall(text)
    english_words = ENGLISH_PATTERN.findall(text)

    kn_char_count = sum(len(w) for w in kannada_chars)
    en_char_count = sum(len(w) for w in english_words)

    kannada_ratio = round(kn_char_count / total_chars, 2)
    english_ratio = round(en_char_count / total_chars, 2)

    has_kannada = kannada_ratio > 0.05
    has_english = english_ratio > 0.05
    is_mixed    = has_kannada and has_english

    # ── Word level analysis ──────────────────────────────────
    kannada_words = KANNADA_PATTERN.findall(text)

    # Separate legal terms from non-legal English words
    legal_terms_found = []
    non_legal_english = []

    for word in english_words:
        if word.lower() in EXPECTED_ENGLISH_LEGAL_TERMS:
            legal_terms_found.append(word)
        else:
            non_legal_english.append(word)

    # ── Dominant language ────────────────────────────────────
    if kannada_ratio > 0.6:
        dominant_language = "kannada"
    elif english_ratio > 0.6:
        dominant_language = "english"
    elif is_mixed:
        dominant_language = "mixed"
    else:
        dominant_language = "unknown"

    result = CodeSwitchResult(
        has_kannada=has_kannada,
        has_english=has_english,
        is_mixed=is_mixed,
        kannada_ratio=kannada_ratio,
        english_ratio=english_ratio,
        kannada_words=kannada_words,
        english_words=english_words,
        legal_terms_found=legal_terms_found,
        non_legal_english=non_legal_english,
        dominant_language=dominant_language,
    )

    logger.debug(
        f"Code-switch: dominant={dominant_language} "
        f"kn={kannada_ratio} en={english_ratio} "
        f"mixed={is_mixed}"
    )
    return result


def get_language_label(text: str) -> str:
    """
    Quick helper — returns just the dominant language label.

    Args:
        text : Input text

    Returns:
        'kannada' | 'english' | 'mixed' | 'unknown'

    Example:
        >>> get_language_label("ನಾನು ಹೋಗುತ್ತೇನೆ")
        'kannada'
        >>> get_language_label("What is Section 302?")
        'english'
        >>> get_language_label("Section 302 ಏನು?")
        'mixed'
    """
    return detect(text).dominant_language


def needs_transliteration(text: str) -> bool:
    """
    Check if the text needs transliteration.
    Returns True if text is mostly Roman script with no Kannada.

    Args:
        text : Input text

    Returns:
        True if transliteration is needed

    Example:
        >>> needs_transliteration("naanu nyayalayakke hoguttene")
        True
        >>> needs_transliteration("ನಾನು ನ್ಯಾಯಾಲಯಕ್ಕೆ ಹೋಗುತ್ತೇನೆ")
        False
    """
    result = detect(text)
    return (
        result.has_english
        and not result.has_kannada
        and len(result.non_legal_english) > 0
    )


def get_summary(result: CodeSwitchResult) -> str:
    """
    Returns a human readable summary of code-switch result.

    Args:
        result : CodeSwitchResult object

    Returns:
        Summary string
    """
    lines = [
        f"Dominant Language : {result.dominant_language}",
        f"Has Kannada       : {result.has_kannada} "
        f"(ratio: {result.kannada_ratio})",
        f"Has English       : {result.has_english} "
        f"(ratio: {result.english_ratio})",
        f"Is Mixed          : {result.is_mixed}",
        f"Legal Terms Found : {result.legal_terms_found}",
        f"Non-legal English : {result.non_legal_english}",
        f"Kannada Words     : {result.kannada_words}",
    ]
    return "\n".join(lines)


# ── Quick test ───────────────────────────────────────────────
if __name__ == "__main__":
    test_queries = [
        # Pure Kannada
        "ಪೊಲೀಸ್ ಬಂಧಿಸಿದಾಗ ನನ್ನ ಹಕ್ಕುಗಳೇನು?",
        # Mixed — legal term + Kannada
        "Section 302 ಅಡಿಯಲ್ಲಿ ಏನು ಬರುತ್ತೆ?",
        # Mixed — IPC + Kannada
        "IPC ಸೆಕ್ಷನ್ 420 ಶಿಕ್ಷೆ ಎಷ್ಟು?",
        # Mixed — FIR + Kannada
        "FIR ದಾಖಲಿಸುವುದು ಹೇಗೆ?",
        # Mostly English
        "What is the punishment under Section 302 IPC?",
        # Roman Kannada
        "naanu nyayalayakke hogabeku",
        # Pure Kannada legal
        "ಜಾಮೀನು ಅರ್ಜಿ ಹೇಗೆ ಸಲ್ಲಿಸಬೇಕು?",
    ]

    print("── Code-Switch Detector Test ──\n")
    for query in test_queries:
        result = detect(query)
        print(f"Query  : {query}")
        print(get_summary(result))
        print(f"Needs Transliteration: {needs_transliteration(query)}")
        print("-" * 55)