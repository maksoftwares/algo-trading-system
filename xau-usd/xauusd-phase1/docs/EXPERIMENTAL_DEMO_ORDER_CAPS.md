# Experimental Demo Order Caps

Last updated: 2026-06-08

Overall status: ACTIVE_GUARDRAILS

## Default Caps

| Cap | Default | Scope |
| --- | ---: | --- |
| Fixed lot | 0.01 | Per order |
| Orders per day | 12 | Per chart instance |
| Orders per day | 24 | Account-level experimental cap |
| Open exposure | 1 | Per chart instance |
| Open exposure | Unlimited | Account-level experimental demo policy; no account-level open-position cap is enforced |
| Minimum seconds between orders | 300 | Per chart instance |
| Deviation | 50 points | Per order |

## Account-Level Counter

The executor stores the daily account-level order count in an MT5 GlobalVariable named:

```text
P2DEMO_ORD_<account_login>_<yyyymmdd>
```

This counter is used only for experimental demo governance. It is not a broker-side risk system and cannot authorize canonical Phase 2.

## Exposure Counting

Account-level open exposure is still counted and logged for review, but it is no longer used as a blocking cap in the standard demo executor.

## Change Rule

Any cap increase requires a new dated owner authorization artifact. Cap reductions are allowed at any time.
