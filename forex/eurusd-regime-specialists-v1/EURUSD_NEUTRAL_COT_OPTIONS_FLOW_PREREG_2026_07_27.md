# EURUSD Neutral CFTC options-equivalent flow preregistration

Frozen: 2026-07-27 19:05 UTC

Campaign: `eurusd-neutral-cot-options-flow-v1`

## Hypothesis

Delta-adjusted EUR options exposure may contain directional information
that is absent from both retail spot prices and futures-only participant
positioning. A deterministic specialist will infer participant
options-equivalent net exposure by subtracting each futures-only position
from its same-date futures-and-options-combined position.

The weekly changes of leveraged funds, asset managers, and dealer
intermediaries will vote on the first eligible Neutral 00:00 UTC opening
after conservative publication availability.

This is not CME CVOL or strike-level risk reversal. It is a free official
aggregate options-delta source. It changes 112 of the 241 directions
selected by the rejected futures-only CFTC flow campaign and is therefore
a materially distinct direction signal.

All archived EURUSD history has already been inspected. Annual windows are
chronological falsification, not pristine out-of-sample evidence.

## Official source and availability

Sources:

- CFTC Traders in Financial Futures, futures-only;
- CFTC Traders in Financial Futures, futures-and-options-combined;
- market `EURO FX - CHICAGO MERCANTILE EXCHANGE`, code `099741`.

The CFTC publishes both formats in annual compressed archives. The CFTC
also explains that combined option positions are delta-adjusted, which is
why combined long and short totals can differ from open interest by one
contract.

Official references:

- https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalCompressed/index.htm
- https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm
- https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalSpecialAnnouncements/index.htm

The eleven futures-only and eleven combined archives from 2016 through
2026 are individually SHA-256 pinned.

Availability control is inherited conceptually from the prior CFTC
campaign:

1. Inner-join only exact same-date futures-only and combined rows.
2. Exclude reports affected by the 2018-2019 federal shutdown, the 2023
   ION interruption, and the 2025 federal shutdown.
3. Calculate weekly changes only after exclusions.
4. Make a paired report usable at 00:00 UTC eight calendar days after its
   report date.
5. Permit a signal only during the following five calendar days.

## Frozen signal

For participant `p` and report `t`:

```text
options_equivalent_net[p,t]
  = combined_long[p,t] - combined_short[p,t]
  - futures_long[p,t] + futures_short[p,t]
```

1. Calculate the week-over-week change in options-equivalent net exposure.
2. Leveraged-money vote is the sign of its change.
3. Asset-manager vote is the sign of its change.
4. Dealer vote is the negative sign of its change.
5. All three changes must be finite and nonzero.
6. Vote sum of at least +1 fixes long; at most -1 fixes short.
7. Select only the first Neutral 00:00 UTC candidate within five calendar
   days of conservative availability.
8. At most one trade is permitted per paired COT report and UTC date.

No strike proxy, volatility threshold, z-score, price confirmation,
participant selection, model, future ranking, or oracle label creates the
signal.

## Outcome-blind census

Before target, stop, P&L, or oracle membership inspection:

- 519 paired reports remained after date and interruption controls;
- 518 had three valid nonzero options-flow votes;
- 655 Neutral 00:00 candidates existed;
- 241 reports found an eligible first Neutral opening;
- 122 trades were long and 119 were short;
- 112 directions, or 46.47%, differed from the prior futures-only flow
  rule on the same candidate dates;
- annual counts were 30, 41, 35, 33, 28, 31, 28, and 15 from 2019 through
  2026 H1.

The capacity requirement is at least 220 trades, 20 in each full forward
year, 10 in 2026 H1, and 100 directions different from the futures-only
campaign.

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
45%-55% win rate, 1.35-1.75 payoff, PF 1.10, and positive expectancy.
Overall maximum drawdown must not exceed 30R. Net R must remain positive
after an extra half-pip round trip and after removing the largest 5% of
winners.

Behavioral admission additionally requires at least 25% exact
oracle-match precision, 2% exact recall, and 25% same-side precision within
15 minutes. Oracle rows are evaluation-only and are loaded only after
candidate direction and price-path outcomes are complete.

Any failure rejects the expert. No post-outcome participant subset,
direction inversion, lag, freshness window, entry time, or vote-strength
repair is permitted.
