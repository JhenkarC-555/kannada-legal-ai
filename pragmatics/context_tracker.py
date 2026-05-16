# pragmatics/context_tracker.py
# Tracks conversation history across multiple turns.
#
# Why is this needed?
#   Turn 1 — User: "IPC ಸೆಕ್ಷನ್ 302 ಏನು?"
#   Turn 2 — User: "ಅದಕ್ಕೆ ಶಿಕ್ಷೆ ಏನು?"
#
#   "ಅದಕ್ಕೆ" means "for that" — referring to Section 302.
#   Without context tracking the model cannot understand
#   what "that" refers to.
#
#   This module:
#     - Stores conversation turns (user + assistant)
#     - Resolves vague references ("ಅದು", "that", "it")
#     - Tracks current legal topic being discussed
#     - Provides conversation history for LLM prompts

from collections import deque
from dataclasses import dataclass, field
from loguru import logger


# ── Turn dataclass ────────────────────────────────────────────
@dataclass
class Turn:
    """
    Represents a single conversation turn.

    Attributes:
        role     : 'user' or 'assistant'
        content  : Text content of the turn
        intent   : Detected intent for this turn
        sections : Legal sections mentioned in this turn
        laws     : Laws mentioned in this turn
        timestamp: When this turn was added
    """
    role:     str
    content:  str
    intent:   str  = "general"
    sections: list = field(default_factory=list)
    laws:     list = field(default_factory=list)


# ── Vague reference terms ─────────────────────────────────────
# These terms refer to something said in a previous turn.
# When detected we resolve them using conversation history.

VAGUE_KANNADA_TERMS = [
    "ಅದಕ್ಕೆ",      # for that
    "ಅದು",          # that
    "ಅದರ",          # of that
    "ಅದನ್ನು",       # that (object)
    "ಅವರಿಗೆ",       # to them
    "ಅವರು",         # they/them
    "ಇದಕ್ಕೆ",       # for this
    "ಇದು",          # this
    "ಅಂಥ",          # such
    "ಅದೇ",          # same/that same
    "ಆ ಕಾನೂನು",    # that law
    "ಆ ಸೆಕ್ಷನ್",   # that section
    "ಮೇಲಿನ",        # above mentioned
]

VAGUE_ENGLISH_TERMS = [
    "that",
    "it",
    "this",
    "the same",
    "the above",
    "aforementioned",
    "such",
    "those",
    "them",
]


# ── Context Tracker class ─────────────────────────────────────
class ContextTracker:
    """
    Tracks conversation history for multi-turn legal queries.

    Attributes:
        max_turns     : Maximum number of turns to keep in memory
        history       : Deque of Turn objects
        current_topic : Currently discussed legal topic
        current_sections : Sections discussed so far
        current_laws  : Laws discussed so far
        session_id    : Optional session identifier
    """

    def __init__(
        self,
        max_turns:  int = 5,
        session_id: str = "",
    ):
        """
        Initialize the ContextTracker.

        Args:
            max_turns  : Max turns to keep (default 5)
            session_id : Optional session ID for logging
        """
        # max_turns * 2 because each turn = user + assistant
        self.history: deque = deque(maxlen=max_turns * 2)
        self.max_turns      = max_turns
        self.session_id     = session_id
        self.current_topic  = ""
        self.current_sections: list = []
        self.current_laws:     list = []

        logger.info(
            f"ContextTracker initialized. "
            f"max_turns={max_turns} "
            f"session={session_id or 'default'}"
        )

    # ── Add turns ─────────────────────────────────────────────
    def add_user_turn(
        self,
        content:  str,
        intent:   str  = "general",
        sections: list = None,
        laws:     list = None,
    ) -> None:
        """
        Add a user turn to conversation history.

        Args:
            content  : User query text
            intent   : Detected intent
            sections : Legal sections found in query
            laws     : Laws found in query

        Example:
            >>> tracker.add_user_turn(
            ...     content="IPC ಸೆಕ್ಷನ್ 302 ಏನು?",
            ...     intent="section_lookup",
            ...     sections=["302"],
            ...     laws=["IPC"]
            ... )
        """
        sections = sections or []
        laws     = laws     or []

        turn = Turn(
            role="user",
            content=content,
            intent=intent,
            sections=sections,
            laws=laws,
        )
        self.history.append(turn)

        # Update current topic tracking
        if intent and intent != "general":
            self.current_topic = intent
        if sections:
            for s in sections:
                if s not in self.current_sections:
                    self.current_sections.append(s)
        if laws:
            for l in laws:
                if l not in self.current_laws:
                    self.current_laws.append(l)

        logger.debug(
            f"User turn added. "
            f"Intent={intent} "
            f"Sections={sections}"
        )

    def add_assistant_turn(
        self,
        content:  str,
        sections: list = None,
        laws:     list = None,
    ) -> None:
        """
        Add an assistant response turn to history.

        Args:
            content  : Assistant response text
            sections : Sections mentioned in response
            laws     : Laws mentioned in response

        Example:
            >>> tracker.add_assistant_turn(
            ...     content="ಸೆಕ್ಷನ್ 302 ಕೊಲೆಗೆ ಶಿಕ್ಷೆ..."
            ... )
        """
        sections = sections or []
        laws     = laws     or []

        turn = Turn(
            role="assistant",
            content=content,
            sections=sections,
            laws=laws,
        )
        self.history.append(turn)
        logger.debug("Assistant turn added.")

    # ── Reference resolution ──────────────────────────────────
    def resolve_reference(self, query: str) -> str:
        """
        Resolve vague references in a query using history.
        If query contains "ಅದಕ್ಕೆ" (for that), "it" etc.
        append previous context to make it clear.

        Args:
            query : Current user query

        Returns:
            Resolved query with added context

        Examples:
            >>> tracker.add_user_turn("IPC ಸೆಕ್ಷನ್ 302 ಏನು?")
            >>> tracker.resolve_reference("ಅದಕ್ಕೆ ಶಿಕ್ಷೆ ಏನು?")
            'ಅದಕ್ಕೆ ಶಿಕ್ಷೆ ಏನು? (ಸಂದರ್ಭ: IPC ಸೆಕ್ಷನ್ 302)'

            >>> tracker.resolve_reference("IPC ಸೆಕ್ಷನ್ 420 ಏನು?")
            'IPC ಸೆಕ್ಷನ್ 420 ಏನು?'  # No vague reference
        """
        if not query:
            return query

        # Check for vague terms
        has_vague = any(
            term in query
            for term in VAGUE_KANNADA_TERMS + VAGUE_ENGLISH_TERMS
        )

        if not has_vague:
            return query

        # Build context from recent history
        context_parts = []

        # Add current sections being discussed
        if self.current_sections:
            law = self.current_laws[0] if self.current_laws else "IPC"
            sections_str = ", ".join(
                f"{law} ಸೆಕ್ಷನ್ {s}"
                for s in self.current_sections[-2:]
            )
            context_parts.append(sections_str)

        # Add last user query topic
        prev_user = self._get_last_user_turn()
        if prev_user and prev_user.content != query:
            context_parts.append(prev_user.content[:60])

        if not context_parts:
            return query

        context_str   = " | ".join(context_parts)
        resolved      = f"{query} (ಸಂದರ್ಭ: {context_str})"

        logger.info(
            f"Reference resolved:\n"
            f"  Original : '{query}'\n"
            f"  Resolved : '{resolved}'"
        )
        return resolved

    # ── Context window for LLM ────────────────────────────────
    def get_context_window(
        self,
        max_turns: int = None,
    ) -> list:
        """
        Get conversation history as a list of dicts.
        Used to pass conversation history to the LLM.

        Args:
            max_turns : Max recent turns to return

        Returns:
            List of {"role": ..., "content": ...} dicts

        Example:
            >>> history = tracker.get_context_window(max_turns=3)
            >>> history
            [
                {"role": "user",      "content": "IPC 302 ಏನು?"},
                {"role": "assistant", "content": "ಸೆಕ್ಷನ್ 302..."},
                {"role": "user",      "content": "ಅದಕ್ಕೆ ಶಿಕ್ಷೆ?"}
            ]
        """
        turns = list(self.history)
        if max_turns:
            turns = turns[-(max_turns * 2):]

        return [
            {"role": t.role, "content": t.content}
            for t in turns
        ]

    def get_context_as_string(self, max_turns: int = 3) -> str:
        """
        Get conversation history as formatted string.
        Used for injecting history into LLM prompts.

        Args:
            max_turns : Max recent turns to include

        Returns:
            Formatted conversation history string

        Example:
            >>> print(tracker.get_context_as_string())
            ಬಳಕೆದಾರ: IPC ಸೆಕ್ಷನ್ 302 ಏನು?
            ಸಹಾಯಕ: ಸೆಕ್ಷನ್ 302 ಕೊಲೆಗೆ ಶಿಕ್ಷೆ ವಿಧಿಸುತ್ತದೆ...
            ಬಳಕೆದಾರ: ಅದಕ್ಕೆ ಎಷ್ಟು ವರ್ಷ?
        """
        turns = list(self.history)
        if max_turns:
            turns = turns[-(max_turns * 2):]

        if not turns:
            return ""

        lines = []
        for turn in turns:
            if turn.role == "user":
                lines.append(f"ಬಳಕೆದಾರ: {turn.content}")
            else:
                # Truncate long assistant responses
                content = turn.content
                if len(content) > 200:
                    content = content[:200] + "..."
                lines.append(f"ಸಹಾಯಕ: {content}")

        return "\n".join(lines)

    # ── Topic tracking ────────────────────────────────────────
    def get_current_topic(self) -> dict:
        """
        Get the current legal topic being discussed.

        Returns:
            Dict with topic, sections and laws

        Example:
            >>> tracker.get_current_topic()
            {
                'topic'   : 'section_lookup',
                'sections': ['302'],
                'laws'    : ['IPC']
            }
        """
        return {
            "topic":    self.current_topic,
            "sections": self.current_sections,
            "laws":     self.current_laws,
        }

    def is_follow_up(self, query: str) -> bool:
        """
        Check if a query is a follow-up to previous conversation.

        Args:
            query : Current user query

        Returns:
            True if query appears to be a follow-up

        Example:
            >>> tracker.is_follow_up("ಅದಕ್ಕೆ ಶಿಕ್ಷೆ ಏನು?")
            True
            >>> tracker.is_follow_up("RTI ಅರ್ಜಿ ಹೇಗೆ ಹಾಕಬೇಕು?")
            False
        """
        if not self.history:
            return False

        has_vague = any(
            term in query
            for term in VAGUE_KANNADA_TERMS + VAGUE_ENGLISH_TERMS
        )
        is_short  = len(query.split()) <= 5

        return has_vague or (is_short and bool(self.history))

    # ── Utility methods ───────────────────────────────────────
    def _get_last_user_turn(self) -> Turn:
        """Get the most recent user turn from history."""
        for turn in reversed(list(self.history)):
            if turn.role == "user":
                return turn
        return None

    def _get_last_assistant_turn(self) -> Turn:
        """Get the most recent assistant turn from history."""
        for turn in reversed(list(self.history)):
            if turn.role == "assistant":
                return turn
        return None

    def get_turn_count(self) -> int:
        """Returns total number of turns in history."""
        return len(self.history)

    def get_user_turn_count(self) -> int:
        """Returns number of user turns in history."""
        return sum(1 for t in self.history if t.role == "user")

    def reset(self) -> None:
        """
        Clear all conversation history.
        Use when starting a new conversation session.

        Example:
            >>> tracker.reset()
        """
        self.history.clear()
        self.current_topic    = ""
        self.current_sections = []
        self.current_laws     = []
        logger.info("ContextTracker reset.")

    def get_summary(self) -> str:
        """
        Returns a summary of the current context state.

        Returns:
            Formatted summary string
        """
        lines = [
            f"Session ID      : {self.session_id or 'default'}",
            f"Total Turns     : {self.get_turn_count()}",
            f"User Turns      : {self.get_user_turn_count()}",
            f"Current Topic   : {self.current_topic or 'None'}",
            f"Current Sections: {self.current_sections}",
            f"Current Laws    : {self.current_laws}",
            f"Max Turns       : {self.max_turns}",
        ]
        return "\n".join(lines)


# ── Module level convenience functions ───────────────────────
# A shared tracker for simple single-session use.
_default_tracker: ContextTracker = None


def get_tracker(session_id: str = "") -> ContextTracker:
    """
    Get or create the default ContextTracker.

    Args:
        session_id : Optional session identifier

    Returns:
        ContextTracker instance
    """
    global _default_tracker
    if _default_tracker is None:
        _default_tracker = ContextTracker(
            max_turns=5,
            session_id=session_id,
        )
    return _default_tracker


def reset_tracker() -> None:
    """Reset the default tracker."""
    global _default_tracker
    if _default_tracker:
        _default_tracker.reset()


# ── Quick test ───────────────────────────────────────────────
if __name__ == "__main__":

    print("══════════════════════════════════════════")
    print("   Context Tracker Test")
    print("══════════════════════════════════════════\n")

    # Create tracker for this session
    tracker = ContextTracker(max_turns=5, session_id="test_001")

    # ── Simulate a multi-turn conversation ───────────────────
    conversation = [
        {
            "role":     "user",
            "content":  "IPC ಸೆಕ್ಷನ್ 302 ಏನು?",
            "intent":   "section_lookup",
            "sections": ["302"],
            "laws":     ["IPC"],
        },
        {
            "role":    "assistant",
            "content": "IPC ಸೆಕ್ಷನ್ 302 ಕೊಲೆಗೆ ಶಿಕ್ಷೆ ವಿಧಿಸುತ್ತದೆ. "
                       "ಮರಣದಂಡನೆ ಅಥವಾ ಜೀವಾವಧಿ ಕಾರಾಗೃಹ ಶಿಕ್ಷೆ.",
        },
        {
            "role":     "user",
            "content":  "ಅದಕ್ಕೆ ಎಷ್ಟು ವರ್ಷ ಜೈಲು?",
            "intent":   "penalty_query",
            "sections": [],
            "laws":     [],
        },
        {
            "role":    "assistant",
            "content": "ಕೊಲೆ ಪ್ರಕರಣದಲ್ಲಿ ಜೀವಾವಧಿ ಅಥವಾ ಮರಣದಂಡನೆ.",
        },
        {
            "role":     "user",
            "content":  "ಅದೇ ಕಾನೂನಿನ ಅಡಿಯಲ್ಲಿ ಜಾಮೀನು ಸಿಗುತ್ತದೆಯೇ?",
            "intent":   "procedure_query",
            "sections": [],
            "laws":     [],
        },
    ]

    print("── Simulating Conversation ──\n")
    for turn in conversation:
        if turn["role"] == "user":
            tracker.add_user_turn(
                content=turn["content"],
                intent=turn.get("intent", "general"),
                sections=turn.get("sections", []),
                laws=turn.get("laws", []),
            )
            print(f"👤 User : {turn['content']}")

            # Test reference resolution
            resolved = tracker.resolve_reference(turn["content"])
            if resolved != turn["content"]:
                print(f"   🔗 Resolved: {resolved}")

            # Test follow-up detection
            is_fu = tracker.is_follow_up(turn["content"])
            print(f"   Follow-up: {is_fu}")

        else:
            tracker.add_assistant_turn(turn["content"])
            print(f"🤖 Bot  : {turn['content'][:80]}...")

        print()

    # ── Show tracker state ────────────────────────────────────
    print("── Tracker Summary ──\n")
    print(tracker.get_summary())

    print("\n── Context Window ──\n")
    print(tracker.get_context_as_string(max_turns=3))

    print("\n── Current Topic ──\n")
    topic = tracker.get_current_topic()
    print(f"Topic    : {topic['topic']}")
    print(f"Sections : {topic['sections']}")
    print(f"Laws     : {topic['laws']}")

    # ── Test reset ────────────────────────────────────────────
    print("\n── After Reset ──\n")
    tracker.reset()
    print(tracker.get_summary())