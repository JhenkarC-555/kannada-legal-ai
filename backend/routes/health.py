# backend/routes/health.py
# Health check endpoint.
# GET /api/health
#
# Used to check if the backend is running correctly.
# Checks all components:
#   - NLP pipeline
#   - Embedding model
#   - Vector store
#   - BM25 index
#
# Great for demo — shows everything is live.

from fastapi import APIRouter
from loguru import logger

from backend.config        import settings
from backend.models.response_models import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description=(
        "Check if all components of the Kannada Legal AI "
        "are running correctly. Returns status of NLP pipeline, "
        "embedding model and vector store."
    ),
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    Checks all pipeline components and returns their status.

    Returns:
        HealthResponse with status of all components

    Example response:
        {
            "status":          "ok",
            "language":        "kn",
            "domain":          "legal",
            "version":         "0.1.0",
            "vector_store":    "ready",
            "nlp_pipeline":    "ready",
            "embedding_model": "ready",
            "total_documents": 84
        }
    """
    logger.info("Health check requested.")

    # ── Track component statuses ─────────────────────────────
    nlp_status       = "unknown"
    embedding_status = "unknown"
    vector_status    = "unknown"
    total_documents  = 0
    overall_status   = "ok"

    # ── Check NLP pipeline ───────────────────────────────────
    try:
        from nlp.preprocessing_pipeline import run as preprocess
        result = preprocess("ಪರೀಕ್ಷೆ")
        if result and result.get("processed_text"):
            nlp_status = "ready"
            logger.info("NLP pipeline: ready")
        else:
            nlp_status = "degraded"
            logger.warning("NLP pipeline: degraded")
    except Exception as e:
        nlp_status     = "error"
        overall_status = "degraded"
        logger.error(f"NLP pipeline error: {e}")

    # ── Check embedding model ────────────────────────────────
    try:
        from rag.embedder import embed_query, get_embedding_dimension
        vector = embed_query("test")
        dim    = get_embedding_dimension()
        if vector and len(vector) == dim:
            embedding_status = "ready"
            logger.info(f"Embedding model: ready (dim={dim})")
        else:
            embedding_status = "degraded"
            logger.warning("Embedding model: degraded")
    except Exception as e:
        embedding_status = "error"
        overall_status   = "degraded"
        logger.error(f"Embedding model error: {e}")

    # ── Check vector store ───────────────────────────────────
    try:
        from rag.vector_store import get_collection_stats
        stats           = get_collection_stats()
        total_documents = stats.get("total_documents", 0)

        if total_documents > 0:
            vector_status = "ready"
            logger.info(
                f"Vector store: ready "
                f"({total_documents} documents)"
            )
        else:
            vector_status  = "empty"
            overall_status = "degraded"
            logger.warning(
                "Vector store: empty. "
                "Run scripts/build_vector_store.py"
            )
    except Exception as e:
        vector_status  = "error"
        overall_status = "degraded"
        logger.error(f"Vector store error: {e}")

    # ── Log summary ──────────────────────────────────────────
    logger.info(
        f"Health check complete.\n"
        f"        Overall   : {overall_status}\n"
        f"        NLP       : {nlp_status}\n"
        f"        Embedding : {embedding_status}\n"
        f"        VectorDB  : {vector_status}\n"
        f"        Documents : {total_documents}"
    )

    return HealthResponse(
        status=overall_status,
        language=settings.DEFAULT_LANGUAGE,
        domain="legal",
        version=settings.APP_VERSION,
        vector_store=vector_status,
        nlp_pipeline=nlp_status,
        embedding_model=embedding_status,
        total_documents=total_documents,
    )


@router.get(
    "/ping",
    summary="Simple Ping",
    description="Simple ping endpoint to check if server is alive.",
)
async def ping():
    """
    Simple ping endpoint.
    Fastest way to check if server is running.
    Does not check any components.

    Returns:
        Simple pong response
    """
    return {
        "ping":    "pong",
        "status":  "alive",
        "message": "ಕನ್ನಡ ಕಾನೂನು AI ಸಕ್ರಿಯವಾಗಿದೆ",
    }