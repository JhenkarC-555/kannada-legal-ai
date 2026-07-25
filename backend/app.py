# backend/app.py
# Main FastAPI application entry point.
#
# Run the server with:
#   uvicorn backend.app:app --reload --port 5000
#
# API docs available at:
#   http://localhost:5000/docs        (Swagger UI)
#   http://localhost:5000/redoc       (ReDoc)

import sys
import os
from pathlib import Path

# ── Add project root to path ─────────────────────────────────
# This ensures all modules (nlp, rag, pragmatics) are importable
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from loguru import logger

from backend.config import settings


# ── Lifespan handler ─────────────────────────────────────────
# Runs startup and shutdown logic for the app.
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup and shutdown events.
    Startup  : Load models, validate settings, warm up pipeline.
    Shutdown : Clean up resources.
    """
    # ── STARTUP ──────────────────────────────────────────────
    logger.info(
        "\n"
        "╔══════════════════════════════════════╗\n"
        "║     ಕನ್ನಡ ಕಾನೂನು AI — Starting      ║\n"
        "║     Kannada Legal AI Backend          ║\n"
        "╚══════════════════════════════════════╝"
    )

    # Log settings
    settings.log_settings()

    # Validate settings
    settings.validate()

    # Warm up NLP pipeline
    logger.info("Warming up NLP pipeline...")
    try:
        from nlp.preprocessing_pipeline import run as preprocess
        test_result = preprocess("ಪರೀಕ್ಷೆ")
        logger.success("NLP pipeline ready.")
    except Exception as e:
        logger.warning(f"NLP warmup failed: {e}")

    # Warm up embedding model
    logger.info("Warming up embedding model...")
    try:
        from rag.embedder import embed_query
        embed_query("test")
        logger.success("Embedding model ready.")
    except Exception as e:
        logger.warning(f"Embedding warmup failed: {e}")

    # Check vector store
    logger.info("Checking vector store...")
    try:
        from rag.vector_store import get_collection_stats
        stats = get_collection_stats()
        if stats["is_empty"]:
            logger.warning(
                "Vector store is empty. "
                "Run: python -m scripts.build_vector_store"
            )
        else:
            logger.success(
                f"Vector store ready: "
                f"{stats['total_documents']} documents."
            )
    except Exception as e:
        logger.warning(f"Vector store check failed: {e}")

    logger.success(
        "\n"
        "╔══════════════════════════════════════╗\n"
        "║     Backend Started Successfully      ║\n"
        f"║     http://localhost:{settings.API_PORT}            ║\n"
        f"║     Docs: /docs                       ║\n"
        "╚══════════════════════════════════════╝"
    )

    yield  # App runs here

    # ── SHUTDOWN ─────────────────────────────────────────────
    logger.info("Shutting down Kannada Legal AI backend...")


# ── Create FastAPI app ───────────────────────────────────────
app = FastAPI(
    title=settings.APP_TITLE,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── Middleware ───────────────────────────────────────────────
# CORS — allows frontend to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip — compress large responses
app.add_middleware(GZipMiddleware, minimum_size=1000)


# ── Exception handlers ───────────────────────────────────────
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error":   "Route not found",
            "message": "ಈ ಮಾರ್ಗ ಅಸ್ತಿತ್ವದಲ್ಲಿಲ್ಲ",
            "docs":    "/docs",
        }
    )


@app.exception_handler(500)
async def server_error_handler(request, exc):
    logger.error(f"Server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error":   "Internal server error",
            "message": "ಸರ್ವರ್ ದೋಷ ಸಂಭವಿಸಿದೆ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.",
        }
    )


# ── Include routers ──────────────────────────────────────────
from backend.routes.query  import router as query_router
from backend.routes.health import router as health_router

app.include_router(
    health_router,
    prefix="/api",
    tags=["Health"],
)
app.include_router(
    query_router,
    prefix="/api",
    tags=["Query"],
)


# ── Root endpoint ────────────────────────────────────────────
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint.
    Returns basic API information.
    """
    return {
        "name":        "ಕನ್ನಡ ಕಾನೂನು AI",
        "name_en":     "Kannada Legal AI",
        "version":     settings.APP_VERSION,
        "description": "Pragmatic legal reasoning in Kannada",
        "language":    "Kannada (ಕನ್ನಡ)",
        "domain":      "Legal",
        "docs":        "/docs",
        "health":      "/api/health",
        "query":       "/api/query",
        "status":      "running",
    }


# ── Run directly ─────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info",
    )