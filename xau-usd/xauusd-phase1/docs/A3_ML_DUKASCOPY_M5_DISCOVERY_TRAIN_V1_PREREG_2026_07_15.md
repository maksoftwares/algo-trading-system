# A3 ML Dukascopy M5 Discovery Train V1 Preregistration

Date: `2026-07-15`

Status: `LOCKED_BEFORE_TRAIN_OUTCOMES`

## Objective

Find at most one mechanically defined XAUUSD M5 strategy profile that combines positive old-period expectancy with enough opportunity coverage to contribute materially toward a future one-to-two-trades-per-day specialist portfolio.

This stage reads only the training window from `2018-07-01` through `2021-06-30`. Validation, test, and the new `2024-07` through `2026-06` holdout are forbidden in this stage.

## Frozen Families

Twelve profiles are declared before their outcomes are read:

- trend pullback and M5 EMA20 reclaim;
- continuation breakout of the prior six M5 bars;
- trend-aligned sweep and reclaim of the prior six-bar extreme;
- each pattern with either completed H1 trend or completed H1 plus H4 trend;
- each combination at `1.0R` and `1.5R` reward.

All profiles use a `2.5` M5 ATR stop with a `350`-point floor and `1,800`-point ceiling. Candidate decisions occur only after the M5 signal bar closes. H1 and H4 indicators use only completed higher-timeframe bars.

## Execution Model

- verified Dukascopy bid/ask ticks;
- fixed `0.01` lot;
- actual bid/ask entry and stop/target resolution;
- spread no greater than `75` points;
- spread-to-stop estimate no greater than `0.10R`;
- extra execution stress of `$0.30` per trade;
- holding stress of `$0.35` per 24 hours;
- one open trade per profile, five-minute cooldown, and 12 entries per server day;
- server time frozen to UTC+4.

The `0.10R` ceiling is declared before this campaign's outcomes. It is not a repair of a single winning trade; it permits the ordinary Dukascopy spread range while retaining a hard cost-to-risk limit.

## Train Selection Gates

A profile must pass every gate:

- at least `500` trades;
- at least `0.65` trades per source day;
- at least `1.25` trades per active trade day;
- active-day coverage of at least `35%`;
- stress profit factor at least `1.25`;
- average stress return at least `0.08R`;
- at least `60%` positive active exit months;
- closed-trade drawdown no greater than `45R` and `$250`;
- each direction at least `20%` of trades;
- no single profitable month contributes more than `35%` of total positive monthly profit;
- net remains positive after removing the top 25 winners;
- calendar-month bootstrap `2.5%` average-R bound above zero.

If multiple profiles pass, select exactly one by stress PF descending, then frequency descending, then family ID ascending. If none pass, validation and test remain unopened.

## Interpretation

A train survivor is only permission to freeze one profile for later evaluation. It is not evidence of profitability outside training and grants no prediction, EA, demo, live, or broker authorization.
