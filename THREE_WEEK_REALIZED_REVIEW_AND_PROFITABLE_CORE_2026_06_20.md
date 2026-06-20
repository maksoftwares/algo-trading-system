# 3-Week Realized-Trade Review — The One Profitable Core + Next-Week Plan

Date: 2026-06-20
Source of truth: `PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv` (Friday export) — 2,059 **actual broker fills** (real spread/costs already in `profit_aed`), 1,989 closed, deduped to 1,247 unique trades. Span 2026-06-01 → 2026-06-19. Demo-only throughout.

This answers the owner's question directly: *was there a profitable core, can we isolate it, cut the bad trades, and repeat it?*

> **CORRECTION (2026-06-20, independently verified with Codex).** Magic 920101's +708.59 belongs to the **A1 standard book (account 1025742)**, NOT A2. Verified three ways: A2's own direct history reproduces at **12 trades / −55.09 AED (negative)**; the primary CSV's 920101 position-tickets have **zero overlap** with A2's; and the export README confirms the primary CSV is the A1 standard export. **Read every "A2 Tier-1 breakout" below as "A1 920101 breakout lane."** A2's clean breakout account is *unproven/negative*, so the profitable evidence sits on the noisier A1 book — which makes a clean forward test more important, not less. Cross-account check (Jun 10–19, both accounts live on the same rule): A1 evening +223.20 (15 tr) vs A2 evening −55.09 (12 tr), combined +168.11 — positive but account-divergent and small.

---

## 1. Ground truth: the 3 weeks lost money on real fills

| Cut | Realized P&L (AED) | Trades |
| --- | ---: | ---: |
| Raw (incl. duplicates) | **−2,966.81** | 1,989 |
| **Deduped (unique signals only)** | **−3,141.76** | 1,247 |

Duplicates netted only +175 AED — the loss is real, not a dedup artifact. By every slice, deduped:

- **By symbol:** XAUUSD −942 · EURUSD −828 · GBPUSD −1,304 · USDJPY −25 · BTCUSD −43 → *all negative.*
- **By direction:** BUY −2,312 (WR 31%) · SELL −830 (WR 38%) → BUY bled most.
- **By session:** Evening −43 (≈breakeven) · Morning −858 · Afternoon −1,061 · Night −1,180.

So "we have been very profitable" is not true at the portfolio level on real money. What *was* true is below.

## 2. The one profitable core — and it survives an out-of-sample test

Of 20 strategy lanes (magics), **exactly one** made real money: **magic 920101 = A2 Tier-1 breakout, XAUUSD.**

| 920101 (A2 breakout, XAU) | P&L | Trades | WR | PF |
| --- | ---: | ---: | ---: | ---: |
| Full period | **+708.59** | 113 | 46% | 1.45 |
| First half (in-sample) | +593.08 | 56 | 46% | 1.99 |
| **Second half (out-of-sample)** | **+115.51** | 57 | 46% | 1.12 |

And almost all of it is **Evening (16:00–19:59)**:

| 920101 Evening XAU | P&L | Trades | WR | PF |
| --- | ---: | ---: | ---: | ---: |
| All evening | **+701.86** | 27 | 67% | 3.75 |
| Evening first half | +433.65 | 13 | 77% | 6.26 |
| **Evening second half (OOS)** | **+268.21** | 14 | 57% | 2.55 |

This is the only thing in 2,059 trades that made money **and** stayed positive when split out-of-sample. The owner's intuition that "something is working" is correct, and the data names it precisely: **A2 breakout, XAUUSD, Evening session.**

## 3. The honest caveats — promising, not proven

- **It cooled in the most recent week.** 920101 made +773 over Jun 1–12 (peak +962 on Jun 11) but **−64 over Jun 13–19**, with two ugly days (Jun 12 −189, Jun 17 −207). The edge has stalled in exactly the newest data.
- **Small sample.** Evening core = 27 trades; the OOS evening half is 14. PF looks great but the sample can't rule out luck.
- **Multiple-comparisons risk.** ~20 magics × 4 sessions ≈ 80 cells. Finding *one* cell with PF>1 that survives a single split is roughly what you'd expect by chance under no edge. One OOS split is suggestive, not conclusive.
- **The naive "keep what worked" filter fails in general.** Selecting first-half-positive magics and applying them unchanged to the second half returned **−315 (PF 0.60)** — only 920101 held; the other first-half winner (920504) reverted. So "repeat the winners" only works for this one specific cell, which is exactly why it must be confirmed forward, not assumed.

## 4. What this means — and the lever that's actually real

The biggest, most reliable lever is **not** finding more edge — it's **cutting the concentrated losses**, which the owner correctly intuited as "reduce the bad trades":

- The other 19 lanes + non-evening sessions + GBP/EUR/JPY lost **~3,850 AED**. Those losses are concentrated and removable.
- Cutting them is a near-certain improvement; it doesn't depend on predicting anything.

## 5. Next-week plan (the owner's hypothesis, done with discipline)

1. **Isolate the core.** Run ONLY the A2 Tier-1 XAU breakout (920101), **Evening session only**. Pause everything else (A1 lanes, A3, all non-evening, GBP/EUR/JPY). This alone removes the bulk of the bleed.
2. **Pre-register it as a forward test.** Lock the exact rule (920101 breakout, XAU, 16:00–19:59) and measure net P&L on **new** evening sessions only — no tuning. This is the single clean experiment.
3. **Decide on persistence, not hope.** If evening-XAU-breakout keeps printing net-positive over the next ~2–4 weeks of forward evenings, it earns a small size increase. If it reverts to the Jun 13–19 behavior (flat/negative), it was luck and we stand down that lane too.
4. **Keep all guardrails on:** dedup (one position per signal), the A1 profit-floor guardian (after the +90.30-vs-100 trigger fix), demo-only, no broker action without passing the bar.

Expectation set honestly: the core is small (≈+700 AED / 3 weeks on 0.01 lots) and recently cooling. This plan's near-term win is **loss reduction** (cutting ~3,850 of removable bleed); the upside (a confirmed evening-breakout edge) is a *maybe* that only forward data can settle.
