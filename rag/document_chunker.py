# rag/document_chunker.py
# Splits legal documents into meaningful chunks for the vector store.
#
# Strategy:
#   1. Section-based chunking  — one chunk per IPC/law section (best)
#   2. Paragraph-based chunking — splits on paragraph breaks
#   3. Sliding window           — fallback for unstructured text
#
# Each chunk keeps its metadata:
#   law_name, section_number, source, language, chunk_type

import re
import os
from dataclasses import dataclass, field
from loguru import logger

# ── Config ──────────────────────────────────────────────────
CHUNK_SIZE    = int(os.getenv("CHUNK_SIZE",    512))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP",  64))

# ── Section patterns ─────────────────────────────────────────
# Matches patterns like:
#   "Section 302."
#   "ವಿಭಾಗ 302"
#   "ಸೆಕ್ಷನ್ 302A"

SECTION_PATTERN = re.compile(
    r"((?:Section|ವಿಭಾಗ|ಸೆಕ್ಷನ್)\s*\d+[A-Z]?\.?.*?)"
    r"(?=(?:Section|ವಿಭಾಗ|ಸೆಕ್ಷನ್)\s*\d|$)",
    re.DOTALL | re.IGNORECASE,
)

SECTION_NUMBER_PATTERN = re.compile(
    r"(?:Section|ವಿಭಾಗ|ಸೆಕ್ಷನ್)\s*(\d+[A-Z]?)",
    re.IGNORECASE,
)


# ── Chunk dataclass ──────────────────────────────────────────
@dataclass
class LegalChunk:
    """
    Represents a single chunk of a legal document.

    Attributes:
        text         : The actual text content of the chunk
        metadata     : Dictionary with source, law, section info
        chunk_id     : Unique identifier for this chunk
        char_count   : Number of characters in the chunk
        token_count  : Approximate number of tokens
    """
    text:       str
    metadata:   dict  = field(default_factory=dict)
    chunk_id:   str   = ""
    char_count: int   = 0
    token_count: int  = 0

    def __post_init__(self):
        self.char_count  = len(self.text)
        self.token_count = len(self.text.split())
        if not self.chunk_id:
            self.chunk_id = f"chunk_{abs(hash(self.text)) % 999999:06d}"


# ── Chunking functions ───────────────────────────────────────
def chunk_by_section(
    document:  str,
    source:    str = "",
    law_name:  str = "",
    language:  str = "en",
) -> list:
    """
    Split a legal document by section markers.
    Best strategy for structured legal texts like IPC.

    Args:
        document : Full legal document text
        source   : Source URL or filename
        law_name : Name of the law (e.g. 'IPC', 'CrPC')
        language : Language code ('en' or 'kn')

    Returns:
        List of LegalChunk objects

    Example:
        >>> chunks = chunk_by_section(ipc_text, law_name="IPC")
        >>> chunks[0].metadata['section_number']
        '302'
    """
    if not document or not document.strip():
        logger.warning("chunk_by_section: empty document received.")
        return []

    matches = SECTION_PATTERN.findall(document)
    chunks  = []

    for match in matches:
        text = match.strip()
        if len(text) < 20:
            continue

        # Extract section number
        num_match  = SECTION_NUMBER_PATTERN.search(text)
        section_num = num_match.group(1) if num_match else "unknown"

        # Extract title (first line)
        lines = text.split("\n")
        title = lines[0].strip() if lines else ""

        chunk = LegalChunk(
            text=text,
            metadata={
                "source":         source,
                "law_name":       law_name,
                "section_number": section_num,
                "title":          title,
                "language":       language,
                "chunk_type":     "section",
            }
        )
        chunks.append(chunk)
        logger.debug(
            f"Section chunk: {law_name} §{section_num} "
            f"({chunk.token_count} tokens)"
        )

    if not chunks:
        logger.info(
            "No section markers found. "
            "Falling back to sliding window chunker."
        )
        chunks = chunk_sliding_window(document, source, law_name, language)

    logger.info(
        f"chunk_by_section: {len(chunks)} chunks "
        f"from '{law_name}' document."
    )
    return chunks


def chunk_by_paragraph(
    document:  str,
    source:    str = "",
    law_name:  str = "",
    language:  str = "en",
) -> list:
    """
    Split a legal document by paragraph breaks.
    Good for judgment texts and articles.

    Args:
        document : Full document text
        source   : Source URL or filename
        law_name : Name of the law or document
        language : Language code

    Returns:
        List of LegalChunk objects

    Example:
        >>> chunks = chunk_by_paragraph(judgment_text, law_name="HC Judgment")
        >>> len(chunks)
        12
    """
    if not document or not document.strip():
        return []

    # Split on double newlines (paragraph breaks)
    paragraphs = re.split(r"\n\s*\n", document)
    chunks     = []

    for i, para in enumerate(paragraphs):
        text = para.strip()
        if len(text) < 30:
            continue

        # Merge short paragraphs with next one
        if len(text.split()) < 20 and i + 1 < len(paragraphs):
            continue

        chunk = LegalChunk(
            text=text,
            metadata={
                "source":         source,
                "law_name":       law_name,
                "paragraph_index": i,
                "language":       language,
                "chunk_type":     "paragraph",
            }
        )
        chunks.append(chunk)

    logger.info(
        f"chunk_by_paragraph: {len(chunks)} chunks "
        f"from '{law_name}' document."
    )
    return chunks


def chunk_sliding_window(
    document:  str,
    source:    str = "",
    law_name:  str = "",
    language:  str = "en",
) -> list:
    """
    Sliding window chunker.
    Fallback for unstructured text.
    Splits text into overlapping windows of words.

    Args:
        document : Full document text
        source   : Source URL or filename
        law_name : Name of the law or document
        language : Language code

    Returns:
        List of LegalChunk objects

    Example:
        >>> chunks = chunk_sliding_window(raw_text)
        >>> chunks[0].token_count
        512
    """
    if not document or not document.strip():
        return []

    words  = document.split()
    chunks = []
    step   = max(CHUNK_SIZE - CHUNK_OVERLAP, 1)

    for i, start in enumerate(range(0, len(words), step)):
        chunk_words = words[start: start + CHUNK_SIZE]
        if not chunk_words:
            break

        text = " ".join(chunk_words)

        chunk = LegalChunk(
            text=text,
            metadata={
                "source":       source,
                "law_name":     law_name,
                "window_index": i,
                "window_start": start,
                "window_end":   start + len(chunk_words),
                "language":     language,
                "chunk_type":   "sliding_window",
            }
        )
        chunks.append(chunk)

    logger.info(
        f"chunk_sliding_window: {len(chunks)} chunks "
        f"(size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})."
    )
    return chunks


# ── Smart chunker ────────────────────────────────────────────
def smart_chunk(
    document:  str,
    source:    str = "",
    law_name:  str = "",
    language:  str = "en",
) -> list:
    """
    Automatically picks the best chunking strategy.

    Strategy selection:
        1. If section markers found   -> chunk_by_section
        2. If paragraph breaks found  -> chunk_by_paragraph
        3. Otherwise                  -> chunk_sliding_window

    Args:
        document : Full document text
        source   : Source URL or filename
        law_name : Name of the law
        language : Language code

    Returns:
        List of LegalChunk objects

    Example:
        >>> chunks = smart_chunk(ipc_text, law_name="IPC")
        >>> chunks[0].metadata['chunk_type']
        'section'
    """
    if not document or not document.strip():
        logger.warning("smart_chunk: empty document.")
        return []

    # Check for section markers
    has_sections = bool(SECTION_PATTERN.search(document))
    if has_sections:
        logger.info("smart_chunk: using section-based chunking.")
        return chunk_by_section(document, source, law_name, language)

    # Check for paragraph breaks
    has_paragraphs = "\n\n" in document
    if has_paragraphs:
        logger.info("smart_chunk: using paragraph-based chunking.")
        return chunk_by_paragraph(document, source, law_name, language)

    # Fallback
    logger.info("smart_chunk: using sliding window chunking.")
    return chunk_sliding_window(document, source, law_name, language)


# ── Chunk from JSON record ───────────────────────────────────
def chunk_from_record(record: dict) -> list:
    """
    Create chunks from a single JSON record.
    Used to process records from translated JSON files.

    Args:
        record : Dictionary with 'text', 'law', 'section_number' etc.

    Returns:
        List of LegalChunk objects

    Example:
        >>> record = {
        ...     "section_number": "302",
        ...     "title": "Punishment for murder",
        ...     "text": "Whoever commits murder...",
        ...     "text_kn": "ಯಾರಾದರೂ ಕೊಲೆ ಮಾಡಿದರೆ...",
        ...     "law": "IPC",
        ...     "source": "indiacode.nic.in"
        ... }
        >>> chunks = chunk_from_record(record)
        >>> len(chunks)
        2  # one English + one Kannada chunk
    """
    chunks     = []
    law_name   = record.get("law",      record.get("law_name", "Unknown"))
    source     = record.get("source",   "")
    section_num = record.get("section_number", "unknown")
    title      = record.get("title",    "")

    base_metadata = {
        "law_name":       law_name,
        "section_number": section_num,
        "title":          title,
        "source":         source,
        "chunk_type":     "record",
    }

    # English chunk
    en_text = record.get("text", "").strip()
    if en_text and len(en_text) > 20:
        chunks.append(LegalChunk(
            text=en_text,
            metadata={**base_metadata, "language": "en"}
        ))

    # Kannada chunk
    kn_text = record.get("text_kn", "").strip()
    if kn_text and len(kn_text) > 20:
        chunks.append(LegalChunk(
            text=kn_text,
            metadata={**base_metadata, "language": "kn"}
        ))

    # Kannada title chunk (for better section lookup)
    kn_title = record.get("title_kn", "").strip()
    if kn_title:
        combined = f"{kn_title}. {kn_text}" if kn_text else kn_title
        chunks.append(LegalChunk(
            text=combined,
            metadata={**base_metadata, "language": "kn", "chunk_type": "title_body"}
        ))

    return chunks


def chunk_from_records(records: list) -> list:
    """
    Process a list of JSON records into chunks.

    Args:
        records : List of record dictionaries

    Returns:
        List of all LegalChunk objects

    Example:
        >>> with open('data/processed/translated_ipc_kn.json') as f:
        ...     records = json.load(f)
        >>> all_chunks = chunk_from_records(records)
        >>> len(all_chunks)
        84
    """
    all_chunks = []
    for i, record in enumerate(records):
        chunks = chunk_from_record(record)
        all_chunks.extend(chunks)
        logger.debug(
            f"Record [{i+1}/{len(records)}]: "
            f"{len(chunks)} chunks created."
        )
    logger.info(
        f"chunk_from_records: "
        f"{len(all_chunks)} total chunks "
        f"from {len(records)} records."
    )
    return all_chunks


def get_chunk_stats(chunks: list) -> dict:
    """
    Returns statistics about a list of chunks.

    Args:
        chunks : List of LegalChunk objects

    Returns:
        Dictionary with stats
    """
    if not chunks:
        return {}

    token_counts = [c.token_count for c in chunks]
    char_counts  = [c.char_count  for c in chunks]
    languages    = [c.metadata.get("language", "unknown") for c in chunks]
    chunk_types  = [c.metadata.get("chunk_type", "unknown") for c in chunks]

    return {
        "total_chunks":     len(chunks),
        "avg_tokens":       round(sum(token_counts) / len(token_counts), 1),
        "max_tokens":       max(token_counts),
        "min_tokens":       min(token_counts),
        "total_tokens":     sum(token_counts),
        "avg_chars":        round(sum(char_counts) / len(char_counts), 1),
        "languages":        {l: languages.count(l) for l in set(languages)},
        "chunk_types":      {t: chunk_types.count(t) for t in set(chunk_types)},
    }


# ── Quick test ───────────────────────────────────────────────
if __name__ == "__main__":
    import json
    from pathlib import Path

    print("── Document Chunker Test ──\n")

    # Test 1 — chunk from JSON records
    ipc_path = Path("data/processed/translated_ipc_kn.json")
    if ipc_path.exists():
        with open(ipc_path, encoding="utf-8") as f:
            records = json.load(f)

        chunks = chunk_from_records(records)
        stats  = get_chunk_stats(chunks)

        print(f"Source     : {ipc_path}")
        print(f"Records    : {len(records)}")
        print(f"Chunks     : {stats['total_chunks']}")
        print(f"Avg tokens : {stats['avg_tokens']}")
        print(f"Languages  : {stats['languages']}")
        print(f"Types      : {stats['chunk_types']}")
        print()

        # Show first chunk
        if chunks:
            print("── First Chunk ──")
            print(f"ID       : {chunks[0].chunk_id}")
            print(f"Text     : {chunks[0].text[:150]}...")
            print(f"Metadata : {chunks[0].metadata}")
            print()

    else:
        # Test with sample text
        print("No JSON files found. Testing with sample text.\n")
        sample = """
        Section 302. Punishment for murder.
        Whoever commits murder shall be punished with death,
        or imprisonment for life, and shall also be liable to fine.

        Section 379. Punishment for theft.
        Whoever commits theft shall be punished with imprisonment
        of either description for a term which may extend to
        three years, or with fine, or with both.
        """

        chunks = smart_chunk(sample, law_name="IPC", source="test")
        stats  = get_chunk_stats(chunks)

        print(f"Chunks     : {stats['total_chunks']}")
        print(f"Avg tokens : {stats['avg_tokens']}")
        print(f"Types      : {stats['chunk_types']}")
        print()

        for chunk in chunks:
            print(f"── Chunk: §{chunk.metadata.get('section_number')} ──")
            print(f"Text : {chunk.text[:100]}...")
            print(f"Meta : {chunk.metadata}")
            print()