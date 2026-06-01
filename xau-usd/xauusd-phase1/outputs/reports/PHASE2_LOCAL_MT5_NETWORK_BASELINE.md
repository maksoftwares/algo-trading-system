# Phase 2 Local MT5 Network Baseline

Overall status: PASS

## Purpose

This report gives a sanitized local MT5 broker-access baseline before VPS selection. It is evidence-only and does not authorize Phase 2, paper trading, demo trading, broker execution, or live capital.

## Summary

| Samples | Latest Ping | Median Ping | Best Ping | Worst Ping | Latest Access Point |
| --- | --- | --- | --- | --- | --- |
| 5761 | 128.54 ms | 129.78 ms | 121.76 ms | 312.50 ms | 2 |

## Access Point Breakdown

| Access Point | Samples | Median Ping | Best Ping | Worst Ping |
| --- | --- | --- | --- | --- |
| 1 | 20 | 174.01 ms | 140.84 ms | 214.80 ms |
| 2 | 5732 | 129.78 ms | 125.76 ms | 312.50 ms |
| 3 | 9 | 170.48 ms | 121.76 ms | 235.49 ms |

## Recent Authorization Pings

| Timestamp | Server | Access Point | Ping |
| --- | --- | --- | --- |
| 2026-05-28 12:00:13.460000 | Capital.ComMena-Live | 1 | 178.49 ms |
| 2026-05-28 12:00:20.686000 | Capital.ComMena-Live | 3 | 174.52 ms |
| 2026-05-28 12:00:25.988000 | Capital.ComMena-Live | 3 | 174.52 ms |
| 2026-05-28 12:00:27.501000 | Capital.ComMena-Live | 1 | 185.76 ms |
| 2026-05-29 19:13:34.641000 | Capital.ComMena-Live | 2 | 310.73 ms |
| 2026-05-29 19:13:42.157000 | Capital.ComMena-Live | 1 | 174.55 ms |
| 2026-05-31 10:37:56.114000 | Capital.ComMena-Live | 1 | 176.40 ms |
| 2026-06-01 03:13:35.060000 | Capital.ComMena-Live | 1 | 167.98 ms |
| 2026-06-01 03:13:40.591000 | Capital.ComMena-Live | 2 | 128.54 ms |
| 2026-06-01 03:17:38.093000 | Capital.ComMena-Live | 2 | 128.54 ms |

## VPS Selection Use

- A candidate VPS should be compared against this local baseline using `PHASE2_VPS_LATENCY_REPORT.md`.
- Prefer a VPS/region that materially improves on local median ping and has 0% packet loss.
- If a VPS cannot beat this local baseline, owner review is required before treating it as an operational improvement.
- MT5 terminal logs do not expose a stable broker DNS endpoint here, so the VPS latency packet still needs broker endpoint evidence from the selected VPS or MT5 connection UI/logs.

## Privacy Boundary

- Account identifiers and previous authorization IP addresses are intentionally excluded.
- Source log lines are not copied into this report.
- No credentials, tokens, or server-cache files are included.

## Source

- Logs directory: `C:\MT5PortableGoldMission\logs`
