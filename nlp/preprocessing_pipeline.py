# nlp/preprocessing_pipeline.py
# Full Kannada preprocessing pipeline.
# Ties together all NLP modules into one single function.
#
# Flow:
#   Raw user query
#       -> Step 1: Detect script
#       -> Step 2: Transliterate if Roman
#       -> Step 3: Detect code-switching
#       -> Step 4: Normalize legal terms
#       -> Step 5: Tokenize
#       -> Step 6: Extract metadata
#       -> Return processed result dict

from loguru import logger

from nlp.transliterator      import preprocess_query, detect_mixed_script
from nlp.code_switch_detector import detect as detect_code_switch
from nlp.code_switch_detector import needs_transliteration
from nlp.legal_normalizer     import (
    normalize,
    normalize_tokens,
    extract_section_numbers,
    extract_law_names,
)
from nlp.tokenizer_kannada    import (
    tokenize,
    tokenize_sentences,
    get_token_count,
    is_kannada,
)


# ── Pipeline result structure ────────────────────────────────
def _make_result(
    original_text:      str,
    processed_text:     str,
    tokens:             list,
    sentences:          list,
    token_count:        int,
    code_switch:        object,
    script_info:        dict,
    section_numbers:    list,
    law_names:          list,
    was_transliterated: bool,
    was_normalized:     bool,
) -> dict:
    """
    Build the standard pipeline result dictionary.

    Returns:
        dict with all processing metadata and results
    """
    return {
        # ── Text ────────────────────────────────────────────
        "original_text":      original_text,
        "processed_text":     processed_text,

        # ── Tokens ──────────────────────────────────────────
        "tokens":             tokens,
        "token_count":        token_count,
        "sentences":          sentences,

        # ── Script analysis ──────────────────────────────────
        "script_info":        script_info,
        "code_switch":        code_switch,
        "dominant_language":  code_switch.dominant_language,

        # ── Legal metadata ───────────────────────────────────
        "section_numbers":    section_numbers,
        "law_names":          law_names,

        # ── Processing flags ─────────────────────────────────
        "was_transliterated": was_transliterated,
        "was_normalized":     was_normalized,
        "is_kannada":         is_kannada(processed_text),
    }


# ── Main pipeline function ───────────────────────────────────
def run(text: str) -> dict:
    """
    Run the full Kannada legal preprocessing pipeline.

    Args:
        text : Raw user input (any script)

    Returns:
        Dictionary with processed text and all metadata

    Example:
        >>> result = run("Section 302 ಶಿಕ್ಷೆ ಏನು?")
        >>> result['processed_text']
        'ವಿಭಾಗ 302 ದಂಡ ಏನು?'
        >>> result['section_numbers']
        ['302']
        >>> result['law_names']
        ['IPC']
    """
    if not text or not text.strip():
        logger.warning("Empty input received by pipeline.")
        return _make_result(
            original_text="",
            processed_text="",
            tokens=[],
            sentences=[],
            token_count=0,
            code_switch=detect_code_switch(""),
            script_info={},
            section_numbers=[],
            law_names=[],
            was_transliterated=False,
            was_normalized=False,
        )

    logger.info(f"Pipeline input: '{text[:80]}...' " if len(text) > 80 else f"Pipeline input: '{text}'")

    original_text = text

    # ── Step 1: Detect script ────────────────────────────────
    script_info         = detect_mixed_script(text)
    was_transliterated  = False

    # ── Step 2: Transliterate if Roman ──────────────────────
    if needs_transliteration(text):
        logger.info("Step 2: Transliterating Roman -> Kannada")
        text               = preprocess_query(text)
        was_transliterated = True
    else:
        logger.info("Step 2: No transliteration needed.")

    # ── Step 3: Detect code-switching ───────────────────────
    logger.info("Step 3: Detecting code-switching...")
    code_switch = detect_code_switch(text)
    logger.info(
        f"        Dominant: {code_switch.dominant_language} | "
        f"Mixed: {code_switch.is_mixed}"
    )

    # ── Step 4: Normalize legal terms ───────────────────────
    logger.info("Step 4: Normalizing legal terminology...")
    normalized_text = normalize(text)
    was_normalized  = normalized_text != text
    if was_normalized:
        logger.info(f"        Normalized: '{text}' -> '{normalized_text}'")
    text = normalized_text

    # ── Step 5: Tokenize ────────────────────────────────────
    logger.info("Step 5: Tokenizing...")
    tokens      = tokenize(text)
    norm_tokens = normalize_tokens(tokens)
    sentences   = tokenize_sentences(text)
    token_count = get_token_count(text)
    logger.info(f"        Tokens: {token_count} | Sentences: {len(sentences)}")

    # ── Step 6: Extract legal metadata ──────────────────────
    logger.info("Step 6: Extracting legal metadata...")
    section_numbers = extract_section_numbers(original_text)
    law_names       = extract_law_names(original_text)
    logger.info(
        f"        Sections: {section_numbers} | "
        f"Laws: {law_names}"
    )

    result = _make_result(
        original_text=original_text,
        processed_text=text,
        tokens=norm_tokens,
        sentences=sentences,
        token_count=token_count,
        code_switch=code_switch,
        script_info=script_info,
        section_numbers=section_numbers,
        law_names=law_names,
        was_transliterated=was_transliterated,
        was_normalized=was_normalized,
    )

    logger.info("Pipeline complete.")
    return result


def run_batch(texts: list) -> list:
    """
    Run the pipeline on a list of texts.

    Args:
        texts : List of raw input strings

    Returns:
        List of result dictionaries

    Example:
        >>> results = run_batch([
        ...     "IPC ಸೆಕ್ಷನ್ 302 ಏನು?",
        ...     "ಜಾಮೀನು ಹೇಗೆ ಪಡೆಯುವುದು?"
        ... ])
    """
    logger.info(f"Batch pipeline: {len(texts)} inputs")
    results = []
    for i, text in enumerate(texts):
        logger.info(f"Processing [{i+1}/{len(texts)}]")
        results.append(run(text))
    return results


def get_pipeline_summary(result: dict) -> str:
    """
    Returns a human-readable summary of pipeline result.

    Args:
        result : Pipeline result dictionary

    Returns:
        Formatted summary string
    """
    lines = [
        "── Pipeline Result ──",
        f"Original       : {result['original_text']}",
        f"Processed      : {result['processed_text']}",
        f"Dominant Lang  : {result['dominant_language']}",
        f"Is Mixed       : {result['code_switch'].is_mixed}",
        f"Tokens         : {result['token_count']}",
        f"Sentences      : {len(result['sentences'])}",
        f"Sections Found : {result['section_numbers']}",
        f"Laws Found     : {result['law_names']}",
        f"Transliterated : {result['was_transliterated']}",
        f"Normalized     : {result['was_normalized']}",
    ]
    return "\n".join(lines)


# ── Quick test ───────────────────────────────────────────────
if __name__ == "__main__":

    test_queries = [
        # Mixed script — section lookup
        "IPC Section 302 ಶಿಕ್ಷೆ ಏನು?",

        # Pure Kannada — rights query
        "ಪೊಲೀಸ್ ಬಂಧಿಸಿದಾಗ ನನ್ನ ಹಕ್ಕುಗಳೇನು?",

        # Colloquial Kannada
        "ಸೆಕ್ಷನ್ 420 ಕೋರ್ಟ್‌ನಲ್ಲಿ ಏನ್ರಿ ಮಾಡ್ಬೇಕು?",

        # Roman Kannada
        "FIR hege daakhalisabeku",

        # Mixed with legal terms
        "FIR ದಾಖಲಿಸಿ ಜಾಮೀನು ಅರ್ಜಿ ಕೋರ್ಟ್‌ನಲ್ಲಿ ಹಾಕಬಹುದೇ?",

        # Karnataka specific law
        "Karnataka Land Revenue Act ಅಡಿಯಲ್ಲಿ ಜಮೀನು ಆಕ್ರಮಣ ಶಿಕ್ಷೆ?",
    ]

    print("══════════════════════════════════════════\n")
    print("   Kannada Legal NLP — Pipeline Test\n")
    print("══════════════════════════════════════════\n")

    for query in test_queries:
        result = run(query)
        print(get_pipeline_summary(result))
        print()