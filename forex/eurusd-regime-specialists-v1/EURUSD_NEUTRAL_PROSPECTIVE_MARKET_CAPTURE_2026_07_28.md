# EURUSD Neutral prospective market capture

## State

`CAPTURE_IMPLEMENTATION_FROZEN_WAITING_FOR_FIRST_ELIGIBLE_RELEASE`

The public market-data half of the prospective specialist is now complete. It
downloads only the hourly Dukascopy tick responses needed around a specified
release for EURUSD, DXY, and the US Treasury bond CFD. No account, OTP, or paid
feed is required.

## Information boundary

The collector refuses to make a request until three post-release M5 bars are
fully complete plus a 60-second safety lag. It then:

- preserves every raw hourly JSON response byte-for-byte;
- records request, provider HTTP, and observation timestamps;
- decodes cumulative tick deltas using the frozen Dukascopy convention;
- constructs only fully completed UTC-aligned M5 bars;
- extracts the last completed pre-event midpoint and third completed
  post-event midpoint;
- excludes the entry bar from confirmation;
- appends a normalized Parquet row and manifest; and
- chains every raw, metadata, and normalized artifact with SHA-256.

Missing EURUSD, DXY, or Treasury bars produce cash rather than a filled or
forward-filled reaction.

The existing no-login prospective DXY/Treasury pipeline was independently
observed active through 2026-07-28 12:00 UTC. This event-specific collector
adds the missing EURUSD leg and stores all three legs under one linked
manifest.

## Usage

After an eligible release's observation window:

```powershell
uv run --with pandas --with pyarrow python capture_prospective_dukascopy_event_m5.py capture --event-time 2026-08-07T12:30:00Z
```

The command is data-only. It cannot place a demo or live order.
