# evaluation/__init__.py

from evaluation.auto_metrics          import run_all
from evaluation.hallucination_checker import check
from evaluation.benchmark_runner      import run

__all__ = ["run_all", "check", "run"]