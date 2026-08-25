# V12 Post-Run Decision

Preregistered code commit: `4db9a1d268047920ecebc25a1b7f541d4893c751`

Decision: **REJECT V12 AND KEEP DEPLOYED V60**

The canonical alpha-health ledger fixed V6's stressed annual instability and
reproduced frozen V6 nominally, but it failed the locked closed-drawdown gates:

- Nominal results matched V6 exactly: 1,377 trades, `$3,681.34`, PF `1.7377`,
  closed drawdown `$217.46`, equity drawdown `$238.28`, and `99.0647%` retention.
- August remained `$17.50` at PF `1.1621` and closed drawdown `$56.69`.
- Twelve V2 vetoes and one anti-chase veto retained their positive component
  evidence; Dukascopy delta remained `$61.49` with no harmed year.
- At `+$0.10`, net improved by `$93.87` and every annual delta was nonnegative,
  but closed drawdown was `$221.81` versus V60's `$220.41`.
- At `+$0.20`, net improved by `$86.46` and 2021 improved by `$8.39`, fixing the
  V6 annual failure, but closed drawdown was `$224.20` versus V60's `$222.29`.
- Stressed sampled equity drawdown was exactly equal to V60, but the contract
  requires both equity and closed-trade drawdown not to worsen.

The result supports separating alpha health from execution-cost accounting, but
V12 is not the required all-gate challenger. The closed-drawdown gate will not be
relaxed after seeing this result. No V12 policy, label, gate, or output will be
tuned or deployed. V60 and frozen V6 remain unchanged.
