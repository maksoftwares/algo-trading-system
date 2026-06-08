# Phase 2X Daily Review Policy

Status: ACTIVE_POLICY

Daily Phase 2X review is mandatory for any owner-authorized demo run. It does not authorize canonical Phase 2, live trading, real capital, cost-suspension removal, or same-family diversification claims.

## Required Daily Checks

- Account/server is demo or practice.
- Symbol is `XAUUSD`.
- Magic is `931000`.
- Lot is fixed `0.01`.
- Orders per day are within owner cap.
- Family open positions are at most `1`.
- Estimated cost R is at most `0.15`.
- Kill switch state is recorded.
- Startup, signal, order, and broker-history evidence reconcile.

## Hard Stop Conditions

Stop the next day if any live/real server marker appears, lot exceeds `0.01`, magic is not `931000`, symbol is not `XAUUSD`, orders exceed cap, family exposure exceeds cap, cost R exceeds `0.15`, broker action occurs without required tokens, kill switch fails, or logs cannot reconcile broker history.
