# evaluation/auto_metrics.py

import re
from loguru import logger

try:
    import evaluate
    rouge = evaluate.load("rouge")
    bleu  = evaluate.load("bleu")
    EVALUATE_AVAILABLE = True
except Exception:
    EVALUATE_AVAILABLE = False

def compute_rouge(predictions: list[str], references: list[str]) -> dict:
    """Computes ROUGE-1, ROUGE-2, ROUGE-L scores."""
    if not EVALUATE_AVAILABLE:
        return {"rouge1": 0.0, "rouge2": 0.0, "rougeL": 0.0}
    result = rouge.compute(predictions=predictions, references=references)
    return {k: round(v, 4) for k, v in result.items()}

def compute_bleu(predictions: list[str], references: list[str]) -> dict:
    """Computes BLEU score against reference text lists."""
    if not EVALUATE_AVAILABLE:
        return {"bleu": 0.0}
    # Hugging Face evaluate library expects references as list of lists
    formatted_refs = [[r] for r in references]
    result = bleu.compute(predictions=predictions, references=formatted_refs)
    return {"bleu": round(result["bleu"], 4)}

def section_exact_match(prediction: str, reference: str) -> bool:
    """Checks if predicted text cites the same legal section numbers as reference."""
    pred_secs = set(re.findall(r"\d+[A-Z]?", prediction))
    ref_secs  = set(re.findall(r"\d+[A-Z]?", reference))
    return bool(pred_secs & ref_secs) if ref_secs else True

def recall_at_k(retrieved: list[str], relevant: list[str], k: int = 5) -> float:
    """Calculates Recall@K for context retrieval."""
    top_k = retrieved[:k]
    hits  = sum(1 for doc in top_k if doc in relevant)
    return round(hits / max(len(relevant), 1), 4)

def run_all(predictions: list[str], references: list[str]) -> dict:
    """Runs all evaluation metrics on predictions vs references."""
    if not predictions or not references:
        return {}
        
    logger.info(f"Running metrics on {len(predictions)} test samples...")
    rouge_scores = compute_rouge(predictions, references)
    bleu_scores  = compute_bleu(predictions, references)
    sem_scores   = [
        section_exact_match(p, r)
        for p, r in zip(predictions, references)
    ]
    
    return {
        **rouge_scores,
        **bleu_scores,
        "section_exact_match": round(sum(sem_scores) / len(sem_scores), 4),
        "num_samples": len(predictions),
    }

if __name__ == "__main__":
    preds = ["ಸೆಕ್ಷನ್ 302 ಕೊಲೆಗೆ ಶಿಕ್ಷೆ"]
    refs  = ["IPC ಸೆಕ್ಷನ್ 302 ಕೊಲೆಗೆ ಮರಣದಂಡನೆ"]
    print(run_all(preds, refs))