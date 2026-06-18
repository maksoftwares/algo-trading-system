# A3 Signal Quality Offline Discovery - 2026-06-18

Status: `PASS`
Decision: `STOP_NO_CANDIDATE`

Offline discovery only. M5 bar replay is not promotion evidence. No MT5 runtime, profile, preset, order, position, or broker action touched.

Raw signals: `131`
Closed raw outcomes: `131`
Data status: `DATA_LIMITED_M5_BAR_REPLAY_NOT_PROMOTION_EVIDENCE`

## Candidate Metrics

| Candidate | Role | Signals | Signal Ret. | Trades | Trade Ret. | Closed | WR | Net PF | Net Exp R | Net R | P95 Cost R | Bad Signal | Giveback | Eligible |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| B0_RAW_ALL_SESSION | BASELINE | 131 | 100.0 | 90 | 100.0 | 90 | 50.0 | 1.2939 | 0.1608 | 14.4722 | 0.1592 | 44.44 | 44.44 | False |
| B1_EVENING_BASELINE | BASELINE | 32 | 24.43 | 19 | 21.11 | 19 | 68.42 | 2.8497 | 0.6377 | 12.1169 | 0.1424 | 33.33 | 66.67 | False |
| F_LOOSE_CT_VETO | DIAGNOSTIC_DISCOVERY_ONLY | 82 | 62.6 | 59 | 65.56 | 59 | 50.85 | 1.3451 | 0.1846 | 10.8929 | 0.1543 | 48.28 | 37.93 | False |
| F_H1_ALIGN | DIAGNOSTIC_DISCOVERY_ONLY | 82 | 62.6 | 59 | 65.56 | 59 | 50.85 | 1.3451 | 0.1846 | 10.8929 | 0.1543 | 48.28 | 37.93 | False |
| F_H1_M15_ALIGN | DIAGNOSTIC_DISCOVERY_ONLY | 68 | 51.91 | 49 | 54.44 | 49 | 48.98 | 1.259 | 0.1432 | 7.0177 | 0.1419 | 48.0 | 40.0 | False |
| F_RETEST_LIGHT | DIAGNOSTIC_DISCOVERY_ONLY | 24 | 18.32 | 21 | 23.33 | 21 | 57.14 | 1.7045 | 0.3325 | 6.9825 | 0.1346 | 11.11 | 66.67 | False |
| F_LOOSE_CT_PLUS_RETEST_LIGHT | DIAGNOSTIC_DISCOVERY_ONLY | 20 | 15.27 | 17 | 18.89 | 17 | 52.94 | 1.4385 | 0.2275 | 3.8674 | 0.1565 | 12.5 | 62.5 | False |
| A3_SQ_MTF_ONLY_V1 | LOCKED_V1_DIAGNOSTIC | 0 | 0.0 | 0 | 0.0 | 0 | None | None | None | 0 | None | None | None | False |
| A3_SQ_RETEST_ONLY_V1 | LOCKED_V1_DIAGNOSTIC | 2 | 1.53 | 2 | 2.22 | 2 | 50.0 | 1.307 | 0.1646 | 0.3293 | 0.0968 | 0.0 | 100.0 | False |
| A3_SQ_COMBINED_V1 | LOCKED_V1_PROMOTION_ELIGIBLE_AFTER_FORWARD_EVIDENCE_ONLY | 0 | 0.0 | 0 | 0.0 | 0 | None | None | None | 0 | None | None | None | False |

## Interpretation

- This is a cheap offline discovery screen, not promotion evidence.
- PF, expectancy, net R, drawdown, and eligibility are computed on net R after subtracting `cost_r`.
- M5 bar replay is conservative/coarse and does not replace forward tick-level validation.
- Any selected diagnostic would need a new locked V2 and a fresh validation window.
- If the decision is `STOP_NO_CANDIDATE`, A3 remains paused and the MQL5 forward apparatus should not be built from this discovery window.

## Outputs

- json: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A3_SIGNAL_QUALITY_SQ03_OFFLINE_DISCOVERY_2026_06_18.json`
- markdown: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A3_SIGNAL_QUALITY_SQ03_OFFLINE_DISCOVERY_2026_06_18.md`
- decisions_csv: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A3_SIGNAL_QUALITY_SQ03_OFFLINE_DISCOVERY_DECISIONS_2026_06_18.csv`
- trades_csv: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A3_SIGNAL_QUALITY_SQ03_OFFLINE_DISCOVERY_TRADES_2026_06_18.csv`
- data_manifest: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A3_SIGNAL_QUALITY_SQ03_OFFLINE_DISCOVERY_DATA_MANIFEST_2026_06_18.json`
