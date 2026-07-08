# DECISION + FINAL TEST — XAU Standalone Short, WR50/RR2 Goal (exact-MT5)

**For:** Codex
**Date:** 2026-07-08
**Reviews:** commit `bb27575a` (WR50/RR2 research packet)
**Governance:** exact-MT5 only, isolated backtest terminal, no live/demo runtime. No hour/session/day/month masks. No lowering RR. Report every run.

---

## 0. Verdict (strict)

**The WR≈50% at fixed ~2R goal is not achievable for a standalone XAUUSD short, and this commit is the proof. Stop chasing it.** Run ONE final falsification test (§4). If it also lands < ~45% WR — which is the expected outcome — the WR50 question is permanently closed and you adopt the reframed target in §5.

This is not pessimism; it is arithmetic plus your own exact-MT5 evidence.

---

## 1. Why WR50 at RR2 is structurally impossible here (the math you're fighting)

At a **fixed** RR (TP = 2R, SL = 1R), **win rate is not a tunable parameter.** It equals `P(price travels +2R in your favor before −1R against)` — a property of the asset's path distribution, not of your entry filter. Filters change *which* setups you take; they do not change gold's path statistics at a 2:1 target.

Fixed points at RR2:
```
Breakeven WR at RR2      = 1 / (1 + 2) = 33.3%
WR needed for PF = 2.0   = 50.0%    <-- your goal
WR needed for PF = 1.5   = ~42.9%
```
Your shorts sit at **33–36% WR = right at breakeven-to-slightly-positive.** To reach 50% you would need gold to hit a 2R-*down* target as often as a 1R stop — i.e., you need down-moves to be as reliable as up-moves. Gold is a **long-biased, safe-haven asset**: 2R down-moves are structurally *less* frequent and less reliable than up-moves. So the WR ceiling on the short side at RR2 is intrinsic. The only levers that raise WR are **lowering RR** (forbidden) or **switching to an asset/side with symmetric or down-skewed paths** (not gold shorts).

---

## 2. Your own exact-MT5 evidence (the empirical proof — recomputed independently)

Four **structurally different** short archetypes, same RR2, all converge:

| Archetype | Variant | Trades | **WR** | W/L | PF | Net | 2023+2024 |
|---|---|---:|---:|---:|---:|---:|---:|
| Momentum-breakdown/retest | v2 R1 (D1 EMA20 bearish) | 329 | **32.83%** | 2.83 | 1.38 | +$441 | −$193 |
| Same, non-up gate | v2 R2 (D1 EMA20 non-up) | 393 | **33.84%** | 2.65 | 1.36 | +$508 | −$166 |
| Same, structural gate | v2 R3 (D1 **EMA50** down) | 242 | **36.36%** | 2.47 | 1.41 | +$346 | −$78 |
| Reversal (lower-high rejection, mode 17) | lower_high | 302 | **33.44%** | 2.12 | 1.06 | +$120 | −$15 |

**Read this table as the answer.** Four different entry structures (continuation, retest, regime-gated, exhaustion-rejection) land in a **3-point band (32.8–36.4%)**. That tight convergence is the fingerprint of a structural ceiling — not a tuning failure and not the "wrong filter." The stronger structural gate (R3, the fix I recommended) did the most it could: WR +3.5 pts and 2023+2024 from −$193 to −$78 — an improvement, but still short of breakeven-years and nowhere near WR50.

**Conclusion:** no additional M5 short archetype or filter at RR2 will reach 50% WR. Continuing to test toward WR50 is spending exact-MT5 cycles to re-confirm a known ceiling.

---

## 3. Answers to your questions

1. **Realistic?** No. Proven by four converging archetypes at 33–36% and by the fixed-RR math (50% WR ⇒ PF 2.0 on the counter-secular side of a long-biased asset).
2. **Wrong archetype?** No — the ceiling is the RR, not the setup. No short archetype naturally yields 50% WR at RR2 on gold. Reversal setups (which should have the highest WR) already landed 33% (lower-high).
3. **Next direction (resistance rejection / spike fade / sweep into HTF resistance)?** Reversion/exhaustion fades are the only ones with a *theoretical* shot at higher WR, and they're worth exactly ONE final falsification at the **higher-timeframe** scale (H4/D1 level, not M5). Expect ~36–42%, not 50%.
4. **Precise next test:** §4 below (H4/D1 major-resistance fade), scored on the **reframed** gate, run once, as the closer on WR50.
5. **Stop doing:** chasing WR50 at RR2; adding filters/archetypes to lift WR; treating 33% WR as "failure"; testing more continuation/breakdown variants (converged); any hint of lowering RR to fake WR.
6. **Methodological problems?** None found. Mode 17 (`BEAR_LOWER_HIGH_REJECTION`) uses fixed inputs and completed-bar structure (swing high over 48 bars, pullback high, prior drop, EMA touch/reclaim, confirmation body) — no lookahead evident, and the un-inflated 33% WR corroborates that. R1/R2/R3 reproduce exactly; the gates/year/block reports are consistent. Clean exact-MT5.
7. **Closest defensible target:** drop WR≥50 entirely (see §5).

---

## 4. The ONE final falsification test (run once, then close the WR50 question)

**`bear_h4d1_resistance_fade` — highest-timeframe exhaustion fade.** This is the single archetype most likely to lift WR, tested at the HTF scale you haven't tried. If it fails, WR50 is done.

**Preregistered exact rule (fixed params, completed bars, short-only, RR 2.0):**
```
Regime:   D1 non-up  (D1 close[1] <= D1 EMA20[1])   [reuse existing gate]
Level:    identify a major resistance = the highest H4 high over the last 30 completed H4 bars
          (or the nearest 25-USD round number above price within 0.5 x H4_ATR) — pick ONE, fixed.
Tag:      current M5 high comes within 0.20 x M5_ATR of that resistance level.
Reject:   an M5 bar closes back below the level with body_fraction >= 0.50 and an upper wick
          >= 40% of its range (bearish rejection).
Entry:    short at that rejection close.
Stop:     above the tagged high + 0.25 x M5_ATR (this is the 1R).
Target:   2.0 x stop distance (fixed RR2). No trailing/BE/partial.
Params fixed: H4 lookback 30, tag 0.20 ATR, body 0.50, wick 0.40, stop buffer 0.25 ATR.
```

**This test is judged on the REFRAMED gate (§5), NOT on WR50.** Its only WR job is falsification: if `bear_h4d1_resistance_fade` WR < ~45% (expected), stop pursuing WR50 permanently.

Do not sweep the params. One fixed configuration. Report it and stop.

---

## 5. Reframed standalone short target (adopt this)

Because WR and RR are inversely coupled at a fixed RR, judge the short by **expectancy and stability**, not WR:
```
[ ] W/L >= 2.0                     (already achieved — keep RR2, do not lower it)
[ ] PF after -0.30/trade >= 1.30
[ ] Full-window net > 0
[ ] Positive or breakeven in >= 3 of 4 calendar years  AND  2023+2024 combined >= 0
[ ] >= ~200 trades (meaningful frequency)
[ ] Net survives removing top-10 trades and top-3 days (not outlier-driven)
WR: whatever it lands at (~33-38%). NOT a gate.
```

**Honest status vs this reframed target:** the best candidate (R3, structural EMA50 gate) is close on PF (1.41) and W/L (2.47) but **still fails multi-year** (2023+2024 = −$78). So even the *reframed* standalone bar is not yet met — the remaining, realistic goal is to get 2023+2024 to breakeven while keeping PF ≥ 1.3, not to reach WR50.

---

## 6. Decision tree

```
Run §4 once.

If bear_h4d1_resistance_fade meets the §5 reframed gate (incl. 2023+2024 >= 0):
    -> it becomes the standalone short base. Draft a forward-watchlist spec (separate, reviewer-signed). No demo.

Else if it improves WR to ~40-45% but still fails §5 (likely):
    -> WR50 is CLOSED. Best standalone candidate is R3 (structural gate). It is a
       weak, regime-dependent edge. Do NOT run it standalone.
    -> Adopt the short as a COMBINED-PORTFOLIO HEDGE only (per the earlier hedge packet:
       near-silent in bull quarters, positive in the long-box's bad quarter).

Else (WR stays ~33-36%, §5 fails):
    -> Same as above: WR50 closed; short = hedge-only; stop standalone short iteration.
```

**Most probable outcome:** the last two branches. Plan for "short is a hedge, not a standalone specialist, and WR50 was never attainable." That is the correct, high-value conclusion — not a failure.

---

## 7. Forbidden (unchanged, mandatory)
```
[ ] No lowering RR to lift WR.
[ ] No hour/session/day/month masks.
[ ] No stacking quality filters to chase WR (proven: shrinks sample, doesn't move the ceiling).
[ ] No parameter sweep on §4 — one fixed config.
[ ] No citing any short's net without disclosing WR and the 2023-2024 result.
[ ] No demo / forward-watchlist without the §5 gate passing and reviewer sign-off.
```

---

## 8. One-line summary for the owner
WR≈50% at fixed 2R is mathematically a PF-2.0 counter-secular gold short — your four exact-MT5 archetypes all land 33–36%, which is the structural ceiling, not a bug. Run one final H4/D1 resistance-fade to confirm, then stop chasing WR50: keep the short at its natural ~33–36% WR / 2.0+ W/L shape and use it as a portfolio hedge, targeting PF ≥ 1.3 with 2023–2024 at breakeven — not a standalone 50% win rate.
