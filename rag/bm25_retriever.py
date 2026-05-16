# rag/bm25_retriever.py
# BM25 keyword-based retriever.
# Essential for exact section number lookups.
#
# Why BM25 alongside ChromaDB?
#   - ChromaDB  : finds semantically similar chunks (meaning-based)
#   - BM25      : finds exact keyword matches (term-based)
#
# Example where BM25 wins:
#   Query: "Section 302"
#   ChromaDB may return section 300, 303 (semantically close)
#   BM25 will return exactly section 302 (keyword match)
#
# Both are combined in hybrid_retriever.py

import json
import pickle
from pathlib import Path
from loguru import logger

try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False
    logger.warning(
        "rank-bm25 not installed. "
        "Run: pip install rank-bm25"
    )

# ── BM25 index save path ─────────────────────────────────────
BM25_INDEX_PATH = Path("data/processed/bm25_index.pkl")
BM25_DOCS_PATH  = Path("data/processed/bm25_docs.json")


# ── BM25 Retriever class ─────────────────────────────────────
class BM25Retriever:
    """
    BM25 keyword retriever for legal documents.

    Attributes:
        documents : List of document strings
        metadatas : List of metadata dicts per document
        bm25      : BM25Okapi index object
    """

    def __init__(self):
        self.documents: list = []
        self.metadatas: list = []
        self.bm25             = None

    # ── Build index ──────────────────────────────────────────
    def build(
        self,
        documents: list,
        metadatas: list = None,
    ) -> None:
        """
        Build a BM25 index from a list of documents.

        Args:
            documents : List of text strings to index
            metadatas : Optional list of metadata dicts

        Example:
            >>> retriever = BM25Retriever()
            >>> retriever.build(
            ...     documents=["Section 302 murder...", "Section 420 cheating..."],
            ...     metadatas=[{"law": "IPC", "section": "302"}, ...]
            ... )
        """
        if not BM25_AVAILABLE:
            logger.error("rank-bm25 not installed.")
            return

        if not documents:
            logger.warning("build: empty document list.")
            return

        self.documents = documents
        self.metadatas = metadatas or [{} for _ in documents]

        logger.info(f"Building BM25 index for {len(documents)} documents...")

        # Tokenize documents for BM25
        # BM25 works on token lists
        tokenized = [
            self._tokenize(doc)
            for doc in documents
        ]

        self.bm25 = BM25Okapi(tokenized)
        logger.success(
            f"BM25 index built.\n"
            f"        Documents : {len(documents)}\n"
            f"        Avg tokens: "
            f"{sum(len(t) for t in tokenized) // len(tokenized)}"
        )

    def _tokenize(self, text: str) -> list:
        """
        Tokenize text for BM25 indexing.
        Handles both Kannada and English text.

        Args:
            text : Input text string

        Returns:
            List of lowercase tokens
        """
        if not text:
            return []

        # Split on whitespace and punctuation
        import re
        tokens = re.findall(
            r"[\u0C80-\u0CFF]+|[a-zA-Z0-9]+",
            text.lower()
        )
        return tokens

    # ── Search ───────────────────────────────────────────────
    def search(
        self,
        query:  str,
        top_k:  int = 5,
    ) -> list:
        """
        Search for most relevant documents using BM25.

        Args:
            query : Search query string
            top_k : Number of results to return

        Returns:
            List of result dicts with text, metadata, score

        Example:
            >>> results = retriever.search("Section 302 murder", top_k=3)
            >>> results[0]['metadata']['section_number']
            '302'
            >>> results[0]['score']
            8.43
        """
        if not self.bm25:
            logger.warning("BM25 index not built yet. Call build() first.")
            return []

        if not query or not query.strip():
            logger.warning("search: empty query.")
            return []

        # Tokenize query
        query_tokens = self._tokenize(query)
        if not query_tokens:
            logger.warning("search: query produced no tokens.")
            return []

        logger.info(
            f"BM25 search: '{query[:60]}' "
            f"tokens={query_tokens[:5]}..."
        )

        # Get BM25 scores
        scores = self.bm25.get_scores(query_tokens)

        # Get top-k indices sorted by score
        top_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )[:top_k]

        # Build results
        results = []
        for idx in top_indices:
            score = float(scores[idx])
            if score <= 0:
                continue
            results.append({
                "text":     self.documents[idx],
                "metadata": self.metadatas[idx],
                "score":    round(score, 4),
                "index":    idx,
            })

        logger.info(
            f"BM25 results: {len(results)} found. "
            f"Top score: {results[0]['score'] if results else 'N/A'}"
        )
        return results

    def search_by_section(
        self,
        section_number: str,
        law_name:       str = "IPC",
        top_k:          int = 3,
    ) -> list:
        """
        Search specifically for a section number.
        Constructs a targeted query for best BM25 results.

        Args:
            section_number : e.g. '302'
            law_name       : e.g. 'IPC'
            top_k          : Number of results

        Returns:
            List of result dicts

        Example:
            >>> results = retriever.search_by_section("302", "IPC")
        """
        query = f"{law_name} Section {section_number} ವಿಭಾಗ {section_number}"
        return self.search(query, top_k=top_k)

    # ── Save / Load index ────────────────────────────────────
    def save(self) -> None:
        """
        Save the BM25 index and documents to disk.
        Avoids rebuilding the index every time.
        """
        if not self.bm25:
            logger.warning("No index to save.")
            return

        BM25_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Save BM25 index (pickle)
        with open(BM25_INDEX_PATH, "wb") as f:
            pickle.dump(self.bm25, f)

        # Save documents and metadata (JSON)
        with open(BM25_DOCS_PATH, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "documents": self.documents,
                    "metadatas": self.metadatas,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        logger.success(
            f"BM25 index saved.\n"
            f"        Index : {BM25_INDEX_PATH}\n"
            f"        Docs  : {BM25_DOCS_PATH}"
        )

    def load(self) -> bool:
        """
        Load a saved BM25 index from disk.

        Returns:
            True if loaded successfully, False otherwise
        """
        if not BM25_INDEX_PATH.exists() or not BM25_DOCS_PATH.exists():
            logger.info("No saved BM25 index found.")
            return False

        try:
            # Load BM25 index
            with open(BM25_INDEX_PATH, "rb") as f:
                self.bm25 = pickle.load(f)

            # Load documents and metadata
            with open(BM25_DOCS_PATH, encoding="utf-8") as f:
                data = json.load(f)

            self.documents = data["documents"]
            self.metadatas = data["metadatas"]

            logger.success(
                f"BM25 index loaded.\n"
                f"        Documents : {len(self.documents)}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to load BM25 index: {e}")
            return False

    # ── Stats ────────────────────────────────────────────────
    def get_stats(self) -> dict:
        """
        Returns stats about the current BM25 index.

        Returns:
            Dictionary with index statistics
        """
        return {
            "total_documents": len(self.documents),
            "index_built":     self.bm25 is not None,
            "index_path":      str(BM25_INDEX_PATH),
            "docs_path":       str(BM25_DOCS_PATH),
            "index_saved":     BM25_INDEX_PATH.exists(),
        }

    def is_ready(self) -> bool:
        """
        Check if the BM25 index is built and ready.

        Returns:
            True if index is ready for search
        """
        return self.bm25 is not None and len(self.documents) > 0


# ── Module-level singleton ───────────────────────────────────
# A single shared retriever instance used across the project.
_retriever: BM25Retriever = None


def get_retriever() -> BM25Retriever:
    """
    Get the shared BM25Retriever instance.
    Loads from disk if available.
    Builds from scratch if not.

    Returns:
        Ready BM25Retriever instance
    """
    global _retriever

    if _retriever is None:
        _retriever = BM25Retriever()

        # Try loading saved index first
        loaded = _retriever.load()

        if not loaded:
            logger.info(
                "No saved BM25 index. "
                "Building from processed data..."
            )
            _build_from_data(_retriever)

    return _retriever


def _build_from_data(retriever: BM25Retriever) -> None:
    """
    Build BM25 index from processed JSON data files.

    Args:
        retriever : BM25Retriever instance to build into
    """
    from rag.document_chunker import chunk_from_records

    data_files = [
        Path("data/processed/translated_ipc_kn.json"),
        Path("data/processed/translated_karnataka_kn.json"),
        Path("data/processed/translated_judgments_kn.json"),
    ]

    all_texts = []
    all_metas = []

    for data_file in data_files:
        if not data_file.exists():
            logger.warning(f"Data file not found: {data_file}")
            continue

        with open(data_file, encoding="utf-8") as f:
            records = json.load(f)

        chunks = chunk_from_records(records)
        for chunk in chunks:
            all_texts.append(chunk.text)
            all_metas.append(chunk.metadata)

        logger.info(
            f"Loaded {len(chunks)} chunks from {data_file.name}"
        )

    if all_texts:
        retriever.build(all_texts, all_metas)
        retriever.save()
    else:
        logger.warning(
            "No data found to build BM25 index. "
            "Run data collection scripts first."
        )


# ── Quick test ───────────────────────────────────────────────
if __name__ == "__main__":

    print("── BM25 Retriever Test ──\n")

    # Get shared retriever
    retriever = get_retriever()

    if not retriever.is_ready():
        print("BM25 index not ready. Run data collection first.")
    else:
        stats = retriever.get_stats()
        print(f"Documents  : {stats['total_documents']}")
        print(f"Index built: {stats['index_built']}")
        print(f"Index saved: {stats['index_saved']}")
        print()

        # Test queries
        test_queries = [
            ("Section 302 murder punishment",      "Exact section — should rank §302 high"),
            ("ಕೊಲೆ ಶಿಕ್ಷೆ",                       "Kannada — murder punishment"),
            ("420 cheating fraud",                  "Exact section — should rank §420 high"),
            ("ಮೋಸ ದಂಡ",                            "Kannada — cheating penalty"),
            ("bail jaminu procedure",               "Procedure — bail"),
            ("FIR ದಾಖಲು",                          "Kannada — FIR filing"),
        ]

        print("── Search Test ──\n")
        for query, label in test_queries:
            results = retriever.search(query, top_k=2)
            print(f"Query  : {query}")
            print(f"Label  : {label}")
            if results:
                top = results[0]
                print(
                    f"Top    : §{top['metadata'].get('section_number','?')} "
                    f"({top['metadata'].get('law_name','?')}) "
                    f"score={top['score']}"
                )
                print(f"Text   : {top['text'][:80]}...")
            else:
                print("No results found.")
            print("-" * 55)

        # Test direct section lookup
        print("\n── Section Lookup Test ──\n")
        for section in ["302", "420", "379"]:
            results = retriever.search_by_section(section, "IPC")
            print(
                f"Section §{section}: "
                f"{len(results)} results | "
                f"Top score: {results[0]['score'] if results else 'N/A'}"
            )