# EURUSD frozen residual historical diagnostic

Date: 2026-07-30

Status: **HISTORICAL_FALSIFICATION_FAILED**

Demo-order authorization: **false**

## Decision

The exact frozen live residual rule is rejected as a solution to the
frequency gap. It did not damage the protected M15 portfolio, but it was
too selective to contribute meaningful recent capacity.

This was a one-candidate, post-freeze falsification replay. No clock,
side, threshold, stop, target, or regime was searched. The result is
retrospective evidence only and cannot count toward the live-forward
admission ledger.

## What is missing

The protected M15 component remains the only demonstrated edge:

- 106 broker every-real-tick trades over 522 weekdays;
- 0.2031 trades per weekday and 18.77% weekday coverage;
- 49.06% wins, 1.4648 payoff, PF 1.4105;
- stressed PF 1.3405 and best-5%-removed PF 1.1068.

The residual component needed to supply independent trades on M15-empty
weekdays. Instead, the exact frozen rule produced:

- 136 trades over 2,608 complete weekdays, or 0.0521 per weekday;
- 5.21% weekday coverage;
- PF 1.0552, stressed PF 0.9398, best-5%-removed PF 0.9087;
- 42.65% wins, 1.4191 payoff, and only +3.925R;
- zero trades in the latest 12 months.

Its chronological PF was 0.5962, 1.2116, 1.2353, and 2.2593 across the
four fixed blocks, but the final block contained only three trades. The
two trade-sequence halves were 1.1672 and 0.9591. This is neither dense
nor stable enough to promote.

## Combined two-year broker window

The exact residual rule added only three trades to the 106 protected
M15 trades:

| Metric | Full two years | Latest 12 months |
|---|---:|---:|
| Trades | 109 | 61 |
| Trades per weekday | 0.2088 | 0.2337 |
| Weekday coverage | 19.35% | 21.46% |
| Win rate | 49.54% | 49.18% |
| Payoff | 1.4413 | 1.5028 |
| Profit factor | 1.4151 | 1.4543 |
| Stressed profit factor | 1.3443 | 1.3833 |
| Best-5%-removed PF | 1.1129 | 1.0977 |
| Net P&L | $62.62 | $38.88 |

The combined edge metrics pass because the M15 component carries them.
The frequency target of 0.85-1.25 trades per weekday and the 65%
weekday-coverage floor fail decisively.

## Next bounded research step

Develop a dense residual family whose side rule is causal and defined
before its outcomes are inspected. It must target otherwise-empty
Monday-Thursday dates, use the frozen 20:00 UTC execution geometry, and
be selected on an earlier development block before being judged on a
later locked validation block. Any family that reaches frequency only
by accepting PF at or below one is rejected.

## Reproducibility

Run:

```powershell
uv run --offline --with pandas --with numpy --with pyarrow python run_frozen_residual_history_diagnostic.py
```

Locked live-candidate hashes:

- frozen live residual config:
  `e11e9db9f1fba5df077548f8c014688076f2c44ec7d5e6083dc03b4b4ff76e79`
- frozen live residual specialist source:
  `084664f4d3f38cf9f300481915501afb8087b99b01235b5e64d163815f5a4741`
- protected M15 trades:
  `3b61273712c75d5aa5cf8ef9d46c71170687ec34fcd9156bfccccf15e8653e43`

Output hashes:

- `COMBINED_TRADES.csv`:
  `dc36c76486b8acea4ce8fb7222c0f4db00dde3dfc82bf5210d4320474b0fa1e9`
- `ELIGIBLE_RESIDUAL_TRADES.json`:
  `97f078d813b843afe308e735236b4dd4f2cadf40530987f2a3d9e9bc6fadff4d`
- `MONTHLY.csv`:
  `dc2225e5549bd6b7d976d88b8ff42c8df6b89146b9b1143aa59492687e84e232`
- `RESULT.json`:
  `3a39845b604d86973d6970b0f6b8c239e7b943bf3a80ae526d78623463e48083`
- `RESULT.md`:
  `35ad2d9b9d23d3aa79c14bfd9fe8cd7c48276a4b320cae485daaafe58ea1926`
