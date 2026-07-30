# EURUSD Compression failed-auction census

Date: 2026-07-30

Status: **CENSUS_CAPACITY_REJECTED**

Demo-order authorization: **false**

## Decision

The exact symmetric failed-auction pattern is too rare to support a dedicated
Cross-Pair Compression specialist. The protocol stopped before opening any
development or locked-validation P&L.

The pattern was frozen before its count was known. It required three exact M5
bars before 20:00 UTC, a failed excursion of at least 3 pips, no more than a
20-pip observation range, a return through the observation open, and a
rejection wick owning at least 55% of the range. These thresholds were
inherited verbatim from an earlier independent preregistration.

## Outcome-blind census

| Metric | Result | Frozen minimum |
|---|---:|---:|
| Total candidates | 37 | 40 |
| Development candidates | 24 | 20 |
| Locked-validation candidates | 13 | 15 |
| Long candidates | 16 | 10 |
| Short candidates | 21 | 10 |

The total and locked-validation capacity gates failed. The thresholds will not
be weakened after seeing the count. The resulting validation trade ledger is
empty, and the protected M15 system remains unchanged.

## Interpretation

Selective rejection is structurally more sensible than forcing a direction,
but this exact 15-minute pattern contributes only about 3.7 candidates per
year. It cannot materially close a 0.65-trade-per-weekday portfolio gap even
if later P&L happened to look attractive. A high-capacity specialist must come
from a different opportunity stream, such as the existing intraday RSI
opportunity ledger segmented and selected chronologically by regime.

## Reproducibility

Run:

```powershell
uv run --offline --with pandas --with numpy --with pyarrow python run_compression_failed_auction.py
```

Implementation hashes:

- config:
  `b35a4a1971795f6aa0abe2abdec42c23a2d47bc569ead7da22a78aeac4a9ae6e`
- source:
  `a7881786b9ad85436403227c939b1fa3a61ae2e00f30eacda899b33211fdeb28`

Output hashes:

- `CANDIDATES.csv`:
  `2be9e1f6ef646302a896e87554ea58025ec5da4bc46a65bd77052ff087cc50fb`
- `VALIDATION_TRADES.csv`:
  `10a96a8c9401da2c9aa4d7befeba0d3eb6cd1e2b4527a8eba821ac0dccb69023`
- `MONTHLY.csv`:
  `c7d4430cb8d9f14b097db57be88df1ed970d261eff97831a2156492d97021d2c`
- `RESULT.json`:
  `af8ba0f1f62554e30753752dec8382425bc2947bdda17500dab20906f5b91404`
- `RESULT.md`:
  `b7581d77d0cadb95b16d66035ac703167455c1a7956d4e31f9b2eeee7fc2300a`
