# Phase 2 Actual Broker Trade Review - 2026-06-02

Status: EXPERIMENTAL REVIEW ONLY

This note records the first useful read from the Capital.com demo broker trade ledger after the Phase 2 experimental demo executors began placing orders. It is intended for reviewer advice and owner decision support. It does not mark canonical Phase 2 as passed, does not override the measured-cost blocker, and does not authorize live trading.

## Source

| Field | Value |
| --- | --- |
| Broker account | Capital.com demo account `1025742` |
| Dashboard source | `demo-observer-dashboard.html` |
| Broker ledger | `xau-usd/xauusd-phase1/outputs/reports/PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv` |
| Refresh command | `python scripts/generate_demo_observer_dashboard.py --repo-root ..\.. --output ..\..\demo-observer-dashboard.html` |
| Refresh time window | 2026-06-02 demo activity through approximately 16:10 local workspace time |
| Duplicate rule | Prefer the deduplicated view where `is_duplicate != true` |

## Headline Finding

The actual broker sample currently looks less like a pure broker-cost failure and more like a winrate and selection-quality problem.

The accepted-only deduplicated set is positive so far, with profit factor above 1.0 and average win larger than average loss. The combined deduplicated set is negative because the provisional `session_extreme_retest_v0` sample is materially weak.

This is promising enough to keep observing, but the sample is too small and too experimental to reopen canonical Phase 2 by itself.

## Raw vs Deduplicated Summary

| View | Trades | Closed | Open | Winrate | Closed PnL | Open PnL | Total PnL | Avg Win | Avg Loss | Profit Factor |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Raw broker ledger | 53 | 50 | 3 | 34.00% | -67.53 AED | +3.16 AED | -64.37 AED | +32.19 AED | -18.63 AED | 0.890 |
| Deduplicated broker ledger | 31 | 28 | 3 | 32.14% | -43.77 AED | +3.16 AED | -40.61 AED | +33.14 AED | -18.00 AED | 0.872 |
| Accepted only, deduplicated | 21 | 19 | 2 | 42.11% | +38.35 AED | +0.85 AED | +39.20 AED | +31.01 AED | -19.07 AED | 1.183 |
| Provisional only, deduplicated | 10 | 9 | 1 | 11.11% | -82.12 AED | +2.31 AED | -79.81 AED | +50.19 AED | -16.54 AED | 0.379 |

## Deduplicated Candidate Breakdown

| Candidate | Status | Closed | Open | Winrate | Total PnL | Avg Win | Avg Loss | Profit Factor | Current Read |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `symbol_normalized_round_retest_v0` | ACCEPTED | 13 | 1 | 46.15% | +65.05 AED | +36.53 AED | -22.01 AED | 1.423 | Best actual-broker sample so far. Keep observing. |
| `breakout_retest` | ACCEPTED | 6 | 1 | 33.33% | -25.85 AED | +14.46 AED | -13.93 AED | 0.519 | Weak early sample, but very small count. Do not conclude yet. |
| `session_extreme_retest_v0` | PROVISIONAL | 9 | 1 | 11.11% | -79.81 AED | +50.19 AED | -16.54 AED | 0.379 | Main drag. Treat as a pause/review candidate. |

## Deduplicated Symbol Breakdown

| Symbol | Trades | Closed | Open | Winrate | Total PnL | Avg Win | Avg Loss | Profit Factor | Current Read |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| EURUSD | 4 | 2 | 2 | 50.00% | +4.15 AED | +5.51 AED | -3.60 AED | 1.531 | Positive but too few trades. |
| USDJPY | 1 | 0 | 1 | n/a | +0.92 AED | n/a | n/a | n/a | Open-trade only; no conclusion. |
| XAUUSD | 26 | 26 | 0 | 30.77% | -45.68 AED | +36.60 AED | -18.80 AED | 0.865 | Weak overall because provisional losses dominate. |

## Interpretation

1. The live demo data does not currently prove that raw broker cost alone is the practical failure mode.
2. The accepted deduplicated set is positive, which suggests the accepted group may be able to survive under current demo execution if selection quality remains controlled.
3. The weak point is winrate, especially from `session_extreme_retest_v0`.
4. `session_extreme_retest_v0` should not be promoted into canonical Phase 2 planning. It should remain quarantined and is a candidate for pause, deeper review, or removal from the demo executor set.
5. `symbol_normalized_round_retest_v0` deserves continued observation, but it remains same-family and cannot be counted as true diversification.

## Caveats

| Caveat | Why it matters |
| --- | --- |
| Small sample | Only 28 deduplicated closed trades exist in this review. |
| Experimental order model | Demo execution uses the experimental executor lane, not the canonical Phase 2 paper-mode implementation. |
| Same-family duplication | Some raw trades are duplicated across related EAs; deduplicated numbers are the cleaner decision view. |
| No canonical reopening | Experimental PnL is not accepted as measured-cost revalidation evidence under `PHASE2_RESOLUTION_PLAN.md`. |

## Recommended Next Action

Ask reviewers whether to pause `session_extreme_retest_v0` in the experimental demo executor lane while continuing observation on the accepted set.

Recommended temporary stance:

```text
ACCEPTED_SET_ACTUAL_BROKER_READ = PROMISING_BUT_SMALL_SAMPLE
SESSION_EXTREME_RETEST_V0_STATUS = PROVISIONAL_PAUSE_CANDIDATE
CANONICAL_PHASE2_STATUS = STILL_BLOCKED_BY_MEASURED_COST
```

