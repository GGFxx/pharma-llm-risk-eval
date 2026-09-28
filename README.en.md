# pharma-llm-risk-eval

**Pharma-vertical LLM risk & reliability evaluation** — an open evaluation suite measuring LLM behavior in pharmaceutical / biomedical contexts:

- **T1 Regulatory faithfulness** — hallucination rate on drug-regulation facts, gold sourced from publicly issued guidelines, clause-level traceable.
- **T2 Medication safety** — whether answers to common medication questions carry necessary safety caveats and clinical-referral guidance.
- **T3 Dual-use knowledge boundary** — measuring model behavior at the edge of dual-use knowledge. **Measurement only**: no harmful content is collected, generated, or distributed; item release is gated behind an ethics review.

Evaluation infrastructure comes first: frozen gold sets, stratified accuracy with Wilson 95% intervals, and threshold-based regression gates — methodology carried over from [ectd-assembler](https://github.com/GGFxx/ectd-assembler). Zero-dependency (Python 3.9+ stdlib).

All seed items currently carry `status: draft-unreviewed` — nothing becomes a gold standard without domain-expert review (human-in-the-loop is the first principle of this project).

See the Chinese [README.md](README.md) for full details.

## License

MIT © 2026 GGFxx
