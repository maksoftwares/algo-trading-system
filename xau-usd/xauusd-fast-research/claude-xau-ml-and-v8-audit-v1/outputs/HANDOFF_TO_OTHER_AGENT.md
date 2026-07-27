# Handoff brief — XAUUSD research corpus

## What you are being given, and what it is worth

A ~10-year XAUUSD research corpus: engine, data pipelines, ~40 analysis scripts,
a labelled ML dataset, and a written record of about 30 experiments.

**Read this first, because it changes how you should use everything else:**

> **Almost every strategy in this corpus FAILED under honest testing.** The
> headline system (GOLD V8) claimed profit factor 2.03 and was reduced to **1.20**
> by an independent review — a 95% confidence interval of [0.96, 1.46], which
> contains 1.0. The ML filter was built, trained, and **refuted**. A per-regime
> specialist family went from an apparent 1.99 to **0.82**. A multi-instrument
> transplant failed on equal footing.

So do **not** lift a strategy from here and expect it to work. What is genuinely
valuable is the **methodology, the tooling, the data pipelines, and roughly
thirty documented negative results** that will stop you re-running experiments
that have already been shown to fail on this data.

If you extract one thing, extract the **validation harness discipline** in §5.
It is what turned a plausible 2.03 into a real 1.20, and it will do the same to
your own results.

---

## 1. Location and environment

**Everything is on branch `codex/regime-teacher-eas-v1`** in a worktree:

```
C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-regime-teacher-wt/
    xau-usd/xauusd-fast-research/regime-teacher-eas-v1/
```

Python (has pyarrow; the phase0 venv does NOT):
```
C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/
    xau-usd/xauusd-fast-research/balanced-horizon-ml-v5/.venv/Scripts/python.exe
```
Run everything with `PYTHONPATH=src` from the package root.

Source data (D: drive):
```
XAUUSD M5 signal   D:/AlgoTradingData/C_DRIVE/DukascopyTickDataFoundationV1/
                     research/xau-confirmed-event-specialists-v1/m5_bidask_features_v1.parquet
XAUUSD M5 exec     D:/AlgoTradingData/research/
                     r5-capital-mt5-full-history-replication-v18/CAPITAL_XAUUSD_M5_FULL_HISTORY_V18.parquet
H4 regime ledger   D:/AlgoTradingData/research/hindsight-opportunity-regimes-v1/HINDSIGHT_H4_REGIME_LEDGER_V1.parquet
built FX/silver    D:/AlgoTradingData/research/regime-teacher-eas-v1/*.parquet
raw Dukascopy ticks D:/AlgoTradingData/C_DRIVE/DukascopyTickDataFoundationV1/raw/
                     {XAUUSD,EURUSD,GBPUSD,USDJPY,XAGUSD,DOLLARIDXUSD,USTBONDTRUSD}
```

---

## 2. GOLD V8 — the system, and why it failed

**Spec:** `outputs/GOLD_V8_SPEC.json` — status `REJECTED`. Read the
`REVIEW_VERDICT` block at the top before anything else; it contains every
corrected figure and all seven defects.

**Source:**
| File | Role |
|---|---|
| `src/gold_v8.py` | sleeve construction, ranker fit, rolling-threshold selection |
| `src/gold_v8_walkforward.py` | causal walk-forward (**contains the S0 bug**) |
| `src/gold_v9_partial.py` | `assemble()` — dedup, K-lock, streak sizing (**S0 bug lives here**) |
| `src/v8_dualfeed.py` | Capital execution leg |
| `src/v8_lot_constrained.py` | realistic 0.01-lot sizing |
| `src/v8_weakness.py` | red-month forensic |
| `src/v8_drawdown.py` | open-risk cap and drawdown-throttle tests |

**Trade records:** `outputs/GOLD_V8_DUALFEED_TRADES.csv` (both feeds, 5,961 rows),
`GOLD_V8_FINAL_TRADES.csv`, `GOLD_V8_WALKFORWARD_TRADES.csv`.

**Design:** 12 specialists = 3 horizons (12h/36h/72h) × 4 entry gates, both
directions. Weekly EMA slope picks the side. Entry is *confirmation* — wait for
price to move 0.5 × stop in the chosen direction, then enter next bar. Stop
6.75 × ATR144, exit at stop or horizon close. Ridge ranker on 8 features with a
rolling-quantile threshold. Dedup to one position per decision bar, K-slot
lockout, streak-based position sizing.

**Why it failed — the defects, in severity order:**

1. **S0 — sizing look-ahead.** Position size was assigned walking trades in
   *exit* order; it must be *entry* order. 63.5% of trades were affected. Alone
   this moved full-history PF 1.790 → 1.183 and the causal walk-forward
   2.034 → 1.202.
2. **S0 — walk-forward not causal.** Trades assigned to years by exit year, so
   positions already open when a year's parameters were chosen were credited to
   that year. State was rebuilt retrospectively per year instead of carried along
   the traded path.
3. **S1 — PF computed on a different series from the dollars.** Recurred in three
   scripts after being fixed once.
4. **S1 — Capital leg inherited Dukascopy sizing state and timestamps.** 2,040 of
   5,961 trades have differing exit times; 73 cross a month boundary.
5. **S1 — no single frozen config.** `gold_v8.py` defaults K=4/streak 3-5; the
   spec says K=6/2-4; `v8_dualfeed.py` inherits different defaults again.
6. **S2 — dedup picks the winning sleeve using a ranker fit through 2024** (41%
   of pre-2025 winners change under prior-year-only rankers).
7. **S2 — K slots reserved at decision time**, using confirmation and exit
   information that does not exist yet.

**The statistic that disqualifies it regardless of the bugs:** removing the top
1% of trades (56 of 5,572) leaves PF 1.000 and −$4. Removing the top 5% leaves
PF 0.606 and −$11,181. Essentially all profit comes from ~56 trades.

---

## 3. The ML work — built, trained, and refuted

**Findings write-up:** `ML_FILTER_FINDINGS.md` (read this first).

**Dataset:** `outputs/ML_TRADE_DATASET.parquet` — **25,781 labelled trade setups
× 32 columns**. This is the most directly reusable artifact in the corpus.

Columns: the 8 ranker features (`speed, flow, imb, activity, spr, eff, adv_pre,
align`), `rank_score`, `macro_slope`, outcome labels (`R`, `win`, `pnl_usd`,
`stop_usd`), timestamps (`dec_time`, `exit_time`), plus point-in-time cross-asset
context for 11,644 of the rows (2022-2026 only):
`spx_/copper_/usdcnh_{return_15m, return_60m, signed_move, spread_shock_ratio}`,
`vol_mid_close`, `vol_return_60m`, and weekly CFTC positioning
(`managed_money_futures_net`, `mm_net_pct_oi`).

**Source:** `src/ml_dataset.py` (build), `ml_train.py` (GBM/logistic,
walk-forward), `ml_apply.py`, `ml_selector.py`.

**Result — refuted.** Walk-forward against the *frozen ranker alone* looked good
(+0.28R vs +0.20R on the top 20%). But tested against the **real incumbent** — the
full deployed family — it lost at every cutoff: as a secondary filter,
drop-bottom-20% gave $1,309 against a $2,891 baseline with drawdown $515 vs $270;
as a primary selector at matched frequency, $1,084 vs $2,891.

**The lesson, which is the transferable part:** *benchmark against the real
incumbent, not a weak component.* The frozen ranker alone scores +0.202R on the
raw population; the full family (ranker + macro filter + dip gates + session
specialisation) scores +0.531R. The ML signal was genuine but **redundant** with
the hand-built rules.

**Related and also refuted:** `src/bad_conditions.py`, `src/apply_difficulty.py` —
a market-difficulty model built from 370k campaign trades
(`D:/AlgoTradingData/research/regime-teacher-eas-v1/ALL_CAMPAIGN_TRADES.parquet`).
Those trades are all screening *rejects*, average −0.27R, and cover 2016-2019
only; they did not transfer.

**Untested ML directions** (stated in the findings doc, never run): cross-asset
as a position-*sizing* or exposure control rather than a binary filter.

---

## 4. What actually survived — use these

### 4a. The single most valuable empirical finding

**Tick microstructure carries most of the edge.** Gold's profit factor drops
from **1.89 to 1.10** on the test era when three features are removed:
`tick_signed_move`, `tick_book_imbalance_mean`, `price_efficiency_5m`.

Every system in this corpus uses them only as a *ranking filter* on a
price-pattern entry. **Nobody has built a mechanism that enters on them.** That
is the most promising unexplored direction here, and it is measured, not
speculative.

Exact definitions, recovered from raw ticks and verified at correlation 1.0000
with `max|diff| = 0.0` against the stored gold parquet:
```
tick_signed_move         = sum(sign(diff(mid)))          # up-ticks minus down-ticks
price_efficiency_5m      = |net move| / sum(|diff(mid)|)
tick_book_imbalance_mean = mean((bidVol - askVol)/(bidVol + askVol))
tick_spread_mean         = mean(ask - bid)
tick_count               = number of ticks in the bar
```
Builder: `src/build_tick_features.py` (validated against gold in
`src/verify_tick_features.py`). EURUSD and GBPUSD are already rebuilt with the
full 8-feature set at `*_M5_FEATURES_V2.parquet`. **DOLLARIDXUSD and
USTBONDTRUSD have raw ticks and have never been built** — that is free ground.

### 4b. Reusable machinery

| File | What it gives you |
|---|---|
| `src/engine.py` | dual-feed backtest engine, execution, regime lookup |
| `src/specialist.py` | cached market context (`load_context()`), specialist runner |
| `src/regime_frontier5.py` | `rolling_thr()` — causal trailing-quantile threshold, vectorised and verified against a naive loop |
| `src/build_tick_features.py` | raw Dukascopy tick → M5 bars with full microstructure |
| `src/multi_instrument.py` | cross-instrument harness (note the cost bug, §6) |
| `src/v6_fix.py` | **correct** entry-order book with heap-settled exits — copy this pattern |

### 4c. Documented negative results — do not re-run these

`REGIME_SPECIALIST_FAMILY_V7.md` and `PREREGISTRATION_MULTI_INSTRUMENT.md` carry
the full record. Summary of what is already closed on this data:

- **Regime-split specialists**: PF 1.99 in-sample → **0.82** causal. The regime
  label does not separate good months from bad — Jan 2026 (+$1,903) and Feb 2026
  (−$1,743) are consecutive, both stable STRONG_BULL.
- **Multi-instrument transplant**: on the *identical* 8-feature ranker, XAUUSD
  1.89 vs EURUSD 1.08, GBPUSD 0.97. Does not transfer.
- **5 entry filters** (trend-strength band, regime transition, regime label,
  stale direction signal, fast/slow agreement) — all failed.
- **9 exit geometries** (partials at 0.75/1.0/1.5R × 30/50/70% with and without
  break-even) — pure trade-off, no free gain. Break-even stops specifically eject
  from the large winners that carry the edge.
- **5 horizon configurations** (3h to 288h) — green months pinned at 63-67%.
- **7 decorrelation configs** (position spacing, per-direction caps) — destroy
  both profit and consistency. The correlation between concurrent positions *is*
  the mechanism, not noise.
- **Monthly loss circuit-breaker** — amputates recoveries, makes drawdown worse.
- **ML filter** — see §3.

---

## 5. The methodology to steal — this is the real deliverable

### 5a. The measured cost of hindsight on this data

Same data, same code, same components; only the amount of hindsight in the
*choosing* varies:

| How the configuration was chosen | PF |
|---|---|
| Best of 24 compositions, dev+test visible, holdout peeked at 4× | **1.99** |
| Walk-forward — parameters causal, candidate pool hand-picked | **1.45** |
| Walk-forward — mechanism also chosen causally, nothing pre-filtered | **0.82** |

**Each layer of hindsight is worth roughly 0.3-0.6 PF here.** The largest leak
was not parameter tuning — it was choosing *which mechanism* belongs where after
seeing every era.

### 5b. The validation standard that survived review

If you take nothing else, take this:

1. **Size and gate in ENTRY order**, settling prior positions from a min-heap of
   actual exits. Never sort by exit time to compute state.
2. **Assign trades to evaluation periods by ENTRY time**, never exit time.
3. **Carry portfolio state continuously** across the whole span — never rebuild
   it retrospectively per period.
4. **Compute PF/WR on the same series as the dollars and the drawdown.** This
   recurred three times here after being fixed once.
5. **Attribute broker P&L to broker timestamps**, not signal-feed timestamps.
6. **One frozen configuration**, passed explicitly. Never rely on per-caller
   defaults.
7. **Reserve position slots at ENTRY**, not at the decision bar.
8. **Preregister the objective in writing before running**, including gates and
   falsification conditions. See `PREREGISTRATION_MULTI_INSTRUMENT.md` for a
   worked example with amendments logged.

### 5c. Cheap tells that caught real bugs here

- **Impossible values.** A mean of −87R when the floor is −1R exposed a
  dimensionally wrong cost constant. **Check arithmetic floors first.**
- **Internal contradictions.** "PF 0.89 with +$1,259 profit" is impossible and
  exposed the series mismatch.
- **Monotone relationships with a nuisance variable.** Damage scaling with price
  level ($2,000 gold unaffected, 1.10 EURUSD destroyed) revealed the fee bug.
- **Selection instability.** A procedure that re-picks a different variant every
  year has no stable edge — this predicted the regime family's failure *before*
  any P&L was consulted. Conversely, RANGE_QUIET picked the same config 8/8 years.
- **A gate that never binds.** If a filter changes nothing when you vary it, it is
  circular — check before crediting it.

---

## 6. Known bugs still live in this corpus — do not inherit them

1. **`src/gold_v9_partial.py::assemble()`** and
   **`src/gold_v8_walkforward.py`** — exit-order sizing (S0). `src/v6_fix.py`
   shows the correct entry-order pattern.
2. **`engine.FEE = 0.30`** is denominated in *gold dollars*. Applied unscaled to
   EURUSD (price 1.10, stop 0.00235) it charges ~444R per trade.
   `src/multi_instrument.py` has the scaled fix
   (`1.5e-4 × median price`), but check any other cross-instrument code.
3. **PF-vs-dollar mismatch** in `v8_lot_constrained.py:46` and
   `v8_drawdown.py:69`.
4. **`outputs/GOLD_V8_WALKFORWARD.json` records PF 1.11** while the write-ups
   reported 2.03 — same series-definition inconsistency.
5. The **"28-sleeve causal chooser PF 2.04"** claim has no saved script or trade
   file. Treat as non-evidence.

---

## 7. Suggested tasks

1. **Read `ML_FILTER_FINDINGS.md`, then load
   `outputs/ML_TRADE_DATASET.parquet`.** 25,781 labelled setups with outcomes and
   cross-asset context. If you can find signal the hand-built rules do not already
   capture, that is a real result — but benchmark against the full family
   (+0.531R), not the ranker alone (+0.202R).
2. **Build a mechanism around tick microstructure** rather than using it as a
   filter (§4a). This is the strongest unexplored lead and it is quantified.
3. **Build DOLLARIDXUSD and USTBONDTRUSD** with `build_tick_features.py`. Raw
   ticks exist, nobody has touched them, and the instrument-selection screen in
   memory suggests screening range/cost *before* searching strategies.
4. **Port the §5b validation standard into your own harness** before you trust any
   of your own numbers.
5. **Do not** re-run anything in §4c without new data or a genuinely different
   mechanism.

## 8. Ground truth for anything you build here

The only system in this corpus with a clean causal validation *and* a proper
dual-feed pass is **V6** (`outputs/SPECIALIST_FAMILY_V6_DEPLOYABLE.json`),
at PF 1.73 in-sample → **1.42** walk-forward. That is the bar. Anything claiming
materially more than ~1.4 on XAUUSD M5 confirmation entries should be assumed to
have a leak until proven otherwise — because in this corpus, every single time,
it did.
