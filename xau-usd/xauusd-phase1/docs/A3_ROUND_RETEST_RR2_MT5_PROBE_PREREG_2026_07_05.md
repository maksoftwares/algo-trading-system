# A3 Round-Retest RR2 MT5 Probe Preregistration - 2026-07-05

## Objective

Probe the existing Account 3 XAUUSD round-retest family under exact MT5 Strategy Tester execution for the current owner goal:

- Signal-level average winner / average loser >= 2.0.
- Signal-level win rate >= 50%.
- Frequency target: active on at least 90% of trading days; lower activity may only be reported as a clue if the first two goals pass.

This is a discovery probe only. It cannot authorize demo/runtime attachment.

## Runtime Boundary

- Run only in isolated MT5 tester root: `C:\MT5A1M5MomentumBacktest`.
- Use Strategy Tester only, with `Visual=0`, `UseRemote=0`, `UseCloud=0`.
- No chart attachment, profile arming, preset loading, live/demo runtime attachment, or broker order outside tester.
- Any pass is `REVIEW_REQUIRED`, not demo-ready.

## Code Boundary

The existing A3 EAs hard-code 1.50R targets, which cannot satisfy the owner W/L >= 2.0 goal except by accident. The only EA change allowed for this probe is:

- Add `InpTargetR` with default `1.50`.
- Replace hard-coded `1.50 * risk` target calculations with `InpTargetR * risk`.

The committed default behavior remains unchanged.

## Fixed Variant List

Window: `2022.07.01 -> 2026.06.30`.
Symbol/timeframe: `XAUUSD`, `M5`.
Lot: `0.01`.
Tester account context: `1025742 / Capital.ComMena-Demo`.
Runtime money guards are neutralized for signal discovery: `InpStreakLossCount=999`, `InpDailyLossStopAed=-999999`, `InpMinSecondsBetweenOrders=0`.
One-position cap remains on: `InpMaxOpenPositionsPerMagic=1`.

Variants:

| Variant | EA | Target R | Cost R | Extra |
| --- | --- | ---: | ---: | --- |
| `rdguard_raw_r20_cost030` | `Account3RoundRetestGuardedExecutor` | `2.0` | `0.30` | impulse veto disabled with `InpImpulseVetoThreshold=-999.0` |
| `rdguard_default_r20_cost030` | `Account3RoundRetestGuardedExecutor` | `2.0` | `0.30` | default impulse veto `-1.5` |
| `rdguard_default_r25_cost030` | `Account3RoundRetestGuardedExecutor` | `2.5` | `0.30` | default impulse veto `-1.5` |
| `rdguard_default_r20_cost015` | `Account3RoundRetestGuardedExecutor` | `2.0` | `0.15` | stricter cost gate |
| `rdstruct_default_r20_cost030` | `Account3RoundRetestStructuredExecutor` | `2.0` | `0.30` | default M15 structure confirmation |
| `rdstruct_default_r25_cost030` | `Account3RoundRetestStructuredExecutor` | `2.5` | `0.30` | default M15 structure confirmation |

No optimizer, no threshold sweep, no post-hoc selection beyond this fixed table.

## Metrics

Primary metrics are recomputed from parsed MT5 deal rows, not copied from the MT5 summary:

- trades, wins, losses
- win rate
- average win
- average loss
- average win / average loss
- manual net PnL
- gross profit/loss and profit factor
- active entry days and active-day percentage
- top-3-winners-removed PnL and worst day

MT5 report summary fields are retained only as cross-checks and provenance.

## Review Spend Rule

Do not request external review unless at least one variant reaches the core shape:

- win rate >= 50%, and
- average win / average loss >= 2.0.

If the core shape passes but active days are below 90%, report it as a clue and ask the reviewer for direction only if the clue is robust enough to justify a portfolio/regime layer.
