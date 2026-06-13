# A3 RDGUARD V1 Build Report

Overall status: PASS

## Global Boundaries

- A3 demo account login: `1033669`.
- Demo only. No live trading. Canonical Phase 2 status unchanged.
- A2 (`1033030`, `breakout_retest`) was not touched.
- A1 (`1025742`) was not touched by T1.
- Committed defaults are non-executing: `InpDryRunOnly=true`, `InpBrokerActionAllowed=false`.
- Locked hypotheses were not edited.

## Source

`xau-usd/xauusd-phase1/mt5/Experts/Account3RoundRetestGuardedExecutor.mq5`

Identity:

- Magic: `933000` in band `933000-933099`.
- Comment: `RDGUARD_V1`.
- Target symbol: `XAUUSD`.
- Account allowlist default: `1033669`.

## Kernel

The EA is self-contained and does not include or share A1 executor source/includes. The source preserves the `symbol_normalized_round_retest_v0` mechanics used by the experimental executor:

- symbol-normalized round increments,
- M5 break search over shifts `3-22`,
- `0.30 * ATR` break threshold,
- 5-point retest tolerance,
- `0.10 * ATR` stop pad,
- `1.50R` take-profit.

## Guards

| Guard | Implementation |
|---|---|
| G1 impulse veto | `ret12_atr=(close[1]-close[13])/ATR14(M5)`, `impulse_alignment=dir_sign*ret12_atr`, threshold `-1.5`; raw values logged on every signal row. |
| G2 family mutex | `GlobalVariableSetOnCondition` on `FAMMUX_RD_XAUUSD_<dir>_<barTime>` before `OrderSend`; failure logs `MUTEX_CLAIMED_ELSEWHERE`. |
| G3 streak breaker | 3 own-magic SL closes inside rolling 2 h pauses entries until the next 4 h boundary. |
| G4 daily stop | Own-magic Dubai-day realized PnL `<= -150 AED` pauses entries until next Dubai day; no position-closing calls exist. |
| G5 caps | T15 baked in: max 1 open position per magic, cost cap `0.15R`, `COST_WARN` above `0.20R`, reject above `0.30R`, spread cap 75 points, min 60 s, fixed 0.01 lot. |
| G6 scope locks | XAUUSD only, demo marker required, live/real refused, allowlist `1033669`, shared `A3_KILL.txt`. |

## Logging

Would-signal logging writes vetoed and blocked rows to `a3_rdguard_v1_signal_log.csv`, including `ret12_atr`, `impulse_alignment`, `estimated_cost_R`, `cost_warn`, open positions per magic, streak count, daily realized PnL, and mutex name.

## Compile

Scratch compile PASS:

`C:/MT5CompileScratch/A3RdGuard_20260614_002511/Logs/compile_Account3RoundRetestGuardedExecutor.log`

Result: `0 errors, 0 warnings`.

Runtime attachment is intentionally deferred to T17 combined preflight.
