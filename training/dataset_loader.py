# training/dataset_loader.py

import json
from pathlib import Path
from loguru import logger

try:
    from datasets import Dataset
    DATASETS_AVAILABLE = True
except ImportError:
    DATASETS_AVAILABLE = False

from training.prompt_templates import format_qa

DATA_DIR = Path("data/annotated")

def load_split(split: str = "train"):
    """Loads a dataset split (train/val/test) from JSONL file."""
    path = DATA_DIR / split / "qa_pairs.jsonl"
    if not path.exists():
        logger.error(f"Dataset split not found at: {path}")
        return None

    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
                text = format_qa(
                    question=row["question"],
                    context=row.get("context", ""),
                    answer=row["answer"],
                    intent=row.get("intent", "general"),
                )
                records.append({"text": text})
            except Exception as e:
                logger.warning(f"Skipping malformed record: {e}")

    logger.info(f"Successfully loaded {len(records)} records from {split} split.")
    
    if not DATASETS_AVAILABLE:
        return records
        
    return Dataset.from_list(records)

def load_all():
    """Loads all three splits into a dictionary."""
    return {split: load_split(split) for split in ("train", "val", "test")}

def get_dataset_stats():
    """Returns row counts for train, val, and test splits."""
    stats = {}
    for split in ("train", "val", "test"):
        path = DATA_DIR / split / "qa_pairs.jsonl"
        if path.exists():
            with open(path, encoding="utf-8") as f:
                count = sum(1 for line in f if line.strip())
            stats[split] = count
        else:
            stats[split] = 0
    return stats

if __name__ == "__main__":
    stats = get_dataset_stats()
    print("Dataset Summary:")
    for split, count in stats.items():
        print(f"  {split:10} : {count} pairs")