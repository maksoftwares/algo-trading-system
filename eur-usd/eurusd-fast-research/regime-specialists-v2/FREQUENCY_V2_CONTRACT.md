# EURUSD Frequency V2 Research Contract

## Objective

Increase the Capital.com EURUSD strategy from the frozen 62-trade control to
at least one completed trade per active broker trading day over the
2024-07-01 through 2026-07-01 evaluation window.

The frozen control remains unchanged:

- 62 completed trades;
- 53.23% win rate;
- 1.45 MT5 profit factor;
- positive net profit;
- 0.11% maximal balance drawdown at 0.01 lots.

## Architecture

Frequency must come from a mutually exclusive, regime-routed portfolio of
independent specialists. It must not come from repeatedly loosening the
frozen Asia/London chop rule. The router may own at most one EURUSD position
and may complete at most two trades on an active trading day.

The research families are:

1. trend continuation and pullback resumption;
2. compression expansion;
3. chop mean reversion;
4. session range expansion and failed expansion.

Each trade is assigned to exactly one H4 regime at signal time. Unsafe spread
or insufficient-history states are not tradable regimes.

## Data partitions

- development: 2016-07-01 through 2022-06-30;
- validation: 2022-07-01 through 2024-06-30;
- adaptive demo replication: 2024-07-01 through 2026-06-30.

The final interval is not described as untouched because earlier EURUSD
research has already inspected it. Any result from that interval is
demo-candidate evidence only and requires prospective shadow/demo evidence.

## Frozen portfolio gates

The portfolio is eligible for a Capital.com real-tick replication only when
the validation interval passes all of the following:

- completed trades / active trading days >= 1.00;
- profit factor >= 1.30;
- win rate >= 52.00%;
- net expectancy > 0 after native spread and declared slippage;
- maximal drawdown <= 25R;
- at least 55% of active calendar months are profitable;
- profit factor after removing the best 5% of trades >= 1.00;
- no more than two completed trades per trading day;
- at least three distinct specialist/regime sleeves contribute trades.

The adaptive demo target is the frozen control's quality:

- profit factor target: 1.45, with 1.30 as the minimum research floor;
- win-rate target: 53.23%, with 52.00% as the minimum floor;
- positive expectancy and controlled drawdown.

Failure to reach one trade per active day is a frequency failure. Reaching
frequency by accepting PF below 1.30 is a quality failure. Neither is
presented as demo-ready.

## Recorded outcome and adaptive fallback

The strict regime-specialist contract above failed. Its frozen portfolio
passed 2022-2024 validation but returned PF 0.68 in the 2024-2026 adaptive
exam. It was not advanced to MT5 replication.

After that failure, research moved to an explicitly adaptive controlled-demo
fallback. This is not represented as a pass of the original strict contract.
The fallback keeps the user's average-frequency objective but replaces the
two-trades-per-day restriction with a maximum of two concurrent positions:
one per independently owned sleeve.

The adaptive fallback gates are:

- completed trades / active broker dates >= 1.00;
- broker-realized portfolio PF >= 1.30;
- win rate >= 52%;
- maximum closed-trade drawdown <= 1% of $10,000;
- at least 55% positive active months;
- PF after removing the best 5% of trades >= 1.00;
- maximum concurrent positions <= 2;
- shadow/demo only, never live.

These gates were declared as the packaging decision after the strict campaign
failed and after the period had already been inspected. They are therefore
adaptive demo controls, not untouched confirmation.
