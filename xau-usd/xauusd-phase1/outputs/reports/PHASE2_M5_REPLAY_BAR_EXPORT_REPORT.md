# Phase 2 M5 Replay Bar Export

Status: `PASS`

Read-only M5 replay-bar export for observer outcome scoring. It copies history rates only and does not touch MT5 charts, profiles, orders, positions, or EA settings.

Requested window UTC: `2026-06-01 00:00:00` to `2026-06-13 21:51:43`
Output dir: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\m5_replay_bars`

## Continuity

| Symbol | Timeframe | Status | Rows | First bar UTC | Last bar UTC | Gaps >5m | Max gap min | Duplicates | Continuity % |
| --- | --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: |
| XAUUSD | M5 | WARN_GAPS_OR_DUPLICATES | 2736 | 2026-06-01 00:00:00 | 2026-06-12 20:55:00 | 9 | 2945.0 | 0 | 80.00 |
| XAUUSD | H1 | WARN_GAPS_OR_DUPLICATES | 228 | 2026-06-01 00:00:00 | 2026-06-12 20:00:00 | 227 | 3000.0 | 0 | 6.69 |
| XAUUSD | H4 | WARN_GAPS_OR_DUPLICATES | 61 | 2026-06-01 00:00:00 | 2026-06-12 20:00:00 | 60 | 2880.0 | 0 | 1.79 |
| XAUUSD | D1 | WARN_GAPS_OR_DUPLICATES | 11 | 2026-06-01 00:00:00 | 2026-06-12 00:00:00 | 10 | 2880.0 | 0 | 0.35 |
| EURUSD | M5 | WARN_GAPS_OR_DUPLICATES | 2836 | 2026-06-01 00:00:00 | 2026-06-12 20:55:00 | 9 | 2885.0 | 0 | 82.92 |
| EURUSD | H1 | WARN_GAPS_OR_DUPLICATES | 237 | 2026-06-01 00:00:00 | 2026-06-12 20:00:00 | 236 | 2940.0 | 0 | 6.95 |
| EURUSD | H4 | WARN_GAPS_OR_DUPLICATES | 61 | 2026-06-01 00:00:00 | 2026-06-12 20:00:00 | 60 | 2880.0 | 0 | 1.79 |
| EURUSD | D1 | WARN_GAPS_OR_DUPLICATES | 11 | 2026-06-01 00:00:00 | 2026-06-12 00:00:00 | 10 | 2880.0 | 0 | 0.35 |
| GBPUSD | M5 | WARN_GAPS_OR_DUPLICATES | 2836 | 2026-06-01 00:00:00 | 2026-06-12 20:55:00 | 9 | 2885.0 | 0 | 82.92 |
| GBPUSD | H1 | WARN_GAPS_OR_DUPLICATES | 237 | 2026-06-01 00:00:00 | 2026-06-12 20:00:00 | 236 | 2940.0 | 0 | 6.95 |
| GBPUSD | H4 | WARN_GAPS_OR_DUPLICATES | 61 | 2026-06-01 00:00:00 | 2026-06-12 20:00:00 | 60 | 2880.0 | 0 | 1.79 |
| GBPUSD | D1 | WARN_GAPS_OR_DUPLICATES | 11 | 2026-06-01 00:00:00 | 2026-06-12 00:00:00 | 10 | 2880.0 | 0 | 0.35 |
| USDJPY | M5 | WARN_GAPS_OR_DUPLICATES | 2836 | 2026-06-01 00:00:00 | 2026-06-12 20:55:00 | 9 | 2885.0 | 0 | 82.92 |
| USDJPY | H1 | WARN_GAPS_OR_DUPLICATES | 237 | 2026-06-01 00:00:00 | 2026-06-12 20:00:00 | 236 | 2940.0 | 0 | 6.95 |
| USDJPY | H4 | WARN_GAPS_OR_DUPLICATES | 61 | 2026-06-01 00:00:00 | 2026-06-12 20:00:00 | 60 | 2880.0 | 0 | 1.79 |
| USDJPY | D1 | WARN_GAPS_OR_DUPLICATES | 11 | 2026-06-01 00:00:00 | 2026-06-12 00:00:00 | 10 | 2880.0 | 0 | 0.35 |

## Boundary

- Read-only history export.
- No chart attachments, order placement, position changes, profile changes, or EA setting changes.
- Gaps are reported explicitly so partial exports cannot silently drive replay conclusions.
