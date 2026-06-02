# Phase 2B Passive Observer Governance

Phase 2B passive observers are runtime telemetry tools for separate Phase 0R candidates. They do not authorize paper mode or live mode.

Allowed runtime behavior:

- observe price
- calculate candidate context
- calculate would-signal state
- calculate theoretical entry, stop, and targets
- calculate projected measured cost_R
- write CSV telemetry

Forbidden behavior:

- creating, modifying, or closing broker positions
- routing candidate signals to execution code
- changing existing canonical EAs
- promoting a draft candidate to paper mode

Each observer row must contain the passive safety fields required by `OBSERVER_LOG_SCHEMA.md`.
