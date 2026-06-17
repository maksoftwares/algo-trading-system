# Phase 2 M5 Replay Bar Export

Status: `PASS`

Read-only M5 replay-bar export for observer outcome scoring. It copies history rates only and does not touch MT5 charts, profiles, orders, positions, or EA settings.

Requested window UTC: `2026-06-01 00:00:00` to `2026-06-16 06:40:11`
Output dir: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\m5_replay_bars`

## Continuity

| Symbol | Timeframe | Status | Rows | First bar UTC | Last bar UTC | Gaps >5m | Max gap min | Duplicates | Continuity % |
| --- | --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: |
| XAUUSD | M5 | WARN_GAPS_OR_DUPLICATES | 3117 | 2026-06-01 00:00:00 | 2026-06-16 06:40:00 | 11 | 2945.0 | 0 | 70.82 |
| EURUSD | M5 | WARN_GAPS_OR_DUPLICATES | 3240 | 2026-06-01 00:00:00 | 2026-06-16 06:40:00 | 11 | 2885.0 | 0 | 73.62 |
| GBPUSD | M5 | WARN_GAPS_OR_DUPLICATES | 3240 | 2026-06-01 00:00:00 | 2026-06-16 06:40:00 | 11 | 2885.0 | 0 | 73.62 |
| USDJPY | M5 | WARN_GAPS_OR_DUPLICATES | 2836 | 2026-06-01 00:00:00 | 2026-06-12 20:55:00 | 9 | 2885.0 | 0 | 82.92 |

## Boundary

- Read-only history export.
- No chart attachments, order placement, position changes, profile changes, or EA setting changes.
- Gaps are reported explicitly so partial exports cannot silently drive replay conclusions.
