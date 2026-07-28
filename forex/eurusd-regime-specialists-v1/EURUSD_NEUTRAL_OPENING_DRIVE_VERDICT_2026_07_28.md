# EURUSD Neutral session-opening-drive verdict

Date: 2026-07-28

Decision: `REJECTED_NEUTRAL_OPENING_DRIVE_V1`

The frozen 30-minute session-opening-drive rule failed every chronological
window and both robustness tests. It is not eligible for demo, live use, or
prospective promotion collection.

## Frozen rule

At 00:00, 06:00, 12:00, and 18:00 UTC, the strategy observed the fully
completed first 30-minute bar in an eligible Neutral state. A body of at
least four pips closing in the directional outer quartile selected the side.
Entry occurred only at the next M5 open.

Execution used fixed 4-pip risk, 1.5R target, 12-hour timeout, causal bid/ask
prices, 0.7-pip spread floor, 0.1-pip slippage per side, stop-first same-bar
handling, and one open position.

The outcome-blind ledger contained 593 candidates, balanced between 299
long and 294 short.

## Chronological results

| Window | Trades | Win rate | Payoff | Profit factor | Net R |
|---|---:|---:|---:|---:|---:|
| Development, 2019-2020 | 160 | 25.00% | 1.439 | 0.480 | -64.00 |
| Development, 2021-2022 | 173 | 32.37% | 1.417 | 0.678 | -38.60 |
| Validation, 2023-2024 | 132 | 33.33% | 1.440 | 0.720 | -25.25 |
| Pseudo-OOS, 2025-2026 H1 | 128 | 39.06% | 1.436 | 0.921 | -6.35 |
| Full history | 593 | 32.04% | 1.432 | 0.675 | -134.20 |

Performance improved monotonically by window but never became profitable.
The latest six months contained 45 trades, won 40.00%, returned PF 0.957,
and lost 1.20R. At the realized 1.435 payoff, this remains below break-even.

## Robustness and oracle resemblance

- Remove the largest 5% of winners: PF 0.568, net -178.48R.
- Add 0.5 pip per round trip: PF 0.551, net -208.33R.
- Same-side/date oracle matches within 60 minutes: 168.
- Oracle precision: 28.33%.
- Oracle recall: 6.42%.
- Median matched timing difference: 15 minutes.

The improving recency pattern is descriptive only and may not be selected
after the full rule failed. Body size, close location, anchors, direction,
and years remain closed without repair.

## Prospective boundary

The preregistration proposed a forward-only start at 2026-07-29 and required
100 trades plus six months. Because the historical admission gate failed,
that watchlist is cancelled with zero post-lock observations. Future data
must be reserved for a genuinely new frozen mechanism.

## Reproduce

```powershell
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_opening_drive.py
```
