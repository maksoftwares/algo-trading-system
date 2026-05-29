# H1 FXA/UUP Aussie-Dollar FX Rotation Follow-Through v0 First Pass

Status: REJECTED_FIRST_PASS
Hypothesis: `docs/hypothesis_h1_fxa_uup_aussie_dollar_fx_rotation_followthrough_v0.md`
Research hash: `136d07a2debfb1648583728099b6419f888fb42fe6ebe5231b90ba3376801e29`
Data proxy: `data/reference/etf/fxa_uup_daily_yahoo_2015_2025.csv`
Data source: Yahoo Finance public FXA/UUP daily OHLCV proxy
Rows acquired: 2,638

## Decision

Reject v0 without tuning.

This candidate had enough sample size in every cell and showed a weak positive pocket in Capital.com/Pepperstone, but it failed the hard matrix expectancy gate with 0/9 PF cells >= 1.30. Dukascopy 2022-2024 was flat-to-negative and P95 costs pushed the latest window below 1.0 PF.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero Months | Result |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | Capital.com | best | 164 | 44.51% | 1.0755 | +3.15% | 6.08% | 1 | FAIL |
| 2 | Capital.com | median | 164 | 44.51% | 1.0755 | +3.15% | 6.08% | 1 | FAIL |
| 3 | Capital.com | p95 | 164 | 43.90% | 1.0476 | +1.99% | 6.28% | 1 | FAIL |
| 4 | Pepperstone | best | 152 | 45.39% | 1.1996 | +8.04% | 4.16% | 1 | FAIL |
| 5 | Pepperstone | median | 152 | 45.39% | 1.1996 | +8.04% | 4.16% | 1 | FAIL |
| 6 | Pepperstone | p95 | 152 | 45.39% | 1.1777 | +7.19% | 4.26% | 1 | FAIL |
| 7 | Dukascopy | best | 175 | 43.43% | 1.0185 | +0.83% | 7.44% | 1 | FAIL |
| 8 | Dukascopy | median | 175 | 42.86% | 0.9943 | -0.25% | 7.78% | 1 | FAIL |
| 9 | Dukascopy | p95 | 175 | 42.29% | 0.9436 | -2.51% | 8.84% | 1 | FAIL |

## Gate Read

| Gate | Observed | Required | Status |
|---|---:|---:|---|
| Matrix PF cells | 0/9 | >= 7/9 | FAIL |
| Trade-count cells | 9/9 | 9/9 with >= 40 trades | PASS |
| Cross-broker portability | Capital.com/Pepperstone weak, Dukascopy flat-to-negative | Robust across windows | FAIL |
| Cost sensitivity | P95 weakens already sub-threshold cells | P95 should not break the edge | FAIL |

## Interpretation

The Australian-dollar ETF rotation signal is more constructive than the FXE/UUP and CYB/UUP attempts, but not close enough to Phase 0 approval. The PF profile is still a weak intermarket drift, not a durable EA candidate.

## Next Action

Do not tune this v0 candidate. Continue the independent search in a different mechanism or a higher-quality data class.
