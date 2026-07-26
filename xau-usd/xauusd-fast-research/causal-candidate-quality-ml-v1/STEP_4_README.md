# Step 4 Locked Walk-Forward Result

Step 4 is complete. The preregistered primary model did not pass its evidence
gate and is not authorized for MT5, shadow, demo, or live use.

Primary out-of-time result across six untouched July-to-July eras:

- `2,368` eligible candidates and `2,275` structural episodes.
- Weighted ROC AUC `0.5193`; 95% five-weekday block interval
  `0.4922` to `0.5474`.
- Every calibration window chose threshold `0.0`, so all `2,368` candidates
  were retained and ML produced no filtering improvement.
- The underlying candidate baseline remained positive at weighted mean
  `0.2510R`, weighted profit factor `1.4142`, and approximately `1.51` raw
  candidates or `1.45` structural episodes per weekday.
- The weighted `74.69R` drawdown is a candidate-quality diagnostic, not an
  account or portfolio drawdown claim.
- `9` of `12` acceptance checks passed. Weighted AUC, its lower confidence
  bound, and the lower confidence bound for improvement over baseline failed.
- Logistic, deterministic-only, and cross-asset ablations did not rescue the
  primary result. COMEX features and the Databento API were not used.

Run the locked evaluation:

```powershell
uv run --no-project --with-requirements requirements-step4.txt python run_step_4.py
```

Verify artifacts, model replay, bootstrap, and control state:

```powershell
uv run --no-project --with-requirements requirements-step4.txt python verify_step_4.py
```
