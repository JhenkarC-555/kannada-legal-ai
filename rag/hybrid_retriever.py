# rag/hybrid_retriever.py
# Hybrid retriever combining ChromaDB (dense) + BM25 (sparse).
#
# Why hybrid?
#   ChromaDB alone : great for meaning-based queries
#                    "ಕೊಲೆಗೆ ಶಿಕ್ಷೆ" finds murder sections
#   BM25 alone     : great for exact keyword matches
#                    "Section 302" finds exactly section 302
#   Hybrid         : best of both worlds
#
# Scoring formula:
#   hybrid_score = (alpha * dense_score) + (1 - alpha) * bm25_score
#   Default alpha = 0.6 (60% semantic, 40% keyword)

from loguru import logger

from rag.vector_store    import search as dense_search
from rag.vector_store    import search_by_section as dense_section_search
from rag.bm25_retriever  import get_retriever


# ── Config ──────────────────────────────────────────────────
DEFAULT_ALPHA = 0.6    # Weight for dense search score
DEFAULT_TOP_K = 5      # Number of results to return


# ── Score normalizer ─────────────────────────────────────────
def _normalize_bm25_scores(results: list) -> list:
    """
    Normalize BM25 scores to [0, 1] range.
    BM25 scores are unbounded — we normalize for fair combination.

    Args:
        results : List of BM25 result dicts

    Returns:
        Same list with normalized scores
    """
    if not results:
        return results

    max_score = max(r["score"] for r in results)
    if max_score == 0:
        return results

    for r in results:
        r["bm25_score_raw"]  = r["score"]
        r["score"]           = round(r["score"] / max_score, 4)

    return results


# ── Merge results ────────────────────────────────────────────
def _merge_results(
    dense_results: list,
    bm25_results:  list,
    alpha:         float,
    top_k:         int,
) -> list:
    """
    Merge dense and BM25 results using weighted scoring.

    Args:
        dense_results : Results from ChromaDB (scores 0-1)
        bm25_results  : Results from BM25 (normalized 0-1)
        alpha         : Weight for dense score (0-1)
        top_k         : Number of final results

    Returns:
        Merged and re-ranked list of result dicts
    """
    # Use text as the merge key
    merged = {}

    # Add dense results
    for r in dense_results:
        key = r["text"][:100]    # Use first 100 chars as key
        merged[key] = {
            "text":        r["text"],
            "metadata":    r.get("metadata", {}),
            "dense_score": r["score"],
            "bm25_score":  0.0,
        }

    # Add or update with BM25 results
    bm25_normalized = _normalize_bm25_scores(bm25_results)
    for r in bm25_normalized:
        key = r["text"][:100]
        if key in merged:
            merged[key]["bm25_score"] = r["score"]
        else:
            merged[key] = {
                "text":        r["text"],
                "metadata":    r.get("metadata", {}),
                "dense_score": 0.0,
                "bm25_score":  r["score"],
            }

    # Compute hybrid score for each result
    for item in merged.values():
        item["hybrid_score"] = round(
            (alpha       * item["dense_score"]) +
            ((1 - alpha) * item["bm25_score"]),
            4
        )

    # Sort by hybrid score descending
    ranked = sorted(
        merged.values(),
        key=lambda x: x["hybrid_score"],
        reverse=True,
    )

    return ranked[:top_k]


# ── Main retrieve function ───────────────────────────────────
def retrieve(
    query:       str,
    top_k:       int   = DEFAULT_TOP_K,
    alpha:       float = DEFAULT_ALPHA,
    filter_lang: str   = None,
    filter_law:  str   = None,
) -> list:
    """
    Retrieve most relevant legal chunks using hybrid search.

    Args:
        query       : User query string (Kannada or English)
        top_k       : Number of results to return
        alpha       : Dense search weight (0.0 to 1.0)
                      0.0 = pure BM25
                      1.0 = pure dense
                      0.6 = default (60% dense, 40% BM25)
        filter_lang : Filter by language ('kn' or 'en')
        filter_law  : Filter by law name ('IPC', 'CrPC' etc.)

    Returns:
        List of merged result dicts sorted by hybrid_score

    Example:
        >>> results = retrieve("ಕೊಲೆಗೆ ಶಿಕ್ಷೆ ಏನು?", top_k=3)
        >>> results[0]['metadata']['section_number']
        '302'
        >>> results[0]['hybrid_score']
        0.89
    """
    if not query or not query.strip():
        logger.warning("retrieve: empty query.")
        return []

    logger.info(
        f"Hybrid retrieve: '{query[:60]}' "
        f"top_k={top_k} alpha={alpha}"
    )

    # ── Dense search (ChromaDB) ──────────────────────────────
    logger.info("Running dense search (ChromaDB)...")
    try:
        dense_results = dense_search(
            query=query,
            top_k=top_k,
            filter_lang=filter_lang,
            filter_law=filter_law,
        )
        logger.info(f"Dense results: {len(dense_results)}")
    except Exception as e:
        logger.error(f"Dense search failed: {e}")
        dense_results = []

    # ── BM25 search ──────────────────────────────────────────
    logger.info("Running BM25 search...")
    try:
        retriever    = get_retriever()
        bm25_results = retriever.search(query, top_k=top_k)
        logger.info(f"BM25 results: {len(bm25_results)}")
    except Exception as e:
        logger.error(f"BM25 search failed: {e}")
        bm25_results = []

    # ── Merge ────────────────────────────────────────────────
    if not dense_results and not bm25_results:
        logger.warning("Both searches returned no results.")
        return []

    merged = _merge_results(
        dense_results=dense_results,
        bm25_results=bm25_results,
        alpha=alpha,
        top_k=top_k,
    )

    logger.success(
        f"Hybrid retrieve complete.\n"
        f"        Dense     : {len(dense_results)} results\n"
        f"        BM25      : {len(bm25_results)} results\n"
        f"        Merged    : {len(merged)} results\n"
        f"        Top score : {merged[0]['hybrid_score'] if merged else 'N/A'}"
    )

    return merged


def retrieve_for_section(
    section_number: str,
    law_name:       str   = "IPC",
    top_k:          int   = 3,
    alpha:          float = 0.4,    # More weight on BM25 for exact lookup
) -> list:
    """
    Specialized retrieval for exact section number queries.
    Uses lower alpha (more BM25 weight) for exact section lookup.

    Args:
        section_number : e.g. '302'
        law_name       : e.g. 'IPC'
        top_k          : Number of results
        alpha          : Dense weight (lower = more BM25)

    Returns:
        List of result dicts for that section

    Example:
        >>> results = retrieve_for_section("302", "IPC")
        >>> results[0]['metadata']['section_number']
        '302'
    """
    logger.info(
        f"Section retrieve: §{section_number} ({law_name})"
    )

    # Dense section search
    try:
        dense_results = dense_section_search(
            section_number=section_number,
            law_name=law_name,
        )
    except Exception as e:
        logger.error(f"Dense section search failed: {e}")
        dense_results = []

    # BM25 section search
    try:
        retriever    = get_retriever()
        bm25_results = retriever.search_by_section(
            section_number=section_number,
            law_name=law_name,
            top_k=top_k,
        )
    except Exception as e:
        logger.error(f"BM25 section search failed: {e}")
        bm25_results = []

    merged = _merge_results(
        dense_results=dense_results,
        bm25_results=bm25_results,
        alpha=alpha,
        top_k=top_k,
    )

    logger.info(
        f"Section retrieve §{section_number}: "
        f"{len(merged)} results."
    )
    return merged


def retrieve_kannada_only(
    query:  str,
    top_k:  int   = DEFAULT_TOP_K,
    alpha:  float = DEFAULT_ALPHA,
) -> list:
    """
    Retrieve only Kannada language chunks.
    Useful when user query is in Kannada and
    we want Kannada answers.

    Args:
        query : Kannada query string
        top_k : Number of results
        alpha : Dense weight

    Returns:
        List of Kannada-only result dicts
    """
    return retrieve(
        query=query,
        top_k=top_k,
        alpha=alpha,
        filter_lang="kn",
    )


def get_retrieval_summary(results: list) -> str:
    """
    Returns a human-readable summary of retrieval results.

    Args:
        results : List of hybrid result dicts

    Returns:
        Formatted summary string
    """
    if not results:
        return "No results found."

    lines = [f"── Top {len(results)} Results ──\n"]
    for i, r in enumerate(results, 1):
        meta = r.get("metadata", {})
        lines.append(
            f"[{i}] §{meta.get('section_number','?')} "
            f"({meta.get('law_name','?')}) "
            f"lang={meta.get('language','?')}\n"
            f"    Hybrid: {r.get('hybrid_score', 0):.3f} | "
            f"Dense: {r.get('dense_score', 0):.3f} | "
            f"BM25: {r.get('bm25_score', 0):.3f}\n"
            f"    Text: {r['text'][:80]}...\n"
        )
    return "\n".join(lines)


# ── Quick test ───────────────────────────────────────────────
if __name__ == "__main__":

    print("══════════════════════════════════════")
    print("   Hybrid Retriever Test")
    print("══════════════════════════════════════\n")

    test_cases = [
        {
            "query": "ಕೊಲೆಗೆ ಶಿಕ್ಷೆ ಏನು?",
            "label": "Pure Kannada — murder punishment",
            "top_k": 3,
        },
        {
            "query": "Section 302 IPC punishment",
            "label": "English — exact section lookup",
            "top_k": 3,
        },
        {
            "query": "IPC ಸೆಕ್ಷನ್ 420 ಮೋಸ",
            "label": "Mixed — cheating section",
            "top_k": 3,
        },
        {
            "query": "FIR ದಾಖಲಿಸುವುದು ಹೇಗೆ?",
            "label": "Procedure — FIR filing",
            "top_k": 3,
        },
        {
            "query": "ಜಾಮೀನು ಅರ್ಜಿ ನ್ಯಾಯಾಲಯ",
            "label": "Bail application court",
            "top_k": 3,
        },
    ]

    for case in test_cases:
        print(f"Query : {case['query']}")
        print(f"Label : {case['label']}")
        results = retrieve(case["query"], top_k=case["top_k"])
        print(get_retrieval_summary(results))
        print("-" * 55)

    # Test section-specific retrieval
    print("\n── Section Retrieval Test ──\n")
    for section in ["302", "420", "379", "354"]:
        results = retrieve_for_section(section, "IPC")
        print(
            f"§{section}: {len(results)} results | "
            f"Top score: {results[0]['hybrid_score'] if results else 'N/A'}"
        )

    # Test alpha sensitivity
    print("\n── Alpha Sensitivity Test ──\n")
    query = "Section 302 ಕೊಲೆ ಶಿಕ್ಷೆ"
    for alpha in [0.0, 0.3, 0.6, 1.0]:
        results = retrieve(query, top_k=1, alpha=alpha)
        top = results[0] if results else {}
        print(
            f"alpha={alpha} | "
            f"§{top.get('metadata',{}).get('section_number','?')} | "
            f"hybrid={top.get('hybrid_score','N/A')}"
        )