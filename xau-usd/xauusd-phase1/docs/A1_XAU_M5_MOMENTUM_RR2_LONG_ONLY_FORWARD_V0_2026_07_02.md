# A1 XAU M5 Momentum RR2 Long-Only Forward V0 - 2026-07-02

Status: `LOCKED_FOR_SMALL_DEMO_FORWARD_TEST`

## Boundary

- Demo account only.
- A1 account `1025742` only.
- Symbol `XAUUSD` only.
- Magic `932200` only.
- Fixed lot `0.01`.
- This is not canonical Phase 2 approval.
- This is not live trading and not real capital.
- Existing `920101` breakout-retest charts must not be edited by this lane.
- A2 and A3 must not be touched by this lane.

## Evidence Basis

This forward candidate replaces the earlier `directional_session_htf_both` A1 momentum rule because the two-year and OOS tests showed a stronger, simpler long-only tail-capture profile.

Primary reports:

- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_REPAIR_RERUN_VERDICT_2026_07_02.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_OOS_AND_RR_DECISION_2026_07_02.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FOUR_YEAR_RR2_LONG_ONLY_2022_07_2026_06_MOMENTUM_USD.md`

Four-year combined MT5 Strategy Tester result, `2022.07.01 -> 2026.06.30`, Every Tick, `98%` history quality:

| Metric | Result |
|---|---:|
| Trades | 798 |
| Win rate | 41.35% |
| Net PnL | +1,744.60 USD |
| Profit factor | 1.50 |
| Max equity DD | 169.62 USD / 6.41% |
| Positive months | 34/44 |
| Positive quarters | 14/16 |
| Top 5 winners removed | +1,466.01 USD |
| Top 10 winners removed | +1,293.13 USD |
| Worst month | -33.00 USD |
| Worst quarter | -47.00 USD |

OOS direction split, `2022.07.01 -> 2024.06.30`, Every Tick, `99%` history quality:

| Variant | Trades | Win rate | Net USD | PF | Top 5 removed | Positive months |
|---|---:|---:|---:|---:|---:|---:|
| RR2 long-only | 212 | 40.09% | +279.43 | 1.39 | +160.38 | 14/20 |
| RR2 short-only | 118 | 27.97% | -104.13 | 0.78 | -186.88 | 6/19 |

Conclusion:

- Long-only RR2 is the only branch in this pass that survived both current and OOS windows.
- Short-only RR2 failed OOS and is excluded from this forward rule.
- The system is a tail-capture profile, not a high-win-rate profile. The expected win rate is around `40-42%`, with profit coming from larger winners.

## Frozen Rule

The EA is `A1XauM5MomentumContinuationExecutor.mq5`.

Common controls:

| Input | Value |
|---|---|
| `InpRunId` | `A1_XAU_M5_MOMENTUM_RR2_LONG_ONLY_FORWARD_V0_20260702` |
| `InpAllowDemoTrading` | `true` |
| `InpAllowNonDemoAccounts` | `false` |
| `InpAllowedAccountLogin` | `1025742` |
| `InpExpectedServerMarker` | `Demo` |
| `InpTargetSymbol` | `XAUUSD` |
| `InpMagicNumber` | `932200` |
| `InpFixedLots` | `0.01` |
| `InpMaxSpreadPoints` | `75` |
| `InpMaxEstimatedCostR` | `0.15` |
| `InpMaxTradesPerDay` | `6` |
| `InpCooldownMinutes` | `10` |
| `InpOnePositionPerMagic` | `true` |
| `InpKillSwitchFileName` | `a1_xau_m5_momentum_rr2_kill_switch.txt` |
| `InpDirectionMode` | `MOMENTUM_LONG_ONLY` |
| `InpUseDirectionalSessionFilter` | `false` |
| `InpUseH1TrendFilter` | `true` |
| `InpH1TrendApplyToLong` | `true` |
| `InpH1TrendApplyToShort` | `true` |
| `InpH1TrendMinSlopePoints` | `0` |
| `InpUseH4TrendFilter` | `true` |
| `InpH4TrendApplyToLong` | `true` |
| `InpH4TrendApplyToShort` | `true` |
| `InpH4TrendMinSlopePoints` | `0` |
| `InpMinAtrAbsoluteForEntry` | `1.5` |
| `InpBlockedEntryHoursCsv` | `9,10` |

Mechanical trigger controls:

| Input | Value |
|---|---|
| `InpBreakLookbackBars` | `12` |
| `InpAtrPeriod` | `14` |
| `InpBreakAtrMultiple` | `0.20` |
| `InpMinRangeAtr` | `0.60` |
| `InpMinBodyFraction` | `0.45` |
| `InpLongCloseLocation` | `0.72` |
| `InpShortCloseLocation` | `0.28` |
| `InpMinThreeBarMoveAtr` | `0.70` |
| `InpMaxThreeBarMoveAtr` | `0.00` |
| `InpStopAtrMultiple` | `2.50` |
| `InpStopFloorPoints` | `350` |
| `InpStopCeilingPoints` | `1800` |
| `InpRiskReward` | `2.00` |

## Forward-Test Question

Can the four-year/OOS-positive RR2 long-only momentum profile repeat on fresh A1 demo data without tuning?

## Attribution Start

Forward evaluation starts from the first RR2 long-only startup row:

`2026-07-02 04:46:42` broker time, run id `A1_XAU_M5_MOMENTUM_RR2_LONG_ONLY_FORWARD_V0_20260702`.

Any prior `932200` fills, signals, or order-log rows are `PRE_SPEC` and excluded from this forward test because the same magic/comment was previously used by the July 1 directional-session momentum lane.

## Minimum Judgment Sample

Do not declare success before:

- At least 100 forward trades, or
- At least 8 calendar weeks, whichever comes later.

At the observed historical rate, 100 forward trades is expected to take roughly `18-25` weeks. Treat this as a multi-month forward test, not a one-week or two-week verdict.

Because this is long-only, there is no short-side pass condition in this forward test. Shorts are excluded by the rule and must not be reintroduced mid-test.

## Kill Rules

Pause/review this lane if any occurs:

- Rolling 40-trade PF below `0.90`.
- Net negative after 60 trades.
- Equity drawdown above `15%` from lane start.
- Any single day contributes more than 25% of positive net.
- Any demo-safety, wrong-account, wrong-symbol, wrong-magic, or non-demo-server violation.

## Pass Rules

Forward test can be marked promising only if:

- PF >= `1.30`.
- Net PnL positive.
- Win rate >= `38%`.
- Result remains positive after removing top 2 winners.
- No mid-test parameter changes were made.

## Forbidden During Forward Test

- No lot increase.
- No extra symbols.
- No extra accounts.
- No threshold tuning.
- No session changes.
- No stop/target changes.
- No adding profit-lock, break-even, or dynamic exit into this same forward-test lane.
- No reintroducing shorts into this lane.

Potential improvements must be tested in separate offline/backtest lanes first.

## Evidence Caveats

- This lane was selected after all currently available historical windows were used. Forward demo is the first uncontaminated test.
- A forward PASS is first confirmation, not proof.
- Expected max losing streak during the test is roughly `8-10` trades and is not itself a failure.
- If the lane bleeds materially during a falling-gold month, that is out-of-character versus the backtest and should trigger early review even before hard kill rules fire.
