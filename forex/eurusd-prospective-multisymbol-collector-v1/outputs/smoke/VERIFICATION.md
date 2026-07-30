# Prospective collector smoke verification

Status: `PASS_READ_ONLY_COLLECTOR_SMOKE_NOT_STRATEGY_ADMISSION`

The compiled observer completed a two-day EURUSD M5 Strategy Tester smoke run
with 0 trades, 0 deals, and an unchanged $10,000.00 balance.

## Runtime results

| Item | Result |
|---|---:|
| MetaEditor compile | 0 errors, 0 warnings |
| Generated M5 bars | 574 |
| Generated EURUSD ticks | 134,788 |
| Captured source rows | 4,592 |
| Valid EURUSD rows | 573 |
| Total trades | 0 |
| Total deals | 0 |
| Final balance | $10,000.00 |

The first Sunday-boundary EURUSD interval contained no ticks. All other 573
EURUSD intervals produced valid two-sided quote aggregates. Historical
cross-pair tick streams were not supplied to this Strategy Tester agent, so the
collector recorded `NO_TICKS` for those sources. The two optional index names
were recorded as `SYMBOL_UNAVAILABLE`.

That behavior is intentional: unavailable information remains missing and is
never substituted. Cross-pair availability still requires a live demo shadow
soak after the owner confirms the exact broker symbols and UTC offset.

All rows are stamped `TESTER_SMOKE_NOT_FORWARD`. They are operational evidence,
not admissible strategy-development observations.
