# A3 ML Shared-Account Portfolio Replay Preregistration

Date: 2026-07-13

## Purpose

Measure the frozen R1/R2 specialists as one XAUUSD account before adding frequency or allowing ML to influence execution. The replay is historical research only. It cannot authorize Python predictions, EA consumption, demo orders, or live orders.

## Frozen Inputs

- Candidate source: `A3_ML_REGIME_PORTFOLIO_CONTINUOUS_10Y_20260713_MT5.json`.
- Period: `2016-07-01 00:00:00` through `2026-06-30 23:59:59`.
- Specialists: `r1_box_clean_strict_uptrend` and `r2_pullback_short_h1_confirm` only.
- Lot size: source-native fixed `0.01` lots.
- Initial shared-account balance: `$10,000`.
- Gold contract size: `100` ounces per lot.
- Assumed research leverage: `20:1`.
- MT5 source P/L already includes modeled spread; stress deducts another `$0.30` per accepted trade.
- Historical M5 bid/ask bars mark open equity. MT5 bid bars with spread are converted to approximate ask bars where native bid/ask fields are unavailable.

## Causal Admission

Candidates are ordered by entry timestamp, source name, and entry deal. Admission may use only information available at entry: current realized balance, current marked equity, initial stop risk, open positions, direction, daily realized P/L, and assumed margin. Future exit or P/L may not influence admission.

Two profiles are frozen:

1. `unconstrained_shared_baseline`: accepts every frozen candidate and measures natural overlap.
2. `risk_controlled_shared_account`: maximum three concurrent positions, maximum `1.0%` initial risk per trade, maximum `2.0%` total open initial risk, maximum `1.5%` same-direction initial risk, maximum `50%` assumed margin utilization, and a `2.0%` realized daily-loss entry halt.

The frequency target is descriptive, not an admission override. The replay must never create trades or relax specialist gates to reach two trades per day.

## Equity Method

- Realized balance changes only when an accepted source trade exits.
- Open positions are marked on M5 liquidation-side prices.
- Intrabar equity evaluates coherent low-price and high-price portfolio scenarios and uses the adverse path for a conservative bar estimate.
- Recent MT5 bar spread is treated as constant across each bar when only one spread field is available.
- Shared-account equity drawdown is compared with each isolated specialist's MT5 maximal equity drawdown. Failure to calibrate within `0.75x` to `1.35x` blocks any drawdown conclusion.
- The final conservative drawdown is the maximum of shared replay drawdown and the largest isolated MT5 component equity drawdown.

## Locked Gates

- Source trade count and baseline net P/L reconcile exactly with the frozen component ledgers.
- Every completed trade joins exactly one successful entry order and initial stop.
- Specialist magic numbers are unique for one-account ownership.
- Each isolated component equity replay calibrates within `0.75x` to `1.35x` of MT5 maximal equity drawdown.
- Ten-year stress profit factor is at least `1.40`.
- Conservative shared-account equity drawdown is at most `15%` of the `$10,000` initial balance.
- At least `75%` of non-overlapping six-month blocks have nonnegative stressed P/L.
- Risk-controlled replay never breaches its frozen concurrent-risk or margin limits at admission.
- Research, Python-demo, EA-consumption, and broker-action authorizations remain false.

## Required Reporting

- accepted and rejected candidates with reason codes;
- realized and stressed P/L;
- closed-balance and M5 equity drawdown in USD and percent;
- maximum concurrent positions, long/short overlap, initial risk, notional, and assumed margin utilization;
- trades per market day and per active day;
- positive-day share, worst day, worst week, and worst month;
- three-month, six-month, five-year, and ten-year windows;
- six-month stability;
- capital required to keep the observed fixed-lot drawdown at or below `10%` and `15%`;
- source hashes, bar hashes, magic-number audit, limitations, gates, and authorization boundary.

## Decision Rule

Any failed locked gate yields `RESEARCH_GATES_FAIL`. Frequency below two trades per day is a research gap, not permission to force entries. A passing replay would authorize only the next reviewed research stage, not demo or live execution.
