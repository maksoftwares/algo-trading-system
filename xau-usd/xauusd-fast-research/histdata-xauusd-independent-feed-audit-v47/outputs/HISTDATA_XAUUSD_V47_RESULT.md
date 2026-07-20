# HistData XAUUSD Independent-Feed Audit V47

Decision: **REJECT_SOURCE_FOR_CROSSVENUE_RESEARCH**

This is a source-quality decision only. It is not evidence of trading edge and has no execution authority.

## Source Quality

- Rows: `3,062,220`
- UTC span: `2024-01-01T23:00:00.312000+00:00` to `2024-02-01T04:59:56.887000+00:00`
- Nonpositive/crossed quotes: `0/0`
- Median / p99 spread: `$0.3300` / `$0.4370`

## Dukascopy Comparison

- Matched M5 bars: `6,066`
- Active-bar coverage: `99.21%`
- Contemporaneous return correlation: `1.000000`
- Median absolute midpoint basis: `$0.0000`
- Basis standard deviation: `$0.0000`
- Exact midpoint-close fraction: `100.00%`

## Frozen Gates

- `minimum_rows`: **PASS**
- `minimum_calendar_days_spanned`: **PASS**
- `timestamps_monotonic`: **PASS**
- `maximum_invalid_quote_rows`: **PASS**
- `positive_median_spread`: **PASS**
- `maximum_spread_p99_dollars`: **PASS**
- `minimum_active_bar_coverage_fraction`: **PASS**
- `minimum_matched_bars`: **PASS**
- `minimum_contemporaneous_return_correlation`: **PASS**
- `maximum_median_absolute_basis_dollars`: **PASS**
- `maximum_exact_mid_close_fraction`: **FAIL**
- `minimum_basis_standard_deviation_dollars`: **FAIL**

## Next Decision

Discard this source route; do not mine strategies from it.
