# V30 Simulator Alias Preregistration

The only authorized transformation is a byte-for-value metadata alias from the
two V30 impulse diagnostics to the two names consumed by the locked V24
simulator. Row count, order, candidate timestamp, side, bid, ask, and every
strategy field must remain identical. The adapter is locked before any V30 entry
or exit price, return, or P&L is opened.

Any other difference fails closed. This package grants no trading or model
authority.
