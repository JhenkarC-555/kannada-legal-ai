# pragmatics/dialect_adapter.py
# Adapts Kannada dialect variations to standard Kannada.
#
# Kannada has 4 major regional dialects:
#   1. Mysuru    — southern Karnataka (formal, classical)
#   2. Dharwad   — northern Karnataka (distinct vocabulary)
#   3. Mangaluru — coastal Karnataka  (Tulu influence)
#   4. Bengaluru — urban mix          (English + Hindi influence)
#
# Legal users may type in their local dialect.
# This module normalizes all dialects to standard Kannada
# so the NLP pipeline works correctly.
#
# Example:
#   Dharwad : "ಏನ್ ಮಾಡ್ರಿ ಈಗ?"
#   Standard: "ಈಗ ಏನು ಮಾಡಬೇಕು?"

from dataclasses import dataclass
from loguru import logger


# ── Dialect maps ──────────────────────────────────────────────
# Each dialect has a dictionary mapping
# dialect word -> standard Kannada word

DIALECT_MAPS = {

    # ── Mysuru dialect ────────────────────────────────────────
    "mysuru": {
        # Question words
        "ಏನ್ರೀ":         "ಏನು",
        "ಏನ್ರಿ":          "ಏನು",
        "ಹೇಗ್ರೀ":         "ಹೇಗೆ",
        "ಹೇಗ್ರಿ":          "ಹೇಗೆ",
        "ಯಾಕ್ರೀ":         "ಯಾಕೆ",
        "ಎಲ್ಲಿಗ್ರೀ":       "ಎಲ್ಲಿ",
        "ಯಾರ್ರೀ":         "ಯಾರು",

        # Verb forms
        "ಮಾಡ್ಬೇಕು":       "ಮಾಡಬೇಕು",
        "ಮಾಡ್ಬಹುದು":      "ಮಾಡಬಹುದು",
        "ಹೋಗ್ಬೇಕು":       "ಹೋಗಬೇಕು",
        "ಬರ್ಬೇಕು":        "ಬರಬೇಕು",
        "ಹೇಳ್ಬೇಕು":       "ಹೇಳಬೇಕು",
        "ಕೊಡ್ಬೇಕು":       "ಕೊಡಬೇಕು",
        "ತೊಗೊಳ್ಬೇಕು":    "ತೆಗೆದುಕೊಳ್ಳಬೇಕು",
        "ಸಿಗ್ತದೆ":         "ಸಿಗುತ್ತದೆ",
        "ಆಗ್ತದೆ":          "ಆಗುತ್ತದೆ",
        "ಆಗಲ್ಲ":           "ಆಗುವುದಿಲ್ಲ",
        "ಇಲ್ವಾ":           "ಇಲ್ಲವೇ",
        "ಬರ್ತದೆ":          "ಬರುತ್ತದೆ",
        "ಕೊಡ್ತಾರೆ":        "ಕೊಡುತ್ತಾರೆ",
        "ಹೋಗ್ತಾರೆ":        "ಹೋಗುತ್ತಾರೆ",
        "ಮಾಡ್ತಾರೆ":        "ಮಾಡುತ್ತಾರೆ",
        "ಬರ್ತಾರೆ":         "ಬರುತ್ತಾರೆ",
        "ಹೇಳ್ತಾರೆ":        "ಹೇಳುತ್ತಾರೆ",

        # Common words
        "ತೊಗೊ":           "ತೆಗೆದುಕೋ",
        "ಏನ್ ಆಯ್ತು":      "ಏನಾಯಿತು",
        "ಎಲ್ಲಿ ಹೋಗ್ತಿ":   "ಎಲ್ಲಿ ಹೋಗುತ್ತಿ",
        "ನಂಗೆ":            "ನನಗೆ",
        "ನಿಂಗೆ":           "ನಿನಗೆ",
        "ಅವ್ರಿಗೆ":         "ಅವರಿಗೆ",
        "ಅದ್ ಹೇಗೆ":        "ಅದು ಹೇಗೆ",

        # Legal specific
        "ಕೇಸ್ ಏನ್ ಮಾಡ್ಬೇಕು":  "ಪ್ರಕರಣದಲ್ಲಿ ಏನು ಮಾಡಬೇಕು",
        "ಪೊಲೀಸ್ ಹತ್ರ ಹೋಗ್ಬೇಕಾ": "ಪೊಲೀಸ್ ಬಳಿ ಹೋಗಬೇಕೇ",
    },

    # ── Dharwad dialect ───────────────────────────────────────
    "dharwad": {
        # Question words
        "ಏನ್ರಿ":           "ಏನು",
        "ಹೇಳ್ರಿ":          "ಹೇಳಿ",
        "ಮಾಡ್ರಿ":          "ಮಾಡಿ",
        "ನೋಡ್ರಿ":          "ನೋಡಿ",
        "ಬನ್ನಿರಿ":         "ಬನ್ನಿ",
        "ಹೋಗ್ರಿ":          "ಹೋಗಿ",
        "ಕೊಡ್ರಿ":          "ಕೊಡಿ",

        # Verb forms — Dharwad unique
        "ಆಗಂಗಿಲ್ಲ":        "ಆಗುವುದಿಲ್ಲ",
        "ಬರಂಗಿಲ್ಲ":        "ಬರುವುದಿಲ್ಲ",
        "ಮಾಡಂಗಿಲ್ಲ":       "ಮಾಡುವುದಿಲ್ಲ",
        "ಹೋಗಂಗಿಲ್ಲ":       "ಹೋಗುವುದಿಲ್ಲ",
        "ಸಿಗಂಗಿಲ್ಲ":        "ಸಿಗುವುದಿಲ್ಲ",
        "ಆಕ್ಕಿಲ್ಲ":          "ಆಗುವುದಿಲ್ಲ",
        "ಬರ್ತದ":           "ಬರುತ್ತದೆ",
        "ಆಗ್ತದ":           "ಆಗುತ್ತದೆ",
        "ಮಾಡ್ತದ":          "ಮಾಡುತ್ತದೆ",
        "ಹೋಗ್ತದ":          "ಹೋಗುತ್ತದೆ",

        # Common words
        "ಅದ ಏನು":          "ಅದು ಏನು",
        "ಇದ ಏನು":          "ಇದು ಏನು",
        "ನಮ್ಗೆ":            "ನಮಗೆ",
        "ನಿಮ್ಗೆ":           "ನಿಮಗೆ",
        "ಅವ್ರ":            "ಅವರ",
        "ಇವ್ರ":            "ಇವರ",
        "ಅದ ಹೇಳ್ರಿ":       "ಅದನ್ನು ಹೇಳಿ",
        "ಯಾಕ ಹೀಂಗ":        "ಯಾಕೆ ಹೀಗೆ",

        # Legal specific
        "ಕೋರ್ಟಿಗ್ ಹೋಗ್ಬೇಕ":  "ನ್ಯಾಯಾಲಯಕ್ಕೆ ಹೋಗಬೇಕು",
        "ವಕೀಲ್ರ ಹತ್ರ ಹೋಗ":  "ವಕೀಲರ ಬಳಿ ಹೋಗು",
        "ದೂರು ಕೊಡ್ಬೇಕ":    "ದೂರು ನೀಡಬೇಕು",
        "ಜಾಮೀನ ಸಿಗ್ತದ":    "ಜಾಮೀನು ಸಿಗುತ್ತದೆ",
    },

    # ── Mangaluru dialect ─────────────────────────────────────
    "mangaluru": {
        # Unique Mangaluru verb forms (Tulu influence)
        "ಆಪುಂಡಿಲ್ಲ":       "ಆಗುವುದಿಲ್ಲ",
        "ಬಪ್ಪುಂಡಿಲ್ಲ":      "ಬರುವುದಿಲ್ಲ",
        "ಮಾಲ್ಪುಂಡಿಲ್ಲ":     "ಮಾಡುವುದಿಲ್ಲ",
        "ಏನ್ ಮಾಡ್ದು":      "ಏನು ಮಾಡುವುದು",
        "ಆಪುಂಡು":          "ಆಗುತ್ತದೆ",
        "ಬಪ್ಪುಂಡು":         "ಬರುತ್ತದೆ",

        # Common words
        "ಎಂಚ":             "ಹೇಗೆ",
        "ಎಂಚಿನ":           "ಹೇಗಿನ",
        "ಉಂಡು":            "ಇದೆ",
        "ಇಜ್ಜಿ":            "ಇಲ್ಲ",
        "ಮಲ್ತೆ":            "ಮಾಡಿದೆ",
        "ಪಂಡೆ":            "ಹೇಳಿದೆ",
        "ಕೇನ್ಲೆ":           "ಕೇಳಿದೆ",
        "ನಿಕ್ಕ":            "ನಿನಗೆ",
        "ಎನ್ಕ":            "ನನಗೆ",
        "ಅಕ್ಲೆ":            "ಅವರಿಗೆ",

        # Legal specific
        "ಕೋರ್ಟ್‌ಗ್ ಪೋವೊಡು":  "ನ್ಯಾಯಾಲಯಕ್ಕೆ ಹೋಗಬೇಕು",
        "ಪೊಲೀಸ್‌ಗ್ ಹೇಳೊಡು": "ಪೊಲೀಸ್‌ಗೆ ಹೇಳಬೇಕು",
        "ದೂರು ಕೊರೊಡು":     "ದೂರು ನೀಡಬೇಕು",
    },

    # ── Bengaluru urban dialect ───────────────────────────────
    "bengaluru": {
        # Heavy English mixing — normalize English parts
        "ಕೇಸ್ ಫೈಲ್ ಮಾಡ್ಬೇಕು":    "ಪ್ರಕರಣ ದಾಖಲಿಸಬೇಕು",
        "ಕಂಪ್ಲೇಂಟ್ ಕೊಡ್ಬೇಕು":    "ದೂರು ನೀಡಬೇಕು",
        "ಕೋರ್ಟ್‌ಗೆ ಹೋಗ್ಬೇಕು":    "ನ್ಯಾಯಾಲಯಕ್ಕೆ ಹೋಗಬೇಕು",
        "ಲಾಯರ್ ತಗೊಳ್ಬೇಕು":      "ವಕೀಲರನ್ನು ನೇಮಿಸಬೇಕು",
        "ಬೇಲ್ ಹೇಗ್ ಮಾಡ್ಬೇಕು":   "ಜಾಮೀನು ಹೇಗೆ ಪಡೆಯಬೇಕು",
        "ಪೊಲೀಸ್ ಸ್ಟೇಷನ್‌ಗೆ":     "ಪೊಲೀಸ್ ಠಾಣೆಗೆ",
        "FIR ಹ್ಯಾಗ್ ಹಾಕ್ಬೇಕು":   "FIR ಹೇಗೆ ದಾಖಲಿಸಬೇಕು",
        "ಜಡ್ಜ್ ಏನ್ ಹೇಳ್ತಾರೆ":     "ನ್ಯಾಯಾಧೀಶರು ಏನು ಹೇಳುತ್ತಾರೆ",
        "ಫೈನ್ ಎಷ್ಟಾಗ್ತದೆ":        "ದಂಡ ಎಷ್ಟಾಗುತ್ತದೆ",
        "ಜೈಲ್‌ಗೆ ಹೋಗ್ತಾರಾ":      "ಜೈಲಿಗೆ ಹೋಗುತ್ತಾರಾ",

        # Short forms common in Bengaluru
        "ಆಗಲ್ಲ":            "ಆಗುವುದಿಲ್ಲ",
        "ಸಿಗಲ್ಲ":            "ಸಿಗುವುದಿಲ್ಲ",
        "ಬರಲ್ಲ":             "ಬರುವುದಿಲ್ಲ",
        "ಹೋಗಲ್ಲ":            "ಹೋಗುವುದಿಲ್ಲ",
        "ಮಾಡಲ್ಲ":            "ಮಾಡುವುದಿಲ್ಲ",
        "ಕೊಡಲ್ಲ":            "ಕೊಡುವುದಿಲ್ಲ",
        "ತಿಳಿಯಲ್ಲ":          "ತಿಳಿಯುವುದಿಲ್ಲ",
    },
}

# ── All known dialect words (combined) ────────────────────────
# Used for auto-detection of dialect.
ALL_DIALECT_WORDS = {}
for dialect, mapping in DIALECT_MAPS.items():
    for word in mapping.keys():
        ALL_DIALECT_WORDS[word] = dialect


# ── Result dataclass ──────────────────────────────────────────
@dataclass
class DialectResult:
    """
    Holds the result of dialect normalization.

    Attributes:
        original_text   : Input text before normalization
        normalized_text : Text after normalization
        detected_dialect: Which dialect was detected
        changes_made    : List of (original, replacement) pairs
        was_normalized  : True if any changes were made
    """
    original_text:    str
    normalized_text:  str
    detected_dialect: str
    changes_made:     list
    was_normalized:   bool


# ── Dialect detector ──────────────────────────────────────────
def detect_dialect(text: str) -> str:
    """
    Auto-detect which Kannada dialect is being used.

    Args:
        text : Input Kannada text

    Returns:
        Dialect name string or 'standard' if not detected

    Example:
        >>> detect_dialect("ಆಗಂಗಿಲ್ಲ ಏನ್ ಮಾಡ್ರಿ")
        'dharwad'
        >>> detect_dialect("ಆಪುಂಡಿಲ್ಲ")
        'mangaluru'
    """
    if not text:
        return "standard"

    dialect_hits = {}
    for word, dialect in ALL_DIALECT_WORDS.items():
        if word in text:
            dialect_hits[dialect] = dialect_hits.get(dialect, 0) + 1

    if not dialect_hits:
        return "standard"

    detected = max(dialect_hits, key=lambda k: dialect_hits[k])
    logger.debug(
        f"Dialect detected: {detected} "
        f"hits={dialect_hits}"
    )
    return detected


# ── Normalizer ────────────────────────────────────────────────
def normalize_dialect(
    text:    str,
    dialect: str = None,
) -> DialectResult:
    """
    Normalize dialect-specific Kannada to standard Kannada.

    Args:
        text    : Input Kannada text (any dialect)
        dialect : Force a specific dialect map to use.
                  If None, auto-detects dialect.

    Returns:
        DialectResult with normalized text and metadata

    Examples:
        >>> result = normalize_dialect("ಏನ್ ಮಾಡ್ರಿ ಈಗ?")
        >>> result.normalized_text
        'ಏನು ಮಾಡಿ ಈಗ?'
        >>> result.detected_dialect
        'dharwad'

        >>> result = normalize_dialect("ಆಪುಂಡಿಲ್ಲ ಕೋರ್ಟ್‌ಗ್ ಪೋವೊಡು")
        >>> result.normalized_text
        'ಆಗುವುದಿಲ್ಲ ನ್ಯಾಯಾಲಯಕ್ಕೆ ಹೋಗಬೇಕು'
        >>> result.detected_dialect
        'mangaluru'
    """
    if not text or not text.strip():
        return DialectResult(
            original_text=text,
            normalized_text=text,
            detected_dialect="standard",
            changes_made=[],
            was_normalized=False,
        )

    # Auto-detect dialect if not provided
    if not dialect:
        dialect = detect_dialect(text)

    if dialect == "standard" or dialect not in DIALECT_MAPS:
        return DialectResult(
            original_text=text,
            normalized_text=text,
            detected_dialect="standard",
            changes_made=[],
            was_normalized=False,
        )

    # Apply dialect map
    dialect_map  = DIALECT_MAPS[dialect]
    normalized   = text
    changes_made = []

    # Sort by length — longest phrases first
    # Avoids partial replacement of longer phrases
    sorted_terms = sorted(
        dialect_map.keys(),
        key=len,
        reverse=True,
    )

    for dialect_word in sorted_terms:
        if dialect_word in normalized:
            standard_word = dialect_map[dialect_word]
            normalized    = normalized.replace(
                dialect_word, standard_word
            )
            changes_made.append((dialect_word, standard_word))
            logger.debug(
                f"Dialect normalize: "
                f"'{dialect_word}' -> '{standard_word}'"
            )

    was_normalized = len(changes_made) > 0

    if was_normalized:
        logger.info(
            f"Dialect normalization complete.\n"
            f"        Dialect  : {dialect}\n"
            f"        Changes  : {len(changes_made)}\n"
            f"        Original : '{text[:60]}'\n"
            f"        Result   : '{normalized[:60]}'"
        )

    return DialectResult(
        original_text=text,
        normalized_text=normalized,
        detected_dialect=dialect,
        changes_made=changes_made,
        was_normalized=was_normalized,
    )


def normalize_text(text: str, dialect: str = None) -> str:
    """
    Quick helper — returns just the normalized text string.

    Args:
        text    : Input text
        dialect : Optional dialect name

    Returns:
        Normalized text string

    Example:
        >>> normalize_text("ಆಗಂಗಿಲ್ಲ ಏನ್ ಮಾಡ್ರಿ")
        'ಆಗುವುದಿಲ್ಲ ಏನು ಮಾಡಿ'
    """
    return normalize_dialect(text, dialect).normalized_text


def normalize_all_dialects(text: str) -> str:
    """
    Apply all dialect maps sequentially.
    Use when dialect is truly unknown.

    Args:
        text : Input text

    Returns:
        Normalized text with all dialect variants replaced
    """
    normalized = text
    for dialect in DIALECT_MAPS.keys():
        result    = normalize_dialect(normalized, dialect)
        normalized = result.normalized_text
    return normalized


def get_supported_dialects() -> list:
    """
    Returns list of supported dialect names.

    Returns:
        List of dialect name strings
    """
    return list(DIALECT_MAPS.keys())


def get_dialect_stats(dialect: str) -> dict:
    """
    Returns stats about a dialect map.

    Args:
        dialect : Dialect name

    Returns:
        Dictionary with stats
    """
    if dialect not in DIALECT_MAPS:
        return {}
    mapping = DIALECT_MAPS[dialect]
    return {
        "dialect":     dialect,
        "total_terms": len(mapping),
        "sample":      list(mapping.items())[:3],
    }


# ── Quick test ───────────────────────────────────────────────
if __name__ == "__main__":

    print("══════════════════════════════════════════")
    print("   Dialect Adapter Test")
    print("══════════════════════════════════════════\n")

    print(f"Supported dialects: {get_supported_dialects()}\n")

    test_cases = [
        # Mysuru
        (
            "ಕೇಸ್‌ನಲ್ಲಿ ಏನ್ರೀ ಮಾಡ್ಬೇಕು?",
            "mysuru",
            "Mysuru — case maadbeku"
        ),
        (
            "ಪೊಲೀಸ್ ಹತ್ರ ಹೋಗ್ಬೇಕಾ ಸರ್?",
            "mysuru",
            "Mysuru — police hatra hogbeka"
        ),

        # Dharwad
        (
            "ಜಾಮೀನ ಸಿಗ್ತದ ಅಲ್ಲಾ?",
            "dharwad",
            "Dharwad — bail sigtada"
        ),
        (
            "ಕೋರ್ಟಿಗ್ ಹೋಗ್ಬೇಕ ಹೇಳ್ರಿ",
            "dharwad",
            "Dharwad — court hogbeka"
        ),
        (
            "ಆಗಂಗಿಲ್ಲ ಏನ್ ಮಾಡ್ರಿ?",
            "dharwad",
            "Dharwad — aagangilla"
        ),

        # Mangaluru
        (
            "ಆಪುಂಡಿಲ್ಲ ಕೋರ್ಟ್‌ಗ್ ಪೋವೊಡು",
            "mangaluru",
            "Mangaluru — aapundilla"
        ),
        (
            "ಪೊಲೀಸ್‌ಗ್ ಹೇಳೊಡು ಎಂಚ?",
            "mangaluru",
            "Mangaluru — police ge helodu"
        ),

        # Bengaluru
        (
            "FIR ಹ್ಯಾಗ್ ಹಾಕ್ಬೇಕು ಸ್ಟೇಷನ್‌ಗೆ?",
            "bengaluru",
            "Bengaluru — FIR haakbeku"
        ),
        (
            "ಲಾಯರ್ ತಗೊಳ್ಬೇಕು ಜೈಲ್‌ಗೆ ಹೋಗ್ತಾರಾ?",
            "bengaluru",
            "Bengaluru — lawyer tagolbeku"
        ),

        # Auto-detect
        (
            "ಆಗಂಗಿಲ್ಲ ಏನ್ ಮಾಡ್ರಿ",
            None,
            "Auto-detect — should find dharwad"
        ),
        (
            "ಆಪುಂಡಿಲ್ಲ ಎಂಚ ಮಾಲ್ಪುಂಡಿಲ್ಲ",
            None,
            "Auto-detect — should find mangaluru"
        ),
    ]

    for text, dialect, label in test_cases:
        result  = normalize_dialect(text, dialect)
        changed = "✅" if result.was_normalized else "ℹ️"

        print(f"{changed} {label}")
        print(f"   Input    : {text}")
        print(f"   Dialect  : {result.detected_dialect}")
        print(f"   Output   : {result.normalized_text}")
        if result.changes_made:
            print(f"   Changes  : {result.changes_made}")
        print("-" * 55)

    # Dialect stats
    print("\n── Dialect Stats ──\n")
    for d in get_supported_dialects():
        stats = get_dialect_stats(d)
        print(
            f"{d:12} : {stats['total_terms']} terms  "
            f"sample={stats['sample'][0]}"
        )