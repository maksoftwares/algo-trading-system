# A3 Failure Diagnosis - 2026-06-17

## Boundary

Read-only diagnosis. No MT5 runtime, EA, preset, chart, order, position, profile, or account setting was changed.

Fresh MT5 sources:

| Source | Path |
| --- | --- |
| A2 account export | `xau-usd/xauusd-phase1/outputs/reports/A2_TIER1_ACCOUNT_HISTORY_2026_06_17.md` |
| A3 account export | `xau-usd/xauusd-phase1/outputs/reports/A3_REPAIR_LANE_ACCOUNT_HISTORY_2026_06_17.md` |
| A2 order log | `C:/MT5PortableTier1BestEA/MQL5/Files/tier1_bestea_order_log_xauusd.csv` |
| A2 signal log | `C:/MT5PortableTier1BestEA/MQL5/Files/tier1_bestea_signal_log_xauusd.csv` |
| A3 plain order log | `C:/MT5PortableRepairLane/MQL5/Files/a3_breakout_plain_order_log.csv` |
| A3 plain signal log | `C:/MT5PortableRepairLane/MQL5/Files/a3_breakout_plain_signal_log.csv` |
| A3 improved signal log | `C:/MT5PortableRepairLane/MQL5/Files/a3_breakout_improved_signal_log.csv` |

## Fresh A3 Result

| Metric | Value |
| --- | ---: |
| Balance | 3900.38 AED |
| Starting balance ops | 4000.00 AED |
| Closed net PnL | -99.62 AED |
| Closed positions | 57 |
| Wins / losses | 20 / 37 |
| Win rate | 35.09% |
| Open positions | 0 |

## Main Verdict

A3 is failing because it is taking trades that A2 is deliberately filtering out.

The two biggest differences are:

1. A2 has an active session gate. A3 plain does not.
2. A2 applies a wider XAUUSD execution stop-distance floor. A3 plain uses the raw observer risk, so its stops are much tighter and cost_R is much higher.

A3 plain also has trend guard and exit protection disabled. The A3 improved lane saw the same would-signals and blocked them all by trend/cost checks, which strongly suggests the current fix layer would have prevented this A3 plain loss cluster.

## A3 Plain Closed Trades

| Position | Entry Dubai | Direction | Session | Net PnL AED | Comment |
| --- | --- | --- | --- | ---: | --- |
| 4100993 | 2026-06-16 15:23:38 | SELL | Afternoon 12:00-15:59 | -12.79 | A3_BREAKOUT_PLAIN |
| 4101166 | 2026-06-16 15:40:01 | SELL | Afternoon 12:00-15:59 | -17.49 | A3_BREAKOUT_PLAIN |
| 4108728 | 2026-06-16 21:30:00 | BUY | Night 20:00-05:59 | -29.18 | A3_BREAKOUT_PLAIN |
| 4115586 | 2026-06-17 09:50:00 | BUY | Morning 06:00-11:59 | -12.42 | A3_BREAKOUT_PLAIN |
| 4116658 | 2026-06-17 10:55:01 | BUY | Morning 06:00-11:59 | -12.75 | A3_BREAKOUT_PLAIN |
| 4116895 | 2026-06-17 11:30:01 | BUY | Morning 06:00-11:59 | -11.76 | A3_BREAKOUT_PLAIN |

Summary: 6 trades, 0 wins, -96.39 AED.

## A3 Plain By Session

| Session | Trades | Wins | Losses | Net PnL AED |
| --- | ---: | ---: | ---: | ---: |
| Afternoon 12:00-15:59 | 2 | 0 | 2 | -30.28 |
| Night 20:00-05:59 | 1 | 0 | 1 | -29.18 |
| Morning 06:00-11:59 | 3 | 0 | 3 | -36.93 |

None of the six A3 plain trades occurred in the A2-style Dubai evening execution window.

## A2 Versus A3 Guard Difference

A2 active preset:

```text
InpTradeSessionGateEnabled=true
InpTradeSessionStartHour=12
InpTradeSessionEndHour=15
InpMaxEstimatedCostR=0.30
InpMaxOpenPositionsPerInstance=1
```

A3 plain active preset:

```text
InpTrendGuardEnabled=false
InpBreakevenEnabled=false
InpPartialTakeProfitEnabled=false
InpMaxEstimatedCostR=0.15
InpMaxOpenPositionsPerMagic=1
```

A3 plain does not have an equivalent session gate. It allowed morning/afternoon trades that A2 would block.

Evidence from overlapping A2 signals:

| A3 Losing Signal Time | A3 Action | A2 Same Signal Behavior |
| --- | --- | --- |
| 2026-06-16 15:39 | A3 sold and lost | A2 saw `WOULD_SIGNAL` but blocked: `server_hour_session_gate` |
| 2026-06-16 21:29 | A3 bought and lost | A2 saw `WOULD_SIGNAL` but blocked: `server_hour_session_gate` |
| 2026-06-17 09:49 | A3 bought and lost | A2 saw `WOULD_SIGNAL` but blocked: `server_hour_session_gate` |
| 2026-06-17 10:54 | A3 bought and lost | A2 saw `WOULD_SIGNAL` but blocked: `server_hour_session_gate` |
| 2026-06-17 11:29 | A3 bought and lost | A2 saw `WOULD_SIGNAL` but blocked: `server_hour_session_gate` |

## Stop-Distance / Cost-R Difference

| Lane | Orders | Avg Stop Distance | Avg Cost_R |
| --- | ---: | ---: | ---: |
| A2 executed orders | 8 | about 958 points | about 0.063R |
| A3 plain executed orders | 6 | about 421 points | about 0.133R |

The same 50-75 point spread consumes roughly twice as much risk budget in A3 plain because its stops are much tighter.

Relevant source difference:

| Lane | Behavior |
| --- | --- |
| A2 `Phase2ExperimentalDemoExecutor.mq5` | Enforces a minimum XAUUSD risk floor before sending: at least broker stop floor, at least 3x spread, and at least 300 points for XAUUSD |
| A3 `A3BreakoutExecutorBase.mqh` | Uses raw observer `signal_risk` directly for SL/TP; no equivalent XAUUSD minimum risk floor in `SendMarketOrder` |

This is a design mismatch, not a broker/account issue.

## Trend-Guard Evidence

A3 improved saw the same would-signals but blocked them:

| Signal Type | Improved Lane Decision |
| --- | --- |
| 2026-06-16 afternoon shorts | Blocked by `TREND_AGAINST_SIGNAL` against UP/UP H1-H4 context |
| 2026-06-17 morning longs | Blocked by `TREND_AGAINST_SIGNAL` or `COST_R_CAP_BLOCK` |
| 2026-06-16 night long | Blocked by `TREND_AGAINST_SIGNAL` because H4 was DOWN |

A3 improved had no orders in its order log at the time of this check. That means the guard did what it was supposed to do: it stopped the bad A3 plain cluster.

## Why A3 Is Failing In Plain English

A3 plain is not failing because MT5 is broken or because A3 cannot trade.

It is failing because:

1. It took non-evening trades that A2 filtered out.
2. It shorted into an UP trend on June 16 afternoon.
3. It took morning trades where recent gold evidence is weak.
4. It used tighter stops than A2, making the same spread/cost heavier in R terms.
5. The safer A3 improved lane blocked these same signals, but the plain lane was allowed to trade them.

## Recommended Next Move

Do not judge A3 plain as a production candidate in its current form.

If we want A3 to become useful, the next design should be a new copy, not a change to running EAs:

```text
A3_BREAKOUT_TIER1_COMPAT_V1
```

Required behavior:

1. Same A2 evening/server-hour gate.
2. Same A2 XAUUSD stop-distance floor.
3. Same family/position cap behavior.
4. Optional trend guard as an experimental switch.
5. Separate magic/comment/logs so it never merges with old A3 plain or A2.

For now, the clean interpretation is:

```text
A2 is the better breakout implementation.
A3 plain is a deliberately useful failed control.
A3 improved/future tier1-compatible lane is where repair work should happen.
```
