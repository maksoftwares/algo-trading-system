# A1 XAU M5 Momentum Directional HTF Forward V0 - 2026-07-01

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

The rule is based on the isolated MT5 Strategy Tester Q2 2026 diagnosis:

- Report: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_Q2_2026.md`
- Diagnosis: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_LONG_FAILURE_DIAGNOSIS_Q2_2026.md`
- Window: `2026.04.01 -> 2026.06.30`
- MT5 history quality: `100%`

Winning diagnostic variant: `directional_session_htf_both`

| Metric | Result |
|---|---:|
| Trades | 101 |
| Win rate | 57.43% |
| Net PnL | +1,996.98 AED |
| Profit factor | 2.14 |
| Max equity DD | 243.96 AED / 10.65% |
| Long trades | 20 |
| Long win rate | 65.00% |
| Long PnL | +553.62 AED |
| Short trades | 81 |
| Short win rate | 55.56% |
| Short PnL | +1,443.36 AED |

Independent reviewer response: `APPROVE_FOR_SMALL_FORWARD_DEMO`, with the rule frozen and judged only after fresh forward data.

## Frozen Rule

The EA is `A1XauM5MomentumContinuationExecutor.mq5`.

Common controls:

| Input | Value |
|---|---|
| `InpRunId` | `A1_XAU_M5_MOMENTUM_DIR_SESSION_HTF_FORWARD_V0_20260701` |
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
| `InpDirectionMode` | `MOMENTUM_BOTH_DIRECTIONS` |
| `InpUseDirectionalSessionFilter` | `true` |
| `InpLongSessionStartHour` | `6` |
| `InpLongSessionEndHour` | `12` |
| `InpShortSessionStartHour` | `16` |
| `InpShortSessionEndHour` | `6` |
| `InpUseH1TrendFilter` | `true` |
| `InpH1TrendApplyToLong` | `true` |
| `InpH1TrendApplyToShort` | `false` |
| `InpH1TrendMinSlopePoints` | `0` |
| `InpUseH4TrendFilter` | `true` |
| `InpH4TrendApplyToLong` | `false` |
| `InpH4TrendApplyToShort` | `true` |
| `InpH4TrendMinSlopePoints` | `0` |

Mechanical trigger controls remain unchanged from the Q2 test:

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
| `InpStopAtrMultiple` | `2.50` |
| `InpStopFloorPoints` | `350` |
| `InpStopCeilingPoints` | `1800` |
| `InpRiskReward` | `1.50` |

## Forward-Test Question

Can the Q2 diagnostic rule repeat on fresh demo data without tuning?

## Minimum Judgment Sample

Do not declare success before:

- At least 100 forward trades, or
- At least 8 calendar weeks, whichever comes later.

Direction-specific read:

- Long side is still only a hypothesis until at least 15-20 forward long trades exist.
- Short side must remain non-negative on fresh data.

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
- Win rate >= `48%`.
- Long and short direction cells are both non-negative, or the weak direction remains too small and explicitly unresolved.
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

Potential improvements such as break-even, profit-lock, candle-exhaustion filters, or dynamic exits must be tested in separate offline/backtest lanes first.
