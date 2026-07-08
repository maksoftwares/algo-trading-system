# WORK ORDER — Short Specialist V2 Robustness / Regime-Stability Pass (exact-MT5)

**For:** Codex
**Date:** 2026-07-08
**Author:** independent reviewer
**Depends on:** commit `21a41fac` (`short_hedge_v2_breakdown_retest`)
**Governance:** exact-MT5 Strategy Tester only, isolated terminal `C:\MT5A1M5MomentumBacktest`. No live/demo runtime, chart, preset, order, position, or broker change. No hour/month/session/day masking. No parameter grids for optimization. Every parameter fixed and preregistered before running. Report EVERY run.

---

## 0. Why this pass exists (read first)

V2 is the best short candidate and it is clean exact-MT5 evidence (verified: numbers reproduce, preregistered, isolated, no lookahead). **But it is not yet a structural edge.** The 4-year positive net is a 2025–2026 phenomenon:

| Year | Trades | WR | PF | Net |
|---|---:|---:|---:|---:|
| 2022 | 79 | 36.7% | 1.20 | +$41 |
| 2023 | 117 | 26.5% | **0.71** | **−$93** |
| 2024 | 58 | 17.2% | **0.56** | **−$100** |
| 2025 | 21 | 38.1% | 2.31 | +$105 |
| 2026 | 54 | 55.6% | 2.56 | +$488 |

First half (2022H2–2024H1, 69% of trades): **PF 0.77, −$147.73.** Second half: PF 2.19, +$589.
**Critical fact:** V2 already runs the D1 regime gate (`InpD1SupportStateGateMode=3`, require-bearish), and it STILL lost in 2023–2024. So this is not a "missing gate" problem.

**The single question this pass answers:** *Can any preregistered regime definition make V2 multi-year stable, or does the breakdown-retest short only work in the 2025–2026 regime?* If yes → V2-regime becomes a validated standalone base. If no → downgrade the short to a combined-portfolio hedge only and stop standalone iteration.

**Do NOT** try to raise win rate. The shape (WR ~33% / W/L 2.83, breakeven WR ~26%) is correct and fine. The target of this pass is **stability across years/blocks**, not WR.

---

## 1. Frozen execution contract (identical to V2 — do not change)

```
Symbol            XAUUSD
Timeframe         M5
Direction         SHORT ONLY
Signal mode       InpSignalMode = 15   (breakdown-retest, as in V2)
Window            2022-07-01 -> 2026-06-30
Tester model      Every Tick, real-tick-quality history
Terminal          C:\MT5A1M5MomentumBacktest (isolated backtest terminal)
Deposit / ccy     same as V2 run
Lot               0.01 fixed
RR                2.0 (TP = 2.0 x SL)   [T3 only varies this, as a robustness check]
Bear-retest params (FROZEN at V2 values):
    InpBearRetestLookbackBars        = 10
    InpBearRetestSupportLookbackBars = 12
    InpBearRetestBreakAtr            = 0.10
    InpBearRetestTouchAtr            = 0.05
    InpBearRetestReclaimAtr          = 0.05
    InpBearRetestStopBufferAtr       = 0.25
    InpBearRetestMinBodyFraction     = 0.30
H1/H4 filters      as in V2 (unchanged)
Guards             existing cooldown / daily cap / spread / cost caps — unchanged
Session/hour       24h. No session, hour, day, or month filter.
```

The ONLY thing T1 varies is the **D1 regime definition**. Everything else is frozen.

---

## 2. Test T1 — Regime-definition robustness (the core test)

Run three variants that differ ONLY in the D1 regime gate. Report all three.

| Variant | D1 regime gate | EA setting |
|---|---|---|
| **R1 (baseline/parity)** | D1 EMA20 bearish (current V2) | `InpD1SupportStateGateMode = 3` |
| **R2 (non-up)** | D1 not in up-state (`close[1] <= D1 EMA20[1]`) | `InpD1SupportStateGateMode = 4` |
| **R3 (structural down)** | slower, structural downtrend | new fixed input (below) |

**R3 exact rule (one new default-off EA input, completed bars only, no look-ahead):**
```
Enter only when:
    D1 close[1]  <  D1 EMA50[1]      AND
    D1 EMA50[1]  <= D1 EMA50[6]      (EMA50 not rising over 5 completed D1 bars)
Implement as: InpD1StructuralDownGateEnabled (default false),
              InpD1StructuralDownEmaPeriod = 50 (fixed),
              InpD1StructuralDownSlopeLagBars = 5 (fixed).
When enabled, this replaces the mode-3/4 gate for R3.
```
R3 is a stronger, slower trend filter (EMA50 vs EMA20) designed to exclude the pullback-inside-uptrend windows that likely caused the 2023–2024 losses. It is one fixed definition — not a swept family.

**T1 pass gate (per variant):**
```
[ ] Positive net in >= 3 of the 4 calendar years (2022 partial counts if positive)
[ ] 2023 + 2024 COMBINED net >= 0 (breakeven) — this is the specific hole to close
[ ] Full-window net > 0 AND cost-stress (-0.30/trade) PF >= 1.20
[ ] Trades >= 200 over the window (frequency not destroyed by the stricter gate)
```

**Selection rule (pre-committed, not argmax):** among variants that pass the T1 gate, choose the one with the **simplest** regime definition (R1 < R2 < R3), NOT the highest net. If none passes, there is no winner — go to §5 decision tree.

---

## 3. Test T2 — Walk-forward stability (gate on the T1 winner only)

Apply to whichever variant wins T1 (if any). This is the real "is it structural" test.

```
Split 2022-07-01 -> 2026-06-30 into eight fixed 6-month blocks:
  B1 2022-07..2022-12, B2 2023-01..2023-06, ... B8 2026-01..2026-06.
Compute per-block: trades, WR, W/L, PF, net.
```
**T2 pass gate:**
```
[ ] >= 6 of 8 blocks are >= breakeven (net >= 0)     (65%+ stability)
[ ] No single block contributes > 50% of full-window net
[ ] The pass does NOT depend only on B7+B8 (2025H2-2026H1): at least one of B1..B6 is positive
```
If T2 fails, the "winner" is still a recent-regime artifact — do not promote it.

---

## 4. Test T3 (optional) — RR robustness (run only if a variant passes T1+T2)

Confirm the edge is not fitted to RR=2. Run the T1/T2 winner at **RR 1.5, 2.0, 2.5** (report all three; do NOT pick the best).
```
[ ] Net > 0 and cost-stress PF >= 1.15 at ALL three RR values
```
If the edge only exists at RR=2.0, flag it as RR-fragile (not a hard fail, but a caveat for the watchlist).

---

## 5. Metrics (compute exactly like this for every variant)

```
WR   = wins/(wins+losses)                 [flats excluded]
W/L  = mean(win)/abs(mean(loss))
PF   = sum(win)/abs(sum(loss))
Net  = sum(pnl)
Cost stress = subtract 0.30/trade; recompute Net, W/L, PF
By year: net + PF for 2022..2026
Walk-forward: net + PF for B1..B8
Concentration: net after removing top-1 / top-5 / top-10 trades; best-day share; net ex-top-3-days
Positive weeks (exit-time buckets); worst week
```
**Concentration guard (applies to any candidate before it can advance):**
```
[ ] Net stays > 0 after removing the top-10 trades
[ ] Net stays > 0 after removing the top-3 days
```

---

## 6. Decision tree

```
If a T1 variant passes T1 gate AND T2 walk-forward AND the §5 concentration guard:
    -> V2-<that regime> is a VALIDATED standalone short base.
    -> Next step (separate, reviewer-signed): draft a FORWARD-WATCHLIST spec
       (exact rule + fixed inputs + the gates it must keep hitting forward). Still NO demo.

Else if a variant passes T1 but fails T2 or concentration:
    -> Recent-regime artifact. Keep V2 frozen as reference. Do NOT watchlist.
       Report honestly and stop standalone short iteration for now.

Else (no variant makes 2023-2024 breakeven / >=3 of 4 years positive):
    -> Conclude gold shorts lack a durable STANDALONE edge (a legitimate, valuable result).
    -> Downgrade the short to a COMBINED-PORTFOLIO HEDGE ONLY (per the earlier hedge packet).
    -> Stop iterating the standalone short. Do not force it with post-hoc filters.
```

**Reviewer expectation:** the honest base rate here is that even R3 may not rescue 2023–2024, because gold simply had few clean tradeable downtrends then. A "no durable standalone edge" outcome is an acceptable, high-value conclusion — do not manufacture a pass.

---

## 7. Forbidden (anti-overfit, mandatory)

```
[ ] No hour / month / session / day masking.
[ ] No stacking extra "quality" filters to lift WR (proven to make shorts worse).
[ ] No picking the regime/RR variant by highest net — selection is by the pre-committed gate, tie-break to the SIMPLER definition.
[ ] No promoting/citing the 4-year net without disclosing the 2023-2024 losing period.
[ ] No judging on Q2-2026 / recent-3M alone.
[ ] No trailing / break-even / partial exits to prettify the curve (keep clean SL/TP at fixed RR).
[ ] No mirroring the long H4/D1 box structure.
[ ] No new tunable parameters beyond the single fixed R3 gate defined in §2.
```

---

## 8. Artifacts + commit sequence

**Commit 1 — preregistration + EA input (no runtime):**
- `docs/A1_XAU_SHORT_V2_ROBUSTNESS_PREREG_2026_07_08.md` — R1/R2/R3 exact rules, frozen §1 contract, T1/T2/T3 gates, §6 tree, §7 forbidden. Hash it.
- EA: add the single default-off `InpD1StructuralDownGate*` input for R3. Long branch and all committed presets untouched.

**Commit 2 — exact-MT5 runs:**
- Per variant (R1, R2, R3): `..._trades.csv`, `..._summary.json`, `..._.htm` in the backtest reports dir.
- No-op parity ledger confirming R1 reproduces the committed V2 result (sanity check the harness is unchanged).

**Commit 3 — scoring + verdict:**
- `outputs/reports/A1_XAU_SHORT_V2_ROBUSTNESS_2026_07_08.md/.json` — the by-year table, the B1..B8 walk-forward table, concentration, and the T1/T2/(T3) gate pass/fail per variant.
- Final verdict per §6, with the decision-tree outcome. Status `DIAGNOSTIC_..._NOT_PROMOTED`. No forward-watchlist or demo spec drafted without reviewer sign-off.

---

## 9. Execution order (do exactly this)
1. Write + hash the prereg; add the one R3 EA input (default off). Do not run yet.
2. Run **R1** (parity — must reproduce committed V2), then **R2**, then **R3**. Exact-MT5, full window, §1 contract.
3. Compute §5 metrics + T1 gate for each; pick the winner by the §2 selection rule.
4. If there's a winner: run **T2** walk-forward on it; then **T3** (optional).
5. Apply §6 decision tree. Report ALL variants and every gate result, pass or fail.
6. Stop. Reviewer sign-off before any forward-watchlist or demo step. A3/live/broker state untouched throughout.

**One-line success definition:** a single, simple, preregistered regime definition under which the breakdown-retest short is net-positive in ≥3 of 4 years, makes 2023–2024 at least breakeven, survives cost and top-10-trade removal, and is ≥ breakeven in ≥6 of 8 six-month blocks — proving the edge is structural, not a 2025–2026 accident.
