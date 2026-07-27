# Adversarial review brief — GOLD V8 (XAUUSD trading system)

## Your role

You are an independent quantitative reviewer. Your job is **not** to confirm that
this works — it is to find the reasons it does not. Assume the author is
competent, motivated to believe their own result, and has already fooled
themselves at least twice (documented below). Treat every headline number as a
hypothesis to be broken.

The author has no stake in the system being validated. **A well-evidenced
"this is broken" is a more valuable deliverable than "looks good."**

Read `REGIME_SPECIALIST_FAMILY_V7.md`, `PREREGISTRATION_MULTI_INSTRUMENT.md`, and
`outputs/GOLD_V8_SPEC.json` first — they contain the campaign's own record of
what was tested and rejected.

---

## 1. What the system is

**GOLD V8** trades XAUUSD on 5-minute bars. Twelve specialists = 3 holding
horizons (12h / 36h / 72h) × 4 entry gates, each trading both directions.

Mechanics:
- **Direction selector**: a weekly EMA slope (span 2016 bars, 1-day change, in
  ATR units, shifted). Slope ≥ 0 → long only; slope < 0 → short only.
- **Entry**: *confirmation*. At a decision bar, wait for price to move 0.5 × stop
  in the selected direction, then enter at the next bar's open.
- **Entry gates**: `None` (trend), or a prior-2h move threshold of 0.5 / 1.0 /
  1.5 ATR *against* the trade direction (buy after a drop, sell after a pop).
- **Stop**: 6.75 × ATR144. **Exit**: stop, or the horizon close. No targets, no
  trailing, no partials (partials were tested and rejected — see §5).
- **Ranker**: ridge regression, 8 features (`speed, flow, imb, activity, spr,
  eff, adv_pre, align`), fit per sleeve on trades **closing** on or before
  2024-12-31. Selection threshold is a *rolling* quantile of the trailing 400
  candidate scores.
- **Portfolio**: dedup to one position per decision bar (highest ranker score
  wins), then a shared K-slot lockout (K=6), then streak sizing (half after 2
  consecutive losers, quarter after 4, reset on any win).
- **Sizing**: target $10 risk/trade in 0.01-lot units; trades with stop > $30 are
  refused.

Data: Dukascopy M5 bid/ask (signal) 2016-07 → 2026-06; Capital.com M5 (execution)
→ 2026-07.

---

## 2. The claims you are asked to break

All figures are on the Capital.com execution feed at 0.01-lot sizing with the $30
stop cap, unless noted.

| Claim | Value | Where produced |
|---|---|---|
| Full history | 5,572 trades, WR 31.0%, PF 1.79, +$10,770, maxDD $1,167 | `v8_lot_constrained.py`, dashboard |
| 5 years | PF 1.93, +$6,965, maxDD $700 | same |
| Sealed 18 months (never fitted) | PF 2.82, +$4,151, 12/18 green | `v8_lot_constrained.py` |
| **Causal walk-forward 2019-26** | **PF 2.03**, +$12,579, 7/8 years profitable | `gold_v8_walkforward.py` |
| Walk-forward, sleeves also chosen causally | PF 2.04 | ad-hoc, 28-sleeve pool |
| Dual-feed retention | Capital retains 102% of Dukascopy PF | `v8_dualfeed.py` |
| Worst single trade | −$30.13 | `v8_drawdown.py` |
| Worst drawdown | $1,169 over 483 days, worst trade inside it −$11 | `v8_drawdown.py` |
| Green months | 40/60 over 5 years (67%) | `v8_weakness.py` |

---

## 3. PRIORITY 1 — the specific bug the author suspects and could not clear

**Streak-sizing look-ahead.** In `src/gold_v9_partial.py::assemble()`:

```python
a = a.loc[keep].sort_values("exit_t").reset_index(drop=True)
size, st = np.ones(len(a)), 0
for k, r in enumerate(a.r.values):
    size[k] = 0.25 if st >= quart else (0.5 if st >= half else 1.0)
    st = 0 if r > 0 else st + 1
```

Position size is assigned walking trades in **exit** order, but size must be
known at **entry**. Average hold is ~25h with up to 6 concurrent positions, so a
trade's multiplier can be derived from trades that closed *after* that trade
opened — i.e. from information not yet available.

- Is this a genuine look-ahead? Quantify it: how many of the 5,572 trades receive
  a multiplier that depends on a trade closing after their own entry?
- Re-derive `size` strictly in **entry** order, settling only trades whose
  `exit_t <= entry_t` of the trade being sized, and re-report every metric in §2.
- `src/v8_drawdown.py::simulate()` attempts the correct entry-order walk — but it
  consumes the pre-computed `size` column rather than re-deriving it, so it is
  **not** an independent check. Confirm or refute this reading.
- If the effect is material, which claims survive? Streak sizing is credited with
  turning Feb 2026 from −$1,743 to −$528 and lifting green months ~11pp.

**This single item may invalidate the drawdown and green-month figures. Do it
first.**

---

## 4. PRIORITY 2 — leakage and causality audit

Check each of these and state PASS / FAIL / UNCLEAR with evidence:

1. **Ranker fit boundary.** `gold_v8.py::candidates()` fits on
   `c.exit_t <= FIT_END`. Is *exit* the right boundary (a trade's label is
   unknown until it closes)? Does any trade opening before and closing after the
   boundary leak?
2. **Feature standardisation.** `mu`, `sd` come from the fit subset and are
   applied to all rows. Correct, or does the fit subset itself depend on
   post-boundary information?
3. **Rolling threshold.** `regime_frontier5.py::rolling_thr()` was vectorised
   with `sliding_window_view`. Verify row *p* sees exactly `scores[max(0,p-W):p]`
   — never itself, never later. A prior test claimed exact equality with the
   naive loop; reproduce it.
4. **Deduplication.** Dedup keeps the highest-scoring sleeve per decision bar.
   Scores come from a ranker fit through 2024. For pre-2025 trades this is
   in-sample — does dedup therefore use hindsight to pick the winner?
5. **Direction selector.** Confirm `slope` is properly shifted and uses no
   same-bar information (`specialist.load_context()`).
6. **ATR / stop.** The stop is 6.75 × ATR144 from the *Dukascopy* feed, then
   applied to *Capital* execution in `v8_dualfeed.py`. Is that legitimate, or
   should the Capital leg compute its own ATR? How much does it matter?
7. **Walk-forward integrity.** In `gold_v8_walkforward.py`, verify that for
   evaluation year Y nothing from Y or later touches: ranker weights, threshold,
   K, streak parameters, or sleeve inclusion.
8. **Warm-up.** `i < 2016` is skipped. Sufficient for a 2016-bar EMA and a
   144-bar ATR?

---

## 5. Known defects already found — look for more of the same species

The author found and fixed these. **Each produced a convincing but wrong result.
Assume more of the same kind exist.**

1. **Duplicate-index inflation.** `pd.concat(parts)` without `reset_index`, then
   `.loc[keep]`, multiplied rows ~6× and inflated an entire family's totals
   (+$21,121 → true +$2,995). **Grep every `concat` + `.loc` / `groupby` pattern
   in `src/` for recurrences.**
2. **Gold-denominated commission.** `engine.FEE = 0.30` is in gold dollars;
   applied unscaled to EURUSD (price 1.10, stop 0.00235) it charged ~444R per
   trade and produced a false negative. Caught only because meanR of −87 is below
   the −1R floor. **Check every cost/unit constant for dimensional correctness.**
3. **Feature handicap.** Gold ranked on 8 features, FX on 5, then the author
   concluded the mechanism was gold-specific. Control: gold on 5 features scores
   PF 1.10 vs 1.89 — the comparison was rigged by construction.
4. **PF computed on unsized returns while dollars included sizing** — produced
   the impossible "PF 0.89, +$1,259". **Verify every reported PF/WR is computed
   on the same series as the reported dollars.**
5. **Fixed dev-era percentile ≠ fixed selectivity.** A "top 5%" gate admitted
   24.6% of holdout candidates after feature drift, faking an alpha decay from
   PF 2.18 to 1.14. The rolling threshold was the fix.
6. **Circular gate.** A standdown rule that selected on prior-window PF *and*
   gated on prior-window PF never bound once the candidate pool was large. Its
   claimed +0.33 PF was an artifact.

---

## 6. PRIORITY 3 — overfitting assessment

The author self-rates overfitting **3/10** and asks you to challenge that number.

Measured selection-leak ladder on this data:

| System | In-sample PF | Causal PF |
|---|---|---|
| Regime-split family (rejected) | 1.99 | **0.82** |
| V6 (currently deployed) | 1.73 | 1.42 |
| **V8** | 2.28 | **2.03** |

Known residual contamination, by the author's own account:
- **The $30 stop cap** — chosen by reading a drawdown table, **zero** out-of-sample
  support. Author flags this as the single weakest parameter (self-rated 8/10).
- **Entry gates inherited from V6**, which was itself tuned — unwindable without
  a rebuild.
- **Bidirectional entry** was motivated by observing June 2026 fail for V6.
- **~30 experiments this session**; V8 is the survivor of that search.
- **April/May/June 2026 were inspected across a dozen tests** and no longer carry
  full evidential weight.

Questions:
1. Is the walk-forward genuinely causal, or does the *grid* offered to it
   (K ∈ {4,6,8}, streak ∈ {(2,4),(1,3),(3,5)}) encode hindsight?
2. What is the effective number of hypotheses tested across the session, and what
   multiple-comparisons correction should be applied to PF 2.03?
3. Estimate honest forward PF. The author says 1.7–1.8. Defend or attack that.
4. The horizon set (12/36/72h) was chosen after comparing five configurations. A
   causal chooser from a 28-sleeve pool reached the same PF (2.04) but only 52%
   green months vs the author's 64%. Is the green-month claim therefore
   contaminated? By how much?

---

## 7. PRIORITY 4 — execution realism

1. **Costs.** `FEE = 0.30` per trade plus the bid/ask spread (ask-fill /
   bid-exit). Is $0.30 realistic for Capital.com XAUUSD across 2016–2026? Check
   against the actual `tick_spread_mean` distribution. Median stop is ~$7 —
   what does the true cost do to a PF of 1.79?
2. **Slippage.** None is modelled beyond the spread. The system enters *after* a
   0.5×stop move — i.e. into momentum. Estimate realistic slippage there and
   re-run. Note 358 trades (6%) produce 143% of all profit; if slippage clips the
   tail specifically, the edge dies.
3. **Stop-fill assumption.** Stops are assumed filled exactly at the stop level.
   Gold gaps. What does gap-through do, especially over weekends?
4. **Horizon in bars vs wall-clock.** 864 bars = "72h", but big winners show a
   median 84h and 90th-percentile 127h wall-clock hold — because bars span
   weekend gaps. Does any exit straddle a closed market?
5. **Hedging vs netting.** V8 holds opposing positions simultaneously in 46
   distinct episodes. On a netting account these offset and the whole backtest is
   invalid. Confirm the requirement and its consequence.
6. **Sizing feasibility.** At $10 target risk, 29.8% of trades are forced to
   over-risk (minimum lot too large) and the streak rule is representable on only
   3.2%. Does the strategy still work when sizing is *actually* executable?
7. **Margin** for 6 simultaneous XAUUSD positions on a small account.

---

## 8. PRIORITY 5 — statistical robustness

1. **Significance.** 5,572 trades, mean +0.27R, heavily right-skewed. Bootstrap
   the PF confidence interval. Is PF 1.79 distinguishable from 1.0 given the
   skew and the serial correlation of overlapping positions?
2. **Tail dependence.** Top 5% of trades = 45% of gross profit; the single best
   is +27.3R. Remove the top 1% / 5% — what survives?
3. **Effective sample size.** Up to 6 concurrent correlated positions. What is
   the effective independent N, and how does that change every confidence
   interval?
4. **Regime dependence.** 2019–2021 returned +$1,009 with a $930 drawdown (ratio
   1.1) while other eras run 5.5–6.5. Is the edge conditional on something not
   modelled?
5. **Green months.** Claimed 40/60. Is that statistically distinguishable from a
   coin flip given monthly volatility?

---

## 9. Things the author claims are *structural*, not fixable — verify or refute

The author asserts these are properties of the edge, having tested 5 entry
filters, 9 exit geometries, 5 horizon configurations and 7 decorrelation configs:

1. A month is green **iff** a ≥3R trade lands in it (97% vs 21%).
2. Red and green months have **identical** gross losses (16.8R) and identical
   worst trades (−1.0R) — the downside is already optimal.
3. Green months are pinned at 63–67% under every configuration.
4. Forcing trade independence (spacing, per-direction caps) **destroys** both
   profit and consistency — the correlation *is* the mechanism.
5. The worst drawdown is a 16-month grind at 24% win rate, worst trade inside it
   −$11, so no position-level risk control can address it.

Are these genuine structural limits, or artifacts of a search that never left a
local optimum?

---

## 10. Files

```
src/gold_v8.py                 V8 sleeve construction, ranker, selection
src/gold_v8_walkforward.py     causal walk-forward (the key validation)
src/gold_v9_partial.py         assemble() — streak sizing, see §3
src/v8_dualfeed.py             Capital execution leg
src/v8_lot_constrained.py      realistic 0.01-lot sizing
src/v8_weakness.py             red-month forensic
src/v8_drawdown.py             open-risk cap + drawdown throttle tests
src/regime_frontier5.py        rolling_thr() — the causal threshold
src/specialist.py, src/engine.py   base mechanics, feature definitions
outputs/GOLD_V8_SPEC.json      spec + rejected components
outputs/GOLD_V8_DUALFEED_TRADES.csv   both-feed trade record
REGIME_SPECIALIST_FAMILY_V7.md        campaign history, negative results
PREREGISTRATION_MULTI_INSTRUMENT.md   preregistration + amendments
```

Environment: `xau-usd/xauusd-fast-research/balanced-horizon-ml-v5/.venv`,
run with `PYTHONPATH=src`. Data on `D:/AlgoTradingData/`.

---

## 11. Deliverable

1. **Verdict**: is V8 sound enough for a paper/demo shadow run? Yes / No / Yes-with-conditions.
2. **Bug list**, severity-ranked, each with a reproduction and an estimate of its
   effect on the headline numbers. Start with §3.
3. **Your own overfitting rating** 1–10, with reasoning, against the author's 3.
4. **Corrected figures** for any claim in §2 you find misstated.
5. **The one test the author should have run and didn't.**
6. **Kill criteria**: what result, if observed in a forward shadow run, should
   retire this system?

Be specific and quantitative. "Looks reasonable" is not a review. If you cannot
break a claim, say which tests you ran that failed to break it — that is the
useful form of a pass.
