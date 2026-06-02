# Phase 2B Observer Promotion Blockers

Observer telemetry cannot promote a candidate by itself.

Promotion remains blocked while any of these are true:

- hypothesis status is not `LOCKED`
- structural cost precheck is not PASS
- Phase 0R matrix has not passed
- decile persistence has not passed
- measured-cost revalidation has not passed
- adversarial review has not passed
- observer parity has not passed
- owner approval is missing

No observer in this lane is execution-ready.

## Forbidden Broker-Action Term List

This section is documentation for the safety scanner. These terms are forbidden in executable MQL5 observer code:

```text
OrderSend
OrderSendAsync
CTrade
trade.Buy
trade.Sell
PositionOpen
PositionModify
PositionClose
HistoryOrderSend
OrderSendResult
```
