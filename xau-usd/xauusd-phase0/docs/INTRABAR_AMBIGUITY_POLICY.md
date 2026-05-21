# Intrabar Ambiguity Policy

Phase 0 currently evaluates OHLC bar data with `ambiguous_intrabar_policy: adverse_first`. When a bar touches both stop loss and take profit, the simulator resolves the exit against the trade.

The command `phase0 generate-intrabar-ambiguity-report --expert breakout_retest` summarizes:

- total matrix trade files inspected
- total trades
- ambiguous exit trades
- same-timestamp entry/exit proxy count
- PF under the current adverse-first policy

Neutral intrabar ordering is not inferred from OHLC bars. If the ambiguity report shows material exposure, the next review step is tick-level replay or a separately specified neutral ordering simulator before Phase 1 approval.
