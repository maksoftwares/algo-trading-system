# EURUSD H4 chop controlled demo runbook

## Scope

This package is for prospective observation on an EURUSD demo account only.
It is not approved for a live account. The source refuses to initialize on a
non-demo account.

The deployed research candidate is the sparse H4-chop Asia/London short
specialist. Its prior Capital.com real-tick result for July 2024 through June
2026 was 62 trades, 53.23% wins, PF 1.45, +$22.85 at 0.01 lot, and $11.00
maximum balance drawdown. Full inspected Dukascopy history was weaker (349
trades, PF 1.20), so the purpose of demo deployment is prospective validation,
not profit expectation.

## Shadow stage

1. Copy `EurUsdH4ChopControlledDemo.ex5` to the terminal's `MQL5/Experts`
   directory.
2. Attach it to one EURUSD H1 chart.
3. Load `EURUSD_H4_CHOP_CONTROLLED_SHADOW_DEMO.set`.
4. Confirm the Experts log contains `INIT_OK` and the common-files audit CSV
   contains `shadow_demo`.
5. Keep the terminal connected and collect signals. This preset cannot order:
   shadow mode, the order switch, emergency stop, arm token, account allowlist,
   and server allowlist all independently block new orders.

## Ordering-demo stage

Do not use the ordering template until shadow signals have been reconciled
against the Python reference.

1. Copy the template to a new local preset.
2. Replace `InpAllowedAccountLogin=0` with the exact demo login.
3. Replace `InpAllowedServer` with the exact demo server string.
4. Confirm the prospective UTC start and broker UTC offset.
5. Verify EURUSD has no foreign or manually opened position.
6. Load the local preset. The EA accepts exactly 0.01 lot and at most one new
   trade per UTC day.

## Automatic blocks

New entries stop when any of these conditions applies:

- non-demo account, account/server mismatch, disarmed token, shadow mode, or
  emergency stop;
- prospective start not reached;
- any EURUSD position already exists;
- spread above 2.0 pips;
- one entry already occurred that UTC day;
- closed strategy P&L reaches -$10 for the UTC day or -$20 over five days;
- session equity falls $25 from EA startup;
- another EA instance owns the terminal mutex.

Time-based exits may still reduce an owned position after an entry breaker
activates. The EA will not manage positions with another magic number.

## Rollback

Set `InpEmergencyStop=true` to block new entries. Then remove the EA after
checking whether its magic-number position is open. Removing the EA does not
close a position; close or supervise that demo position explicitly. Preserve
the common-files audit CSV and terminal logs for reconciliation.
