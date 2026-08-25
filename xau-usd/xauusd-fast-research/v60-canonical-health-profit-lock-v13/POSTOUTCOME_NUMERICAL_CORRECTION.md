# V13 Post-Outcome Numerical Correction

The first completed replay showed August V13 and frozen V6 had the same 21
trades, P/L, PF, and drawdown. The net gate nevertheless failed because the
recomputed sum was `3.5e-14` below the JSON reference.

The comparison now uses the same `1e-9` numerical tolerance already used by the
historical floor gates, and the retained candidate-ID set is checked explicitly
instead of being recorded as a constant.

No trade, policy action, threshold, P/L value, or substantive acceptance gate
changed. V13 remains rejected on historical net/PF, 12-month net, 2022 annual
performance, and both cost-stress comparisons.
