# Forex Broker Data Refresh Spec - 2026-07-03

Status: RESEARCH_ONLY_DATA_REQUEST

Boundary: this spec does not authorize MT5 terminal access, chart edits, preset edits, EA deployment, order placement, or any broker/runtime action. It defines the offline CSV evidence needed before the Forex lane can continue responsibly.

## Why This Exists

The Forex lane found no demo-forward survivor. The independent review confirmed the methodology and the no-approval verdict, but identified three frozen watchlist clues that justify one broker-authoritative refresh:

1. `eurusd_h4_real_yield_dollar_pressure_reversal_v0`
   - Historical broker replay: 147 trades, PF 1.3882, +23.47R, 9.79R max DD.
   - Broker split: Capital.com +9.88R / PF 1.4215; Dukascopy +6.43R / PF 1.1989; Pepperstone +7.17R / PF 2.5164, but only 15 trades.
   - Recent public Yahoo proxy stress: only 2 trades, PF 0.7486.
   - Final gate: REJECT_MACRO_RECENT_LOW_SAMPLE.

2. `eurusd_h4_rates_dollar_yield_pressure_short_session_v1`
   - Historical broker replay: 295 trades, PF 1.2258, +29.97R.
   - All historical broker splits were positive.
   - Recent public Yahoo proxy stress: only 9 trades, PF 2.5920, +4.89R.
   - Final status: historical watchlist-only clue, not a survivor.

3. `usdjpy_h4_bond_vol_asia_session_carry_relief_v1`
   - Historical broker replay: 125 trades, PF 2.0645, +48.23R.
   - All historical broker splits were positive.
   - Recent public MOVE/FX proxy stress: only 7 trades, PF 0.3170, -2.98R.
   - Review note: v1 came after within-family iteration, so its historical headline may be inflated. Retest v0 and v1 together with frozen definitions; do not tune thresholds during refresh evaluation.

None of these leads is approved. They need broker-authoritative 2022-01-01 through current data, with measured or exported spread, before any forward-test package can even be drafted. The wider 2022-current window is intentional: it gives enough true recent broker data for sparse H4/session candidates and checks whether the historical clues survive the post-2022 regime.

Reviewer addition accepted: every refresh file must be auditable as broker-authoritative. The validator must record raw-file SHA256, normalized-file SHA256, and terminal/account provenance in the validation report. Missing provenance is a validation warning and must be resolved before relying on the file as broker-authoritative evidence.

## Required Data

Priority 1:

| Broker | Symbol | Timeframes | Minimum window | Required fields | Purpose |
| --- | --- | --- | --- | --- | --- |
| Capital.com demo/export | EURUSD | H1 and H4, or H1 only if H4 is derived | 2022-01-01 through 2026-07-03 or later/current | UTC bar time, OHLC, spread median or bar spread, p95 spread if available | Retest the EURUSD macro-pressure reversal and rates/dollar short-session clues on broker-authoritative data. |
| Capital.com demo/export | USDJPY | H1 and H4, or H1 only if H4 is derived | 2022-01-01 through 2026-07-03 or later/current | UTC bar time, OHLC, spread median or bar spread, p95 spread if available | Retest the USDJPY bond-vol v0/v1 family and confirm the dead carry/session family on broker-authoritative data. |

Priority 2:

| Broker | Symbol | Timeframes | Minimum window | Required fields | Purpose |
| --- | --- | --- | --- | --- | --- |
| Any independent broker/source already acceptable to Phase 0 | EURUSD | H1 and H4, or H1 only if H4 is derived | 2022-01-01 through 2026-07-03 or later/current | UTC bar time, OHLC, spread if available | Check whether the EURUSD macro/rates clues are venue-specific. |
| Any independent broker/source already acceptable to Phase 0 | USDJPY | H1 and H4, or H1 only if H4 is derived | 2022-01-01 through 2026-07-03 or later/current | UTC bar time, OHLC, spread if available | Check whether the USDJPY bond-vol clue is venue-specific. |
| Capital.com demo/export | GBPUSD | H1 and H4, optional M15/M5 | 2024-01-01 through 2026-07-03 or later | UTC bar time, OHLC, spread median or bar spread, p95 spread if available | Add the missing major pair to cost geometry and screen only if costs are sane. |

## CSV Contract

Preferred columns:

```text
timestamp_utc,bar_start_utc,bar_end_utc,broker,symbol,timeframe,open,high,low,close,spread_median_points,spread_p95_points,tick_count,volume_sum
```

Minimum acceptable columns:

```text
timestamp_utc,open,high,low,close,spread_median_points
```

Recommended provenance columns, if the export format can carry file-level metadata:

```text
export_terminal,export_account_login,export_account_server,export_account_type,export_broker_company,exported_at_utc,export_timezone,export_method
```

If the export format should stay bar-only, place a JSON sidecar next to the CSV using one of these names:

```text
<file>.csv.provenance.json
<file>.provenance.json
<file>_provenance.json
```

Sidecar example:

```json
{
  "provenance": {
    "export_terminal": "Capital.com demo terminal export",
    "export_account_login": "1025742",
    "export_account_server": "Capital.ComMena-Demo",
    "export_account_type": "demo",
    "export_broker_company": "Capital.com",
    "exported_at_utc": "2026-07-03T00:00:00Z",
    "export_timezone": "UTC",
    "export_method": "read-only history CSV export"
  }
}
```

Rules:

- Timestamps must be UTC or explicitly documented with conversion rules.
- Prices must be raw broker prices, not rounded report screenshots.
- Spread units must be points in the broker point convention. If spread is in price units, the conversion must be documented.
- Terminal/account provenance must be supplied through provenance columns or a sidecar JSON file. If unavailable, disclose why; the validator will warn `PROVENANCE_MISSING`.
- Duplicate bars, missing OHLC rows, and non-monotonic timestamps must be cleaned or disclosed.
- H4 may be derived from H1 by the lane harness; H1 must therefore be complete enough for clean aggregation.
- Public Yahoo proxy data is not a replacement for this broker data.

## Offline Storage Target

Owner-supplied or exported files should be placed under a new research-only import area, not into an MT5 runtime directory:

```text
forex-research/data/broker_refresh/raw/<broker>/<symbol>/<timeframe>/
```

Example:

```text
forex-research/data/broker_refresh/raw/capital_com/EURUSD/H1/EURUSD_capital_com_H1_20250701_20260703.csv
```

Do not overwrite the existing Phase 0 processed bar tree until the import is validated.

## Validation Command

Run the offline validator after placing CSV files in the raw import area:

```powershell
python forex-research\scripts\run_forex_research_lane.py broker-refresh-validate
```

The validator writes:

- `forex-research/outputs/reports/FOREX_BROKER_REFRESH_VALIDATION_2026_07_03.md`
- `forex-research/outputs/reports/FOREX_BROKER_REFRESH_VALIDATION_2026_07_03.json`
- normalized replay-ready CSVs under `forex-research/data/broker_refresh/validated/<broker>/<symbol>/<timeframe>/` only when a file passes timestamp, OHLC, and spread checks.

The validation report records each raw file's SHA256, each normalized output file's SHA256, provenance status, provenance source, terminal, account login, account server, export time, export timezone, and export method. Validator PASS means replay-ready only. It does not approve a Forex EA or authorize a demo-forward-test spec.

## Frozen Retest Command

After validation, run the frozen refresh replay:

```powershell
python forex-research\scripts\run_forex_research_lane.py broker-refresh-retest
```

The retest command:

- Re-runs validation first.
- Loads only normalized files from `forex-research/data/broker_refresh/validated/<broker>/<symbol>/<timeframe>/`.
- Retests the frozen EURUSD macro, EURUSD rates/dollar, and USDJPY bond-volatility v0/v1 families.
- Uses 2022-01-01 onward refreshed broker bars, measured/exported spread, existing slippage assumptions, and no threshold/session edits.
- Writes `forex-research/outputs/reports/FOREX_BROKER_REFRESH_RETEST_2026_07_03.md` and `forex-research/outputs/reports/FOREX_BROKER_REFRESH_RETEST_STATUS_2026_07_03.json`.

If no validated files are present, the retest report must say `NO_VALIDATED_REFRESH_FILES`; that is an evidence gap, not a candidate failure.

## Promotion Gates After Refresh

The frozen EURUSD macro, frozen EURUSD rates/dollar, and frozen USDJPY bond-vol families may move from REJECTED_LEAD / WATCHLIST_CLUE to WATCHLIST only if all of the following pass on broker-authoritative refreshed data:

- Run the frozen v0/v1 definitions together. No threshold edits, session edits, or post-review tuning are allowed inside this refresh evaluation.
- For USDJPY bond-vol, evaluate the broad v0s and Asia-session v1 together and report the v1 selection caveat explicitly.
- For sparse H4/session candidates, replace public recent-proxy triage with the refreshed broker recent window; do not treat a 7- to 11-trade proxy result as decisive evidence.

| Gate | Threshold |
| --- | --- |
| Recent broker sample | At least 20 recent closed trades, preferably 40+; sparse H4/session candidates need the full 2022-current refresh before interpretation. |
| Recent broker PF | PF >= 1.15 net of spread/slippage. |
| Recent expectancy | Net expectancy > +0.03R. |
| Top-winner removal | Total net R remains positive after removing the largest winner. |
| Drawdown | Max DD <= 12R on the refreshed recent window. |
| Cost geometry | H4 p95 cost_R remains <= 0.05 using refreshed spread data. |
| Direction/session stability | No single direction or single session is the entire edge unless pre-registered. |
| Broker robustness | If a second recent broker/source exists, it must not be materially negative. |

Passing these gates would still mean WATCHLIST_ONLY. A demo-forward-test spec would require a separate owner-approved step with unique magic/comment and no attachment until explicitly approved.

## Current Decision

No Forex EA is approved. No Forex demo-forward-test spec is prepared. The next valid action is data refresh or a genuinely new external signal class.
