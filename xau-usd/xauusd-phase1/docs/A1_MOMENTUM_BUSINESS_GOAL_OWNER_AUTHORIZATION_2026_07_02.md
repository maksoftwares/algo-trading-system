# A1 Momentum Business-Goal Owner Authorization - 2026-07-02

Status: `PENDING_OWNER_DECISION`

Scope: demo-only A1 account `1025742`, `Capital.ComMena-Demo`, `XAUUSD` only, `M5`, fixed lot `0.01`.

This packet does not approve canonical Phase 2, live trading, real capital, lot increases, extra symbols, extra accounts, or mid-test tuning. It only asks the owner to decide whether to replace the sparse A1 RR2 momentum lane with a frequent intraday momentum package for demo forward testing.

2026-07-03 causal cadence update: after reviewer feedback found future leakage in the 2026-07-02 daily guard simulation, the market-day coverage search was rerun with an event-time causal guard. The old 3900-trade / 66.13% / PF 1.44 headline is rejected as stated and must not be used for approval. The repaired candidate is still frequent and positive, but weaker and marked review/revise only.

## Decision Required

Write exactly one decision in the table below before any runtime replacement:

| Option | Decision | Meaning |
| --- | --- | --- |
| Primary `residual_plus75_high_net` | `PENDING` | Approve A1 demo forward test of the higher-net package using magics `932300/932301`. |
| Fallback `residual_plus50_10m` | `PENDING` | Approve A1 demo forward test of the smoother +50 package using magics `932298/932299`. |
| Market-day coverage portfolio | `PENDING_REVIEW_ONLY` | New higher-cadence review candidate; requires separate reviewer signoff and a fresh runtime spec before any approval. |
| No replacement | `PENDING` | Keep current runtime unchanged and continue research only. |

Allowed decision values: `APPROVE` or `DECLINE`.

## Evidence Basis

Primary evidence:

- Scoreboard: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_BUSINESS_GOAL_SCOREBOARD_2026_07_02.md`
- Promotion packet: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_BUSINESS_GOAL_PROMOTION_PACKET_2026_07_02.md`
- Calendar cadence audit: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_BUSINESS_GOAL_CALENDAR_CADENCE_AUDIT_2026_07_02.md`
- Market-day coverage search, causal rerun: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_MARKET_DAY_COVERAGE_SEARCH_CAUSAL_2026_07_03.md`
- Market-day coverage stress, causal rerun: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_MARKET_DAY_COVERAGE_STRESS_CAUSAL_2026_07_03.md`
- Market-day coverage kept/dropped audit CSV: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_MARKET_DAY_COVERAGE_SEARCH_CAUSAL_2026_07_03_BEST_KEPT_DROPPED.csv`
- +75 readiness: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS75_HIGH_NET_READINESS_2026_07_02.md`
- +50 readiness: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS50_COOLDOWN10_READINESS_2026_07_02.md`

Stricter market-day coverage candidate:

| Metric | Market-day coverage portfolio |
| --- | ---: |
| Composition | residual +75 high-net + block-bad-hours + V6 max2 companion |
| Daily overlay | +75 target / 10m loss cooldown |
| Guard model | event-time causal v2 |
| Trades | 3714 |
| Win rate | 64.27% |
| Profit factor | 1.29 |
| Net | +2391.40 USD |
| Trades / market day | 3.57 |
| Trades / active day | 5.02 |
| 3+ trade market days | 46.35% |
| Positive active days | 51.49% |
| Top 100 winners removed | +1142.41 USD |
| Top 200 winners removed | +191.20 USD |
| Top 300 winners removed | -629.28 USD |
| Duplicate drops before scoring | 2218 |
| Half-year stability | 8/8 positive |
| Quarter stability | 16/16 positive |
| Rolling windows | 339 negative 250-trade windows, 0 negative 500-trade windows |

Interpretation: this is still the closest current package to the owner's original "multiple trades per day" target, but it is no longer a promotion pass. It was found by a combination search, depends on a package overlay, has negative 250-trade rolling windows, and loses robustness after removing the top 300 winners. It is review/revise evidence, not runtime-approved.

| Metric | Primary +75 high-net | Fallback +50 smoother |
| --- | ---: | ---: |
| Trades | 2231 | 1823 |
| Win rate | 69.48% | 69.17% |
| Profit factor | 1.54 | 1.53 |
| Net | +2400.90 USD | +1863.81 USD |
| Trades / market day | 2.15 | 1.75 |
| Trades / active day | 3.90 | 3.19 |
| 3+ trade market days | 28.08% | 28.08% |
| 3+ trade active days | 51.05% | 51.05% |
| Positive active days | 60.66% | 62.94% |
| Top 100 winners removed | +1324.53 USD | +829.08 USD |
| Top 200 winners removed | +489.31 USD | +57.55 USD |
| Max closed DD | 91.59 USD | 84.11 USD |

Interpretation:

- The +75 package best matches the owner's raw daily-trading goal: more trades and higher net.
- The +50 package is smoother: fewer trades, lower net, better positive-day rate, and lower drawdown.
- Neither package should be described as trading 3+ times every market day. They are frequent on active days, and quiet days still occur.
- The sparse RR2 lane is not the primary answer because it does not produce enough trades for the owner's daily-frequency goal.

## If Primary +75 Is Approved

Attach only the following A1 demo lanes:

| Lane | Value |
| --- | --- |
| Account | `1025742` |
| Server marker | `Demo` |
| Symbol | `XAUUSD` |
| Timeframe | `M5` |
| EA | `A1XauM5MomentumContinuationExecutor.mq5` |
| Long run id | `A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS75_HIGH_NET_LONG_20260702` |
| V13 run id | `A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS75_HIGH_NET_V13_20260702` |
| Magics | `932300`, `932301` |
| Comments | `A1_XAU_M5_MOM_RR75_L`, `A1_XAU_M5_MOM_RR75_B` |
| Lot | `0.01` fixed |
| Package target | `+75 USD` |
| Shared max-trade cap | Disabled / `0` |
| Cooldown after package loss | `10` minutes |
| Broker action | `true` after owner approval only |
| Dry run | `false` after owner approval only |

## If Fallback +50 Is Approved

Attach only the following A1 demo lanes:

| Lane | Value |
| --- | --- |
| Account | `1025742` |
| Server marker | `Demo` |
| Symbol | `XAUUSD` |
| Timeframe | `M5` |
| EA | `A1XauM5MomentumContinuationExecutor.mq5` |
| Long run id | `A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS50_COOLDOWN10_LONG_20260702` |
| V13 run id | `A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS50_COOLDOWN10_V13_20260702` |
| Magics | `932298`, `932299` |
| Comments | `A1_XAU_M5_MOM_RR10_L`, `A1_XAU_M5_MOM_RR10_B` |
| Lot | `0.01` fixed |
| Package target | `+50 USD` |
| Shared max-trade cap | `6` package trades/day |
| Cooldown after package loss | `10` minutes |
| Broker action | `true` after owner approval only |
| Dry run | `false` after owner approval only |

## Required Runtime Evidence After Any Approved Replacement

| Gate | Required evidence |
| --- | --- |
| Profile backup | Backup path recorded before profile change |
| Compile proof | MetaEditor compile log with `0 errors / 0 warnings` |
| Startup proof | Startup log shows correct account, server marker, symbol, timeframe, run id, magic, lot, and demo-only broker action |
| Replacement proof | Current sparse RR2 chart is either disarmed or documented as unchanged by owner choice |
| No duplicate attachment | No duplicate chart for the same selected magic/run id |
| Safety proof | Phase 1 safety audit passes after the replacement |
| Status proof | `status.html` and `status_summary.md` regenerated after replacement |
| First-order proof | First closed/open order rows with selected magics are captured once valid signals occur |

## Forward-Test Rules

| Field | Rule |
| --- | --- |
| Minimum sample | At least 4 weeks and at least 150 closed trades before any promotion decision; prefer 8 weeks / 300 trades |
| Pass rule | Forward PF >= 1.25, WR >= 55%, net positive, trades/active day >= 3, trades/market day >= 2 where market is open, positive active days >= 55%, and no single day > 30% of net |
| Kill/revert rule | Rolling 80-trade PF < 0.95, drawdown > 1.5x historical scaled DD, net negative after 150 trades, or any broker/runtime safety violation |
| No tuning rule | Do not change hours, filters, RR, package target, cooldown, lot, or magics during the forward window |

## Boundaries

- Demo only.
- No live trading.
- No real capital.
- No canonical Phase 2 status change.
- No lot increase.
- No extra symbols.
- No extra accounts unless separately authorized.
- No committed armed preset.
- No change to A2/A3.
- No runtime replacement until owner decision is recorded and reviewer feedback is considered.
