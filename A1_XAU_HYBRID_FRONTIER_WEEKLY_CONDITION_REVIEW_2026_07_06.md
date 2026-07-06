# INDEPENDENT REVIEW — HYBRID FRONTIER + WEEKLY-POSITIVE CONDITION
Date: 2026-07-06 | Reviewer: Independent (Claude) | Offline only. Composition ledger independently
recomputed from `..._HYBRID_KEPT.csv`: n/WR/W-L/PF/net all reproduce within rounding. Reporting is accurate.

## HEADLINE VERDICTS
- Methodology (Q1): SOUND — exact-MT5 sources, causal composition, honest stress disclosure. One
  required fix: frontier tables MUST include top-winner-removal rows (see §2 — it changes the story).
- Proposed next step (Q5/Q9/Q12): APPROVED WITH MODIFICATIONS — one preregistered H4/D1 risk-geometry
  iteration (grid in §5), plus a loss-responsive sizing overlay, and the owner gets the weekly-math
  note (§3) NOW, not after.

## 1. Where the frontier really stands
Credit first: touching 50.23% / 2.0002 on an exact ledger is the closest this project has ever come
to the owner's corner — +0.50R/trade nominal expectancy, double the best previously validated book.
But my recompute adds two facts the summary omits:
- **Tail-carried compliance.** Remove the top 1% of winners (38 trades): W/L falls to 1.625, PF 1.62.
  Remove 2%: 1.394/1.36. Both core metrics fail on a 1% haircut. Combined with the failed +0.30
  stress (1.90), the 50/2.0 is NOMINAL, not robust. New standing gate: ex-top-1% must still show
  W/L ≥ 1.7 and PF ≥ 1.5 before anything is called demo-reviewable.
- **The monthly shape is worse than the weekly summary implies: 29/48 months positive (60%), worst
  month −$1,056** (vs June 2026's −$223 that triggered the alarm). The loss-shape problem is not a
  June anomaly; it is the book's character. H4/D1 sub-book: worst weeks −$506 to −$566, largest
  single losses −$170 to −$230 — a bad week is 3–4 clustered H4/D1 losses, exactly as diagnosed.

## 2. The weekly-positive condition — the math the owner must see (Q2/Q3/Q4)
**"Every week positive" is mathematically unattainable for any honest strategy at this frequency.**
Arithmetic: ~18 signals/week at a TRUE +0.5R/trade edge gives a weekly mean of ~9R against a weekly
standard deviation of ~6.4R (per-trade σ≈1.5R × √18) → P(positive week) ≈ 92%. Even that
world-class book prints ~17 red weeks per 4 years. To reach 99% weekly you would need ~+0.9R/trade
at the same volatility — beyond anything retail-verifiable. Therefore: any backtest that shows 100%
positive weeks over 208 weeks is, by construction, overfit, leaked, or martingale-shaped. The
current book's 58.65% positive weeks isn't a bug to eliminate; it's a variance level to reduce.
**Rigorous definition (Q2):** calendar week Mon–Sun in broker time; CLOSED P&L by EXIT date (money
truth; requires adding exit_time to composition ledgers — currently entry-only); zero-trade weeks
EXCLUDED from the positive-week ratio (the activity gate already polices them); floating week-end
equity reported as information only, never gated.
**Replacement gates (Q4)** — proposed to the owner as the "weekly loss-shape" standard:
1. Positive weeks ≥ 65% (path to 70%);
2. Worst week ≥ −2.0× average weekly net profit (at current scale ≈ −$215);
3. Rolling-4-week net positive ≥ 85% of windows;
4. Positive months ≥ 70% (currently 60%), worst month ≥ −3× average monthly net.
These produce "positive months from acceptable weeks" — the owner's stated fallback — and are
reachable by variance reduction without fabricating a straight equity line.

## 3. Answers to the remaining questions
**Q5/Q9 — is H4/D1 stop/risk geometry the right iteration? YES**, and it is the only sensible one:
count caps already failed (they amputate the engine), and the engine has WR headroom to spend
(58.0% WR, W/L 2.31 standalone) — tighter/capped stops can trade some of that WR for higher W/L,
letting the book keep composed metrics at LOWER per-trade dollar risk. Warning attached: pure
size-reduction alone will likely BREAK the composed W/L ≥ 2.0 (it shrinks the high-W/L engine's
weight against the ~1.9 substrate) — the grid must therefore include geometry cells, not just
sizing cells, and every cell must be judged on the RECOMPOSED book.
**Q6 — preregistered grid (one pass, exact MT5, declared before running):** H4/D1 components only —
- per-signal risk normalization: {$60, $90} (current implied ≈ $150–230);
- stop geometry: {current anchor; ATR-capped at 0.8× current; structure anchor + cap};
- early adverse exit: {none; exit at first H4 CLOSE beyond −0.6R};
- NEW loss-responsive sizing overlay (causal — uses only PAST realized outcomes): {none; halve
  H4/D1 size for 5 sessions after any H4/D1 loss}.
2×3×2×2 = 24 recomposed cells maximum, full kept/dropped ledgers, judged on: WR / W-L / stress-W/L /
active% / positive-week% / worst week / worst month / last-12 / June-2026. Nothing else changes: no
hours, no entries, no directions, no substrate edits. This is the H4/D1 family's single refinement
pass; after it, frozen.
**Q7 — loss caps without cheating:** allowed = smaller size, tighter/capped stop AT ENTRY, early
exit on OBSERVED H4 closes, loss-responsive sizing from PAST trades. Forbidden = post-hoc realized-
loss caps (the $50 sensitivity is direction-finding only — correctly labeled), any exit rule
referencing future bars, and any stop-trading-because-the-week-is-red rule inside a BACKTEST gate
(outcome-shaping; if the owner wants it at runtime as a preference, it must be simulated causally
and will cost expectancy — separate decision).
**Q8 — keep or remove H4/D1? KEEP.** It is the only +0.5R-class engine in four years of search;
removing it returns the book to sub-goal frontier (substrate alone ≈ +$6.2k, W/L < 2). The repair
target is its variance, not its existence.
**Q10 — promotion gates (consolidated, before "demo-reviewable"):**
core AFTER stress: signal WR ≥ 50% AND realized W/L ≥ 2.0 under +$0.30/ticket; activity ≥ 90%
weekdays; weekly loss-shape gates §2; last-12-months passes all of the above standalone;
ex-top-1%-winners W/L ≥ 1.7 / PF ≥ 1.5; H4/D1 sub-book ex-top-5 positive; ledgers reproduce under
independent recompute; manifests current; full variant ledger with cell counts.
**Q11 — missing classes for this shape?** Two, both already named in the approved plan: (a) BOOK-
LEVEL VOLATILITY TARGETING — the standard institutional answer to weekly-shape problems, causal,
untried here (the loss-responsive cell above is its first cousin); (b) RELATIVE-VALUE (gold/silver
"rubber band") — the one class whose NATURAL distribution is many-small-wins/weekly-smooth. If the
geometry iteration cannot fix the weekly shape, that family is the correct next hypothesis rather
than more XAU surgery.
**Q12 — stop and tell the owner, or continue?** Both, in parallel: run the §5 iteration (it is
cheap, preregistered, and targets the exact failure), and deliver the §3 math note to the owner NOW
so the "every week positive" expectation is renegotiated to the loss-shape gates before results
arrive. The full intersection INCLUDING literal every-week-positivity does not exist honestly; the
intersection with the §2 loss-shape gates plausibly does — that is the honest sentence for the owner.

## 4. Required process additions from this review
1. Frontier tables must carry ex-top-1%/2% rows permanently.
2. Composition ledgers must include exit_time (weekly gating is exit-dated).
3. The monthly shape (29/48, worst −$1,056) goes into the owner note alongside the weekly stats.
4. The 24-cell grid is declared, hash-logged, and run ONCE; results reviewed before any further step.
