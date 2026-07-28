# Claude V60 Portfolio-State ML V1 — Result

Decision: **CLAUDE_V60_SIZING_OVERLAY_V3_EFFECT_SIGNIFICANT_P0006_PREREG_GATE4_FAILS_BY_INSUFFICIENT_POWER_FORWARD_TEST_REQUIRED**

(V1 token, superseded: `CLAUDE_V60_PORTFOLIO_STATE_ML_V1_GATE_FAIL_QUARANTINED_STRONG_SIGNAL_RECORDED`)

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

## V3: gate 4 was mis-specified — it cannot tell "no edge" from "negative edge"

Thirty-two configurations tested *policies*. None tested whether the gate-4
failure was **real**. It is not.

Gate 4 counts the **sign** of each year's delta with no tolerance, so a year in
which the model has genuinely zero edge fails it on a coin flip. Permuting the
ranks within each year (the exact null "this year's ranking carries no
information") gives:

| year | delta | null SD | z | perm p | verdict |
|---|---|---|---|---|---|
| 2021 | −$6 | $32 | −0.37 | **0.710** | no signal |
| 2022 | −$13 | $31 | −0.62 | **0.543** | no signal |
| 2023 | +$70 | $52 | 1.84 | 0.065 | marginal |
| 2024 | +$120 | $85 | 1.59 | 0.112 | not significant |
| 2025 | +$287 | $134 | 2.12 | **0.032** | significant |
| 2026 | +$401 | $198 | 2.04 | **0.037** | significant |

**The two years that fail gate 4 are the two years in which the model has no
measurable edge at all.** Their deltas are a fifth of a standard deviation from
zero. With two zero-edge years, a model with a *genuinely perfect* recent-era
edge passes a sign-counting gate with probability only ~0.5^2 = 25%. Gate 4 was
therefore ~75% likely to fail on merit-neutral grounds before any model was fit.
That is a power defect in the gate, not evidence against the overlay.

### Bagging: the variance fix worked, and confirmed the years are genuinely flat

The algebra says only a better ranking can change a year's sign. A single model
on ~400 trades is high-variance, so the ranking was bagged over bootstrap
resamples of the training window (varying `random_state` alone does nothing here
— at these sample sizes sklearn's early stopping is off and the binning subsample
never triggers, so the seeds return identical models).

| variant | net | net/DD | years+ | 2021 | 2022 | gates passed |
|---|---|---|---|---|---|---|
| single model (deterministic) | $5,940 | 18.66 | 4/6 | −6 | −13 | 0 |
| bagged x5 | $5,948 ± 142 | 19.32 ± 1.10 | 4–5 | −6 ± 6 | −28 ± 15 | **2 of 10 seeds** |
| bagged x15 | $5,998 ± 95 | 19.58 ± 0.87 | 4–4 | −7 ± 4 | −29 ± 9 | 0 of 10 |
| bagged x40 | $5,975 ± 60 | 19.29 ± 0.36 | 4–4 | −6 ± 3 | −27 ± 5 | 0 of 10 |

One seed of bagged x5 passed all four gates. It survives re-randomisation in only
**2 of 10 seeds**, and its 2021 delta was exactly +$0 — a knife-edge. It is a
lucky seed and is recorded as such, not claimed.

The instructive part: **more bagging makes gate 4 fail more reliably.** Estimator
noise falls (net/DD spread 1.10 → 0.36) and the 2021/2022 deltas tighten onto a
small negative number. Better estimation does not rescue those years; it reveals
that the true effect there is flat, which is exactly what the permutation test
says independently.

### The aggregate test gate 4 was reaching for

Permuting ranks within every year simultaneously (respecting the block structure,
since ranks are formed per year):

```
pooled effect: observed +$884, null SD $262, z 3.37, two-sided p 0.0006
years significantly negative at p<0.05: NONE
```

So on the substance: **the overlay's effect is real (p = 0.0006), no year is
significantly negative, and the two gate-4 failures are zero-edge years.**

Headline figures, bagged x40, averaged over 10 seeds — more conservative and far
more stable than the single-model +32%:

| | net | net/DD | green |
|---|---|---|---|
| V60 as deployed | $5,082 | 17.05 | 63.6% |
| trivial bar (drop V8+V25) | $4,999 | 17.91 | — |
| **bagged sizing overlay** | **$5,975 ± 60 (+17.6%)** | **19.29 ± 0.36** | 63.6% |

**Honesty constraint, stated plainly:** the preregistered gate 4 still FAILS, at
4 of 6 years, in 10 of 10 seeds. "No year significantly negative and pooled
effect significant" is a better-specified criterion, but it was written *after*
seeing the result, so it is weaker evidence than the gate it replaces. It does
not convert this into a preregistered pass. What it does establish is that the
failure has a named, measured cause — insufficient gate power on zero-edge years
— rather than being evidence the overlay is harmful.

## V4: a look-ahead was found in the sizing map, removed, and the result improved

Self-audit before handing the lane to review found that V1-V3 built the
multiplier from `scores.rank(pct=True)` over the **whole test year**, normalised
by `raw / raw.mean()` over the same year. A January trade was therefore ranked
against the following December's trades. No P&L is involved so it is not outcome
leakage, but the policy was not implementable live, and it is the same class of
defect as the fixed dev-era percentile threshold that faked an alpha decay
earlier in this research.

Three mappings on identical model scores, 5 seeds each:

| mapping | net | net/DD | years+ | mean mult | gates |
|---|---|---|---|---|---|
| A within-year rank (**not causal**) | $6,051 | 19.37 | 4/6 | 1.000 | 0/5 seeds |
| B train-distribution (causal) | $6,059 | 18.50 | 4–5/6 | 1.006 | 1/5 seeds |
| **C expanding OOS (causal)** | **$6,311** | 19.10 | 4–5/6 | 1.017 | 2/5 seeds |

B fixes the map at model-fit time; C ranks each trade against every previously
scored out-of-sample trade, appending only after use. Both are implementable in
real time. The normaliser becomes the constant `(lo+hi)/2`, which is the mean of
a uniform rank map, so no test-set quantity is consulted.

Pooled permutation test on C: **observed +$1,110, null SD $264, z 4.21,
p < 0.0001** — stronger than the non-causal version (z 3.37).

**A spurious effect disappears when look-ahead is removed. This one got bigger.**
That is the single most reassuring result in the lane.

Per-year deltas are unchanged in character: 2021 −$4 and 2022 −$22 remain flat
to slightly negative under every mapping, consistent with the zero-edge finding.

Caveat carried forward: mean multiplier under C is 1.017, so the book runs 1.7%
larger on average. Naive 1.017x leverage on the baseline would yield ~$5,168 of
the $6,311, so leverage explains roughly $86 of the $1,229 gain — but the overlay
is not exactly size-neutral and any deployment must normalise it to mean 1.0.

## What would change the verdict

Forward evidence only. The overlay needs to improve in 2027 and beyond, on data
that did not exist when it was fitted. Nothing in the historical record can settle
a 4-of-6 consistency failure, and no further search of this record should be
treated as if it could.
