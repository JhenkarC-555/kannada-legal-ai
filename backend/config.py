# backend/config.py
# Central configuration for the Flask backend.
# Loads all settings from the .env file.
# All other backend files import settings from here.

import os
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

# ── Load .env file ───────────────────────────────────────────
# Looks for .env in the project root folder
ENV_PATH = Path(__file__).parent.parent / ".env"

if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
    logger.info(f".env loaded from: {ENV_PATH}")
else:
    logger.warning(
        f".env file not found at {ENV_PATH}. "
        f"Using default values."
    )


# ── App settings ─────────────────────────────────────────────
class Settings:
    """
    Central settings class.
    All values loaded from .env file.
    Falls back to safe defaults if not set.
    """

    # ── FastAPI ──────────────────────────────────────────────
    APP_TITLE       = "ಕನ್ನಡ ಕಾನೂನು AI"
    APP_DESCRIPTION = (
        "Kannada Legal AI — Pragmatic legal reasoning "
        "in Kannada language"
    )
    APP_VERSION     = "0.1.0"
    API_HOST        = os.getenv("API_HOST",  "0.0.0.0")
    API_PORT        = int(os.getenv("API_PORT", "5000"))
    DEBUG           = os.getenv("DEBUG", "True").lower() == "true"

    # ── CORS ─────────────────────────────────────────────────
    # Origins allowed to call the API
    # Add your frontend URL here
    ALLOWED_ORIGINS = ["*"]

    # ── Model settings ───────────────────────────────────────
    BASE_MODEL_NAME      = os.getenv(
        "BASE_MODEL_NAME",
        "ai4bharat/indic-bert"
    )
    FINETUNED_MODEL_PATH = os.getenv(
        "FINETUNED_MODEL_PATH",
        "training/checkpoints/best_model"
    )
    HF_TOKEN             = os.getenv("HF_TOKEN", "")

    # ── RAG settings ─────────────────────────────────────────
    EMBEDDING_MODEL = os.getenv(
        "EMBEDDING_MODEL",
        "sentence-transformers/LaBSE"
    )
    CHROMA_DB_PATH  = os.getenv(
        "CHROMA_DB_PATH",
        "data/vector_store"
    )
    CHUNK_SIZE      = int(os.getenv("CHUNK_SIZE",    "512"))
    CHUNK_OVERLAP   = int(os.getenv("CHUNK_OVERLAP",  "64"))
    TOP_K_RESULTS   = int(os.getenv("TOP_K_RESULTS",   "5"))

    # ── Legal disclaimers ────────────────────────────────────
    DISCLAIMER_KN = os.getenv(
        "DISCLAIMER_KN",
        "ಇದು ಕಾನೂನು ಸಲಹೆ ಅಲ್ಲ — ವಕೀಲರನ್ನು ಸಂಪರ್ಕಿಸಿ"
    )
    DISCLAIMER_EN = os.getenv(
        "DISCLAIMER_EN",
        "This is not legal advice — consult a qualified lawyer"
    )

    # ── Weights & Biases ─────────────────────────────────────
    WANDB_API_KEY = os.getenv("WANDB_API_KEY", "")
    WANDB_PROJECT = os.getenv("WANDB_PROJECT", "kannada-legal-ai")

    # ── Language settings ────────────────────────────────────
    DEFAULT_LANGUAGE  = "kn"
    SUPPORTED_LANGUAGES = ["kn", "en"]

    # ── API limits ───────────────────────────────────────────
    MAX_QUERY_LENGTH  = 500     # Max characters per query
    MAX_HISTORY_TURNS = 5       # Max conversation turns to keep
    REQUEST_TIMEOUT   = 30      # Seconds before timeout

    @classmethod
    def log_settings(cls):
        """Log all current settings for debugging."""
        logger.info(
            f"\n{'='*50}\n"
            f"  Kannada Legal AI — Settings\n"
            f"{'='*50}\n"
            f"  Host          : {cls.API_HOST}\n"
            f"  Port          : {cls.API_PORT}\n"
            f"  Debug         : {cls.DEBUG}\n"
            f"  Embedding     : {cls.EMBEDDING_MODEL}\n"
            f"  ChromaDB      : {cls.CHROMA_DB_PATH}\n"
            f"  Top K         : {cls.TOP_K_RESULTS}\n"
            f"  Max Query     : {cls.MAX_QUERY_LENGTH} chars\n"
            f"  HF Token      : {'Set' if cls.HF_TOKEN else 'Not set'}\n"
            f"{'='*50}"
        )

    @classmethod
    def validate(cls):
        """
        Validate critical settings on startup.
        Logs warnings for missing optional settings.
        """
        issues = []

        # Check ChromaDB path
        if not Path(cls.CHROMA_DB_PATH).exists():
            logger.warning(
                f"ChromaDB path does not exist: {cls.CHROMA_DB_PATH}. "
                f"Run scripts/build_vector_store.py first."
            )

        # Check HuggingFace token
        if not cls.HF_TOKEN:
            logger.warning(
                "HF_TOKEN not set. "
                "Some models may not be accessible."
            )

        # Check WandB key
        if not cls.WANDB_API_KEY:
            logger.warning(
                "WANDB_API_KEY not set. "
                "Training metrics will not be tracked."
            )

        if issues:
            for issue in issues:
                logger.error(issue)
            return False

        logger.success("Settings validation passed.")
        return True


# ── Singleton instance ────────────────────────────────────────
settings = Settings()


# ── Quick test ───────────────────────────────────────────────
if __name__ == "__main__":
    settings.log_settings()
    settings.validate()