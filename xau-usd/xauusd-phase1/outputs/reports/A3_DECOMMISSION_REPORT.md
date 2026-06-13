# A3 Decommission Report

Status: **PASS**

## Boundary

- A3 login: `1033669`.
- Demo only; canonical Phase 2 unchanged.
- A2 remains untouched.
- Committed defaults remain non-executing.

## Checks

| Check | Status | Evidence |
|---|---|---|
| old_p2weakness_runtime_process_stopped | PASS | process_count=0 |
| wr50_execution_lane_process_stopped | PASS | process_count=0; observer roots are telemetry-only and not counted |
| p2weakness_chart_profile_detached | PASS | NO_PROFILE_EVIDENCE |
| p2weakness_runtime_logs_archived | PASS | order_log_exists=False; startup_log_exists=False |
| no_open_930101_positions_or_orders | PASS | source=C:\Program Files\MetaTrader 5\terminal64.exe; positions=0; orders=0 |
| no_stale_committed_execution_presets | PASS | execution_enabled_count=0 |

## Evidence

```json
{
  "p2weakness_audit_status": "NO_ACTIVE_P2WEAKNESS_RUNTIME_RISK_OBSERVED",
  "decommission_archive_note": "P2WEAKNESS CSV runtime logs were moved under C:/MT5PortableP2WeaknessDemo/_codex_quarantine/a3_decommission_*.",
  "exposure_audit": {
    "created_at_utc": "2026-06-13T20:57:19.488511Z",
    "terminal": "C:\\Program Files\\MetaTrader 5\\terminal64.exe",
    "status": "PASS",
    "positions": [],
    "orders": [],
    "account_login": "1025742",
    "account_server": "Capital.ComMena-Demo",
    "total_positions": 8,
    "total_orders": 0
  }
}
```
