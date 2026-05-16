# rag/embedder.py
# Multilingual sentence embedder using LaBSE model.
# LaBSE supports Kannada and allows cross-lingual retrieval.
# Meaning: user can ask in Kannada and retrieve English legal docs.
#
# Model: sentence-transformers/LaBSE
# Embedding dimension: 768

import os
from loguru import logger

from sentence_transformers import SentenceTransformer

# ── Config ──────────────────────────────────────────────────
MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/LaBSE"
)

# ── Model singleton ──────────────────────────────────────────
# Model is loaded once and reused for all embedding calls.
# Avoids reloading the model on every request.
_model: SentenceTransformer = None


def get_model() -> SentenceTransformer:
    """
    Load and return the embedding model.
    Uses singleton pattern — loads only once.

    Returns:
        SentenceTransformer model instance
    """
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {MODEL_NAME}")
        logger.info("This may take a minute on first load...")
        try:
            _model = SentenceTransformer(MODEL_NAME)
            logger.success(
                f"Embedding model loaded successfully.\n"
                f"        Model     : {MODEL_NAME}\n"
                f"        Dimension : 768"
            )
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    return _model


def embed(texts: list) -> list:
    """
    Embed a list of texts into dense vectors.

    Args:
        texts : List of strings to embed

    Returns:
        List of float vectors (each 768 dimensions)

    Example:
        >>> vectors = embed(["IPC ಸೆಕ್ಷನ್ 302 ಏನು?"])
        >>> len(vectors[0])
        768
    """
    if not texts:
        logger.warning("embed() called with empty list.")
        return []

    # Filter out empty strings
    valid_texts = [t for t in texts if t and t.strip()]
    if not valid_texts:
        logger.warning("All texts were empty after filtering.")
        return []

    try:
        model   = get_model()
        logger.info(f"Embedding {len(valid_texts)} text(s)...")
        vectors = model.encode(
            valid_texts,
            show_progress_bar=len(valid_texts) > 10,
            batch_size=32,
            normalize_embeddings=True,    # Normalize for cosine similarity
        )
        logger.info(f"Embedding complete. Shape: {vectors.shape}")
        return vectors.tolist()

    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        raise


def embed_query(query: str) -> list:
    """
    Embed a single query string.
    Convenience wrapper around embed().

    Args:
        query : Single input string

    Returns:
        Single float vector (768 dimensions)

    Example:
        >>> vector = embed_query("ಪೊಲೀಸ್ ಬಂಧಿಸಿದರೆ ಹಕ್ಕುಗಳೇನು?")
        >>> len(vector)
        768
    """
    if not query or not query.strip():
        logger.warning("embed_query() called with empty string.")
        return []

    vectors = embed([query])
    return vectors[0] if vectors else []


def embed_documents(documents: list) -> list:
    """
    Embed a list of legal documents.
    Same as embed() but with document-specific logging.

    Args:
        documents : List of document strings

    Returns:
        List of float vectors

    Example:
        >>> docs = ["Section 302 — Murder...", "Section 420 — Cheating..."]
        >>> vectors = embed_documents(docs)
        >>> len(vectors)
        2
    """
    logger.info(f"Embedding {len(documents)} documents...")
    return embed(documents)


def similarity(vec1: list, vec2: list) -> float:
    """
    Calculate cosine similarity between two vectors.
    Since embeddings are normalized, dot product = cosine similarity.

    Args:
        vec1 : First embedding vector
        vec2 : Second embedding vector

    Returns:
        Similarity score between 0.0 and 1.0

    Example:
        >>> v1 = embed_query("ಕೊಲೆ ಶಿಕ್ಷೆ ಏನು?")
        >>> v2 = embed_query("ಹತ್ಯೆಗೆ ದಂಡ ಎಷ್ಟು?")
        >>> similarity(v1, v2)
        0.92   # High similarity — same meaning
    """
    if not vec1 or not vec2:
        return 0.0
    if len(vec1) != len(vec2):
        logger.warning("Vectors have different dimensions.")
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    return round(float(dot_product), 4)


def get_embedding_dimension() -> int:
    """
    Returns the embedding dimension of the loaded model.

    Returns:
        Integer dimension (768 for LaBSE)
    """
    model = get_model()
    return model.get_sentence_embedding_dimension()


# ── Quick test ───────────────────────────────────────────────
if __name__ == "__main__":

    print("── Embedder Test ──\n")

    # Test single query embedding
    query   = "IPC ಸೆಕ್ಷನ್ 302 ಕೊಲೆಗೆ ಶಿಕ್ಷೆ ಏನು?"
    vector  = embed_query(query)

    print(f"Query          : {query}")
    print(f"Vector dim     : {len(vector)}")
    print(f"First 5 values : {vector[:5]}")
    print()

    # Test similarity between related queries
    print("── Similarity Test ──\n")

    pairs = [
        (
            "ಕೊಲೆ ಶಿಕ್ಷೆ ಏನು?",
            "ಹತ್ಯೆಗೆ ದಂಡ ಎಷ್ಟು?",
            "Should be HIGH — same meaning"
        ),
        (
            "IPC ಸೆಕ್ಷನ್ 302 ಏನು?",
            "Section 302 IPC punishment for murder",
            "Should be HIGH — cross-lingual same meaning"
        ),
        (
            "ಕೊಲೆ ಶಿಕ್ಷೆ ಏನು?",
            "ಗ್ರಾಹಕ ನ್ಯಾಯಾಲಯ ದೂರು ಹೇಗೆ?",
            "Should be LOW — different topics"
        ),
    ]

    for q1, q2, label in pairs:
        v1    = embed_query(q1)
        v2    = embed_query(q2)
        score = similarity(v1, v2)
        print(f"Q1       : {q1}")
        print(f"Q2       : {q2}")
        print(f"Score    : {score}")
        print(f"Expected : {label}")
        print("-" * 55)