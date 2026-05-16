# rag/vector_store.py
# ChromaDB vector store manager.
# Stores legal document chunks as dense vectors.
# Retrieves most relevant chunks for a given query.
#
# Flow:
#   Add chunks -> embed -> store in ChromaDB
#   Query      -> embed -> find nearest vectors -> return chunks

import os
import json
from pathlib import Path
from loguru import logger

import chromadb
from chromadb.config import Settings

from rag.embedder       import embed, embed_query
from rag.document_chunker import LegalChunk

# ── Config ──────────────────────────────────────────────────
DB_PATH         = os.getenv("CHROMA_DB_PATH", "data/vector_store")
COLLECTION_NAME = "kannada_legal_docs"
TOP_K_DEFAULT   = int(os.getenv("TOP_K_RESULTS", 5))

# ── Client singleton ─────────────────────────────────────────
_client     = None
_collection = None


def _get_collection():
    """
    Get or create the ChromaDB collection.
    Uses singleton pattern — connects only once.

    Returns:
        ChromaDB collection object
    """
    global _client, _collection

    if _collection is None:
        # Create DB directory if needed
        Path(DB_PATH).mkdir(parents=True, exist_ok=True)

        logger.info(f"Connecting to ChromaDB at: {DB_PATH}")
        _client = chromadb.PersistentClient(path=DB_PATH)

        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={
                "hnsw:space":           "cosine",
                "hnsw:construction_ef": 100,
                "hnsw:search_ef":       50,
            }
        )
        logger.success(
            f"ChromaDB ready.\n"
            f"        Collection : {COLLECTION_NAME}\n"
            f"        Documents  : {_collection.count()}\n"
            f"        Path       : {DB_PATH}"
        )

    return _collection


# ── Add chunks ───────────────────────────────────────────────
def add_chunks(chunks: list) -> None:
    """
    Add a list of LegalChunk objects to the vector store.

    Args:
        chunks : List of LegalChunk objects

    Example:
        >>> from rag.document_chunker import chunk_from_records
        >>> chunks = chunk_from_records(records)
        >>> add_chunks(chunks)
    """
    if not chunks:
        logger.warning("add_chunks: empty chunk list.")
        return

    col = _get_collection()

    # Process in batches of 100 to avoid memory issues
    batch_size = 100
    total_added = 0

    for batch_start in range(0, len(chunks), batch_size):
        batch  = chunks[batch_start: batch_start + batch_size]
        texts  = [c.text     for c in batch]
        metas  = [c.metadata for c in batch]
        ids    = [
            f"{c.chunk_id}_{batch_start + i}"
            for i, c in enumerate(batch)
        ]

        # Generate embeddings
        logger.info(
            f"Embedding batch "
            f"[{batch_start + 1} - {batch_start + len(batch)}]"
            f" of {len(chunks)}..."
        )
        embeddings = embed(texts)

        if not embeddings:
            logger.error("Embedding failed for batch. Skipping.")
            continue

        # Serialize metadata values
        # ChromaDB only supports str, int, float, bool
        clean_metas = []
        for meta in metas:
            clean = {}
            for k, v in meta.items():
                if isinstance(v, (str, int, float, bool)):
                    clean[k] = v
                else:
                    clean[k] = str(v)
            clean_metas.append(clean)

        # Add to ChromaDB
        try:
            col.add(
                documents=texts,
                embeddings=embeddings,
                metadatas=clean_metas,
                ids=ids,
            )
            total_added += len(batch)
            logger.info(
                f"Batch added: {len(batch)} chunks. "
                f"Total so far: {total_added}"
            )
        except Exception as e:
            logger.error(f"Failed to add batch: {e}")
            continue

    logger.success(
        f"add_chunks complete.\n"
        f"        Added     : {total_added} chunks\n"
        f"        Total DB  : {col.count()} documents"
    )


def add_chunk(chunk: LegalChunk) -> None:
    """
    Add a single LegalChunk to the vector store.

    Args:
        chunk : Single LegalChunk object
    """
    add_chunks([chunk])


# ── Search ───────────────────────────────────────────────────
def search(
    query:       str,
    top_k:       int  = TOP_K_DEFAULT,
    filter_lang: str  = None,
    filter_law:  str  = None,
) -> list:
    """
    Search for most relevant legal chunks for a query.

    Args:
        query       : User query string (Kannada or English)
        top_k       : Number of results to return
        filter_lang : Filter by language ('kn' or 'en')
        filter_law  : Filter by law name ('IPC', 'CrPC' etc.)

    Returns:
        List of result dicts with text, metadata, score

    Example:
        >>> results = search("ಕೊಲೆಗೆ ಶಿಕ್ಷೆ ಏನು?", top_k=3)
        >>> results[0]['metadata']['section_number']
        '302'
        >>> results[0]['score']
        0.94
    """
    if not query or not query.strip():
        logger.warning("search: empty query received.")
        return []

    col = _get_collection()

    if col.count() == 0:
        logger.warning(
            "Vector store is empty. "
            "Run scripts/build_vector_store.py first."
        )
        return []

    # Build filter conditions
    where = {}
    if filter_lang and filter_law:
        where = {
            "$and": [
                {"language": {"$eq": filter_lang}},
                {"law_name": {"$eq": filter_law}},
            ]
        }
    elif filter_lang:
        where = {"language": {"$eq": filter_lang}}
    elif filter_law:
        where = {"law_name": {"$eq": filter_law}}

    # Embed query
    logger.info(f"Searching: '{query[:60]}...' " if len(query) > 60 else f"Searching: '{query}'")
    q_vector = embed_query(query)

    if not q_vector:
        logger.error("Failed to embed query.")
        return []

    # Query ChromaDB
    try:
        query_params = {
            "query_embeddings": [q_vector],
            "n_results":        min(top_k, col.count()),
            "include":          ["documents", "metadatas", "distances"],
        }
        if where:
            query_params["where"] = where

        results = col.query(**query_params)

    except Exception as e:
        logger.error(f"ChromaDB query failed: {e}")
        return []

    # Format results
    hits = []
    docs      = results.get("documents", [[]])[0]
    metas     = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for doc, meta, dist in zip(docs, metas, distances):
        # Convert distance to similarity score
        # ChromaDB cosine distance: 0 = identical, 2 = opposite
        score = round(1 - (dist / 2), 4)
        hits.append({
            "text":     doc,
            "metadata": meta,
            "score":    score,
            "distance": round(dist, 4),
        })

    logger.info(
        f"Search complete. "
        f"Found {len(hits)} results. "
        f"Top score: {hits[0]['score'] if hits else 'N/A'}"
    )
    return hits


def search_by_section(
    section_number: str,
    law_name:       str = "IPC",
) -> list:
    """
    Direct section number lookup in the vector store.

    Args:
        section_number : Section number string e.g. '302'
        law_name       : Law name e.g. 'IPC'

    Returns:
        List of matching chunks

    Example:
        >>> results = search_by_section("302", "IPC")
        >>> results[0]['metadata']['title']
        'Punishment for murder'
    """
    col = _get_collection()

    if col.count() == 0:
        logger.warning("Vector store is empty.")
        return []

    try:
        results = col.get(
            where={
                "$and": [
                    {"section_number": {"$eq": section_number}},
                    {"law_name":       {"$eq": law_name}},
                ]
            },
            include=["documents", "metadatas"],
        )

        hits = []
        for doc, meta in zip(
            results.get("documents", []),
            results.get("metadatas", [])
        ):
            hits.append({
                "text":     doc,
                "metadata": meta,
                "score":    1.0,   # Exact match
            })

        logger.info(
            f"Section lookup §{section_number} ({law_name}): "
            f"{len(hits)} results."
        )
        return hits

    except Exception as e:
        logger.error(f"Section lookup failed: {e}")
        return []


# ── Utility functions ────────────────────────────────────────
def get_collection_stats() -> dict:
    """
    Returns stats about the current vector store.

    Returns:
        Dictionary with collection statistics
    """
    col   = _get_collection()
    count = col.count()

    return {
        "collection_name": COLLECTION_NAME,
        "total_documents": count,
        "db_path":         DB_PATH,
        "is_empty":        count == 0,
    }


def clear_collection() -> None:
    """
    Delete all documents from the collection.
    Use with caution — this cannot be undone.
    """
    global _collection
    col = _get_collection()
    col.delete(where={"chunk_type": {"$ne": ""}})
    logger.warning("Vector store cleared.")


def collection_exists() -> bool:
    """
    Check if the vector store has any documents.

    Returns:
        True if collection has documents
    """
    col = _get_collection()
    return col.count() > 0


# ── Quick test ───────────────────────────────────────────────
if __name__ == "__main__":
    import json
    from pathlib import Path
    from rag.document_chunker import chunk_from_records

    print("── Vector Store Test ──\n")

    # ── Step 1: Check stats ──────────────────────────────────
    stats = get_collection_stats()
    print(f"Collection : {stats['collection_name']}")
    print(f"Documents  : {stats['total_documents']}")
    print(f"Path       : {stats['db_path']}")
    print()

    # ── Step 2: Load and index data ──────────────────────────
    ipc_path = Path("data/processed/translated_ipc_kn.json")

    if ipc_path.exists() and not collection_exists():
        print("Indexing IPC sections into vector store...")
        with open(ipc_path, encoding="utf-8") as f:
            records = json.load(f)
        chunks = chunk_from_records(records)
        add_chunks(chunks)
        print()

    # ── Step 3: Search test ──────────────────────────────────
    if collection_exists():
        test_queries = [
            "ಕೊಲೆಗೆ ಶಿಕ್ಷೆ ಏನು?",
            "What is punishment for murder?",
            "ಮೋಸ ಮಾಡಿದರೆ ಎಷ್ಟು ಜೈಲು?",
            "FIR ದಾಖಲಿಸುವುದು ಹೇಗೆ?",
        ]

        print("── Search Test ──\n")
        for query in test_queries:
            results = search(query, top_k=2)
            print(f"Query   : {query}")
            if results:
                top = results[0]
                print(f"Top hit : §{top['metadata'].get('section_number','?')} "
                      f"({top['metadata'].get('law_name','?')})")
                print(f"Score   : {top['score']}")
                print(f"Text    : {top['text'][:100]}...")
            else:
                print("No results found.")
            print("-" * 55)

        # ── Step 4: Direct section lookup ────────────────────
        print("\n── Section Lookup Test ──\n")
        results = search_by_section("302", "IPC")
        if results:
            print(f"Section 302 found: {len(results)} chunks")
            print(f"Text: {results[0]['text'][:100]}...")
        else:
            print("Section 302 not found in vector store.")
    else:
        print(
            "Vector store is empty.\n"
            "Run: python scripts/build_vector_store.py"
        )