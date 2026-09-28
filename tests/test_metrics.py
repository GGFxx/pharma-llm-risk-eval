import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pharma_llm_risk_eval.metrics import (  # noqa: E402
    accuracy_with_interval,
    stratified_report,
    wilson_interval,
)
from pharma_llm_risk_eval.runner import gate, score, validate_items  # noqa: E402


class TestWilson(unittest.TestCase):
    def test_three_of_three(self):
        low, high = wilson_interval(3, 3)
        self.assertAlmostEqual(low, 0.438, delta=0.001)
        self.assertEqual(high, 1.0)

    def test_zero_of_three(self):
        low, high = wilson_interval(0, 3)
        self.assertEqual(low, 0.0)
        self.assertAlmostEqual(high, 0.562, delta=0.001)

    def test_symmetry(self):
        # 3/3 与 0/3 的区间关于 0.5 镜像
        low_all, _ = wilson_interval(3, 3)
        _, high_none = wilson_interval(0, 3)
        self.assertAlmostEqual(low_all, 1 - high_none, delta=1e-9)

    def test_no_sample_no_information(self):
        self.assertEqual(wilson_interval(0, 0), (0.0, 1.0))

    def test_accuracy_payload(self):
        payload = accuracy_with_interval(2, 4)
        self.assertEqual(payload["accuracy"], 0.5)
        self.assertLess(payload["wilson_low"], 0.5)
        self.assertGreater(payload["wilson_high"], 0.5)


class TestStratifiedReport(unittest.TestCase):
    def test_layers_and_overall(self):
        records = [
            {"track": "T1", "category": "法规事实", "correct": True},
            {"track": "T1", "category": "法规事实", "correct": True},
            {"track": "T1", "category": "法规事实", "correct": False},
            {"track": "T2", "category": "用药安全", "correct": True},
        ]
        report = stratified_report(records)
        self.assertEqual(report["overall"]["total"], 4)
        self.assertEqual(report["overall"]["correct"], 3)
        t1 = report["strata"]["T1 / 法规事实"]
        self.assertEqual(t1["total"], 3)
        self.assertAlmostEqual(t1["accuracy"], 0.6667, delta=0.0001)


class TestValidateAndScore(unittest.TestCase):
    def _item(self, **overrides):
        item = {
            "id": "T1-0001",
            "track": "T1-regulatory-faithfulness",
            "category": "法规事实",
            "question": "示例问题？",
            "choices": {"A": "甲", "B": "乙", "C": "丙", "D": "丁"},
            "answer": "C",
            "sources": ["公开指导原则名称"],
            "risk_level": "low",
            "status": "draft-unreviewed",
        }
        item.update(overrides)
        return item

    def test_valid_item_passes(self):
        self.assertEqual(validate_items([self._item()]), [])

    def test_missing_sources_fails(self):
        problems = validate_items([self._item(sources=[])])
        self.assertTrue(any("sources" in p for p in problems))

    def test_bad_status_fails(self):
        problems = validate_items([self._item(status="gold")])
        self.assertTrue(any("status" in p for p in problems))

    def test_answer_outside_choices_fails(self):
        problems = validate_items([self._item(answer="E")])
        self.assertTrue(any("answer" in p for p in problems))

    def test_duplicate_id_fails(self):
        problems = validate_items([self._item(), self._item(id="T1-0001")])
        self.assertTrue(any("重复" in p for p in problems))

    def test_score_missing_prediction_counts_wrong(self):
        records = score([self._item()], [])
        self.assertEqual(records[0]["correct"], False)
        self.assertEqual(records[0]["answered"], False)

    def test_score_correct_prediction(self):
        records = score(
            [self._item()], [{"id": "T1-0001", "model": "demo", "parsed_answer": "C"}]
        )
        self.assertTrue(records[0]["correct"])

    def test_gate(self):
        overall = accuracy_with_interval(9, 10)
        self.assertTrue(gate(overall, 0.85))
        self.assertFalse(gate(overall, 0.95))
        self.assertFalse(gate({"accuracy": None}, 0.5))


class TestEvalsOnDisk(unittest.TestCase):
    """仓库内种子条目必须能通过自身校验（防手滑破坏格式）。"""

    ROOT = os.path.join(os.path.dirname(__file__), "..")

    def _files(self):
        for track_dir in ("T1-regulatory-faithfulness", "T2-medication-safety"):
            path = os.path.join(self.ROOT, "evals", track_dir, "items.draft.jsonl")
            if os.path.exists(path):
                yield path

    def test_seed_items_valid(self):
        for path in self._files():
            with open(path, "r", encoding="utf-8") as fh:
                items = [json.loads(line) for line in fh if line.strip()]
            self.assertEqual(validate_items(items), [], msg=path)


if __name__ == "__main__":
    unittest.main()
