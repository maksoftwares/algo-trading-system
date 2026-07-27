# EURUSD Neutral CFTC participant-flow preregistration

Frozen: 2026-07-27 18:20 UTC

Campaign: `eurusd-neutral-cot-flow-v1`

## Hypothesis

Fresh changes in the disclosed CME Euro FX positions of leveraged funds,
asset managers, and dealer intermediaries may contain causal directional
information not present in retail spot prices. A simple participant-flow
specialist will trade the first eligible Neutral 00:00 UTC opening after
the report becomes conservatively usable.

The mechanism is intentionally minimal. Leveraged-money and asset-manager
net-position changes vote directly in EURUSD orientation. Dealer inventory
change votes inversely because dealers intermediate the other participants'
flow. A two-of-three majority determines direction.

This is not a level-extreme or H4 failed-break reversal. It is a new test
of whether weekly institutional flow can choose the hindsight oracle's
future-winning midnight side.

All archived EURUSD history has already been inspected. Annual windows are
chronological falsification, not pristine out-of-sample evidence.

## Official source and availability

Source: CFTC Traders in Financial Futures, futures-only, `EURO FX -
CHICAGO MERCANTILE EXCHANGE`, market code `099741`.

The CFTC states that COT data normally describe Tuesday positions and are
published Friday at 15:30 Eastern. The archive report date is not treated
as its availability date.

To avoid historical-release leakage:

1. A normal report becomes usable only at 00:00 UTC eight calendar days
   after its report date.
2. Report rows affected by the 2018-2019 federal shutdown, the 2023 ION
   interruption, and the 2025 federal shutdown are excluded entirely.
3. Weekly changes are calculated only after those exclusions, so an
   unpublished intermediate row cannot enter a change feature.
4. A report may create a signal only during the five calendar days after
   conservative availability.

Official references:

- https://www.cftc.gov/MarketReports/CommitmentsofTraders/AbouttheCOTReports/index.htm
- https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm
- https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalSpecialAnnouncements/index.htm

The eleven official annual archives from 2016 through 2026 are individually
SHA-256 pinned in the frozen configuration.

## Frozen signal

For each admissible COT report:

1. Calculate participant net position as long contracts minus short
   contracts, divided by current open interest.
2. Calculate its change from the preceding admissible report.
3. Leveraged-money vote is the sign of its change.
4. Asset-manager vote is the sign of its change.
5. Dealer vote is the negative sign of its change.
6. All three changes must be finite and nonzero.
7. Vote sum of at least +1 establishes a long direction; vote sum of at
   most -1 establishes a short direction.
8. Starting at conservative availability, select only the first Neutral
   00:00 UTC candidate within five calendar days.
9. At most one trade is permitted per COT report and UTC date.

No COT threshold, z-score, price confirmation, model, future ranking, or
oracle label is used to create the signal.

## Outcome-blind census

Before inspecting target, stop, P&L, or oracle membership:

- 519 COT rows remained after interruption exclusions;
- 518 had three valid participant-flow votes;
- 655 Neutral 00:00 candidates existed;
- 241 reports found an eligible first Neutral opening;
- 126 trades were long and 115 were short;
- annual counts were 30, 41, 35, 33, 28, 31, 28, and 15 from 2019 through
  2026 H1.

The frozen capacity requirement is at least 220 total candidates, 20 in
each full forward year, and 10 in 2026 H1.

## Execution

- fixed 4-pip risk;
- 1.50R target;
- 12-hour maximum hold;
- exact bid/ask execution;
- 0.70-pip minimum retail spread;
- 0.10-pip adverse slippage per side;
- stop first when an M5 bar touches both stop and target;
- one open position and one trade per UTC date;
- 0.25 portfolio-R per position.

## Evaluation and rejection

Development is 2019-2022. Frozen chronological windows are 2023, 2024,
2025, and 2026 H1.

Development and every forward window must reach the frozen sample,
45%-55% win rate, 1.35-1.75 payoff, PF 1.10, and positive-expectancy
gates. Overall maximum drawdown must not exceed 30R. Net R must remain
positive after an extra half-pip round trip and after removing the largest
5% of winners.

Behavioral admission additionally requires at least 25% exact
oracle-match precision, 2% exact recall, and 25% same-side precision within
15 minutes. Oracle rows are evaluation-only and are loaded only after
candidate direction and price-path outcomes are complete.

Any failure rejects the expert. No post-outcome participant subset,
direction inversion, lag, freshness window, entry time, or gate repair is
permitted.
