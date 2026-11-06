# Evidence Score Evaluation

The evaluation set checks whether the deterministic score behaves like an evidence-completeness measure rather than an investment-quality prediction.

Run:

```bash
python -m eval.run_eval
```

The 12 deterministic cases include complete, partial, minimal, negative, team-only, traction-only, economics-heavy, risk-heavy, explicit-missing and keyword-stuffing notes. Passing requires the score and review status to fall within the *revised conservative* rubric expectations. Cases E02, E05, E11 and E12 additionally assert zero evidence credit for specified missing categories. The prior baseline scores included missing-disclosure false positives and must not be treated as ground truth.

Each case supplies extracted signals alongside its notes, and only signals the notes back earn credit. E05 is deliberately inconsistent: its extraction lists a customer segment and a risk that its notes say are not described, so those categories must score zero. E01's notes state the traction, customer and risk facts its signals claim.

This tests the rubric only, not the correctness of live AI extraction, external source verification or investment recommendations.
