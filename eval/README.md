# Evidence Score Evaluation

The evaluation set checks whether the deterministic score behaves like an evidence-completeness measure rather than an investment-quality prediction.

Run:

```bash
python -m eval.run_eval
```

The cases include complete, partial, minimal, negative, team-only, traction-only, economics-heavy, and risk-heavy notes. Passing means the score falls within the documented band and receives the expected diligence status.
