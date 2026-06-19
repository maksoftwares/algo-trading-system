# A3 Net-Of-Cost Deduped Rebaseline - 2026-06-19

Status: `PASS`
Decision: `NO_CANDIDATE_CLEARS_NET_COST_DISCOVERY_SCREEN`

Analysis-only net-of-cost deduped rebaseline. No MT5 terminal, profile, chart, preset, order, position, or broker runtime state was touched.

## Cost Model

- `source_csv`: C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase0\outputs\reports\cost_model_measured.csv
- `charged_spread_points`: max(realized bar spread, measured median spread for entry UTC hour)
- `p95_sensitivity_points`: max(realized bar spread, measured P95 spread for entry UTC hour)
- `entry_slippage_points`: 10.0
- `stop_exit_slippage_points`: 50.0
- `cost_guard`: trade rejected from screen metrics when charged_cost_R > 0.12
- `cost_r_note`: Winning trades pay spread + entry slippage; losing trades also pay stop-exit slippage. Default stop-exit slippage is conservative at 50 points after Claude Round 3.
- `stress_model`: P95 spread plus the same 50-point stop-exit slippage.

## Thresholds

| Gate | Value |
| --- | ---: |
| `discovery_min_net_expectancy_r` | 0.1 |
| `discovery_min_net_profit_factor` | 1.25 |
| `promotion_min_net_expectancy_r` | 0.15 |
| `promotion_min_net_profit_factor` | 1.3 |
| `min_closed_net_trades` | 100 |
| `min_long_trades` | 25 |
| `min_short_trades` | 25 |
| `min_weeks` | 4 |
| `min_weeks_with_15_trades` | 3 |
| `min_trade_retention_vs_b0_pct` | 40.0 |
| `max_trade_cost_r` | 0.12 |
| `max_p95_cost_r` | 0.1 |
| `max_drawdown_r` | 8.0 |
| `min_t_stat` | 2.0 |
| `robustness` | positive after best 1 and best 2 days removed; positive after worst day removed; worst day > -4R; positive aggregate on both up and down market days |

## Raw Deduped Gate

| Candidate | Raw trades | Long | Short | Cost rejects | Reject rate | Raw PF | Raw exp R | Raw R | Raw stress PF | Raw stress exp R | Raw P95 cost R | Raw max DD R | Raw worst day R | Raw t-stat | Raw net | Raw cost | Raw stress | Raw DD | Raw robust |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- |
| B0_RAW_ALL_SESSION | 885 | 499 | 386 | 800 | 90.4% | 0.7357 | -0.2069 | -183.0996 | 0.6375 | -0.3028 | 0.828 | 193.3555 | -12.5157 | -4.5125 | False | False | False | False | False |
| A3_SQ_SOFT_RETEST_W15_B45_C60_RCM05_V2 | 490 | 281 | 209 | 433 | 88.37% | 1.1242 | 0.0778 | 38.1202 | 0.9701 | -0.0199 | 0.7595 | 22.5077 | -6.5572 | 1.2796 | False | False | False | False | False |
| A3_WIDE_STOP_800PT_SOFT_RETEST_V0 | 303 | 175 | 128 | 150 | 49.5% | 1.183 | 0.107 | 32.4259 | 1.1273 | 0.0765 | 0.1375 | 10.1525 | -4.55 | 1.4524 | False | False | False | False | False |

## Cost-Guard Survivor Diagnostics

These rows are diagnostic only. They show what remains after `cost_R <= 0.12`, but they do not by themselves prove edge because the cost filter was not pre-registered as an entry rule for these candidates.

| Candidate | Raw trades | Cost rejects | Screen trades | Long | Short | Ret. vs B0 | WR | Net PF | Net exp R | Net R | P95 cost R | Raw P95 cost R | Best 2 days removed R | Up-day R | Down-day R | Discovery pass | Promotion pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| B0_RAW_ALL_SESSION | 885 | 800 | 85 | 41 | 44 | 100.0% | 83.53% | 6.5003 | 0.9984 | 84.8615 | 0.1179 | 0.828 | 74.5688 | 46.7315 | 38.13 | False | False |
| A3_SQ_SOFT_RETEST_W15_B45_C60_RCM05_V2 | 490 | 433 | 57 | 23 | 34 | 67.06% | 89.47% | 10.8919 | 1.146 | 65.3228 | 0.1174 | 0.7595 | 56.4694 | 34.1223 | 31.2005 | False | False |
| A3_WIDE_STOP_800PT_SOFT_RETEST_V0 | 303 | 150 | 153 | 89 | 64 | 180.0% | 96.08% | 31.7439 | 1.3269 | 203.0233 | 0.075 | 0.1375 | 191.5947 | 115.8297 | 85.7686 | False | False |

## Cost-Guard Survivor Stress Diagnostics

Diagnostic only; these numbers are after dropping high-cost trades and are not the approval gate.

| Candidate | Stress PF | Stress exp R | Max DD R | Worst day R | Worst-day removed R | t-stat | 800-floor provenance |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| B0_RAW_ALL_SESSION | 6.2021 | 0.9641 | 3.3283 | -2.2164 | 87.0778 | 9.8085 |  |
| A3_SQ_SOFT_RETEST_W15_B45_C60_RCM05_V2 | 10.3875 | 1.1102 | 2.229 | -1.1127 | 66.4356 | 11.1259 |  |
| A3_WIDE_STOP_800PT_SOFT_RETEST_V0 | 30.4304 | 1.2966 | 2.229 | -1.1127 | 204.1361 | 33.355 | POST_HOC_EXPLORATORY_ONLY. No pre-registration or hash-lock evidence was found before this 2026-06-19 screen; the 800-point floor was introduced as an A2-style exploratory cost-feasibility floor. |

## Gate Diagnostics

| Candidate | Raw net | Raw cost | Raw stress | Raw DD | Raw robust | Raw sig | Screen sample | Screen weeks | Survivor cost | Discovery | Failure reasons |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B0_RAW_ALL_SESSION | False | False | False | False | False | False | False | False | False | False | ['raw_deduped_net_gate_failed', 'raw_cost_discipline_failed', 'raw_p95_spread_50pt_stop_slip_stress_failed', 'raw_max_drawdown_above_8R', 'raw_robustness_failed', 'raw_significance_t_below_2', 'sample_or_direction_floor_failed', 'week_coverage_failed', 'cost_gate_failed'] |
| A3_SQ_SOFT_RETEST_W15_B45_C60_RCM05_V2 | False | False | False | False | False | False | False | False | False | False | ['raw_deduped_net_gate_failed', 'raw_cost_discipline_failed', 'raw_p95_spread_50pt_stop_slip_stress_failed', 'raw_max_drawdown_above_8R', 'raw_robustness_failed', 'raw_significance_t_below_2', 'sample_or_direction_floor_failed', 'week_coverage_failed', 'cost_gate_failed'] |
| A3_WIDE_STOP_800PT_SOFT_RETEST_V0 | False | False | False | False | False | False | True | False | True | False | ['raw_deduped_net_gate_failed', 'raw_cost_discipline_failed', 'raw_p95_spread_50pt_stop_slip_stress_failed', 'raw_max_drawdown_above_8R', 'raw_robustness_failed', 'raw_significance_t_below_2', 'week_coverage_failed'] |

## Interpretation

- This is the first A3 screen that charges a non-zero measured spread floor plus slippage.
- Raw deduped metrics are now the primary gate; survivor metrics after `cost_R <= 0.12` are diagnostic only unless the filter is pre-registered.
- Round 3 raised default stop-exit slippage to 50 points and added stress, max-drawdown, worst-day, and t-stat gates.
- Raw cost rejection count is not hidden; it shows how much of each candidate is structurally too tight for the measured cost floor.
- The 800-point wide-stop variant remains exploratory/post-hoc and does not clear the updated screen.
- A candidate must pass on the raw deduped net book and the P95-stress book before it can earn forward tick-level validation.

## Outputs

- json: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A3_NET_COST_DEDUPED_REBASELINE_2026_06_19.json`
- markdown: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A3_NET_COST_DEDUPED_REBASELINE_2026_06_19.md`
- trades_csv: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A3_NET_COST_DEDUPED_REBASELINE_TRADES_2026_06_19.csv`
