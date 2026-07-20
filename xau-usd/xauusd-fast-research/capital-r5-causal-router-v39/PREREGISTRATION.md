# Capital R5 Causal Router V39 Preregistration

## Purpose

V35 can generate frozen R5 candidate facts, and V38 can resolve their component
outcomes. V39 is the separately locked successor that lets the frozen V11
180-day router learn from those prospective labels without retrospective
information. It does not change a signal, geometry, component weight, router
parameter, or execution rule.

## Frozen policy

- Router attempt `27135`, ID `16df08f0e24d9d95`.
- `TRAILING_DRAWDOWN_GATE` over 180 days.
- Minimum history: five component outcomes.
- Drawdown pass threshold: `2.0 R`.
- Cold start: half weight.
- Weak multiplier: `0.25`.
- Base component weights: `1.0`, `0.25`, `0.75`, and `0.75` for attempts
  `23925`, `24877`, `24995`, and `25048` respectively.

The V11 manifest row and 330 selected historical trades must reproduce before
the forward service can run.

## Causal history

For a candidate at time `T`, historical V9 outcomes remain eligible when their
exit is strictly before `T`. A V38 prospective outcome is eligible only when all
of these are true:

1. Its resolution status is `EXECUTED`.
2. Its exit time is strictly before `T`.
3. Its recorded causal knowledge time is strictly before `T`.

Rejected component candidates never enter router history. Outcomes at exactly
`T` are excluded. Later outcomes cannot modify a route decision already
appended. History is ordered by exit time before drawdown is calculated.

V39 waits when V38 has not yet consumed the complete V35 candidate prefix or
when V38's status predates V35's status. This prevents a poll-order race from
freezing a route before the outcome resolver has had a chance to process the
available evidence.

## Integrity and authority

V39 verifies the frozen V35, V38, V9, and V11 hashes. It verifies V38's own
candidate and resolution prefix anchors, then records independent prefix anchors
for both inputs and its routed output. Any mutation, truncation, partial record,
dependency change, or authority flag fails closed.

V39 imports no MT5 package, opens no aggregate economics, and has no execution
path. Model training, Python prediction, EA consumption, demo/live trading, and
broker action remain false.
