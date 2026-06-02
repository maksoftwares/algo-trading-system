# Experimental Demo Kill-Switch Test

Overall status: PENDING_TEST

This test is required before any future reattachment or redeployment of the quarantined experimental demo executor. It is not Phase 2 authorization.

## Test Procedure

1. Create the MT5 Files-directory kill-switch file named by `InpKillSwitchFileName`.
2. Put the text `KILL` in the file.
3. Start or reload the experimental demo executor on a demo chart with owner-approved account/candidate inputs.
4. Confirm startup or pre-order checks report kill switch active.
5. Confirm no new demo order is sent while the file contains `KILL`.
6. Remove or clear the file only after owner review.
7. Record evidence in the daily review template.

## Pass Rule

```text
PASS only if no new order can be sent while kill switch is active.
```

## Boundary

The kill switch blocks new orders only. It does not manage existing broker positions and does not make the experimental lane canonical.
