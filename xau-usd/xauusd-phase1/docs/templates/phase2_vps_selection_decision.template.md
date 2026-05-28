# Phase 2 VPS Selection Decision Template

Use this template to fill the `Decision Record` table in `docs/PHASE2_VPS_SELECTION_MATRIX.md` after the VPS is selected and latency evidence exists.

Do not change `Overall status` in `PHASE2_VPS_SELECTION_MATRIX.md` to `PASS` until every value below is real and no placeholder remains.

```markdown
## Decision Record

| Field | Value |
| --- | --- |
| Selected provider | <provider name> |
| Selected region | <region> |
| Selected plan | <plan name> |
| Monthly cost | <amount and currency> |
| Backup method | <snapshot/file backup method and frequency> |
| Monitoring endpoint or scheduler | <external monitor or scheduler> |
| Recovery access owner | <owner name> |
| Latency evidence path | outputs/reports/PHASE2_VPS_LATENCY_REPORT.md |
| Decision date | <YYYY-MM-DD> |
| Owner acceptance | Phase 2 paper-mode only accepted; no live capital; no broker execution until readiness PASS |
```

Minimum acceptable decision:

- 2 vCPU / 4 GB RAM or better
- 60 GB SSD/NVMe or better
- Windows Server compatible with MT5 Portable
- NTP/time sync available
- RDP or console recovery path available
- Backup method selected
- Latency report generated and PASS
