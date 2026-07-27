# USDJPY Session-Seed Regime Decomposition Preregistration — 2026-07-27

Status: `HASH_LOCKED_BEFORE_REGIME_OUTCOME_JOIN`

Boundary: offline research only. No MT5, broker, account, chart, EA, or order action is authorized.

## Purpose

Apply the Gold trajectory to the strongest existing frozen Forex watchlist seed instead of repairing the failed cross-asset campaign.

The base seed is the previously documented `USDJPY london120_break_m15 D1 ATR20` rule. Its parameters, directions, range hours, risk geometry, and daily trade cap remain unchanged. This campaign has one question: when its signals are assigned ex ante to exclusive causal regimes, does any regime own a standalone robust expert?

The base seed's aggregate history is already known. The regime-level join and regime-level P&L have not been inspected before this hash lock. All resulting evidence remains development evidence.

## Frozen Base Seed

- Build the USDJPY 06:00–08:00 UTC range from completed M15 bars.
- Evaluate completed M15 bars from 08:00 through 11:45 UTC.
- Require M15 ATR(14), range/ATR from 0.45 through 3.20, prior D1 ATR(14), session range/prior-D1-ATR at least 0.20, and candle body fraction at least 0.30.
- Long close must exceed range high plus 0.05 M15 ATR and close in the upper 35% of its bar.
- Short is the exact inverse.
- Stop is the farther of 1.0 M15 ATR, 1.0 session range, 30 points, and the opposite session boundary; reject above 900 points.
- Target is 1R.
- Maximum two entries per UTC day and no overlapping USDJPY positions.

These values come from the frozen watchlist-v1 implementation and are not selected by this campaign.

## Causal Regime Timestamp

For each completed M15 signal, attach only the most recent H1 state that was fully complete by the M15 close. The state is the already hash-locked Dollar Index/Treasury/FX direction-volatility-phase classifier from the first campaign. No regime threshold changes are permitted.

## Exclusive Ownership

Precedence is exact:

1. `SHOCK_CASH`: any shock state; no trade.
2. `COMPRESSION_RELEASE`: the latest completed H1 state has both Dollar Index and USDJPY marked compressed; the M15 breakout is the release expert.
3. `ESTABLISHED_ALIGNED`: established USD direction and breakout direction agree (`USD_UP`/long or `USD_DOWN`/short).
4. `TRANSITION_ALIGNED`: transition USD direction and breakout direction agree.
5. `NEUTRAL_NORMAL`: neutral/unresolved, non-shock, non-compressed state; the local session structure owns the trade.

Established or transition signals that oppose the causal USD direction map to cash. Ownership is mutually exclusive; a trade cannot appear in two experts.

## Experts

- `S1 established aligned breakout`
- `S2 transition aligned breakout`
- `S3 compression-release breakout`
- `S4 neutral-normal breakout`

Every expert uses the same frozen base signal and risk rule. They differ only in exclusive regime ownership.

## Execution

- Use official Dukascopy M5 bid/ask bars.
- Long entry at next M5 ask; short entry at next M5 bid.
- Long exits are evaluated on bid; short exits on ask.
- Stop wins ambiguous same-bar collisions.
- Add 0.1 pip adverse slippage per side.
- No time exit, matching the frozen seed.
- Exclude the inherited USDJPY quarantine interval from new entries.

## Standalone Admission

Each expert must independently achieve:

- at least 30 trades in each chronological window;
- PF at least 1.10 in each window;
- expectancy above +0.02R in each window;
- overall max drawdown no more than 12R;
- positive net after removing the top 5% winners;
- positive net under another 0.5-pip round-trip stress.

Failure cannot be rescued by combination. Only admitted experts enter the existing one-position shared router with -2R daily and -4R weekly entry brakes.

## Decision Rule

If no expert passes, record `NO_PORTFOLIO_FORMED` and close this exact decomposition. Do not merge regimes, drop a direction, or alter a threshold after outcomes.
