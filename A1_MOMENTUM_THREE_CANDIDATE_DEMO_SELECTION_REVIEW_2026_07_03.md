# INDEPENDENT REVIEW — THREE CANDIDATES, ONE DEMO DECISION
Date: 2026-07-03 | Reviewer: Independent (Claude) | Offline only. All books recomputed from tester CSVs.

## VERDICT: APPROVE_BOTH_PARALLEL — Pure-Causal as PRIMARY lane, Split-Entry as EXPERIMENTAL lane.
Risk-Balanced package: REJECT for this round (not a four-year book — its source run is 2024-07→2026-06
only, so its headline is not comparable; it also carries the worst top-300 stress and Codex's own
REVISE status). Re-enter it only after a full-window rerun.

## 1. Verification
- **Pure-Causal**: verified previously to the cent (3,156 / 66.00% / +2,773.63 / PF 1.42 / 3.03/day);
  guard causality passes; standing caveats: constructed rolling-250 repair, 2026Q2 cadence collapse
  (1.07 trades/day recent), dead-weight v4 component.
- **Split-Entry components**: all three verify exactly (1,412/2,018/2,736 tickets; PF 1.49/1.38/1.49).
- **Split-Entry portfolio**: structure verifies exactly (4,950 tickets / 2,475 signals; dedupe
  fingerprint matches) but my causal first-in-time dedupe yields **net 6,683 / PF 1.44**, vs claimed
  7,452 / 1.49. The +769 difference rides on which component wins a same-bar tie. Not leakage — but
  the tie-break priority MUST be pinned in the runtime spec (fixed component priority), and the
  honest planning number is ~6,700.

## 2. The finding that changes how you read Split-Entry: per-decision WR is 45%, not 52%
The 52.16% headline counts each signal twice (two tickets). Reconstructing per-signal outcomes:
| Signal outcome | Share |
|---|--:|
| Both tickets win (TP1 + runner 2R) | 42.1% |
| TP1 wins, runner loses more than TP1 gained | **18.0%** |
| TP1 wins, net still positive | 3.2% |
| Both tickets lose | 36.7% |
Per decision: **WR 45.3%, avg win $17.22, avg loss $9.26, W/L 1.86** (breakeven at that ratio: 35%).
This is a healthy, tail-monetizing book — but the OWNER'S GOAL "win rate > 50%" is NOT met as
experienced per trading decision. Pure-Causal delivers 66% per decision with W/L 0.73; Split delivers
45% per decision with W/L 1.86. These are the two ends of the same exchange rate — you cannot have
both ends at once, and the forward test is partly about which equity-curve FEEL the owner can live with.

## 3. Answers
**Q1 — best for isolated demo forward test?** Both, in parallel, separate magics. They answer
different questions (feel-first vs money-shape-first) at trivial demo cost. If forced to one: keep
Pure-Causal primary — more robust per my stress recompute (see Q3) and already fully reviewed.
**Q2 — is Split genuinely stronger or exposure-flattered?** Partly both. Per unit of exposure
(halving the two-ticket book): ~3,340 vs 2,774 = ~+20% — a real improvement, mostly from the runner
monetizing the documented tail, and per-ticket net ($1.35) is more cost-robust than Pure-Causal's
($0.88). But the raw +7,452-vs-+2,774 comparison is illegitimate: double exposure + tie-break
favoritism. Honest statement: "+20% per unit of risk, with heavier tail-dependence."
**Q3 — does W/L 1.37 justify lower WR and rolling weakness?** The W/L improvement is real (1.86 per
signal), but at SIGNAL level the book is less stable than the ticket presentation: 1 negative
quarter, 112 negative rolling-125-signal windows (~4.8%), and top-200-signal removal flips negative
(−960; that's removing 8% of signals). Pure-Causal at matched removal-share is similar (−159 at
9.5%) — both books are breadth books with thin tails, Split slightly heavier-tailed by design.
Verdict: justified as an EXPERIMENT, not as a replacement.
**Q4 — keep Pure-Causal primary + Split experimental?** Yes. Exactly that.
**Q5 — forward spec I would approve:**
- Lanes: Pure-Causal on magic 932300 (0.01 fixed, one ticket); Split-Entry on magics 932400/932401
  (TP1/runner tickets, 2×0.01, owner explicitly signs the doubled minimum exposure).
- Pre-attach (blocking, all inherited): kill-switch filename separation per lane; +75-USD-vs-AED
  guard currency check; pinned dedupe/tie-break priority in the EA guard; pinned start timestamps;
  SHA256-locked specs; no directional/session/parameter changes mid-test.
- Sample: ≥150 signals or 12 weeks per lane (state honestly: recent regime ≈1 signal/day → expect
  ~5-6 months; historic 3/day → ~10 weeks).
- Pass (Pure-Causal): PF ≥ 1.20, WR ≥ 60% (breakeven 57.8%), net > 0 after $0.10/ticket haircut,
  top-2%-removal positive, no day > 25% of net.
- Pass (Split, per SIGNAL): PF ≥ 1.25, signal-WR ≥ 40% (breakeven 35%), W/L ≥ 1.5, net > 0 after
  $0.10/ticket (i.e. $0.20/signal) haircut, top-2%-signal-removal positive.
- Kill (both): rolling-80 PF < 0.95; net negative after 100 signals; lane DD > 1.5× backtest max;
  any safety/account/magic violation. No streak-based kills (expect 7+ losing days occasionally).
**Q6 — what would make me reject Split despite +7,452?** Four things, pre-registered now: (a) the
tie-break: if the pinned causal priority can't reproduce ≥ ~6,700, the headline was an artifact;
(b) per-signal accounting hidden from the owner — if any status page reports 52% WR without the
45%-per-decision line, that's misrepresentation; (c) forward tail failure: if slippage/spread clips
runners so the 2R leg under-delivers, this book degrades toward breakeven fast (top-200-signal
removal already flips it negative); (d) the 18% bucket (§2) surviving the BE-timing fix — see Q7 —
would mean the runner's protection doesn't work as designed.
**Q7 — one specific repair before attachment: verify/fix the runner BE-move timing.** 18% of signals
bank TP1 and then lose MORE on the runner — that should be near-impossible if the runner's SL moves
to breakeven when TP1 fills. The tester evidence says the BE move triggers late (bar-close or at a
higher threshold). Codex should confirm the EA moves runner SL to BE on the TP1 fill event itself,
and rerun the split book once with that verified. This is a mechanical-correctness fix on the already
pre-registered structure — not a new search. If it converts even half of the 18% bucket to ~breakeven
signals, signal-WR rises toward ~50% and the book strengthens materially with zero new selection debt.
One rerun, no new variants, then freeze.

## 4. Reviewer notes for agent.md
1. Split-entry evidence status: exact-MT5, causal dedupe verified, net 6,683–7,452 depending on
   tie-break priority (pin it); per-decision WR 45.3% (report alongside ticket WR always).
2. All 2022–2026 momentum data remains fully burned for entry search; these two lanes are the last
   candidates from this generation. New search happens only on 2016–2022 data or new forward data.
3. Cadence expectation for both lanes in current regime: ~1 signal/day (not 3).
