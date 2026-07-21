# Source Contract

- Instrument: Dukascopy `VOL.IDX/USD` (`VOLIDXUSD`).
- Official origin: `https://jetta.dukascopy.com/v1`.
- Source period: `2023-01-01T00:00:00Z` to `2026-07-01T00:00:00Z` exclusive.
- Maximum acquisition concurrency: sixteen.
- No paid source, Databento, broker action, XAUUSD outcome, strategy score, or
  execution authority is permitted.
- M5 features are timestamped by bar open and become usable only at
  `available_timestamp_ms = bar_open_timestamp_ms + 300000`.
- No forward fill is performed across a missing M5 bar.
- Raw hourly payloads and their monthly manifests are immutable inputs.
- Crossed or non-positive official quotes are excluded and counted. Any nonempty
  hour with more than 10% invalid quotes fails source validation.
