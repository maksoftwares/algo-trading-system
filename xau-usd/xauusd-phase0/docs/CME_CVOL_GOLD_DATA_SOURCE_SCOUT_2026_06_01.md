# CME Gold CVOL Data Source Scout - 2026-06-01

## Goal

Find a higher-quality options-skew data class for the next independent H4 EA search. The target lane is `h4_cme_cvol_skew_reversal_v0`, using official CME Gold CVOL / UpVar / DnVar / Skew / ATM / Convexity data rather than another XAUUSD OHLC-only pattern or public proxy.

## Sources Checked

| Source | Finding | Current repo action |
| --- | --- | --- |
| CME Metals Data | CME lists metals options data and describes QuikStrike volatility curves plus CVOL indices for Gold, Silver, and Copper. | Treat as credible primary data class, not yet acquired. |
| CME CVOL product page | CME states CVOL is derived from actively traded options on futures and includes auxiliary indicators such as DnVar, UpVar, Skew, Convexity, and ATM. | Created a local schema matching the indicators needed for an H4 skew candidate. |
| CME CVOL End-of-Day API documentation | Historical CVOL is available by API, but production access requires OAuth/API entitlement. | Marked real matrix as blocked until licensed/entitled data is supplied. |
| CME CVOL client wiki | Gold CVOL code is `GCVL`; the methodology also lists Gold associated indicators `GCUP`, `GCDN`, `GCSK`, `GCAM`, and `GCCV`. Up to nine years of history are available to license through CME DataMine. | Added `data/reference/options/cme_cvol_gold_daily.csv` as the required local handoff file. |
| Cboe Option Sentiment specification | Cboe has equity/ETF option-sentiment fields such as IV30 and normalized 25-delta skew, but this is equity/ETF-oriented and not primary COMEX Gold options. | Defer for GLD ETF-options sentiment unless CME Gold CVOL cannot be acquired. |

## Required Local File

```text
xau-usd/xauusd-phase0/data/reference/options/cme_cvol_gold_daily.csv
```

Required columns:

```text
timestamp_utc
gold_cvol
gold_upvar
gold_downvar
gold_skew
gold_atm
gold_convexity
```

Preferred source fields:

```text
GCVL -> gold_cvol
GCUP -> gold_upvar
GCDN -> gold_downvar
GCSK -> gold_skew
GCAM -> gold_atm
GCCV -> gold_convexity
```

## Current Decision

```text
h4_cme_cvol_skew_reversal_v0: REGISTERED_RESEARCH_CANDIDATE_DATA_BLOCKED
```

The candidate is now implemented for synthetic smoke and has a strict data contract. A real 9-cell matrix must not be run until licensed CME Gold CVOL history covers the full Phase 0 matrix window.

## Next Action

Acquire or export licensed CME Gold CVOL EOD history covering the matrix window, place it at the required path, then run:

```powershell
.\.venv\Scripts\phase0.exe run-research-matrix --expert h4_cme_cvol_skew_reversal_v0 --hypothesis-file docs/hypothesis_h4_cme_cvol_skew_reversal_v0.md
```
