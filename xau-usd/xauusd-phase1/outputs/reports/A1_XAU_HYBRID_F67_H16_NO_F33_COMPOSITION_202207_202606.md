# A1 XAU Hybrid F67-H16 No-F33 Composition

Generated UTC: `2026-07-05T13:24:09Z`

Scope: exact-ledger portfolio composition only. The f67 hour-16 source was exact-MT5 replayed; unchanged component ledgers are reused from exact MT5 reports. No MT5 launch, live/demo runtime, chart, preset, order, position, or broker state was changed by this composition step.

Status: `EXACT_LEDGER_CORE_FRONTIER_ACTIVITY_GAP_NO_REVIEW`
Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_HYBRID_F67_H16_NO_F33_COMPOSITION_PREREG_2026_07_05.md`
Input raw exact-ledger CSV: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_HYBRID_F67_H16_EXACT_REPAIR_202207_202606_HYBRID_RAW.csv`

## Final Hybrid Metrics

| Signals | WR% | W/L | Active% | PF | Net USD | Max DD | Last12 WR/WL/Active | Stress -0.30 W/L | Decision |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| 3751 | 50.23 | 2.0002 | 86.39 | 2.0336 | 22294.46 | 1583.72 | 52.86/2.2118/80.84 | 1.9029 | `EXACT_LEDGER_CORE_FRONTIER_ACTIVITY_GAP_NO_REVIEW` |

## Composition Counts

- Raw rows before f33 removal: `5854`
- Removed f33 raw rows: `1885`
- Raw rows after f33 removal: `3969`
- Kept / dropped after dedupe: `3751` / `218`

## Source Contributions

| Source | Signals | Net USD |
| --- | ---: | ---: |
| `freq_step3_frontier` | 3417 | 6161.63 |
| `h4_d1_long_best_box2_atr80` | 332 | 15613.96 |
| `h4_d1_long_broad_box3_atr60` | 2 | 518.87 |

## Verdict

The exact-ledger composition clears WR and W/L by a razor-thin margin but remains below the 90% active-day threshold and fails the +0.30/ticket W/L stress. Keep as frontier evidence; do not draft a demo spec.

## Artifacts

- kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_HYBRID_F67_H16_NO_F33_COMPOSITION_202207_202606_KEPT.csv`
- dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_HYBRID_F67_H16_NO_F33_COMPOSITION_202207_202606_DROPPED.csv`
- removed_f33_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_HYBRID_F67_H16_NO_F33_COMPOSITION_202207_202606_REMOVED_F33.csv`
- json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_HYBRID_F67_H16_NO_F33_COMPOSITION_202207_202606.json`
- md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_HYBRID_F67_H16_NO_F33_COMPOSITION_202207_202606.md`
