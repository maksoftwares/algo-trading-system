# Forex Demo Readiness V1 — Independent Audit

Verdict: **`RESEARCH_WATCHLIST`**

The legacy `CONTROLLED_SHADOW_DEMO_READY` label is not substantiated by the
evidence required for a shared-account controlled shadow or demo trial. The
historical result remains a positive research lead, but it is downgraded to
`RESEARCH_WATCHLIST` until the blockers below are closed prospectively.

## Reproduced headline

| Metric | Reproduced |
|---|---:|
| Trades | 697 |
| Declared trades / active broker date | 1.1333 |
| Win rate | 57.82% |
| Net P&L | $119.42 |
| Profit factor | 1.3075 |
| Average trade | $0.1713 |
| Maximum closed-trade drawdown | $28.45 |
| Worst day | $-8.77 |
| Worst month | $-7.76 |
| Positive active months | 64.00% |
| PF after removing top 5% | 1.0191 |

## Material findings

- The legacy arithmetic is reproducible: 697 trades, $119.42 net, PF 1.3075, and 58 cross-sleeve time overlaps.
- The M15 standalone report itself is PF 1.29; the combined PF clears 1.30 only after adding the sparse H1 control.
- The trend overlay is implemented as `requested_lots += 0.01` on the same entry and exit, not as an independent candidate.
- The claimed maximum of two concurrent positions assumes a hedging account, but the packet does not attest the account margin mode.
- The reports were produced separately, so their concatenation cannot establish shared-account fills, ownership, margin, or equity drawdown.
- The existing test suite passes because it asserts the old adaptive label and shallow source-string guards; it does not test the missing portfolio controls.
- October 2024 remains explicitly quarantined for EURUSD and USDJPY at 2024-10-09 23:00 through 2024-10-10 01:00 UTC.

## Overlay decomposition

| Component | Trades | Net | PF |
|---|---:|---:|---:|
| M15 reported | 635 | $96.57 | 1.2864 |
| M15 normalized 0.01-lot core | 635 | $73.00 | 1.2533 |
| Same-entry incremental overlay | 120 | $23.57 | 1.4805 |

The overlay is a risk multiplier on the same opportunity. It is not a second
specialist, candidate, position owner, or independently timed exposure.

## Specialist / sleeve evidence

| Pair | Direction | Session / regime ownership | Sleeve | Trades | Net | PF |
|---|---|---|---|---:|---:|---:|
| EURUSD | Long | M15 all-day RSI extreme; H4 trend only changes size | M15 core + overlay | 635 | $96.57 | 1.2864 |
| EURUSD | Short | Asia/London, completed-H4 chop | H1 control | 62 | $22.85 | 1.4466 |

No GBPUSD, USDJPY, cross-pair, or other Forex specialist is present in the
packaged portfolio. Pair diversification is therefore zero.

## Recent windows

| Window | Trades | Net | PF | Closed DD |
|---|---:|---:|---:|---:|
| last 3 months | 101 | $6.64 | 1.1299 | $11.05 |
| last 6 months | 214 | $13.45 | 1.1121 | $12.93 |
| last 12 months | 399 | $-0.48 | 0.9980 | $28.45 |
| last 24 months | 697 | $119.42 | 1.3075 | $28.45 |

Five-year packaged MT5 portfolio evidence is unavailable.

## Cost stress

| Extra round-trip cost | Net | PF |
|---|---:|---:|
| +0.5 pip | $78.57 | 1.1939 |
| +1.0 pip | $37.72 | 1.0893 |

## Sequence-preserving Monte Carlo

- Method: moving-block bootstrap, 10000 paths, 20-trade blocks, seed `20260727`.
- Median maximum drawdown: $19.44.
- 95th / 99th percentile maximum drawdown: $32.38 / $40.93.
- Conditional risk of ruin / 10% drawdown: 0.00% / 0.00%.
- This resamples adaptively selected history and is not independent evidence.

## New bounded research

No new strategy outcome was opened. Eleven prior mechanism classes are already
closed, AUDUSD has no local intraday cache, and no causal official
event-surprise dataset with release-vintage controls is present. Retesting a
closed price-only or microstructure family would create more selection debt.
The pair-by-pair cache snapshot is in `DATA_COVERAGE_MANIFEST.json`; the
append-only hypothesis history is in `PRIOR_TRIAL_REGISTRY.csv`.

## Decision gates

| Gate | Status | Evidence |
|---|---|---|
| frequency at least 1 per active trading day | UNVERIFIED | 1.1333 uses a hard-coded 615-date denominator; the hashed broker M15 source is absent. |
| base profit factor at least 1 30 | PASS | Report-derived combined PF 1.3075. |
| stressed profit factor at least 1 15 | PASS | PF 1.1939 after +0.5 pip round-trip per trade. |
| hard 1pip cost stress profit factor at least 1 15 | FAIL | PF 1.0893 after +1.0 pip round-trip per trade. |
| cost stressed top 5pct removed profit factor at least 1 | FAIL | PF 0.9235 after +0.5 pip cost and removal of the top 5% of trades. |
| positive expected value per trade | PASS | Average $0.1713 per completed trade. |
| trailing 12 month pf at least 1 15 and positive | FAIL | PF 0.9980, net $-0.48. |
| two chronological validation windows profitable | FAIL | The packaged MT5 portfolio has one adaptive 2024-2026 interval and no two untouched validation windows. |
| positive active month share at least 55pct | PASS | 64.00% of active months positive. |
| top 5pct winners removed pf at least 1 | PASS | PF 1.0191; only 0.019 above break-even. |
| no single pair direction or specialist hides failure | FAIL | All 697 trades are EURUSD; 635/697 are one long-only M15 source and 120 use same-entry lot doubling. |
| base floating equity drawdown at most 5pct | UNVERIFIED | No combined-account equity path. Standalone maxima sum to a conservative $54.21 bound only. |
| stressed floating equity drawdown at most 10pct | UNVERIFIED | No synchronized bid/ask position path or combined MT5 report exists. |
| monte carlo risk of ruin below 1pct | PASS | Conditional block-bootstrap ruin 0.00%; does not repair adaptive selection. |
| no duplicate or same opportunity stacking | FAIL | The H4 trend overlay adds 0.01 lot to the identical M15 entry/SL/TP rather than owning a new opportunity. |
| source ex5 preset report build chain locked | FAIL | Files are hashable, but no compiler attestation proves each EX5 was built from the exact hashed source; the control chain is absent from the legacy verdict. |
| exact combined mt5 strategy tester parity | FAIL | Only two standalone reports were arithmetically concatenated; no same-account combined Strategy Tester run exists. |
| fail closed demo only account and server guard | FAIL | The control EA does not reject non-demo accounts in OnInit and its time-exit close path has no demo-mode check. |
| fixed initial 0 01 lot research sizing | FAIL | 120 M15 trades used 0.02 lots through the same-entry trend overlay. |

## Remaining blockers

- Adaptive selection contamination: the only packaged MT5 interval was inspected before the fallback and gates were declared.
- Missing Capital.com M15 broker-bar source prevents source reproduction and active-day denominator verification.
- No combined same-account MT5 run, account margin-mode attestation, or exact cross-sleeve fill/ownership parity.
- No synchronized combined floating-equity reconstruction or stressed floating drawdown.
- Trend overlay is same-opportunity lot doubling, not independent specialist exposure.
- No shared-account daily/rolling loss, margin, floating drawdown, USD exposure, concurrency, or kill-switch engine.
- Control EA live-safety and magic-owned position-selection defects.
- No exact source-to-EX5 compiler attestation for both EAs and no complete locked chain in the legacy verdict.
- Portfolio is single-pair and overwhelmingly one-direction/one-source; it is not the requested diversified Forex architecture.
- No genuinely untouched historical holdout remains; prospective evidence must be locked before observation.

## Reproduction

```powershell
python forex/forex-demo-readiness-v1/audit_demo_readiness.py
python -m pytest forex/forex-demo-readiness-v1/tests -q
```

No terminal, account, chart, order, or broker runtime was touched.
