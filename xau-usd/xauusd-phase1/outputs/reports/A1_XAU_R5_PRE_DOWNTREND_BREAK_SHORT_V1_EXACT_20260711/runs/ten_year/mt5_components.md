# A1 XAU M5 Momentum Continuation Variant Backtests

Generated: `2026-07-11T14:05:09.847932+00:00`
Period: `2016.07.01 -> 2026.06.30`
Tester currency: `USD`

## Boundary

- Offline MT5 Strategy Tester only.
- No chart, preset, order, or live/demo runtime change was made by this script.
- Variants were limited to pre-declared cells and fixed inputs; no post-result threshold sweep.
- Any positive result here is diagnostic only and requires fresh forward confirmation.
- Profit/loss table values are in tester currency `USD`.
- Currency note: Raw shared-parser fields named profit_aed or pnl_aed contain tester-currency USD values in this packet; the names are retained only for backward-compatible schema consumption.

## Variants

| Variant | Trades | Win Rate | Net USD | PF | Max Equity DD | Short USD | Long USD | Decision |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `r5_upchop_downside_impulse_retest_q55_v1` | `612` | `28.92%` | `-380.64` | `0.8` | `488.11 (44.09%)` | `-380.64` | `0` | `fail` |

## Winner Status

- Status: `NO_VARIANT_CLEARS_MINIMUM_BAR`
- Note: Positive diagnostic variants still need forward confirmation before runtime promotion.

## Artifacts

### `r5_upchop_downside_impulse_retest_q55_v1`

- Label: R5 causal UPTREND/CHOP q55 downside impulse/retest short, fixed 0.01 lot and 2R
- MT5 report: `runs/ten_year/a1_momentum_variants_r5_pre_downtrend_q55_ten_year_20260701/A1XauM5Momentum_R5_PRE_DOWNTREND_Q55_TEN_YEAR_XAUUSD_M5_r5_upchop_downside_impulse_retest_q55_v1.htm`
- Trade CSV: `runs/ten_year/a1_momentum_variants_r5_pre_downtrend_q55_ten_year_20260701/A1XauM5Momentum_R5_PRE_DOWNTREND_Q55_TEN_YEAR_XAUUSD_M5_r5_upchop_downside_impulse_retest_q55_v1_trades.csv`
- Order CSV: `runs/ten_year/a1_momentum_variants_r5_pre_downtrend_q55_ten_year_20260701/A1XauM5Momentum_R5_PRE_DOWNTREND_Q55_TEN_YEAR_XAUUSD_M5_r5_upchop_downside_impulse_retest_q55_v1_orders.csv`
- Signal CSV (gzip): `runs/ten_year/a1_momentum_variants_r5_pre_downtrend_q55_ten_year_20260701/A1XauM5Momentum_R5_PRE_DOWNTREND_Q55_TEN_YEAR_XAUUSD_M5_r5_upchop_downside_impulse_retest_q55_v1_signals.csv.gz`
- Management CSV: `runs/ten_year/a1_momentum_variants_r5_pre_downtrend_q55_ten_year_20260701/A1XauM5Momentum_R5_PRE_DOWNTREND_Q55_TEN_YEAR_XAUUSD_M5_r5_upchop_downside_impulse_retest_q55_v1_management.csv`
- Summary JSON: `runs/ten_year/a1_momentum_variants_r5_pre_downtrend_q55_ten_year_20260701/A1XauM5Momentum_R5_PRE_DOWNTREND_Q55_TEN_YEAR_XAUUSD_M5_r5_upchop_downside_impulse_retest_q55_v1_summary.json`
- Order activity: `{"rows": 4848, "actions": {"GUARD_BLOCK": 4236, "ORDER_SEND_OK": 612}, "guard_reasons": {"estimated_cost_r_too_high": 1063, "regime_router_allow_short_r5_uptrend_chop_only_state_chop": 388, "regime_router_allow_short_r5_uptrend_chop_only_state_uptrend": 224, "regime_router_block_short_r5_uptrend_chop_only_state_compression": 906, "regime_router_block_short_r5_uptrend_chop_only_state_downtrend": 611, "regime_router_block_short_r5_uptrend_chop_only_state_shock": 654, "stop_ceiling_exceeded": 175, "own_position_exists": 25, "daily_trade_cap_reached": 790, "spread_too_high": 12}}`

## Interpretation

The baseline failed because long-side momentum entries were much worse than shorts. If a variant improves materially, it should be treated as a hypothesis for forward testing, not as a proof of profitability. The cleanest next action is to forward-observe or demo-test only the winning diagnostic variant at minimum size, with the baseline retained as the control.
