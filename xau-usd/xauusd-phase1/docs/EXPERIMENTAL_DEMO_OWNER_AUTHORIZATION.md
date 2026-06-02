# Experimental Demo Owner Authorization

Overall status: PENDING_OWNER_AUTHORIZATION

This document is a fillable owner authorization record for the quarantined experimental demo executor lane only. It does not authorize canonical Phase 2, demo trading as Phase 2 evidence, broker-side production execution, live trading, or real capital.

## Required Answers Before Any Future Experimental Continuation

| Question | Owner answer |
| --- | --- |
| Which account login is whitelisted? | PENDING_OWNER_INPUT |
| Which candidates are explicitly authorized? | PENDING_OWNER_INPUT |
| What daily account-level order cap is allowed? | PENDING_OWNER_INPUT |
| What account-level open exposure cap is allowed? | PENDING_OWNER_INPUT |
| Where is the kill-switch file? | `experimental_demo_kill_switch.txt` in the MT5 Files directory selected by runtime input |
| Who reviews order logs daily? | PENDING_OWNER_INPUT |
| What exact condition stops the experiment? | PENDING_OWNER_INPUT |
| How are open demo orders/positions reconciled at end of day? | PENDING_OWNER_INPUT |

## Required Acknowledgements

```text
ack_phase2_not_authorized:
ack_demo_pnl_not_phase2_evidence:
ack_no_live_or_real_capital:
ack_same_family_not_diversification:
ack_kill_switch_test_required:
```

## Boundary

If any owner field remains pending, the hardened experimental executor source may be reviewed and compiled, but it must not be reattached or redeployed.
