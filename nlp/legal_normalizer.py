# nlp/legal_normalizer.py
# Normalizes Kannada legal terminology.
# Maps colloquial / synonym / dialect terms to
# canonical legal terms used in the knowledge base.
#
# Example:
#   'ಸೆಕ್ಷನ್'  ->  'ವಿಭಾಗ'
#   'ಧಾರೆ'     ->  'ವಿಭಾಗ'
#   'ಕೊಲೆ'     ->  'ಹತ್ಯೆ'

import re
import json
from pathlib import Path
from loguru import logger


# ── Glossary file path ───────────────────────────────────────
GLOSSARY_PATH = (
    Path(__file__).parent.parent
    / "data"
    / "processed"
    / "legal_glossary_kn.json"
)

# ── Seed glossary ────────────────────────────────────────────
# Built-in legal term mappings.
# Loaded first — then overridden by glossary file if it exists.

SEED_GLOSSARY = {

    # ── Section synonyms ─────────────────────────────────────
    "ಸೆಕ್ಷನ್":           "ವಿಭಾಗ",
    "ಧಾರೆ":              "ವಿಭಾಗ",
    "ಸೆಕ್ಷನ":            "ವಿಭಾಗ",
    "ಅಧಿನಿಯಮ":          "ವಿಭಾಗ",

    # ── Punishment synonyms ──────────────────────────────────
    "ಶಿಕ್ಷೆ":             "ದಂಡ",
    "ಸಜಾ":               "ದಂಡ",
    "ಶಿಕ್ಷಣ":            "ದಂಡ",

    # ── Crime synonyms ───────────────────────────────────────
    "ಕೊಲೆ":              "ಹತ್ಯೆ",
    "ಕೊಲ್ಲುವಿಕೆ":        "ಹತ್ಯೆ",
    "ಮರ್ಡರ್":            "ಹತ್ಯೆ",
    "ಕಳವು":              "ಕಳ್ಳತನ",
    "ಕದಿಯುವಿಕೆ":         "ಕಳ್ಳತನ",
    "ಲೂಟಿ":              "ದರೋಡೆ",
    "ದರೋಡೆ":             "ದರೋಡೆ",
    "ವಂಚನೆ":             "ಮೋಸ",
    "ಮೋಸಗಾರಿಕೆ":         "ಮೋಸ",
    "ಫ್ರಾಡ್":             "ಮೋಸ",
    "ಹೊಡೆತ":             "ಹಲ್ಲೆ",
    "ಮಾರಾಟ":             "ಹಲ್ಲೆ",
    "ಅತ್ಯಾಚಾರ":          "ಅತ್ಯಾಚಾರ",
    "ರೇಪ್":              "ಅತ್ಯಾಚಾರ",
    "ಭ್ರಷ್ಟಾಚಾರ":        "ಭ್ರಷ್ಟಾಚಾರ",
    "ಲಂಚ":               "ಲಂಚ",
    "ಬ್ರೈಬ್":             "ಲಂಚ",

    # ── Court synonyms ───────────────────────────────────────
    "ಕೋರ್ಟ್":            "ನ್ಯಾಯಾಲಯ",
    "ಕಚೇರಿ":             "ನ್ಯಾಯಾಲಯ",
    "ಅದಾಲತ್":           "ನ್ಯಾಯಾಲಯ",

    # ── People synonyms ──────────────────────────────────────
    "ವಕೀಲ":              "ಅಭಿಭಾಷಕ",
    "ಲಾಯರ್":             "ಅಭಿಭಾಷಕ",
    "ಅಡ್ವೋಕೇಟ್":         "ಅಭಿಭಾಷಕ",
    "ಜಡ್ಜ್":             "ನ್ಯಾಯಾಧೀಶ",
    "ನ್ಯಾಯಮೂರ್ತಿ":       "ನ್ಯಾಯಾಧೀಶ",
    "ಪೊಲೀಸ್":           "ಪೊಲೀಸ್",
    "ಪೋಲೀಸ್":           "ಪೊಲೀಸ್",
    "ಕಾನ್ಸ್ಟೇಬಲ್":        "ಪೊಲೀಸ್ ಕಾನ್ಸ್ಟೇಬಲ್",

    # ── Document synonyms ────────────────────────────────────
    "ಅರ್ಜಿ":             "ಮನವಿ",
    "ಪಿಟಿಷನ್":           "ಮನವಿ",
    "ಅಪ್ಲಿಕೇಶನ್":        "ಮನವಿ",
    "ತೀರ್ಪು":            "ತೀರ್ಪು",
    "ಜಡ್ಜ್ಮೆಂಟ್":         "ತೀರ್ಪು",
    "ವರ್ಡಿಕ್ಟ್":          "ತೀರ್ಪು",
    "ನೋಟಿಸ್":            "ಸೂಚನೆ",

    # ── Procedure synonyms ───────────────────────────────────
    "ಅರೆಸ್ಟ್":            "ಬಂಧನ",
    "ಹಿಡಿದಿಡು":          "ಬಂಧನ",
    "ಜಾಮೀನು":           "ಜಾಮೀನು",
    "ಬೇಲ್":              "ಜಾಮೀನು",
    "ವಿಚಾರಣೆ":          "ವಿಚಾರಣೆ",
    "ಟ್ರಯಲ್":            "ವಿಚಾರಣೆ",
    "ಮೇಲ್ಮನವಿ":         "ಮೇಲ್ಮನವಿ",
    "ಅಪೀಲ್":             "ಮೇಲ್ಮನವಿ",

    # ── Rights synonyms ──────────────────────────────────────
    "ಹಕ್ಕು":             "ಹಕ್ಕು",
    "ರೈಟ್ಸ್":            "ಹಕ್ಕುಗಳು",
    "ಅಧಿಕಾರ":           "ಹಕ್ಕು",

    # ── Property synonyms ────────────────────────────────────
    "ಆಸ್ತಿ":             "ಆಸ್ತಿ",
    "ಪ್ರಾಪರ್ಟಿ":          "ಆಸ್ತಿ",
    "ಜಮೀನು":            "ಭೂಮಿ",
    "ಭೂಮಿ":             "ಭೂಮಿ",
    "ನಿವೇಶನ":           "ಭೂಮಿ",

    # ── Colloquial question words ────────────────────────────
    "ಏನ್ರಿ":             "ಏನು",
    "ಏನ್ರೀ":             "ಏನು",
    "ಹೇಗ್ರಿ":            "ಹೇಗೆ",
    "ಹೇಗ್ರೀ":            "ಹೇಗೆ",
    "ಎಲ್ಲಿಗ್ರಿ":          "ಎಲ್ಲಿ",
    "ಯಾಕ್ರಿ":            "ಯಾಕೆ",
    "ಮಾಡ್ಬೇಕು":         "ಮಾಡಬೇಕು",
    "ಮಾಡ್ಬಹುದು":        "ಮಾಡಬಹುದು",
    "ಆಗ್ತದೆ":            "ಆಗುತ್ತದೆ",
    "ಆಗಲ್ಲ":             "ಆಗುವುದಿಲ್ಲ",
    "ಇಲ್ವಾ":             "ಇಲ್ಲವೇ",
    "ಬರ್ತದೆ":            "ಬರುತ್ತದೆ",
    "ಕೊಡ್ತಾರೆ":          "ಕೊಡುತ್ತಾರೆ",
    "ಹೋಗ್ತಾರೆ":          "ಹೋಗುತ್ತಾರೆ",

    # ── Dialect variants (Mysuru / Dharwad / Mangaluru) ──────
    "ಆಗಂಗಿಲ್ಲ":          "ಆಗುವುದಿಲ್ಲ",    # Dharwad
    "ಆಪುಂಡಿಲ್ಲ":         "ಆಗುವುದಿಲ್ಲ",    # Mangaluru
    "ಏನ್ ಮಾಡದು":        "ಏನು ಮಾಡುವುದು",  # Mangaluru
    "ಹೇಳ್ರಿ":            "ಹೇಳಿ",           # Dharwad
    "ಮಾಡ್ರಿ":            "ಮಾಡಿ",           # Dharwad
    "ನೋಡ್ರಿ":            "ನೋಡಿ",           # Dharwad
}

# ── In-memory glossary (loaded once) ────────────────────────
_glossary: dict = {}


def load_glossary() -> None:
    """
    Load the legal glossary from file.
    Falls back to seed glossary if file not found.
    """
    global _glossary

    if GLOSSARY_PATH.exists():
        try:
            with open(GLOSSARY_PATH, encoding="utf-8") as f:
                file_glossary = json.load(f)
            # Merge: file overrides seed
            _glossary = {**SEED_GLOSSARY, **file_glossary}
            logger.info(
                f"Glossary loaded: {len(_glossary)} terms "
                f"(file: {len(file_glossary)}, "
                f"seed: {len(SEED_GLOSSARY)})"
            )
        except Exception as e:
            logger.warning(f"Glossary file error: {e}. Using seed glossary.")
            _glossary = SEED_GLOSSARY.copy()
    else:
        _glossary = SEED_GLOSSARY.copy()
        logger.info(
            f"Glossary file not found. "
            f"Using seed glossary: {len(_glossary)} terms."
        )


def save_glossary() -> None:
    """
    Save the current in-memory glossary to the JSON file.
    Used when new terms are added at runtime.
    """
    GLOSSARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(GLOSSARY_PATH, "w", encoding="utf-8") as f:
        json.dump(_glossary, f, ensure_ascii=False, indent=2)
    logger.success(f"Glossary saved: {len(_glossary)} terms -> {GLOSSARY_PATH}")


def add_term(colloquial: str, canonical: str) -> None:
    """
    Add a new term mapping to the glossary.

    Args:
        colloquial : The informal / synonym term
        canonical  : The standard legal term to map to

    Example:
        >>> add_term("ಮರ್ಡರ್", "ಹತ್ಯೆ")
    """
    if not _glossary:
        load_glossary()
    _glossary[colloquial] = canonical
    logger.info(f"Term added: '{colloquial}' -> '{canonical}'")


def normalize(text: str) -> str:
    """
    Normalize Kannada legal text.
    Replaces colloquial / synonym terms with canonical forms.

    Args:
        text : Raw Kannada input text

    Returns:
        Normalized text with canonical legal terms

    Example:
        >>> normalize("ಸೆಕ್ಷನ್ 302 ಕೊಲೆಗೆ ಶಿಕ್ಷೆ ಏನು?")
        'ವಿಭಾಗ 302 ಹತ್ಯೆಗೆ ದಂಡ ಏನು?'
    """
    if not _glossary:
        load_glossary()

    if not text or not text.strip():
        return text

    normalized = text

    # Sort by length (longest first) to avoid partial replacements
    sorted_terms = sorted(
        _glossary.keys(),
        key=len,
        reverse=True
    )

    for term in sorted_terms:
        if term in normalized:
            canonical  = _glossary[term]
            normalized = normalized.replace(term, canonical)
            logger.debug(f"Normalized: '{term}' -> '{canonical}'")

    return normalized


def normalize_tokens(tokens: list) -> list:
    """
    Normalize a list of tokens.
    Applies normalization to each token individually.

    Args:
        tokens : List of word tokens

    Returns:
        List of normalized tokens

    Example:
        >>> normalize_tokens(['ಸೆಕ್ಷನ್', '302', 'ಕೊಲೆ'])
        ['ವಿಭಾಗ', '302', 'ಹತ್ಯೆ']
    """
    if not _glossary:
        load_glossary()

    return [_glossary.get(token, token) for token in tokens]


def extract_section_numbers(text: str) -> list:
    """
    Extract IPC / CrPC / CPC section numbers from text.

    Args:
        text : Input text

    Returns:
        List of section number strings found

    Example:
        >>> extract_section_numbers("IPC ಸೆಕ್ಷನ್ 302 ಮತ್ತು 307")
        ['302', '307']
    """
    pattern = re.compile(
        r"(?:section|ವಿಭಾಗ|ಸೆಕ್ಷನ್|ಧಾರೆ)\s*(\d+[A-Z]?)",
        re.IGNORECASE
    )
    matches = pattern.findall(text)
    return list(set(matches))


def extract_law_names(text: str) -> list:
    """
    Extract law names mentioned in the text.

    Args:
        text : Input text

    Returns:
        List of law name strings found

    Example:
        >>> extract_law_names("IPC ಮತ್ತು CrPC ಪ್ರಕಾರ")
        ['IPC', 'CrPC']
    """
    law_patterns = [
        r"\bIPC\b",
        r"\bCrPC\b",
        r"\bCPC\b",
        r"\bRTI\b",
        r"\bPWDVA\b",
        r"Consumer Protection Act",
        r"Karnataka Land Revenue Act",
        r"Karnataka Police Act",
        r"Karnataka Rent Control Act",
        r"Legal Services.*?Act",
    ]
    found = []
    for pattern in law_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        found.extend(matches)
    return list(set(found))


def get_glossary_size() -> int:
    """Returns the number of terms in the loaded glossary."""
    if not _glossary:
        load_glossary()
    return len(_glossary)


# ── Load on import ───────────────────────────────────────────
load_glossary()


# ── Quick test ───────────────────────────────────────────────
if __name__ == "__main__":
    test_inputs = [
        "ಸೆಕ್ಷನ್ 302 ಕೊಲೆಗೆ ಶಿಕ್ಷೆ ಏನು?",
        "ಕೋರ್ಟ್‌ನಲ್ಲಿ ವಕೀಲ ಬೇಕೇ?",
        "FIR ದಾಖಲಿಸಲು ಅರೆಸ್ಟ್ ಆಗಬೇಕೇ?",
        "ಬೇಲ್ ಹೇಗೆ ಪಡೆಯುವುದು?",
        "ಜಮೀನು ಆಕ್ರಮಣ ಆದರೆ ಏನ್ರಿ ಮಾಡ್ಬೇಕು?",
        "ಮರ್ಡರ್ ಕೇಸ್‌ನಲ್ಲಿ ಜಡ್ಜ್ ಏನು ಹೇಳ್ತಾರೆ?",
    ]

    print("── Legal Normalizer Test ──\n")
    print(f"Glossary size: {get_glossary_size()} terms\n")

    for text in test_inputs:
        normalized = normalize(text)
        sections   = extract_section_numbers(text)
        laws       = extract_law_names(text)
        print(f"Input     : {text}")
        print(f"Normalized: {normalized}")
        print(f"Sections  : {sections}")
        print(f"Laws      : {laws}")
        print("-" * 55)