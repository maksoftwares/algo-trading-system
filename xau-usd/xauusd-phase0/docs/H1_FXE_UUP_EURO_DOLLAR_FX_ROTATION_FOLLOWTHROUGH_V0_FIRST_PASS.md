# H1 FXE/UUP Euro-Dollar FX Rotation Follow-Through v0 First Pass

Status: REJECTED_FIRST_PASS
Hypothesis: `docs/hypothesis_h1_fxe_uup_euro_dollar_fx_rotation_followthrough_v0.md`
Research hash: `8b3161dbce3dbc07b1c1dd2e549380213ece0fc8ba0234ea2fc4bd10a3886c03`
Data proxy: `data/reference/etf/fxe_uup_daily_yahoo_2015_2025.csv`
Data source: Yahoo Finance public FXE/UUP daily OHLCV proxy
Rows acquired: 2,638

## Decision

Reject v0 without tuning.

This candidate produced adequate sample size, but it failed the first hard expectancy gate. No cell reached PF >= 1.30. The only positive pocket was Pepperstone 2019-2021 near PF 1.05, which is well below the acceptance threshold and not portable across broker/time windows.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero Months | Result |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | Capital.com | best | 142 | 38.03% | 0.8600 | -5.38% | 8.94% | 1 | FAIL |
| 2 | Capital.com | median | 142 | 38.03% | 0.8600 | -5.38% | 8.94% | 1 | FAIL |
| 3 | Capital.com | p95 | 142 | 37.32% | 0.8325 | -6.46% | 9.31% | 1 | FAIL |
| 4 | Pepperstone | best | 145 | 42.07% | 1.0510 | +1.94% | 4.62% | 0 | FAIL |
| 5 | Pepperstone | median | 145 | 42.07% | 1.0510 | +1.94% | 4.62% | 0 | FAIL |
| 6 | Pepperstone | p95 | 145 | 42.07% | 1.0221 | +0.84% | 5.03% | 0 | FAIL |
| 7 | Dukascopy | best | 173 | 38.73% | 0.8708 | -5.92% | 11.01% | 0 | FAIL |
| 8 | Dukascopy | median | 173 | 38.73% | 0.8439 | -7.09% | 11.65% | 0 | FAIL |
| 9 | Dukascopy | p95 | 173 | 37.57% | 0.7923 | -9.45% | 13.07% | 0 | FAIL |

## Gate Read

| Gate | Observed | Required | Status |
|---|---:|---:|---|
| Matrix PF cells | 0/9 | >= 7/9 | FAIL |
| Trade-count cells | 9/9 | 9/9 with >= 40 trades | PASS |
| Cross-broker portability | Capital.com negative, Pepperstone weak positive, Dukascopy negative | Robust across windows | FAIL |
| Cost sensitivity | P95 cost weakens already sub-threshold PF | P95 should not break the edge | FAIL |

## Interpretation

FXE/UUP euro-dollar rotation did not produce durable XAU follow-through. The result is directionally consistent with the previous FXY/UUP and FXF/UUP failures: public daily FX ETF rotation can provide enough events, but the signal is not strong enough after XAU execution costs and broker/time-window variation.

## Next Action

Do not tune this v0 candidate. Continue the independent search in a genuinely new data class or mechanism.
