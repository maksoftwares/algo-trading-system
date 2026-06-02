# Experimental Demo Kill Switch

Last updated: 2026-06-02

Overall status: ACTIVE

## File Contract

The executor reads the MT5 Files-directory kill-switch file named by:

```text
InpKillSwitchFileName = experimental_demo_kill_switch.txt
```

If the file exists and contains:

```text
KILL
```

then new experimental demo orders are blocked immediately.

## Intended Use

Use the kill switch when:

```text
wrong account
wrong server
unexpected order volume
spread spike
executor behavior mismatch
manual review requested
owner pause requested
```

## Boundary

The kill switch blocks new orders only. Existing broker positions still require manual terminal review because this experimental lane is not a full canonical position-management system.
