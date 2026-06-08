# Experimental Demo Deployment Freeze Policy

Status: ACTIVE

This policy applies to any non-canonical experimental demo executor that contains broker-action code, including `Phase2ExperimentalDemoExecutor.mq5`, `Phase2WeaknessBreakoutRetestExecutor.mq5`, and WR50 experimental execution helpers.

## Freeze Rule

While an experimental executor is attached or deployable, do not change any of the following without a documented owner/reviewer note:

| Area | Rule |
|---|---|
| Source | No source change while attached without a runtime note and post-change governance audit. |
| Preset | No preset change while attached. Use a new versioned preset instead. |
| Chart state | No attach, detach, profile replacement, or chart modification without a runtime note. |
| Magic numbers | No magic-number change without updating the registry and collision audit. |
| Tokens | No owner-token or cost-acknowledgement change without an owner note. |
| Caps | No increase to daily order cap, exposure cap, duplicate-family cap, lot size, or spread/cost guard without review. |
| Runtime | No terminal restart, profile replacement, or EA replacement as part of governance-only fixes. |

## Current P2WEAKNESS Boundary

`P2WEAKNESS_BR_V1` is paused for new deployments until the reviewer-requested governance fixes are reviewed. Source defaults and the normal demo preset are non-executing. Any future owner-authorized demo use must be separated by preset, magic number, order comment, logs, and startup audit fields.

## Authority

This freeze policy does not authorize canonical Phase 2, paper-mode broker execution, live trading, or real capital.
