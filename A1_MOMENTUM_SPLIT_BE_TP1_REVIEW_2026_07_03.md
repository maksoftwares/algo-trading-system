# INDEPENDENT REVIEW — SPLIT-ENTRY WITH BE-ON-TP1 FIX (RECENT-3M EXACT MT5)
Date: 2026-07-03 | Reviewer: Independent (Claude) | Offline only.

## VERDICT: APPROVE_FOR_SMALL_DEMO (experimental lane) — with the 4-year fixed rerun required in parallel and the standing pre-attach conditions.

## 1. Mechanics (Q1) — PASS
`OnTradeTransaction` implementation is correct: fires on `DEAL_ADD`, filters magic/symbol, requires
`DEAL_ENTRY_OUT` + `DEAL_REASON_TP`, resolves the TP1 position's entry deal, matches the paired
`_RUN` ticket, moves SL to BE on the fill event itself — event-driven, not bar-delayed. The
pre-existing threshold-BE (unrealized ≥ 0.7R) remains as backup; log counts (46 ALREADY_BE vs 7
ON_TP1_MODIFY_OK) show the two mechanisms overlap correctly rather than conflict. Guard chain keeps
everything off by default and shadow-only. NO_MATCH logging exists for the orphan-runner edge case.
Clean work.

## 2. Did it kill the giveback bucket? (Q2) — YES in the tested window
The failure class I flagged ("TP1 wins, runner gives back more") is now `tp1_win_runner_giveback_
net_positive`: 22 signals, +235.00 — every TP1-win signal in the window ended net-positive. Signal
WR moved from 45.3% (unfixed, 4-year) to **65.62%** (fixed, recent 3M). Verified arithmetic: weekly
ledger sums to +345.78 exactly; bucket counts (20 both-win +706.50, 22 tp1-net-positive +235.00,
21 both-loss −595.72, 1 flat) reconcile to 64 signals and the net.
Honest counterweight: the fix has a cost side that this window cannot price — runners that dip to BE
and would have recovered to 2R now exit flat. In trending regimes (2025-style) that cost is larger.
Only the full-window rerun prices it.

## 3. Do the recent results support a small demo test? (Q3) — Yes, at experimental-lane standard
n=64 signals, 13 weeks: WR 65.6% (95% CI ≈ 53–77%), PF 1.58, net +345.78, W/L per signal 0.79.
This clears "test-worthy," not more. Two flags for the gates: best day (+167.74, 2026-04-14) is
**48.5% of net** — one day carries half the result at this sample size; and May was a negative month
(−57) between positive April (+192) and June (+210). 8/13 weeks positive, worst week −88.70.

## 4. Distribution health (Q4) & frequency (Q5)
Healthy for n=64 with the concentration caveat above. Frequency: 64 signals / 63 market days ≈
1.0/day, active on 44% of days — identical to every other lane in the current regime. It meets
"frequent when the market cooperates," not "multiple trades every day"; that is the market, not the
strategy, and no honest repair changes it.

## 5. Recency weighting (Q6) — as agreed: gate, not trophy
Applied exactly per the standing framework: the LONG-history gate is satisfied by the structure (the
unfixed split book was +6.7k/PF 1.44 over four years — the fix only alters post-TP1 dynamics), and
the RECENT gate is now satisfied by this exact run in the current regime. That combination is why
this approval is possible despite n=64. What recency must never do: pick this lane OVER others
because its last-3-months look best — it earns its lane on structure + recent health together.

## 6. Is the 4-year timeout a blocker? (Q7) — No, but it is a DEBT with a deadline
The timeout is an engineering artifact (transaction-logging overhead on the v6/max2 component;
900s cap), not a data problem. Demo attach may proceed without it because the direction of the fix
is structurally predictable and recent-exact evidence is in hand. But the completed 4-year fixed
rerun is REQUIRED within the first 4 weeks of the forward window (raise timeout to 3600s and/or trim
per-transaction logging), because: (a) pass/kill gates need calibrated long-run DD and WR baselines
for the fixed structure; (b) the BE-cost in trending regimes must be priced. If the rerun shows the
fix degrades the 4-year book materially (>15% net), the lane goes to immediate review.

## 7. WR above 50%? (Q8) — Already achieved; do not touch
Signal-level WR is 65.6% in the current regime and structurally ~60%+ expected on the full window
(the fix converts the former 18% giveback bucket into wins). The correct next move on this candidate
is NOTHING — freeze, attach, measure. Any further WR-chasing on burned data subtracts credibility.

## 8. Forward spec conditions (pre-attach, blocking)
- Kill-switch filename separation for this lane (STILL open project-wide); +75-USD-vs-AED package
  guard currency check; dedicated magic (single magic, `_TP1`/`_RUN` comments as implemented —
  verify comment survives broker deal records for attribution); pinned tie-break priority
  (v6_max2 → weak_hours → v13 — as declared, freeze it); SHA256-locked spec; pinned start timestamp;
  owner signs the 2×0.01 minimum exposure explicitly.
- Sample: ≥150 signals or 16 weeks, whichever later (~4–7 months at current cadence).
- PASS: signal-WR ≥ 55%; PF ≥ 1.25; net > 0 after $0.20/signal cost haircut; no day > 30% of net;
  top-2%-signal removal positive; W/L ≥ 0.7.
- KILL: rolling-40-signal PF < 0.90; net negative after 80 signals; signal-WR < 45% after 80
  signals; lane DD > 2× recent-3M max DD until the 4-year rerun recalibrates it; any safety/account/
  magic violation. No streak kills (a 3-signal losing day ≈ −$60–90 is in-distribution).
- Owner briefing note: 33% of signals lose both tickets (−2R). Several −$60+ days per month are
  NORMAL for this lane even while it passes.

## 9. Next actions
1. Codex: complete the 4-year fixed rerun (timeout 3600s / reduced logging) — due within 4 weeks of attach.
2. Codex: pre-attach condition set (§8 bullet 1) + frozen spec doc with SHA256 for owner sign-off.
3. Owner: explicit acceptance of 2-ticket exposure; then manual attach per process.
4. Reviewer (me): recheck first-week fills against the spec (magic, comments, BE events in deals).
