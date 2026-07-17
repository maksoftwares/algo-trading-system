# CFTC Gold Options Positioning Foundation V1

This package acquires the official CFTC disaggregated gold Commitments of
Traders records for:

- futures only; and
- futures and options combined.

The curated dataset pairs records by report date and subtracts futures-only
positions from combined positions. CFTC describes this as a way to estimate
options positions, with some spreading information lost. The resulting values
are delta-equivalent positioning measures, not an option-volatility surface.

Each report is assigned a conservative `available_utc` of the first Monday
strictly after its as-of date at 00:00 UTC. This also handles holiday-dated
reports. Research code must join on `available_utc`, never on the report date.

Raw and curated data live outside the repository by default at
`C:/CftcGoldOptionsPositioningV1`. No API key, subscription, payment, broker
action, or Databento access is used.

```powershell
python acquire.py
```
