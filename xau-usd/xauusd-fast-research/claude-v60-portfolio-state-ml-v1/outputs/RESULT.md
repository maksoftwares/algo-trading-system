# Claude V60 Portfolio-State ML V1 — Result

Decision: **CLAUDE_V60_PORTFOLIO_STATE_ML_V1_GATE_FAIL_QUARANTINED_STRONG_SIGNAL_RECORDED**

Historical research only. `ml_runtime_authorized: false` and
`ml_shadow_authorized: false` in the V60 config. This lane authorizes no runtime,
EA, demo, live or broker change.

## Summary

The preregistered hypothesis — that **portfolio state** is orthogonal information
the nine sleeves cannot see — is **refuted by ablation**.

A different result survived: a P&L-regression **sizing overlay on market features**
takes V60 from net/DD 17.05 to **19.94** and net $5,082 to **$6,694 (+32%)** on the
2021-2026 walk-forward. It fails the preregistered year-consistency gate (4 of 6
years) and is therefore quarantined, but the signal is monotone and is recorded
in full because it explains why every veto attempt in this repository has failed.

## Gate outcome

| Gate | Requirement | Best variant | Pass |
|---|---|---|---|
| 1 | net P&L must not fall | $6,694 vs $5,082 | **yes** |
| 2 | net/maxDD must improve | 19.94 vs bar 17.91 | **yes** |
| 3 | green months within 2 points | 63.6% vs 61.6% | **yes** |
| 4 | improve in >= 5 of the walk-forward years | **4 of 6** | **NO** |

0 of 18 policies passed all four. Gate 4 is binding.

**Preregistration error, disclosed:** gate 4 was written as "at least 5 of the 8
walk-forward years", but only **6** years are evaluable — 200 training trades do
not accumulate until 2021. The literal count (5) is applied here. A proportional
reading (5/8 = 62.5%) would pass 4/6 = 66.7%. The stricter literal reading is
used because softening a gate after seeing the result is the specific error this
lane was designed to avoid.

## The hypothesis was wrong — ablation

| feature set | delta | net/DD | corr | years+ |
|---|---|---|---|---|
| **market only (16)** | **+$1,612** | **19.94** | +0.1256 | 4/6 |
| portfolio only (7) | +$567 | 14.24 | +0.0564 | 3/6 |
| both (25) | +$1,709 | 19.15 | +0.1252 | 4/6 |

Adding portfolio state to market features buys $97 of net and **costs** 0.79 of
net/DD. It contributes nothing incremental.

**Methodological note worth carrying forward:** permutation importance ranked
`pnl_last5`, `dd_from_peak` and `pnl_last20` in the top five features, and the
portfolio block held 27% of total importance. That is importance being *shared
among correlated features*, not incremental value. **The ablation is the test;
the importance table is not.** Reading only the importance table would have
produced a confident and wrong conclusion.

## What the signal actually is

| score quintile | n | mean $ | net | win rate |
|---|---|---|---|---|
| Q1 | 343 | +0.649 | +$222 | 44.3% |
| Q2 | 342 | +0.541 | +$185 | 41.2% |
| Q3 | 343 | +3.768 | +$1,293 | 45.8% |
| Q4 | 342 | +4.199 | +$1,436 | 45.6% |
| Q5 | 343 | +5.672 | +$1,946 | 50.7% |

Monotone: 8.7x spread in mean P&L, win rate 44.3% -> 50.7%.

**Q1 and Q2 are not losing trades. They are near-zero winners (+$0.6/trade).**

That single fact explains every failed veto in this repository, including
`v6-causal-ml-veto-v1` (PF 1.177 -> 1.221 while net fell $303.59 -> $293.99) and
all four of my own XAUUSD lanes. A veto on a positive-expectancy population
removes expectancy, so PF rises and net falls. Sizing underweights it instead, so
net rises.

**The model can identify low-expectancy trades. It cannot identify losing trades.**
Any future lane here should be a sizing policy, not a filter.

## Year detail (T3 sizing, market features)

| year | V60 base | sized | delta | corr |
|---|---|---|---|---|
| 2021 | $258 | $236 | −$23 | +0.012 |
| 2022 | −$20 | −$115 | **−$96** | **−0.169** |
| 2023 | $534 | $686 | +$152 | +0.157 |
| 2024 | $827 | $929 | +$102 | +0.045 |
| 2025 | $1,791 | $2,334 | +$542 | +0.096 |
| 2026 | $1,691 | $2,659 | **+$969** | **+0.181** |

The two failing years are the earliest, when training data was thinnest (~400
prior trades), and the correlation is strongest in the most recent year. That is
the opposite of the overfitting signature, which decays out of sample. It is not
proof — a longer record could still turn — but it is the reason this negative is
recorded rather than discarded.

## Fragility

- 90% of the +$1,612 comes from the top 5% of trades by absolute gain.
- V60 itself is equally tail-carried: removing its top 5% winners leaves $142 of
  $5,082.
- Removing V60's top 5% winners, the overlay still adds **+$151 on that $142
  residual** — so it is not purely re-riding the same tail.

## Defect found and fixed during the lane

`R1_NATIVE_POSITION` records no `risk_usd` — 444 of 444 rows NaN. The first
feature build propagated that into the open-risk aggregate and silently dropped
**35% of the book, including 83% of R1**, the most profitable sleeve (PF 2.03,
52% of all profit). The dropped trades had *higher* mean P&L ($3.38 vs $2.07), so
the model would have trained on a biased subset. Fixed with a nansum and by
removing `risk_usd` as a per-trade feature; coverage went 65.1% -> 100%. The
portfolio-state block only came alive after the fix (`open_positions` max 3 -> 9).

## Benchmarks

| variant | net | maxDD | net/DD |
|---|---|---|---|
| V60 as deployed (scored set) | $5,082 | $298 | 17.05 |
| trivial: drop V8 + V25 | $4,999 | $279 | 17.91 |
| **T3 sizing, market features** | **$6,694** | — | **19.94** |

Note V8_RETEST_HEALTH (204 trades, PF 1.04, $18 net) and V25_CHOP (111 trades,
PF 1.10, $32) contribute 15% of trade count for 0.9% of profit — but dropping
them is roughly neutral, not free money, and the yearly deltas alternate sign.

## V2: the diagnosed fixes were tried and did not work

V1's gate-4 failure was diagnosed as thin training data in 2021-2022, plus two
omissions. Both were addressed:

- **sleeve identity** — the model saw only `is_core`, though sleeve quality runs
  from PF 1.04 (V8) to 2.03 (R1). Added as a causally target-encoded mean over
  prior trades, shrunk toward the global mean by sample size.
- **confidence shrinkage** — the policy sized as hard on 400 training trades as
  on 1,500. The multiplier is now shrunk toward flat by sqrt(n_train / 1500).

| variant | net | net/DD | years+ |
|---|---|---|---|
| V1 reproduction | $6,408 | 19.26 | 4/6 |
| + sleeve identity | $6,555 | 18.39 | 4/6 |
| + shrinkage only | $6,368 | 19.38 | 4/6 |
| V2: both | $6,529 | 18.68 | 4/6 |

Shrinkage worked on the diagnosed symptom — 2022 improved from −$96 to −$32 —
but no variant reached 5 of 6 years.

A band x shrinkage sweep (5 widths x 2 shrinkage levels) then confirmed the
limit:

| band | 2021 delta | 2022 delta |
|---|---|---|
| (0.9, 1.1) | −$1 | −$4 |
| (0.7, 1.3) | −$4 | −$13 |
| (0.5, 1.5) | −$7 | −$21 |

**2021 and 2022 are negative at every band width and every shrinkage level.**
Narrowing the ramp shrinks the loss toward zero but never changes its sign.
**0 of 32 total configurations passed all four gates.**

### Why no band can ever work — this is algebra, not a sweep result

The per-year deltas are exactly linear in band half-width (2025: +86, +172, +258,
+344, +430 — steps of precisely 86; 2026: steps of precisely 75). That is forced,
because the multiplier is an affine function of score rank:

```
delta_year  =  width  x  SUM_i ( pnl_i  x  (rank_i - mean_rank) )
```

The sum is a fixed per-year quantity — the covariance between the model's ranking
and realised P&L in that year. Band width is a positive scalar multiplying it.
**A positive scalar cannot change a sign.** So if a year's score/P&L covariance is
negative, every band width loses money in that year, and the sweep could not have
found otherwise. Running it at five widths was redundant; one width plus the
linearity determines all of them.

This converts gate 4 from a tuning failure into a structural one: the only way to
fix 2021 and 2022 is to change the **ranking**, not the policy applied to it.
V2's sleeve-identity variant was an attempt at exactly that — a better ranking,
not a gentler policy — and it also came in at 4/6, with net/DD *falling* 19.26 ->
18.39. That is the evidence against the remaining structural idea (per-sleeve
models): a per-sleeve model is a higher-variance version of sleeve encoding,
fitted on ~200 trades per sleeve instead of 1,500 pooled, so it is very unlikely
to rank better where pooled encoding already ranked worse.

## Search budget, declared

32 configurations were evaluated on 1,713 trades: 3 targets x 6 policies, one
ablation, sleeve identity, confidence shrinkage, and 5 bands x 2 shrinkage levels.
That is already enough search that a marginal pass would not be credible. The lane
stops here rather than continuing until something clears — which is the failure
mode documented across this repository at a measured cost of 0.3-0.6 PF per layer
of hindsight.

## What would change the verdict

Forward evidence only. The overlay needs to improve in 2027 and beyond, on data
that did not exist when it was fitted. Nothing in the historical record can settle
a 4-of-6 consistency failure, and no further search of this record should be
treated as if it could.
