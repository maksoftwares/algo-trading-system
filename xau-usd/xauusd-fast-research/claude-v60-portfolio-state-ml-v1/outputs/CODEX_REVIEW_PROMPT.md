# Adversarial review request: ML sizing overlay on the deployed V60 portfolio

You are reviewing a research lane that claims to improve the **already-deployed
V60 demo portfolio** using a machine-learning **position-sizing overlay**. Your
job is to try to break it. If it survives, say so plainly — a clean bill of
health is a valid and useful verdict. Do not soften findings to be agreeable, and
do not manufacture findings to look rigorous.

The author of this lane has a documented history in this repository of shipping
results that later proved defective (an exit-order sizing look-ahead that cost a
claimed PF 2.03 which was really 1.20; a PF-vs-dollars mismatch that recurred
three times; a cross-asset overlay whose feature silently selected a favourable
era). Assume the same class of error is present until you have checked.

---

## 1. What is being claimed

**Claim:** V60's nine sleeves produce trades whose expected value can be ranked
by a model trained on market state; sizing the trades by that rank — keeping
every trade, changing only the size — increases net profit and the
net-profit-to-max-drawdown ratio, and the effect is statistically significant.

**Headline numbers** (causal walk-forward, 2021–2026, 1,713 trades, the common
scored set):

| | net | maxDD ratio | green months |
|---|---|---|---|
| V60 as deployed | $5,082 | 17.05 | 63.6% |
| trivial benchmark: drop the 2 dead sleeves | $4,999 | 17.91 | — |
| ML sizing overlay, bagged x40, causal rank | **$6,311** | 19.10 | 63.6% |

Pooled permutation test: **observed +$1,110, null SD $264, z 4.21, p < 0.0001.**

**Last 12 available months (2025-07 → 2026-06), same trades and same win rate:**
net $2,509 → $2,950 (+18%), green months 9/12 → 10/12, **maxDD $153 → $229**,
so net/DD in that window gets WORSE (16.41 → 12.89).

**Explicitly NOT claimed:** the lane fails its own preregistered gate 4
("improve in ≥5 of 6 walk-forward years"), at 4/6 in most seeds. The author
argues that gate lacks statistical power (see §5). Treat that argument as a
claim to audit, not a given.

---

## 2. Where everything is

Branch `claude/xau-ml-and-v8-audit-v1`, commits `4c32d65c`, `09fdb653`,
`111d1d26`, `e43a6926`, and the V4 commit that adds `v4_causal_rank.py`.

Package: `xau-usd/xauusd-fast-research/claude-v60-portfolio-state-ml-v1/`

```
PREREGISTRATION.md              gates fixed BEFORE any model was trained
outputs/RESULT.md               full writeup, all four rounds, V1→V4
outputs/CONTRACT_LOCK.json
src/features.py                 feature build: market(16) + portfolio(7) + trade(2)
src/walkforward.py              three targets x six policies
src/evaluate.py                 all four gates on a common scored set
src/v2_sleeve_shrink.py         sleeve target-encoding + confidence shrinkage
src/v2_band_sweep.py            5 band widths x 2 shrinkage levels
src/v3_significance_bagging.py  permutation tests + bagged ranking + seed stability
src/v4_causal_rank.py           THE IMPORTANT ONE: causal vs non-causal rank map
src/v3_monthly_compare.py       month-by-month V60 vs overlay
```

Run any of them with:

```bash
cd xau-usd/xauusd-fast-research/claude-v60-portfolio-state-ml-v1
PYTHONPATH=src ../balanced-horizon-ml-v5/.venv/Scripts/python.exe src/v4_causal_rank.py
```

Build features first if the parquets are absent: `PYTHONPATH=src ... src/features.py`

**Inputs:**
- V60 ledger (2,194 rows):
  `xau-usd/xauusd-fast-research/one-trade-per-day-floating-equity-v60/outputs/ONE_TRADE_PER_DAY_FLOATING_EQUITY_V60_PRICE_LEDGER.parquet`
- Market features:
  `D:/AlgoTradingData/C_DRIVE/DukascopyTickDataFoundationV1/research/xau-confirmed-event-specialists-v1/m5_bidask_features_v1.parquet`
- P&L column used throughout: `fee_stress_pnl_usd`

---

## 3. Method, in one paragraph

For each year Y from 2021, train on every trade that **closed** before
`Y-01-01 minus a 48-hour purge`, predict a continuous P&L score for trades
**entered** in Y. Target is winsorised P&L (1st/99th pct),
`HistGradientBoostingRegressor(max_depth=3, max_iter=200, lr=0.05,
min_samples_leaf=40, l2=1.0)`. The ranking is bagged over 40 bootstrap resamples
of the training window and the ranks averaged. Each trade's score is converted to
a percentile **causally** (against the model's training-set predictions, or
against an expanding window of prior out-of-sample scores), mapped to a
multiplier in [0.5, 1.5] normalised by the constant `(lo+hi)/2`, then shrunk
toward 1.0 by `min(1, sqrt(n_train/1500))`. Every trade is kept; only size moves.

---

## 4. Defects the author already found and disclosed

Verify each was actually fixed, and that the fix is correct — do not take these
on trust. Their presence here is not evidence of thoroughness.

1. **`R1_NATIVE_POSITION` has no `risk_usd`** (444/444 NaN). The first feature
   build propagated NaN into the open-risk aggregate and silently dropped 35% of
   the book including 83% of the most profitable sleeve, whose trades had
   *higher* mean P&L. Fixed with `nansum` and by removing `risk_usd` as a
   per-trade feature. Coverage went 65.1% → 100%.
2. **Invalid baseline comparison**: policies were scored on 1,713 trades against
   a baseline computed on 2,019. `evaluate.py` restricts everything to a common
   scored set; six apparent passes became zero.
3. **Look-ahead in the sizing map (V1–V3)**: `rank(pct=True)` over the whole test
   year, normalised by that year's mean. Fixed in `v4_causal_rank.py`; the result
   *improved*, which is the main reason the author believes the effect is real.
4. **Preregistration error, disclosed**: gate 4 says "5 of the 8 walk-forward
   years" but only 6 years are evaluable. The stricter literal count (5) was
   applied.

---

## 5. The argument you most need to attack

The lane fails preregistered gate 4 (improve in ≥5 of 6 years). The author's
defence is that **the gate lacks power**, on this evidence:

- Permuting ranks within each year (null: "this year's ranking is uninformative")
  gives 2021 z −0.37 p 0.710, 2022 z −0.62 p 0.543 — the two failing years are
  the two years with **no measurable edge**, deltas ~0.2 SD from zero.
- A sign-counting gate fails a zero-edge year ~50% of the time, so with two such
  years even a perfect model passes with probability ~25%.
- Bagging (which reduces estimator variance) makes gate 4 fail *more* reliably,
  which the author reads as evidence those years are genuinely flat rather than
  noisily good.
- The proposed replacement — "pooled effect significant AND no year
  significantly negative" — was written **after** seeing results.

**Attack this specifically.** Is the permutation null correctly specified? Ranks
are formed per year, so the permutation is blocked by year — is that the right
block, given trades overlap in time and are not independent? Is the pooled z 4.21
inflated by serial dependence between overlapping trades? Is "the gate lacks
power" a legitimate statistical argument or a post-hoc rescue of a failed gate?
The author states it is weaker evidence than the preregistered gate and does not
overturn it; check whether the writeup lives up to that anywhere it matters.

---

## 6. Specific things to check

**Causality and leakage**
1. `features.py::portfolio_features` walks a min-heap of open positions. Confirm
   a trade can never see its own outcome or any later one. The heap stores
   `(exit_time, risk, sleeve, pnl)` — check the pnl is only ever popped for
   trades that closed before the current entry.
2. `assert_causal()` checks a FORBIDDEN list. Is that list complete? Anything
   derived from exit price, duration or outcome that is not on it?
3. The 48-hour purge: **what is the maximum holding period of a V60 trade?** If
   any trade is held longer than 48h, the training window can contain trades that
   were still open into the test year. Compute the true max duration and say
   whether 48h is sufficient.
4. `v4_causal_rank.py` mode C appends to `hist` **after** using it. Verify. Also
   verify mode B's reference distribution uses only training-window predictions.
5. Market features are read at the last completed bar at or before entry
   (`searchsorted(..., side="right") - 1`). Check for off-by-one.
6. Sleeve target-encoding in `v2_sleeve_shrink.py` uses `meta.iloc[:upto_idx]`
   where `upto_idx` is derived from the training mask. Confirm this cannot
   include the trade being encoded or any later trade.

**Statistics**
7. Bagging bootstraps rows of the training set, but trades **overlap in time** and
   are not iid. Does that invalidate the bootstrap, and does it make the seed-
   stability spread (net/DD ± 0.36) too narrow?
8. 32+ configurations were evaluated on 1,713 trades before the V4 result. Is the
   final claim adequately discounted for that search? The author declares the
   budget in RESULT.md but does not apply a formal multiple-comparison penalty.
9. Is the trivial benchmark (17.91, drop the two dead sleeves) the right bar, or
   is there a cheaper non-ML rule that beats 19.10?

**Practical viability — the part most likely to kill this**
10. **Minimum lot size.** V60 trades on a demo account with a 0.01 lot minimum.
    A 0.5x–1.5x continuous multiplier is **not executable** on a 0.01 base lot —
    you cannot trade 0.005. Determine V60's actual per-trade lot sizes and decide
    whether the overlay is implementable at all, or whether it only works for
    accounts large enough that base size is ≥0.05 lots. **If this fails, the
    entire result is academic.** The author has hit this exact constraint before
    in a "0.01 lot constrained" test elsewhere in the repo.
11. Mean multiplier is 1.017 under mapping C, i.e. the book runs 1.7% larger.
    Quantify how much of the +$1,229 is just extra leverage rather than better
    allocation. Author estimates ~$86; verify, and re-run forced to mean exactly
    1.0.
12. The last-12-month drawdown gets worse ($153 → $229). Is the long-run net/DD
    improvement (17.05 → 19.10) an artefact of the early era, and is the recent
    era telling a different story?
13. V60 has a one-trade-per-day / floating-equity structure. Does resizing
    interact with any position cap, margin rule, or the floating-equity logic in
    a way the backtest does not model?

---

## 7. Deliver

For each finding: **file:line, what is wrong, why it matters, and what it does to
the headline numbers if fixed.** Rank by severity. Distinguish
"invalidates the result" from "reduces it" from "cosmetic".

Then one of:
- **ADOPT** — the effect is real and implementable; state the honest expected
  improvement and the preconditions.
- **ADOPT WITH CHANGES** — list them.
- **REJECT** — state the single finding that kills it.

Constraints on you: this lane authorises **no** runtime, EA, demo, live or broker
change (`ml_runtime_authorized: false`). Do not modify the V60 runtime, MT5
terminals, account settings, or any frozen package. Read everything; write only
in your own package and branch.
