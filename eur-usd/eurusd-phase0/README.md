# EURUSD Phase 0

This directory packages the strongest existing EURUSD actual-MT5 research
candidate as a deterministic, research-only baseline.

Candidate:

`EURUSD_M30_RSI_BB_CLOSE_FADE_LONG_V1`

The strategy buys after a completed M30 candle closes at or below the lower
20-period Bollinger Band while RSI(14) is at or below 35. It uses a stop at the
wider of 1.4 ATR(14), 30 points, or the lowest low of the last six completed
M30 bars; the stop is capped at 700 points and the target is 0.8R. Entry hours
6, 7, 10, and 13 in broker/tester time are blocked. Only one position owned by
the strategy may be open.

The executable implementation remains the tester-only EA at
`forex-research/mt5/Experts/ForexMeanReversionScout.mq5`. The preset in this
package freezes only inputs supported by that source.

Run the evidence audit:

```powershell
python eur-usd/eurusd-phase0/run_evidence_audit.py
python eur-usd/eurusd-phase0/run_window_report.py
python -m pytest eur-usd/eurusd-phase0/tests -q
```

Independent reviewers should begin with
`EURUSD_PF_IMPROVEMENT_REVIEW_PROMPT_2026_07_23.md`.

The historical MT5 result is development evidence. This package does not
authorize a chart attachment, demo order, live order, or broker-state change.
Promotion requires a source/EX5 parity rerun and a locked prospective shadow
exam on current data.
