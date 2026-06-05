# WR50 Kill Rules

Document date: 2026-06-04

The following conditions block startup or new order placement.

## Startup Failures

| Trigger | Required action |
| --- | --- |
| Non-demo account detected | Fail startup. |
| Server text does not include a demo marker | Fail startup unless explicitly disabled for broker-specific review. |
| Runtime registry missing while required | Fail startup. |
| Runtime registry disables the EA | Fail startup. |
| Magic number outside assigned range | Fail startup. |
| Owner demo trading flag is false | Fail startup. |
| Owner authorization token missing or mismatched | Fail startup. |
| Account is netting and netting risk is not explicitly accepted | Fail startup. |

## New Trade Blocks

| Trigger | Required action |
| --- | --- |
| Spread greater than `InpMaxSpreadPoints` | Block new trade and log block. |
| Daily trade count exceeded | Block new trade and log block. |
| Max open WR50 positions exceeded | Block new trade and log block. |
| Max open positions for this EA exceeded | Block new trade and log block. |
| Daily experimental group loss exceeded | Block new trade and log block. |
| Same-symbol non-WR50 exposure exists and shared exposure is not allowed | Block new trade and log block. |
| Account margin insufficient | Block new trade and log block. |
| Broker stop levels invalidate SL/TP | Block new trade and log block. |
| Manual blackout active | Block new trade and log block. |
| Rollover blackout active | Block new trade and log block. |

No kill rule may be bypassed to rescue a trade.

