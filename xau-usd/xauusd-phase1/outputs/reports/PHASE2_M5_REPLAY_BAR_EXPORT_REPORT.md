# Phase 2 M5 Replay Bar Export

Status: `PASS`

Read-only M5 replay-bar export for observer outcome scoring. It copies history rates only and does not touch MT5 charts, profiles, orders, positions, or EA settings.

Requested window UTC: `2026-06-01 00:00:00` to `2026-06-12 09:19:13`
Output dir: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\m5_replay_bars`

## Continuity

| Symbol | Status | Rows | First bar UTC | Last bar UTC | Gaps >5m | Max gap min | Duplicates | Continuity % |
| --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: |
| XAUUSD | WARN_GAPS_OR_DUPLICATES | 2596 | 2026-06-01 00:00:00 | 2026-06-12 09:15:00 | 9 | 2945.0 | 0 | 79.15 |
| EURUSD | WARN_GAPS_OR_DUPLICATES | 2696 | 2026-06-01 00:00:00 | 2026-06-12 09:15:00 | 9 | 2885.0 | 0 | 82.20 |
| GBPUSD | WARN_GAPS_OR_DUPLICATES | 2696 | 2026-06-01 00:00:00 | 2026-06-12 09:15:00 | 9 | 2885.0 | 0 | 82.20 |
| USDJPY | WARN_GAPS_OR_DUPLICATES | 1611 | 2026-06-01 00:00:00 | 2026-06-08 14:30:00 | 5 | 2885.0 | 0 | 73.53 |

## Boundary

- Read-only history export.
- No chart attachments, order placement, position changes, profile changes, or EA setting changes.
- Gaps are reported explicitly so partial exports cannot silently drive replay conclusions.
