# V91 SGE source result

Status: **SOURCE FOUNDATION ACCEPTED; NO XAU OUTCOMES INSPECTED**

The public Shanghai Gold Exchange daily-report archive was collected and
normalized before any V91 strategy outcomes were opened. No paid data and no
Databento data were used.

## Frozen artifacts

- External root: `C:\SgeGoldDemandFoundationV1`
- Normalized data: `normalized\sge_daily_contracts_v1.parquet`
- Manifest: `normalized\sge_daily_contracts_v1.manifest.json`
- Normalized SHA-256: `5a388b154b8836a7b18ba90815377b17aa2ada96949fbadb01cf0ec79062bcb3`
- Raw archive digest: `f414385684b23a0f514b244319f0ee813c34fa710bd1fc64c58c2af8070acb91`
- Manifest content hash: `c77b89a6f34513ae658be227639ee7d6672ca8f11121ce032fe9d154d0287504`
- Raw HTML files: 2,667
- Valid normalized rows: 32,353
- Unique SGE trading dates: 2,423
- Date range: 2016-07-01 through 2026-06-30
- Duplicate `(date, contract)` keys: 0

The external raw and normalized data are intentionally not committed to Git.
The collector, parser tests, source contract, hashes, and audit result are
committed so the source can be reproduced and verified.

## Core coverage

| Contract | Rows/dates | First | Last | Missing close | Missing volume |
|---|---:|---|---|---:|---:|
| `Au99.99` | 2,422 | 2016-07-01 | 2026-06-30 | 7 | 7 |
| `Au(T+D)` | 2,423 | 2016-07-01 | 2026-06-30 | 7 | 7 |
| `mAu(T+D)` | 2,423 | 2016-07-01 | 2026-06-30 | 6 | 7 |
| `Ag(T+D)` | 2,422 | 2016-07-01 | 2026-06-30 | 7 | 7 |

All four contracts have 485 dates in Dev2, 242 in Confirmation, and 242 in
Final. The historical-to-modern endpoint boundary is continuous from
2023-12-29 to 2024-01-02, with all four core contracts on each trading date.

The seven affected source dates are 2021-04-23, 2021-06-07, 2021-12-13,
2021-12-14, 2022-01-04, 2022-01-05, and 2022-09-20. V91 must not impute these
market values. A mechanism that requires a missing field must abstain.

## Audited source exceptions

- Reports `543406`, `543424`, and `10000802` are NYAuTN reference notices,
  not daily contract tables.
- Report `543277` omits contract identities and is unusable.
- Report `542439` misspells its title month as `Apri`; its registered trading
  date is 2017-04-18.
- A run of 2019 titles misspells `February` as `Feburary`; the spelling alias
  changes only the month token.
- Six footer-note rows were rejected by the contract-name grammar.
- Direction typography is normalized to `long_to_short` or `short_to_long`;
  one `Au(T+D)` row on 2022-06-14 has no direction and remains missing.

## Causal-use rule

An SGE report for trading date `D` is unavailable to V91 until `D + 1 day`
at `00:00 UTC`. No same-date XAU entry may consume it. This is deliberately
more conservative than the exchange session close and avoids publication-time
ambiguity.

This acceptance covers source integrity only. It is not evidence that any SGE
mechanism predicts XAUUSD or qualifies as a specialist.
