# backend/models/response_models.py
# Pydantic models for outgoing API responses.
# FastAPI uses these to automatically serialize
# and validate response data.
#
# These models define exactly what the frontend receives.

from pydantic import BaseModel, Field
from typing import Optional
from loguru import logger


# ── Legal Source model ────────────────────────────────────────
class LegalSource(BaseModel):
    """
    Represents a single retrieved legal document chunk.
    Shown to the user as a citation.

    Fields:
        text           : The actual legal text content
        law_name       : Name of the law (IPC, CrPC etc.)
        section_number : Section number if available
        language       : Language of the chunk (kn or en)
        score          : Relevance score 0.0 to 1.0
        chunk_type     : Type of chunk (section, paragraph etc.)
        source         : Source URL or document name
    """

    text: str = Field(
        description="The retrieved legal text content"
    )

    law_name: str = Field(
        default="Unknown",
        description="Name of the law"
    )

    section_number: str = Field(
        default="",
        description="Section number if available"
    )

    language: str = Field(
        default="en",
        description="Language of the chunk"
    )

    score: float = Field(
        default=0.0,
        description="Relevance score 0.0 to 1.0"
    )

    chunk_type: str = Field(
        default="section",
        description="Type of chunk"
    )

    source: str = Field(
        default="",
        description="Source document or URL"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "text":           "ಯಾರಾದರೂ ಕೊಲೆ ಮಾಡಿದರೆ...",
                "law_name":       "IPC",
                "section_number": "302",
                "language":       "kn",
                "score":          0.94,
                "chunk_type":     "section",
                "source":         "indiacode.nic.in",
            }
        }


# ── Code switch info model ────────────────────────────────────
class CodeSwitchInfo(BaseModel):
    """
    Information about language mixing in the query.

    Fields:
        has_kannada      : True if Kannada detected
        has_english      : True if English detected
        is_mixed         : True if both languages present
        dominant_language: Main language of the query
        kannada_ratio    : Fraction of Kannada characters
        english_ratio    : Fraction of English characters
    """

    has_kannada:       bool  = False
    has_english:       bool  = False
    is_mixed:          bool  = False
    dominant_language: str   = "unknown"
    kannada_ratio:     float = 0.0
    english_ratio:     float = 0.0


# ── Main Query Response ───────────────────────────────────────
class QueryResponse(BaseModel):
    """
    Response model for POST /api/query

    Fields:
        success          : True if query was processed
        query            : Original user query
        processed_query  : NLP processed version of query
        intent           : Detected intent
        intent_name_kn   : Kannada display name for intent
        confidence       : Intent classification confidence
        answer           : Generated answer text
        sources          : List of retrieved legal sources
        section_numbers  : Section numbers found in query
        law_names        : Law names found in query
        implicature      : Implied legal context if detected
        was_transliterated: True if Roman->Kannada conversion done
        was_normalized   : True if dialect normalization done
        dominant_language: Detected language of query
        code_switch      : Code switching analysis
        disclaimer       : Legal disclaimer in Kannada
        session_id       : Session ID for conversation tracking
        error            : Error message if success is False

    Example response:
        {
            "success": true,
            "query": "IPC ಸೆಕ್ಷನ್ 302 ಏನು?",
            "intent": "section_lookup",
            "answer": "ಸೆಕ್ಷನ್ 302 ಕೊಲೆಗೆ ಶಿಕ್ಷೆ...",
            "sources": [...],
            ...
        }
    """

    # ── Status ───────────────────────────────────────────────
    success: bool = Field(
        default=True,
        description="True if query processed successfully"
    )

    error: Optional[str] = Field(
        default=None,
        description="Error message if success is False"
    )

    # ── Query info ───────────────────────────────────────────
    query: str = Field(
        description="Original user query"
    )

    processed_query: str = Field(
        default="",
        description="NLP processed version of query"
    )

    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for conversation tracking"
    )

    # ── Intent ───────────────────────────────────────────────
    intent: str = Field(
        default="general",
        description="Detected intent of the query"
    )

    intent_name_kn: str = Field(
        default="ಸಾಮಾನ್ಯ ಸಹಾಯ",
        description="Kannada display name for the intent"
    )

    confidence: float = Field(
        default=0.0,
        description="Intent classification confidence 0.0 to 1.0"
    )

    # ── Answer ───────────────────────────────────────────────
    answer: str = Field(
        default="",
        description="Generated answer text in Kannada"
    )

    prompt: Optional[str] = Field(
        default=None,
        description="Full LLM prompt (shown in debug mode only)"
    )

    # ── Sources ──────────────────────────────────────────────
    sources: list[LegalSource] = Field(
        default=[],
        description="Retrieved legal document sources"
    )

    # ── Legal metadata ───────────────────────────────────────
    section_numbers: list[str] = Field(
        default=[],
        description="Section numbers found in the query"
    )

    law_names: list[str] = Field(
        default=[],
        description="Law names found in the query"
    )

    implicature_detected: bool = Field(
        default=False,
        description="True if implied legal meaning was detected"
    )

    implicature_offense: Optional[str] = Field(
        default=None,
        description="Detected implied legal offense"
    )

    implicature_hint: Optional[str] = Field(
        default=None,
        description="Legal context hint from implicature analysis"
    )

    # ── Language info ────────────────────────────────────────
    dominant_language: str = Field(
        default="kn",
        description="Dominant language of the query"
    )

    was_transliterated: bool = Field(
        default=False,
        description="True if Roman script was converted to Kannada"
    )

    was_normalized: bool = Field(
        default=False,
        description="True if dialect normalization was applied"
    )

    code_switch: Optional[CodeSwitchInfo] = Field(
        default=None,
        description="Code switching analysis results"
    )

    # ── Disclaimer ───────────────────────────────────────────
    disclaimer: str = Field(
        default=(
            "⚠️ ಇದು ಕಾನೂನು ಸಲಹೆ ಅಲ್ಲ. "
            "ನಿಮ್ಮ ಪ್ರಕರಣಕ್ಕೆ ವಕೀಲರನ್ನು ಸಂಪರ್ಕಿಸಿ."
        ),
        description="Legal disclaimer in Kannada"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success":             True,
                "query":               "IPC ಸೆಕ್ಷನ್ 302 ಏನು?",
                "processed_query":     "IPC ವಿಭಾಗ 302 ಏನು?",
                "intent":              "section_lookup",
                "intent_name_kn":      "ವಿಭಾಗ ಮಾಹಿತಿ",
                "confidence":          0.9,
                "answer":              "IPC ಸೆಕ್ಷನ್ 302 ಕೊಲೆಗೆ ಶಿಕ್ಷೆ...",
                "sources":             [],
                "section_numbers":     ["302"],
                "law_names":           ["IPC"],
                "implicature_detected": False,
                "dominant_language":   "kn",
                "was_transliterated":  False,
                "was_normalized":      True,
                "disclaimer":          "⚠️ ಇದು ಕಾನೂನು ಸಲಹೆ ಅಲ್ಲ...",
            }
        }


# ── Health Response ───────────────────────────────────────────
class HealthResponse(BaseModel):
    """
    Response model for GET /api/health

    Fields:
        status         : 'ok' or 'error'
        language       : Supported language
        domain         : Application domain
        version        : API version
        vector_store   : Vector store status
        nlp_pipeline   : NLP pipeline status
        embedding_model: Embedding model status
        total_documents: Total docs in vector store
    """

    status: str = Field(
        default="ok",
        description="Service status"
    )

    language: str = Field(
        default="kn",
        description="Primary supported language"
    )

    domain: str = Field(
        default="legal",
        description="Application domain"
    )

    version: str = Field(
        default="0.1.0",
        description="API version"
    )

    vector_store: str = Field(
        default="unknown",
        description="Vector store status"
    )

    nlp_pipeline: str = Field(
        default="unknown",
        description="NLP pipeline status"
    )

    embedding_model: str = Field(
        default="unknown",
        description="Embedding model status"
    )

    total_documents: int = Field(
        default=0,
        description="Total documents in vector store"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status":          "ok",
                "language":        "kn",
                "domain":          "legal",
                "version":         "0.1.0",
                "vector_store":    "ready",
                "nlp_pipeline":    "ready",
                "embedding_model": "ready",
                "total_documents": 84,
            }
        }


# ── Error Response ────────────────────────────────────────────
class ErrorResponse(BaseModel):
    """
    Standard error response model.
    Returned when something goes wrong.

    Fields:
        success : Always False for errors
        error   : Error type
        message : Human readable error message in Kannada
        detail  : Technical detail for debugging
    """

    success: bool = Field(
        default=False,
        description="Always False for errors"
    )

    error: str = Field(
        description="Error type"
    )

    message: str = Field(
        description="Human readable error message"
    )

    detail: Optional[str] = Field(
        default=None,
        description="Technical detail for debugging"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error":   "validation_error",
                "message": "ಪ್ರಶ್ನೆ ಖಾಲಿ ಇರಬಾರದು",
                "detail":  "question field is required",
            }
        }


# ── Helper function ───────────────────────────────────────────
def build_query_response(
    query:        str,
    rag_result:   dict,
    intent_result: object,
    impl_result:  object,
    session_id:   str  = None,
    debug:        bool = False,
) -> QueryResponse:
    """
    Build a QueryResponse from pipeline results.
    Converts raw pipeline output into the API response format.

    Args:
        query         : Original user query
        rag_result    : Result dict from rag_pipeline.answer()
        intent_result : IntentResult from intent_classifier
        impl_result   : ImplicatureResult from implicature_handler
        session_id    : Optional session ID
        debug         : If True include prompt in response

    Returns:
        QueryResponse object ready to return to frontend
    """
    from pragmatics.prompt_router import get_intent_display_name

    # ── Build sources list ───────────────────────────────────
    sources = []
    for ctx in rag_result.get("contexts", []):
        meta = ctx.get("metadata", {})
        sources.append(LegalSource(
            text=ctx.get("text", ""),
            law_name=meta.get("law_name", "Unknown"),
            section_number=meta.get("section_number", ""),
            language=meta.get("language", "en"),
            score=ctx.get(
                "hybrid_score",
                ctx.get("score", 0.0)
            ),
            chunk_type=meta.get("chunk_type", "section"),
            source=meta.get("source", ""),
        ))

    # ── Build code switch info ───────────────────────────────
    cs = rag_result.get("code_switch")
    code_switch_info = None
    if cs:
        code_switch_info = CodeSwitchInfo(
            has_kannada=cs.has_kannada,
            has_english=cs.has_english,
            is_mixed=cs.is_mixed,
            dominant_language=cs.dominant_language,
            kannada_ratio=cs.kannada_ratio,
            english_ratio=cs.english_ratio,
        )

    # ── Build the answer placeholder ─────────────────────────
    # Until the fine-tuned model is connected
    # we return the top retrieved context as the answer
    answer = ""
    if sources:
        top_source = sources[0]
        answer = (
            f"**{top_source.law_name} "
            f"ವಿಭಾಗ {top_source.section_number}**\n\n"
            f"{top_source.text}"
        ) if top_source.section_number else top_source.text
    else:
        answer = (
            "ಕ್ಷಮಿಸಿ, ಈ ಪ್ರಶ್ನೆಗೆ ಸಂಬಂಧಿತ ಮಾಹಿತಿ "
            "ದೊರೆಯಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ."
        )

    # ── Get NLP processing flags ─────────────────────────────
    nlp = rag_result.get("nlp_result", {})

    return QueryResponse(
        success=True,
        query=query,
        processed_query=rag_result.get("processed_query", query),
        session_id=session_id,
        intent=intent_result.intent,
        intent_name_kn=get_intent_display_name(intent_result.intent),
        confidence=intent_result.confidence,
        answer=answer,
        prompt=rag_result.get("prompt") if debug else None,
        sources=sources[:5],
        section_numbers=rag_result.get("section_numbers", []),
        law_names=rag_result.get("law_names", []),
        implicature_detected=impl_result.detected,
        implicature_offense=(
            impl_result.likely_offense
            if impl_result.detected else None
        ),
        implicature_hint=(
            impl_result.resolved_hint
            if impl_result.detected else None
        ),
        dominant_language=rag_result.get("dominant_language", "kn"),
        was_transliterated=nlp.get("was_transliterated", False),
        was_normalized=nlp.get("was_normalized", False),
        code_switch=code_switch_info,
        disclaimer=(
            "⚠️ ಇದು ಕಾನೂನು ಸಲಹೆ ಅಲ್ಲ. "
            "ನಿಮ್ಮ ಪ್ರಕರಣಕ್ಕೆ ಅರ್ಹ ವಕೀಲರನ್ನು ಸಂಪರ್ಕಿಸಿ."
        ),
    )


# ── Quick test ───────────────────────────────────────────────
if __name__ == "__main__":

    print("── Response Models Test ──\n")

    # Test LegalSource
    source = LegalSource(
        text="ಯಾರಾದರೂ ಕೊಲೆ ಮಾಡಿದರೆ ಮರಣದಂಡನೆ ವಿಧಿಸಲಾಗುತ್ತದೆ.",
        law_name="IPC",
        section_number="302",
        language="kn",
        score=0.94,
    )
    print(f"LegalSource:")
    print(f"  Law     : {source.law_name}")
    print(f"  Section : {source.section_number}")
    print(f"  Score   : {source.score}")
    print(f"  Text    : {source.text[:50]}...")
    print()

    # Test QueryResponse
    response = QueryResponse(
        query="IPC ಸೆಕ್ಷನ್ 302 ಏನು?",
        processed_query="IPC ವಿಭಾಗ 302 ಏನು?",
        intent="section_lookup",
        intent_name_kn="ವಿಭಾಗ ಮಾಹಿತಿ",
        confidence=0.9,
        answer="ಸೆಕ್ಷನ್ 302 ಕೊಲೆಗೆ ಶಿಕ್ಷೆ ವಿಧಿಸುತ್ತದೆ.",
        sources=[source],
        section_numbers=["302"],
        law_names=["IPC"],
    )
    print(f"QueryResponse:")
    print(f"  Success  : {response.success}")
    print(f"  Intent   : {response.intent}")
    print(f"  Confidence: {response.confidence}")
    print(f"  Sources  : {len(response.sources)}")
    print(f"  Answer   : {response.answer[:60]}...")
    print()

    # Test HealthResponse
    health = HealthResponse(
        status="ok",
        vector_store="ready",
        nlp_pipeline="ready",
        embedding_model="ready",
        total_documents=84,
    )
    print(f"HealthResponse:")
    print(f"  Status   : {health.status}")
    print(f"  Docs     : {health.total_documents}")
    print(f"  VS       : {health.vector_store}")
    print()

    # Test ErrorResponse
    error = ErrorResponse(
        error="validation_error",
        message="ಪ್ರಶ್ನೆ ಖಾಲಿ ಇರಬಾರದು",
        detail="question field is required",
    )
    print(f"ErrorResponse:")
    print(f"  Success  : {error.success}")
    print(f"  Error    : {error.error}")
    print(f"  Message  : {error.message}")