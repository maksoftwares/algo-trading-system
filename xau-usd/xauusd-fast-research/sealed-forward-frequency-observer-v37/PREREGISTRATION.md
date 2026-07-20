# Sealed Forward Frequency Observer V37 Contract

## Purpose

V37 provides one authoritative, outcome-blind view of every active forward
candidate clock needed by the 3-4 trades-per-weekday research goal. It does not
create or modify a strategy.

## Safety boundary

- Runtime collector status and existing V24.1/V26 inventory files are the only
  dynamic inputs.
- V37 may refresh V24.1/V26 inventories only while both have fewer than 19
  eligible complete weekdays.
- At 19 eligible weekdays, automatic refresh stops. Opening the 20-day validation
  remains an explicit later action under the frozen component protocols.
- V37 never reads a validation trade file, outcome, exit, return, P&L, win rate,
  profit factor, or drawdown.
- V37 does not infer missing candidate timestamps or deduplicate different clocks.
- It reports the sum as raw component candidate supply, never as executed trade
  frequency or economic evidence.
- Any stale, malformed, missing, economically opened, or execution-authorized
  source fails the observer status closed.

## Authority

V37 has no broker module or order path. Python execution, EA consumption, demo,
live, account, terminal, and broker actions remain unauthorized. It cannot admit
a specialist or open a sealed stage.
