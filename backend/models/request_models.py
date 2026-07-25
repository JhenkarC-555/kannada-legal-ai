# backend/models/request_models.py
# Pydantic models for incoming API requests.
# FastAPI uses these to automatically validate
# and parse request data.
#
# If a request is missing required fields or
# has wrong types FastAPI returns a clear error
# automatically — no manual validation needed.

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from loguru import logger


# ── Query Request ─────────────────────────────────────────────
class QueryRequest(BaseModel):
    """
    Request model for POST /api/query

    Fields:
        question   : The legal question in Kannada or English
        session_id : Optional session ID for conversation tracking
        language   : Language hint ('kn' or 'en')
        top_k      : Number of context chunks to retrieve
        alpha      : Hybrid search weight (0.0 to 1.0)
        dialect    : Optional Kannada dialect hint

    Example request body:
        {
            "question": "IPC ಸೆಕ್ಷನ್ 302 ಏನು?",
            "session_id": "user_123",
            "language": "kn",
            "top_k": 5
        }
    """

    question: str = Field(
        ...,
        min_length=2,
        max_length=500,
        description="Legal question in Kannada or English",
        examples=["IPC ಸೆಕ್ಷನ್ 302 ಏನು?"],
    )

    session_id: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Optional session ID for conversation tracking",
        examples=["user_123_session_456"],
    )

    language: Optional[str] = Field(
        default="kn",
        description="Language of the query — 'kn' or 'en'",
        examples=["kn"],
    )

    top_k: Optional[int] = Field(
        default=5,
        ge=1,       # greater than or equal to 1
        le=10,      # less than or equal to 10
        description="Number of context chunks to retrieve (1-10)",
        examples=[5],
    )

    alpha: Optional[float] = Field(
        default=0.6,
        ge=0.0,     # greater than or equal to 0.0
        le=1.0,     # less than or equal to 1.0
        description=(
            "Hybrid search weight. "
            "0.0 = pure BM25, 1.0 = pure dense, "
            "0.6 = recommended"
        ),
        examples=[0.6],
    )

    dialect: Optional[str] = Field(
        default=None,
        description=(
            "Optional Kannada dialect hint. "
            "One of: mysuru, dharwad, mangaluru, bengaluru"
        ),
        examples=["mysuru"],
    )

    # ── Validators ───────────────────────────────────────────
    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        """
        Validate and clean the question field.
        - Strip whitespace
        - Reject empty strings
        - Reject queries that are only numbers
        """
        cleaned = value.strip()

        if not cleaned:
            raise ValueError(
                "Question cannot be empty. "
                "ಪ್ರಶ್ನೆ ಖಾಲಿ ಇರಬಾರದು."
            )

        if cleaned.isdigit():
            raise ValueError(
                "Question cannot be only numbers. "
                "ಸಂಖ್ಯೆಗಳು ಮಾತ್ರ ಇರಬಾರದು."
            )

        logger.debug(f"Query validated: '{cleaned[:50]}'")
        return cleaned

    @field_validator("language")
    @classmethod
    def validate_language(cls, value: str) -> str:
        """Validate language code."""
        if value not in ["kn", "en"]:
            logger.warning(
                f"Unknown language '{value}'. "
                f"Defaulting to 'kn'."
            )
            return "kn"
        return value

    @field_validator("dialect")
    @classmethod
    def validate_dialect(cls, value: Optional[str]) -> Optional[str]:
        """Validate dialect name if provided."""
        if value is None:
            return None
        valid_dialects = ["mysuru", "dharwad", "mangaluru", "bengaluru"]
        if value.lower() not in valid_dialects:
            logger.warning(
                f"Unknown dialect '{value}'. "
                f"Ignoring dialect hint."
            )
            return None
        return value.lower()

    class Config:
        # Allow population by field name
        populate_by_name = True
        # Show example in docs
        json_schema_extra = {
            "example": {
                "question":   "IPC ಸೆಕ್ಷನ್ 302 ಅಡಿಯಲ್ಲಿ ಶಿಕ್ಷೆ ಏನು?",
                "session_id": "user_001",
                "language":   "kn",
                "top_k":      5,
                "alpha":      0.6,
                "dialect":    None,
            }
        }


# ── Feedback Request ──────────────────────────────────────────
class FeedbackRequest(BaseModel):
    """
    Request model for POST /api/feedback
    Allows users to rate the quality of answers.

    Fields:
        session_id  : Session that generated the answer
        question    : The original question asked
        rating      : Rating from 1 (bad) to 5 (excellent)
        comment     : Optional feedback comment
        was_helpful : Simple helpful yes/no flag
    """

    session_id: str = Field(
        ...,
        description="Session ID of the answered query",
        examples=["user_001"],
    )

    question: str = Field(
        ...,
        min_length=2,
        max_length=500,
        description="The original question",
        examples=["IPC ಸೆಕ್ಷನ್ 302 ಏನು?"],
    )

    rating: int = Field(
        ...,
        ge=1,
        le=5,
        description="Rating from 1 (poor) to 5 (excellent)",
        examples=[4],
    )

    comment: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Optional feedback comment in Kannada or English",
        examples=["ಉತ್ತರ ತುಂಬಾ ಉಪಯೋಗಕರವಾಗಿತ್ತು"],
    )

    was_helpful: Optional[bool] = Field(
        default=None,
        description="Was the answer helpful?",
        examples=[True],
    )

    class Config:
        json_schema_extra = {
            "example": {
                "session_id":  "user_001",
                "question":    "IPC ಸೆಕ್ಷನ್ 302 ಏನು?",
                "rating":      4,
                "comment":     "ಉತ್ತರ ಸ್ಪಷ್ಟವಾಗಿತ್ತು",
                "was_helpful": True,
            }
        }


# ── Quick test ───────────────────────────────────────────────
if __name__ == "__main__":

    print("── Request Models Test ──\n")

    # Test valid request
    valid_requests = [
        {
            "question":   "IPC ಸೆಕ್ಷನ್ 302 ಏನು?",
            "session_id": "user_001",
            "language":   "kn",
            "top_k":      5,
            "alpha":      0.6,
        },
        {
            "question":   "What is punishment for murder?",
            "language":   "en",
        },
        {
            "question":   "ಜಾಮೀನು ಹೇಗೆ ಪಡೆಯಬೇಕು?",
            "dialect":    "dharwad",
        },
    ]

    print("✅ Valid Requests:\n")
    for req_data in valid_requests:
        req = QueryRequest(**req_data)
        print(f"  Question : {req.question}")
        print(f"  Language : {req.language}")
        print(f"  Top K    : {req.top_k}")
        print(f"  Alpha    : {req.alpha}")
        print(f"  Dialect  : {req.dialect}")
        print()

    # Test invalid requests
    print("❌ Invalid Requests (should raise errors):\n")

    invalid_requests = [
        {"question": ""},           # Empty
        {"question": "12345"},      # Only numbers
        {"question": "A" * 501},    # Too long
    ]

    for req_data in invalid_requests:
        try:
            req = QueryRequest(**req_data)
            print(f"  ⚠️  Should have failed: {req_data}")
        except Exception as e:
            print(f"  ✅ Correctly rejected: {str(e)[:60]}")
        print()

    # Test feedback request
    print("── Feedback Request Test ──\n")
    feedback = FeedbackRequest(
        session_id="user_001",
        question="IPC ಸೆಕ್ಷನ್ 302 ಏನು?",
        rating=4,
        comment="ಉತ್ತರ ತುಂಬಾ ಉಪಯೋಗಕರವಾಗಿತ್ತು",
        was_helpful=True,
    )
    print(f"Session  : {feedback.session_id}")
    print(f"Rating   : {feedback.rating}/5")
    print(f"Helpful  : {feedback.was_helpful}")
    print(f"Comment  : {feedback.comment}")