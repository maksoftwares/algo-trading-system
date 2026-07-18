# XAUUSD R2 Downtrend Portability V1

Date: `2026-07-18`

## Purpose

Test whether two previously frozen MT5 R2 short mechanisms transfer unchanged
to a high-quality continuous Dukascopy bid/ask history. The MT5 source period
was 2022-07 through 2026-06, so only the earlier eras can provide portability
evidence.

## Registered Attempts

1. Attempt `11,114`: H1 bearish pullback rejection, M5 body at least 0.58, all
   hours.
2. Attempt `11,115`: the same pullback rule restricted to Capital.com server
   hours 05 through 18.
3. Attempt `11,116`: M5 downside impulse/retest with M5 ATR above 4.50.
4. Attempt `11,117`: the same impulse/retest with M5 ATR above 5.00.

The first two attempts share one mechanism family. The last two share another.
At most one variant from each family can count as distinct.

## Frozen Mechanics

- Broker calendar: `Europe/Helsinki`, matching EET/EEST server boundaries.
- Regime: two completed D1 bars and the last completed H4 bar must have bearish
  EMA 20/50 stacks and non-increasing EMA slopes over five bars.
- Shock veto: last completed H1 range at least 3 ATR or completed D1 ATR at or
  above its 95th percentile over 60 observations.
- Pullback: completed H1 bearish rejection after touching the current H1 EMA
  20/50 zone, three-bar lookback, 0.25 ATR touch and stop buffers, H1 body at
  least 0.35, close location at most 0.35, and prior M5 body at least 0.58.
- Impulse/retest: unchanged 10-bar break search, 12-bar support, 0.10 ATR break,
  0.05 ATR touch/reclaim, 0.25 ATR stop buffer, 3-bar impulse of at least 1.20
  ATR, and bearish break/signal bodies of at least 0.45.
- Entry: first Dukascopy bid quote at or after the decision, within ten minutes.
- Exit: chronological raw Dukascopy ask ticks. Stops pay the observed ask when
  the quote crosses the stop; targets remain frozen at the target price. M5
  ask highs/lows may only prefilter potential hits and cannot order exits.
- Stop floor: 3.50 USD. Stop ceiling: 22.00 USD. Target: 2R.
- Entry spread ceiling: 0.75 USD and 0.15R. Ticket, holding, and stress
  slippage costs are fixed in the JSON contract.

## Windows

1. `old_replication`: 2010-01-01 through 2016-06-30. This market era has been
   opened for other registered mechanisms, but R2 outcomes were not used to
   define these frozen rules.
2. `predevelopment_confirmation`: 2016-07-01 through 2022-06-30. This predates
   the MT5 source window and is the strongest portability evidence.
3. `source_period_diagnostic`: 2022-07-01 through 2026-06-30. Diagnostic only;
   it cannot qualify a candidate because it supplied the original hypothesis.

All four candidates form one Holm family within each evidentiary window. A
candidate qualifies only if it passes every economic, drawdown, concentration,
and adjusted-significance gate in both earlier windows. Source-period agreement
is reported, not used as independent proof.

## Prohibited Actions

No parameter rescue, inversion, subgroup selection, threshold change, paid
data, Databento request, broker action, model training, Python serving, EA
consumption, demo execution, or live execution is authorized.
