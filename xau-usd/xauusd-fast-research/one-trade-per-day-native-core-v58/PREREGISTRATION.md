# V58 Native-Position Core Repair

## Known defect

V57 inherited the historical R1 ledger's FIFO-by-direction exit pairing. The
native-position audit established before this evaluation that 388 of 678 R1/R2
control rows name another position's exit and 387 carry another position's P/L.
Aggregate source P/L is preserved, but a policy that removes overlapping rows
cannot safely use those row-level outcomes.

## Frozen repair

V58 makes only this correctness repair:

- rebuild all 558 R1 rows from the frozen MT5 native-position reconciliation;
- retain the same two R1 source identities and their unchanged aggregate P/L;
- reapply the V50 one-open-position and one-entry-per-UTC-day rule to the
  corrected native entry/exit intervals;
- replay the frozen V57 add-on candidate set through the same unified causal
  account governor;
- retain every V57 window, economic gate, drawdown threshold, and sleeve rule.

No strategy threshold, signal, add-on outcome, evaluation window, or acceptance
gate may change after this document and the contract are locked.

## Terminal decision

V58 passes only if all inherited V57 gates pass after native-position repair.
A failure is terminal for V58. Any later repair requires a new preregistered
version and must not substitute outcomes into this package.

## Evidence limits

The native deal logs contain deal profit, commission, and swap but no complete
`DEAL_FEE` evidence. V58 reports this explicitly and does not claim complete
fee stress. Whole-account floating-equity reconstruction, prospective shadow,
and MT5 parity remain separate mandatory gates.

V58 is historical research only. It grants no Python serving, EA, demo, live,
or broker authority.
