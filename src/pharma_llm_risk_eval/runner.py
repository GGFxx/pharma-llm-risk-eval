"""评测条目与预测文件的校验、评分。

条目 schema（JSONL，一行一条）：
    id / track / category / question / answer 必填；
    sources 必填且非空（金标必须可溯源）；
    risk_level in {low, medium, high}；
    status in {draft-unreviewed, reviewed, frozen}。

冻结纪律：
- status=frozen 的条目集进入 eval 前做一致性校验（id 唯一、answer 在 choices 内）；
- 含 draft-unreviewed 的条目集可以跑评测，但结果必须标注 draft（不构成对外结论）。

预测文件（JSONL）：{"id": ..., "model": ..., "parsed_answer": ...}
"""

import json
from typing import Dict, Iterable, List

REQUIRED_FIELDS = ("id", "track", "category", "question", "answer", "sources")
VALID_RISK = {"low", "medium", "high"}
VALID_STATUS = {"draft-unreviewed", "reviewed", "frozen"}


class ItemError(ValueError):
    pass


def load_jsonl(path):
    items = []
    with open(path, "r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ItemError("第 %d 行不是合法 JSON：%s" % (lineno, exc)) from exc
    return items


def validate_items(items: Iterable[Dict]) -> List[str]:
    """返回问题列表；空列表 = 全部通过。"""
    problems = []
    seen_ids = set()
    for idx, item in enumerate(items, 1):
        where = "条目#%d(%s)" % (idx, item.get("id", "?"))
        for field in REQUIRED_FIELDS:
            if field not in item or item[field] in (None, "", []):
                problems.append("%s 缺少必填字段 %s" % (where, field))
        if item.get("risk_level") not in VALID_RISK:
            problems.append("%s risk_level 非法：%r" % (where, item.get("risk_level")))
        if item.get("status") not in VALID_STATUS:
            problems.append("%s status 非法：%r" % (where, item.get("status")))
        if item.get("id") in seen_ids:
            problems.append("%s id 重复" % where)
        seen_ids.add(item.get("id"))
        choices = item.get("choices")
        if choices is not None:
            if not isinstance(choices, dict) or not choices:
                problems.append("%s choices 必须是非空对象" % where)
            elif item.get("answer") not in choices:
                problems.append("%s answer 不在 choices 内" % where)
    return problems


def score(gold_items: List[Dict], predictions: List[Dict]) -> List[Dict]:
    """把预测对齐到金标并打分；缺失预测按错误计（缺席不是免答）。"""
    pred_by_id = {}
    for p in predictions:
        pred_by_id[p.get("id")] = p

    records = []
    for item in gold_items:
        pred = pred_by_id.get(item["id"])
        correct = bool(pred) and pred.get("parsed_answer") == item["answer"]
        records.append(
            {
                "id": item["id"],
                "track": item["track"],
                "category": item["category"],
                "correct": correct,
                "answered": pred is not None,
            }
        )
    return records


def gate(overall: Dict[str, object], min_accuracy: float) -> bool:
    acc = overall.get("accuracy")
    if acc is None:
        return False
    return acc >= min_accuracy
