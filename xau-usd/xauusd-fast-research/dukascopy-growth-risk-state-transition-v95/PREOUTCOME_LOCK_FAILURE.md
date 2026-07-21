# V95 Pre-outcome Lock Failure

V95 is retired without XAU outcome evaluation.

The source-only contract lock failed while generating the preregistered policy
manifest. `RISK_GROWTH_CONVERGENCE` produced zero policies satisfying the locked
source-event density and long/short balance gates; 200 were required. The exact
exception was:

```text
Only 0 source-eligible V95 policies for RISK_GROWTH_CONVERGENCE; required 200
```

The growth-risk parquet and manifest hashes matched the bound configuration.
No XAU bars, labels, trades, or P&L were opened for policy admission, no strategy
was scored, and no threshold was changed after the failure. V95 therefore has no
valid contract lock and must not run. Any transition redesign belongs to a new
version and must be justified by source-only density evidence before outcomes.
