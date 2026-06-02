# Separate EA Boundary

Phase 0R and Phase 2B passive observers are separate from the current canonical EA lane.

They do not:

- modify existing Phase 0 strategy files
- modify current accepted or rejected expert logic
- change the measured-cost decision for the breakout-retest family
- authorize paper-mode execution
- authorize live execution

They may:

- observe price
- calculate candidate signals
- calculate theoretical entry, stop, and targets
- calculate projected cost_R
- write CSV logs
- write summary reports
- display passive dashboard information

Every runtime row must include:

```text
dry_run=true
trade_permission=false
broker_action_allowed=false
phase2_execution_authorized=false
```
