# WORK ORDER — XAUUSD Short Specialist as a Regime Hedge (exact-MT5)

**For:** Codex
**Date:** 2026-07-07
**Author:** independent reviewer
**Governance:** exact-MT5 Strategy Tester only. No live/demo runtime. No chart/preset/order/position/broker changes. No post-hoc hour/month/session tuning. No parameter grids. Every parameter is fixed and preregistered before running.

---

## 0. Read this first — the goal is a HEDGE, not a twin

The ledgers you already produced settle the strategic question. Do **not** try to build a short branch that mirrors the long branch's WR/PF. It is not achievable on gold and it is not the point.

**Why (from your own exact-MT5 ledgers):**
- Every short variant lands at **WR 27–34%.** That is not a tuning failure — it is gold's structural long bias (safe-haven bid, "up the stairs, down the elevator"). Shorts get squeezed on bounces.
- The **direct mirror of the winning long box** (`down_down_h4_d1_short_box2`) **loses −$994.** The box structure does not invert. Stop mirroring it.
- **Adding "quality" filters made the short worse** (`bq_bear_quality_*` = −$114 to −$145). Over-filtering deletes the rare big winners that create the W/L. Stop stacking filters.
- **Reversal/range-fade (`nonup_*`) is negative in Q2-2026** (−$36 to −$218), the exact quarter you need covered. It does not provide the hedge.
- **The plain momentum-breakdown short IS a valid regime hedge.** `bi_bear_break_run_h1h4_rr2`: quiet in the bull quarters, and **positive (+$182) in Q2-2026 when the long box lost −$1,522.**

**Combined long-box + `bear_break_run` short, by quarter (the evidence):**

| Quarter | Long box | Short | Combined |
|---|---:|---:|---:|
| 2025 Q3 | +5,974 | +45 | +6,020 |
| 2025 Q4 | +1,831 | +52 | +1,883 |
| 2026 Q1 | +4,139 | +33 | +4,172 |
| **2026 Q2** | **−1,522** | **+182** | **−1,340** |

**Conclusion you must build around:** the short is insurance — cheap and near-silent in bull markets, positive in bear phases. Judge it on the COMBINED portfolio and on the down-regime quarters, not on standalone WR. The original WR≥50 / W/L≥2.0 / PF>1.2 targets are **combined-portfolio** targets (the long branch already meets them); the short standalone is judged by the hedge gates in §5.

---

## 1. Fixed execution contract (identical for every variant)

Do not change any of these between variants. Changing them is tuning.

```
Symbol:            XAUUSD
Timeframe:         M5
Direction:         SHORT ONLY
Backtest window:   2022-07-01 -> 2026-06-30   (full window, same as long branch)
Tester model:      Every Tick, real-tick-quality history
Deposit / ccy:     match the long-branch runs (e.g. 1000 USD)
Lot:               0.01 fixed
Reward:Risk (RR):  2.0   (TP distance = 2.0 x SL distance) — fixed for all, to preserve W/L>=2.0
Stop construction: reuse the EXISTING bear source's SL logic unchanged (so results are comparable)
Exits:             SL / TP only. No trailing, no break-even, no partial (keeps the test clean)
Guards:            reuse existing cooldown, daily cap, spread cap, cost cap at their CURRENT settings — do not retune
Session/hour:      24h. No session, hour, day-of-week, or month filter.
```

The only thing that varies across variants is the **entry setup** and its **regime gate**, defined in §3. All are `default-off` EA inputs; the long branch and all committed presets stay untouched.

---

## 2. Reference numbers (freeze these as the baseline to beat / not break)

**Long branch (guarded/supportive baseline) — must not be degraded by adding the short:**
```
Signals 3645 | WR 50.40% | W/L 2.0895 | PF 2.1395 | Net +20,701.41 USD
Active weekdays 85.71% | Stress W/L (-0.30/trade) 1.9720
Profit engine h4_d1_long_best_box2_atr80: 332 tr, WR ~57.5%, PF ~3.09, +15,614 USD
Long-box worst quarter: 2026 Q2 = -1,522 USD  <-- the hole the short must help fill
```

**Best short hedge so far (bar to beat):** `bi_bear_break_run_h1h4_rr2` — full +$208, Q2-2026 +$182, survives −$0.30/trade at +$74, W/L 2.35, PF 1.11, WR 32.1%.

---

## 3. The preregistered variants (V1–V3 mandatory, V4 optional)

Each is ONE fixed configuration. Do not sweep. Reuse the existing exact triggers where noted; only the entry structure and regime gate change.

### V1 — D1-down-gated momentum breakdown  *(direct inverse of the long supportive guard)*
- **Base trigger:** the existing `bear_break_run_h1h4` momentum-breakdown short trigger, unchanged (M5 break-and-run down with H1 EMA20<EMA50 and H4 EMA20<EMA50).
- **New regime gate (the only addition):** enter only when
  ```
  D1 close[1] <  D1 EMA20[1]      AND
  D1 EMA20[1] <= D1 EMA20[6]      (EMA20 not rising over 5 completed D1 bars)
  ```
  This is the exact mirror of the long supportive guard (which required `close>EMA20 AND EMA20 rising`). Same EMA period (20) and slope lag (5). Completed bars only — no look-ahead.
- **SL/TP:** existing stop, TP = 2.0×SL.
- **Hypothesis:** concentrating the working momentum short into confirmed D1 downtrends raises WR/PF and cost-robustness, the same way the guard repaired the long box. This is the highest-probability improvement because it is the proven mechanism applied symmetrically.

### V2 — Breakdown-retest short  *(mirror the proven long breakout-retest family — NOT the box)*
- **Structure:** run the existing breakout-retest engine in **support-breakdown/short** mode:
  1. Identify a support level using the same level logic the long engine uses for resistance (prior swing low / session low / normalized round level).
  2. **Break:** an M5 close below the level.
  3. **Retest:** price returns up to the broken level (now resistance) within **K=10 M5 bars** without an M5 close back above `level + buffer` (buffer = existing engine's buffer, unchanged).
  4. **Entry:** short on a bearish confirmation candle at the retest (reuse the long engine's confirmation-candle definition, inverted).
- **Regime gate:** require `H1 EMA20 < H1 EMA50 AND H4 EMA20 < H4 EMA50` at signal bar (down alignment). Fixed.
- **SL:** above the retest swing high + existing buffer. **TP:** 2.0×SL.
- **Hypothesis:** the retest confirmation raises WR over a raw breakdown without the over-filtering that killed the quality variants, and it is structurally symmetric to a long concept you already trust.

### V3 — Liquidity-sweep-reclaim short  *(exhaustion reversal — the structurally different setup)*
- **Structure:**
  1. `prior_high` = high of the previous completed calendar day (server time).
  2. **Sweep:** current session prints a high **> prior_high**.
  3. **Reclaim:** an M5 bar **closes back below prior_high** on the same or next M5 bar after the sweep.
  4. **Entry:** short at that reclaim close.
- **Regime gate:** allow only when `D1 close[1] <= D1 EMA20[1]` (D1 non-up). Fixed.
- **SL:** above the sweep high + existing buffer (this is the 1R). **TP:** 2.0×SL.
- **Hypothesis:** this targets gold's false-breakout-up-then-drop exhaustion, a setup none of the momentum/box variants captured, and it should be the least correlated with the long box.

### V4 (optional) — H4 lower-high / resistance rejection
- In `D1 close[1] <= D1 EMA20[1]` regime, when price tags a prior H4 swing high (or H4 EMA20 from below) and prints a bearish rejection candle (close in lower third of range, upper wick ≥ 50% of range), short. SL above the high (1R), TP 2.0×SL. Run only if V1–V3 leave time; lower priority (pure reversal was negative in Q2, so it needs a real level).

---

## 4. Metrics — compute exactly like this (so results are comparable and honest)

For each variant's raw MT5 ledger:
```
trade      = one closed position package; pnl in the ledger currency (report USD; keep AED column if present)
WR         = wins / (wins + losses)                         [flats excluded]
W/L        = mean(win pnl) / abs(mean(loss pnl))
PF         = sum(win pnl) / abs(sum(loss pnl))
Net        = sum(pnl)
Cost stress= subtract 0.30 per trade (per ticket if multi-leg); recompute Net, W/L, PF
Positive weeks = resample by EXIT time to broker weeks; share of non-zero weeks with net>0
Activity   = share of trading weekdays in the window with >=1 trade
Regime cuts= report Net for: full window, calendar year 2025 (bull), and each quarter 2025Q3..2026Q2
Worst week = min weekly net (exit-time buckets)
Concentration = share of net from top-1 and top-5 trades; largest single-day net share
```
Also produce the **combined** long-box + short ledgers (union of trades) and compute the same metrics on the union, plus the by-quarter table.

---

## 5. Gates

### 5a. Standalone short gate (reframed — WR≥50 is dropped)
A short variant is a **viable hedge** if ALL hold:
```
[ ] PF after -0.30/trade  >= 1.15
[ ] W/L raw >= 2.0   AND   W/L after -0.30/trade >= 1.90
[ ] Net after -0.30/trade > 0
[ ] Net in 2026 Q2 (long-box failure quarter) > 0
[ ] No single trade > 25% of net; no single day > 30% of net
[ ] >= ~200 trades over the window (>= ~1/week frequency)
```

### 5b. Combined long+short gate (the real success bar)
Combine the guarded long box with the short variant, then require ALL:
```
[ ] Combined WR >= 48%                          (not materially below long-alone 50.40%)
[ ] Combined W/L >= 2.00 raw  AND  >= 1.90 after -0.30/trade
[ ] Combined PF > 1.5
[ ] Worst quarter loss reduced >= 30% vs long-alone   (2026 Q2: -1,522 -> >= -1,065; target near breakeven)
[ ] Positive-week% improves by >= +2 pts vs long-alone, and worst week is not worse
[ ] Combined active weekdays >= long-alone active weekdays
[ ] Bull-quarter erosion small: combined 2025Q3+2025Q4+2026Q1 net >= 0.95 x long-alone over the same quarters
[ ] Regime anti-correlation: short quarterly net is >0 in >=1 quarter where long-box quarterly net is <0, and short does not drag any bull quarter negative
```

---

## 6. Decision tree (what to conclude)

```
If a variant passes BOTH 5a and 5b:
    -> Adopt long+short as the new frontier. Freeze it (hash the prereg + inputs).
    -> Next step: owner-approved SMALL frozen forward DEMO (exact-MT5 -> demo), long+short, 0.01 lot.

Else if a variant passes 5b but not 5a:
    -> Adopt it as a hedge OVERLAY only (it helps the portfolio but is not a standalone strategy);
       run it at reduced size; flag clearly it is not a standalone short specialist.

Else (no variant reduces the worst quarter by >= 30%):
    -> Conclude gold shorts are a WEAK hedge (expected). STOP tuning shorts. Pivot to ONE of:
       (a) long-only with explicitly relaxed weekly/activity targets (positive-weeks ~60-65%), OR
       (b) regime-SIZE the long box: cut long-box lot/exposure when D1 is non-up
           (test as a separate preregistered exact-MT5 probe) — this likely protects red quarters
           more reliably than any short can.
```

Expectation check for you: even the best hedge so far offsets only **+$182 of the −$1,522** Q2 hole (~12%). A pass on the 5b "≥30% worst-quarter reduction" gate is a real, non-trivial bar. If V1 (the regime-gated momentum short) can push the Q2 short contribution from +$182 toward +$450–$500 by trading only in confirmed downtrends, it can clear it. If it can't, that is a legitimate, valuable finding — do not force it with post-hoc filters.

---

## 7. Anti-overfit guardrails (mandatory)

```
[ ] All params fixed and written in the prereg doc BEFORE running. Hash the prereg.
[ ] No hour / month / session / day-of-week filter on any variant.
[ ] No stacking of extra "quality" filters (proven to make shorts worse).
[ ] Do NOT mirror the H4/D1 box structure (proven -994).
[ ] One fixed configuration per variant. No grid, no argmax-over-many.
[ ] Report EVERY variant you run (including failures). The winner is decided by the gates in §5,
    not by picking the best net after the fact.
[ ] Cost stress is mandatory for every claim (thin short edges die to cost).
[ ] Judge on COMBINED + regime, never on standalone net.
[ ] Keep a no-op parity ledger proving the long-box reference is byte-identical/unchanged.
```

---

## 8. Artifacts to produce (per commit)

**Commit 1 — preregistration + EA inputs (no runtime):**
- `docs/A1_XAU_SHORT_HEDGE_PREREG_2026_07_07.md` — the exact V1–V4 rules, fixed params, §1 contract, §5 gates, §6 tree. Hash it.
- EA: add the three short setups as `default-off` inputs (short-only), plus the D1-down/ non-up regime gate input. Committed defaults stay off; long branch untouched.

**Commit 2 — exact-MT5 runs:**
- Per variant: `..._trades.csv`, `..._summary.json`, `..._<variant>.htm` under `outputs/reports/mt5_backtests/...`.
- `..._RESULTS.csv` — one row per variant with all §4 metrics + 5a pass/fail.
- No-op parity ledger for the long box.

**Commit 3 — combined scoring + verdict:**
- `outputs/reports/A1_XAU_SHORT_HEDGE_COMBINED_2026_07_07.md/.json` — the combined long+short metrics, the by-quarter table, and the 5b gate table (pass/fail per variant).
- Final verdict per §6, with the decision-tree outcome and the recommended next step. Status `DIAGNOSTIC_..._NOT_PROMOTED` until reviewer sign-off. No demo spec drafted without review.

---

## 9. Execution order (do exactly this)
1. Write + hash the prereg (Commit 1). Add default-off EA inputs. Do not run yet.
2. Run **V1** first (highest-probability). Then **V2**, then **V3**. (V4 only if time.) Exact-MT5, full window, §1 contract.
3. Compute §4 metrics + 5a for each; build the combined ledgers + 5b table (Commit 2–3).
4. Apply §6 decision tree. Report all variants, pass/fail by gate, and the outcome.
5. Stop. Reviewer sign-off before any forward-demo step. A3/live/broker state stays untouched throughout.

**One-line success definition:** a short variant that is near-silent in the 2025-Q3→2026-Q1 bull quarters and turns the 2026-Q2 combined result from −$1,522 toward breakeven, without dropping combined WR below ~48% or W/L below ~2.0 after cost.
```
