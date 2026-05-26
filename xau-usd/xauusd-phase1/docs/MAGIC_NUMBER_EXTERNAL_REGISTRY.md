# Magic Number External Registry

Last updated: 2026-05-26

Phase 1 reserves the `910000-910999` magic-number range for the XAUUSD Master EA program.

| System | Account / scope | Magic namespace | Collision decision |
| --- | --- | --- | --- |
| Phase 1 dry-run shell | XAUUSD Master EA telemetry | `910000-910999` | Reserved for this repo. |
| V61 | Legacy / archived EA | External namespace, not in `910000-910999` | Must remain off the Phase 1 isolated account or be rechecked before paper mode. |
| V77 | Legacy EA | External namespace, not in `910000-910999` | Must remain off the Phase 1 isolated account or be rechecked before paper mode. |
| V80 | Legacy EA | External namespace, not in `910000-910999` | Must remain off the Phase 1 isolated account or be rechecked before paper mode. |
| V85 | Existing deployed EA namespace | External namespace, not in `910000-910999` | Must not share an account with Phase 2 paper mode unless the exact magic range is documented and non-overlap is revalidated. |
| Manual tools | Human/manual intervention | No Phase 1 reserved magic | Manual tools must not create orders inside `910000-910999`. |

## Paper-Mode Rule

Paper mode requires account isolation or a documented cross-EA collision plan before any order-sending code exists. If the account is not isolated, the operator must list every active EA, script, and manual tool namespace and prove no overlap with `910000-910999`.

## Runtime Backstop

`Phase1Magic.mqh` validates the reserved range and checks open positions and pending orders for unknown magic numbers inside `910000-910999`. This registry is the static companion to that runtime check; both must remain clean before paper mode.
