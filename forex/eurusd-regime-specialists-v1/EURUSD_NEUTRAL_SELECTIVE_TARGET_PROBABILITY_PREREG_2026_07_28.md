# EURUSD Neutral selective target-probability preregistration

This contract is being frozen before the first trade-ledger or oracle
evaluation for the exact selective target-probability rule.

## Rationale

The forced direction ranker and the two-venue sign-agreement filter both
failed. The user's relaxation of the four-trades-per-day objective allows the
strategy to address the more fundamental question: is either side's estimated
chance of reaching the 1.5R target high enough to justify a trade?

This is one predeclared model, not a threshold sweep. Historical EURUSD
outcomes have been inspected by earlier campaigns, so all results remain
adaptive research. Within this campaign, however, every inference window is
strictly chronological and its outcomes are forbidden from its fit.

## Frozen model

Each source-complete decision becomes two training rows, one LONG and one
SHORT. The binary label is whether that side hit the 1.5R target first. A
side's label becomes available only at its exit timestamp.

One shared L2 logistic model uses:

- side-aligned 3- and 12-period returns;
- side-aligned EMA gap, anchor gap, close location, room, DXY gap, and quote
  change imbalance;
- Kraken and Binance flow imbalances aligned to the candidate side;
- the absolute Kraken and Binance imbalance magnitudes.

There are exactly 12 features. The model uses `C=0.1`, the `liblinear`
solver, no class balancing, no interaction, no clock feature, and no
probability recalibration.

At the start of each evaluation window, the scaler and model refit on every
side row whose entry and exit are strictly earlier than the window start.
For each new decision:

1. estimate LONG and SHORT target-first probabilities;
2. select the higher probability, mapping an exact tie to LONG;
3. trade only if the higher probability is at least 0.45;
4. otherwise stay in CASH.

The 0.45 hurdle is frozen above the roughly 0.41 break-even win probability
implied by the locked realized payoff. It is not fitted to any subgroup.

## Outcome-blind source census

The parent source contains 532 development decisions on 133 complete Neutral
dates in 2020-2021. Evaluation contains 1,280 possible decisions on 320 dates:
560 in 2022-2023, 248 in 2024, 316 in 2025, and 156 in 2026 H1.

The number of executed decisions cannot be known from source fields alone
because it depends on models fitted only to chronologically prior labels. A
pre-evaluation selection census will be generated and added to the frozen
contract before any selected trade outcome is routed.

### Pre-evaluation selection screen

The chronological fits selected zero of 1,280 evaluation decisions at the
frozen 0.45 hurdle. The overall maximum predicted target-first probability
was 0.431762; the 99th percentile was 0.404727. In 2026 H1, the maximum was
only 0.400222. All 320 source-complete evaluation dates therefore remain in
CASH.

This is a structural no-trade rejection before trade outcomes or oracle
matches. The threshold will not be lowered to create activity. The complete
serialized selection census is pinned by SHA-256
`62d0fe950d86f7642a6f89eb5c605471c17288c73257a5948c0b342d1b22341f`.

## Execution and gates

Execution remains the same executable bid/ask 4-pip-stop, 6-pip-target,
12-hour-hold contract with a 0.7-pip spread floor, 0.1 pip adverse slippage
per side, and stop-first same-bar policy.

Every evaluation window must have at least 20 trades, a 1.35-1.75 payoff,
ticket and daily PF strictly above 1.00, positive expectancy, and conditional
direction accuracy strictly above 50%. Overall PF must be at least 1.15,
exact oracle precision at least 25%, and same-side 15-minute precision at
least 45%.

The strategy must also remain positive with stress PF above 1.00 after an
extra half pip, remain positive after removing the best 5% of winners, and
keep daily portfolio drawdown at or below 20R. The last six months require at
least 20 trades, positive net R, and ticket and daily PF above 1.00. Frequency
otherwise has no gate.

Even a complete historical pass cannot authorize demo execution before 100
new observations and six post-lock months beginning 2026-07-29.
