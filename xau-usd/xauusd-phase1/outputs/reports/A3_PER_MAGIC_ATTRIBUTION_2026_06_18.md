# A3 Per-Magic Attribution - 2026-06-18

Status: `PASS`

Read-only A3 review follow-up. No MT5 runtime, EA, chart, preset, order, position, or profile setting was changed.

Rows CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A3_PER_MAGIC_ATTRIBUTION_2026_06_18.csv`

| magic | lane_name | closed_trades | wins | losses | win_rate | net_pnl_aed | profit_factor | avg_win | avg_loss | max_loss | consecutive_losses | open_positions | open_orders | dry_run_now | broker_action_allowed_now | run_id_now |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 933200 | A3_BREAKOUT_PLAIN | 14 | 0 | 14 | 0.00% | -510.44 | 0.00 | 0.0 | -36.46 | -129.07 | 14 | 0 | 0 | true | false | A3_BREAKOUT_PLAIN_V1_STOPPED_20260618 |
| 933300 | A3_BREAKOUT_IMPROVED | 8 | 1 | 7 | 12.50% | -156.04 | 0.00 | 0.26 | -22.33 | -45.52 | 7 | 0 | 0 | false | true | A3_BREAKOUT_IMPROVED_V1_ARMED_20260616 |
| 933400 | A3_BREAKOUT_TIER1_COMPAT | 1 | 0 | 1 | 0.00% | -92.31 | 0.00 | 0.0 | -92.31 | -92.31 | 1 | 0 | 0 | false | true | A3_BREAKOUT_TIER1_COMPAT_V1_ARMED_20260617 |

Interpretation: `933200` is expected to remain stopped with `dry_run_now=true` and `broker_action_allowed_now=false`. `933300` and `933400` remain conditional demo lanes pending fresh forward evidence.
