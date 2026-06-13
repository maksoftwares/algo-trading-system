# P2WEAKNESS BR V1 Runtime Attachment Audit

Status: NO_ACTIVE_P2WEAKNESS_RUNTIME_RISK_OBSERVED

Read-only P2WEAKNESS_BR_V1 runtime attachment audit. This script reads profile files, deployed source, CSV logs, and optionally MT5 open positions/orders; it does not attach charts, deploy files, change presets, restart terminals, create kill switches, or authorize canonical Phase 2/live trading.

Created at UTC: `2026-06-13T20:56:30.403273Z`

## Reviewer Questions

| Question | Answer |
|---|---|
| Is any old `930101` EA still attached? | `NO_PROFILE_EVIDENCE` |
| Is any broker-action-capable P2WEAKNESS chart active? | `NO_PROFILE_EVIDENCE` |
| Are there open positions by old magic `930101`? | `UNKNOWN` |
| Are there open orders by old magic `930101`? | `UNKNOWN` |
| Was the hardened `931000` source deployed? | `YES` |

## Runtime Boundary

- Terminal root: `C:\MT5PortableP2WeaknessDemo`
- MT5 runtime touched by script: `False`
- Standard demo terminal touched: `False`
- New deployments paused: `True`
- Broker-side execution authorized: `False`
- Live/real capital authorized: `False`
- Runtime decision: `KEEP_PAUSED_OR_QUARANTINED_UNTIL_OWNER_AUTH_KILL_SWITCH_AND_REVIEWER_SIGNOFF`

## Runtime Risks

- No active P2WEAKNESS runtime risks were observed by this read-only audit.

## Deployed Source

- Repo source SHA256: `aa92344a8b3e8c74a21443073333a2381e939187b4a5b874287c65fb5f4ec2a7`
- Deployed source exists: `True`
- Deployed source SHA256: `aa92344a8b3e8c74a21443073333a2381e939187b4a5b874287c65fb5f4ec2a7`
- Deployed source matches repo: `True`
- Deployed EX5 exists: `True`
- Deployed source magic: `931000`
- Deployed dry-run default: `true`
- Deployed broker-action default: `false`

## Chart Profile Scan

- Chart directory: `C:\MT5PortableP2WeaknessDemo\MQL5\Profiles\Charts\Default`
- Chart files scanned: `4`
- P2WEAKNESS charts found: `0`

| Chart | Symbol | Expert | Magic | Dry run | Broker action | Evidence |
|---|---|---|---:|---|---|---|
| n/a | n/a | n/a | n/a | n/a | n/a | No P2WEAKNESS chart block found in profile files. |

## Open Exposure

- MT5 bridge status: `SKIPPED_BY_ARGUMENT`
- MT5 bridge note: `MT5 bridge query disabled by argument.`
- Positions with magic `930101`: `0`
- Orders with magic `930101`: `0`
- Positions with magic `931000`: `0`
- Orders with magic `931000`: `0`

## Log Evidence

- Order log exists: `False`
- Startup log exists: `False`
- Kill switch exists: `False`
- Order rows: `0`
- Startup rows: `0`
- Runtime magics observed: `[]`
- Latest order action: ``
- Latest order magic: ``
- Latest guard reason: ``
- Latest startup dry-run: ``
- Latest startup broker-action allowed: ``
- Latest startup status: ``

## Required Before Future Continuation

- Owner authorization fields completed out-of-band.
- Kill switch file created and tested.
- Old 930101 runtime source/chart state stopped or explicitly quarantined.
- Fresh deployment uses only hardened 931000 source and owner-authorized preset.
- Startup log proves account whitelist, auth token, cost-suspension acknowledgement, and intended broker-action mode.
- Reviewer signs off before any P2WEAKNESS continuation.
