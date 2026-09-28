# pharma-llm-risk-eval

**医药垂域 LLM 风险与可靠性评测** ｜ Pharma-vertical LLM Risk & Reliability Evaluation

[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue)]() [![License: MIT](https://img.shields.io/badge/License-MIT-green)]() [![status](https://img.shields.io/badge/status-立项建设中-orange)]() [![deps](https://img.shields.io/badge/deps-零依赖stdlib-success)]()

> **English** · An open evaluation suite for measuring LLM risks and reliability in the pharmaceutical / biomedical vertical — regulatory faithfulness, medication safety, and dual-use knowledge boundaries. Evaluation-infrastructure-first: frozen gold sets, stratified metrics with Wilson intervals, and regression gates. See [README.en.md](README.en.md).

通用 LLM 安全基准（如公开的综合安全测验）覆盖暴力、违法、隐私等横向风险，但**药品监管与用药场景的垂域风险**——监管条文幻觉、错误用药建议、双用途知识边界——缺少系统化的开源评测。本项目补这个空白：给「生物医药垂域的 LLM 应用」一套可复现、可回归的风险度量工具。

**方法论来源**：评测基建（金标冻结、分层指标、回归门禁）复用自同作者的开源项目 [ectd-assembler](https://github.com/GGFxx/ectd-assembler) 在 LLM 可靠性工程上的实践。

## 三条评测线

| 线 | 名称 | 测什么 | 状态 |
|---|---|---|---|
| T1 | **监管事实可靠性**（Regulatory Faithfulness） | 模型对药品监管条文/事实的回答忠实度与幻觉率——以公开指导原则为金标来源，条文级可溯源 | 设计 + 种子条目（待专家复核） |
| T2 | **用药安全**（Medication Safety） | 模型对常见用药问题（剂量/禁忌/相互作用）的回答是否包含必要的安全提示与就医引导 | 设计 + 种子条目（待专家复核） |
| T3 | **双用途知识边界**（Dual-use Boundary） | 模型对生物/化学双用途知识的边界行为——**只测能力存在性，不收集不分发有害内容** | 仅设计原则（伦理审查前置） |

## 评测基建（已实现，零依赖）

- **金标冻结**：评测条目一经冻结（`frozen: true`）不可增删改；新增标注必须另建新集——度量工具不能污染自己的标尺。
- **分层指标**：按 track / category 分层统计准确率，每层带 **Wilson 95% 置信区间**——小样本下区间自然变宽（3/3 的 100% 区间是 [43.8%, 100%]），那是「还不该下结论」的信号，不是一个可以引用的数字。
- **回归门禁**：`--min-accuracy` 阈值门禁，换模型 / 改 prompt 必须重跑并通过门禁；CLI 退出码可直接接入 CI。

```bash
# 校验条目集格式（schema + 必填字段 + 冻结规则）
python3 -m pharma_llm_risk_eval verify evals/T1-regulatory-faithfulness/items.draft.jsonl

# 跑评测（预测文件 vs 金标），分层指标 + Wilson 区间 + 阈值门禁
python3 -m pharma_llm_risk_eval eval --gold evals/T1-regulatory-faithfulness/items.draft.jsonl \
    --predictions preds.example.jsonl --min-accuracy 0.9
```

（零第三方依赖，Python 3.9+ 标准库即可运行。）

## 条目格式

```json
{
  "id": "T1-0001",
  "track": "T1-regulatory-faithfulness",
  "category": "法规事实",
  "question": "……",
  "choices": {"A": "…", "B": "…", "C": "…", "D": "…"},
  "answer": "C",
  "sources": ["公开来源名称与可核验出处"],
  "risk_level": "low|medium|high",
  "status": "draft-unreviewed"
}
```

**状态纪律**：`draft-unreviewed`（未经领域专家复核，仅示例格式，不得用于对外结论）→ `reviewed`（专家复核通过）→ `frozen`（冻结为金标基线）。当前仓库内全部种子条目均为 `draft-unreviewed`——这是有意的：**没有领域专家复核的条目不配当金标**，HITL 是本项目的第一原则。

## 伦理与安全红线（先读 [docs/ETHICS.md](docs/ETHICS.md)）

- 仅使用**公开**数据构建评测条目；不使用、不复制任何非公开监管工作信息。
- **测量不教学**：T3 只测量模型对双用途知识的行为边界，不收集、不生成、不分发任何有害操作内容；条目集在伦理审查完成前不发布本体。
- 评测结果**不构成**任何模型的安全性认证或背书，仅供研究参考。
- 个人开源项目，与任何机构无关。

## 路线图

1. **T1 扩充**：基于公开指导原则结构化语料（643 篇全量，见作者另一项目）批量生成候选条目 → 领域专家复核 → 冻结 v1.0 金标集
2. **评测驱动**：接入主流中文/通用模型的首轮基线报告（分层指标 + 区间，不排名、只报告）
3. **T2 扩充**：与执业药师/临床药师协作复核用药安全条目
4. **T3 伦理审查**：参照公开双用途基准的治理惯例设计条目发布流程
5. **回归门禁 CI 化**：模型/prompt 变更的自动回归

## License

[MIT](LICENSE) © 2026 GGFxx
