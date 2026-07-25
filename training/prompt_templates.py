LEGAL_QA_TEMPLATE = """### ಸೂಚನೆ:
ನೀವು ಒಬ್ಬ ಕನ್ನಡ ಕಾನೂನು ತಜ್ಞ. ಕೆಳಗಿನ ಪ್ರಶ್ನೆಗೆ ನಿಖರ ಮತ್ತು ಸ್ಪಷ್ಟ ಉತ್ತರ ನೀಡಿ.
ಉತ್ತರದಲ್ಲಿ ಸಂಬಂಧಿತ ವಿಭಾಗ ಸಂಖ್ಯೆ ಮತ್ತು ಕಾನೂನಿನ ಹೆಸರು ಉಲ್ಲೇಖಿಸಿ.

### ಸಂದರ್ಭ:
{context}

### ಪ್ರಶ್ನೆ:
{question}

### ಉತ್ತರ:
{answer}"""

SECTION_EXPLAIN_TEMPLATE = """### ಸೂಚನೆ:
ಈ ಕಾನೂನು ವಿಭಾಗವನ್ನು ಸರಳ ಕನ್ನಡದಲ್ಲಿ ವಿವರಿಸಿ.

### ವಿಭಾಗ:
{section_text}

### ಸರಳ ವ್ಯಾಖ್ಯಾನ:
{explanation}"""

RIGHTS_TEMPLATE = """### ಸೂಚನೆ:
ನೀವು ಒಬ್ಬ ಕನ್ನಡ ಕಾನೂನು ಸಹಾಯಕ. ವ್ಯಕ್ತಿಯ ಕಾನೂನು ಹಕ್ಕುಗಳನ್ನು
ಸರಳ ಕನ್ನಡದಲ್ಲಿ ವಿವರಿಸಿ. ಸಂಬಂಧಿತ ವಿಭಾಗಗಳನ್ನು ಉಲ್ಲೇಖಿಸಿ.

### ಸಂದರ್ಭ:
{context}

### ಪ್ರಶ್ನೆ:
{question}

### ಉತ್ತರ:
{answer}"""

PROCEDURE_TEMPLATE = """### ಸೂಚನೆ:
ನೀವು ಒಬ್ಬ ಕನ್ನಡ ಕಾನೂನು ಮಾರ್ಗದರ್ಶಕ. ಹಂತ-ಹಂತವಾಗಿ
ಕಾನೂನು ಪ್ರಕ್ರಿಯೆ ವಿವರಿಸಿ.

### ಸಂದರ್ಭ:
{context}

### ಪ್ರಶ್ನೆ:
{question}

### ಉತ್ತರ:
{answer}"""

INTENT_TEMPLATES = {
    "section_lookup":  LEGAL_QA_TEMPLATE,
    "rights_query":    RIGHTS_TEMPLATE,
    "penalty_query":   LEGAL_QA_TEMPLATE,
    "procedure_query": PROCEDURE_TEMPLATE,
    "document_help":   LEGAL_QA_TEMPLATE,
    "general":         LEGAL_QA_TEMPLATE,
}

def format_qa(question: str, context: str, answer: str, intent: str = "general") -> str:
    """Formats question, context, and answer into prompt template based on intent."""
    template = INTENT_TEMPLATES.get(intent, LEGAL_QA_TEMPLATE)
    return template.format(
        context=context,
        question=question,
        answer=answer,
    )

def format_section(section_text: str, explanation: str) -> str:
    """Formats section explanation prompt."""
    return SECTION_EXPLAIN_TEMPLATE.format(
        section_text=section_text,
        explanation=explanation,
    )

def extract_answer_from_output(generated_text: str) -> str:
    """Extracts final Kannada answer from generated model text."""
    marker = "### ಉತ್ತರ:"
    if marker in generated_text:
        return generated_text.split(marker)[-1].strip()
    return generated_text.strip()