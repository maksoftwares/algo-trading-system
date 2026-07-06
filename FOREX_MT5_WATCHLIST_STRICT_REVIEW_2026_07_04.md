# STRICT INDEPENDENT REVIEW — FOREX MT5 LANE & USDJPY LONDON120 LEAD
Date: 2026-07-04 | Reviewer: Independent (Claude) | Offline only. Headline numbers recomputed from raw MT5 trade CSVs — all match to the cent.

## VERDICTS
- **METHODOLOGY SOUND** — real MT5 tester evidence, isolated root, no-tuning discipline held (the blockh7
  rejection and the refused long-only promotion are exactly right), failures reported as prominently as leads.
- **BEST CANDIDATE TO CONTINUE**: USDJPY `london120_break_m15` — with two explicit discounts attached (below).
- **DEMO SPEC BLOCKED** — the NO DEMO / WATCHLIST ONLY conclusion is correct.

## The two discounts that must ride with this candidate
1. **Survivorship**: it is the sole survivor of a ~25–30-cell honest sweep (3–5 symbols × 4 sessions ×
   2 TFs + extra majors). Its 7/7 positive years 2020–2026 is the strongest fact (p≈1/128 by luck per
   cell, ≈20–25% that SOME cell shows it across the sweep) — so: probably real, definitely not proven.
   REQUIRED: add a cell-count ledger to the packet so future readers see the denominator.
2. **Regime decay — the decisive issue under the owner's recency priority.** The edge's best years are
   behind it: 2022 PF 1.49, 2023 PF 1.69, 2024 PF 1.47 — then **2025 PF 1.08 (+$14.85 on 141 trades,
   near-flat) and 2026-partial PF 1.24 (77 trades)**. The aggregate PF 1.39 (2022–26) is carried by a
   golden era that may be ending. By the standing recency-as-gate rule, the recent 12–18 months are a
   MARGINAL pass at best. This, not 2018–2019, is the biggest open question.

## Answers
**Q1 — NO DEMO correct?** Yes. Blockers are real and material; nothing is close enough that delay costs
more than premature attach would.
**Q2 — best path or least-bad survivor?** Both, and that's not a contradiction. It has the only
multi-year raw consistency in the lane plus a plausible structure story (Tokyo→London volatility
handoff, USDJPY-specific). Continue it — with the two discounts above stated in every future packet.
**Q3 — missing evidence for demo-ready:**
  (a) Recent-regime strength: standalone trailing-12-month PF ≥ ~1.15 (currently ~1.08–1.24 thin) —
      accrues monthly with no work; (b) EA code/methodology review of `ForexSessionBreakoutScout.mq5`
      (self-identified); (c) slippage stress table (+0.3/+0.5/+1.0 pip round-trip: at $0.24/trade avg,
      +0.5 pip ≈ −14% of edge, +1 pip ≈ −28% — must be in the packet); (d) survivorship ledger (Q2);
      (e) alternate-history validation (replay the frozen rule on Dukascopy bars — data exists in repo);
      (f) the one pre-declared structural test (Q5).
**Q4 — next step:** deeper robustness on the lead + alternate-history validation. NOT more raw
frequency screens now (diminishing returns, rising survivorship debt), NOT abandonment, NOT tuning.
**Q5 — the one pre-declared improvement: session/range-quality guard.** It addresses the known failure
mode of session breakouts (chop-day noise breaks) and is structurally motivated rather than mined.
Discipline: declare the rule and threshold BEFORE running (e.g., "skip entries when the 06:00–08:00
range < X% of daily ATR(14)", X fixed from first principles, ONE value, no sweep), run once on
2018–2026, accept or reject. Separately, a max-spread-at-entry guard should be added as DEPLOYMENT
HYGIENE (not an edge claim, no backtest privilege). WARN — the following would be data-mining and are
refused in advance: long-only promotion (post-hoc direction cut), hour blocks from the hour table,
RR/session-time adjustments, and calendar/news filters (too many degrees of freedom, event-list
selection risk); volatility-regime guards are second-choice (threshold mining risk) — only if the
range-quality guard is rejected and only with a single pre-declared threshold.
**Q6 — most dangerous hidden risks:** (1) regime-fit masquerading as robustness (2022–24 carry/
intervention-era USDJPY volatility — see discount 2); (2) sweep survivorship without a ledger;
(3) slow-motion tuning: "one constrained pass per family" across many families reassembles a grid —
keep a lane-level tuning registry; (4) execution modeling: M15 signals on M5 chart — confirm every-tick
model and record the tester's tick-model line in each packet; (5) CSV-vs-MT5 PF gaps are disclosed and
small — keep publishing both.
**Q7 — gates:** about right; one refinement — fixed-size rolling-window negativity (50/100-trade) will
be negative in ANY PF≈1.2 system at some point and over-penalizes high-n books; scale the rolling gate
to sample (e.g., no negative window ≥ 25% of sample) and keep the absolute ones for smaller windows.
Do not loosen anything else pre-demo.
**Q8 — portability failure:** confidence penalty, not a blocker. A USDJPY-session-specific edge is
theoretically defensible, but failed EURUSD/GBPUSD portability removes the universality defense, so the
USDJPY-specific evidence bar rises (which is exactly how the lane is treating it).
**Q9 — conditional minimal demo spec** (ONLY if Q3 items pass): magic 933001 (new series), comment
`FX_SB_LDN120_V0`, USDJPY only, fixed 0.01, dedicated kill-switch file, max-spread guard 25 points,
max 3 trades/day, daily loss stop −$5, demo server allowlist, SHA256-locked EA+set, pinned start
timestamp. Honest cadence: ~2.5 trades/week → minimum sample n≥60 or 24 weeks, whichever later.
PASS: PF ≥ 1.15 AND net > 0 after +0.5-pip slippage haircut AND both directions traded AND no day
> 30% of net. KILL: rolling-40 PF < 0.90; net < 0 after 50 trades; DD > $50; any account/symbol/magic
violation. No mid-test changes of any kind.
**Q10 — iterations to demo-ready:** best case 2 (code review + slippage table clean, range-quality
guard accepted or cleanly rejected, trailing-12M strengthens → spec); base case 3–5 (guard indecisive,
alternate-history mixed,需要 two more quarters of recent data); worst case ∞ — 2025-style decay
continues and the lane correctly never promotes. Honest probability this specific candidate ever
reaches demo: ~35–45%. That is a compliment by this project's standards.

## NEXT 3 ACTIONS (priority order)
1. **One review packet**: EA source review of `ForexSessionBreakoutScout.mq5` + tick-model line +
   slippage stress table + sweep cell-count ledger + Dukascopy alternate-history replay of the frozen
   rule. No new variants.
2. **Pre-declared range-quality guard test** — rule and single threshold written and hash-logged BEFORE
   the run; one run over 2018–2026; accept/reject; no second threshold.
3. **Recent-regime watch**: monthly frozen-rule rerun as H2-2026 data accrues; demo spec discussion
   opens only when trailing-12M PF ≥ 1.15 standalone. Meanwhile the XAU forward lanes remain the
   project's active demo tests — this lane must not rush to join them.
