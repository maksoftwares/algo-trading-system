# V98 Causal Event Near-Miss Ranker Result

Decision: `V98_ENGINEERING_INVALIDATED_TERMINAL`

V98 opened its immutable Discovery marker and then stopped before producing any
policy metric or selected-trade ledger. The first policy raised `V98
calibration target is outside candidate support`.

The source-only census had measured roughly 53 raw event times per weekday, but
the locked grid did not preregister an executable-support census after the
side-correct next-bar spread and risk filters. Post-invalidation diagnosis
showed minimum calibration support ranging from 0.09 to 1.23 unique events per
weekday across the five exit profiles, below parts of the locked 0.9-1.8/day
target grid.

V98 will not be patched or rerun. It produced no valid P&L, PF, drawdown, AUC,
or frequency result. Confirmation and Final remain sealed. V59/V60 remain
byte-identical and no execution authority is granted.
