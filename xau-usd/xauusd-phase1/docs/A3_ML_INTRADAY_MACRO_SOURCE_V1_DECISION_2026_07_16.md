# A3 ML Intraday Macro Source V1 Decision

Date: 2026-07-16

Classification: `INTRADAY_MACRO_SOURCE_VALID`

## Result

The locked Dukascopy intraday source pipeline passed its acquisition, integrity,
coverage, and determinism gates for the common 2019-01-01 through 2026-06-30
window.

| Measure | DOLLARIDXUSD | USTBONDTRUSD |
|---|---:|---:|
| Complete monthly partitions | 90 / 90 | 90 / 90 |
| Raw ticks | 34,217,173 | 31,833,731 |
| Active source days overlapping XAU | 1,934 | 2,323 |
| Locked-window XAU active days | 2,332 | 2,332 |
| Active-day coverage | 82.9331% | 99.6141% |

Additional gates:

- Negative spreads: 0
- Conflicting same-timestamp observations: 0
- Monthly normalized rebuild hashes identical: yes, 720 files per run
- Combined M5 rebuild hashes identical: yes
- Combined M5 rows: 525,099
- Combined M5 SHA-256: `3982a3bb56741a5c5139f0381696d4ec4f50d7b1be7588a0efa2664bbf51ffa4`
- Manifest SHA-256: `d1250292258d64ac3d052d4cb90691d9415bd638dd03a31f0fdc2a50845c10c8`

The initial report incorrectly included pre-2019 XAU days in the coverage
denominator. The implementation now clips both source and reference days to the
contract's locked common window, with a regression test covering this case.

## Interpretation

These Dukascopy CFDs are causal intraday proxies for broad U.S. dollar and U.S.
Treasury-bond price movement. They are not ICE DXY, exchange futures, Treasury
yields, exchange volume, or order flow. The source verdict allows a separately
preregistered gold event census to use these inputs.

## Authorization

This decision authorizes source use for research only. It does not authorize
strategy selection, model training, Python demo predictions, EA consumption, or
broker action.
