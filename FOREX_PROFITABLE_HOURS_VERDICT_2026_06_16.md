# Research Verdict — Forex "profitable hours" (19:00 & 23:00 Dubai) — 2026-06-16

**Account:** Capital.ComMena-Demo, A1 1025742. **Source:** actual MT5 broker history. **Scope:** EUR/GBP/USDJPY.
**Data:** `FOREX_PROFITABLE_HOURS_TRADES_2026_06_16.csv` (46 rows).

## Bottom line
**Treat this as a NULL result, not an edge.** The headline (+532 AED, 67% win) shrinks to a small,
fragile **+60 AED at 0.01 lot** once you strip three confounds — and that +60 is carried entirely by
**two days (June 10–11)**. It is most likely a small-sample regime artifact. **Do not restrict forex to
these hours. Observer/shadow only.**

## How the headline dissolves
| Step | Trades | Win % | PnL (AED) |
|---|---:|---:|---:|
| Raw (as reported) | 46 | 67.4% | **+532.2** |
| − lot-size: 42 of 46 were **0.05**; normalize to 0.01 | 46 | 67.4% | +116.1 |
| − de-duplicate stacked EAs (46 = **33 unique signals**, ~1.4×) | 33 | 60.6% | +298 (raw) |
| **De-confounded: dedup + 0.01 lot** | **33** | **60.6%** | **+60.5** |
| − remove the single best day (June 10) | 32 | — | +25.5 |
| − remove the **two** carrying days (Jun 10–11) | 25 | — | **negative** |

## Answers to the eight questions

**1. Meaningful or small-sample artifact?** Artifact, almost certainly. The 33 unique signals fall on
only **7 distinct days**, and June 10 (+35) and June 11 (+28.5, a 6-for-6 day) account for more than the
entire +60.5. The other 5 days net ~zero-to-negative; 4 of 7 days positive is a coin flip. A binomial test
on 33 "independent" trades gives p=0.0007 (Bonferroni×24h = 0.016), but that **independence assumption is
false** — within-day trades share one market state, so the effective sample is ~7 days, which is not
significant.

**2. Observe, restrict, or shadow-rule first?** **Shadow/observer rule only.** Restricting forex to these
hours would be textbook overfitting on 7 days (2 of them lucky). Do not expand forex either — it loses
overall. Log forward and accumulate independent days before considering any action.

**3. Which symbols / EAs carry the profit?** Symbols: **EURUSD** (20 signals, 65%, +183 raw) and **GBPUSD**
(13, 54%, +115); **no USDJPY**. EAs: spread **broadly across all of them** — breakout_retest, swing,
session_extreme, round, and the repair lane all "won" in these hours. That breadth is itself a red flag:
when even the known-losing EAs (session_extreme, round) win in a window, it's the **market that moved**
favorably, not the strategies — i.e. a time/regime effect, not an edge.

**4. Duplicate/stacked trades inflating?** **Yes, modestly.** 46 trades = 33 unique signals (~1.4× stacking;
the first three rows are one EURUSD SELL counted 3×). Stacking inflates the trade count and, with the 0.05
lots, the PnL. Dedup drops 67% → 61%.

**5. Normalized to 0.01?** **Large effect — this is the biggest single confound.** 42 of 46 were 0.05 lot.
Raw +532 → +116 (raw, 0.01) → **+60.5 (dedup, 0.01)**. At the lot size you now use, the result is ~9× smaller
than the headline.

**6. Follow-up tables Codex should generate (no history rewrite):**
- **Per-day jackknife** of these two hours (dedup, 0.01) — confirm the 2-day dependence and watch it forward.
- **Full 24-hour table** (dedup, 0.01-normalized) so 19/23 can be seen against *all* hours — a real session
  effect should be **smooth across adjacent hours** (18, 20, 22, 00), not two isolated spikes.
- **Adjacent-hour control** (18:00, 20:00, 22:00, 00:00) — if they look just as good, 19/23 were multiple-
  comparison luck.
- **Cost/spread per trade in-window** — is the "edge" really just lower spread at those hours?
- **Forward shadow log** of forex signals in these hours from today on (new independent days only).

**7. Proposed rule for next week:** **No trading rule.** A *shadow* rule: tag and log every forex signal in
19:00 and 23:00 (plus the four adjacent control hours), record outcome and 0.01-normalized PnL, accumulate.
Pre-registered bar to ever act: over **≥15–20 NEW independent days**, the dedup/0.01 win rate stays clearly
above break-even, is **not** driven by 1–2 days, and the adjacent control hours are **not** equally good.
The only mechanistically defensible version is "**active NY session**" (19:00 ≈ NY morning) tested as a
*band with a reason* — never two cherry-picked isolated hours.

**8. What would invalidate it (any one kills it):**
- Forward shadow reverts toward the ~32% base rate (most likely outcome).
- Adjacent control hours win about as much → 19/23 were just 2 of many noisy hours.
- Removing the best 1–2 days flips it negative (already true in-sample) and recurs forward.
- The effect is explained by spread/cost (cheap-spread hours), not direction.
- It depends on the 0.05-lot history and vanishes at 0.01 (largely already true).

## Safe next step
Add the shadow log + the 24-hour and adjacent-control tables. Change no live trading. Re-evaluate after
≥3–4 weeks of new independent days. This neither rewrites history nor overfits — it just keeps watching.
