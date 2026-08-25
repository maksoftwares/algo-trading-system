# V11 Post-Run Decision

Preregistered code commit: `283329c793061a52ca45143722060a6942a53067`

Decision: **REJECT V11 AND KEEP DEPLOYED V60**

The one-close persistence rule preserved the exposed August improvement and
passed all nominal V60 comparison gates, but failed the frozen V6 and cost gates:

- August remained `$17.50` at PF `1.1621` and closed drawdown `$56.69`.
- Full-history net was `$3,675.01`, or `+$71.45` versus V60 but `$6.33` below V6.
- PF was `1.7355`, below V6's `1.7377`.
- Trade retention was `99.1367%`.
- Eleven V2 vetoes avoided `$45.86` at PF `0.0466`; the anti-chase veto avoided
  `$25.59` at PF `0.0`.
- The persistence delay retained a useful 2022 loss that V6 vetoed, removing
  `$6.33` of V6's benefit.
- It did not retain the harmful `+$0.20` 2021 winner because the source was
  degraded in both shifted windows; 2021 still fell `-$3.57` versus V60.
- At `+$0.10`, closed drawdown increased from `$220.41` to `$221.81`.
- At `+$0.20`, closed drawdown increased from `$222.29` to `$224.20`.
- Dukascopy remained nonnegative in every year, but its total delta `$56.00` was
  below V6's `$61.49`.

Persistence does not address the actual failure: hypothetical extra execution
cost changes the health state itself. No V11 rule, threshold, gate, or output
will be tuned or deployed. V60 and frozen V6 remain unchanged.
