# backend/routes/query.py
# Main query endpoint.
# POST /api/query
#
# This is the heart of the backend.
# Takes a Kannada legal question and runs it through
# the full pipeline:
#
#   Request
#     -> Validate input
#     -> Dialect normalization
#     -> NLP preprocessing
#     -> Intent classification
#     -> Implicature resolution
#     -> RAG retrieval
#     -> Build response
#     -> Return to frontend

import time
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from loguru import logger

from backend.config import settings
from backend.models.request_models import QueryRequest, FeedbackRequest
from backend.models.response_models import (
    QueryResponse,
    ErrorResponse,
    build_query_response,
)

router = APIRouter()


# ── Helper: run full pipeline ─────────────────────────────────
def _run_pipeline(req: QueryRequest) -> QueryResponse:
    """
    Run the full Kannada Legal AI pipeline for a query.

    Args:
        req : Validated QueryRequest object

    Returns:
        QueryResponse with all pipeline results

    Raises:
        Exception if any pipeline step fails critically
    """
    start_time = time.time()
    logger.info(
        f"\n{'='*50}\n"
        f"New Query\n"
        f"  Question : {req.question[:80]}\n"
        f"  Session  : {req.session_id or 'none'}\n"
        f"  Language : {req.language}\n"
        f"  Dialect  : {req.dialect or 'auto'}\n"
        f"{'='*50}"
    )

    # ── Step 1: Dialect normalization ─────────────────────────
    question = req.question
    if req.dialect:
        logger.info(f"Step 1: Dialect normalization ({req.dialect})...")
        try:
            from pragmatics.dialect_adapter import normalize_text
            question = normalize_text(question, req.dialect)
            logger.info(f"        Normalized: '{question[:60]}'")
        except Exception as e:
            logger.warning(f"Dialect normalization failed: {e}")
    else:
        logger.info("Step 1: Auto dialect detection...")
        try:
            from pragmatics.dialect_adapter import (
                detect_dialect,
                normalize_dialect,
            )
            detected = detect_dialect(question)
            if detected != "standard":
                result   = normalize_dialect(question, detected)
                question = result.normalized_text
                logger.info(
                    f"        Auto detected: {detected}\n"
                    f"        Normalized  : '{question[:60]}'"
                )
        except Exception as e:
            logger.warning(f"Auto dialect detection failed: {e}")

    # ── Step 2: Intent classification ─────────────────────────
    logger.info("Step 2: Intent classification...")
    try:
        from pragmatics.intent_classifier import classify
        intent_result = classify(question)
        logger.info(
            f"        Intent     : {intent_result.intent}\n"
            f"        Confidence : {intent_result.confidence}\n"
            f"        Ambiguous  : {intent_result.is_ambiguous}"
        )
    except Exception as e:
        logger.error(f"Intent classification failed: {e}")
        from pragmatics.intent_classifier import IntentResult
        intent_result = IntentResult(
            intent="general",
            confidence=0.5,
            matched_patterns=[],
            all_scores={},
        )

    # ── Step 3: Implicature resolution ────────────────────────
    logger.info("Step 3: Implicature resolution...")
    try:
        from pragmatics.implicature_handler import resolve
        impl_result = resolve(question)
        if impl_result.detected:
            logger.info(
                f"        Offense  : {impl_result.likely_offense}\n"
                f"        Sections : {impl_result.likely_sections}\n"
                f"        Confidence: {impl_result.confidence}"
            )
        else:
            logger.info("        No implicature detected.")
    except Exception as e:
        logger.warning(f"Implicature resolution failed: {e}")
        from pragmatics.implicature_handler import ImplicatureResult
        impl_result = ImplicatureResult(
            detected=False,
            original_query=question,
            resolved_hint="",
            likely_sections=[],
            likely_offense="",
            confidence=0.0,
        )

    # ── Step 4: Context tracking ──────────────────────────────
    logger.info("Step 4: Context tracking...")
    try:
        from pragmatics.context_tracker import get_tracker
        tracker  = get_tracker(req.session_id or "default")
        question = tracker.resolve_reference(question)

        if tracker.is_follow_up(question):
            logger.info("        Follow-up query detected.")
    except Exception as e:
        logger.warning(f"Context tracking failed: {e}")

    # ── Step 5: RAG pipeline ──────────────────────────────────
    logger.info("Step 5: RAG pipeline...")
    try:
        from rag.rag_pipeline import answer as rag_answer
        rag_result = rag_answer(
            query=question,
            top_k=req.top_k,
            alpha=req.alpha,
        )
        logger.info(
            f"        Contexts   : {len(rag_result.get('contexts', []))}\n"
            f"        Sections   : {rag_result.get('section_numbers', [])}\n"
            f"        Laws       : {rag_result.get('law_names', [])}"
        )
    except Exception as e:
        logger.error(f"RAG pipeline failed: {e}")
        rag_result = {
            "query":            question,
            "processed_query":  question,
            "intent":           intent_result.intent,
            "section_numbers":  [],
            "law_names":        [],
            "contexts":         [],
            "context_text":     "",
            "prompt":           "",
            "dominant_language": req.language,
            "code_switch":      None,
        }

    # ── Step 6: Add implicature context if detected ───────────
    if impl_result.detected and impl_result.resolved_hint:
        logger.info("Step 6: Adding implicature context to RAG...")
        try:
            from rag.hybrid_retriever import retrieve
            impl_contexts = retrieve(
                query=impl_result.resolved_hint,
                top_k=2,
                alpha=0.5,
            )
            existing = {
                c["text"][:50]
                for c in rag_result.get("contexts", [])
            }
            for ctx in impl_contexts:
                if ctx["text"][:50] not in existing:
                    rag_result["contexts"].append(ctx)
                    existing.add(ctx["text"][:50])
            logger.info(
                f"        Added {len(impl_contexts)} "
                f"implicature contexts."
            )
        except Exception as e:
            logger.warning(f"Implicature context failed: {e}")

    # ── Step 7: Update conversation history ───────────────────
    logger.info("Step 7: Updating conversation history...")
    try:
        from pragmatics.context_tracker import get_tracker
        tracker = get_tracker(req.session_id or "default")
        tracker.add_user_turn(
            content=req.question,
            intent=intent_result.intent,
            sections=rag_result.get("section_numbers", []),
            laws=rag_result.get("law_names", []),
        )
    except Exception as e:
        logger.warning(f"Context update failed: {e}")

    # ── Step 8: Build response ────────────────────────────────
    logger.info("Step 8: Building response...")
    response = build_query_response(
        query=req.question,
        rag_result=rag_result,
        intent_result=intent_result,
        impl_result=impl_result,
        session_id=req.session_id,
        debug=settings.DEBUG,
    )

    # ── Log completion ────────────────────────────────────────
    elapsed = round(time.time() - start_time, 2)
    logger.success(
        f"Pipeline complete in {elapsed}s.\n"
        f"        Intent  : {response.intent}\n"
        f"        Sources : {len(response.sources)}\n"
        f"        Sections: {response.section_numbers}"
    )

    return response


# ── POST /api/query ───────────────────────────────────────────
@router.post(
    "/query",
    response_model=QueryResponse,
    summary="Ask a Kannada Legal Question",
    description=(
        "Submit a legal question in Kannada or English. "
        "The system runs the full NLP + RAG + Pragmatics pipeline "
        "and returns relevant legal information with citations."
    ),
    responses={
        200: {"description": "Successful query response"},
        400: {"description": "Invalid query"},
        500: {"description": "Internal server error"},
    },
)
async def query_endpoint(req: QueryRequest) -> QueryResponse:
    """
    Main query endpoint for Kannada legal questions.

    Runs the full pipeline:
    1. Dialect normalization
    2. Intent classification
    3. Implicature resolution
    4. Context tracking
    5. RAG retrieval (ChromaDB + BM25)
    6. Response building

    Example request:
        POST /api/query
        {
            "question": "IPC ಸೆಕ್ಷನ್ 302 ಏನು?",
            "session_id": "user_001",
            "language": "kn",
            "top_k": 5
        }
    """
    try:
        response = _run_pipeline(req)
        return response

    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=400,
            detail={
                "error":   "validation_error",
                "message": str(e),
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error in query endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error":   "pipeline_error",
                "message": (
                    "ಸರ್ವರ್ ದೋಷ ಸಂಭವಿಸಿದೆ. "
                    "ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ."
                ),
                "detail":  str(e),
            }
        )


# ── GET /api/query/examples ───────────────────────────────────
@router.get(
    "/query/examples",
    summary="Get Example Queries",
    description=(
        "Returns a list of example Kannada legal queries "
        "to help users understand what to ask."
    ),
)
async def get_examples():
    """
    Returns example Kannada legal queries.
    Shown in the frontend to help users get started.
    """
    return {
        "examples": [
            {
                "question":    "IPC ಸೆಕ್ಷನ್ 302 ಏನು?",
                "intent":      "section_lookup",
                "description": "Section 302 IPC information",
            },
            {
                "question":    "ಪೊಲೀಸ್ ಬಂಧಿಸಿದರೆ ನನ್ನ ಹಕ್ಕುಗಳೇನು?",
                "intent":      "rights_query",
                "description": "Rights when arrested",
            },
            {
                "question":    "ಕಳ್ಳತನಕ್ಕೆ ಎಷ್ಟು ಜೈಲು ಶಿಕ್ಷೆ?",
                "intent":      "penalty_query",
                "description": "Punishment for theft",
            },
            {
                "question":    "FIR ದಾಖಲಿಸುವುದು ಹೇಗೆ?",
                "intent":      "procedure_query",
                "description": "How to file FIR",
            },
            {
                "question":    "ಜಾಮೀನು ಅರ್ಜಿ ಸಲ್ಲಿಸುವ ಪ್ರಕ್ರಿಯೆ",
                "intent":      "procedure_query",
                "description": "Bail application process",
            },
            {
                "question":    "RTI ಅರ್ಜಿ ಹೇಗೆ ಹಾಕಬೇಕು?",
                "intent":      "procedure_query",
                "description": "How to file RTI",
            },
            {
                "question":    "ಉಚಿತ ವಕೀಲರ ಸಹಾಯ ಹೇಗೆ ಪಡೆಯಬಹುದು?",
                "intent":      "rights_query",
                "description": "How to get free legal aid",
            },
            {
                "question":    "ಕೌಟುಂಬಿಕ ಹಿಂಸೆ ಆದರೆ ಎಲ್ಲಿ ದೂರು ನೀಡಬೇಕು?",
                "intent":      "procedure_query",
                "description": "Domestic violence complaint",
            },
        ]
    }


# ── POST /api/feedback ────────────────────────────────────────
@router.post(
    "/feedback",
    summary="Submit Feedback",
    description=(
        "Submit feedback on the quality of an answer. "
        "Helps improve the system over time."
    ),
)
async def submit_feedback(req: FeedbackRequest):
    """
    Feedback endpoint.
    Records user ratings for answer quality.
    Stored for future model improvement.
    """
    logger.info(
        f"Feedback received.\n"
        f"        Session  : {req.session_id}\n"
        f"        Rating   : {req.rating}/5\n"
        f"        Helpful  : {req.was_helpful}\n"
        f"        Comment  : {req.comment or 'None'}"
    )

    # TODO: Save feedback to database or file
    # For now just log it
    feedback_log = {
        "session_id":  req.session_id,
        "question":    req.question,
        "rating":      req.rating,
        "was_helpful": req.was_helpful,
        "comment":     req.comment,
    }

    # Save to feedback file
    import json
    from pathlib import Path
    feedback_path = Path("data/feedback.jsonl")
    feedback_path.parent.mkdir(parents=True, exist_ok=True)
    with open(feedback_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(feedback_log, ensure_ascii=False) + "\n")

    return {
        "success": True,
        "message": "ಧನ್ಯವಾದಗಳು! ನಿಮ್ಮ ಪ್ರತಿಕ್ರಿಯೆ ದಾಖಲಾಗಿದೆ.",
        "message_en": "Thank you! Your feedback has been recorded.",
    }


# ── GET /api/query/stats ──────────────────────────────────────
@router.get(
    "/query/stats",
    summary="Query Statistics",
    description="Returns statistics about the knowledge base.",
)
async def get_stats():
    """
    Returns statistics about the Kannada Legal AI knowledge base.
    Useful for the demo to show what the system knows.
    """
    stats = {
        "knowledge_base": {
            "ipc_sections":        28,
            "karnataka_laws":      16,
            "vikaspedia_articles":  8,
            "sample_judgments":     3,
            "manual_qa_pairs":     15,
        },
        "supported_laws": [
            "IPC (Indian Penal Code)",
            "CrPC (Code of Criminal Procedure)",
            "Karnataka Land Revenue Act",
            "Karnataka Police Act",
            "Karnataka Shops and Establishments Act",
            "Karnataka Rent Control Act",
            "RTI Act 2005",
            "Consumer Protection Act 2019",
            "PWDVA 2005",
        ],
        "supported_dialects": [
            "Mysuru",
            "Dharwad",
            "Mangaluru",
            "Bengaluru",
        ],
        "languages": ["Kannada (ಕನ್ನಡ)", "English"],
        "intents": [
            "section_lookup",
            "rights_query",
            "penalty_query",
            "procedure_query",
            "document_help",
            "general",
        ],
    }

    try:
        from rag.vector_store import get_collection_stats
        vs_stats = get_collection_stats()
        stats["vector_store"] = {
            "total_documents": vs_stats.get("total_documents", 0),
            "collection":      vs_stats.get("collection_name", ""),
        }
    except Exception as e:
        logger.warning(f"Could not get vector store stats: {e}")
        stats["vector_store"] = {"total_documents": 0}

    return stats