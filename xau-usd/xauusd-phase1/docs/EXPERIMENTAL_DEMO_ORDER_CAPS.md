# Experimental Demo Order Caps

Last updated: 2026-06-02

Overall status: ACTIVE_GUARDRAILS

## Default Caps

| Cap | Default | Scope |
| --- | ---: | --- |
| Fixed lot | 0.01 | Per order |
| Orders per day | 12 | Per chart instance |
| Orders per day | 24 | Account-level experimental cap |
| Open exposure | 1 | Per chart instance |
| Open exposure | 3 | Account-level experimental cap |
| Minimum seconds between orders | 300 | Per chart instance |
| Deviation | 50 points | Per order |

## Account-Level Counter

The executor stores the daily account-level order count in an MT5 GlobalVariable named:

```text
P2DEMO_ORD_<account_login>_<yyyymmdd>
```

This counter is used only for experimental demo governance. It is not a broker-side risk system and cannot authorize canonical Phase 2.

## Exposure Counting

Account-level open exposure counts positions and orders with experimental magic numbers in the `920000-920999` namespace.

## Change Rule

Any cap increase requires a new dated owner authorization artifact. Cap reductions are allowed at any time.
