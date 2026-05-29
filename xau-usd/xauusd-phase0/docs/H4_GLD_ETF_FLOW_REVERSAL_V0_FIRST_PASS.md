# H4 GLD ETF Flow Reversal v0 First Pass

Status: REJECTED_FIRST_PASS

Generated at UTC: 2026-05-29

## Boundary

This was a research-candidate first pass only. It does not approve an EA, does not add any Phase 1 observer, and does not authorize decile, multisymbol, adversarial, paper-mode, or live execution work for this candidate.

## Data Class

This candidate used a new public data class for this repo: GLD ETF daily OHLCV participation.

The local source file is:

```text
data/reference/etf/gld_daily_yahoo_2015_2025.csv
```

It was acquired from Yahoo Finance chart API symbol `GLD`. This is a public ETF flow proxy, not primary COMEX/CME order-flow, not broker fill evidence, and not live execution evidence.

## Hypothesis Lock

| Item | Value |
| --- | --- |
| Expert | `h4_gld_etf_flow_reversal_v0` |
| Hypothesis file | `docs/hypothesis_h4_gld_etf_flow_reversal_v0.md` |
| SHA256 | `2aa540060366b2363dcc3c5e4a3925916320f571d8b70b2cda7a574318ec72dd` |
| Synthetic smoke | PASS |
| Result-producing command | `phase0 run-research-matrix --expert h4_gld_etf_flow_reversal_v0 --hypothesis-file docs/hypothesis_h4_gld_etf_flow_reversal_v0.md` |

## Matrix Summary

| Cell | Broker | Cost | Trades | PF | Return % | Win Rate | Max DD % |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 29 | 1.5070 | 2.5276 | 55.17% | 1.5097 |
| 2 | capital_com | median | 29 | 1.5070 | 2.5276 | 55.17% | 1.5097 |
| 3 | capital_com | p95 | 29 | 1.4885 | 2.4532 | 55.17% | 1.5305 |
| 4 | pepperstone | best_case | 39 | 1.4945 | 3.6574 | 51.28% | 3.3891 |
| 5 | pepperstone | median | 39 | 1.4945 | 3.6574 | 51.28% | 3.3891 |
| 6 | pepperstone | p95 | 39 | 1.4851 | 3.5998 | 51.28% | 3.4011 |
| 7 | dukascopy | best_case | 36 | 1.5478 | 3.4186 | 50.00% | 3.9368 |
| 8 | dukascopy | median | 36 | 1.5310 | 3.3356 | 50.00% | 3.9800 |
| 9 | dukascopy | p95 | 36 | 1.5210 | 3.2640 | 50.00% | 3.9739 |

## Gate Read

| Gate | Result |
| --- | --- |
| PF >= 1.30 in at least 7/9 cells | PASS: 9/9 cells |
| Minimum 40 trades per cell | FAIL: 0/9 cells reached 40 trades; best cells had 39 |
| Max zero-trade months <= 3 | FAIL: observed 4-6 consecutive zero-trade months |
| Single-trade concentration <= 10% | FAIL: largest trade contribution was 20.76%-30.13% of net PnL |
| Top-5 concentration <= 40% | FAIL: top five trades contributed 101.22%-143.75% of net PnL |
| Cost sensitivity | PASS by first-pass PF stability: P95 cells remained above 1.30 |
| Next validation | STOP: no deciles, multisymbol, intrabar, or Gate 9 for v0 |

## Decision

Reject v0 without tuning.

This is the strongest independent first-pass lead found so far because all 9 cells cleared PF 1.30 and P95 cost remained robust. It is still not an approved expert because the trade count, zero-activity, and concentration gates failed. Any attempt to broaden the sample must be a new pre-registered versioned hypothesis, not an edit to v0.
