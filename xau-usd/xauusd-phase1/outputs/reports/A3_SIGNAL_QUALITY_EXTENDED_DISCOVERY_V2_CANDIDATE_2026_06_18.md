# A3 Signal Quality Extended Discovery V2 Candidate - 2026-06-18

Status: `PASS`
Decision: `SELECT_CANDIDATE_FOR_V2_LOCK`

Offline historical discovery only. Uses phase0 Dukascopy XAUUSD bars. No MT5 runtime, profile, preset, order, position, or broker action touched.

## Selected Candidate

Candidate: `A3_SQ_SOFT_RETEST_W15_B45_C60_RCM05_V2`

| Metric | B0 | Candidate |
| --- | ---: | ---: |
| Accepted signals | 1453 | 586 |
| Signal retention | 100.0% | 40.33% |
| Opened virtual trades | 885 | 490 |
| Trade retention vs B0 | 100.0% | 55.37% |
| Median weekly trade retention | 100.0% | 59.38% |
| Profit factor | 1.2484 | 1.9186 |
| Expectancy R | 0.1356 | 0.4031 |
| Win rate | 45.42% | 56.12% |
| Bad-signal loss share | 50.1% | 35.81% |
| Bad-signal improvement | 0.0% | 28.52% |
| Max consecutive losses | 14 | 6 |
| Max drawdown R | 20.5 | 7.5 |

## Candidate Rule

- `candidate_id`: A3_SQ_SOFT_RETEST_W15_B45_C60_RCM05_V2
- `family`: breakout_retest
- `bars_after_break`: 1..15 completed M5 bars
- `retest_close_margin`: LONG retest close >= level + 0.05 ATR; SHORT retest close <= level - 0.05 ATR
- `confirmation_body_to_range`: >= 0.45
- `confirmation_directional_close_location`: LONG close location >= 0.60; SHORT close location <= 0.40
- `exit_model`: fixed 1.50R, unchanged
- `position_model`: one virtual position per candidate

## Interpretation

- This selects a V2 hypothesis candidate for a fresh validation window.
- This is not promotion evidence and does not authorize A3 reactivation.
- The June 2026 SQ-03 window remains too small for the 100-trade gate; its maximum one-position schedule is below 100.

## Outputs

- json: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A3_SIGNAL_QUALITY_EXTENDED_DISCOVERY_V2_CANDIDATE_2026_06_18.json`
- markdown: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A3_SIGNAL_QUALITY_EXTENDED_DISCOVERY_V2_CANDIDATE_2026_06_18.md`
- trades_csv: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A3_SIGNAL_QUALITY_EXTENDED_DISCOVERY_V2_CANDIDATE_TRADES_2026_06_18.csv`
