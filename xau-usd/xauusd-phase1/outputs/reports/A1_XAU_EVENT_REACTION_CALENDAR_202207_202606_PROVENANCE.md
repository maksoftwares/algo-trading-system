# A1 XAU Event-Reaction Calendar Provenance

Date: 2026-07-07

Status: `EVENT_CALENDAR_OFFICIAL_PROVENANCE_FROZEN_NO_MT5_RUN`

## Boundary

This freezes the current calendar provenance state for the event-reaction branch. It does not run MT5, does not approve a strategy, and does not make any trading result acceptance-ready.

FOMC events are official-provenance because the Federal Reserve calendar was fetched and hashed locally. NFP and CPI events are official-provenance because the BLS yearly release-calendar pages were fetched, hashed, and parsed from their release tables.

## Counts

| Event type | Provenance | Count |
|---|---|---:|
| `CPI` | `BLS_OFFICIAL_FETCHED` | 47 |
| `FOMC` | `FED_OFFICIAL_FETCHED` | 32 |
| `NFP` | `BLS_OFFICIAL_FETCHED` | 47 |

## Files

- Calendar CSV: `xau-usd/xauusd-phase1/data/external/event_reaction_calendar/A1_XAU_EVENT_REACTION_CALENDAR_202207_202606.csv`
- Manifest JSON: `xau-usd/xauusd-phase1/data/external/event_reaction_calendar/A1_XAU_EVENT_REACTION_CALENDAR_202207_202606.manifest.json`
- Report: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_EVENT_REACTION_CALENDAR_202207_202606_PROVENANCE.md`
- Calendar CSV SHA256: `39ebfd218ff3910643963f87b64de4431a35ad390a1862e82fe516203b4b69a1`

## Source Fetches

| Source | Status | Detail |
|---|---|---|
| `https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm` | `FETCH_OK` | `b225a57d1ddc1e5c9fec4f0579dfd4a1d2b67fd60e21c18a8fad502a49634b85` |
| `https://www.bls.gov/schedule/2022/home.htm` | `FETCH_OK` | `12ed4a8940a6a6dee04e90eb73ae1d6e8d9d42425e090620d98a05dfb47dae3d` |
| `https://www.bls.gov/schedule/2023/home.htm` | `FETCH_OK` | `6d1760861d47cc0f2e73e611985f47281ca9db2c5033d0da72eb7b6fcb0a1920` |
| `https://www.bls.gov/schedule/2024/home.htm` | `FETCH_OK` | `e09a2837cebcff91f621f40758a31f61430888a5504be2cd5361d05f06e10054` |
| `https://www.bls.gov/schedule/2025/home.htm` | `FETCH_OK` | `1d303c6d63df3346dcc50495589b509217cc00e1fc814e11c55386963b18ac31` |
| `https://www.bls.gov/schedule/news_release/current_year.asp` | `FETCH_OK` | `959fbf278b15a90ab2e1bf9eeed8b29b669b834390d615140cdc1a91b1d77d34` |

## Acceptance Blocker

Calendar provenance is frozen for the first exact-MT5 event-reaction implementation. This still does not approve a strategy or demo spec; it only removes the event-calendar provenance blocker.
