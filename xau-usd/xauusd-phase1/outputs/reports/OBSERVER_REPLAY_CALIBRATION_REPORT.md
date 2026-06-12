# Observer Replay Calibration Report

Status: `PERMANENTLY_QUARANTINED_PENDING_NEW_DESIGN`

Read-only replay calibration. It compares broker-joined outcomes against M5 replay and does not touch MT5 runtime.

Replay model under test: `executor_v2`
Broker-joined rows: `81`
Closed broker rows: `81`
v1 outcome agreement: `43` / `81` = `53.09%`
v1 PnL-sign agreement: `43` / `81` = `53.09%`
v2 outcome agreement: `49` / `81` = `60.49%`
v2 PnL-sign agreement: `49` / `81` = `60.49%`

## By Symbol And Bucket

| symbol | time_bucket | rows | closed | outcome_match_count | outcome_match_pct |
| --- | --- | --- | --- | --- | --- |
| EURUSD | Night 20:00-05:59 | 2 | 2 | 0 | 0.0 |
| XAUUSD | Afternoon 12:00-15:59 | 13 | 13 | 7 | 53.85 |
| XAUUSD | Evening 16:00-19:59 | 10 | 10 | 8 | 80.0 |
| XAUUSD | Morning 06:00-11:59 | 24 | 24 | 14 | 58.33 |
| XAUUSD | Night 20:00-05:59 | 32 | 32 | 20 | 62.5 |

## By Candidate

| candidate | rows | closed | outcome_match_count | outcome_match_pct |
| --- | --- | --- | --- | --- |
| breakout_retest | 1 | 1 | 0 | 0.0 |
| round_number_retest_v0 | 40 | 40 | 25 | 62.5 |
| swing_breakout_retest_v0 | 1 | 1 | 0 | 0.0 |
| symbol_normalized_round_retest_v0 | 39 | 39 | 24 | 61.54 |

## Rule

- >=90% outcome agreement: replay rows are usable.
- 75-90% outcome agreement: replay rows are usable with a disclosed error bar.
- <75% outcome agreement after executor_v2 means `PERMANENTLY_QUARANTINED_PENDING_NEW_DESIGN`; scoreboards must be broker-joined-only.
