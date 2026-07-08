# ROADMAP — XAUUSD Regime Taxonomy + Specialist Router (exact-MT5)

**For:** Codex + owner review
**Date:** 2026-07-08
**Author:** independent reviewer
**Status of evidence:** `REGIME_DEPENDENCE_CONFIRMED` — the current blend's edge is regime-locked (long box = bull harvester; short = down-regime only; freq = near-breakeven filler).

---

## 0. Verdict up front

**Yes — "regime specialists + router" is the correct architecture and strictly better than continuing the one-combined-strategy hunt.** Your own audit proves why a single strategy can't work: the long box did 78.3% WR / +$10,845 in the 2025 bull but $0 in Q2-2026; the short is positive only in down-regimes; the freq engine is near-breakeven padding. No single edge spans regimes. Routing solves exactly this — arm the proven engine for the current regime, stand down when none has proven edge.

**But two disciplines make or break it:** (a) the router must **stand down** in un-edged regimes (that is a feature, not a gap), and (b) you must **quarantine the freq filler** — it fails cost stress (stress W/L 1.33) and only exists to fake activity, which this architecture explicitly rejects.

Good news: your EA already has the detector primitives (D1 support-state gate, D1 structural-down EMA50, D1 compression by ATR percentile, ATR floors, pullback/sweep/opening-range). The router is mostly wiring, not new indicators.

---

## 1. Regime taxonomy (prioritized cascade, causal, completed-bars only)

Five states, evaluated **top-down, first match wins** (mutually exclusive by priority). All detection uses **completed** D1/H4/H1 bars (index `[1]` and older), never the forming bar.

### R0 — SHOCK / abnormal volatility  *(priority 1: STAND DOWN)*
- **Detect:** most recent completed H1 (or M15) true range ≥ `k`×trailing ATR (e.g. ≥ 3.0×H1 ATR14), OR D1 ATR14 > its 95th percentile over trailing 60 D1 bars.
- **Timeframes:** H1/M15 range vs ATR; D1 ATR percentile.
- **Indicators:** ATR14 (existing `InpAtrPeriod`), rolling ATR percentile.
- **Lookahead avoidance:** use the last *closed* bar's range and a trailing percentile that excludes the current bar.
- **Failure mode:** whipsaw right after a news candle; specialists get stopped both ways. → **No trade** (or minimal) until vol normalizes.

### R1 — Strong D1 uptrend  *(priority 2)*
- **Detect:** `D1 close[1] > D1 EMA20[1] > D1 EMA50[1]` AND `EMA20[1] >= EMA20[6]` AND `EMA50[1] >= EMA50[6]` (both rising).
- **Timeframes:** D1 primary; H4 EMA20>EMA50 as confirmation.
- **Indicators:** existing `InpD1SupportStateEmaPeriod=20`, `InpD1StructuralDownEmaPeriod=50` (reuse as up-stack), slope lags.
- **Lookahead avoidance:** all EMAs on completed D1 bars.
- **Failure mode:** late in a blow-off top the trend reads "up" right before a reversal → mitigate with the SHOCK/expansion check having priority.

### R2 — Strong D1 downtrend  *(priority 3)*
- **Detect:** `D1 close[1] < D1 EMA20[1] < D1 EMA50[1]` AND `EMA20[1] <= EMA20[6]` AND `EMA50[1] <= EMA50[6]` (both falling). (This is the structural-down gate you already added.)
- **Timeframes:** D1 primary; H4 EMA20<EMA50 confirmation.
- **Indicators:** `InpD1StructuralDownEmaPeriod=50`, `InpD1SupportStateGateMode=3/4`.
- **Failure mode:** sharp counter-rallies (gold squeezes hard) stop breakdown shorts → require an H1/H4 lower-high before entry.

### R3 — Compression / low-volatility range  *(priority 4)*
- **Detect:** `D1 ATR percentile <= 30` over trailing window AND price oscillating inside a box (median D1 range small) — your existing `InpD1CompressionAtrPercentileMax=30`, `InpD1CompressionBoxDays=5`, `InpD1CompressionRangeMedianMax`.
- **Timeframes:** D1 compression + M15/M5 box edges for entries.
- **Failure mode:** false breakouts at box edges; range "works" until the expansion that ends it. → tight risk, small size, or no-trade.

### R4 — Chop / undefined  *(priority 5: NO TRADE)*
- **Detect:** none of R0–R3 cleanly true — e.g. D1 EMA20/EMA50 mixed (price between them, flat slopes), or D1 and H4 trend disagree.
- **Action:** **no trade.** This is the safety default. Most calendar time that isn't a clean trend or compression lands here, and not trading it is how you protect the book.

**Note on pullbacks:** do NOT make "pullback inside uptrend/downtrend" separate regimes. A pullback is *how you enter* the trend specialist (entry logic within R1/R2), not a regime. Treating it as a regime multiplies states and invites overfitting.

---

## 2. Specialist per regime

| Regime | Specialist | Entry concept | Stop | Target | Expected WR / payoff | Freq | 50%WR@2R realistic? | Role |
|---|---|---|---|---|---|---|---|---|
| **R1 uptrend** | Pullback-continuation LONG (+ the H4/D1 box) | buy a pullback to H1/M15 EMA20 or prior breakout level, in D1-up | below the pullback swing low + ATR buffer | fixed 2R | **50–67% WR**, W/L 2.0–2.5 (box already 67%/2.49 in-regime) | low–med | **Yes** — the one regime where it's real | **Standalone** (proven) |
| **R2 downtrend** | Breakdown-retest / failed-reclaim SHORT (short_v4/R3 line) | short the retest of broken support, or a failed reclaim of a swept high, in D1-down | above the retest/sweep high + ATR buffer | fixed 2R | **35–42% WR**, W/L 2.0–2.6 (structurally capped) | low–med | **No** — gold shorts cap ~33–40% at 2R | **Standalone (weak) → mainly hedge** |
| **R3 range** | Range-fade / opening-range reversal | fade box extremes with confirmation, or fade a failed opening-range break | just beyond the box edge + ATR | fixed 2R or scale at 1R | ~40–48% WR, W/L ~1.5–2.0 (unproven on gold) | low | Unlikely | Build only if it clears gates; else **no-trade** |
| **R0 shock** | — | — | — | — | — | — | — | **No trade** |
| **R4 chop** | — | — | — | — | — | — | — | **No trade** |

**Reality check per your own data:** only R1 (long-in-uptrend) can plausibly hit ~50% WR at 2R — the box does 67% in-regime. R2 (short-in-downtrend) cannot; accept 35–42% and treat it as coverage/hedge. R3 is speculative; require it to earn its place or route it to no-trade.

---

## 3. What to code first (ranked)

**#1 — The ROUTER itself (D1 regime gate + arm/disarm).** Highest expected value, lowest effort. It immediately converts your proven long box from "bleeds when it fires off-regime" to "stands down." In Q2-2026 alone that is ~+$1,500 of loss avoidance (the box's off-regime losses simply don't happen). It reuses existing gates. Build this before any new specialist.
- **Gate to accept the router:** with the long box gated to R1 and the short gated to R2, the routed book's Q2-2026 net ≥ breakeven AND full-window net not reduced vs current AND the long box takes **zero** trades outside R1.
- **Stop this path if:** the D1 regime label whipsaws so often that specialists are switched mid-trade > ~15% of the time (add a regime-persistence/hysteresis rule, don't abandon).

**#2 — The R2 DOWNTREND SHORT specialist.** This is your biggest missing piece (non-uptrend coverage) AND the current regime (gold is below D1 EMA20/EMA50 right now). You already have short_v4/R3 as a head start.
- **Gate:** in R2 episodes only — PF ≥ 1.30 after −$0.30/ticket, W/L ≥ 2.0, positive across ≥2 of the 3 independent down-episodes in 2022–2026, ≥ ~1 trade/week when R2 is active. WR wherever it lands (~35–42%, NOT a gate).
- **Stop this path if:** it can't beat breakeven-after-cost inside R2 across ≥2 independent down-episodes. Then shorts are hedge-only, permanently.

**#3 — The R1 PULLBACK-CONTINUATION LONG.** Raises the uptrend specialist's frequency/WR and reduces reliance on the sparse box. Lower urgency because R1 is already covered by the box.
- **Gate:** in R1 episodes — WR ≥ 50%, W/L ≥ 2.0, PF ≥ 1.5 after cost, positive in ≥3 of 4 years' up-episodes.

Do **not** build R3 range or R0/R4 (they're no-trade) until #1–#3 are proven.

---

## 4. Router design (cleanest form)

- **Hard mutually-exclusive states** via the §1 priority cascade on completed bars. Exactly one regime is active per bar.
- **Specialists do NOT overlap:** one active regime → one specialist armed; all others disarmed. Overlap creates conflicting signals and double-counts.
- **Priority order:** `SHOCK > UPTREND > DOWNTREND > RANGE > CHOP`. (Shock overrides trend so you don't trade into a news candle.)
- **Undefined/chop = NO TRADE.** Non-negotiable — this is the mechanism that stops the book bleeding in un-edged conditions.
- **Add regime hysteresis:** require a regime to hold for ≥ N completed D1 bars (e.g. 2) before switching, so a one-bar EMA flicker doesn't flip engines mid-trade. Preregister N.
- **Quarantine the frequency engine.** `freq_step3` is near-breakeven (stress W/L 1.33) and exists only to pad activity. Do **not** run it across all regimes. Either drop it from the routed book, or restrict it to a single regime where it independently clears PF ≥ 1.2 after cost (your data suggests none). Fake activity is not a goal in this architecture.

---

## 5. Anti-overfit rules (preregister every specialist before running)

```
[ ] Fix ALL regime-detector params BEFORE testing any specialist. Never tune the router to rescue a specialist's losses.
[ ] Reuse existing detector primitives (EMA20/EMA50, ATR14, the compression/pullback inputs). No new indicator families.
[ ] <= 3-4 thresholds per detector. If a regime needs 6 thresholds to "work," it is overfit.
[ ] No month / date / hour masks. No hour filters discovered from losses.
[ ] RR is fixed per specialist. Never lower RR to lift WR or pass a gate.
[ ] No low-edge frequency filler to fake activity. Activity = real-edge trades only.
[ ] Do NOT delete a profitable source just to raise WR.
[ ] One specialist = one fixed config. No grids; if you test 2-3 variants, pre-commit the selection gate and tie-break to the simpler config.
[ ] Every specialist must be net-positive-after-cost AND stable across >=2 independent episodes of its own regime (multi-year / walk-forward), not just the recent one.
[ ] Report every run, including failures. Router assignment must be causal (completed bars, verifiable).
```

---

## 6. Acceptance gates (realistic — 90% weeks/activity are retired)

**Standalone specialist (judged INSIDE its assigned regime):**
```
R1 long:   WR >= 50%, W/L >= 2.0, PF >= 1.5 after -0.30/ticket, positive in >=3 of 4 up-episodes
R2 short:  WR wherever (~35-42%), W/L >= 2.0, PF >= 1.30 after cost, positive full-window after cost,
           positive in >=2 of 3 down-episodes
R3 range:  PF >= 1.20 after cost in-regime, W/L >= 1.8 — else route to NO-TRADE
All:       >= ~1 trade/week when its regime is active; no single trade > 25% of net; no single day > 30%
```

**Final routed portfolio:**
```
[ ] Full-window net > 0, PF >= 1.4 after -0.30/ticket
[ ] Recent 3 months >= breakeven (regime-appropriate engine live)
[ ] Positive months >= 60% (not 90%)
[ ] Max DD <= ~$1,000 (or <= 8% of net)
[ ] Walk-forward: >= 6 of 8 six-month blocks >= breakeven
[ ] No filler: every source in the book independently clears PF >= 1.2 after cost in its regime
[ ] Blended WR ~45-52%, W/L >= 2.0 after cost (WR carried by R1, not gated per-source)
[ ] Exact-MT5 verified end-to-end; no offline masks
```

---

## 7. Final verdict (direct answers)

1. **Better than one-combined hunt?** Yes, decisively. Your audit proves no single strategy spans regimes; routing + stand-down is the architecture that fits the evidence.
2. **Essential XAUUSD regimes:** **SHOCK (stand down), UPTREND (long), DOWNTREND (short), RANGE/COMPRESSION (build-or-no-trade), CHOP (no trade).** Pullbacks are entry logic within trend, not regimes.
3. **Code first:** the **ROUTER** (D1 regime gate) — immediate loss avoidance on the proven long box — then the **R2 downtrend short** (missing coverage + current regime).
4. **Stop immediately:** forcing the long box to trade outside uptrends; padding the book with the near-breakeven freq filler; chasing 50% WR / 2R on shorts (structurally impossible); the one-combined-strategy hunt; any post-hoc month/hour masks; deleting profitable sources to lift WR.
5. **Demo-review-worthy result:** a routed, exact-MT5 book where — long trades only in R1, short only in R2, no trade in R0/R3/R4 — the portfolio is **positive full-window AND in the recent 3 months, ≥60% positive months, Max DD ≤ ~$1k, PF ≥ 1.4 after cost, walk-forward positive in ≥6/8 blocks, with no filler**, and each engine is individually positive-after-cost in its own regime across ≥2 independent episodes. Hit that, and it earns a small frozen forward-demo review.

---

## 8. Suggested commit sequence
```
C1  Router: preregister regime cascade + hysteresis (hash it); wire D1 gate to arm/disarm long(R1)/short(R2); exact-MT5 run; parity check the long box is unchanged inside R1.
C2  R2 downtrend short specialist: preregister; exact-MT5; judge on §6 R2 gates across down-episodes.
C3  R1 pullback-continuation long: preregister; exact-MT5; §6 R1 gates.
C4  Routed-portfolio scoring vs §6 portfolio gates; freq quarantined. Verdict; no demo without reviewer sign-off.
```
Nothing goes to demo until the routed portfolio clears §6 and a reviewer signs off. Exact-MT5 only throughout.
