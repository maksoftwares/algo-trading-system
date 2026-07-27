# Claude XAUUSD ML and V8 Audit V1 — Result

Decision: **CLAUDE_XAU_ML_AND_V8_AUDIT_V1_SIX_LANES_FAIL_QUARANTINED_ONE_PARTIAL_PASS**

Historical research only. Execution is not authorized.

Source package: `algo-regime-teacher-wt/.../regime-teacher-eas-v1`, branch
`codex/regime-teacher-eas-v1`. This directory restates those findings in the
`v6-causal-ml-*` package format; it does not re-run them.

## Lane outcomes

| Lane | Hypothesis | Decision |
|---|---|---|
| A | per-regime specialist family | **FAIL — QUARANTINED** |
| B | multi-instrument transfer | **FAIL — TERMINAL** |
| C | GOLD V8 horizon-diversified family | **FAIL — REJECTED BY REVIEW** |
| D | ML early exit before the stop | **FAIL — QUARANTINED** |
| E | ML entry filter on the V6 book | **FAIL — QUARANTINED** |
| F | cross-asset position sizing | **FAIL — QUARANTINED** |
| G | microstructure-generated entries | **FAIL — QUARANTINED** |
| C' | V6 entry-time slot locking (fix C) | **PARTIAL PASS** |

## Lane A — per-regime specialists

In-sample best cell reached WR 63.0% / PF 1.99 / maxDD $121. Under a walk-forward
that also chose the mechanism causally: **WR 49.1% / PF 0.82 / -$435**. The
regime label does not separate good months from bad — 2026-01 (+$1,903) and
2026-02 (-$1,743) are consecutive months, both stable STRONG_BULL.

## Lane B — multi-instrument transfer

Gold config transplanted unchanged, per-instrument gate PF >= 1.20 on dev AND
test. Test-era PF on the identical 8-feature ranker: **XAUUSD 1.89, EURUSD 1.08,
GBPUSD 0.97**. USDJPY 1.01, XAGUSD 1.02. None passed. Terminal after three
attempts; two of the three were voided by defects found mid-lane (see Defects).

## Lane C — GOLD V8

Claimed causal walk-forward PF 2.03. Independent adversarial review corrected it
to **PF 1.202**, weekly-block 95% CI **[0.96, 1.46]** — the interval contains 1.0.
Full-history PF 1.79 -> **1.242** on executable dollars; maxDD $1,167 -> **$1,980**.

Disqualifying independent of the defects: **removing the top 1% of trades (56 of
5,572) leaves PF 1.000 and -$4.** Removing the top 5% leaves PF 0.606 and
-$11,181.

## Lane D — ML early exit

Adverse observations: current unrealised **-0.313R**, mean final **-0.270R**.
**Holding beats exiting by +0.043R.** Searched 6 features x 3 adverse buckets x 5
quintiles = 90 cells; best was -0.084R, non-monotone, i.e. noise. Mechanically an
adverse excursion on a confirmation entry with a 6.75xATR stop *is* the setup
deepening.

Independently corroborated by `v6-causal-ml-early-exit-v3`, which reached the
same conclusion on 399k training rows: net dollars saved **-$299.44**.

## Lane E — ML entry filter

Applied to the V6 book, cutoff chosen from the fit era:

| cutoff | sealed PF | sealed $ |
|---|---|---|
| none | 2.122 | $2,187 |
| drop 10% | 2.305 | $2,237 |
| drop 25% | 2.385 | $2,082 |
| drop 40% | 2.378 | $1,601 |

**PF rises and P&L falls at every cutoff** — removal, not selection. The model
uses the same 8 features the frozen ranker already selected on.

Independently corroborated by `v6-causal-ml-veto-v1`: PF 1.177 -> 1.221 while net
fell $303.59 -> $293.99.

## Lane F — cross-asset sizing

Initially passed: causal quarterly walk-forward, return/DD **3.99 -> 5.21**,
survived lot-rounding, both feature halves independent, CFTC point-in-time
verified (publication lag 6.0 days median).

**Retracted.** The feature set required the gold vol index, which starts 2023-01,
silently restricting the test to the era where the base strategy earns meanR
+0.174/+0.107/+0.397. Dropping that feature extended coverage to 2022-01 and
11,583 rows: the overlay then **failed**, turning the weak era's $1,751 into
**$171** and losing in 3 of 5 years.

## Lane G — microstructure entries

Four triggers (absorption, imbalance, efficiency, flow-break) x three thresholds.
**0 of 12 cells passed.** Every trigger loses across 2016-2024 and wins in
2025-26 — a regime effect, and the reverse of the overfitting signature.

## Lane C' — V6 entry-time slot locking (the only partial pass)

V6 reserves position slots at the **decision** bar, using confirmation and exit
information that does not exist yet. Locking at entry instead:

| | V6 as deployed | + entry-time locking |
|---|---|---|
| PF (Capital, full history) | 1.656 | **1.671** |
| net | $3,783 | **$3,917** |
| maxDD | $270 | $270 |
| green months | 57/113 | 58/113 |

Free: more money, better PF, identical risk, and it removes look-ahead.

**Caveat that reduces its value:** a live EA cannot reserve a slot at decision
time — it only knows its real book when it tries to open. So this is most likely
a *backtest* correction rather than a deployable change, and V6's live behaviour
may already match the fixed version. Requires runtime verification.

## Defects found (in this work and in V6)

| Defect | Effect |
|---|---|
| Exit-order position sizing | look-ahead; PF 2.03 -> 1.202 when corrected |
| PF computed on a different series from dollars | recurred 3x after one fix |
| Gold-denominated fee applied to FX | ~444R/trade on EURUSD; voided a lane |
| Feature availability selecting the window | two false positives in one day |
| **V6 double-booking** | **79.4% of signals open two positions; $236.58 peak risk on one signal** |
| **V6 starved threshold** | admits 0.43-0.62x the trades the spec calls for |

## Durable measurements

- **Selection-leak ladder on this data:** PF 1.99 (full hindsight) -> 1.45
  (parameters causal, pool hand-picked) -> **0.82** (nothing pre-chosen). Roughly
  0.3-0.6 PF per layer of hindsight.
- **Tick microstructure carries most of the edge:** gold PF **1.89 -> 1.10** on
  the test era without `tick_signed_move`, `tick_book_imbalance_mean`,
  `price_efficiency_5m`. It works as a ranking signal and not as an entry signal
  (lane G).
- **Selection instability predicts failure** before any P&L is consulted: the
  annual re-pick churned STRONG_BULL variants every year and it failed;
  RANGE_QUIET picked the same config 8/8 years and held.

## Interpretation

Seven hypotheses tested, seven failed. One free correctness fix survives and may
be a backtest artifact rather than a deployable change. The only line in this
corpus with a clean causal validation and a proper dual-feed pass remains **V6 at
walk-forward PF 1.42**, which nothing here improved on.
