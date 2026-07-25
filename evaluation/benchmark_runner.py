# evaluation/benchmark_runner.py

import json
import os
from pathlib import Path
from loguru import logger

from evaluation.auto_metrics          import run_all
from evaluation.hallucination_checker import batch_check

def run(
    test_path="data/annotated/test/qa_pairs.jsonl",
    output_path="evaluation/eval_report.json",
):
    """Evaluates the full pipeline against the annotated test dataset."""
    if not Path(test_path).exists():
        logger.error(f"Test dataset file not found: {test_path}")
        return {}

    test_pairs = []
    with open(test_path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                test_pairs.append(json.loads(line))

    logger.info(f"Loaded {len(test_pairs)} test QA pairs.")
    if not test_pairs:
        return {}

    predictions   = []
    references    = []
    contexts_list = []

    try:
        from rag.rag_pipeline import answer as rag_answer
        for i, pair in enumerate(test_pairs):
            try:
                result   = rag_answer(pair["question"], top_k=3)
                contexts = result.get("contexts", [])
                pred     = contexts[0]["text"] if contexts else ""
                predictions.append(pred)
                references.append(pair["answer"])
                contexts_list.append(contexts)
                logger.info(f"[{i+1}/{len(test_pairs)}] Evaluated question: {pair['question'][:40]}...")
            except Exception as e:
                logger.warning(f"Failed pair {i}: {e}")
                predictions.append("")
                references.append(pair["answer"])
                contexts_list.append([])
    except ImportError:
        logger.error("RAG pipeline module not imported cleanly.")
        return {}

    metrics = run_all(predictions, references)
    halluc  = batch_check(predictions, contexts_list)

    report = {
        "test_samples": len(test_pairs),
        "metrics":      metrics,
        "hallucination": {
            "total":             halluc["total"],
            "hallucinated":      halluc["hallucinated_count"],
            "clean":             halluc["clean_count"],
            "hallucination_rate": halluc["hallucination_rate"],
        },
        "sample_results": [
            {
                "question":   test_pairs[i]["question"],
                "reference":  references[i],
                "prediction": predictions[i][:200],
            }
            for i in range(min(3, len(predictions)))
        ],
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    logger.success("=" * 50)
    logger.success("Evaluation Summary Report")
    logger.success(f"  Test samples : {report['test_samples']}")
    for k, v in metrics.items():
        logger.success(f"  {k:25} : {v}")
    logger.success(f"  Hallucination Rate: {halluc['hallucination_rate']}")
    logger.success(f"  Report saved to   : {output_path}")

    return report

if __name__ == "__main__":
    run()