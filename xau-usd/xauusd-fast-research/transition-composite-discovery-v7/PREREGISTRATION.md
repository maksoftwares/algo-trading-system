# Transition Composite Discovery V7

## Purpose

Search a small frozen set of transition composites whose components have
different mechanisms and visibly different weak eras. This is post-selection
discovery on exposed history. It is not an independent test.

## Frozen component pool

- 24640: ancestry residual reacceleration
- 24877: residual breakout
- 24995: single-factor resolution
- 25048: ancestry overshoot reversal

The pool was selected after the V6 component outcomes were visible. The reason
is explicit: 24995 is weak in the first era but strong later, while 25048 is
strong in the first and final eras and weak in the middle. The other two add
different continuation mechanics. No component may be added after composite
outcomes are opened.

## Search space

All component subsets of size two, three, or four are tested. Each subset uses
two deterministic tie policies: component attempt ascending and descending.
That creates exactly 22 composite policies, attempts 25120 through 25141.

Each component first applies its original standalone non-overlap and daily-cap
policy. The composite then orders the retained component trades by entry time
and tie priority, accepts no overlapping position, and allows at most four
entries per UTC day. Returns and costs are not changed.

## Gates and interpretation

The full V6 economic gates remain unchanged. P-values are Bonferroni-adjusted
for all 22 subset/tie policies. A historical economic pass remains selected on
exposed outcomes and must survive separately locked exact raw-tick execution,
independent-period evidence, and prospective shadow observation.

Same-version repair, paid data, model training, and trading authorization are
prohibited.

