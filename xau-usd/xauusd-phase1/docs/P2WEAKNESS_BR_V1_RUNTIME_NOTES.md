# P2WEAKNESS_BR_V1 Runtime Notes

`P2WEAKNESS_BR_V1` is a separate owner-requested experimental demo EA created from the 2026-06-06 demo trade weakness review.

## Boundary

- Non-canonical experimental demo only.
- Does not authorize canonical Phase 2.
- Does not authorize live trading.
- Does not modify or replace the existing running EAs.
- New deployments are paused until governance fixes are reviewed.
- Source defaults and the normal demo preset are review-only and non-executing.
- Owner-authorized demo execution, if ever resumed, must be generated from the separate owner-authorized template after owner authorization is complete.

## Identity

| Field | Value |
|---|---|
| EA file | `Phase2WeaknessBreakoutRetestExecutor.mq5` |
| Run ID | `P2WEAKNESS_BR_V1` |
| Order comment | `P2WEAKNESS_BR_V1` |
| Magic namespace | `931000-931099` |
| Active magic number | `931000` |
| Candidate | `breakout_retest` |
| Symbol | `XAUUSD` |
| Default lot | `0.01` |
| Safe default preset | `Phase2WeaknessBreakoutRetestExecutor.demo_xauusd.set` |
| Owner-authorized template | `Phase2WeaknessBreakoutRetestExecutor.owner_authorized_demo_xauusd.template.set` |
| Signal log | `p2weakness_br_v1_signal_log_xauusd.csv` |
| Startup log | `p2weakness_br_v1_startup_xauusd.csv` |
| Order log | `p2weakness_br_v1_order_log_xauusd.csv` |

## Source Defaults

The committed source defaults are intentionally non-executing:

| Input | Default |
|---|---|
| `InpDryRunOnly` | `true` |
| `InpBrokerActionAllowed` | `false` |
| `InpAllowedAccountLoginsCsv` | blank |
| `InpExperimentalAuthorizationToken` | blank |
| `InpCostSuspensionAcknowledgementToken` | blank |
| `InpCandidateStatus` | `EXPERIMENTAL_QUARANTINE_REVIEW_ONLY` |
| `InpFamilyLifecycleStatus` | `COST_SUSPENDED_CANONICAL` |

## Reviewer-Driven Restrictions

- Only the core `breakout_retest` candidate is executable.
- Weak reviewed variants are not included.
- USDJPY is not included.
- Same-family duplicate exposure is suppressed against known demo-family magic ranges `920000-920999`, `930000-930999`, and `931000-931099`.
- The EA refuses broker-action mode on non-demo server markers, account logins outside `InpAllowedAccountLoginsCsv`, missing experimental authorization, or missing cost-suspension acknowledgement.
- Startup logs include `source_default_safe`, `owner_authorized_set_used`, `experimental_authorization_token_present`, and `cost_suspension_acknowledged`.

## Deployment Evidence

The committed deployment-boundary summary is:

`xau-usd/xauusd-phase1/outputs/reports/P2WEAKNESS_BR_V1_DEPLOYMENT.md`

The P2WEAKNESS-specific governance artifacts are:

- `xau-usd/xauusd-phase1/outputs/reports/P2WEAKNESS_BR_V1_SOURCE_GOVERNANCE_PARITY.md`
- `xau-usd/xauusd-phase1/outputs/reports/P2WEAKNESS_BR_V1_CLEAN_CLONE_RECONCILIATION.md`
- `xau-usd/xauusd-phase1/outputs/reports/P2WEAKNESS_BR_V1_MAGIC_COLLISION_AUDIT.md`
- `xau-usd/xauusd-phase1/outputs/reports/P2WEAKNESS_BR_V1_DEPLOYMENT.md`

The deployment script defaults to report-only/no-copy/no-compile mode. If an explicit future deploy is authorized, it must still avoid closing MT5, restarting MT5, replacing profiles, or attaching charts. The owner-authorized template is not active and is not execution-enabled in the committed repo.
