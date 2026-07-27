# Forex Regime-Specialist Campaign Preregistration — 2026-07-27

Status: `HASH_LOCKED_BEFORE_OUTCOME_INSPECTION`

Boundary: offline research only. This campaign does not authorize MT5, broker, terminal, chart, EA attachment, account, demo, or order actions.

## Objective

Follow the reusable Gold research trajectory without copying Gold thresholds or treating the historical Gold control as deployable evidence:

1. classify orthogonal direction, volatility, and phase states;
2. give each expert exclusive regime ownership;
3. admit experts on standalone chronological evidence;
4. route only independently admitted experts through one shared risk layer;
5. default to cash where no specialist owns the state.

This is a bounded first campaign, not an optimization sweep. Its outcome may legitimately be zero admitted specialists.

## Prior-Research Boundary

The Forex lane already closed price-only geometry, RSI/Bollinger, session conditioning, Tokyo drift, momentum/value, carry, microstructure, volatility-conditioned microstructure, crosses, fixed-spread dislocation, ML, slow daily macro pressure, rates/dollar H4 pullbacks, and FX relative-strength catch-up/dispersion reversal.

This campaign therefore excludes:

- daily ETF or FRED threshold signals;
- H4 EMA pullback/rejection rules;
- lagging-pair catch-up and residual/dispersion reversal;
- session masks chosen from prior P&L;
- any parameter grid or post-outcome threshold edit.

The new mechanism is simultaneous intraday transmission across an official Dollar Index CFD, an official U.S. Treasury Bond CFD, and executable bid/ask FX bars.

## Data and Chronology

- Context: official Dukascopy hourly raw bid/ask tick responses for `DOLLARIDXUSD` and `USTBONDTRUSD`.
- Execution: prepared official Dukascopy M5 bid/ask bars for `EURUSD`, `GBPUSD`, and `USDJPY`.
- Eligible range: `2019-01-02` through `2026-06-30` UTC.
- Design: 2019-01-02 through 2021-12-31.
- Validation: 2022-01-01 through 2024-06-30.
- Adaptive exam: 2024-07-01 through 2026-06-30.
- All three windows are development evidence because the historical archive has already been broadly inspected.
- The inherited EURUSD/USDJPY interval `2024-10-09T23:00Z` through `2024-10-10T01:00Z` is quarantined before outcomes.
- Signals use completed H1 bars only. Entry is the next available M5 executable quote.

## Orthogonal State Classifier

At every completed H1 bar:

### Direction

- `USD_UP`: Dollar Index EMA(24) is above EMA(120) by at least 0.25 Dollar Index ATR(24), Treasury Bond EMA(24) is below EMA(120) by at least 0.25 bond ATR(24), and at least two of EURUSD-down, GBPUSD-down, USDJPY-up agree by their own EMA(24)/EMA(120) sign.
- `USD_DOWN`: the exact inverse.
- Otherwise `NEUTRAL`.

### Volatility

- `SHOCK`: the just-completed H1 true range of the Dollar Index, bond, or selected trading symbol exceeds its causal rolling 95th percentile over the prior 480 H1 observations.
- `COMPRESSED`: the prior completed 12-hour high-low range, normalized by ATR(24), is at or below its causal rolling 60th percentile over the prior 480 observations for both the Dollar Index and selected trading symbol.
- Otherwise `NORMAL`.

### Phase

- `ESTABLISHED`: the same non-neutral direction has persisted for three completed H1 bars.
- `TRANSITION`: direction is non-neutral but not established.
- `UNRESOLVED`: direction is neutral.

Shock dominates every other label and always maps to cash.

## Specialist R1 — USD Trend Synchronization

Owned state: `ESTABLISHED`, `NORMAL`, non-shock `USD_UP` or `USD_DOWN`.

Instrument: `USDJPY`.

Signal:

- `USD_UP`: the just-completed Dollar Index H1 close exceeds the prior completed 24-hour high and USDJPY H1 close exceeds its prior completed 24-hour high.
- `USD_DOWN`: both closes break their prior completed 24-hour lows.
- Treasury confirmation and two-of-three FX breadth are already required by the direction classifier.
- The first signal in an episode is eligible; no repeat entry while the symbol has an open position.

Trade:

- direction follows the USD state;
- stop distance is 1.25 × USDJPY ATR(24) from the executable entry;
- target is 2R;
- maximum hold is 18 completed H1 bars;
- no entry at 21:00, 22:00, or 23:00 UTC.

Mechanism: an established Dollar/rates move that is simultaneously transmitted into USDJPY should persist beyond the confirming close. It is not a lagging-pair catch-up rule.

## Specialist R2 — Cross-Asset Compression Release

Owned state: the just-completed bar transitions out of joint `COMPRESSED` state into a non-neutral, non-shock direction.

Instrument: `GBPUSD`.

Signal:

- the preceding completed H1 bar was jointly compressed in Dollar Index and GBPUSD;
- the just-completed Dollar Index close breaks its prior completed 12-hour extreme;
- the just-completed GBPUSD close simultaneously breaks the inverse prior completed 12-hour extreme;
- the Dollar/bond/breadth direction classifier agrees with the release;
- only the first release signal in an episode is eligible.

Trade:

- `USD_UP` means short GBPUSD; `USD_DOWN` means long GBPUSD;
- stop distance is 1.0 × GBPUSD ATR(24);
- target is 2R;
- maximum hold is 12 completed H1 bars;
- no entry at 21:00, 22:00, or 23:00 UTC.

Mechanism: synchronized release from causal cross-asset compression, not price-only Bollinger/Donchian breakout.

## Explicit Cash States

No specialist may trade:

- shock;
- neutral/unresolved direction;
- ordinary transition;
- normal chop;
- compression without synchronized release;
- any state not exactly owned above.

There is no absorption-reversal specialist in this campaign because that would overlap the closed FX dispersion/reversal family.

## Execution and Cost Contract

- Long entry at next M5 ask; short entry at next M5 bid.
- Long stop/target evaluated on bid; short stop/target evaluated on ask.
- If stop and target are both touched in one M5 bar, stop wins.
- Raw bid/ask spread is embedded.
- Add 0.1 pip adverse slippage on each entry and exit.
- Time exit uses the first executable M5 close at or after the deadline.
- One position per symbol.

## Standalone Admission

Each specialist must independently satisfy:

- at least 30 trades in each chronological window;
- PF ≥ 1.10 in each window;
- expectancy > +0.02R in each window;
- overall max drawdown ≤ 12R;
- overall net R remains positive after removing the top 5% winning trades;
- overall net R remains positive under an additional 0.5 pip round-trip stress.

A failed specialist cannot be rescued by the portfolio.

## Router and Shared Risk

Only standalone-admitted specialists enter the router.

- maximum one concurrent FX position;
- deterministic priority: R1, then R2 when timestamps collide;
- 1R nominal risk per trade;
- stop opening new trades after closed daily P&L reaches -2R;
- stop opening new trades after closed weekly P&L reaches -4R;
- no state-dependent sizing and no P&L-based specialist selection.

Portfolio research target:

- PF ≥ 1.15;
- positive in every chronological window;
- positive after top-5%-winner removal and +0.5 pip stress;
- at least one routed trade per active FX day on average.

The frequency target is diagnostic, never a reason to force trades.

## Decision Vocabulary

- `ADMITTED_RESEARCH_COMPONENT`
- `REJECTED_STANDALONE`
- `NO_PORTFOLIO_FORMED`
- `RESEARCH_PORTFOLIO_SURVIVOR`

No result from this campaign may be labeled demo-ready.
