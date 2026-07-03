# A1 XAU M5 Momentum Robust Repair Forward Draft - 2026-07-02

Status: REVIEW_DRAFT_NOT_ATTACHED

Boundary: demo-only forward-test draft. No canonical Phase 2 approval, no live trading, no real capital, and no MT5 runtime attachment is authorized by this document alone.

## Purpose

The robust XAU M5 portfolio matches the owner's requirement better than sparse RR2 lanes: it trades frequently, keeps win rate above 50%, and remains positive after de-duplication. Its main weakness is thin profitability in 2022-H2.

This repair draft applies the smallest useful repair found by the diagnostic search:

```text
Block server hour 18 only for v13_ema_trend_h1h4_long_rr0p6_no_morning.
```

No other lane is changed.

## Candidate

```text
v6_freq_v4_rr0p7_max2
+
v13_ema_trend_h1h4_long_rr0p6_no_morning with hour 18 blocked
+
freq_h1_h4_short_rr0p7_v1_night_early
```

## Evidence

Source report:

- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_REPAIR_DIAGNOSTIC_2026_07_02.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_ROBUST_REPAIR_WALKFORWARD_2026_07_02.md`

| Metric | Baseline robust | Repaired one-filter |
|---|---:|---:|
| Trades | 2503 | 2443 |
| Win rate | 66.40% | 66.56% |
| Net USD | +1933.57 | +1944.34 |
| Profit factor | 1.37 | 1.38 |
| Active days | 603 | 600 |
| Trades / active day | 4.15 | 4.07 |
| Positive / negative months | 37 / 11 | 37 / 11 |
| Worst month USD | -21.84 | -21.84 |
| Top 25 winners removed | +1611.51 | +1622.28 |
| Top 100 winners removed | +839.77 | +852.68 |
| Max closed DD USD | 93.43 | 93.43 |
| 2022-H2 net / PF | +32.38 / 1.07 | +46.68 / 1.10 |
| Older split net / PF | +441.29 / 1.24 | +473.75 / 1.27 |
| Newer split net / PF | +1492.28 / 1.44 | +1470.59 / 1.44 |

Interpretation: this repair improves the weak 2022-H2 window and older split while preserving overall frequency. The improvement is modest, but it is explainable and low-complexity.

Walk-forward frequency check for the repaired candidate:

| Check | Result |
|---|---:|
| Half-year buckets positive | 8 / 8 |
| Quarter buckets positive | 15 / 16 |
| Weakest half-year | 2022-H2: +46.68 USD / PF 1.10 / 291 trades |
| Weakest quarter | 2022-Q3: -15.01 USD / PF 0.91 / 103 trades |
| Rolling 250-trade windows | All non-negative, weakest +0.66 USD / PF 1.00 |
| Trades / active day | 4.07 |

Frequency conclusion: this candidate fits the owner's high-activity requirement far better than the sparse RR2 lane. It still needs review because the 2022-Q3 and 2024-Q4 style weak windows show the edge can flatten, but it is not a two-trades-per-month system.

## Lane 1 - V6 Max2 Long

Magic: 932240

Order comment: `A1_XAU_M5_MOM_RP_L1`

Run id: `A1_XAU_M5_MOMENTUM_ROBUST_REPAIR_V6_MAX2_LONG_20260702`

Inputs:

| Input | Value |
|---|---|
| Symbol | XAUUSD |
| Timeframe | M5 |
| Direction | LONG only |
| Signal mode | Break-and-run default |
| H1 trend filter | true |
| H1 min slope points | 0 |
| H4 trend filter | true |
| H4 min slope points | 0 |
| Risk reward | 0.70 |
| Max estimated cost R | 0.05 |
| Blocked server hours | 2,9,10,11,12,13,17,19,21,23 |
| One position per magic | false |
| Max open positions per magic | 2 |
| Max trades per day | 20 |
| Cooldown minutes | 3 |

## Lane 2 - V13 Long No Morning, Hour 18 Repaired

Magic: 932241

Order comment: `A1_XAU_M5_MOM_RP_L2`

Run id: `A1_XAU_M5_MOMENTUM_ROBUST_REPAIR_V13_LONG_NO_MORNING_NO18_20260702`

Inputs:

| Input | Value |
|---|---|
| Symbol | XAUUSD |
| Timeframe | M5 |
| Direction | LONG only |
| Signal mode | M5 EMA trend continuation |
| H1 trend filter | true |
| H1 min slope points | 0 |
| H4 trend filter | true |
| H4 min slope points | 0 |
| Risk reward | 0.60 |
| Max estimated cost R | 0.05 |
| Blocked server hours | 0,2,4,9,10,11,12,16,18,19,20 |
| Blocked long server hours | 6,7,8 |
| M5 EMA fast / slow | 8 / 21 |
| M5 slope bars | 3 |
| M5 min slope ATR | 0.03 |
| M5 max distance ATR | 1.20 |
| Min range ATR | 0.35 |
| Min body fraction | 0.30 |
| Long close location | 0.58 |
| Min 3-bar move ATR | 0.10 |
| Max trades per day | 24 |
| Cooldown minutes | 0 |

## Lane 3 - Short Night/Early

Magic: 932242

Order comment: `A1_XAU_M5_MOM_RP_S`

Run id: `A1_XAU_M5_MOMENTUM_ROBUST_REPAIR_SHORT_NIGHT_EARLY_20260702`

Inputs:

| Input | Value |
|---|---|
| Symbol | XAUUSD |
| Timeframe | M5 |
| Direction | SHORT only |
| Signal mode | Break-and-run default |
| H1 trend filter | true |
| H1 min slope points | 0 |
| H4 trend filter | true |
| H4 min slope points | 0 |
| Risk reward | 0.70 |
| Max estimated cost R | 0.05 |
| Blocked server hours | 0,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23 |
| Max trades per day | 12 |
| Cooldown minutes | 5 |

## Forward-Test Rules

- Account: A1 demo account only unless owner explicitly approves another account.
- Lot: 0.01 fixed.
- Broker action: disabled until owner approval and reviewer signoff.
- No parameter changes during the forward test.
- No extra XAU momentum lanes added during the first scoring window.
- Daily and weekly reports must separate the three magics.
- Duplicate scoring must use same-minute same-direction de-duplication.

## Promotion Bar

- At least 300 closed forward trades.
- At least 6 trading weeks.
- Portfolio WR >= 55%.
- Portfolio PF >= 1.25.
- Portfolio net positive after removing top 10 winners.
- No single day contributes more than 30% of net profit.
- No lane creates a persistent negative drag for two consecutive weeks.

## Kill Rules

- Portfolio net negative after 150 trades.
- Rolling 100-trade PF below 0.90.
- Closed drawdown exceeds 150 USD at 0.01 lot.
- Any safety/broker-action mismatch appears.
- Runtime identity differs from the magics/comments in this document.

## Current Decision

This package is `ROBUST_REPAIR_REVIEW_CANDIDATE_NOT_ATTACHED`.

It is the best current repair candidate because it improves the known weak window without materially reducing trade frequency. It still needs independent review before demo attachment.
