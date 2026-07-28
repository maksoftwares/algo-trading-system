# EURUSD Neutral prospective consensus capture

## State

`CAPTURE_PIPELINE_ACTIVE_NO_FORECAST_ROWS_YET`

An append-only point-in-time capture pipeline is now active for the exact
TradingView CPI MoM, PPI MoM, and NFP tickers. It requires no account or OTP.
It is evidence collection only and cannot place demo or live orders.

## Why this was necessary

The historical consensus archive materially improved source quality, but its
JSON responses were downloaded after the events. The forecast field looked
plausible and reconciled correctly, yet its pre-release existence could not be
proved independently.

The new pipeline records:

- the exact raw HTTP response;
- local request start and finish timestamps;
- the provider/CDN HTTP `Date`;
- response-cache headers;
- an immutable metadata record;
- a normalized snapshot containing only forecasts observed strictly before
  release with no actual present;
- SHA-256 for every artifact; and
- a deterministic chain across every raw, metadata, and normalized snapshot.

Existing evidence files are opened with exclusive-create semantics. A retry
with identical bytes is harmless; different bytes can never overwrite the
prior snapshot.

## First capture

The first public request covered 28 July through 26 September 2026.

- Local request: 2026-07-28 12:42:41-12:42:42 UTC.
- Provider HTTP date: 2026-07-28 12:42:50 UTC.
- Raw SHA-256:
  `338a35c9d58b15c3a429b6456646a21670b8b9b42ca183b794aa091e874a447b`.
- Evidence-chain SHA-256:
  `235c645e2b939027d495f38152ede4b760b1d88758ae8fd3348f3aa873fdc09d`.
- Manifest SHA-256:
  `9cec7db675a29e6298441eafad615d2de26545b1fcbfb9e594c155777a2bc7e6`.
- Admissible pre-release forecast rows: zero.

Zero rows is the correct outcome. The response already contained the three
future target events, but their forecasts were still null:

| Family | Scheduled UTC time | Forecast at capture | Previous |
|---|---|---:|---:|
| NFP | 2026-08-07 12:30 | null | 57,000 |
| CPI MoM | 2026-08-12 12:30 | null | -0.4 |
| PPI MoM | 2026-08-13 12:30 | null | -0.3 |

The null snapshot is retained permanently. It proves the pipeline did not
backfill a later forecast into an earlier observation.

## Admission contract

A normalized forecast row is admitted only when all conditions hold:

1. the ticker is exactly CPI MoM, PPI MoM, or NFP;
2. the provider HTTP/local evidence time is at least 60 seconds before the
   scheduled event;
3. the actual field is absent;
4. the forecast field is present; and
5. the raw response and normalized row reference the same immutable SHA-256.

Released events, rows with an actual, missing forecasts, wrong tickers, and
last-minute race-condition captures stay out.

## Capture cadence

Run the same command repeatedly as releases approach. Each invocation creates
new immutable files; it never revises a prior observation.

```powershell
uv run --with pandas --with pyarrow python capture_prospective_tradingview_consensus.py capture --days-ahead 60
```

For a final pre-release observation, run it again during the hour before the
event while retaining more than the 60-second safety margin. Later strategy
evaluation must select the latest admissible snapshot strictly before that
event.

## Remaining boundary

This pipeline fixes the point-in-time forecast problem. It does not rescue any
rejected historical strategy or establish profitability. Regime 1 remains
cash until an unchanged causal rule passes a sufficient untouched prospective
sample.
