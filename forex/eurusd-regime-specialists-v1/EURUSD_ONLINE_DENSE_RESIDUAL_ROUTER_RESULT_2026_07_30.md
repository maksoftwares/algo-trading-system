# EURUSD online dense residual router result

Date: 2026-07-30

Status: **HISTORICAL_VALIDATION_REJECTED**

Demo-order authorization: **false**

## Result

The causal online router substantially closed the activity gap, but it did so
by adding a losing residual sleeve. It is not safe to deploy.

The router was preregistered before this run. On each resolved residual date,
it selected one of the twelve already frozen direction rules using only
completed prior shadow outcomes from the same causal regime. The current
outcome entered history only after the current rule and side were fixed. One
router variant was evaluated.

## Locked 2022-2026 residual validation

| Metric | Result |
|---|---:|
| Trades | 821 |
| Trades per weekday | 0.7005 |
| Weekday coverage | 70.05% |
| Win rate | 38.37% |
| Payoff | 1.2271 |
| Profit factor | 0.7669 |
| Stressed profit factor | 0.6790 |
| Best-5%-removed PF | 0.6334 |
| Net result | -109.0375R |

The two trade-sequence halves were PF 0.7723 and 0.7609. The loss is broad,
not confined to one brief period.

By causal regime:

| Regime | Trades | Net R | PF |
|---|---:|---:|---:|
| Cross-pair compression | 277 | -28.1625 | 0.8134 |
| Mixed transition | 390 | -62.6000 | 0.7195 |
| Broad EUR down | 69 | -13.1375 | 0.7026 |
| Broad EUR up | 71 | -8.3750 | 0.8071 |
| Short/long disagreement | 14 | +3.2375 | 1.5329 |

Only Short/Long Disagreement was profitable, and its 14 trades are far too few
to support promotion. All four high-capacity regimes lost.

## Protected M15 plus online residual, two years

| Metric | Full two years | Latest 12 months |
|---|---:|---:|
| Trades | 430 | 219 |
| Trades per weekday | 0.8238 | 0.8391 |
| Weekday coverage | 80.84% | 81.99% |
| Win rate | 41.63% | 42.47% |
| Payoff | 1.5232 | 1.5886 |
| Profit factor | 1.0906 | 1.1725 |
| Stressed profit factor | 1.0055 | 1.0860 |
| Best-5%-removed PF | 0.6694 | 0.7400 |
| Net P&L | $26.92 | $27.18 |

The portfolio needed at least 444 trades to pass the 0.85/day floor, so it was
short by 14 trades. That small count gap is not the primary blocker:

- the residual component supplied 324 trades but lost 43.35R, or about
  $34.68 at 0.01 lot;
- protected M15 supplied 106 trades and +$61.60, carrying the combined result;
- the first 12 months of the combined portfolio lost $0.26;
- full-period PF 1.0906 missed 1.15;
- stressed PF 1.0055 missed 1.05;
- best-5%-removed PF 0.6694 shows severe winner concentration;
- 41.63% wins missed the 45% floor.

Adding another 14 trades cannot repair those economic failures. Weakening the
gate would only hide the negative residual edge.

## What is now known

Static or trailing-performance variants of the same 20:00 cross-pair
direction signal do not solve the empty-day problem. The high-capacity regimes
need genuinely different mechanisms, not a more permissive router over the
same signals.

The next research unit should therefore be a dedicated Cross-Pair Compression
expert using an independent own-price mean-reversion mechanism, followed by
separate mechanisms for Mixed Transition and the two broad-trend regimes.
Each regime specialist must be selected without later-period outcomes and
must independently pass after-cost validation before combination.

## Reproducibility

Run:

```powershell
uv run --offline --with pandas --with numpy --with pyarrow python run_online_dense_residual_router.py
```

Implementation hashes:

- config:
  `57fd19ba086a51dd0c45201d2c8893bb5cbd2824bc8211f2aa0c5f060fee7feb`
- source:
  `83ed3c4a1d34879ac69f4ce7dc9ce5722856691e66c2f656e882181ca2c5ba89`

Output hashes:

- `VALIDATION_TRADES.csv`:
  `5021a0044248a04101bf9d9e62648688a34669e0918155c1327b07363ab2bbe5`
- `MONTHLY.csv`:
  `d5a8c0e1df90d8656de9d1ce67b5e937ee5eea0b3fb348f775c4cb3cb0deef32`
- `RESULT.json`:
  `24e0b900ae293a8ed0933f4ef404b45c9776ac1c7952b7f92b8d208546a4fc06`
- `RESULT.md`:
  `f8fcf398b04b6a9bb9f37d1426c6cad3e0886290424f9a430e0d12dcd5491dd0`
