# nlp/tokenizer_kannada.py
# Kannada tokenizer using IndicNLP library.
# Falls back to whitespace tokenizer if IndicNLP is unavailable.

from loguru import logger

try:
    from indicnlp.tokenize import indic_tokenize
    INDICNLP_AVAILABLE = True
    logger.info("IndicNLP tokenizer loaded successfully.")
except ImportError:
    INDICNLP_AVAILABLE = False
    logger.warning(
        "IndicNLP not found — using whitespace tokenizer fallback. "
        "Install with: pip install indic-nlp-library"
    )


def tokenize(text: str, lang: str = "kn") -> list:
    """
    Tokenize Kannada text into word tokens.

    Args:
        text : Input Kannada text string
        lang : Language code (default 'kn' for Kannada)

    Returns:
        List of word tokens

    Example:
        >>> tokenize("ನಾನು ಕನ್ನಡ ಮಾತನಾಡುತ್ತೇನೆ")
        ['ನಾನು', 'ಕನ್ನಡ', 'ಮಾತನಾಡುತ್ತೇನೆ']
    """
    if not text or not text.strip():
        return []

    if INDICNLP_AVAILABLE:
        try:
            return indic_tokenize.trivial_tokenize(text, lang)
        except Exception as e:
            logger.warning(f"IndicNLP tokenization failed: {e}. Using fallback.")
            return text.split()

    return text.split()


def detokenize(tokens: list) -> str:
    """
    Join tokens back into a single string.

    Args:
        tokens : List of word tokens

    Returns:
        Joined string

    Example:
        >>> detokenize(['ನಾನು', 'ಕನ್ನಡ', 'ಮಾತನಾಡುತ್ತೇನೆ'])
        'ನಾನು ಕನ್ನಡ ಮಾತನಾಡುತ್ತೇನೆ'
    """
    if not tokens:
        return ""
    return " ".join(tokens)


def tokenize_sentences(text: str) -> list:
    """
    Split Kannada text into sentences.
    Splits on common Kannada sentence-ending punctuation.

    Args:
        text : Input Kannada paragraph

    Returns:
        List of sentences

    Example:
        >>> tokenize_sentences("ನಾನು ಹೋದೆ. ಅವರು ಬಂದರು.")
        ['ನಾನು ಹೋದೆ.', 'ಅವರು ಬಂದರು.']
    """
    if not text or not text.strip():
        return []

    if INDICNLP_AVAILABLE:
        try:
            from indicnlp.sent_tokenize import indic_sent_tokenize
            return indic_sent_tokenize.sentence_split(text, lang="kn")
        except Exception as e:
            logger.warning(f"Sentence tokenization failed: {e}. Using fallback.")

    # Fallback — split on punctuation
    import re
    sentences = re.split(r"[।\.!\?]+", text)
    return [s.strip() for s in sentences if s.strip()]


def get_token_count(text: str) -> int:
    """
    Count number of tokens in a Kannada text.

    Args:
        text : Input Kannada text

    Returns:
        Integer token count

    Example:
        >>> get_token_count("ನಾನು ಕನ್ನಡ ಮಾತನಾಡುತ್ತೇನೆ")
        3
    """
    return len(tokenize(text))


def is_kannada(text: str) -> bool:
    """
    Check if a text contains Kannada characters.
    Kannada Unicode range: U+0C80 to U+0CFF

    Args:
        text : Input text string

    Returns:
        True if text contains Kannada characters

    Example:
        >>> is_kannada("ನಾನು")
        True
        >>> is_kannada("Hello")
        False
    """
    return any("\u0C80" <= ch <= "\u0CFF" for ch in text)


# ── Quick test ───────────────────────────────────────────────
if __name__ == "__main__":
    sample_texts = [
        "ನಾನು ಕನ್ನಡ ಮಾತನಾಡುತ್ತೇನೆ",
        "IPC ಸೆಕ್ಷನ್ 302 ಕೊಲೆಗೆ ಶಿಕ್ಷೆ ವಿಧಿಸುತ್ತದೆ",
        "ಪೊಲೀಸ್ ಬಂಧಿಸಿದಾಗ ನಿಮಗೆ ಹಕ್ಕುಗಳಿವೆ",
    ]

    print("── Tokenizer Test ──")
    for text in sample_texts:
        tokens = tokenize(text)
        count  = get_token_count(text)
        kn     = is_kannada(text)
        print(f"\nInput  : {text}")
        print(f"Tokens : {tokens}")
        print(f"Count  : {count}")
        print(f"Kannada: {kn}")