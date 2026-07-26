# Regime-Specific Candidate Quality Models V2

This package trains one independent, strongly regularized candidate-quality
model per canonical specialist family using the locked causal Step 3 dataset
and purged expanding walk-forward folds.

Seven families had enough fold-local data to train. R2 and V25 failed closed as
`INSUFFICIENT_EVIDENCE`. Only `V8_RETEST_HEALTH` passed all locked development
gates. Across 102 out-of-time candidates, it selected 60, produced weighted AUC
`0.6388` (95% block-bootstrap lower bound `0.5297`), improved mean stressed
outcome from `0.4801R` to `0.7031R`, improved PF from `2.1883` to `3.3571`, and
reduced candidate-sequence drawdown from `7.7286R` to `3.4836R`. The lower 95%
bound on selected-minus-baseline mean stressed outcome was only `0.0076R`, and
the latest fold's delta was negative, so the evidence is promising but thin.

This result is development-only on exposed history. It does not authorize ML
shadow, demo, live, filtering, routing, or MT5 integration. The next legitimate
step is prospective V8 scoring with predictions recorded but ignored by the
deterministic demo executor until a separately locked forward gate passes.

Run verification with:

```powershell
uv run --with-requirements requirements.txt python verify.py
```
