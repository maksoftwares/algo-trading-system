# London Historical Bar Quote-Contract Closure V1

**THIS IS A DATA-CONTRACT AUDIT**

**NOT A STRATEGY OPTIMIZATION | NOT A PROFITABILITY RESULT | NOT DEPLOYMENT EVIDENCE**

**Classification:** `LONDON_QUOTE_CONTRACT_UNRESOLVED_CLOSE_BAR_ROUTE`

## XAUUSD

- Classification: `PROVENANCE_CHAIN_INCOMPLETE`
- Provenance: `PROVENANCE_CHAIN_INCOMPLETE`
- Tick overlap: `NONE` to `NONE`
- Complete days / comparable M5 bars: `0` / `0`
- Selected quote basis: `UNKNOWN`
- Selected spread statistic: `UNKNOWN`
- Quote alternatives: `BID: open=0.000000%, high=0.000000%, low=0.000000%, close=0.000000% | ASK: open=0.000000%, high=0.000000%, low=0.000000%, close=0.000000% | MID: open=0.000000%, high=0.000000%, low=0.000000%, close=0.000000% | LAST: open=0.000000%, high=0.000000%, low=0.000000%, close=0.000000%`
- Spread alternatives: `BAR_OPEN_SPREAD: exact=0.000000%, within1=0.000000% | BAR_CLOSE_SPREAD: exact=0.000000%, within1=0.000000% | BAR_MINIMUM_SPREAD: exact=0.000000%, within1=0.000000% | BAR_MAXIMUM_SPREAD: exact=0.000000%, within1=0.000000% | BAR_MEAN_SPREAD: exact=0.000000%, within1=0.000000% | BAR_MEDIAN_SPREAD: exact=0.000000%, within1=0.000000%`
- M15/H1 consistency: `True` / `True`
- Failed gates: `provenance_completeness | tick_overlap_days | tick_overlap_bars | m5_open_match | m5_high_match | m5_low_match | m5_close_match | alternative_basis_separation | spread_match | spread_unit_conversion | timestamp_alignment`

## EURUSD

- Classification: `PROVENANCE_CHAIN_INCOMPLETE`
- Provenance: `PROVENANCE_CHAIN_INCOMPLETE`
- Tick overlap: `2025-03-11T12:54:25.900000+00:00` to `2025-06-30T23:59:55.563000+00:00`
- Complete days / comparable M5 bars: `42` / `8918`
- Selected quote basis: `UNKNOWN`
- Selected spread statistic: `UNKNOWN`
- Quote alternatives: `BID: open=0.639157%, high=0.190626%, low=0.437318%, close=0.515811% | ASK: open=0.033640%, high=0.011213%, low=0.000000%, close=0.044853% | MID: open=0.067280%, high=0.056066%, low=0.022427%, close=0.033640% | LAST: open=0.000000%, high=0.000000%, low=0.000000%, close=0.000000%`
- Spread alternatives: `BAR_OPEN_SPREAD: exact=0.000000%, within1=0.224266% | BAR_CLOSE_SPREAD: exact=0.000000%, within1=0.358825% | BAR_MINIMUM_SPREAD: exact=0.022427%, within1=0.302758% | BAR_MAXIMUM_SPREAD: exact=0.000000%, within1=1.883830% | BAR_MEAN_SPREAD: exact=0.000000%, within1=0.740076% | BAR_MEDIAN_SPREAD: exact=0.000000%, within1=0.313972%`
- M15/H1 consistency: `True` / `True`
- Failed gates: `provenance_completeness | m5_open_match | m5_high_match | m5_low_match | m5_close_match | alternative_basis_separation | spread_match | spread_unit_conversion | timestamp_alignment`

## USDJPY

- Classification: `PROVENANCE_CHAIN_INCOMPLETE`
- Provenance: `PROVENANCE_CHAIN_INCOMPLETE`
- Tick overlap: `2025-03-11T12:54:26.774000+00:00` to `2025-06-30T23:59:54.050000+00:00`
- Complete days / comparable M5 bars: `42` / `8916`
- Selected quote basis: `UNKNOWN`
- Selected spread statistic: `UNKNOWN`
- Quote alternatives: `BID: open=0.269179%, high=0.213100%, low=0.257963%, close=0.381337% | ASK: open=0.022432%, high=0.011216%, low=0.011216%, close=0.011216% | MID: open=0.000000%, high=0.011216%, low=0.033647%, close=0.022432% | LAST: open=0.000000%, high=0.000000%, low=0.000000%, close=0.000000%`
- Spread alternatives: `BAR_OPEN_SPREAD: exact=0.000000%, within1=0.482279% | BAR_CLOSE_SPREAD: exact=0.000000%, within1=0.459847% | BAR_MINIMUM_SPREAD: exact=0.000000%, within1=0.471063% | BAR_MAXIMUM_SPREAD: exact=0.000000%, within1=1.031853% | BAR_MEAN_SPREAD: exact=0.000000%, within1=0.695379% | BAR_MEDIAN_SPREAD: exact=0.000000%, within1=0.459847%`
- M15/H1 consistency: `True` / `True`
- Failed gates: `provenance_completeness | m5_open_match | m5_high_match | m5_low_match | m5_close_match | alternative_basis_separation | spread_match | spread_unit_conversion | timestamp_alignment`

No instrument contract resolved because immutable provenance is incomplete. XAUUSD also has no tick/bar overlap, and the available EURUSD/USDJPY overlap does not meet the frozen OHLC or spread reconciliation thresholds. The provisional strategy was not rerun.
