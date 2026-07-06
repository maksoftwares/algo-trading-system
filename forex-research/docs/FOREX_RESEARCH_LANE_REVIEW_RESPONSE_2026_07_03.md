# Forex Research Lane Review Response - 2026-07-03

Status: REVIEW_ACCEPTED_RESEARCH_ONLY

Boundary: repo/documentation update only. No MT5 terminal, demo account, running XAU EA, chart, preset, order, position, or broker runtime state was touched.

Review source: `FOREX_RESEARCH_LANE_INDEPENDENT_REVIEW_2026_07_03.md`

## Review Verdict

The independent review confirmed the expected conclusion:

- Methodology is sound.
- Runtime isolation passes: the Forex runner is pure offline Python/pandas research code and does not import broker APIs, invoke terminals, edit charts/profiles/presets, or submit orders.
- Daily context joins, signal timing, dedupe, costs, and recent-proxy labeling are acceptable.
- No Forex EA is approved.
- No Forex demo-forward-test spec should be prepared yet.
- Broker-authoritative EURUSD/USDJPY H1+H4 refresh with measured spread is the correct next evidence requirement.

## Accepted Action Items

1. Refresh scope expanded from EURUSD-only to EURUSD plus USDJPY H1/H4.
2. Minimum refresh window expanded to 2022-01-01 through current, not only 2025-07-01 onward, so sparse H4/session candidates get enough true recent broker evidence.
3. The broker-refresh spec now requires frozen definitions: no threshold/session tuning during refresh evaluation.
4. USDJPY bond-vol v1 is explicitly demoted from "strong clue" to "watchlist clue with within-family selection caveat"; broad v0s and v1 must be tested together.
5. Public recent-proxy stress remains recency triage only, especially for sparse H4/session systems where 7-11 trades cannot decide survivorship.
6. Refresh validation now records raw-file SHA256, normalized-file SHA256, and terminal/account provenance from CSV columns or JSON sidecars. Missing provenance remains visible as a validation warning and must be resolved before calling a file broker-authoritative evidence.

## Current Best Clues

| Candidate | Historical evidence | Recent/proxy caveat | Status |
| --- | --- | --- | --- |
| `eurusd_h4_real_yield_dollar_pressure_reversal_v0` | 147 trades, PF 1.3882, +23.47R | 2 recent proxy trades, PF 0.7486 | REJECTED_LEAD_PENDING_BROKER_REFRESH |
| `eurusd_h4_rates_dollar_yield_pressure_short_session_v1` | 295 trades, PF 1.2258, +29.97R | 9 recent proxy trades | WATCHLIST_CLUE_ONLY |
| `usdjpy_h4_bond_vol_asia_session_carry_relief_v1` | 125 trades, PF 2.0645, +48.23R, all broker splits positive | 7 recent proxy trades, PF 0.3170; v1 selection caveat | WATCHLIST_CLUE_ONLY_DEMOTED_EXPECTATION |

## Next Required Evidence

Use `forex-research/docs/FOREX_BROKER_DATA_REFRESH_SPEC_2026_07_03.md`.

Priority 1:

- Capital.com EURUSD H1/H4 from 2022-01-01 through current with measured/exported spread.
- Capital.com USDJPY H1/H4 from 2022-01-01 through current with measured/exported spread.
- Terminal/account provenance and file identity hashes recorded by `broker-refresh-validate`.

Priority 2:

- Independent EURUSD and USDJPY H1/H4 source over the same window, if available.
- GBPUSD only after EURUSD/USDJPY refresh, unless clean data is already available.

## Decision

No demo-forward-test spec is prepared. A refreshed-data pass would move a candidate to WATCHLIST_ONLY at most. Demo-forward drafting still requires a separate owner-approved step with unique magic/comment and no attachment until explicitly approved.
