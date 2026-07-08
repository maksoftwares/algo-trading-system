# REVIEW REQUEST - XAUUSD Regime Router Next Steps After Exact-MT5 Router/Short Tests

We need reviewer guidance on the next highest-value direction.

## Context

We pivoted from one combined strategy hunt to a regime-router architecture because the current best blend was proven regime-dependent:

- The long H4/D1 box is the real profit engine, but mainly during gold-bull/uptrend behavior.
- Recent Q2-2026 survival came from frequency and short rows, not from the long edge.
- The frequency layer gives activity but damages payoff and is likely filler unless assigned to a proven regime.

The latest exact-MT5 work implemented and tested this direction.

## New Exact-MT5 Work In This Commit

### 1. EA-side Regime Router V1

File:

- `xau-usd/xauusd-phase1/mt5/Experts/A1XauM5MomentumContinuationExecutor.mq5`

Router states:

- `SHOCK`: no trade
- `UPTREND`: long specialist allowed
- `DOWNTREND`: short specialist allowed
- `COMPRESSION`: no specialist yet
- `CHOP`: no trade

All regime decisions use completed bars only.

Prereg/report:

- `xau-usd/xauusd-phase1/docs/A1_XAU_REGIME_ROUTER_V1_EXACT_PREREG_2026_07_08.md`
- `xau-usd/xauusd-phase1/scripts/run_a1_regime_router_v1_exact.py`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_REGIME_ROUTER_V1_EXACT_20260708.md`

### Router V1 Result

Status: `ROUTER_V1_SHADOW_ONLY`

| Component | Trades | WR | W/L | PF | Net | Q2 net | Router blocks |
|---|---:|---:|---:|---:|---:|---:|---:|
| `router_v1_r1_long_box2_prevhealth` | 145 | 59.31% | 2.1804 | 3.1782 | +$7,050.42 | $0.00 | 171 |
| `router_v1_r2_short_v4_structural` | 0 | 0.00% | n/a | n/a | $0.00 | $0.00 | 4,307 |

Portfolio diagnostics:

| Portfolio | Trades | WR | W/L | Stress W/L | Net | Max DD | Positive months | Q2 net |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| routed long+short, no frequency | 145 | 59.31% | 2.1804 | 2.1631 | +$7,050.42 | $866.37 | 15 | $0.00 |
| routed long+short + frequency observer | 3,555 | 49.90% | 1.7547 | 1.6425 | +$13,067.88 | $958.86 | 32 | +$279.22 |

Interpretation:

- R1 uptrend long specialist is clean and real.
- R2 strict downtrend router is too restrictive for the current V4 short: it produced zero trades.
- Frequency restores activity and recent Q2 profit, but lowers W/L and remains filler unless proven in a regime.

### 2. Non-Up HTF Resistance Sweep Short

This tested the reviewer-suggested quality short archetype:

- D1 non-up
- price sweeps higher-timeframe resistance
- M15 bearish reclaim/failure
- fixed 2R

Prereg/report:

- `xau-usd/xauusd-phase1/docs/A1_XAU_NONUP_HTF_RESISTANCE_SWEEP_SHORT_PREREG_2026_07_08.md`
- `xau-usd/xauusd-phase1/scripts/run_a1_nonup_htf_resistance_sweep_short.py`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_NONUP_HTF_RESISTANCE_SWEEP_SHORT_20260708.md`

Result:

Status: `NONUP_HTF_RESISTANCE_SWEEP_NO_SURVIVOR`

| Trades | WR | W/L | PF | Net | Stress PF | Stress net | Recent3 | 2023+2024 | Top10 removed |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 299 | 29.43% | 2.0257 | 0.8449 | -$255.11 | 0.7981 | -$344.81 | +$135.72 | -$271.34 | -$635.83 |

By year:

| Year | Trades | WR | PF | Net |
|---|---:|---:|---:|---:|
| 2022 | 57 | 35.09% | 1.2880 | +$54.87 |
| 2023 | 81 | 33.33% | 1.0277 | +$7.56 |
| 2024 | 69 | 18.84% | 0.3484 | -$278.90 |
| 2025 | 58 | 29.31% | 0.8907 | -$41.99 |
| 2026 | 34 | 32.35% | 1.0091 | +$3.35 |

Interpretation:

- This fixed short archetype failed clearly.
- Recent 3 months were positive, but full-window durability and 2024 failed.
- Do not tune this short path without review.

## What We Need From Reviewers

Please answer directly.

1. Is `ROUTER_V1_SHADOW_ONLY` the correct interpretation, or should the router be rejected because the short side produced zero trades?
2. Should we relax the strict R2 downtrend definition, or would that create too much router overfit risk?
3. Should the next specialist be:
   - R1 pullback-continuation long,
   - R3 balanced-compression breakout,
   - a less strict non-up short hedge,
   - or frequency-regime attribution/quarantine?
4. Given repeated short failures, should we stop chasing a standalone short specialist and treat shorts as hedge-only?
5. What exact next preregistered test should Codex run next?
6. What gates should that next test use?
7. What should we stop doing immediately?

## My Current Working View

The next best path is probably not more short tuning.

The evidence now says:

- R1 long/uptrend is real but sparse.
- Strong R2 short does not fire with V4.
- Non-up resistance sweep short failed full-window.
- Frequency gives activity but hurts W/L and must not be global filler.

Candidate next directions:

1. Build/test `R1_PULLBACK_CONTINUATION_LONG` to increase activity during the only proven profitable regime.
2. Build/test `R3_BALANCED_COMPRESSION_BREAKOUT` as the first true non-trend specialist.
3. Run a frequency-regime attribution audit to decide whether `freq_step3_frontier` has any regime where it is legitimate.

Please recommend one next move, and be strict about overfitting risk.

