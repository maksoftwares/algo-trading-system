# A3 Signal Quality Offline Discovery - 2026-06-18

Status: `PASS`
Decision: `STOP_NO_CANDIDATE`

Offline discovery only. M5 bar replay is not promotion evidence. No MT5 runtime, profile, preset, order, position, or broker action touched.

Raw signals: `131`
Closed raw outcomes: `131`
Data status: `DATA_LIMITED_M5_BAR_REPLAY_NOT_PROMOTION_EVIDENCE`

## Candidate Metrics

| Candidate | Role | Signals | Signal Ret. | Trades | Trade Ret. | Closed | WR | PF | Exp R | Net R | Bad Signal | Giveback | Eligible |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| B0_RAW_ALL_SESSION | BASELINE | 131 | 100.0 | 90 | 68.7 | 90 | 50.0 | 1.5 | 0.25 | 22.5 | 44.44 | 44.44 | False |
| B1_EVENING_BASELINE | BASELINE | 32 | 24.43 | 19 | 14.5 | 19 | 68.42 | 3.25 | 0.7105 | 13.5 | 33.33 | 66.67 | False |
| F_LOOSE_CT_VETO | DIAGNOSTIC_DISCOVERY_ONLY | 82 | 62.6 | 59 | 45.04 | 59 | 50.85 | 1.5517 | 0.2712 | 16.0 | 48.28 | 37.93 | False |
| F_H1_ALIGN | DIAGNOSTIC_DISCOVERY_ONLY | 82 | 62.6 | 59 | 45.04 | 59 | 50.85 | 1.5517 | 0.2712 | 16.0 | 48.28 | 37.93 | False |
| F_H1_M15_ALIGN | DIAGNOSTIC_DISCOVERY_ONLY | 68 | 51.91 | 49 | 37.4 | 49 | 48.98 | 1.44 | 0.2245 | 11.0 | 48.0 | 40.0 | False |
| F_RETEST_LIGHT | DIAGNOSTIC_DISCOVERY_ONLY | 24 | 18.32 | 21 | 16.03 | 21 | 57.14 | 2.0 | 0.4286 | 9.0 | 11.11 | 66.67 | False |
| F_LOOSE_CT_PLUS_RETEST_LIGHT | DIAGNOSTIC_DISCOVERY_ONLY | 20 | 15.27 | 17 | 12.98 | 17 | 52.94 | 1.6875 | 0.3235 | 5.5 | 12.5 | 62.5 | False |
| A3_SQ_MTF_ONLY_V1 | LOCKED_V1_DIAGNOSTIC | 0 | 0.0 | 0 | 0.0 | 0 | None | None | None | 0 | None | None | False |
| A3_SQ_RETEST_ONLY_V1 | LOCKED_V1_DIAGNOSTIC | 2 | 1.53 | 2 | 1.53 | 2 | 50.0 | 1.5 | 0.25 | 0.5 | 0.0 | 100.0 | False |
| A3_SQ_COMBINED_V1 | LOCKED_V1_PROMOTION_ELIGIBLE_AFTER_FORWARD_EVIDENCE_ONLY | 0 | 0.0 | 0 | 0.0 | 0 | None | None | None | 0 | None | None | False |

## Interpretation

- This is a cheap offline discovery screen, not promotion evidence.
- M5 bar replay is conservative/coarse and does not replace forward tick-level validation.
- Any selected diagnostic would need a new locked V2 and a fresh validation window.
- If the decision is `STOP_NO_CANDIDATE`, A3 remains paused and the MQL5 forward apparatus should not be built from this discovery window.

## Outputs

- json: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A3_SIGNAL_QUALITY_SQ03_OFFLINE_DISCOVERY_2026_06_18.json`
- markdown: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A3_SIGNAL_QUALITY_SQ03_OFFLINE_DISCOVERY_2026_06_18.md`
- decisions_csv: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A3_SIGNAL_QUALITY_SQ03_OFFLINE_DISCOVERY_DECISIONS_2026_06_18.csv`
- trades_csv: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A3_SIGNAL_QUALITY_SQ03_OFFLINE_DISCOVERY_TRADES_2026_06_18.csv`
- data_manifest: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A3_SIGNAL_QUALITY_SQ03_OFFLINE_DISCOVERY_DATA_MANIFEST_2026_06_18.json`
