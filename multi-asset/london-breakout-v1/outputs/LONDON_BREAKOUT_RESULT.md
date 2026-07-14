# Multi-Asset London Range Expansion Fast Discovery V1

- Branch: `codex/multiasset-london-breakout-fast-discovery-v1`
- Base: `68a9988d51d04fe0c5812792e7c347570b75fb27`
- Base tree: `a769ab1bcaf3311a2004db7cf6f05928aabfa729`
- Classification: `LONDON_BREAKOUT_V1_DATA_INADEQUATE_NO_SCORING`
- Strategy scoring performed: `false`
- Parameter search count: `0`

## Mandatory pre-scoring gate

Complete trustworthy instruments: `0` / `3`.

| Instrument | H1 | M15 | M5 | Historical execution source | Earliest terminal tick returned | Trustworthy full period |
| --- | --- | --- | --- | --- | --- | --- |
| XAUUSD | True | True | True | BAR_OHLC_PLUS_SINGLE_SPREAD_FIELD | 2026-05-06T00:00:00.291000+00:00 | False |
| EURUSD | True | True | True | BAR_OHLC_PLUS_SINGLE_SPREAD_FIELD | 2025-03-11T12:54:25.900000+00:00 | False |
| GBPUSD | False | False | False | MISSING | 2025-03-11T12:54:25.888000+00:00 | False |
| USDJPY | True | True | True | BAR_OHLC_PLUS_SINGLE_SPREAD_FIELD | 2025-03-11T12:54:26.774000+00:00 | False |

The existing historical bars contain OHLC plus one spread field, not raw executable Bid/Ask ticks. The connected terminal does not supply ticks back to 2016-07-01, and GBPUSD has no repository Capital.com bar set. Under the frozen authorization, bar-spread reconstruction is insufficient for promotion and fewer than three trustworthy instruments requires stopping before strategy scoring.

## Disposition

No signal generation, trade replay, parameter search, instrument selection, economic scoring or portfolio construction was performed. No EA, deployment, demo/live execution, broker order or risk increase is authorized.
