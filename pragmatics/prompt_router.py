# pragmatics/prompt_router.py
# Routes a classified intent to the correct system prompt template.
# Also handles disclaimer injection and prompt formatting.
#
# This is the final layer before the LLM receives the prompt.
#
# Flow:
#   Intent -> get_system_prompt() -> build full prompt
#   Response -> add_disclaimer()  -> return to user

from loguru import logger


# ── Disclaimer ────────────────────────────────────────────────
DISCLAIMER_KN = (
    "\n\n---\n"
    "⚠️ **ಪ್ರಮುಖ ಸೂಚನೆ:** ಇದು ಕಾನೂನು ಸಲಹೆ ಅಲ್ಲ. "
    "ಈ ಮಾಹಿತಿ ಕೇವಲ ಸಾಮಾನ್ಯ ಜ್ಞಾನಕ್ಕಾಗಿ ಮಾತ್ರ. "
    "ನಿಮ್ಮ ನಿರ್ದಿಷ್ಟ ಕಾನೂನು ಪ್ರಕರಣಕ್ಕೆ ಅರ್ಹ ವಕೀಲರನ್ನು "
    "ಸಂಪರ್ಕಿಸಿ."
)

DISCLAIMER_EN = (
    "\n\n---\n"
    "⚠️ **Important:** This is not legal advice. "
    "This information is for general awareness only. "
    "Please consult a qualified lawyer for your specific case."
)


# ── System prompt templates ───────────────────────────────────
# One template per intent.
# Each template sets the role and behavior of the LLM.

SYSTEM_PROMPTS = {

    "section_lookup": (
        "ನೀವು ಒಬ್ಬ ಅನುಭವಿ ಕನ್ನಡ ಕಾನೂನು ತಜ್ಞ.\n"
        "ನಿಯಮಗಳು:\n"
        "1. ಕೇಳಿದ ವಿಭಾಗದ ಸಂಪೂರ್ಣ ವ್ಯಾಖ್ಯಾನ ನೀಡಿ\n"
        "2. ವಿಭಾಗ ಸಂಖ್ಯೆ ಮತ್ತು ಕಾನೂನಿನ ಹೆಸರು ಯಾವಾಗಲೂ "
        "ಉಲ್ಲೇಖಿಸಿ\n"
        "3. ಸರಳ ಕನ್ನಡದಲ್ಲಿ ವಿವರಿಸಿ\n"
        "4. ಸಂಬಂಧಿತ ವಿಭಾಗಗಳನ್ನೂ ತಿಳಿಸಿ\n"
        "5. ಉದಾಹರಣೆ ನೀಡಿ\n"
        "6. ತಪ್ಪು ಮಾಹಿತಿ ನೀಡಬೇಡಿ"
    ),

    "rights_query": (
        "ನೀವು ಒಬ್ಬ ಕನ್ನಡ ಕಾನೂನು ಸಹಾಯಕ.\n"
        "ನಿಯಮಗಳು:\n"
        "1. ವ್ಯಕ್ತಿಯ ಕಾನೂನು ಹಕ್ಕುಗಳನ್ನು ಸ್ಪಷ್ಟವಾಗಿ ವಿವರಿಸಿ\n"
        "2. ಸರಳ ಕನ್ನಡ ಬಳಸಿ — ಕಾನೂನು ಪರಿಭಾಷೆ ತಪ್ಪಿಸಿ\n"
        "3. ಸಂಬಂಧಿತ ಕಾನೂನು ವಿಭಾಗಗಳನ್ನು ಉಲ್ಲೇಖಿಸಿ\n"
        "4. ಹಕ್ಕು ಉಲ್ಲಂಘನೆ ಆದಾಗ ಏನು ಮಾಡಬೇಕು "
        "ಎಂದು ತಿಳಿಸಿ\n"
        "5. ಸಹಾಯ ಸಂಖ್ಯೆ ಮತ್ತು ಸಂಪನ್ಮೂಲಗಳನ್ನು ನೀಡಿ"
    ),

    "penalty_query": (
        "ನೀವು ಒಬ್ಬ ಕನ್ನಡ ಕಾನೂನು ತಜ್ಞ.\n"
        "ನಿಯಮಗಳು:\n"
        "1. ಶಿಕ್ಷೆ ಮತ್ತು ದಂಡದ ನಿಖರ ವಿವರ ನೀಡಿ\n"
        "2. ಸಂಬಂಧಿತ ವಿಭಾಗ ಸಂಖ್ಯೆ ಉಲ್ಲೇಖಿಸಿ\n"
        "3. ಕನಿಷ್ಠ ಮತ್ತು ಗರಿಷ್ಠ ಶಿಕ್ಷೆ ಎರಡನ್ನೂ ತಿಳಿಸಿ\n"
        "4. ಜಾಮೀನು ಸಾಧ್ಯತೆ ತಿಳಿಸಿ\n"
        "5. ಅಂದಾಜು ಶಿಕ್ಷೆ ನೀಡಬೇಡಿ — "
        "ನಿಖರ ಕಾನೂನು ಮಾಹಿತಿ ಮಾತ್ರ"
    ),

    "procedure_query": (
        "ನೀವು ಒಬ್ಬ ಕನ್ನಡ ಕಾನೂನು ಮಾರ್ಗದರ್ಶಕ.\n"
        "ನಿಯಮಗಳು:\n"
        "1. ಹಂತ-ಹಂತವಾಗಿ ಪ್ರಕ್ರಿಯೆ ವಿವರಿಸಿ\n"
        "2. ಅಗತ್ಯ ದಾಖಲೆಗಳ ಪಟ್ಟಿ ನೀಡಿ\n"
        "3. ಎಲ್ಲಿ ಹೋಗಬೇಕು ಎಂದು ತಿಳಿಸಿ\n"
        "4. ಸಮಯ ಮಿತಿ ಇದ್ದರೆ ತಿಳಿಸಿ\n"
        "5. ಶುಲ್ಕ ಮತ್ತು ವೆಚ್ಚದ ಬಗ್ಗೆ ತಿಳಿಸಿ\n"
        "6. ಉಚಿತ ಕಾನೂನು ಸಹಾಯ ಲಭ್ಯವಿದ್ದರೆ ತಿಳಿಸಿ"
    ),

    "document_help": (
        "ನೀವು ಒಬ್ಬ ಕನ್ನಡ ಕಾನೂನು ಲೇಖಕ.\n"
        "ನಿಯಮಗಳು:\n"
        "1. ಔಪಚಾರಿಕ ಕನ್ನಡ ಭಾಷೆ ಬಳಸಿ\n"
        "2. ದಾಖಲೆಯ ಸರಿಯಾದ ಮಾದರಿ ನೀಡಿ\n"
        "3. ಅಗತ್ಯ ವಿವರಗಳನ್ನು [ಇಲ್ಲಿ ಭರ್ತಿ ಮಾಡಿ] "
        "ಎಂದು ಗುರುತಿಸಿ\n"
        "4. ದಾಖಲೆ ಯಾರಿಗೆ ಸಲ್ಲಿಸಬೇಕು ತಿಳಿಸಿ\n"
        "5. ಅಂಚೆ ಮತ್ತು ಡಿಜಿಟಲ್ ಸಲ್ಲಿಕೆ ಮಾಹಿತಿ ನೀಡಿ"
    ),

    "general": (
        "ನೀವು ಒಬ್ಬ ಸಹಾಯಕ ಕನ್ನಡ ಕಾನೂನು ಸಲಹೆಗಾರ.\n"
        "ನಿಯಮಗಳು:\n"
        "1. ಸರಳ ಮತ್ತು ಸ್ಪಷ್ಟ ಕನ್ನಡದಲ್ಲಿ ಉತ್ತರಿಸಿ\n"
        "2. ಅಗತ್ಯವಿದ್ದರೆ ಹೆಚ್ಚಿನ ಮಾಹಿತಿ ಕೇಳಿ\n"
        "3. ಸಂಬಂಧಿತ ಕಾನೂನು ವಿಭಾಗಗಳನ್ನು ಉಲ್ಲೇಖಿಸಿ\n"
        "4. ತಿಳಿಯದ ವಿಷಯ ಹೇಳಲು ಮುಜುಗರ ಪಡಬೇಡಿ"
    ),
}

# ── Intent display names ──────────────────────────────────────
INTENT_DISPLAY_NAMES = {
    "section_lookup":  "ವಿಭಾಗ ಮಾಹಿತಿ",
    "rights_query":    "ಹಕ್ಕುಗಳ ಮಾಹಿತಿ",
    "penalty_query":   "ಶಿಕ್ಷೆ ಮಾಹಿತಿ",
    "procedure_query": "ಪ್ರಕ್ರಿಯೆ ಮಾಹಿತಿ",
    "document_help":   "ದಾಖಲೆ ಸಹಾಯ",
    "general":         "ಸಾಮಾನ್ಯ ಸಹಾಯ",
}

# ── Helpline numbers ──────────────────────────────────────────
# Added to responses for relevant intents.
HELPLINES = {
    "women":    "181 (ಮಹಿಳಾ ಸಹಾಯವಾಣಿ)",
    "police":   "100 (ಪೊಲೀಸ್)",
    "legal_aid":"15100 (ರಾಷ್ಟ್ರೀಯ ಕಾನೂನು ಸೇವೆ)",
    "consumer": "1800-11-4000 (ಗ್ರಾಹಕ ಸಹಾಯ)",
    "child":    "1098 (ಮಕ್ಕಳ ಸಹಾಯ)",
}


# ── Core functions ────────────────────────────────────────────
def get_system_prompt(intent: str) -> str:
    """
    Get the system prompt for a given intent.

    Args:
        intent : Intent string from intent_classifier

    Returns:
        System prompt string for the LLM

    Example:
        >>> prompt = get_system_prompt("section_lookup")
        >>> print(prompt[:50])
        'ನೀವು ಒಬ್ಬ ಅನುಭವಿ ಕನ್ನಡ ಕಾನೂನು ತಜ್ಞ.'
    """
    prompt = SYSTEM_PROMPTS.get(
        intent,
        SYSTEM_PROMPTS["general"]
    )
    logger.debug(f"System prompt selected for intent: {intent}")
    return prompt


def add_disclaimer(
    response: str,
    language: str = "kn",
) -> str:
    """
    Add legal disclaimer to a response.

    Args:
        response : LLM response text
        language : 'kn' for Kannada, 'en' for English

    Returns:
        Response with disclaimer appended

    Example:
        >>> response = "ಸೆಕ್ಷನ್ 302 ಕೊಲೆಗೆ ಶಿಕ್ಷೆ ವಿಧಿಸುತ್ತದೆ."
        >>> add_disclaimer(response)
        'ಸೆಕ್ಷನ್ 302 ಕೊಲೆಗೆ...\n\n⚠️ ಇದು ಕಾನೂನು ಸಲಹೆ ಅಲ್ಲ...'
    """
    disclaimer = (
        DISCLAIMER_KN if language == "kn"
        else DISCLAIMER_EN
    )
    return response.strip() + disclaimer


def build_full_prompt(
    question:   str,
    context:    str,
    intent:     str,
    history:    str  = "",
    implicature: str = "",
) -> str:
    """
    Build the complete LLM prompt with all components.

    Components:
        1. System prompt  (role + rules)
        2. History        (previous conversation turns)
        3. Implicature    (implied legal context if detected)
        4. Retrieved context (legal documents)
        5. Question       (user query)

    Args:
        question    : User query string
        context     : Retrieved legal context from RAG
        intent      : Detected intent
        history     : Conversation history string (optional)
        implicature : Implicature hint string (optional)

    Returns:
        Complete prompt string ready for LLM

    Example:
        >>> prompt = build_full_prompt(
        ...     question="IPC ಸೆಕ್ಷನ್ 302 ಏನು?",
        ...     context="Section 302 — Murder...",
        ...     intent="section_lookup",
        ... )
    """
    parts = []

    # ── 1. System prompt ─────────────────────────────────────
    system = get_system_prompt(intent)
    parts.append(f"[ವ್ಯವಸ್ಥೆ]\n{system}")

    # ── 2. Conversation history ──────────────────────────────
    if history and history.strip():
        parts.append(f"[ಹಿಂದಿನ ಸಂವಾದ]\n{history}")

    # ── 3. Implicature hint ──────────────────────────────────
    if implicature and implicature.strip():
        parts.append(
            f"[ಸಂದರ್ಭ ಸುಳಿವು]\n{implicature}"
        )

    # ── 4. Legal context ─────────────────────────────────────
    if context and context.strip():
        parts.append(f"[ಕಾನೂನು ಮಾಹಿತಿ]\n{context}")
    else:
        parts.append(
            "[ಕಾನೂನು ಮಾಹಿತಿ]\n"
            "ಯಾವುದೇ ನೇರ ಮಾಹಿತಿ ದೊರೆಯಲಿಲ್ಲ. "
            "ಸಾಮಾನ್ಯ ಕಾನೂನು ಜ್ಞಾನ ಬಳಸಿ ಉತ್ತರಿಸಿ."
        )

    # ── 5. Question ──────────────────────────────────────────
    parts.append(f"[ಪ್ರಶ್ನೆ]\n{question}")

    # ── 6. Answer trigger ────────────────────────────────────
    parts.append("[ಉತ್ತರ]")

    full_prompt = "\n\n".join(parts)

    logger.info(
        f"Prompt built.\n"
        f"        Intent   : {intent}\n"
        f"        Length   : {len(full_prompt)} chars\n"
        f"        History  : {'Yes' if history else 'No'}\n"
        f"        Implctr  : {'Yes' if implicature else 'No'}"
    )

    return full_prompt


def get_intent_display_name(intent: str) -> str:
    """
    Get human readable Kannada display name for an intent.

    Args:
        intent : Intent string

    Returns:
        Kannada display name

    Example:
        >>> get_intent_display_name("section_lookup")
        'ವಿಭಾಗ ಮಾಹಿತಿ'
    """
    return INTENT_DISPLAY_NAMES.get(intent, "ಸಾಮಾನ್ಯ ಸಹಾಯ")


def get_relevant_helplines(intent: str) -> str:
    """
    Get relevant helpline numbers for an intent.

    Args:
        intent : Intent string

    Returns:
        Formatted helpline string or empty string

    Example:
        >>> get_relevant_helplines("rights_query")
        '📞 ಸಹಾಯವಾಣಿ: 181 | 100 | 15100'
    """
    relevant = []

    if intent in ["rights_query", "procedure_query", "general"]:
        relevant.append(HELPLINES["legal_aid"])
        relevant.append(HELPLINES["police"])

    if intent in ["document_help", "procedure_query"]:
        relevant.append(HELPLINES["legal_aid"])

    if not relevant:
        return ""

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for h in relevant:
        if h not in seen:
            unique.append(h)
            seen.add(h)

    return "📞 ಸಹಾಯವಾಣಿ: " + " | ".join(unique)


def format_response(
    response:   str,
    intent:     str,
    language:   str  = "kn",
    add_help:   bool = True,
) -> str:
    """
    Format the final response with disclaimer and helplines.

    Args:
        response  : Raw LLM response text
        intent    : Detected intent
        language  : Response language ('kn' or 'en')
        add_help  : Whether to add helpline numbers

    Returns:
        Fully formatted response string

    Example:
        >>> formatted = format_response(
        ...     response="ಸೆಕ್ಷನ್ 302 ಕೊಲೆಗೆ ಶಿಕ್ಷೆ...",
        ...     intent="section_lookup",
        ... )
    """
    result = response.strip()

    # Add helplines if relevant
    if add_help:
        helplines = get_relevant_helplines(intent)
        if helplines:
            result += f"\n\n{helplines}"

    # Add disclaimer
    result = add_disclaimer(result, language)

    return result


def get_prompt_summary(
    intent:     str,
    has_history: bool = False,
    has_implicature: bool = False,
) -> str:
    """
    Returns a summary of what the prompt will contain.

    Args:
        intent          : Intent string
        has_history     : True if conversation history present
        has_implicature : True if implicature hint present

    Returns:
        Summary string
    """
    lines = [
        f"Intent          : {intent}",
        f"Display Name    : {get_intent_display_name(intent)}",
        f"System Prompt   : {get_system_prompt(intent)[:60]}...",
        f"Has History     : {has_history}",
        f"Has Implicature : {has_implicature}",
        f"Helplines       : {get_relevant_helplines(intent)}",
    ]
    return "\n".join(lines)


# ── Quick test ───────────────────────────────────────────────
if __name__ == "__main__":

    print("══════════════════════════════════════════")
    print("   Prompt Router Test")
    print("══════════════════════════════════════════\n")

    # Test all intents
    intents = [
        "section_lookup",
        "rights_query",
        "penalty_query",
        "procedure_query",
        "document_help",
        "general",
    ]

    print("── System Prompts ──\n")
    for intent in intents:
        name   = get_intent_display_name(intent)
        prompt = get_system_prompt(intent)
        help_  = get_relevant_helplines(intent)
        print(f"Intent  : {intent}")
        print(f"Name    : {name}")
        print(f"Prompt  : {prompt[:80]}...")
        print(f"Helpline: {help_ or 'None'}")
        print("-" * 55)

    # Test full prompt building
    print("\n── Full Prompt Build Test ──\n")

    prompt = build_full_prompt(
        question="IPC ಸೆಕ್ಷನ್ 302 ಅಡಿಯಲ್ಲಿ ಶಿಕ್ಷೆ ಏನು?",
        context=(
            "[1] IPC ವಿಭಾಗ 302 (ಕನ್ನಡ):\n"
            "ಯಾರಾದರೂ ಕೊಲೆ ಮಾಡಿದರೆ ಮರಣದಂಡನೆ "
            "ಅಥವಾ ಜೀವಾವಧಿ ಶಿಕ್ಷೆ."
        ),
        intent="section_lookup",
        history="ಬಳಕೆದಾರ: IPC ಎಂದರೇನು?\nಸಹಾಯಕ: IPC ಭಾರತೀಯ ದಂಡ ಸಂಹಿತೆ.",
        implicature="This appears to be a murder punishment query.",
    )

    print(prompt)

    # Test response formatting
    print("\n── Response Formatting Test ──\n")

    raw_response = (
        "IPC ಸೆಕ್ಷನ್ 302 ಅಡಿಯಲ್ಲಿ ಕೊಲೆ ಮಾಡಿದವರಿಗೆ "
        "ಮರಣದಂಡನೆ ಅಥವಾ ಜೀವಾವಧಿ ಕಾರಾಗೃಹ ಶಿಕ್ಷೆ "
        "ವಿಧಿಸಲಾಗುತ್ತದೆ ಮತ್ತು ದಂಡ ಕೂಡ ವಿಧಿಸಬಹುದು."
    )

    formatted = format_response(
        response=raw_response,
        intent="penalty_query",
        language="kn",
        add_help=True,
    )

    print("Raw Response:")
    print(raw_response)
    print("\nFormatted Response:")
    print(formatted)