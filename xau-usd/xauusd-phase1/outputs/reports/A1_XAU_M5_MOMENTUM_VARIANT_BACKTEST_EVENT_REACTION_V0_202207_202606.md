# A1 XAU M5 Momentum Continuation Variant Backtests

Generated: `2026-07-07T09:21:17.756389+00:00`
Period: `2022.07.01 -> 2026.06.30`
Tester currency: `USD`

## Boundary

- Offline MT5 Strategy Tester only.
- No chart, preset, order, or live/demo runtime change was made by this script.
- Variants were limited to pre-declared cells and fixed inputs; no post-result threshold sweep.
- Any positive result here is diagnostic only and requires fresh forward confirmation.
- Profit/loss table values are in tester currency `USD`.

## Variants

| Variant | Trades | Win Rate | Net USD | PF | Max Equity DD | Short USD | Long USD | Decision |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `event_impulse_nfp_rr2` | `17` | `47.06%` | `46.71` | `1.46` | `39.26 (3.69%)` | `-7.1` | `53.81` | `too_few_trades` |
| `event_fade_nfp_rr2` | `23` | `30.43%` | `-15.71` | `0.8` | `45.15 (4.42%)` | `-13.92` | `-1.79` | `fail` |
| `event_impulse_cpi_rr2` | `18` | `38.89%` | `22.75` | `1.19` | `61.89 (5.97%)` | `-42.16` | `64.91` | `too_few_trades` |
| `event_fade_cpi_rr2` | `28` | `46.43%` | `40.73` | `1.45` | `31.06 (3.04%)` | `59.39` | `-18.66` | `diagnostic_only` |
| `event_impulse_fomc_rr2` | `16` | `56.25%` | `68.52` | `1.81` | `53.57 (4.85%)` | `27.66` | `40.86` | `too_few_trades` |
| `event_fade_fomc_rr2` | `9` | `33.33%` | `5.64` | `1.16` | `30.97 (3.01%)` | `13.03` | `-7.39` | `too_few_trades` |

## Winner Status

- Status: `DIAGNOSTIC_WINNER_NOT_PROMOTED`
- Note: This is a backtest-window diagnostic. Do not promote without fresh forward evidence.

## Artifacts

### `event_impulse_nfp_rr2`

- Label: Event reaction v0: NFP 15m impulse continuation, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_event_reaction_v0_202207_202606_20260701\A1XauM5Momentum_EVENT_REACTION_V0_202207_202606_XAUUSD_M5_event_impulse_nfp_rr2.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_event_reaction_v0_202207_202606_20260701\A1XauM5Momentum_EVENT_REACTION_V0_202207_202606_XAUUSD_M5_event_impulse_nfp_rr2_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_event_reaction_v0_202207_202606_20260701\A1XauM5Momentum_EVENT_REACTION_V0_202207_202606_XAUUSD_M5_event_impulse_nfp_rr2_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_event_reaction_v0_202207_202606_20260701\A1XauM5Momentum_EVENT_REACTION_V0_202207_202606_XAUUSD_M5_event_impulse_nfp_rr2_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_event_reaction_v0_202207_202606_20260701\A1XauM5Momentum_EVENT_REACTION_V0_202207_202606_XAUUSD_M5_event_impulse_nfp_rr2_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_event_reaction_v0_202207_202606_20260701\A1XauM5Momentum_EVENT_REACTION_V0_202207_202606_XAUUSD_M5_event_impulse_nfp_rr2_summary.json`
- Order activity: `{"rows": 26, "actions": {"ORDER_SEND_OK": 17, "GUARD_BLOCK": 9}, "guard_reasons": {"pass": 17, "stop_ceiling_exceeded": 9}}`

### `event_fade_nfp_rr2`

- Label: Event reaction v0: NFP 15m spike fade, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_event_reaction_v0_202207_202606_20260701\A1XauM5Momentum_EVENT_REACTION_V0_202207_202606_XAUUSD_M5_event_fade_nfp_rr2.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_event_reaction_v0_202207_202606_20260701\A1XauM5Momentum_EVENT_REACTION_V0_202207_202606_XAUUSD_M5_event_fade_nfp_rr2_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_event_reaction_v0_202207_202606_20260701\A1XauM5Momentum_EVENT_REACTION_V0_202207_202606_XAUUSD_M5_event_fade_nfp_rr2_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_event_reaction_v0_202207_202606_20260701\A1XauM5Momentum_EVENT_REACTION_V0_202207_202606_XAUUSD_M5_event_fade_nfp_rr2_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_event_reaction_v0_202207_202606_20260701\A1XauM5Momentum_EVENT_REACTION_V0_202207_202606_XAUUSD_M5_event_fade_nfp_rr2_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_event_reaction_v0_202207_202606_20260701\A1XauM5Momentum_EVENT_REACTION_V0_202207_202606_XAUUSD_M5_event_fade_nfp_rr2_summary.json`
- Order activity: `{"rows": 23, "actions": {"ORDER_SEND_OK": 23}, "guard_reasons": {"pass": 23}}`

### `event_impulse_cpi_rr2`

- Label: Event reaction v0: CPI 15m impulse continuation, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_event_reaction_v0_202207_202606_20260701\A1XauM5Momentum_EVENT_REACTION_V0_202207_202606_XAUUSD_M5_event_impulse_cpi_rr2.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_event_reaction_v0_202207_202606_20260701\A1XauM5Momentum_EVENT_REACTION_V0_202207_202606_XAUUSD_M5_event_impulse_cpi_rr2_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_event_reaction_v0_202207_202606_20260701\A1XauM5Momentum_EVENT_REACTION_V0_202207_202606_XAUUSD_M5_event_impulse_cpi_rr2_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_event_reaction_v0_202207_202606_20260701\A1XauM5Momentum_EVENT_REACTION_V0_202207_202606_XAUUSD_M5_event_impulse_cpi_rr2_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_event_reaction_v0_202207_202606_20260701\A1XauM5Momentum_EVENT_REACTION_V0_202207_202606_XAUUSD_M5_event_impulse_cpi_rr2_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_event_reaction_v0_202207_202606_20260701\A1XauM5Momentum_EVENT_REACTION_V0_202207_202606_XAUUSD_M5_event_impulse_cpi_rr2_summary.json`
- Order activity: `{"rows": 33, "actions": {"GUARD_BLOCK": 15, "ORDER_SEND_OK": 18}, "guard_reasons": {"stop_ceiling_exceeded": 15, "pass": 18}}`

### `event_fade_cpi_rr2`

- Label: Event reaction v0: CPI 15m spike fade, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_event_reaction_v0_202207_202606_20260701\A1XauM5Momentum_EVENT_REACTION_V0_202207_202606_XAUUSD_M5_event_fade_cpi_rr2.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_event_reaction_v0_202207_202606_20260701\A1XauM5Momentum_EVENT_REACTION_V0_202207_202606_XAUUSD_M5_event_fade_cpi_rr2_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_event_reaction_v0_202207_202606_20260701\A1XauM5Momentum_EVENT_REACTION_V0_202207_202606_XAUUSD_M5_event_fade_cpi_rr2_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_event_reaction_v0_202207_202606_20260701\A1XauM5Momentum_EVENT_REACTION_V0_202207_202606_XAUUSD_M5_event_fade_cpi_rr2_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_event_reaction_v0_202207_202606_20260701\A1XauM5Momentum_EVENT_REACTION_V0_202207_202606_XAUUSD_M5_event_fade_cpi_rr2_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_event_reaction_v0_202207_202606_20260701\A1XauM5Momentum_EVENT_REACTION_V0_202207_202606_XAUUSD_M5_event_fade_cpi_rr2_summary.json`
- Order activity: `{"rows": 29, "actions": {"ORDER_SEND_OK": 28, "GUARD_BLOCK": 1}, "guard_reasons": {"pass": 28, "stop_ceiling_exceeded": 1}}`

### `event_impulse_fomc_rr2`

- Label: Event reaction v0: FOMC 15m impulse continuation, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_event_reaction_v0_202207_202606_20260701\A1XauM5Momentum_EVENT_REACTION_V0_202207_202606_XAUUSD_M5_event_impulse_fomc_rr2.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_event_reaction_v0_202207_202606_20260701\A1XauM5Momentum_EVENT_REACTION_V0_202207_202606_XAUUSD_M5_event_impulse_fomc_rr2_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_event_reaction_v0_202207_202606_20260701\A1XauM5Momentum_EVENT_REACTION_V0_202207_202606_XAUUSD_M5_event_impulse_fomc_rr2_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_event_reaction_v0_202207_202606_20260701\A1XauM5Momentum_EVENT_REACTION_V0_202207_202606_XAUUSD_M5_event_impulse_fomc_rr2_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_event_reaction_v0_202207_202606_20260701\A1XauM5Momentum_EVENT_REACTION_V0_202207_202606_XAUUSD_M5_event_impulse_fomc_rr2_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_event_reaction_v0_202207_202606_20260701\A1XauM5Momentum_EVENT_REACTION_V0_202207_202606_XAUUSD_M5_event_impulse_fomc_rr2_summary.json`
- Order activity: `{"rows": 28, "actions": {"ORDER_SEND_OK": 16, "GUARD_BLOCK": 12}, "guard_reasons": {"pass": 16, "stop_ceiling_exceeded": 12}}`

### `event_fade_fomc_rr2`

- Label: Event reaction v0: FOMC 30m spike fade, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_event_reaction_v0_202207_202606_20260701\A1XauM5Momentum_EVENT_REACTION_V0_202207_202606_XAUUSD_M5_event_fade_fomc_rr2.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_event_reaction_v0_202207_202606_20260701\A1XauM5Momentum_EVENT_REACTION_V0_202207_202606_XAUUSD_M5_event_fade_fomc_rr2_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_event_reaction_v0_202207_202606_20260701\A1XauM5Momentum_EVENT_REACTION_V0_202207_202606_XAUUSD_M5_event_fade_fomc_rr2_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_event_reaction_v0_202207_202606_20260701\A1XauM5Momentum_EVENT_REACTION_V0_202207_202606_XAUUSD_M5_event_fade_fomc_rr2_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_event_reaction_v0_202207_202606_20260701\A1XauM5Momentum_EVENT_REACTION_V0_202207_202606_XAUUSD_M5_event_fade_fomc_rr2_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_event_reaction_v0_202207_202606_20260701\A1XauM5Momentum_EVENT_REACTION_V0_202207_202606_XAUUSD_M5_event_fade_fomc_rr2_summary.json`
- Order activity: `{"rows": 10, "actions": {"ORDER_SEND_OK": 9, "GUARD_BLOCK": 1}, "guard_reasons": {"pass": 9, "stop_ceiling_exceeded": 1}}`

## Interpretation

The baseline failed because long-side momentum entries were much worse than shorts. If a variant improves materially, it should be treated as a hypothesis for forward testing, not as a proof of profitability. The cleanest next action is to forward-observe or demo-test only the winning diagnostic variant at minimum size, with the baseline retained as the control.
