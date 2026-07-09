# A1 XAU R1 Box / R3 Overlap Priority Audit

Generated UTC: `2026-07-09T20:20:44Z`
Status: `R1_BOX_R3_OVERLAP_PRIORITY_KILL_PORTFOLIO_USE`
Decision: `KILLED_FOR_PORTFOLIO_USE_KEEP_STANDALONE_SHADOW_ONLY`

Boundary: Diagnostic recomposition of existing exact-MT5 ledgers only. Not promotion evidence; no new MT5 run or runtime change.

## Verdict

At least one preregistered kill rule triggered. Do not run the conditional exact-MT5 source-priority test or tune R3.

R3 improves the 110-trade overlap net by $2382.02. Replacement combined max closed DD is $1217.13 versus the $1023.14 cap and exceeds the hard cap by $193.99.

## Fixed Audit Rule

- Control: `Keep existing baseline priority; h4_d1_long_best_box2_atr80 owns validated same-direction overlaps.`
- Replacement: `Replace only the validated overlapping h4_d1_long_best_box2_atr80 row with r1_long_expansion_r3_reclass_strict_r1.`
- Non-overlap: `Unchanged.`
- Same-direction window: `300` seconds.
- No month, hour, session, direction, profit, or outcome filter was used.
- W/L materiality: R3 W/L must meet the greater of baseline W/L + 0.20 or baseline W/L x 1.10.
- `r3_replaces_baseline_delta_dd`: replacement combined max closed DD minus current baseline-priority control combined max closed DD.

## Integrity Checks

| Check | Result |
| --- | --- |
| `control_full_partition_reconciles` | PASS |
| `control_kept_contains_all_baseline_rows` | PASS |
| `r3_partitions_into_nonoverlap_and_dropped` | PASS |
| `all_control_drops_are_r3` | PASS |
| `all_control_drops_point_to_box` | PASS |
| `overlap_pairs_are_one_to_one` | PASS |
| `all_pairs_within_5_minutes` | PASS |
| `no_r3_overlap_with_other_baseline_sources` | PASS |
| `replacement_trade_count_reconciles` | PASS |
| `control_and_replacement_share_max_dd_window` | PASS |
| `dd_window_attribution_reconciles_swap_delta` | PASS |

## Overlap Comparison

| Owner | Trades | WR% | W/L | PF | Net | Overlap-subset max closed DD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline box control | 110 | 58.18 | 1.9140 | 2.6630 | 4236.90 | 866.37 |
| R3 replacement | 110 | 66.36 | 1.8062 | 3.5635 | 6618.92 | 856.09 |

- Overlap count: `110`
- R3 dropped by current control: `110`
- Baseline overlap trades kept by current control: `110`
- R3 non-overlap: `29` trades / `$3523.80`
- Overlap net delta: `$2382.02`
- Overlap-subset DD delta: `-$10.28`

## Portfolio Recomposition

| Book | Trades | WR% | W/L | PF | Net | Stress net | Recent3 net | Max closed DD | +Months | Best month share% | Top10 rem | Top3 days rem |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `current_r1_r2_baseline` | 678 | 51.03 | 2.6082 | 2.7182 | 9640.05 | 9436.65 | 764.92 | 889.69 | 26 | 27.96 | 6731.40 | 7275.75 |
| `current_baseline_priority_control` | 707 | 51.91 | 2.9075 | 3.1384 | 13163.85 | 12951.75 | 764.92 | 1076.56 | 27 | 21.39 | 10087.27 | 10532.25 |
| `r3_priority_replacement_combined` | 707 | 53.18 | 3.0911 | 3.5113 | 15545.87 | 15333.77 | 764.92 | 1217.13 | 27 | 21.71 | 12055.93 | 12566.55 |

### Drawdown deltas

- Replacement vs current baseline-priority control: `$140.57`.
- Replacement vs R1+R2 baseline: `$327.44`.
- Replacement DD cap headroom: `-$193.99` (negative means over cap).

### Max-DD window attribution

The control and replacement share the same peak-to-trough window. 5 R3 replacements close $140.57 worse than 5 box counterparts inside that window, matching the $140.57 full-book DD increase.

- Window: `2025-04-02 23:46:32` peak exit to `2025-08-11 11:31:42` trough exit.
- Replaced box rows closing in window: `5` / `-$305.37`.
- R3 replacement rows closing in window: `5` / `-$445.94`.
- Window P/L deterioration: `-$140.57`; full-book DD increase: `$140.57`.

## Pass Gates

| Gate | Result |
| --- | --- |
| `overlap_count_ge_80` | PASS |
| `r3_overlap_net_gt_baseline_overlap_net` | PASS |
| `r3_overlap_pf_gte_baseline_overlap_pf` | PASS |
| `r3_overlap_wr_gte_baseline_or_wl_materially_higher` | PASS |
| `replacement_net_ge_baseline_plus_2000` | PASS |
| `replacement_stress_net_ge_baseline_plus_2000` | PASS |
| `replacement_wr_ge_50` | PASS |
| `replacement_wl_ge_2` | PASS |
| `replacement_pf_ge_2p50` | PASS |
| `replacement_dd_lte_115pct_baseline` | FAIL |
| `replacement_recent3_ge_baseline_minus_50` | PASS |
| `replacement_top10_removed_net_gt_0` | PASS |
| `replacement_top3_days_removed_net_gt_0` | PASS |
| `replacement_best_month_share_lte_30pct` | PASS |
| `replacement_positive_months_gte_baseline` | PASS |

Failed gates: `replacement_dd_lte_115pct_baseline`.

## Kill Rules

| Rule | Triggered |
| --- | --- |
| `r3_overlap_net_lte_baseline_overlap_net` | no |
| `replacement_dd_gt_115pct_baseline` | YES |
| `replacement_recent3_lt_baseline_minus_50` | no |
| `replacement_wr_lt_50` | no |
| `replacement_pf_lt_2p50` | no |
| `replacement_top10_concentration_fails` | no |
| `replacement_top3_day_concentration_fails` | no |

Triggered kill rules: `replacement_dd_gt_115pct_baseline`.

## ORDER_SEND_FAIL_RECONCILIATION

Both failures were valid long signals rejected because the tester returned MT5 retcode 10018 (market closed). The raw evidence cannot distinguish a genuine broker-session closure from a tester session-calendar artifact. They are unexecuted entry opportunities, not members of the 139-trade normalized ledger; no retry or outcome is imputed.

Counts: `139` ORDER_SEND_OK + `2` ORDER_SEND_FAIL; `139` normalized executed trades.

| Time | Side | Entry | SL | TP | Retcode | Reason | Previous OK | Next OK | Ledger trade at same time | Classification |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 2024.10.29 21:00:00 | LONG | 2774.21 | 2716.79 | 2889.05 | 10018 | market closed | 2024.10.29 16:00:00 | 2025.01.15 20:00:00 | False | `UNEXECUTED_SIGNAL_MARKET_CLOSED_HYPOTHETICAL_PNL_UNKNOWN` |
| 2025.03.27 21:00:00 | LONG | 3056.81 | 3002.85 | 3164.73 | 10018 | market closed | 2025.03.27 12:00:00 | 2025.03.28 04:00:00 | False | `UNEXECUTED_SIGNAL_MARKET_CLOSED_HYPOTHETICAL_PNL_UNKNOWN` |

No same-timestamp retry was logged. Any later accepted order was a distinct new signal. No hypothetical P/L was assigned to either failed order, and neither appears in the overlap audit.

## Closed vs MT5 Drawdown Evidence

| Book/evidence | Max closed DD | MT5 balance DD | MT5 equity DD |
| --- | ---: | ---: | ---: |
| R1+R2 baseline recomposition | 889.69 | n/a | n/a |
| R3 standalone exact MT5 | 856.09 | 856.09 | 1720.10 |
| Current control recomposition | 1076.56 | n/a | n/a |
| R3-priority replacement recomposition | 1217.13 | n/a | n/a |

Portfolio MT5 balance/equity DD is unavailable for the control and replacement because this task is ledger-only and did not run MT5. The replacement cannot be promoted from this diagnostic.

## Decision Boundary

- Do not tune R3 or add session/hour/month variants.
- Do not add R3 to the current R1+R2 baseline from ledger evidence alone.
- Do not run R3+shock, R3+transition, or a DD-governor repair.
- Keep R3 as a standalone shadow source; portfolio use is killed by the triggered hard rule.
- Do not run the conditional exact-MT5 source-priority test because the ledger audit did not pass.

## Inputs

- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709_current_r1_best_r2_pullback_plus_r2_impulse_body45_atr45_daily_loss10_KEPT.csv` — SHA256 `47cbe6a562ba2874d93a97255affbde613566ed06340a149ed2795d69a5dae52`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R1_LONG_EXPANSION_R3_RECLASS_EXACT_20260709_r1_long_expansion_r3_reclass_strict_r1_NORMALIZED_TRADES.csv` — SHA256 `af69cee52d2e8e5b0c1b45d506dfce9ccb71edbf6305305cbb9802f5d3d51c8a`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R1_LONG_EXPANSION_R3_RECLASS_EXACT_20260709_current_r1_r2_plus_r1_long_expansion_r3_reclass_strict_r1_KEPT.csv` — SHA256 `e71dac2cd86f35108f0792ab593370415138ed5b206d35ec98cf60d3fa06092b`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R1_LONG_EXPANSION_R3_RECLASS_EXACT_20260709_current_r1_r2_plus_r1_long_expansion_r3_reclass_strict_r1_DROPPED.csv` — SHA256 `a330c5ef482c1f0792513a89595fe83f64c0f8d2a8862606c9ff57f2f1969d86`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R1_LONG_EXPANSION_R3_RECLASS_EXACT_20260709_MT5.json` — SHA256 `ace68c11d079ce68ab17c62815a040023ef5de1c4cfe37580b8204c2aaf93293`
- `xau-usd/xauusd-phase1/outputs/reports/mt5_backtests/a1_momentum_variants_owner_goal_r1_long_expansion_r3_reclass_exact_202207_202606_20260701/A1XauM5Momentum_OWNER_GOAL_R1_LONG_EXPANSION_R3_RECLASS_EXACT_202207_202606_XAUUSD_M5_r1_long_expansion_r3_reclass_strict_r1_orders.csv` — SHA256 `9fac9e28f7a9a020ea65bae2192e73b8fc1a1a5988cda8f655f3443a8decfe8f`
- `xau-usd/xauusd-phase1/outputs/reports/mt5_backtests/a1_momentum_variants_owner_goal_r1_long_expansion_r3_reclass_exact_202207_202606_20260701/A1XauM5Momentum_OWNER_GOAL_R1_LONG_EXPANSION_R3_RECLASS_EXACT_202207_202606_XAUUSD_M5_r1_long_expansion_r3_reclass_strict_r1_signals.csv` — SHA256 `1cd9e92073e079b33da425aceb30543254bafdbd7f951194e9cb47e9335041c8`

## Artifacts

- report_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R1_BOX_R3_OVERLAP_PRIORITY_AUDIT_20260709.md`
- report_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R1_BOX_R3_OVERLAP_PRIORITY_AUDIT_20260709.json`
- summary_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R1_BOX_R3_OVERLAP_PRIORITY_AUDIT_20260709_SUMMARY.csv`
- overlap_pairs_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R1_BOX_R3_OVERLAP_PRIORITY_AUDIT_20260709_OVERLAP_PAIRS.csv`
- replacement_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R1_BOX_R3_OVERLAP_PRIORITY_AUDIT_20260709_REPLACEMENT_KEPT.csv`
