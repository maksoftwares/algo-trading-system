# FX Edge Research — Phase 1 Findings (2026-06-14)

**Goal:** find a real, FX-native trading edge for EUR/GBP (no money — offline research),
before deciding whether to build anything. Pre-registered bar for a "candidate worth
shadow-testing": win rate ≥ ~50% with positive expectancy net of spread, **stable across a
train/test split**.

**Data:** M5 replay bars, 2026-06-01 → 2026-06-12, ~2,700 bars/pair (~11 calendar / ~10
trading days). Real per-bar `spread` column used for costs. **This is a thin, in-sample
window** — strong enough to *reject* ideas, far too small to *confirm* one.

**Verdict: NO-GO.** No FX edge survived. Do not build an FX lane on anything tested here.

---

## What we did and found

### Step 1 — Characterize the market (does the premise even hold?)
Before testing a "fade the spike" idea, we checked whether EUR/GBP actually mean-revert at M5.

| Symbol | Lag-1 autocorrelation | Reverts after a >2σ spike (1 bar) | Read |
|---|---:|---:|---|
| EURUSD | **+0.06** | 43% | mild *trend*, not reversion |
| GBPUSD | +0.01 | 52% | random |
| XAUUSD | 0.00 | 56% | random |

The mean-reversion premise is **false** at M5 — EURUSD mildly continues, the rest are coin
flips. A naive fade strategy was killed before we built it. (Gold's edge isn't bar-to-bar
predictability either — it's structure + session + wide stops.)

### Step 2 — Screen principled entries (R:R 1.5, net of real spread)
All standard archetypes, both pairs, in-sample:

| Strategy | EURUSD | GBPUSD |
|---|---|---|
| A. Naive breakout (continuation) | 46% WR, −0.17 R/trade | 39% WR, −0.48 R |
| B. Failed-breakout fade (reversion) | 32% WR, −0.52 R | 39% WR, −0.51 R |
| C. Trend-aligned breakout | 47% WR, −0.14 R | 39% WR, −0.49 R |

**Every variant loses**, even in-sample, even before overfitting concerns. Fade is the
worst (confirms Step 1). EURUSD trend-aligned is the "least bad"; GBP is worse across the
board — partly because its spread (~1.3 pip) is roughly double EUR's (~0.7 pip), a real drag
at this trade frequency.

### Step 3 — Quality vs frequency probe (EURUSD trend-aligned)
Does demanding *fewer, higher-quality* trades help? (Directly tests the "trade more = more
profit" idea.)

| Variant | Trades/day | Win rate | Expectancy |
|---|---:|---:|---:|
| base | 27 | 47% | −0.14 R |
| + strong break (>0.25 ATR) | 18 | 43% | −0.25 R |
| + high-volatility only | 15 | 51% | **+0.08 R** |
| + London/NY hours (07–15 UTC) | 11 | 52% | **+0.11 R** |
| + strong & session | 7.5 | 46% | −0.06 R |

Clear signal: **frequency was the enemy.** Cutting from 27 to ~11 trades/day (active session
only) lifted win rate 47% → 52% and flipped expectancy positive. This is the opposite of
"trade more," and it mirrors why gold works: selective, session-gated, not high-churn.

### Step 4 — Robustness (the test that matters)
Split the one positive candidate (EURUSD, trend-aligned, London/NY hours) into first vs
second half:

| Window | n | Win rate | Expectancy |
|---|---:|---:|---:|
| EURUSD full | 124 | 52% | +0.11 R |
| EURUSD **first half** | 73 | **60%** | +0.30 R |
| EURUSD **second half** | 51 | **41%** | −0.17 R |
| GBPUSD full | 116 | 42% | −0.23 R |

**The "edge" was first-half luck.** It earns 60% for ~5 days, then collapses to 41% and goes
negative. It does not persist. This is the exact overfitting signature that produced the
earlier repair lanes (great on the window they were fit to, losers afterward). GBP never
worked at all.

---

## Conclusion & recommendation

We tested the obvious FX edges — continuation, reversion, trend-aligned, with
strength/volatility/session filters — and **none produces a stable, positive expectancy.**
The single in-sample winner failed a basic two-way split. On the evidence we have, **there is
no FX edge to deploy or even to shadow-test yet**, because we don't have a hypothesis that
survives even minimal out-of-sample scrutiny.

Two honest caveats, both pointing the same way:
- 10 trading days is too thin to *confirm* any edge — but it's enough to show these
  candidates *fail*, and a real edge usually shows *some* cross-split stability even on small
  data. None did.
- FX edges, if they exist, more often live on higher timeframes (H1/H4) or in non-price
  signals (news, rates, flow) — but we have far too few H1 bars here (~260) to test that
  without generating more noise.

**Recommended path:**
1. **Default — don't build FX. Put the energy into gold, where a real edge exists.** The
   opportunity cost of chasing a missing FX edge is the bigger risk.
2. **If you still want to pursue FX**, treat it as a multi-week program, not a quick fix:
   collect a longer, clean dataset (weeks of bars + a shadow logger), test genuinely
   different signal families (H1/H4 structure, session-bias, volatility regimes), and only
   promote a candidate that clears the bar **out-of-sample, forward, in shadow** — the same
   discipline that just saved us from shipping a 60%→41% mirage.

**The transferable lesson for both gold and FX:** the route toward winning was *fewer,
higher-quality, session-timed* trades — not more of them. Frequency multiplies whatever edge
you have; it never creates one.
