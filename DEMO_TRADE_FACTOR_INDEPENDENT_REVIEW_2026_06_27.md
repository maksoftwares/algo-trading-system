# Independent Review & Challenge — Codex Demo Trade Factor Analysis

**Reviewer:** independent (offline only; no MT5 runtime, EA, preset, chart, order, or position touched)
**Codex report reviewed:** `DEMO_TRADE_FACTOR_COMMONALITY_2026_06_27.md` (+ json/csv)
**Money-truth sources I recomputed from scratch:** `PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv` (legacy, 2,059 fills) and the fresh C02 per-account `deals.csv` (A1/A2/A3, reconstructed to 1,429 closed XAU trades).
**Verdict:** **REVISE.** Codex's arithmetic is correct and its evidence labels are mostly honest — but the conclusions overstate a result that is one-day, one-account, outlier- and direction-dependent.

---

## 1. Executive summary (plain English)

Codex's numbers check out to the decimal — I reproduced every headline independently. The problem is what they *mean*.

The "fresh XAUUSD is now positive (+642.58 AED, PF 1.02)" headline is **not evidence of an edge**. It is:
- **92% one account** — A1 (1,320 of 1,429 trades, +1,405 AED), which runs the **920101 evening-core strategy, not the breakout_retest family the ML program targets.** The actual breakout demo, **A3, is −803 AED at PF 0.53**.
- **Essentially one day** — remove **June 10** and the whole book goes from **+643 to −1,428** (June 10 alone made ≈ +2,071, driven by shorts on a big down-move).
- **Outlier-dependent** — removing the **top 5 winning trades** flips +643 to **−61**; the top 5 gross (704) exceeds the entire net.
- **Decaying** — first chronological half **+2,442**, second half **−1,799** (PF 1.19 → 0.86).
- **Direction-skewed** — SELL +2,000 vs BUY −1,358.

The "winning signals show stronger trend alignment" factor story is real *in the diagnostic data* but is computed on **633 rows that are 100% `label_status = OPTIMISTIC_DIAGNOSTIC_ONLY`**, with **141 `DATA_UNRESOLVED` rows counted as losses**, and is **never joined to broker fills**. On actual money (my prior bar-joined analysis of 712 XAU fills) the same trend edge is roughly half as strong. So the factors are a research hypothesis, not proof.

Bottom line: there is **no robust realized edge yet**. The single genuinely repeatable-looking slice (with-trend, Dubai-evening, A1) is fragile and belongs in a forward test, not a deployment.

---

## 2. Verification of Codex's numbers — all reproduce

| Codex claim | Codex value | My independent value | Match |
|---|---|---|---|
| Legacy all-symbol, duplicate-hidden | −3,141.76 / 1,298 / 34.2% / PF 0.82 | −3,141.8 / 1,298 / 34.2% / PF 0.82 | ✅ exact |
| Legacy raw all-symbol | −2,966.81 / 2,059 / 35.9% / PF 0.90 | −2,966.8 / 2,059 / 35.9% / PF 0.90 | ✅ exact |
| Fresh XAU all-account | +642.58 / 1,429 / 38.9% / PF 1.02 | +643 / 1,429 / 38.9% / PF 1.02 | ✅ exact |
| Fresh XAU evening (Dubai 16–20) | +2,750.22 / 413 / 45.5% / PF 1.33 | +2,750 / 413 / 45.5% / PF 1.33 | ✅ exact |
| Morning & afternoon negative | yes | Morning −806, Afternoon −1,080 | ✅ |
| A1 positive, A3 strongly negative | A1 +1,405, A3 −803 (PF 0.53) | identical | ✅ |
| Round-family / weak lanes = drag | yes | symbol_normalized_round_retest −2,115 (legacy); A3 plain −510, improved −156 | ✅ |
| Winning signals: stronger D1/H1 trend, EMA-distance, ATR pct, break dist | yes | d1 d=0.42, h1_slope d=0.26, h1_dist d=0.25, atr_pct d=0.24, break d=0.20 | ✅ on diagnostic labels |

**Codex did not fabricate or miscompute anything.** I also confirm a tz subtlety in my own first pass: deal `time` is epoch‑UTC; Dubai = UTC+4, so Codex's "EVENING 16:00–19:59" is correctly the profitable window.

---

## 3. Disagreements / corrections (interpretation, not arithmetic)

1. **"Fresh XAU positive" ≠ progress on the breakout thesis.** It is A1's evening-core strategy. The breakout_retest demo (A3) remains a clear loser (PF 0.53). Reporting a combined "+642 XAU" invites the wrong read.
2. **Codex did not single-day / outlier stress-test.** The entire positive result is June 10 + a handful of trades (see §5). This is the single most important omission.
3. **A1 vs A3 are different *strategies*, not a clean account comparison.** A1=1,320 trades (920101 evening), A3=84 (breakout), A2=25. A2/A3 samples are too small for any conclusion; "A1 beats A3" is apples-to-oranges.
4. **The factor table is on `OPTIMISTIC_DIAGNOSTIC_ONLY` virtual labels with unresolved-as-loss.** Codex labels it "diagnostic," which is fair, but the strength (d up to 0.42) is inflated relative to realized money (~0.13 on fills) and should not be cited as a deployable separator.
5. **Legacy vs fresh are different populations** (all-symbol vs XAU-only; pre- vs through-June‑26; phase2 magics vs A1/A2/A3 logins). You cannot read −942 (legacy XAU) → +643 (fresh XAU) as an "improvement."
6. **Duplicates are not neutral.** Removing them makes the legacy book *worse* (dups were net +175, PF 1.01), so the dedup −3,141.76 is the honest figure — but the dup flag clearly isn't random.

---

## 4. Winner / loser factor tables

### Money-truth: top/worst slices (concrete tables)

**Legacy dedup by symbol** (all negative; FX is the real drag):

| Symbol | Trades | WR | PnL | PF |
|---|---|---|---|---|
| XAUUSD | 712 | 37.4% | −942 | 0.92 |
| EURUSD | 296 | 34.5% | −828 | 0.63 |
| GBPUSD | 229 | 24.9% | **−1,304** | **0.48 (worst)** |
| BTCUSD | 40 | 33.3% | −43 | 0.71 |
| USDJPY | 21 | 20.0% | −25 | 0.45 |

**Legacy dedup by EA/candidate** (only one positive):

| Candidate | Trades | WR | PnL | PF |
|---|---|---|---|---|
| round_number_retest_v0 | 40 | 42.5% | **+17** | 1.04 |
| breakout_retest | 401 | 36.6% | −357 | 0.91 |
| session_extreme_retest_v0 | 142 | 33.1% | −184 | 0.85 |
| swing_breakout_retest_v0 | 92 | 21.6% | −358 | 0.51 |
| symbol_normalized_round_retest_v0 | 605 | 34.6% | **−2,116 (worst)** | 0.79 |

**Fresh XAU by session (Dubai)** and **by account**:

| Session | Trades | WR | PnL | PF |  | Account | Trades | WR | PnL | PF |
|---|---|---|---|---|---|---|---|---|---|---|
| Evening 16–20 | 413 | 45.5% | **+2,750** | 1.33 |  | A1 (920101 evening) | 1,320 | 39.6% | **+1,405** | 1.06 |
| Night 20–6 | 528 | 40.2% | −221 | 0.98 |  | A2 (tier1) | 25 | 36.0% | +40 | 1.08 |
| Morning 6–12 | 304 | 33.9% | −806 | 0.82 |  | A3 (breakout) | 84 | 28.6% | **−803** | 0.53 |
| Afternoon 12–16 | 184 | 28.8% | **−1,080** | 0.65 |  |  |  |  |  |  |

### Diagnostic (virtual `OPTIMISTIC_DIAGNOSTIC_ONLY` labels, 633 signals — NOT money)

Winner vs loser feature means (Cohen's d), reproduced from the C01 snapshot:

| Feature | Win mean | Loss mean | d |
|---|---|---|---|
| d1_trend_score_aligned | 0.330 | 0.085 | **0.42** |
| h1_ema20_slope_aligned_atr | 0.222 | 0.117 | 0.26 |
| price_h1_ema20_distance_aligned_atr | 0.936 | 0.627 | 0.25 |
| m5_atr_percentile_trailing_20d | 0.562 | 0.496 | 0.24 |
| break_distance_atr | 0.651 | 0.556 | 0.20 |
| m15_ema20_slope_aligned_atr | 0.132 | 0.159 | −0.08 |
| confirmation_body_ratio / close_loc | ~equal | ~equal | ~0 |

Direction of the story (winners = more trend-aligned, higher ATR percentile, larger break) is correct — but on optimistic virtual labels with 141 unresolved rows lumped into losses, so treat as hypothesis-grade. **Codex's "best one-factor thresholds" (e.g. h1_slope ≥ 0.457 → 48% WR) are in-sample best cuts scanned over many features/thresholds on these labels — textbook curve-fit risk, no out-of-sample.**

---

## 5. Robustness checks (the decisive section)

| Test | Result | Read |
|---|---|---|
| Remove top 1 / 3 / 5 winners | +500 / +215 / **−61** | net edge gone after 5 trades |
| Top 5 / top 10 winners gross | +704 / +1,390 | exceed the +643 net |
| **Remove June 10** | **+643 → −1,428** | one day *is* the result |
| June 10 alone | +2,071 (209 tr, shorts +3,357 / longs −1,286) | one trend-down day, shorts |
| Single best day | ≈ +2,300 vs +643 net | net < one day |
| Chrono 1st half / 2nd half | +2,442 / **−1,799** | edge decays/reverses |
| By week | wk23 +321, wk24 +1,201, wk25 **−1,003**, wk26 +124 | wobbling around zero |
| Evening ex‑June 10 | +2,750 → **+588** (PF 1.08) | 78% of evening profit = June 10 |
| Evening by account | A1 +2,864 / A2 +40 / **A3 −154** | evening edge is A1 only |
| Evening by week | +597 / +1,567 / +391 / +196 | *this* slice is positive all 4 weeks |
| Longs vs shorts (book) | BUY −1,358 / SELL +2,000 | shorts carried it |

The **one** finding that partially survives: the **Dubai-evening window is positive in every week and still +588 without June 10** — but it is entirely A1 and still 78% one day. Everything else (the overall +643, A1's edge, the second half) collapses under a single-day or top-5-trade removal.

---

## 6. Evidence-level discipline (as requested)

- **Money truth (real broker fills):** legacy `PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv` and fresh per-account `deals.csv` (profit + commission + swap + fee; I required a closing OUT deal, so no open trades counted — 1,429 IN/OUT pairs reconcile exactly).
- **Diagnostic only (do NOT treat as money):** the 633 C01 snapshot rows (virtual `y_net_R`, `OPTIMISTIC_DIAGNOSTIC_ONLY`, expected R == stress R because slippage is INSUFFICIENT) and any signal/observer/replay label. **These are not joined to broker fills.** Codex's factor table lives entirely here.

## 7. Data-quality issues found

- **Account labels:** present only in the *fresh* data. The *legacy* file has **no login column** — it cannot be split by A1/A2/A3 (Codex correctly didn't try).
- **Sessions:** Dubai = broker server = UTC+4; deal `time` is epoch‑UTC and must be shifted +4. Get this wrong and "evening" moves a whole bucket (I hit this myself; corrected).
- **Duplicates:** the dup flag is reliable enough but non-random (dups skew positive); use the dedup figures.
- **Open trades:** not contaminating — only closed positions counted.
- **Profit:** fresh and legacy are realized broker PnL; the C01 R is modeled/optimistic.
- **A1/A2/A3 comparability:** poor — different strategies and 1,320 vs 25 vs 84 trades.
- **Fresh-vs-legacy:** different symbol scope, window, and accounts; must not be chained as "improvement."

---

## 8. Verdict

- **Agree with Codex's numbers?** Yes — every figure reproduces.
- **What Codex missed:** single-day dependence (June 10 = the whole result), top-5-trade fragility, chronological decay (2nd half −1,799), and that A1≠breakout strategy.
- **What Codex overstated:** the fresh XAU result as encouraging, and the diagnostic factor separators as if they predict realized money.
- **Most likely real reason trades win:** catching a **strong directional/trend day** (e.g., June 10's down-move) **with the trend**, in the evening window — trend-continuation on a few high-momentum days, consistent with the D1/H1-alignment separator.
- **Most likely real reason trades lose:** most days are choppy/mean-reverting, where breakout-retest entries get **stopped out fast**; counter-trend, low-trend, morning/afternoon, FX symbols, and the round-retest variants bleed steadily, and a couple of trend days mask the bleed.
- **Forward-test next:** the with-trend evening slice (below), shadow-only.
- **Do NOT deploy anything.** A3 breakout is PF 0.53; the "positive" book is one day. No runtime change.

**FINAL VERDICT: REVISE** — endorse the measurements, reject the optimistic conclusion. Reframe as "no robust realized edge yet; one fragile, post-hoc slice worth forward-testing."

---

## 9. Recommended locked forward-test hypothesis (not a runtime change)

> **H1 — With-trend evening filter (shadow/forward only).** On XAUUSD `breakout_retest` would-signals, mark TAKE only when **`d1_trend_score_aligned ≥ 0.25` AND `h1_ema20_slope_aligned_atr ≥ 0.35`** (direction with the higher-timeframe trend) **and** the Dubai-time entry is in **16:00–19:59**; mark SKIP otherwise.

- **Why it should help:** the only money-positive slice is with-trend + evening; the strongest diagnostic separators are D1/H1 trend alignment; realized wins concentrate on trending days.
- **Supporting data:** evening +2,750 (PF 1.33; positive all 4 weeks; +588 even ex-June 10); d1 d=0.42 / h1_slope d=0.26 on diagnostic labels; with-trend > counter-trend on real fills.
- **What would falsify it:** forward evening + trend-aligned trades show **WR < 40% or PF < 1.10**, **or** > 50% of net profit comes from any single day, **or** the edge appears only on A1.
- **Minimum sample:** ≥ 150 forward trend-aligned evening trades, ≥ 6 distinct weeks, ≥ 4 distinct profitable days (no single day > 35% of net), both directions present, and it must hold on **A3 (breakout)**, not just A1.
- **Kill condition:** rolling 50-trade PF < 0.9, or any single day > 50% of cumulative net, or second-half PF more than 0.3 below first-half.
- **Overfitting risk: HIGH.** The slice was chosen *after* seeing the data, it's one account running a different strategy, 78% of the evening profit is one day, and the thresholds are in-sample best cuts. Treat strictly as an out-of-sample forward test; a backtest "confirmation" on this same data proves nothing.
