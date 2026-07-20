# V52 Post-Run Audit

Status: **TERMINAL RESULT; DEVELOPMENT-SELECTION PROVENANCE MISMATCH**

The exploratory command that produced the preregistered development figures
filtered `BREAK_AND_RUN == 1` but did not also exclude rows tagged with another
mechanism. The sealed V52 contract correctly required pure break rows:

```text
BREAK_AND_RUN == 1
DOWNSIDE_IMPULSE_RETEST == 0
OPENING_RANGE_REVERSAL == 0
```

Consequently, the preregistration's 408-trade development description is not
the result of the exact sealed policy. The sealed pure-break implementation
produced 355 development trades, 0.453 per weekday, USD 167.29 net, PF 1.177,
and USD 157.88 closed drawdown.

This mismatch does not rescue or weaken the later result. V52 already failed
the locked final and recent marginal-expectancy gates. It adds a separate reason
not to treat V52 as a valid selected-policy confirmation. Locked files and
outcomes remain unchanged; no same-version repair or execution is authorized.
