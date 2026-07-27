# EURUSD Regime 1 Neutral CFTC participant-flow verdict

Date: 2026-07-27

Decision: `REJECTED_NEUTRAL_COT_FLOW_V1`

## Question tested

Can newly disclosed CME Euro FX positioning changes from leveraged funds,
asset managers, and dealer intermediaries causally choose the
future-winning direction at the Neutral oracle's midnight cluster?

This campaign used a genuinely different information class from the prior
spot-price, tick, DXY, Treasury, and cross-pair experiments. It contained
no fitted model, level threshold, z-score, price confirmation, or
post-outcome participant selection.

## Official source and causal-release control

The source was the CFTC Traders in Financial Futures futures-only report
for `EURO FX - CHICAGO MERCANTILE EXCHANGE`, market code `099741`.

The [CFTC report description](https://www.cftc.gov/MarketReports/CommitmentsofTraders/AbouttheCOTReports/index.htm)
states that reports normally describe Tuesday positions and are released
Friday at 15:30 Eastern. The archive's report date was therefore never
treated as an availability date.

The rule used an eight-calendar-day lag to 00:00 UTC. Rows affected by the
2018-2019 federal shutdown, the 2023 ION reporting interruption, and the
2025 federal shutdown were excluded before weekly changes were calculated.
Those interruptions are documented in the
[CFTC historical special announcements](https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalSpecialAnnouncements/index.htm).

Eleven annual archives from 2016 through 2026 were independently
SHA-256 pinned. After exclusions, 519 Euro FX reports remained.

## Frozen rule

For each admissible report:

1. Participant net position was long minus short, divided by current open
   interest.
2. Weekly change was calculated against the preceding admissible report.
3. Leveraged-money and asset-manager changes voted directly in EURUSD
   orientation.
4. Dealer inventory change voted inversely.
5. All three votes had to be finite and nonzero.
6. A simple two-of-three majority fixed direction.
7. Only the first Neutral 00:00 UTC candidate in the five days after
   conservative availability could trade.
8. At most one trade was allowed per COT report and UTC date.

Execution used fixed 4-pip risk, a 1.50R target, a 12-hour maximum hold,
exact bid/ask prices, a 0.70-pip minimum spread, 0.10-pip adverse slippage
per side, and stop-first resolution of ambiguous M5 bars.

## Outcome-blind census

Before target, stop, P&L, or oracle membership inspection:

- 519 admissible COT reports remained;
- 518 had three valid nonzero participant-flow votes;
- 655 Neutral midnight candidates existed;
- 241 reports found an eligible first Neutral opening;
- 126 candidates were long and 115 were short;
- annual counts were 30, 41, 35, 33, 28, 31, 28, and 15 from 2019 through
  2026 H1.

The frozen capacity and direction-balance checks passed.

## Development result

| Window | Trades | Win rate | Payoff | PF | Net | Max DD | Extra 0.5-pip net |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2019-2022 | 139 | 34.53% | 1.439 | 0.759 | -22.48R | 23.60R | -39.85R |

Development failed the win-rate, PF, expectancy, and cost-stress gates.
No participant, sign, lag, or freshness rule was changed.

## Chronological forward result

| Window | Trades | Win rate | Payoff | PF | Net | Exact precision | Exact recall | 15m precision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 28 | 35.71% | 1.439 | 0.799 | -3.70R | 35.71% | 3.33% | 50.00% |
| 2024 | 31 | 32.26% | 1.439 | 0.685 | -6.78R | 32.26% | 3.80% | 41.94% |
| 2025 | 28 | 46.43% | 1.439 | 1.247 | +3.80R | 46.43% | 4.06% | 64.29% |
| 2026 H1 | 15 | 13.33% | 1.439 | 0.221 | -10.38R | 13.33% | 1.25% | 26.67% |
| Overall | 102 | 34.31% | 1.439 | 0.752 | -17.05R | 34.31% | 3.36% | 48.04% |

Only 2025 passed the frozen annual economic gate, including the extra-cost
stress at +0.30R. It did not persist: 2026 H1 produced two winners and
thirteen losers, including eleven consecutive losses after January 29.

The latest six-month result is 15 trades, 13.33% wins, 1.439 payoff,
PF 0.221, -10.38R net, and 11.28R maximum drawdown. At the frozen 0.25
portfolio-R allocation, net performance was -2.59 portfolio-R.

## Failure anatomy

| Frozen vote group | Trades | Win rate | Net |
|---|---:|---:|---:|
| Unanimous short, sum -3 | 48 | 31.25% | -11.70R |
| Majority short, sum -1 | 67 | 38.81% | -3.68R |
| Majority long, sum +1 | 62 | 30.65% | -16.05R |
| Unanimous long, sum +3 | 64 | 35.94% | -8.10R |

Every frozen vote-strength and direction group was negative. The failure
cannot be honestly reframed as one bad side or weak-majority contamination.
Selecting the observed majority-short subset would be post-outcome
overfitting and would still be negative.

Across the forward period, all 35 exact oracle members won +51.63R while
all 67 nonmembers lost -68.68R. As established by the prior UTC-open
campaign, this identity follows mechanically from the oracle starting its
future scan at midnight. Economic win rate therefore equals exact
same-entry, same-side precision.

The CFTC flow improved exact precision from the prior pre-open price vote's
31.11% to 34.31%, but remained below the approximately 41.0% break-even
requirement.

## Robustness

Across all history, the rule produced 241 trades, 34.44% wins, PF 0.756,
and -39.53R, with 40.20R maximum drawdown. Adding another half pip round
trip reduced net to -69.65R and PF to 0.617. Removing the largest 5% of
winners reduced net to -58.70R and PF to 0.638.

## Verdict

Official weekly CFTC Euro FX participant flow does not solve Regime 1 at
the requested 4-pip/1.50R lifecycle. One good year is contradicted by
negative development, two other negative full forward years, and a severe
latest-six-month collapse.

Post-outcome participant removal, direction inversion, shorter lag, wider
freshness, or conditioning on the observed 2025 state is prohibited. This
exact weekly participant-flow route is closed without retuning.

The missing information is more timely and granular than weekly aggregate
position disclosure: executed EUR futures flow, multi-venue order-book
imbalance, point-in-time macroeconomic consensus surprises, an options
surface, or a genuinely untouched prospective period. Regime 1 remains
`CASH`.

## Reproduce

```powershell
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_cot_flow.py
```
