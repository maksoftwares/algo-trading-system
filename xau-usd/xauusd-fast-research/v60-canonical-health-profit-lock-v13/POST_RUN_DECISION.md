# V13 Post-Run Decision

Preregistration commit: `af5359f3`

Implemented pre-outcome at commits `1ca02601` and `e16f9040`. The post-outcome
floating-point correction at `ec0a034e` changed no trade or metric.

Decision: **REJECT V13 AND KEEP DEPLOYED V60**

V13 proved that the conservative individual lock can reduce historical
drawdown, but it did not preserve the frozen V12/V6 edge:

- V13: 1,395 trades, `$3,649.55` net, PF `1.7338`, closed drawdown `$213.83`,
  equity drawdown `$231.99`.
- Frozen V12/V6: 1,377 trades, `$3,681.34` net, PF `1.7377`, closed drawdown
  `$217.46`, equity drawdown `$238.28`.
- Drawdown improved by `$3.63` closed and `$6.29` equity versus V12, but net fell
  `$31.79` and PF fell `0.0039`.
- The 12-month result was `$1,748.63`, `$5.65` below V12. The 3- and 6-month
  windows were preserved or improved.
- 2022 was `$19.77` worse than V60, so the annual stability gate failed.
- At `+$0.10`, V13 net was `$3,537.43` and closed drawdown `$215.15`; at
  `+$0.20`, net was `$3,362.43` and closed drawdown `$221.39`. Drawdown improved,
  but both stressed net/PF and annual gates failed versus V12.
- The policy armed 625 historical positions and closed 27. Earlier closes freed
  capacity and changed dynamic source-health paths, producing 1,395 closes rather
  than V12's 1,377.

## August hard objective

V13 preserved V6 exactly through August 25: 21 trades, `$17.50` net, PF
`1.1621`, and `$56.69` closed drawdown, versus V60's `-$24.87`.

However, it made zero August managed closes. It therefore did not create the
August improvement; the frozen V6 entry vetoes did. Ten retained trades reached
the armed state but none returned to the `0.25R` floor before their broker exit.

## Conclusion

The universal P05 profit lock is not the required challenger. Its risk benefit
is real but its opportunity-cost and path-coupling damage are too large. No
threshold, source exception, or gate will be tuned in V13. V60 remains deployed,
V6 remains read-only, and clean forward evidence remains mandatory.
