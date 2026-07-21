# Source Contract

- Origin: `https://jetta.dukascopy.com/v1` only.
- Period: `2022-01-01T00:00:00Z` through `2026-07-01T00:00:00Z`, end exclusive.
- Instruments: `USA500.IDX-USD`, `COPPER.CMD-USD`, and `USD-CNH`.
- Granularity: official hourly tick payloads, aggregated locally to completed M5 bars.
- Raw preservation: deterministic gzip plus hashes of compressed and exact expanded bytes.
- Availability: a bar is usable only at its recorded five-minute close.
- Missing bars are never forward-filled when returns are calculated.
- Crossed, nonpositive, nonfinite, or off-hour quotes invalidate their source hour.
- Paid data and Databento are prohibited.
- XAU outcomes, labels, strategy scoring, model training, and broker actions are prohibited.

Collecting this source does not preregister or authorize a trading hypothesis.
Any later campaign must lock its mechanics, attempts, stages, costs, gates, and
shared-account rules before opening XAUUSD outcomes.
