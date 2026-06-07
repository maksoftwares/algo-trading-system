# CME CVOL Blocker Revalidation

Generated: 2026-06-07

## Verdict

`h4_cme_cvol_skew_reversal_v0` remains `BLOCKED_DATA_SOURCE`.

The official CME CVOL End-of-Day API documentation confirms that historical CVOL data is available through the production API, but access requires OAuth authentication and entitled CME Market Data API credentials. The local workspace has no CME/CVOL credential environment variables set and no required local file at `data/reference/options/cme_cvol_gold_daily.csv`.

## Local Verification

- Required local file: missing.
- Required local columns if supplied: `timestamp_utc`, `gold_cvol`, `gold_upvar`, `gold_downvar`, `gold_skew`, `gold_atm`, `gold_convexity`.
- Credential environment check: no `CME`, `CVOL`, `DATAMINE`, `QUANDL`, or `NASDAQ` credential variables were present.
- Direct unauthenticated API check against CME production history endpoint returned `401 Unauthorized`.
- Controlled matrix attempt failed at configuration load with the expected strict data-contract error.

## Decision

Do not run a proxy or partial matrix for `h4_cme_cvol_skew_reversal_v0`. The lane should only resume after licensed CME Gold CVOL/skew history is supplied at the required path.

## Evidence

- Local data contract: `src/phase0/cme_cvol_gold_data.py`
- Strategy: `src/phase0/strategies/h4_cme_cvol_skew_reversal_v0.py`
- Scout: `docs/CME_CVOL_GOLD_DATA_SOURCE_SCOUT_2026_06_01.md`
- CME CVOL API documentation checked 2026-06-07: production history API requires OAuth entitlement.
