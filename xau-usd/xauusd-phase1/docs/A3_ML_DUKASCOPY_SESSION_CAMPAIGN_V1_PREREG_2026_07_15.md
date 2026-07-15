# A3 ML Dukascopy Session Campaign V1 Preregistration

Date locked: `2026-07-15`

## Objective

Test a bounded set of intraday XAUUSD specialists designed for materially higher opportunity coverage than the rejected H1 pullback and D1-compression families. The research target is one to two qualified trades per active trading day, not permission to force trades.

The campaign may produce no survivor. A profitable result is accepted only when the train-selected profile remains profitable on untouched chronological validation and test data after observed spread and frozen execution stress.

## Frozen Data

- Verified Dukascopy XAUUSD bid/ask ticks only.
- July 2018 through June 2024, `72` contiguous monthly partitions.
- Signal construction uses causal H1 bid bars from the verified cache.
- Entry and outcome replay uses raw Dukascopy bid/ask ticks.
- UTC timestamps and chronological splits are mandatory.
- No MT5 price history is used for strategy discovery.

## Frozen Sessions

Each profile can emit at most one candidate for each session on an active UTC date:

- London signal bars start at `06:00` or `07:00` UTC.
- New York signal bars start at `12:00` or `13:00` UTC.
- The first qualifying bar consumes that profile/session/date opportunity.
- Maximum theoretical frequency is two trades per profile per active day.

The paired UTC hours deliberately cover seasonal open shifts without using a post-result daylight-saving mask.

## Frozen Indicators

- Wilder-style ATR14 using the repository's established exponentially weighted convention.
- EMA20 and its five-completed-H1-bar slope.
- Signal H1 range between `0.60` and `2.50 ATR`.
- Signal candle body fraction at least `0.35`.
- Prior lookback bars must not span more than three missing market hours beyond the declared lookback.

## Frozen Mechanisms

### Trend-Aligned Breakout

- Lookback is the previous `4` or `8` active H1 bars.
- Long requires a bullish signal close at least `0.05 ATR` above the prior high, close location at least `0.70`, close above EMA20, and nondecreasing five-bar EMA slope.
- Short is symmetric below the prior low with a nonincreasing EMA slope.
- Stop is fixed at `1.0 ATR`.

### Liquidity-Sweep Reversal

- Lookback is the previous `4` or `8` active H1 bars.
- Long requires a downside breach of at least `0.05 ATR`, a bullish close back inside by at least `0.05 ATR`, and close location at least `0.55`.
- Short is symmetric after an upside breach.
- Stop covers the swept signal extreme plus `0.10 ATR`, with a minimum of `0.60 ATR` and maximum of `1.50 ATR`.
- No trend or direction-performance mask is allowed.

## Frozen Profiles

The eight declared profiles are the Cartesian product of:

- mechanism: breakout or sweep reversal;
- lookback: `4` or `8` H1 bars;
- target: `1.5R` or `2.0R`.

No additional profile, parameter, session, direction split, or calendar filter may be introduced after replay begins.

## Frozen Execution

- Entry is the first quote no more than five minutes after the completed signal H1 bar.
- Long enters at Ask and exits on Bid; short enters at Bid and exits on Ask.
- Raw tick order resolves stop versus target.
- Maximum hold is eight hours.
- Fixed size is `0.01` lot.
- Observed spread is embedded.
- Additional execution stress is `$0.30` per trade.
- Holding stress is `$0.35` per 24 hours, applied pro rata.

## Frozen Splits and Selection

- Train: before July 2021.
- Validation: July 2021 through June 2023.
- Test: July 2023 through June 2024.

All eight profiles are replayed, but profile ranking may read train labels only. A profile must pass every train-selection gate before it can be ranked. Rank order is:

1. highest train calendar-month bootstrap lower 2.5% average-R bound;
2. highest train stress profit factor;
3. highest train average stress R;
4. highest train trades per active day;
5. lexical family ID as a deterministic final tie-break.

Only the selected profile may be evaluated on validation and test. Nonselected validation and test metrics must not be exposed in the report.

## Train-Selection Gates

- At least `500` resolved train trades.
- At least `75` train rows in each direction.
- At least `100` train rows in each session.
- At least `0.75` resolved trades per active train day.
- Stress PF at least `1.10`.
- Average stress R at least `0.02`.
- Maximum closed drawdown no more than `35R`.
- At least `50%` positive active exit months.
- Fixed-seed month-bootstrap average-R lower 2.5% bound at least `-0.02`.

## Final Strategy Gates

All must pass:

- At least `250` validation and `120` test trades.
- Required direction and session sample minimums from the machine contract.
- At least `0.75` trades per active day in both validation and test.
- Validation stress PF at least `1.15`; test stress PF at least `1.10`.
- Validation average stress R at least `0.02`; test average stress R nonnegative.
- Test maximum closed drawdown no more than `20R`.
- Positive active exit months at least `55%` in validation and `50%` in test.
- No more than two concurrent positions.
- Test month-bootstrap average-R lower 2.5% bound above zero.

## Decision Classes

- `DUKASCOPY_SESSION_CAMPAIGN_RESEARCH_SURVIVOR`: source quality, train selection, and every final gate pass.
- `DUKASCOPY_SESSION_CAMPAIGN_NO_TRAIN_SURVIVOR`: no profile passes all train-selection gates; validation and test stay suppressed.
- `DUKASCOPY_SESSION_CAMPAIGN_NO_FINAL_SURVIVOR`: a train profile is frozen but fails validation or test.
- `DUKASCOPY_SESSION_CAMPAIGN_INVALID`: source, resolution, identity, or protocol integrity fails.

No result authorizes Python demo prediction, EA consumption, broker action, shared-account sizing, or deployment.
