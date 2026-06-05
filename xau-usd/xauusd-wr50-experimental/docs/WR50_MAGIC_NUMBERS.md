# WR50 Magic Numbers

Document date: 2026-06-04

The WR50 experimental namespace is separate from the Phase 1 `910000-910999` namespace.

| Range | Assignment |
| --- | --- |
| `930000-930099` | `WR50_BreakoutEvening_v0` |
| `930100-930199` | `WR50_BreakoutQuality_v0` |
| `930200-930299` | `WR50_BreakoutExit1R_v0` |
| `930300-930399` | Reserved future WR50 EA |
| `930400-930499` | Reserved future WR50 EA |
| `930500-930999` | Reserved |

## Active Assignments

| EA | Short code | Active magic | Comment prefix |
| --- | --- | ---: | --- |
| `WR50_BreakoutEvening_v0` | `BEV0` | `930000` | `WR50\|BEV0` |
| `WR50_BreakoutQuality_v0` | `BQV0` | `930100` | `WR50\|BQV0` |
| `WR50_BreakoutExit1R_v0` | `E1R0` | `930200` | `WR50\|E1R0` |

Every WR50 order must use a magic number inside `930000-930999`. No WR50 EA may share an active magic number.

