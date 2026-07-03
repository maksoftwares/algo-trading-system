# Claude Review Prompt — A1 Momentum Broad Portfolio Search

Boundary: offline review only. Do not touch MT5 runtime, charts, presets, orders, positions, or demo/live account state.

The owner clarified that the target is not a sparse “pretty stats” EA. We need:

```text
multiple trades on active days
win rate above 50%
positive net result
enough active days to support a daily-profit style system
no accidental duplicate-stacking illusion
```

Codex ran a broad offline portfolio search across exact four-year MT5 Strategy Tester trade CSVs. Review these files:

```text
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_BROAD_PORTFOLIO_SEARCH_2026_07_02.md
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_BROAD_PORTFOLIO_SEARCH_2026_07_02.json
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_BROAD_PORTFOLIO_SEARCH_2026_07_02.csv
xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_BROAD_PORTFOLIO_SEARCH_VERDICT_2026_07_02.md
xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_CLEAN_LONG_SHORT_PORTFOLIO_FORWARD_DRAFT_2026_07_02.md
xau-usd/xauusd-phase1/scripts/attach_a1_xau_m5_momentum_continuation.py
```

Important: Codex added a duplicate-like metric. Trades are duplicate-like if two different variants fire the same direction in the same minute. High duplicate-like percentage may mean accidental leverage rather than a clean portfolio.

## Candidate A: strongest headline numbers

```text
rr_2p0_long_only_h1_h4_atr15_no0910
+
v6_freq_v4_rr0p7_max2
```

Metrics:

```text
Trades: 2009
Win rate: 56.65%
Net: +2884.32 USD
PF: 1.49
Active days: 435
Trades / active day: 4.62
Positive / negative months: 36 / 11
Top-25 removed: +1964.06
Max closed DD: 131.65
Duplicate-like trade pct: 26.28%
```

Codex concern: strong, but includes max2 exposure and meaningful overlap. It may be controlled scaling rather than a clean independent portfolio.

## Candidate B: best clean no-duplicate candidate

```text
v5_v4_move12
+
freq_h1_h4_short_rr0p7_v1_core_1_5_15_19
```

Metrics:

```text
Trades: 1317
Win rate: 64.54%
Net: +1139.94 USD
PF: 1.43
Active days: 535
Trades / active day: 2.46
Multi-trade days: 321
Positive / negative months: 37 / 11
Worst month: -22.58
Top-25 removed: +824.07
Max closed DD: 59.38
Duplicate-like trade pct: 0.00%
```

Mechanics:

Long lane `v5_v4_move12`:

```text
Signal: break-and-run
Direction: LONG only
H1+H4 EMA20/50 alignment
RR: 0.70R
Cost cap: 0.05R
Blocked hours: 2,9,10,11,12,13,17,19,21,23
Min 3-bar move: 1.20 ATR
Max trades/day: 12
Cooldown: 5 minutes
```

Short lane `freq_h1_h4_short_rr0p7_v1_core_1_5_15_19`:

```text
Signal: break-and-run
Direction: SHORT only
H1+H4 EMA20/50 alignment
RR: 0.70R
Cost cap: 0.05R
Allowed hours: 1,2,3,4,5,15,19
Max trades/day: 12
Cooldown: 5 minutes
```

Questions:

1. Independently recompute Candidate A and Candidate B from the source CSVs.
2. Is Candidate A valid controlled scaling, or should it be rejected/penalized for overlap?
3. Is Candidate B the better forward-test candidate because it has 0% duplicate-like overlap and low drawdown?
4. Are the hour masks too overfit, or acceptable because they survive four years, 37 positive months, and top-winner removal?
5. What forward-test spec would you recommend if we demo-test Candidate B?
6. Should the long and short lanes use separate magic numbers and separate kill rules, or one combined family kill rule?
7. What minimum forward sample is needed before judging?
8. What would make you reject both and continue searching?
9. Codex prepared, but did not execute, attach variants `clean_long_v5_move12` and `clean_short_core`. Are the proposed magics `932210` and `932211`, comments, hash-locked shared draft, and separate lane identity acceptable?

Return one of:

```text
ENDORSE_CANDIDATE_B
ENDORSE_CANDIDATE_A_WITH_STACKING_GUARDS
REVISE
REJECT
```

Please be rigorous but constructive. The owner wants a system that actually trades often enough, and Candidate B appears to be the cleanest no-duplicate answer so far.
