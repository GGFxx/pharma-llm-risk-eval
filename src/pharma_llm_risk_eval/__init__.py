"""pharma-llm-risk-eval：医药垂域 LLM 风险与可靠性评测（零依赖）。"""

__version__ = "0.0.1"

from .metrics import accuracy_with_interval, stratified_report, wilson_interval  # noqa: F401
from .runner import load_jsonl, score, validate_items  # noqa: F401
