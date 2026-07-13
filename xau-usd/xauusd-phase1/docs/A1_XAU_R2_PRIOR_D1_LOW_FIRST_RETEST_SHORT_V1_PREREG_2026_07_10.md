# A1 XAU R2 Prior-D1-Low First-Retest Short V1 Preregistration

Date: 2026-07-10

## Purpose

Test one materially new strict-R2 short family without tuning the frozen R2 V1/V2/V4 controls.

The frozen controls show two non-durable paths:

- the scale-normalized M5 impulse/retest has broad sample but low full-window win rate and weak 2022-2024 durability;
- the V4 absolute ATR floor raises recent quality by selecting almost exclusively 2026 high-volatility bars.

This source therefore uses a completed higher-timeframe structural level and distribution-normalized volatility. It is a new family, not an R2 V5 filter pass.

## Runtime Boundary

Research-only exact MT5 Strategy Tester work. No demo/live attachment, chart, preset, profile, account, position, order, registry, or broker state change is authorized.

Do not launch the historical test until this preregistration and the runner's static checks have been reviewed.

## Frozen Source Identity

- Source: `r2_prior_d1_low_first_retest_short_v1`
- Variant: `r2_pdl_first_retest_structural_v1`
- Signal mode: `SIGNAL_R2_PRIOR_D1_LOW_FIRST_RETEST_SHORT = 22`
- Direction: short only
- Native router: strict R2 downtrend only
- Exactly one parameter cell; no grid or sensitivity variants

## Causal Signal

Every decision uses completed bars only.

1. Use the previous completed D1 low as the structural support level.
2. Arm a break only after a completed H1 bar:
   - is bearish;
   - closes at least `0.10 * H1 ATR(14)` below that D1 low;
   - has range at least `1.00 * H1 ATR(14)`;
   - has body/range at least `0.50`;
   - closes in the bottom `0.25` of its range;
   - has H1 ATR(14) percentile from `40.00` through `90.00`, inclusive, over 480 completed H1 observations.
3. Observe only the next eight completed M15 bars after the H1 break closes.
4. A retest must reach at least `D1 low - 0.25 * M15 ATR(14)`.
5. Invalidate the break if any completed M15 close is above `D1 low + 0.10 * H1 ATR(14)`.
6. The first qualifying rejection must:
   - be bearish;
   - close at least `0.10 * M15 ATR(14)` below the D1 low;
   - have body/range at least `0.50`;
   - close in the bottom `0.25` of its range.
7. Stop above the highest completed M15 high since the break plus `0.20 * M15 ATR(14)`.
8. Block the opportunity if stop distance exceeds `1.00 * H1 ATR(14)`.
9. Consume the break after the first qualifying rejection, including when a later execution/risk guard blocks it. No retry or second entry from the same break.

The 40th/90th percentile bounds are fixed distribution bands: below the 40th percentile lacks participation; above the 90th percentile is a local volatility tail. They are not selected from this source's outcomes.

## Frozen Tester Inputs

| Input | Value |
| --- | ---: |
| `InpSignalMode` | `22` |
| `InpRegimeRouterMode` | `2` |
| `InpDirectionMode` | `2` |
| `InpRiskReward` | `2.00` |
| `InpR2PdlAtrPeriod` | `14` |
| `InpR2PdlH1AtrPercentileLookback` | `480` |
| `InpR2PdlH1AtrPercentileMin` | `40.00` |
| `InpR2PdlH1AtrPercentileMax` | `90.00` |
| `InpR2PdlBreakMarginH1Atr` | `0.10` |
| `InpR2PdlBreakMinRangeH1Atr` | `1.00` |
| `InpR2PdlBreakMinBodyFraction` | `0.50` |
| `InpR2PdlBreakCloseLocationMax` | `0.25` |
| `InpR2PdlRetestWindowM15Bars` | `8` |
| `InpR2PdlRetestTouchM15Atr` | `0.25` |
| `InpR2PdlInvalidReclaimH1Atr` | `0.10` |
| `InpR2PdlRejectDistanceM15Atr` | `0.10` |
| `InpR2PdlRejectMinBodyFraction` | `0.50` |
| `InpR2PdlRejectCloseLocationMax` | `0.25` |
| `InpR2PdlStopBufferM15Atr` | `0.20` |
| `InpR2PdlMaxStopH1Atr` | `1.00` |
| `InpMinAtrAbsoluteForEntry` | `0.00` |
| `InpStopFloorPoints` | `0` |
| `InpStopCeilingPoints` | `0` |
| `InpStopCapPoints` | `0` |
| `InpMaxEstimatedCostR` | `0.10` |
| `InpUseRiskNormalizedLots` | `true` |
| `InpRiskAmountUsd` | `50.00` |
| `InpMaxRiskLots` | `0.10` |
| `InpRejectRiskOvershootEnabled` | `true` |
| `InpMaxRiskOvershootPct` | `10.00` |
| `InpOnePositionPerMagic` | `true` |
| `InpMaxTradesPerDay` | `0` |
| `InpCooldownMinutes` | `0` |
| `InpUseDirectionalSessionFilter` | `false` |
| all blocked-hour/day CSV inputs | empty |
| profit protection / partial / split entry | disabled |

Tester deposit is `10000` USD. Intended risk is `50` USD per trade. The default-off risk overshoot guard blocks if symbol-volume normalization produces actual stop risk above `55` USD.

## Evidence Partitions

The one exact run covers `2022.07.01 -> 2026.06.30`, but the report must keep these partitions separate:

- development chronology: `2022.07.01 -> 2023.12.31`;
- locked replication chronology: `2024.01.01 -> 2026.06.30`;
- causal downtrend episodes: 2022-07-01 through 2022-11-04, 2023-10-02 through 2023-10-13, and native-R2 entries from 2026-03-01 through 2026-06-30.

Existing Capital.com and Dukascopy M15/H1/D1 bars may be used for signal-portability checks over the 2016 Q4, 2018 Q3, and 2021 March bear episodes, but those are not exact-MT5 execution evidence. Only post-2026-07 forward shadow evidence is genuinely untouched.

## Standalone Gates

All core gates must pass before any portfolio recomposition:

- at least 80 exact trades overall and at least 20 in the locked replication chronology;
- WR >= 50.00%;
- average win/loss >= 1.90;
- PF >= 2.00;
- stress PF after -0.30 USD/ticket >= 1.90 and stress net > 0;
- locked replication net > 0 and PF >= 1.50;
- at least two of the three causal downtrend episodes net-positive;
- no episode contributes more than 60% of total positive net;
- native accepted-entry regime purity is 100% `downtrend`;
- max closed drawdown <= 12R and exact-MT5 max equity drawdown <= 15R;
- longest losing streak <= 8;
- net after removing the ten largest wins > 0;
- net after removing the three best entry days > 0;
- best-month share <= 30%;
- same-direction entry overlap within 15 minutes of every frozen R2 V1/V2/V4 control <= 30%.

If any core gate fails, keep the result research-only and do not tune thresholds, add a session mask, or combine it with R1.

## Required Audit Semantics

For this signal mode, the existing signal log fields are intentionally mapped as follows:

- `recent_high`: frozen prior-D1-low anchor;
- `recent_low`: completed H1 break close;
- OHLC/body/close-location/ATR: completed M15 rejection bar;
- `three_bar_move_atr`: H1 ATR percentile divided by 100;
- `break_distance_atr`: rejection close distance below the anchor divided by H1 ATR;
- signal reason suffix: native regime state at the rejection decision.

Report all guard counts, including `r2_pdl_stop_h1_atr_exceeded` and `risk_amount_overshoot`.

