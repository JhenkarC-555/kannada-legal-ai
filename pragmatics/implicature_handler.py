# pragmatics/implicature_handler.py
# Handles implied meaning in Kannada legal queries.
#
# What is implicature?
#   User says : "ನನ್ನ ಮನೆ ಯಾರೋ ತೆಗೆದುಕೊಂಡು ಹೋದರು"
#               (Someone took my house)
#   User means: Property encroachment / criminal trespass
#               -> IPC Section 441/447
#
#   User says : "ನನ್ನ ಹಣ ವಾಪಸ್ ಕೊಡಲಿಲ್ಲ"
#               (They did not return my money)
#   User means: Cheating / breach of trust
#               -> IPC Section 420 / 406
#
# The model must understand what the user MEANS
# not just what they literally SAY.

import re
from dataclasses import dataclass
from loguru import logger


# ── Implicature result dataclass ─────────────────────────────
@dataclass
class ImplicatureResult:
    """
    Holds the result of implicature resolution.

    Attributes:
        detected        : True if implicature was detected
        original_query  : The raw user query
        resolved_hint   : Legal context hint for the query
        likely_sections : List of likely IPC/CrPC sections
        likely_offense  : Name of the likely legal offense
        confidence      : Confidence score 0.0 to 1.0
        trigger_phrase  : The phrase that triggered detection
    """
    detected:       bool
    original_query: str
    resolved_hint:  str
    likely_sections: list
    likely_offense: str
    confidence:     float
    trigger_phrase: str = ""


# ── Implicature rules ─────────────────────────────────────────
# Each rule has:
#   triggers  : list of Kannada/English phrases to match
#   offense   : legal offense name
#   sections  : relevant IPC/CrPC section numbers
#   hint      : legal context hint for retrieval
#   confidence: how confident we are in this mapping

IMPLICATURE_RULES = [

    # ── Property crimes ──────────────────────────────────────
    {
        "triggers": [
            "ಮನೆ ತೆಗೆದುಕೊಂಡು",
            "ಮನೆ ಆಕ್ರಮಿಸಿ",
            "ಜಮೀನು ಆಕ್ರಮಿಸಿ",
            "ಆಸ್ತಿ ಆಕ್ರಮಿಸಿ",
            "ಜಮೀನು ತೆಗೆದುಕೊಂಡ",
            "ಮನೆ ಒಕ್ಕಲೆಬ್ಬಿಸಿ",
            "ಆಸ್ತಿ ಕಬಳಿಸಿ",
            "ನನ್ನ ಜಮೀನು ಹೋಯಿತು",
            "encroachment",
            "property encroached",
        ],
        "offense":   "Criminal Trespass / Property Encroachment",
        "sections":  ["441", "447"],
        "hint": (
            "This appears to be a property encroachment case. "
            "IPC Section 441 defines criminal trespass. "
            "IPC Section 447 prescribes punishment for criminal trespass. "
            "Karnataka Land Revenue Act Section 94 deals with "
            "encroachment on government land."
        ),
        "confidence": 0.85,
    },

    # ── Financial fraud ──────────────────────────────────────
    {
        "triggers": [
            "ಹಣ ವಾಪಸ್ ಕೊಡಲಿಲ್ಲ",
            "ಹಣ ತಿರಿಗಿ ಕೊಡಲಿಲ್ಲ",
            "ಹಣ ಹಿಂತಿರುಗಿಸಲಿಲ್ಲ",
            "ದುಡ್ಡು ವಾಪಸ್ ಬರಲಿಲ್ಲ",
            "ಹಣ ಮೋಸ",
            "ಹಣ ಕೊಡಲಿಲ್ಲ",
            "ಸಾಲ ವಾಪಸ್ ಮಾಡಲಿಲ್ಲ",
            "cheated money",
            "money not returned",
            "fraud money",
        ],
        "offense":   "Cheating / Criminal Breach of Trust",
        "sections":  ["415", "420", "406"],
        "hint": (
            "This appears to be a cheating or breach of trust case. "
            "IPC Section 420 deals with cheating and dishonestly "
            "inducing delivery of property. "
            "IPC Section 406 deals with criminal breach of trust. "
            "Punishment under Section 420 is up to 7 years imprisonment."
        ),
        "confidence": 0.88,
    },

    # ── Physical assault ─────────────────────────────────────
    {
        "triggers": [
            "ಹೊಡೆದರು",
            "ಮಾರಿದರು",
            "ಹಲ್ಲೆ ಮಾಡಿದರು",
            "ಗಾಯ ಮಾಡಿದರು",
            "ಥಳಿಸಿದರು",
            "ಚಚ್ಚಿದರು",
            "ಹೊಡೆದು ಗಾಯ",
            "ಮೈ ಮೇಲೆ ಹಾಕಿದರು",
            "beat me",
            "attacked me",
            "physically hurt",
            "assault",
        ],
        "offense":   "Assault / Voluntarily Causing Hurt",
        "sections":  ["351", "323", "324", "325"],
        "hint": (
            "This appears to be an assault or hurt case. "
            "IPC Section 323 deals with voluntarily causing hurt "
            "— punishment up to 1 year or fine up to Rs.1000. "
            "IPC Section 325 deals with grievous hurt "
            "— punishment up to 7 years. "
            "File an FIR at the nearest police station."
        ),
        "confidence": 0.87,
    },

    # ── Threat / intimidation ────────────────────────────────
    {
        "triggers": [
            "ಬೆದರಿಕೆ ಹಾಕಿದರು",
            "ಬೆದರಿಕೆ ಒಡ್ಡಿದರು",
            "ಜೀವ ಬೆದರಿಕೆ",
            "ಕೊಲ್ಲುತ್ತೇನೆ ಎಂದರು",
            "ಹಾನಿ ಮಾಡುತ್ತೇನೆ ಎಂದರು",
            "ಭಯ ತೋರಿಸಿದರು",
            "threatening me",
            "death threat",
            "threatened",
            "intimidating",
        ],
        "offense":   "Criminal Intimidation",
        "sections":  ["503", "506"],
        "hint": (
            "This appears to be a criminal intimidation case. "
            "IPC Section 503 defines criminal intimidation as "
            "threatening another with injury to cause alarm. "
            "IPC Section 506 prescribes punishment "
            "— up to 2 years imprisonment or fine or both. "
            "For death threats, punishment extends to 7 years."
        ),
        "confidence": 0.90,
    },

    # ── Domestic violence ────────────────────────────────────
    {
        "triggers": [
            "ಗಂಡ ಹೊಡೆಯುತ್ತಾನೆ",
            "ಗಂಡ ಹಿಂಸೆ ಕೊಡುತ್ತಾನೆ",
            "ಮನೆಯಲ್ಲಿ ಹಿಂಸೆ",
            "ಕೌಟುಂಬಿಕ ಹಿಂಸೆ",
            "ಗಂಡ ಮಾರುತ್ತಾನೆ",
            "ಅತ್ತೆ ಹಿಂಸೆ",
            "ವರದಕ್ಷಿಣೆ ಕಿರುಕುಳ",
            "husband beats",
            "domestic violence",
            "husband harassing",
            "dowry harassment",
        ],
        "offense":   "Domestic Violence / Dowry Harassment",
        "sections":  ["498A", "3", "4"],
        "hint": (
            "This appears to be a domestic violence case. "
            "IPC Section 498A deals with husband or relatives "
            "subjecting a woman to cruelty — punishment up to 3 years. "
            "Protection of Women from Domestic Violence Act 2005 "
            "provides protection orders, residence orders "
            "and monetary relief. "
            "Call helpline 181 for immediate assistance."
        ),
        "confidence": 0.92,
    },

    # ── Sexual harassment ────────────────────────────────────
    {
        "triggers": [
            "ಕಿರುಕುಳ ನೀಡಿದರು",
            "ಮಾನ ಕ್ಷುಣ್ಣ",
            "ಅಸಭ್ಯ ಮಾತು",
            "ಲೈಂಗಿಕ ಕಿರುಕುಳ",
            "ಸೀಟಿ ಹೊಡೆದರು",
            "ಅಸಭ್ಯ ಸನ್ನೆ",
            "ಮಾನ ತೆಗೆದರು",
            "sexual harassment",
            "eve teasing",
            "outrage modesty",
            "inappropriate touch",
        ],
        "offense":   "Sexual Harassment / Outraging Modesty",
        "sections":  ["354", "354A", "509"],
        "hint": (
            "This appears to be a sexual harassment case. "
            "IPC Section 354 deals with assault or criminal force "
            "to a woman with intent to outrage her modesty "
            "— punishment up to 2 years. "
            "IPC Section 354A deals with sexual harassment "
            "— punishment up to 3 years. "
            "IPC Section 509 deals with words or gestures "
            "intended to insult a woman's modesty. "
            "Call helpline 1091 (Women's helpline) or 181."
        ),
        "confidence": 0.91,
    },

    # ── Defamation / false information ───────────────────────
    {
        "triggers": [
            "ಸುಳ್ಳು ಹರಡಿದರು",
            "ಸುಳ್ಳು ಆರೋಪ",
            "ಮಾನ ಹಾನಿ",
            "ಅಪಪ್ರಚಾರ",
            "ಹೆಸರು ಕೆಡಿಸಿದರು",
            "ಸುಳ್ಳು ಸುದ್ದಿ",
            "false accusation",
            "defamation",
            "spreading lies",
            "false news about me",
            "ruining reputation",
        ],
        "offense":   "Defamation",
        "sections":  ["499", "500"],
        "hint": (
            "This appears to be a defamation case. "
            "IPC Section 499 defines defamation as making or "
            "publishing any imputation concerning a person "
            "intending to harm their reputation. "
            "IPC Section 500 prescribes punishment "
            "— simple imprisonment up to 2 years or fine or both. "
            "You can also file a civil suit for damages."
        ),
        "confidence": 0.83,
    },

    # ── Theft / robbery ──────────────────────────────────────
    {
        "triggers": [
            "ಕದ್ದರು",
            "ಕಳ್ಳತನ ಆಯಿತು",
            "ಚೀಲ ಕದ್ದರು",
            "ಫೋನ್ ಕದ್ದರು",
            "ವಸ್ತು ಕದ್ದರು",
            "ದರೋಡೆ ಮಾಡಿದರು",
            "ಲೂಟಿ ಮಾಡಿದರು",
            "stolen",
            "theft",
            "robbed",
            "snatched",
            "bag snatched",
        ],
        "offense":   "Theft / Robbery",
        "sections":  ["378", "379", "390", "392"],
        "hint": (
            "This appears to be a theft or robbery case. "
            "IPC Section 379 deals with punishment for theft "
            "— up to 3 years imprisonment or fine or both. "
            "IPC Section 392 deals with robbery "
            "— up to 10 years rigorous imprisonment. "
            "File an FIR immediately at the nearest police station. "
            "For chain/phone snatching file under Section 356 also."
        ),
        "confidence": 0.89,
    },

    # ── RTI / government information ─────────────────────────
    {
        "triggers": [
            "ಸರ್ಕಾರ ಮಾಹಿತಿ ಕೊಡಲಿಲ್ಲ",
            "ಇಲಾಖೆ ಉತ್ತರ ಕೊಡಲಿಲ್ಲ",
            "ಅಧಿಕಾರಿ ಮಾಹಿತಿ ನಿರಾಕರಿಸಿದ",
            "RTI ಉತ್ತರ ಬರಲಿಲ್ಲ",
            "government not giving information",
            "officer refused information",
            "no reply to RTI",
        ],
        "offense":   "RTI Violation",
        "sections":  ["6", "7", "18", "19"],
        "hint": (
            "This appears to be an RTI violation case. "
            "RTI Act 2005 Section 7 mandates information "
            "must be provided within 30 days. "
            "If denied, file first appeal under Section 19(1) "
            "with the first appellate authority within 30 days. "
            "If still denied, file second appeal with the "
            "State Information Commission under Section 19(3)."
        ),
        "confidence": 0.86,
    },

    # ── Police misconduct ────────────────────────────────────
    {
        "triggers": [
            "ಪೊಲೀಸ್ ಹೊಡೆದರು",
            "ಪೊಲೀಸ್ ದೌರ್ಜನ್ಯ",
            "ಠಾಣೆಯಲ್ಲಿ ಹಿಂಸಿಸಿದರು",
            "ಪೊಲೀಸ್ ಲಂಚ ಕೇಳಿದರು",
            "ಸುಳ್ಳು ಕೇಸ್ ಹಾಕಿದರು",
            "ಪೊಲೀಸ್ FIR ತೆಗೆದುಕೊಳ್ಳಲಿಲ್ಲ",
            "police beat me",
            "police brutality",
            "false case filed",
            "police refused FIR",
            "police bribe",
        ],
        "offense":   "Police Misconduct",
        "sections":  ["154", "166", "330"],
        "hint": (
            "This appears to be a police misconduct case. "
            "If police refuse to file FIR, approach the "
            "Superintendent of Police or Magistrate. "
            "IPC Section 166 deals with public servant "
            "disobeying law — up to 1 year imprisonment. "
            "IPC Section 330 deals with causing hurt to "
            "extort confession. "
            "File complaint with State Human Rights Commission "
            "or High Court."
        ),
        "confidence": 0.84,
    },

    # ── Consumer complaint ───────────────────────────────────
    {
        "triggers": [
            "ಕೆಟ್ಟ ವಸ್ತು ಮಾರಿದರು",
            "ನಕಲಿ ವಸ್ತು",
            "ಸೇವೆ ನೀಡಲಿಲ್ಲ",
            "ದುಡ್ಡು ವಾಪಸ್ ಕೊಡಲಿಲ್ಲ",
            "ಹಣ ಮರಳಿಸಲಿಲ್ಲ",
            "ಕಂಪನಿ ಮೋಸ",
            "defective product",
            "fake product",
            "service not provided",
            "refund not given",
            "company cheated",
            "bad service",
        ],
        "offense":   "Consumer Complaint",
        "sections":  ["2", "35", "36"],
        "hint": (
            "This appears to be a consumer complaint case. "
            "Consumer Protection Act 2019 protects buyers "
            "of goods and services. "
            "File complaint at District Consumer Disputes "
            "Redressal Commission for claims up to Rs.20 lakhs. "
            "No lawyer needed to file the complaint. "
            "Keep all bills, receipts and communication as evidence."
        ),
        "confidence": 0.82,
    },
]


# ── Core resolve function ─────────────────────────────────────
def resolve(query: str) -> ImplicatureResult:
    """
    Resolve implied legal meaning from a Kannada query.

    Args:
        query : Raw user query string

    Returns:
        ImplicatureResult with detected offense and hints

    Examples:
        >>> result = resolve("ನನ್ನ ಮನೆ ಯಾರೋ ತೆಗೆದುಕೊಂಡು ಹೋದರು")
        >>> result.detected
        True
        >>> result.likely_offense
        'Criminal Trespass / Property Encroachment'
        >>> result.likely_sections
        ['441', '447']

        >>> result = resolve("IPC ಸೆಕ್ಷನ್ 302 ಏನು?")
        >>> result.detected
        False
    """
    if not query or not query.strip():
        return ImplicatureResult(
            detected=False,
            original_query=query,
            resolved_hint="",
            likely_sections=[],
            likely_offense="",
            confidence=0.0,
        )

    query_lower = query.lower()
    best_match  = None
    best_score  = 0.0
    trigger_found = ""

    # Check each rule
    for rule in IMPLICATURE_RULES:
        for trigger in rule["triggers"]:
            if trigger.lower() in query_lower:
                score = rule["confidence"]
                if score > best_score:
                    best_score  = score
                    best_match  = rule
                    trigger_found = trigger

    # No implicature detected
    if not best_match:
        logger.info(f"resolve: no implicature detected in query.")
        return ImplicatureResult(
            detected=False,
            original_query=query,
            resolved_hint="",
            likely_sections=[],
            likely_offense="",
            confidence=0.0,
        )

    # Implicature detected
    logger.info(
        f"resolve: implicature detected.\n"
        f"        Offense  : {best_match['offense']}\n"
        f"        Sections : {best_match['sections']}\n"
        f"        Trigger  : '{trigger_found}'\n"
        f"        Confidence: {best_match['confidence']}"
    )

    return ImplicatureResult(
        detected=True,
        original_query=query,
        resolved_hint=best_match["hint"],
        likely_sections=best_match["sections"],
        likely_offense=best_match["offense"],
        confidence=best_match["confidence"],
        trigger_phrase=trigger_found,
    )


def get_hint(query: str) -> str:
    """
    Quick helper — returns just the legal hint string.
    Returns empty string if no implicature detected.

    Args:
        query : User query

    Returns:
        Legal hint string or empty string

    Example:
        >>> get_hint("ಹಣ ವಾಪಸ್ ಕೊಡಲಿಲ್ಲ")
        'This appears to be a cheating or breach of trust case...'
    """
    result = resolve(query)
    return result.resolved_hint if result.detected else ""


def get_sections(query: str) -> list:
    """
    Quick helper — returns likely sections for a query.

    Args:
        query : User query

    Returns:
        List of section number strings

    Example:
        >>> get_sections("ನನ್ನ ಮನೆ ಆಕ್ರಮಿಸಿದರು")
        ['441', '447']
    """
    result = resolve(query)
    return result.likely_sections if result.detected else []


def get_implicature_summary(result: ImplicatureResult) -> str:
    """
    Returns human readable summary of implicature result.

    Args:
        result : ImplicatureResult object

    Returns:
        Formatted summary string
    """
    if not result.detected:
        return "No implicature detected."

    lines = [
        f"Detected        : {result.detected}",
        f"Likely Offense  : {result.likely_offense}",
        f"Likely Sections : {result.likely_sections}",
        f"Confidence      : {result.confidence}",
        f"Trigger Phrase  : '{result.trigger_phrase}'",
        f"Legal Hint      : {result.resolved_hint[:100]}...",
    ]
    return "\n".join(lines)


# ── Quick test ───────────────────────────────────────────────
if __name__ == "__main__":

    test_queries = [
        # Property
        ("ನನ್ನ ಮನೆ ಯಾರೋ ತೆಗೆದುಕೊಂಡು ಹೋದರು",
         "Criminal Trespass"),

        # Financial fraud
        ("ಅವರು ನನ್ನ ಹಣ ವಾಪಸ್ ಕೊಡಲಿಲ್ಲ",
         "Cheating"),

        # Assault
        ("ನೆರೆಯವರು ನನ್ನನ್ನು ಹೊಡೆದರು",
         "Assault"),

        # Threat
        ("ಅವರು ನನಗೆ ಜೀವ ಬೆದರಿಕೆ ಹಾಕಿದರು",
         "Criminal Intimidation"),

        # Domestic violence
        ("ನನ್ನ ಗಂಡ ನನ್ನನ್ನು ಹೊಡೆಯುತ್ತಾನೆ",
         "Domestic Violence"),

        # Sexual harassment
        ("ಕಚೇರಿಯಲ್ಲಿ ನನಗೆ ಲೈಂಗಿಕ ಕಿರುಕುಳ ನೀಡಿದರು",
         "Sexual Harassment"),

        # Defamation
        ("ಅವರು ನನ್ನ ಬಗ್ಗೆ ಸುಳ್ಳು ಹರಡಿದರು",
         "Defamation"),

        # Theft
        ("ನನ್ನ ಫೋನ್ ಕದ್ದರು",
         "Theft"),

        # Consumer
        ("ಅಂಗಡಿಯವರು ಕೆಟ್ಟ ವಸ್ತು ಮಾರಿದರು",
         "Consumer Complaint"),

        # Police
        ("ಪೊಲೀಸ್ FIR ತೆಗೆದುಕೊಳ್ಳಲಿಲ್ಲ",
         "Police Misconduct"),

        # No implicature — direct query
        ("IPC ಸೆಕ್ಷನ್ 302 ಏನು?",
         "No implicature"),
    ]

    print("══════════════════════════════════════════")
    print("   Implicature Handler Test")
    print("══════════════════════════════════════════\n")

    for query, expected in test_queries:
        result = resolve(query)
        icon   = "✅" if result.detected else "ℹ️"
        print(f"{icon} Query    : {query}")
        print(f"   Expected : {expected}")
        print(get_implicature_summary(result))
        print("-" * 55)