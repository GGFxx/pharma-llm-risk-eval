"""Wilson 置信区间与分层指标——零依赖实现。

口径约定：
- 所有区间为 Wilson score interval（95%，z=1.959963985），小样本下自然放宽
  （3/3 全对的下界约 43.8%）——区间宽度本身就是「样本量还不足以下结论」的信号。
- 分层只做两层：track -> category；每层输出 (correct, total, acc, low, high)。
"""

import math
from typing import Dict, List, Optional, Tuple

Z_95 = 1.959963984540054


def wilson_interval(correct: int, total: int, z: float = Z_95) -> Tuple[float, float]:
    """Wilson score interval for a binomial proportion.

    3/3 -> (0.438, 1.000); 0/3 -> (0.000, 0.562)（对称性可作测试断言）。
    total == 0 时返回 (0.0, 1.0)——无样本即无信息，不假装有结论。
    """
    if total <= 0:
        return (0.0, 1.0)
    n = total
    k = min(max(correct, 0), n)
    p = k / n
    denom = 1.0 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    margin = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    low = max(0.0, center - margin)
    high = min(1.0, center + margin)
    # 贴边情形钉死精确值，消除浮点残差（0/n 下界恒 0，n/n 上界恒 1）
    if k == 0:
        low = 0.0
    if k >= n:
        high = 1.0
    return (low, high)


def accuracy_with_interval(correct: int, total: int, z: float = Z_95) -> Dict[str, object]:
    low, high = wilson_interval(correct, total, z)
    return {
        "correct": correct,
        "total": total,
        "accuracy": round(correct / total, 4) if total else None,
        "wilson_low": round(low, 4),
        "wilson_high": round(high, 4),
    }


def stratified_report(
    records: List[Dict[str, object]],
    stratum_keys: Optional[List[str]] = None,
) -> Dict[str, object]:
    """records: [{"track": ..., "category": ..., "correct": bool}, ...]

    返回 overall + 按 stratum_keys（默认 ["track", "category"]）的分层指标。
    """
    stratum_keys = stratum_keys or ["track", "category"]
    buckets = {}

    def bucket_key(rec):
        return tuple(str(rec.get(k, "unknown")) for k in stratum_keys)

    for rec in records:
        key = bucket_key(rec)
        b = buckets.setdefault(key, {"correct": 0, "total": 0})
        b["total"] += 1
        if rec.get("correct"):
            b["correct"] += 1

    layers = {}
    for key in sorted(buckets):
        b = buckets[key]
        label = " / ".join(key)
        layers[label] = accuracy_with_interval(b["correct"], b["total"])

    total_correct = sum(b["correct"] for b in buckets.values())
    total_n = sum(b["total"] for b in buckets.values())
    return {"overall": accuracy_with_interval(total_correct, total_n), "strata": layers}
