# CODEX WORK ORDER — Observer upgrades for trustworthy insight (2026-06-16)

Owner: Ali (mohdalikhans97.com@gmail.com). Demo only.

## Scope and hard boundary
Two **analysis-side** upgrades only. We change how observer outputs are **scored and summarized** —
we do **NOT** touch any trading EA, preset, arming flag, magic, session gate, or the running
observers' behavior. No live trade decision changes. Read the existing logs; produce better
analysis from them. This is consistent with the "observe-only this week" rule.

## Why
Two gaps make our current insight weaker than it should be:
1. Outcomes are scored by **synthetic replay**, which contradicts reality (replay said Night was
   the worst gold session; the real broker trades said Night was the best). We must score on
   **real broker fills.**
2. We have no clean **MFE/MAE** (how far each trade ran for/against before it closed) — the single
   most useful missing diagnostic for whether stops/targets are placed right.

## Task 1 — Score outcomes on REAL broker fills, not replay
In the pipeline that produces `OBSERVER_OUTCOME_RESOLUTION_ROWS.csv` (and the scoreboards built
from it):
- When a signal has a matched real broker trade (`matched_position_ticket` present), the
  **authoritative outcome = the actual broker result** (`actual_profit_aed` / actual exit), not the
  replay. Replay becomes a **fallback only** for signals with no broker match.
- Add an `evidence_tier` column: `BROKER` (authoritative) vs `REPLAY` (fallback/low-evidence).
- **Regenerate every scoreboard** (by session, cost, direction, regime, family, lane) computed on
  `BROKER`-tier rows only. Keep a separate replay view for reference, clearly labelled.
- Report counts: how many signals are broker-resolved vs replay-only, per symbol/family — so we
  know the trustworthy sample size.

## Task 2 — Add MFE/MAE per trade (from existing path logs)
New **offline** analysis script (reads existing position-path snapshot logs; no observer-EA change):
For each closed gold trade, per account, compute over the position's lifetime:
- `mfe_points`, `mfe_r` — furthest price moved **in favor** (toward target); R = points ÷ stop distance.
- `mae_points`, `mae_r` — furthest price moved **against** (toward stop).
- `went_green_then_lost` — flag for a losing trade whose `mfe_r` exceeded a threshold (e.g. 0.5R)
  before it closed at a loss (i.e. a winner we gave back).
- Source flag: `PATH_SNAPSHOTS` (preferred) or `M5_BAR_FALLBACK` if path data is missing for a trade.

Output `MFE_MAE_<DATE>.csv` plus a summary in the report:
- avg `mae_r` on **winners** (are stops wider than they need to be?),
- avg `mfe_r` on **losers** (did losers go green first?),
- % of losers that were green before stopping (`went_green_then_lost`).

## Reporting
`OBSERVER_UPGRADES_REPORT_2026_06_16.md`: broker-vs-replay resolved counts, the regenerated
broker-fill scoreboards (session/cost/direction at minimum), the MFE/MAE summary with the three
diagnostics above, and raw command output. State explicitly that no trading EA/preset/arming was
changed (paste `git status` showing only analysis scripts/reports changed).

## Acceptance
- Scoreboards now computed on real broker fills, with `evidence_tier` visible and replay demoted to fallback.
- MFE/MAE columns produced for the day's gold trades with the summary diagnostics.
- Proof nothing live/trading changed.
