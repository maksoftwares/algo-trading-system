# V57 Frozen Audit Contract

## Correctness reason

V56 passed the economic gate while preserving a fixed V54 trade ledger. That
proves capacity but is not the preferred shared-account runtime because old
add-on decisions were made on a counterfactual equity path without the new
overlay.

V57 makes one correctness change: all add-on candidates are governed together
on the actual causal combined closed-equity path. No outcome, signal, entry,
exit, health gate, evaluation window, or acceptance threshold changes.

## Frozen policy

- V50 remains unchanged;
- V7, V8, and V25 candidate construction remains unchanged from V53;
- the V56 breakout rule and its duplicate-event exclusion remain unchanged;
- original add-on candidates receive same-timestamp priority over the new
  overlay through a deterministic trade-ID ordering;
- all add-ons share two open positions, USD 45 concurrent initial risk, and
  two entries per UTC date;
- all add-ons suspend at USD 225 causal combined closed drawdown and resume at
  USD 180;
- every action remains at its recorded 0.01-lot-equivalent economics; no
  fractional risk scaling is used;
- the USD 300 required-window combined closed-drawdown ceiling remains fixed.

V57 is locked before its single terminal evaluation.

## Authority

The selected breakout rule and all historical windows are exposed. A pass is a
historical portfolio candidate only. It grants no Python serving, EA, MT5,
demo, live, or broker authority. Prospective evidence, MT5 parity, and complete
whole-account floating-equity reconstruction remain required.
