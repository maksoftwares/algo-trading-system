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

## Frequency V2 overlay

`ForexMeanReversionScout.ex5` is the frequency sleeve. Its source is
`forex-research/mt5/Experts/ForexMeanReversionScout.mq5`. The V2 version:

- defaults to shadow mode with demo orders disabled;
- rejects non-demo accounts outside Strategy Tester;
- supports a login allow-list and demo-server marker;
- owns at most one position per magic number;
- applies the frozen completed-H4 trend classifier before adding 0.01 lots;
- compiles with zero errors and zero warnings.

Attach it to EURUSD M5 using
`EURUSD_FREQUENCY_V2_M15_SHADOW_DEMO.set`. Run the frozen chop control on a
separate EURUSD H1 chart. Their different magic numbers allow at most two
concurrent positions.

The owner-authorized template is intentionally unusable until its account
placeholder is replaced. It must never be used on a live account.
