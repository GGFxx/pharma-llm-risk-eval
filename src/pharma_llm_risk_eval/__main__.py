"""CLI：verify（条目集校验）/ eval（评分 + 分层指标 + 门禁）。

用法（仓库根目录，PYTHONPATH=src）：
    PYTHONPATH=src python3 -m pharma_llm_risk_eval verify evals/T1-regulatory-faithfulness/items.draft.jsonl
    PYTHONPATH=src python3 -m pharma_llm_risk_eval eval --gold <gold.jsonl> --predictions <preds.jsonl> [--min-accuracy 0.9]

退出码：0 = 通过/门禁通过；2 = 校验失败；3 = 门禁未达标。
"""

import argparse
import json
import sys

from .metrics import stratified_report
from .runner import gate, load_jsonl, score, validate_items


def cmd_verify(args):
    items = load_jsonl(args.items)
    problems = validate_items(items)
    if problems:
        print("校验失败（%d 个问题）：" % len(problems))
        for p in problems:
            print("  -", p)
        return 2
    frozen = sum(1 for i in items if i.get("status") == "frozen")
    draft = sum(1 for i in items if i.get("status") == "draft-unreviewed")
    print("校验通过：%d 条（frozen=%d, reviewed=%d, draft-unreviewed=%d）"
          % (len(items), frozen, len(items) - frozen - draft, draft))
    if draft:
        print("注意：含 draft-unreviewed 条目，不得用于对外结论。")
    return 0


def cmd_eval(args):
    gold = load_jsonl(args.gold)
    problems = validate_items(gold)
    if problems:
        print("金标校验失败：%s" % problems[:3])
        return 2
    preds = load_jsonl(args.predictions) if args.predictions else []
    records = score(gold, preds)
    report = stratified_report(records)

    print(json.dumps(report, ensure_ascii=False, indent=2))
    overall = report["overall"]
    if args.min_accuracy is not None:
        if gate(overall, args.min_accuracy):
            print("门禁通过：accuracy=%s >= %s" % (overall["accuracy"], args.min_accuracy))
            return 0
        print("门禁未达标：accuracy=%s < %s" % (overall["accuracy"], args.min_accuracy))
        return 3
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="pharma_llm_risk_eval")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_verify = sub.add_parser("verify", help="校验评测条目集")
    p_verify.add_argument("items")
    p_verify.set_defaults(func=cmd_verify)

    p_eval = sub.add_parser("eval", help="评分并输出分层指标")
    p_eval.add_argument("--gold", required=True)
    p_eval.add_argument("--predictions", default=None)
    p_eval.add_argument("--min-accuracy", type=float, default=None)
    p_eval.set_defaults(func=cmd_eval)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
