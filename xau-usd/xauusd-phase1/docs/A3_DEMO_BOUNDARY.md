# A3 Demo Boundary

Status: ACTIVE_BOUNDARY_FOR_T17_PREFLIGHT

- A3 login: `1033669`.
- Server marker must include `Demo` or equivalent practice marker.
- Server names containing `live` or `real` are refused.
- XAUUSD only.
- Demo only. No live trading. Canonical Phase 2 status unchanged.
- A2 (`1033030`, `breakout_retest`) is not touched.
- A1 (`1025742`) is touched only by the T0 mutex repair already reported.
- Committed defaults are non-executing.
- Owner execution presets are local-only and must not be committed.
- Execution kill switch file for A3 EAs: `A3_EXECUTION_KILL.txt`; it blocks broker actions while permitting passive startup/logging.
- Full-stop file for A3 EAs: `A3_FULL_STOP.txt`; it refuses init entirely and is not used for ordinary shadow observation.
- No `PositionClose`, `PositionModify`, or `OrderDelete` logic is permitted in EA-T1 or EA-T2.

Attachment is allowed only after `A3_COMBINED_PREFLIGHT_REPORT.md` records PASS for all mandatory gates and the owner signs the packet.
