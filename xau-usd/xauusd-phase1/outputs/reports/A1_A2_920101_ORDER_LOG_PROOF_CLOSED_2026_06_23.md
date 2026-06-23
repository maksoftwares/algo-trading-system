# A1/A2 920101 Order-Log Proof Closed - 2026-06-23

Status: `PASS_ORDER_LOG_PROOF_CLOSED`

Boundary: read-only evidence review. No MT5 chart, preset, EA, order, or position state was modified.

## Source Files

| Lane | Account | Source |
|---|---:|---|
| A1 | `1025742` | `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files\a1_920101_evening_order_log.csv` |
| A2 | `1033030` | `C:\MT5PortableTier1BestEA\MQL5\Files\a2_920101_evening_order_log.csv` |
| Runtime inventory | n/a | `xau-usd/xauusd-phase1/outputs/reports/RUNTIME_CHART_INVENTORY_FORENSIC_2026_06_21.csv` |

## Runtime Identity Check

| Lane | Chart | Symbol | Expert | Magic | State | Session | Account |
|---|---|---|---|---:|---|---|---:|
| A1 | `chart03.chr` | `XAUUSD` | `Phase2ExperimentalDemoExecutor` | `920101` | `BROKER_ACTION_ENABLED` | `12->15` | `1025742` |
| A2 | `chart02.chr` | `XAUUSD` | `Phase2ExperimentalDemoExecutor` | `920101` | `BROKER_ACTION_ENABLED` | `12->15` | `1033030` |

## Qualifying Order Rows

Rows below are post-repair, post-2026-06-23 `ORDER_SEND_OK` rows with `magic=920101`, `broker_action_allowed=true`, `dry_run=false`, `guard_reason=pass`, and 0.01-lot `XAUUSD` exposure.

| Lane | Broker time | UTC | Direction | Volume | Request | SL | TP | Retcode | Order | Deal | Result price | Cost R | Stop points |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A1 | `2026.06.23 12:15:01` | `2026.06.23 12:15:01` | `SHORT` | `0.01` | `4113.78` | `4118.99` | `4105.97` | `10009` | `4206253` | `3880812` | `4113.80` | `0.0960` | `520.99` |
| A1 | `2026.06.23 12:30:01` | `2026.06.23 12:30:01` | `SHORT` | `0.01` | `4115.05` | `4123.12` | `4102.95` | `10009` | `4206636` | `3881143` | `4115.05` | `0.0620` | `806.90` |
| A1 | `2026.06.23 14:00:00` | `2026.06.23 14:00:00` | `SHORT` | `0.01` | `4135.29` | `4145.88` | `4119.40` | `10009` | `4208668` | `3882711` | `4135.53` | `0.0472` | `1059.24` |
| A2 | `2026.06.23 12:15:01` | `2026.06.23 12:15:01` | `SHORT` | `0.01` | `4113.76` | `4118.97` | `4105.95` | `10009` | `4206254` | `3880813` | `4113.82` | `0.0960` | `520.99` |
| A2 | `2026.06.23 12:30:00` | `2026.06.23 12:30:00` | `SHORT` | `0.01` | `4115.07` | `4123.14` | `4102.97` | `10009` | `4206633` | `3881140` | `4115.09` | `0.0620` | `806.90` |
| A2 | `2026.06.23 14:00:00` | `2026.06.23 14:00:00` | `SHORT` | `0.01` | `4135.29` | `4145.88` | `4119.40` | `10009` | `4208669` | `3882712` | `4135.44` | `0.0472` | `1059.24` |

## Verdict

The pending first-order proof is closed for both accounts. The A1 and A2 `920101` forward-test lanes are not blocked; they placed qualifying demo orders in the allowed server-hour window after the repair.
