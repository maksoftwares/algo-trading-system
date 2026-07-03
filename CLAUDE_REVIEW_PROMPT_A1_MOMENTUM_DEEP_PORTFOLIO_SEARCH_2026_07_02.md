# Claude Review Prompt - A1 XAU M5 Momentum Deep Portfolio Search

Please independently review the new A1 XAU M5 momentum deep portfolio search.

Boundary: offline review only. Do not touch MT5 runtime, presets, charts, orders, or positions.

## Owner requirement

The owner rejected sparse strategies. A primary strategy must create enough intraday opportunity:

- multiple trades on active days,
- win rate above 50%,
- positive net result,
- no fake improvement from duplicate stacking,
- realistic enough cadence for daily profit objectives.

Sparse RR2-style lanes with only a few trades per month should be treated as support evidence only, not primary candidates.

## Files to review

Primary report:

```text
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_SEARCH_2026_07_02.md
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_SEARCH_2026_07_02.json
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_SEARCH_2026_07_02.csv
```

Stress report:

```text
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_STRESS_2026_07_02.md
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_STRESS_2026_07_02.json
```

Verdict:

```text
xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_SEARCH_VERDICT_2026_07_02.md
xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_FORWARD_DRAFT_2026_07_02.md
```

Script:

```text
xau-usd/xauusd-phase1/scripts/analyze_a1_momentum_deep_portfolio_search.py
```

Related context:

```text
xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_FREQUENCY_REQUIREMENT_VERDICT_2026_07_02.md
xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_BROAD_PORTFOLIO_SEARCH_VERDICT_2026_07_02.md
xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_CLEAN_LONG_SHORT_PORTFOLIO_FORWARD_DRAFT_2026_07_02.md
status_summary.md
```

## Candidate to verify

The best low-overlap frequency portfolio is:

```text
v6_freq_v4_rr0p7_max2
+
v13_ema_trend_h1h4_both_rr0p6_no_weak_short_no_long_morning
+
freq_h1_h4_short_rr0p7_v1_core_1_5_15_19
```

Reported metrics:

```text
Raw trades: 3107
Deduped trades: 3058
Win rate: 65.73%
Net USD: +2156.21
PF: 1.34
Active days: 718
Trades / active day: 4.26
Positive months: 37
Negative months: 11
Worst month: -37.02
Top 25 winners removed: +1835.20
Max closed DD: 89.04
Raw duplicate-like trade pct: 3.15%
Deduped trades removed: 49
```

## What I need from you

1. Independently recompute the candidate from the underlying trade CSVs, not only from the report.
2. Verify that the deterministic same-minute same-direction de-duplication is reasonable and not using hindsight.
3. Challenge whether this is genuinely better than the cleaner two-lane candidate:

```text
v5_v4_move12
+
freq_h1_h4_short_rr0p7_v1_night_early
```

4. Stress test the candidate:
   - remove top 10 / top 25 / top 50 winners,
   - monthly split,
   - yearly split,
   - worst 5 days removed and best 5 days removed,
   - day-of-week and hour/session split,
   - LONG vs SHORT contribution,
   - duplicate-like overlap by member,
   - whether one member is doing all the work.
5. Pay special attention to the existing stress-test caveat:
   - 2022-07 to 2024-06 is positive but weaker: 1544 trades, 63.08% WR, +374.00, PF 1.15.
   - 2024-07 to 2026-06 is stronger: 1514 trades, 68.43% WR, +1782.21, PF 1.46.
   Decide whether the older-window weakness still permits a minimum-lot forward test.
6. Decide whether this is:
   - `ENDORSE_FOR_MINIMUM_LOT_FORWARD_TEST`,
   - `REVISE_BEFORE_FORWARD_TEST`,
   - or `REJECT_AS_SELECTED/STACKED/UNSTABLE`.
7. If endorsed, propose the exact frozen forward-demo spec:
   - which lanes,
   - separate magic numbers,
   - lot size,
   - kill rules,
   - sample size,
   - pass/fail thresholds,
   - no-tuning rule.

Important: be rigorous, but do not reject merely because the candidate came from a search. The owner explicitly asked us to search permutations. Reject only if the evidence fails robustness, relies on stacking, or does not satisfy the frequency-plus-quality goal.
