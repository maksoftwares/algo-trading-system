# P2WEAKNESS BR V1 Magic Collision Audit

Status: PASS

Magic collision audit for experimental namespaces. PASS does not authorize deployment or trading.

Created at UTC: `2026-06-08T07:17:07.102538Z`

- P2WEAKNESS namespace: `931000-931099`
- Active magic: `931000`
- Runtime previous-magic warning: `True`

| Check | Status | Evidence |
|---|---|---|
| source_magic_in_p2weakness_namespace | PASS | value=931000; allowed=931000-931099 |
| safe_preset_magic_in_p2weakness_namespace | PASS | value=931000; allowed=931000-931099 |
| owner_preset_magic_in_p2weakness_namespace | PASS | value=931000; allowed=931000-931099 |
| active_magic_is_931000 | PASS | value=931000; expected=931000 |
| p2weakness_not_inside_wr50_namespace | PASS | P2WEAKNESS=931000-931099; WR50=930000-930999 |
| active_magic_values_unique | PASS | duplicates=none |
| registry_mentions_p2weakness_namespace | PASS | registry updated |

## Active Assignments

| EA | Magic |
|---|---:|
| WR50_BreakoutEvening_v0 | 930000 |
| WR50_BreakoutQuality_v0 | 930100 |
| WR50_BreakoutExit1R_v0 | 930200 |
| P2WEAKNESS_BR_V1 | 931000 |
