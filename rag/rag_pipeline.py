# rag/rag_pipeline.py
# Full RAG pipeline — ties everything together.
# Takes a raw user query and returns retrieved context + prompt.
#
# Flow:
#   Raw query
#     -> NLP preprocessing  (transliterate, normalize, tokenize)
#     -> Intent detection   (section lookup? rights? penalty?)
#     -> Section extraction (is there a section number in query?)
#     -> Hybrid retrieval   (ChromaDB + BM25)
#     -> Prompt building    (context + question -> LLM prompt)
#     -> Return result dict

from loguru import logger

from nlp.preprocessing_pipeline import run as preprocess
from nlp.legal_normalizer        import extract_section_numbers, extract_law_names
from rag.hybrid_retriever        import retrieve, retrieve_for_section


# ── Disclaimer ───────────────────────────────────────────────
DISCLAIMER_KN = (
    "\n\n⚠️ ಇದು ಕಾನೂನು ಸಲಹೆ ಅಲ್ಲ. "
    "ನಿಮ್ಮ ನಿರ್ದಿಷ್ಟ ಪ್ರಕರಣಕ್ಕೆ ಅರ್ಹ ವಕೀಲರನ್ನು ಸಂಪರ್ಕಿಸಿ."
)


# ── Prompt templates ─────────────────────────────────────────
PROMPT_TEMPLATES = {

    "section_lookup": (
        "ನೀವು ಒಬ್ಬ ಕನ್ನಡ ಕಾನೂನು ತಜ್ಞ.\n"
        "ಕೆಳಗಿನ ಕಾನೂನು ಮಾಹಿತಿ ಬಳಸಿ ಕೇಳಿದ ವಿಭಾಗದ "
        "ಸಂಪೂರ್ಣ ವ್ಯಾಖ್ಯಾನ ಮತ್ತು ಅನ್ವಯ ನೀಡಿ.\n"
        "ಯಾವಾಗಲೂ ವಿಭಾಗ ಸಂಖ್ಯೆ ಮತ್ತು ಕಾನೂನಿನ ಹೆಸರು "
        "ಉಲ್ಲೇಖಿಸಿ.\n\n"
        "[ಕಾನೂನು ಮಾಹಿತಿ]\n{context}\n\n"
        "[ಪ್ರಶ್ನೆ]\n{question}\n\n"
        "[ಉತ್ತರ]"
    ),

    "rights_query": (
        "ನೀವು ಒಬ್ಬ ಕನ್ನಡ ಕಾನೂನು ಸಹಾಯಕ.\n"
        "ವ್ಯಕ್ತಿಯ ಕಾನೂನು ಹಕ್ಕುಗಳನ್ನು ಸರಳ ಕನ್ನಡದಲ್ಲಿ "
        "ವಿವರಿಸಿ. ಸಂಬಂಧಿತ ವಿಭಾಗಗಳನ್ನು ಉಲ್ಲೇಖಿಸಿ.\n\n"
        "[ಕಾನೂನು ಮಾಹಿತಿ]\n{context}\n\n"
        "[ಪ್ರಶ್ನೆ]\n{question}\n\n"
        "[ಉತ್ತರ]"
    ),

    "penalty_query": (
        "ನೀವು ಒಬ್ಬ ಕನ್ನಡ ಕಾನೂನು ತಜ್ಞ.\n"
        "ಶಿಕ್ಷೆ, ದಂಡ ಮತ್ತು ಸಂಬಂಧಿತ ವಿಭಾಗಗಳನ್ನು "
        "ನಿಖರವಾಗಿ ನಮೂದಿಸಿ.\n\n"
        "[ಕಾನೂನು ಮಾಹಿತಿ]\n{context}\n\n"
        "[ಪ್ರಶ್ನೆ]\n{question}\n\n"
        "[ಉತ್ತರ]"
    ),

    "procedure_query": (
        "ನೀವು ಒಬ್ಬ ಕನ್ನಡ ಕಾನೂನು ಮಾರ್ಗದರ್ಶಕ.\n"
        "ಹಂತ-ಹಂತವಾಗಿ ಕಾನೂನು ಪ್ರಕ್ರಿಯೆ ವಿವರಿಸಿ.\n\n"
        "[ಕಾನೂನು ಮಾಹಿತಿ]\n{context}\n\n"
        "[ಪ್ರಶ್ನೆ]\n{question}\n\n"
        "[ಉತ್ತರ]"
    ),

    "document_help": (
        "ನೀವು ಒಬ್ಬ ಕನ್ನಡ ಕಾನೂನು ಲೇಖಕ.\n"
        "ಔಪಚಾರಿಕ ಕನ್ನಡ ಭಾಷೆಯಲ್ಲಿ ದಾಖಲೆ "
        "ಸಿದ್ಧಪಡಿಸಲು ಸಹಾಯ ಮಾಡಿ.\n\n"
        "[ಕಾನೂನು ಮಾಹಿತಿ]\n{context}\n\n"
        "[ಪ್ರಶ್ನೆ]\n{question}\n\n"
        "[ಉತ್ತರ]"
    ),

    "general": (
        "ನೀವು ಒಬ್ಬ ಸಹಾಯಕ ಕನ್ನಡ ಕಾನೂನು ಸಲಹೆಗಾರ.\n"
        "ಸರಳ ಮತ್ತು ಸ್ಪಷ್ಟ ಕನ್ನಡದಲ್ಲಿ ಉತ್ತರಿಸಿ.\n\n"
        "[ಕಾನೂನು ಮಾಹಿತಿ]\n{context}\n\n"
        "[ಪ್ರಶ್ನೆ]\n{question}\n\n"
        "[ಉತ್ತರ]"
    ),
}


# ── Intent detector ──────────────────────────────────────────
def _detect_intent(query: str, nlp_result: dict) -> str:
    """
    Detect the intent of a legal query.
    Uses keyword patterns on normalized text.

    Args:
        query      : Original query
        nlp_result : Result from NLP preprocessing pipeline

    Returns:
        Intent string — one of:
        'section_lookup' | 'rights_query' | 'penalty_query' |
        'procedure_query' | 'document_help' | 'general'
    """
    import re
    text = (query + " " + nlp_result.get("processed_text", "")).lower()

    # Section lookup patterns
    if re.search(
        r"section\s*\d+|ವಿಭಾಗ\s*\d+|ಸೆಕ್ಷನ್\s*\d+|"
        r"\bipc\b|\bcrpc\b|\bcpc\b",
        text, re.IGNORECASE
    ):
        return "section_lookup"

    # Rights query patterns
    if re.search(
        r"ಹಕ್ಕು|ಹಕ್ಕುಗಳು|rights?|ಅಧಿಕಾರ|"
        r"entitled|ರಕ್ಷಣೆ",
        text, re.IGNORECASE
    ):
        return "rights_query"

    # Penalty query patterns
    if re.search(
        r"ಶಿಕ್ಷೆ|ದಂಡ|punishment|penalty|"
        r"ಜೈಲು|imprisonment|ಜೀವಾವಧಿ|"
        r"ಮರಣದಂಡನೆ|death",
        text, re.IGNORECASE
    ):
        return "penalty_query"

    # Procedure query patterns
    if re.search(
        r"ಹೇಗೆ|ಏನು ಮಾಡ|how|process|procedure|"
        r"FIR|ದೂರು|complaint|ಅರ್ಜಿ|apply|"
        r"ಜಾಮೀನು|bail|ಸಲ್ಲಿಸು",
        text, re.IGNORECASE
    ):
        return "procedure_query"

    # Document help patterns
    if re.search(
        r"draft|ಬರೆ|write|petition|"
        r"affidavit|notice|agreement|"
        r"ದಾಖಲೆ|document",
        text, re.IGNORECASE
    ):
        return "document_help"

    return "general"


# ── Context builder ──────────────────────────────────────────
def _build_context(results: list, max_chars: int = 2000) -> str:
    """
    Build context string from retrieval results.
    Joins top results with source citations.

    Args:
        results   : List of retrieval result dicts
        max_chars : Max total characters for context

    Returns:
        Formatted context string
    """
    if not results:
        return "ಯಾವುದೇ ಸಂಬಂಧಿತ ಕಾನೂನು ಮಾಹಿತಿ ದೊರೆಯಲಿಲ್ಲ."

    context_parts = []
    total_chars   = 0

    for i, result in enumerate(results, 1):
        meta    = result.get("metadata", {})
        text    = result.get("text", "")
        law     = meta.get("law_name", "Unknown")
        section = meta.get("section_number", "")
        lang    = meta.get("language", "")

        # Build citation header
        if section and section != "unknown":
            citation = f"[{i}] {law} ವಿಭಾಗ {section}"
        else:
            citation = f"[{i}] {law}"

        # Add language tag for clarity
        if lang == "kn":
            citation += " (ಕನ್ನಡ)"
        elif lang == "en":
            citation += " (English)"

        part = f"{citation}:\n{text}"

        # Check total length
        if total_chars + len(part) > max_chars:
            # Truncate this part to fit
            remaining = max_chars - total_chars
            if remaining > 100:
                part = part[:remaining] + "..."
                context_parts.append(part)
            break

        context_parts.append(part)
        total_chars += len(part)

    return "\n\n".join(context_parts)


# ── Prompt builder ───────────────────────────────────────────
def _build_prompt(
    question: str,
    context:  str,
    intent:   str,
) -> str:
    """
    Build the final LLM prompt from question, context and intent.

    Args:
        question : Processed user question
        context  : Retrieved legal context
        intent   : Detected query intent

    Returns:
        Complete prompt string ready for LLM
    """
    template = PROMPT_TEMPLATES.get(intent, PROMPT_TEMPLATES["general"])
    return template.format(
        context=context,
        question=question,
    )


# ── Main answer function ─────────────────────────────────────
def answer(
    query:       str,
    top_k:       int   = 5,
    alpha:       float = 0.6,
    lang_filter: str   = None,
) -> dict:
    """
    Full RAG pipeline — from raw query to answer-ready result.

    Args:
        query       : Raw user input (Kannada or English)
        top_k       : Number of context chunks to retrieve
        alpha       : Hybrid search weight (0-1)
        lang_filter : Filter results by language ('kn'/'en')

    Returns:
        Dictionary with all pipeline results:
        {
            query            : original query
            processed_query  : NLP-processed query
            intent           : detected intent
            section_numbers  : sections found in query
            law_names        : laws found in query
            contexts         : list of retrieved chunks
            context_text     : formatted context string
            prompt           : complete LLM prompt
            dominant_language: detected language
            code_switch      : code-switch analysis
            disclaimer       : legal disclaimer in Kannada
        }

    Example:
        >>> result = answer("IPC ಸೆಕ್ಷನ್ 302 ಶಿಕ್ಷೆ ಏನು?")
        >>> result['intent']
        'section_lookup'
        >>> result['contexts'][0]['metadata']['section_number']
        '302'
    """
    if not query or not query.strip():
        logger.warning("answer: empty query received.")
        return {"error": "Empty query", "query": query}

    logger.info(
        f"\n{'='*50}\n"
        f"RAG Pipeline Start\n"
        f"Query: {query[:80]}\n"
        f"{'='*50}"
    )

    # ── Step 1: NLP Preprocessing ────────────────────────────
    logger.info("Step 1: NLP Preprocessing...")
    nlp_result      = preprocess(query)
    processed_query = nlp_result["processed_text"]
    section_numbers = nlp_result["section_numbers"]
    law_names       = nlp_result["law_names"]
    dominant_lang   = nlp_result["dominant_language"]
    code_switch     = nlp_result["code_switch"]

    logger.info(
        f"        Processed : '{processed_query[:60]}'\n"
        f"        Sections  : {section_numbers}\n"
        f"        Laws      : {law_names}\n"
        f"        Language  : {dominant_lang}"
    )

    # ── Step 2: Intent Detection ─────────────────────────────
    logger.info("Step 2: Detecting intent...")
    intent = _detect_intent(query, nlp_result)
    logger.info(f"        Intent: {intent}")

    # ── Step 3: Retrieval ────────────────────────────────────
    logger.info("Step 3: Retrieving context...")
    contexts = []

    # If specific section numbers found — use section retrieval
    if section_numbers:
        law = law_names[0] if law_names else "IPC"
        for sec in section_numbers[:2]:    # Max 2 sections
            sec_results = retrieve_for_section(
                section_number=sec,
                law_name=law,
                top_k=2,
            )
            contexts.extend(sec_results)
        logger.info(
            f"        Section retrieval: {len(contexts)} results "
            f"for §{section_numbers}"
        )

    # Always run hybrid retrieval too
    hybrid_results = retrieve(
        query=processed_query,
        top_k=top_k,
        alpha=alpha,
        filter_lang=lang_filter,
    )

    # Merge section and hybrid results (deduplicate)
    existing_texts = {c["text"][:50] for c in contexts}
    for r in hybrid_results:
        if r["text"][:50] not in existing_texts:
            contexts.append(r)
            existing_texts.add(r["text"][:50])

    logger.info(f"        Total contexts: {len(contexts)}")

    # ── Step 4: Build context string ─────────────────────────
    logger.info("Step 4: Building context...")
    context_text = _build_context(contexts[:top_k])

    # ── Step 5: Build prompt ─────────────────────────────────
    logger.info("Step 5: Building prompt...")
    prompt = _build_prompt(
        question=processed_query,
        context=context_text,
        intent=intent,
    )

    logger.success(
        f"RAG Pipeline Complete.\n"
        f"        Intent    : {intent}\n"
        f"        Contexts  : {len(contexts)}\n"
        f"        Prompt len: {len(prompt)} chars"
    )

    return {
        # ── Query info ───────────────────────────────────────
        "query":             query,
        "processed_query":   processed_query,

        # ── Intent & metadata ────────────────────────────────
        "intent":            intent,
        "section_numbers":   section_numbers,
        "law_names":         law_names,

        # ── Retrieval results ────────────────────────────────
        "contexts":          contexts[:top_k],
        "context_text":      context_text,

        # ── LLM prompt ───────────────────────────────────────
        "prompt":            prompt,

        # ── Language info ────────────────────────────────────
        "dominant_language": dominant_lang,
        "code_switch":       code_switch,

        # ── Disclaimer ───────────────────────────────────────
        "disclaimer":        DISCLAIMER_KN,
    }


def answer_batch(queries: list, **kwargs) -> list:
    """
    Run the RAG pipeline on multiple queries.

    Args:
        queries : List of query strings
        **kwargs: Passed to answer()

    Returns:
        List of result dicts
    """
    logger.info(f"Batch answer: {len(queries)} queries")
    return [answer(q, **kwargs) for q in queries]


# ── Quick test ───────────────────────────────────────────────
if __name__ == "__main__":

    print("══════════════════════════════════════════")
    print("   RAG Pipeline — Full Test")
    print("══════════════════════════════════════════\n")

    test_queries = [
        "IPC ಸೆಕ್ಷನ್ 302 ಶಿಕ್ಷೆ ಏನು?",
        "ಪೊಲೀಸ್ ಬಂಧಿಸಿದಾಗ ನನ್ನ ಹಕ್ಕುಗಳೇನು?",
        "FIR ದಾಖಲಿಸುವುದು ಹೇಗೆ?",
        "ಕಳ್ಳತನಕ್ಕೆ ಎಷ್ಟು ಜೈಲು ಶಿಕ್ಷೆ?",
        "ಜಾಮೀನು ಅರ್ಜಿ ಸಲ್ಲಿಸುವ ಪ್ರಕ್ರಿಯೆ",
    ]

    for query in test_queries:
        print(f"Query  : {query}")
        result = answer(query, top_k=3)
        print(f"Intent : {result['intent']}")
        print(f"Sections: {result['section_numbers']}")
        print(f"Laws   : {result['law_names']}")
        print(f"Contexts: {len(result['contexts'])}")
        if result["contexts"]:
            top = result["contexts"][0]
            meta = top.get("metadata", {})
            print(
                f"Top ctx: §{meta.get('section_number','?')} "
                f"({meta.get('law_name','?')}) "
                f"score={top.get('hybrid_score', top.get('score','?'))}"
            )
        print(f"\nPrompt preview:\n{result['prompt'][:300]}...")
        print(f"\n{result['disclaimer']}")
        print("\n" + "=" * 55 + "\n")