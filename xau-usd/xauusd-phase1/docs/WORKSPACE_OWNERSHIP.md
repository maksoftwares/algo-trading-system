# Workspace Ownership And Deployment Paths

Last updated: 2026-05-22

## Canonical Repository

The canonical project source is the GitHub repository:

```text
https://github.com/maksoftwares/algo-trading-system
```

Any Windows path in `agent.md`, reports, or logs is machine-local evidence, not a requirement for another reviewer.

## Active Development Machine

Current active workspace:

```text
C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system
```

Current MT5 Portable deployment target:

```text
C:\MT5PortableGoldMission
```

These paths reflect the machine that generated the current Phase 1 dry-run telemetry.

## Reviewer Machines

A reviewer may clone the repository to a different user profile or drive, such as:

```text
C:\Users\DELL\...
```

That is expected. Reviewers should use committed source files and committed small evidence bundles first, then regenerate local runtime evidence only after updating deployment paths for their own MT5 installation.

## Handoff Rule

When the project moves to another machine:

1. Update `agent.md` with the new workspace root and MT5 target.
2. Regenerate Phase 1 status reports from the new machine.
3. Preserve the old machine's review bundles as historical evidence.
4. Do not compare absolute file paths across machines as if they were stable identifiers.
