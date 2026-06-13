# A3 RDSTRUCT V1 Build Report

Overall status: PASS

## Global Boundaries

- A3 demo account login: `1033669`.
- Demo only. No live trading. Canonical Phase 2 status unchanged.
- A2 (`1033030`, `breakout_retest`) was not touched.
- A1 (`1025742`) was not touched by T13.
- Committed defaults are non-executing: `InpDryRunOnly=true`, `InpBrokerActionAllowed=false`.
- EA-T3 code was not written; magic band `933200-933299` remains reserved only.
- Locked hypotheses were not edited.

## Source

`xau-usd/xauusd-phase1/mt5/Experts/Account3RoundRetestStructuredExecutor.mq5`

Identity:

- Magic: `933100` in band `933100-933199`.
- Comment: `RDSTRUCT_V1`.
- Target symbol: `XAUUSD`.
- Account allowlist default: `1033669`.

## Kernel

The EA is self-contained and does not include or share A1 or EA-T1 executor source/includes. The round-retest mechanics match the EA-T1 source basis: symbol-normalized round increments, M5 break shifts `3-22`, `0.30 * ATR` break threshold, 5-point retest tolerance, `0.10 * ATR` stop pad, and `1.50R` take-profit.

## Structural Gate

EA-T2 does not include G1 or any impulse veto logic. Its one new variable is structural confirmation. Because the Phase B write-up did not specify an exact M15 bar count/threshold, this build carries over the existing `swing_breakout_retest_v0` confirmed-swing constants:

- M15 structure lookback: `20` bars.
- Swing confirmation: `left=4`, `right=4`.
- LONG passes when a recent M15 close breaks above a confirmed M15 swing high.
- SHORT passes when a recent M15 close breaks below a confirmed M15 swing low.
- Failed confirmation logs `STRUCT_FILTER_BLOCK`.

Raw structural fields are logged on every signal row: swing bar index/time, break direction, level, break close, and distance from level.

## Guards

| Guard | Implementation |
|---|---|
| G2 family mutex | `GlobalVariableSetOnCondition` on `FAMMUX_RDSTRUCT_XAUUSD_<dir>_<barTime>` before `OrderSend`; failure logs `MUTEX_CLAIMED_ELSEWHERE`. |
| G3 streak breaker | 3 own-magic SL closes inside rolling 2 h pauses entries until the next 4 h boundary. |
| G4 daily stop | Own-magic Dubai-day realized PnL `<= -150 AED` pauses entries until next Dubai day; no position-closing calls exist. |
| G5 caps | T15 baked in: max 1 open position per magic, cost cap `0.15R`, `COST_WARN` above `0.20R`, reject above `0.30R`, spread cap 75 points, min 60 s, fixed 0.01 lot. |
| G6 scope locks | XAUUSD only, demo marker required, live/real refused, allowlist `1033669`, shared `A3_KILL.txt`. |

## Compile

Scratch compile PASS:

`C:/MT5CompileScratch/A3RdStruct_20260614_002840/Logs/compile_Account3RoundRetestStructuredExecutor.log`

Result: `0 errors, 0 warnings`.

Runtime attachment is intentionally deferred to T17 combined preflight.
