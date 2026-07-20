# V56 Frozen Audit Contract

## Provenance

V54 controlled required-window closed drawdown but reached only 0.927 trades
per weekday in the final year. V55 showed that fractional de-risking could
restore one trade per day, but that is not a deployable minimum-lot solution.

An exposed fixed-family search evaluated 4,989 unique interpretable rules after
the already established causal 100-completed-trade health gate. Six passed the
development-2, confirmation, and final economic screens. The selected rule was
the highest-frequency candidate under the fixed ranking of final frequency,
minimum required-window PF, and final net:

`mechanism=BREAK&action_id=SWING_2R_36H&h4adx=HIGH`

This selection is exposed-history research and is not an out-of-sample claim.

## Frozen V56 policy

- preserve all 849 V54 accepted add-ons and the complete V50 core unchanged;
- generate the exact breakout rule above with one open rule position and at
  most two raw rule entries per UTC date;
- enable it only after 100 strictly prior completed shadow trades have trailing
  PF at least 1.0 and positive trailing net;
- reject underlying event IDs already eligible for V7 or V8 after their health
  gates, even when account governance rejected the older candidate;
- cap proposed risk at USD 30 at the recorded 0.01-lot-equivalent action;
- admit only incremental trades that keep the combined add-on limits at two
  open positions, USD 45 concurrent initial risk, and two entries per UTC date;
- suspend only new V56 entries at USD 225 causal closed drawdown and resume at
  USD 180; fixed V54 trades are never removed or reordered.

All windows, economic gates, and the USD 300 combined closed-drawdown ceiling
remain inherited from V53. The contract and implementation are locked before
the terminal V56 reproduction run.

## Authority

A pass establishes an exposed historical one-trade-per-day portfolio candidate
only. It does not authorize Python serving, EA consumption, MT5 attachment,
demo trading, live trading, or broker action. Prospective shadow confirmation,
MT5 parity, and whole-account floating-equity evidence remain required.
