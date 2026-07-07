# A1 XAU Event Red-Week Overlay Audit

Generated UTC: `2026-07-07T11:43:16Z`

Scope: offline recomposition of already-generated exact-MT5 event-reaction V0 ledgers onto the corrected supportive-guard book. No new MT5 run, tuning sweep, live/demo runtime, chart, preset, order, position, or broker state change.

Baseline: `supportive_guard_session_parity`
Status: `NO_EVENT_OVERLAY_RED_WEEK_SURVIVOR`

## Results

| Combo | Signals | WR% | W/L | Active% | Net | Stress W/L | Pos weeks% | Delta pp | Worst week | Event kept | Event net | Red touched | Red flipped | Red worsened | Event red net | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `event_impulse_fomc_rr2_only` | 3659 | 50.42 | 2.0859 | 85.91 | 20757.31 | 1.9688 | 57.21 | -0.48 | -878.18 | 15 | 79.91 | 6 | 0 | 4 | -21.79 | `REJECT_WEEKLY_NOT_IMPROVED` |
| `event_fade_cpi_rr2_only` | 3672 | 50.35 | 2.0886 | 85.91 | 20718.94 | 1.9710 | 57.21 | -0.48 | -878.18 | 28 | 40.73 | 11 | 0 | 8 | -19.12 | `REJECT_WEEKLY_NOT_IMPROVED` |
| `event_fomc_impulse_plus_cpi_fade` | 3686 | 50.38 | 2.0851 | 86.10 | 20774.84 | 1.9678 | 56.73 | -0.96 | -878.18 | 43 | 120.64 | 16 | 0 | 11 | -40.91 | `REJECT_WEEKLY_NOT_IMPROVED` |
| `event_all_v0_positive_net` | 3729 | 50.25 | 2.0839 | 86.58 | 20838.83 | 1.9668 | 57.69 | 0.00 | -878.18 | 86 | 184.63 | 28 | 3 | 19 | -102.59 | `REJECT_WEEKLY_NOT_IMPROVED` |
| `event_all_v0_including_negative_control` | 3750 | 50.13 | 2.0890 | 86.67 | 20820.57 | 1.9714 | 57.69 | 0.00 | -878.18 | 107 | 166.37 | 33 | 3 | 23 | -102.01 | `REJECT_WEEKLY_NOT_IMPROVED` |

## Interpretation

The exact-MT5 event V0 ledgers are too sparse to repair weekly shape. They do not flip enough red weeks and do not move the corrected supportive-guard book toward the 70-80% weekly target. This weakens the event-overlay path.

## Artifacts

- md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_EVENT_RED_WEEK_OVERLAY_AUDIT_202207_202606.md`
- json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_EVENT_RED_WEEK_OVERLAY_AUDIT_202207_202606.json`
- results_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_EVENT_RED_WEEK_OVERLAY_AUDIT_202207_202606_RESULTS.csv`
- event_impulse_fomc_rr2_only_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_EVENT_RED_WEEK_OVERLAY_AUDIT_202207_202606_event_impulse_fomc_rr2_only_KEPT.csv`
- event_impulse_fomc_rr2_only_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_EVENT_RED_WEEK_OVERLAY_AUDIT_202207_202606_event_impulse_fomc_rr2_only_DROPPED.csv`
- event_fade_cpi_rr2_only_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_EVENT_RED_WEEK_OVERLAY_AUDIT_202207_202606_event_fade_cpi_rr2_only_KEPT.csv`
- event_fade_cpi_rr2_only_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_EVENT_RED_WEEK_OVERLAY_AUDIT_202207_202606_event_fade_cpi_rr2_only_DROPPED.csv`
- event_fomc_impulse_plus_cpi_fade_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_EVENT_RED_WEEK_OVERLAY_AUDIT_202207_202606_event_fomc_impulse_plus_cpi_fade_KEPT.csv`
- event_fomc_impulse_plus_cpi_fade_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_EVENT_RED_WEEK_OVERLAY_AUDIT_202207_202606_event_fomc_impulse_plus_cpi_fade_DROPPED.csv`
- event_all_v0_positive_net_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_EVENT_RED_WEEK_OVERLAY_AUDIT_202207_202606_event_all_v0_positive_net_KEPT.csv`
- event_all_v0_positive_net_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_EVENT_RED_WEEK_OVERLAY_AUDIT_202207_202606_event_all_v0_positive_net_DROPPED.csv`
- event_all_v0_including_negative_control_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_EVENT_RED_WEEK_OVERLAY_AUDIT_202207_202606_event_all_v0_including_negative_control_KEPT.csv`
- event_all_v0_including_negative_control_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_EVENT_RED_WEEK_OVERLAY_AUDIT_202207_202606_event_all_v0_including_negative_control_DROPPED.csv`
