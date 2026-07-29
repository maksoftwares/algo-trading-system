# EURUSD Neutral prospective SWFX sentiment validation

## Purpose

This contract independently validates every prospective SWFX source-census
artifact from raw JSONP bytes. The capture implementation cannot certify its
own normalized values or census gates.

The validator is source-only. It cannot generate a direction, threshold,
signal, trade, or broker action.

## Frozen replay rules

For every immutable capture manifest available by the validation timestamp,
the validator must:

1. verify the content-addressed manifest filename and SHA-256;
2. verify the scheduled clock is a frozen UTC-weekday `HH:02` or `HH:32`
   slot no earlier than `2026-07-29T06:30:00Z`;
3. reject a successful request that began before its slot or more than 300
   seconds late;
4. verify the raw response path, byte count, and SHA-256;
5. independently parse the JSONP array without importing the capture parser;
6. require exactly one case-sensitive `EUR/USD` row;
7. independently coerce and test all eight required finite fields;
8. require every long/short pair to sum to zero within `0.0001`;
9. verify the normalized artifact hash and reconstruct every normalized value
   from raw bytes;
10. verify all no-price, no-return, no-P&L, no-oracle, no-signal, no-trade,
    and no-broker boundaries; and
11. fail closed on missing, duplicate, malformed, or hash-drifted evidence.

Missing scheduled slots count against coverage. Failed captures and missing
manifests count as failures. Evidence after the validation timestamp is
excluded, not used early.

## Frozen census gates

The validator applies the exact gates already frozen in
`frozen_prospective_neutral_swfx_sentiment_source_census_v1.json`. It cannot
admit the source before 27 calendar days and 20 UTC weekdays have elapsed.
All coverage, validity, variation, consecutive-failure, and official-widget
comparison gates must pass.

Passing this validator permits only a later, separately preregistered
prospective strategy design. It is not evidence that any trading rule is
profitable.

## Safety

The validator makes no network request and loads no EURUSD market price,
return, outcome, oracle label, or P&L.
