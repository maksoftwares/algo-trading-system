# Sealed Forward Frequency Observer V37

Read-only observer for the active XAUUSD forward candidate clocks:

- frozen R2/R3 Core adapter V28;
- frozen R1 adapter V29;
- frozen R4 adapter V34;
- frozen R5 adapter V35;
- quote-microburst V24.1;
- gap-restart V26.

The observer reports liveness, cumulative candidate supply, source quality, and
sealed-stage progress. It cannot calculate trade outcomes, combine P&L, place an
order, or call a broker API. Candidate totals are not represented as executed
trade frequency because cross-clock overlap and portfolio constraints have not
yet been resolved.
