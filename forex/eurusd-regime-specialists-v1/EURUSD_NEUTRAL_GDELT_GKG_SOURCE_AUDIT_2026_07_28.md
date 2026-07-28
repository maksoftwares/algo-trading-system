# EURUSD Neutral GDELT GKG source audit

Date: `2026-07-28`

Status: `FREE_TIMESTAMPED_SOURCE_ACCEPTED_FOR_PROSPECTIVE_CENSUS_ONLY`

The [GDELT Project](https://www.gdeltproject.org/) is a free, open global
news metadata source. Its official GDELT 2.0 documentation states that the
Events and Global Knowledge Graph streams update every 15 minutes and include
article timestamps, themes, organizations, and document-level tone.

The no-login `lastupdate.txt` feed listed the 18:30 UTC GKG batch with:

- 7,563,257 bytes;
- provider MD5 `51b4d4a4dde88aeab93506f5468003ec`; and
- URL
  `http://data.gdeltproject.org/gdeltv2/20260728183000.gkg.csv.zip`.

The batch was preserved only on `D:`. Its provider MD5 matches and its
independent SHA-256 is
`5b1d45505628a4690f6390d5c84de1c5eb84abb11a95f9576cb2b135057115fe`.
It contains one 23,359,158-byte member, 1,800 rows, exactly 27 fields per
row, and a single `20260728183000` batch timestamp.

## Semantic audit

The sample contains potentially useful themes:

- `EPU_POLICY_FEDERAL_RESERVE`: 15 documents;
- `ECON_CENTRALBANK`: 24;
- `ECON_WORLDCURRENCIES_EURO`: 1; and
- `ECON_WORLDCURRENCIES_US_DOLLAR`: 1.

A stricter filter requiring a monetary-policy or central-bank theme plus an
explicit central-bank organization found 12 Federal Reserve documents and
zero ECB documents. Several Fed matches concern oil, broad equities, or
political fact checking. Their tone is whole-document sentiment, not a direct
measurement of expected USD appreciation.

This establishes technical novelty and prospective timestamp availability,
but not an economic side rule. Creating a EURUSD trade from one convenient
batch would be narrative fitting.

## Decision

The source is accepted only for a separately frozen, outcome-blind
multi-date coverage census. That census must measure ECB/Fed symmetry,
missing batches, publication lag, duplicate documents, source concentration,
and clock coverage before any EURUSD return or oracle match is loaded.

No GDELT strategy, threshold, or direction mapping is preregistered. No
historical or prospective EURUSD outcome was opened. The current macro
specialist remains unchanged and no broker action is authorized.

Reproduce:

```powershell
uv run --offline python audit_neutral_gdelt_gkg_source.py
```
