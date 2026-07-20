# One-Trade-Per-Day Break Overlay V56

V56 preserves every fixed V54 base trade and adds a non-duplicated breakout
swing sleeve only when the existing account governor has spare capacity.

The overlay rule is mechanical: `BREAK`, `SWING_2R_36H`, and H4 ADX above 30.
It uses the established causal 100-completed-trade PF/net health gate, excludes
events already eligible for the V7 or V8 sleeve, and remains behind the fixed
USD 225/180 hard drawdown circuit.
