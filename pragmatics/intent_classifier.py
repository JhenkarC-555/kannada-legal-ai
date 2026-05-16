# pragmatics/intent_classifier.py
# Classifies the intent of a Kannada legal query.
#
# Intents:
#   section_lookup  — user wants info about a specific section
#   rights_query    — user asking about their legal rights
#   penalty_query   — user asking about punishment / fine
#   procedure_query — user asking how to do something legally
#   document_help   — user wants help drafting a document
#   general         — general legal question
#
# Uses rule-based pattern matching.
# Can be upgraded to ML classifier later.

import re
from dataclasses import dataclass
from loguru import logger


# ── Intent patterns ──────────────────────────────────────────
# Each intent has a list of regex patterns.
# Patterns checked against the full query (Kannada + English).

INTENT_PATTERNS = {

    "section_lookup": [
        r"section\s*\d+",
        r"ವಿಭಾಗ\s*\d+",
        r"ಸೆಕ್ಷನ್\s*\d+",
        r"\bipc\b",
        r"\bcrpc\b",
        r"\bcpc\b",
        r"\brti\b",
        r"ಕಾಯ್ದೆ\s*\d+",
        r"ಅಧಿನಿಯಮ\s*\d+",
        r"act\s*\d+",
    ],

    "rights_query": [
        r"ಹಕ್ಕು",
        r"ಹಕ್ಕುಗಳು",
        r"ಅಧಿಕಾರ",
        r"rights?",
        r"entitled",
        r"ರಕ್ಷಣೆ",
        r"ಸ್ವಾತಂತ್ರ್ಯ",
        r"freedom",
        r"liberty",
        r"ಮೂಲಭೂತ",
        r"fundamental",
        r"ನನ್ನ ಹಕ್ಕು",
        r"ಹಕ್ಕೇನು",
        r"ಹಕ್ಕಿದೆಯೇ",
    ],

    "penalty_query": [
        r"ಶಿಕ್ಷೆ",
        r"ದಂಡ",
        r"punishment",
        r"penalty",
        r"ಜೈಲು",
        r"imprisonment",
        r"ಜೀವಾವಧಿ",
        r"life\s*imprisonment",
        r"ಮರಣದಂಡನೆ",
        r"death\s*penalty",
        r"fine",
        r"ದಂಡ\s*ಎಷ್ಟು",
        r"ಶಿಕ್ಷೆ\s*ಏನು",
        r"ಎಷ್ಟು\s*ವರ್ಷ",
        r"how\s*many\s*years",
        r"ಕಠಿಣ",
        r"rigorous",
    ],

    "procedure_query": [
        r"ಹೇಗೆ",
        r"how\s*to",
        r"how\s*do",
        r"ಏನು\s*ಮಾಡ",
        r"what\s*to\s*do",
        r"process",
        r"procedure",
        r"steps?",
        r"ಹಂತ",
        r"FIR",
        r"ದೂರು\s*ಸಲ್ಲಿಸ",
        r"ದೂರು\s*ನೀಡ",
        r"complaint",
        r"ಅರ್ಜಿ\s*ಸಲ್ಲಿಸ",
        r"apply",
        r"ಜಾಮೀನು\s*ಪಡೆ",
        r"get\s*bail",
        r"ಠಾಣೆ",
        r"police\s*station",
        r"ನ್ಯಾಯಾಲಯಕ್ಕೆ\s*ಹೋಗ",
        r"go\s*to\s*court",
        r"ಎಲ್ಲಿ\s*ಹೋಗ",
        r"where\s*to\s*go",
    ],

    "document_help": [
        r"draft",
        r"ಬರೆ",
        r"write",
        r"petition",
        r"ಅರ್ಜಿ\s*ಬರೆ",
        r"affidavit",
        r"notice",
        r"agreement",
        r"ದಾಖಲೆ\s*ತಯಾರ",
        r"document\s*prepare",
        r"format",
        r"template",
        r"ಮಾದರಿ",
        r"ಪತ್ರ\s*ಬರೆ",
        r"letter\s*write",
    ],
}

# ── Confidence weights ────────────────────────────────────────
# How much each pattern match contributes to confidence.
# More specific patterns get higher weight.

PATTERN_WEIGHTS = {
    "section_lookup":  1.5,   # High — very specific
    "rights_query":    1.2,
    "penalty_query":   1.3,
    "procedure_query": 1.0,
    "document_help":   1.4,   # High — very specific
    "general":         0.5,
}


# ── Result dataclass ──────────────────────────────────────────
@dataclass
class IntentResult:
    """
    Holds the result of intent classification.

    Attributes:
        intent          : Detected intent string
        confidence      : Confidence score 0.0 to 1.0
        matched_patterns: List of patterns that matched
        all_scores      : Scores for all intents
        is_ambiguous    : True if top two intents are close
    """
    intent:           str
    confidence:       float
    matched_patterns: list
    all_scores:       dict
    is_ambiguous:     bool = False


# ── Classifier ───────────────────────────────────────────────
def classify(query: str) -> IntentResult:
    """
    Classify the intent of a Kannada legal query.

    Args:
        query : Raw user query string

    Returns:
        IntentResult with intent and confidence

    Examples:
        >>> result = classify("IPC ಸೆಕ್ಷನ್ 302 ಏನು?")
        >>> result.intent
        'section_lookup'
        >>> result.confidence
        0.9

        >>> result = classify("ಪೊಲೀಸ್ ಬಂಧಿಸಿದರೆ ನನ್ನ ಹಕ್ಕೇನು?")
        >>> result.intent
        'rights_query'

        >>> result = classify("ಕಳ್ಳತನಕ್ಕೆ ಎಷ್ಟು ಜೈಲು?")
        >>> result.intent
        'penalty_query'
    """
    if not query or not query.strip():
        logger.warning("classify: empty query.")
        return IntentResult(
            intent="general",
            confidence=0.0,
            matched_patterns=[],
            all_scores={},
            is_ambiguous=False,
        )

    query_lower = query.lower()
    scores      = {}
    matched     = {}

    # Score each intent
    for intent, patterns in INTENT_PATTERNS.items():
        intent_score    = 0.0
        intent_matches  = []

        for pattern in patterns:
            if re.search(pattern, query_lower, re.IGNORECASE):
                weight        = PATTERN_WEIGHTS.get(intent, 1.0)
                intent_score += weight
                intent_matches.append(pattern)

        if intent_score > 0:
            scores[intent]  = round(intent_score, 2)
            matched[intent] = intent_matches

    # No patterns matched — general intent
    if not scores:
        logger.info(f"classify: no patterns matched. Intent=general")
        return IntentResult(
            intent="general",
            confidence=0.5,
            matched_patterns=[],
            all_scores={},
            is_ambiguous=False,
        )

    # Find best intent
    best_intent = max(scores, key=lambda k: scores[k])
    total_score = sum(scores.values())
    confidence  = round(scores[best_intent] / total_score, 2)

    # Check ambiguity
    sorted_scores = sorted(scores.values(), reverse=True)
    is_ambiguous  = (
        len(sorted_scores) >= 2
        and (sorted_scores[0] - sorted_scores[1]) < 0.5
    )

    result = IntentResult(
        intent=best_intent,
        confidence=confidence,
        matched_patterns=matched.get(best_intent, []),
        all_scores=scores,
        is_ambiguous=is_ambiguous,
    )

    logger.info(
        f"classify: intent={result.intent} "
        f"confidence={result.confidence} "
        f"ambiguous={result.is_ambiguous}"
    )

    return result


def classify_batch(queries: list) -> list:
    """
    Classify a list of queries.

    Args:
        queries : List of query strings

    Returns:
        List of IntentResult objects

    Example:
        >>> results = classify_batch([
        ...     "IPC ಸೆಕ್ಷನ್ 302 ಏನು?",
        ...     "ಜಾಮೀನು ಹೇಗೆ ಪಡೆಯುವುದು?"
        ... ])
    """
    return [classify(q) for q in queries]


def get_intent_label(query: str) -> str:
    """
    Quick helper — returns just the intent string.

    Args:
        query : User query

    Returns:
        Intent string

    Example:
        >>> get_intent_label("ಕಳ್ಳತನಕ್ಕೆ ಶಿಕ್ಷೆ ಏನು?")
        'penalty_query'
    """
    return classify(query).intent


def get_intent_summary(result: IntentResult) -> str:
    """
    Returns human readable summary of classification result.

    Args:
        result : IntentResult object

    Returns:
        Formatted summary string
    """
    lines = [
        f"Intent           : {result.intent}",
        f"Confidence       : {result.confidence}",
        f"Is Ambiguous     : {result.is_ambiguous}",
        f"Matched Patterns : {result.matched_patterns}",
        f"All Scores       : {result.all_scores}",
    ]
    return "\n".join(lines)


# ── Quick test ───────────────────────────────────────────────
if __name__ == "__main__":

    test_queries = [
        # Section lookup
        ("IPC ಸೆಕ್ಷನ್ 302 ಏನು?",
         "section_lookup"),

        # Rights query
        ("ಪೊಲೀಸ್ ಬಂಧಿಸಿದರೆ ನನ್ನ ಹಕ್ಕೇನು?",
         "rights_query"),

        # Penalty query
        ("ಕಳ್ಳತನಕ್ಕೆ ಎಷ್ಟು ವರ್ಷ ಜೈಲು ಶಿಕ್ಷೆ?",
         "penalty_query"),

        # Procedure query
        ("FIR ದಾಖಲಿಸುವುದು ಹೇಗೆ?",
         "procedure_query"),

        # Document help
        ("ಜಾಮೀನು ಅರ್ಜಿ ಬರೆಯಲು ಸಹಾಯ ಮಾಡಿ",
         "document_help"),

        # Mixed — section + penalty
        ("IPC ಸೆಕ್ಷನ್ 420 ಶಿಕ್ಷೆ ಏನು?",
         "section_lookup or penalty_query"),

        # Mixed — rights + procedure
        ("ಪೊಲೀಸ್ ಬಂಧಿಸಿದರೆ ಏನು ಮಾಡಬೇಕು?",
         "rights_query or procedure_query"),

        # General
        ("ಕಾನೂನು ಸಹಾಯ ಬೇಕು",
         "general"),

        # English query
        ("What is the punishment for murder under IPC?",
         "penalty_query or section_lookup"),

        # Mixed language
        ("Section 302 ಅಡಿಯಲ್ಲಿ ಶಿಕ್ಷೆ ಏನು?",
         "section_lookup"),
    ]

    print("══════════════════════════════════════════")
    print("   Intent Classifier Test")
    print("══════════════════════════════════════════\n")

    correct = 0
    for query, expected in test_queries:
        result = classify(query)
        match  = "✅" if result.intent in expected else "⚠️"
        print(f"{match} Query    : {query}")
        print(f"   Expected : {expected}")
        print(get_intent_summary(result))
        print("-" * 55)