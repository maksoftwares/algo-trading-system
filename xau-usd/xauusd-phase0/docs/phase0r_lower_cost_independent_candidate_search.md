# Phase 0R Lower-Cost Independent Candidate Search

Last updated: 2026-06-02

Overall status: ACTIVE_RESEARCH_BACKLOG

## Purpose

Find replacement candidates that can survive the measured XAUUSD cost environment after the breakout-retest family was marked `COST_SUSPENDED_CANONICAL`.

## Hard Search Rules

| Requirement | Target |
| --- | --- |
| Decision timeframe | H1, H4, D1, or W1 preferred |
| M5 trigger | Not allowed if the candidate claims timeframe diversification |
| Expected trades/year | Materially lower than `breakout_retest` |
| Stop distance | Wide enough that measured P95 spread is <= 0.20R to 0.30R |
| Measured P95 spread assumption | 75 points minimum |
| Reporting surface | Fixed-notional R-series first |
| Registration | Pre-registered hypothesis with SHA256 lock |
| Tuning | No post-result filters or parameter rescue |

## Candidate Backlog

| Candidate family | Expected timeframe | Expected trades/year | Expected median hold | Expected median stop distance | Measured P95 cost-R target | Required data source | Hash-lock status | Falsification criteria |
| --- | --- | ---: | --- | --- | --- | --- | --- | --- |
| D1 compression to H4 expansion | D1 setup, H4 decision | 20-80 | 8-48h | >= 250 points | <= 0.30R | XAUUSD H4/D1 bars, ATR/realized-vol features | REJECTED_FIRST_PASS | Existing `d1_compression_h4_expansion_v0` was already tested and rejected; do not tune v0. |
| H4 trend continuation after D1 pullback | D1 setup, H4 decision | 20-100 | 8-72h | >= 250 points | <= 0.30R | XAUUSD H4/D1 bars, EMA/ADX/ATR features | NOT_REGISTERED | Multi-cell PF failure or concentration gate failure |
| H4/D1 volatility contraction then expansion | H4/D1 | 15-80 | 12-96h | >= 300 points | <= 0.25R | XAUUSD H4/D1 bars, range compression and ATR percentile features | HYPOTHESIS_DRAFTED_COST_PRECHECK_PASS | `hypothesis_h4_d1_volatility_contraction_expansion_v0.md` and `phase0r_cost_precheck_h4_d1_volatility_contraction_expansion_v0.md`; next step is SHA256 registration before implementation. |
| Weekly level rejection with H4 confirmation | W1 setup, H4 decision | 10-50 | 24-120h | >= 350 points | <= 0.22R | XAUUSD H4/D1/W1 bars, weekly level map | NOT_REGISTERED | Trade-count/activity failure or rejection candles do not transfer across brokers |
| Post-news delayed H1/H4 continuation | H1/H4 | 15-80 | 4-48h | >= 250 points | <= 0.30R | High-quality economic calendar, XAUUSD H1/H4 bars | DATA_SOURCE_PENDING | News timestamp/source quality insufficient, or event families do not pass fixed-notional gates |
| CME Gold CVOL/skew reversal | H4/D1 | 10-60 | 12-96h | >= 300 points | <= 0.25R | Licensed CME Gold CVOL/skew history plus XAUUSD bars | BLOCKED_DATA_SOURCE | Do not run proxy matrix; reject if licensed data is unavailable or CVOL signal fails 9-cell gates |
| Macro/intermarket stress behavior | H4/D1 | 10-80 | 12-120h | >= 300 points | <= 0.25R | Primary-quality macro/intermarket data with documented availability | DATA_SOURCE_PENDING | Reject if data coverage, alignment, or broker-transfer gates fail |

## Explicitly Avoid

```text
more M5 retest variants
more same-family round-number retests
more tight-stop intraday scalps
adding spread/session filters to rescue breakout_retest_v1.0
treating same-family variants as diversification
```

## First Research Action

`d1_compression_h4_expansion_v0` was already tested and rejected, so do not duplicate or tune it. The current fresh draft is `h4_d1_volatility_contraction_expansion_v0`, which has a measured-cost structural precheck PASS at an expected 400-point median stop. Next step: SHA256-register the hypothesis before any strategy implementation or matrix run.
