# V9 Post-Run Decision

Preregistered code commit: `8fc7f6bf15bd7010e321d3ca252b26ef3c95fdd9`

Decision: **REJECT V9 AND KEEP DEPLOYED V60**

The single permitted retrospective replay preserved V6's exposed August result
but failed the locked preservation gates:

- August through August 25 remained positive at `$17.50`, versus V60 at
  `-$24.87`.
- Full-history net was `$3,638.08`, only `$34.52` above V60 and `$43.26` below
  frozen V6.
- Trade retention was `97.9856%`, below the locked `98%` floor.
- The 17 anti-chase vetoes lost `$16.00` of avoided P/L and had PF `1.148`.
- Six-month net fell to `$1,124.10`, below V60's `$1,139.94` and V6's
  `$1,165.53`.
- Twelve-month net was `$1,714.43`, below V6's `$1,754.28`.
- Both cost-stress scenarios failed annual and recent-window gates.
- Dukascopy same-timing deltas were negative in 2024 and 2026.

Conclusion: the bottom-decile causal rank condition was carrying useful
selectivity. Removing it made the mechanism more frequent but diluted the edge.
No V9 threshold, rule, gate, or output will be tuned or deployed. V60 and frozen
V6 remain unchanged.
