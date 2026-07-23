# MT5 shadow-demo package

`EurUsdV4AsiaLondonCompressionShort.mq5` (legacy evidence filename) implements
the frozen Capital-native H4-chop Asia/London short strategy.
It is safe by default: `ShadowMode=true` and `EnableDemoOrders=false`.

Attach it to an EURUSD chart with `EURUSD_V4_SHADOW_DEMO.set`. Set
`BrokerUtcOffsetHours` to the broker-server offset from UTC. It evaluates once at
each new H1 bar, logs eligible signals to the MT5 Common Files folder, and never
orders in the shadow preset.

The ordering template is intentionally not active. It has a hard runtime check
that rejects non-demo accounts. It may be used only after broker-history Strategy
Tester parity is reviewed and the owner explicitly authorizes demo orders.

Research status: controlled demo-rehearsal candidate. The final Capital.com
real-tick Strategy Tester run produced 62 trades, 53.23% wins, PF 1.45, +$22.85
at 0.01 lot, and 0.11% maximal balance drawdown. This does not authorize live
trading.
