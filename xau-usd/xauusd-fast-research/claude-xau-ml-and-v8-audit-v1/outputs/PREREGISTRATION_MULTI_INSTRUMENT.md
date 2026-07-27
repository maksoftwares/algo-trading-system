# Preregistration — multi-instrument portfolio (MI-V1)

**Written 2026-07-26, BEFORE any multi-instrument result was computed.**
Everything below is fixed at the moment of writing. Anything I change later gets
recorded as an amendment with its reason, and any result produced after an
amendment is reported as such.

Owner goal: good frequency, every month positive, good profit factor, good win
rate, **no overfitting**.

---

## 1. Why this experiment, in one line

Gold alone generates ~0.4 tradeable setups per day at a real quality bar; the
drawdown-vs-frequency sweep showed 1 trade/day on gold costs $600+ of drawdown
against a $300 limit. Adding instruments raises frequency at *unchanged*
selectivity, and because their losing streaks are not synchronised the combined
drawdown should grow sub-linearly. That is the hypothesis under test.

## 2. The one thing that makes this credible: no new tuning

Today's headline finding was that hindsight in *choosing* is worth 0.3–0.6 PF
(63.0%/1.99 in-sample → 49.1%/0.82 when nothing is pre-chosen). The defence is
to remove the choice.

**The gold configuration is transplanted UNCHANGED to every instrument.** No
per-instrument parameter search, at all. Specifically fixed:

| Parameter | Value | Where it came from |
|---|---|---|
| entry | confirmation at 0.5×stop | V6, unchanged |
| stop | 6.75 × ATR144 | V6, unchanged |
| horizon | 432 bars (36h) | V6, unchanged |
| session | 07:00–17:00 UTC, 30-min grid | V6, unchanged |
| specialists | the 7 V6 members, same gates and percentiles | V6, unchanged |
| macro filter | `macro_long_slope_min = 0` | V6, unchanged |
| dedup | on — one position per distinct setup | gold drawdown work, today |
| K | 4 concurrent | gold's best cell under the $300 limit |

I am **not** free to re-pick K or the percentiles per instrument. If EURUSD would
look better at K=6, that is not available to me.

## 3. Forced deviations (declared now, not discovered later)

Three, all imposed by data rather than chosen:

1. **5-feature ranker on non-gold.** `tick_signed_move`,
   `tick_book_imbalance_mean` and `price_efficiency_5m` do not exist in the FX/
   silver datasets. The ranker for those instruments uses the 5 available
   features (speed, activity, spread, adv_pre, align). Gold keeps all 8.
2. **Ranker refit per instrument, dev era only.** Gold's frozen V8 coefficients
   are meaningless on EURUSD — different units, different scale. Each instrument
   fits its own ridge on its own 2016–2021 candidates and nothing later. Note
   the campaign's earlier finding that refit rankers overfit relative to the
   frozen one; that risk is accepted and disclosed, because there is no
   alternative.
3. **No regime ledger off gold.** The H4 regime labels exist only for XAUUSD, so
   the two trend specialists' `exclude: [R0_SHOCK, R3_COMPRESSION]` becomes
   `ALL` on other instruments.

## 4. Hard limitations that no result can overcome

- **Single feed off gold.** There is no Capital execution feed for EURUSD,
  GBPUSD, USDJPY or XAGUSD. The work order says single-feed discovery is
  invalid, and that stands: non-gold sleeves are Dukascopy-only and are
  **research evidence, not deployment evidence**, however good they look.
- **USDJPY ends 2024-06-30, XAGUSD ends 2024-07-12.** Neither can say anything
  about the last two years. They are included for breadth but excluded from any
  recent-period or green-month claim, and that exclusion is decided now.
- Only **XAUUSD, EURUSD, GBPUSD** carry data into 2026. Any statement about
  current performance rests on those three.

## 5. Decision rules, fixed in advance

**Per-instrument inclusion.** An instrument joins the portfolio iff, on its own
dev (≤2021) AND test (2022–2024) eras: `PF ≥ 1.20` and `n ≥ 100`.
Inclusion is decided on the instrument's own record — **never** on what it does
to the portfolio, because that is selection on the outcome.

**Portfolio gates** (all must hold, measured on the causal walk-forward, not
in-sample):

| metric | threshold |
|---|---|
| frequency | ≥ 1.0 trades / trading day |
| win rate | ≥ 40% |
| profit factor | ≥ 1.30 |
| green months | ≥ 70% |
| max drawdown | ≤ $300 at 0.01 lot |

**Primary threshold mode** is `frozen` (the exact gold config). `rolling` (the
drift fix) is a preregistered secondary; both get reported whatever they show.

**Arbiter.** The mechanism-causal walk-forward is the number of record — for
each year, sleeves are scored only on trades closed before that year. In-sample
figures are reported for comparison and are explicitly not evidence.

## 6. What would falsify the hypothesis

- Non-gold sleeves fail their own PF ≥ 1.20 gate → the mechanism is
  gold-specific and does not transfer. This is a real possibility: an earlier
  campaign already recorded "instrument transplants fail."
- Sleeves pass individually but combined drawdown scales *linearly* rather than
  sub-linearly → the diversification premise is wrong, and 1 trade/day at $300
  drawdown stays unreachable.
- Green months stay below 70% → monthly consistency needs something other than
  more instruments.

Any of these gets reported as a negative result. No post-hoc instrument
dropping, no threshold shopping, no re-running with a different K until it
passes. Three preregistrations maximum for this lane, then it closes.

## 7. Attempt log

| # | date | what changed | outcome |
|---|------|--------------|---------|
| 1 | 2026-07-26 | initial transplant, config frozen as above | **VOID — defect, see amendment A1** |
| 2 | 2026-07-26 | A1 cost fix + proper true range, config otherwise unchanged | **FAIL — but confounded, see A2** |
| 3 | 2026-07-26 | A2 equal-footing retest: FX rebuilt with the full 8-feature set | **FAIL — lane closes `MULTI_INSTRUMENT_TERMINAL_FAIL`** |

### Result of attempt 3 — the mechanism does not transfer

EURUSD and GBPUSD rebuilt from raw ticks with the identical 8-feature ranker
gold uses (builder validated to max\|diff\| = 0.000e+00 against gold's stored
features). Test-era profit factor, before and after removing the handicap:

| symbol | 5-feature (run 2) | **8-feature (run 3)** | gate |
|---|---|---|---|
| XAUUSD | 1.89 | 1.89 | PASS |
| EURUSD | 0.78 | **1.08** | FAIL |
| GBPUSD | 0.87 | **0.97** | FAIL |

The features mattered — EURUSD gained +0.30 PF on test, which confirms amendment
A2's diagnosis was correct and that run 2's rejection was indeed unfair. But the
corrected result still falls short of the preregistered PF ≥ 1.20, and both
instruments are outright losing on holdout (EURUSD 0.79, GBPUSD 0.72).

On identical features gold scores 1.89 against EURUSD's 1.08. **The gap is the
instrument, not the feature set.** The mechanism is genuinely gold-specific,
which is what this repo's earlier "instrument transplants fail" note recorded —
now established on equal footing rather than by accident.

**Consequences, accepted:**
- The multi-instrument route to ≥1 trade/day is closed. Gold alone yields ~0.4
  setups/day inside the $300 drawdown limit.
- "Every month green" is not reachable at ~5 trades/month on one instrument.
- No fourth attempt. Reopening requires new information — a different venue,
  instrument class, or trade definition — not more search over this data.

### Amendment A2 — the feature handicap was mine, and it was decisive (2026-07-26)

Run 2 rejected all four non-gold instruments (EURUSD 0.78, GBPUSD 0.87,
USDJPY 1.01, XAGUSD 1.02 on test). I attributed this to the mechanism being
gold-specific. **That attribution was wrong**, and the confound was one I
introduced in section 3, deviation 1: gold ranked on 8 features, everything else
on 5, because three tick-microstructure features had never been computed for the
FX datasets.

Control experiment — gold run through the same 5-feature ranker the FX sleeves
got:

| gold ranker | dev PF | test PF | holdout PF |
|---|---|---|---|
| 8 features (as run) | 1.62 | **1.89** | 1.68 |
| 5 features (FX-matched) | 1.55 | **1.10** | 1.41 |

Handicapped gold lands at 1.10 on test — indistinguishable from USDJPY (1.01)
and XAGUSD (1.02). The instruments were not competing on equal terms, so run 2
cannot support the conclusion that the mechanism does not transfer.

**A first-order finding in its own right:** the three tick features carry most of
the edge, not the price-shape logic. That is worth more than the transplant
result either way.

**Attempt 3:** rebuild the non-gold M5 datasets from raw Dukascopy ticks with the
full feature set, then re-run the identical transplant. The definitions were
recovered from gold's own raw ticks and verified at correlation 1.0000 with
identical medians against the stored gold parquet:

| feature | definition |
|---|---|
| `tick_signed_move` | Σ sign(Δmid) over ticks in the bar |
| `price_efficiency_5m` | \|net move\| / Σ\|Δmid\| |
| `tick_book_imbalance_mean` | mean((bidVol − askVol)/(bidVol + askVol)) |

**Not a tuning change:** no parameter is introduced or moved. This removes a
handicap so that the comparison tests what it claims to test. Every decision rule
in sections 2, 3 and 5 is unchanged, including PF ≥ 1.20 on dev AND test.

**This is the third and final attempt.** If the non-gold sleeves fail on equal
footing, the lane closes as `MULTI_INSTRUMENT_TERMINAL_FAIL` and the conclusion
is that the mechanism genuinely does not transfer.

### Amendment A1 — dimensionally incorrect commission (2026-07-26)

Run 1 rejected EURUSD, GBPUSD, USDJPY and XAGUSD. Those rejections are **void**:
the mechanism never got a fair test, because `engine.FEE = 0.30` is denominated
in gold dollars and was applied unscaled to every instrument. Since realised R
divides by a stop expressed in each instrument's own price units, the commission
term `FEE/stop` exploded on low-priced instruments:

| symbol | price | FEE/stop | reported meanR |
|---|---|---|---|
| EURUSD | ~1.10 | ~444 | −87.5 |
| GBPUSD | ~1.27 | ~350 | −64.8 |
| USDJPY | ~110 | ~2.2 | −0.74 |
| XAGUSD | ~25 | ~4.4 | −0.89 |
| XAUUSD | ~2000+ | ~0.02 | +0.43 |

A mean R of −87 is arithmetically impossible (the floor is −1R per trade), so
this is a defect, not a finding. The monotone relationship with price level is
the signature.

**Fix:** express commission as a constant fraction of notional rather than an
absolute number — `FEE_sym = 1.5e-4 × median(price)`, which reproduces gold's
$0.30 at ~$2,000 exactly and scales correctly elsewhere. The bid/ask spread is
already charged separately through ask-fills and bid-exits.

**Why this is not a tuning change:** it introduces no free parameter that can be
moved toward a better answer. The constant is pinned by gold's existing value,
not chosen; a single number fixes all instruments at once, and I cannot adjust
it per instrument. Also fixed in the same amendment: true range now uses the
correct `max(H−L, |H−prevC|, |L−prevC|)` instead of the approximation
`max(H−L, |ΔC|)`.

**Unchanged:** every decision rule in sections 2, 3 and 5. The per-instrument
gate is still PF ≥ 1.20 on dev AND test with n ≥ 100, and inclusion is still
decided on each instrument's own record.
