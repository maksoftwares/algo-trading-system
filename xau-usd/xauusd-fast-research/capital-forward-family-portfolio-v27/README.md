# Capital Forward Family Portfolio V27

V27 is the preregistered family-level evaluation for the frozen V24.1 continuous
microburst and V26 gap-restart hypotheses. It does not create another signal and
does not inspect component economics before their sealed stages open.

Both components must pass their original gates and the stricter V27 external
selection gate. There is no outcome-based single-lane fallback. Passing trades
are combined by a fixed chronological router with one satellite position at a
time and at most three selected satellite trades per UTC day.

The frozen Core remains byte-identical. V27 tests whether the satellite sleeve
adds the 2.386973 to 3.386973 trades per weekday required to project the existing
0.613027 Core rate into the 3-4 total target while retaining positive marginal
economics and the locked account-risk ceiling.

Nothing in this package authorizes model training, Python predictions, EA
consumption, demo trading, live trading, or broker action.
