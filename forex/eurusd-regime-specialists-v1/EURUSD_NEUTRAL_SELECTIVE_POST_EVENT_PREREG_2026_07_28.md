# EURUSD Neutral selective post-event preregistration

This contract is locked before loading a 2023-2026 forward outcome for this
exact selective rule. The parent post-event campaign's aggregate results were
already known, so this is adaptive research rather than a fresh holdout.

## Hypothesis

The unconditional post-event drive failed because a 1.5R trade needs roughly
40% wins before costs, while the rule traded every accepted event. A causal
side-stacked probability model may identify a small subset whose predicted
win probability exceeds the cost-aware 0.42 threshold. All other candidates
remain cash; frequency is not a target.

## Frozen source and features

The source is the 495-candidate, hash-locked N29 post-event census. No candidate
definition, event taxonomy, observation length, stop, target, hold, spread, or
slippage changes.

Each candidate receives 13 features complete at entry:

- side-aligned first-15-minute impulse;
- side-aligned pre-event 15-, 60-, and 240-minute returns;
- own-side structure risk;
- opposite-minus-own risk advantage;
- observation range;
- observation range divided by the prior 288-bar median range;
- event-hour sine and cosine;
- EUR and USD event-cluster flags;
- log-transformed event-cluster size.

Event title and tag are excluded. There is no feature, interaction, clock, or
subgroup search.

## Frozen learner

- Stack LONG and SHORT as separate training rows with shared coefficients.
- Label a side positive only when that side realizes positive R.
- Train once on the 285 candidates and 570 side rows from 2019-2022.
- Require every label's exit to precede 2023.
- Standardize on the training data only.
- Fit one L2 logistic regression with `C=0.1`, `liblinear`, no class weights,
  and random seed 20260728.
- Score both sides of each 2023-2026 candidate.
- Select the higher-probability side, breaking exact ties LONG.
- Trade only if the higher probability is at least 0.42.
- Never refit, recalibrate, lower the threshold, or force a trade.

The training positive rate is 34.91%: 199 positive side rows among 570.

## Forward-outcome-blind selection screen

| Window | Source candidates | Selected | Cash | Selected LONG |
|---|---:|---:|---:|---:|
| 2023 validation | 54 | 11 | 43 | 63.64% |
| 2024 validation | 55 | 5 | 50 | 20.00% |
| 2025 pseudo-OOS | 64 | 9 | 55 | 77.78% |
| 2026 H1 pseudo-OOS | 37 | 3 | 34 | 66.67% |
| Forward total | 210 | 28 | 182 | 60.71% |

The maximum score is 0.4858, the median is 0.3905, and the 90th percentile is
0.4266. The selected candidate manifest SHA-256 is:

`8885005fdc71cbe0332ae61e6dff1eeda790c9f5d22f4409170de93025d18232`

## Admission and structural stop

Every forward window requires at least eight trades before its P&L may be used
for admission. The screen produces only five in 2024 and three in 2026 H1.
This exact version therefore fails capacity before forward P&L.

Had capacity passed, every window would also have required 40-60% wins, a
1.35-1.75 payoff ratio, positive net R, and ticket and daily PF above 1.00.
Forward overall PF would require 1.15, win rate 45-55%, positive cost stress,
positive net after removing the best 5% of winners, and the existing oracle
and drawdown gates.

The threshold will not be lowered after this screen. A lower threshold would
be a separate outcome-blind capacity experiment and could not repair this
version.

## Evidence status

Forward P&L is intentionally unopened because capacity already failed. No
broker action is authorized. Any future historical pass would remain
research-only and require at least 100 new observations and six post-lock
calendar months from 2026-07-29.
