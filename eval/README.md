# Evidence Score Evaluation

The evaluation set checks whether the deterministic score behaves like an evidence-completeness measure rather than an investment-quality prediction.

Run:

```bash
python -m eval.run_eval
```

The 12 deterministic cases include complete, partial, minimal, negative, team-only, traction-only, economics-heavy, risk-heavy, explicit-missing and keyword-stuffing notes. Passing requires the score and review status to fall within the *revised conservative* rubric expectations. Cases E02, E11 and E12 additionally assert zero evidence credit for specified missing categories. The prior baseline scores included missing-disclosure false positives and must not be treated as ground truth.\n\nThis tests the rubric only—not the correctness of live AI extraction, external source verification or investment recommendations.\n
