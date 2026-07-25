# evaluation/hallucination_checker.py

import re
from loguru import logger

def extract_sections(text: str) -> set:
    """Extracts all legal section numbers mentioned in text (in Kannada or English)."""
    return set(re.findall(
        r"(?:Section|ವಿಭಾಗ|ಸೆಕ್ಷನ್)\s*(\d+[A-Z]?)",
        text, re.IGNORECASE,
    ))

def check(response: str, contexts: list[dict]) -> dict:
    """Checks if response contains section numbers not present in context docs."""
    response_sections = extract_sections(response)
    context_text      = " ".join(c.get("text", "") for c in contexts)
    context_sections  = extract_sections(context_text)
    
    # Sections cited in response that were nowhere in context documents
    hallucinated = response_sections - context_sections
    
    if hallucinated:
        logger.warning(f"Hallucinated sections detected: {hallucinated}")
        
    return {
        "response_sections":   list(response_sections),
        "context_sections":    list(context_sections),
        "hallucinated":        list(hallucinated),
        "is_hallucinated":     len(hallucinated) > 0,
        "hallucination_count": len(hallucinated),
    }

def batch_check(responses: list[str], contexts_list: list[list[dict]]) -> dict:
    """Runs hallucination check over a batch of test evaluations."""
    results      = []
    halluc_count = 0
    for response, contexts in zip(responses, contexts_list):
        result = check(response, contexts)
        results.append(result)
        if result["is_hallucinated"]:
            halluc_count += 1
            
    total = len(responses)
    return {
        "total":              total,
        "hallucinated_count": halluc_count,
        "clean_count":        total - halluc_count,
        "hallucination_rate": round(halluc_count / max(total, 1), 4),
        "clean_rate":         round((total - halluc_count) / max(total, 1), 4),
        "details":            results,
    }