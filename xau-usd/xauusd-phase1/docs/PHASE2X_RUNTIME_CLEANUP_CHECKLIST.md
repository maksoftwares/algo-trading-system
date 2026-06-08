# Phase 2X Runtime Cleanup Checklist

Status: CHECKLIST_ONLY

This checklist prepares the isolated demo runtime before any Phase 2X owner-authorized attach. It does not authorize canonical Phase 2, live trading, real capital, cost-suspension removal, or same-family diversification claims.

## Required Evidence

- Old magic `930101` positions are closed or absent.
- Old magic `930101` pending orders are closed or absent.
- Old magic `930101` charts are detached or explicitly quarantined.
- Current magic `931000` source/preset is ready.
- No open same-family exposure exists before attach.
- No existing P2WEAKNESS orders today violate caps.
- Kill-switch file was created and tested.
- Demo/practice account is confirmed.
- Owner authorization is valid and unexpired.

Any item that cannot be verified from files must be marked `PENDING_MANUAL_CONFIRMATION`. Phase 2X preflight cannot PASS until those items are resolved.
