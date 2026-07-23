# EURUSD M30 RSI/Bollinger Fade V1 Evidence Contract

Status: `RETROSPECTIVE_BASELINE_LOCK_RESEARCH_ONLY`

This is a lock of an already selected historical candidate, not an untouched
preregistration. All observations through the existing July 2026 MT5 run are
development data and may not be relabeled as forward evidence.

## Frozen strategy

- Symbol: `EURUSD`
- Decision timeframe: `M30`
- Execution chart: `M5`
- Direction: long only
- Bollinger Bands: close, 20 periods, 2.0 standard deviations
- RSI: close, 14 periods, oversold at 35
- Signal: completed M30 close at or below the lower band and RSI <= 35
- Entry: first executable tick after the new M30 bar is detected
- Blocked broker/tester hours: `6,7,10,13`
- Fixed research size: `0.01` lot
- Initial stop: wider of 1.4 ATR(14), 30 points, or the lowest low of the last
  six completed M30 bars
- Maximum stop: 700 points
- Target: 0.8 times initial stop distance
- Spread guard: 100 points
- Maximum entries per broker/tester day: 20
- Maximum owned open positions: one
- No trailing, partial close, compounding, ML, or discretionary override

## Working-research gate

This gate answers only whether there is a reproducible strategy baseline worth
prospective work:

- actual MT5 Strategy Tester evidence exists;
- at least 500 closed trades;
- MT5 profit factor >= 1.15;
- MT5 total net profit > 0;
- MT5 maximal equity drawdown <= 5%;
- both fixed chronological research splits have positive parsed P/L and
  profit factor > 1;
- parsed P/L remains positive after removing the ten largest winners;
- the current EA source matches the SHA256 lock;
- the EA is explicitly Strategy-Tester-only.

Passing this gate produces
`WORKING_RESEARCH_STRATEGY_FORWARD_NOT_AUTHORIZED`, never demo/live authority.

## Promotion blockers

The following remain mandatory:

1. Refresh Capital.com provenance, spread, contract, and current-bar evidence.
2. Freeze a prospective shadow start before observing its outcomes.
3. Complete at least six calendar months or 200 mature forward trades.
4. Pass shared-account risk and USD-factor overlap tests with XAUUSD.

The current source was recompiled on 2026-07-23 with zero errors and warnings,
then reproduced the inherited 831-trade result exactly in the isolated MT5
Strategy Tester. The source, EX5, compile log, tester configuration, reports,
and ledgers are recorded in the parity manifest.
