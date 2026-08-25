# V13 Pre-Outcome Implementation Fix

The first V13 command stopped during module import, before loading replay data or
producing any strategy result. V12's runner imports a generic `src.scenario`
module name, which resolved to V13's module in the shared process.

The three small immutable helper calculations needed from that runner were
copied locally, removing the colliding import. The frozen policy, inputs,
thresholds, gates, and replay behavior did not change.
