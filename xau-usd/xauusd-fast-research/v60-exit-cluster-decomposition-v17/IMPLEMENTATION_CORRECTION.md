# V17 Implementation Correction

Date: `2026-08-25`

The first diagnostic execution correctly reproduced V60 and V6, then showed
that the preregistered `protection_changed` definition also counted normal
`SOURCE_EXIT` rows whose replay settlement timestamp differed from the frozen
endpoint by a few seconds. That timestamp drift is operationally real but is
not a portfolio-protection action.

Before issuing the final V17 decision, the report was corrected to distinguish:

- `protection_changed`: the original preregistered broad timestamp/P&L flag;
- `protection_action`: close reason is `OPEN_PROFIT_GIVEBACK`;
- `pnl_changed`: protected P/L differs from endpoint P/L.

The preregistered minimum of 30 "protected closes" is interpreted as 30 actual
`OPEN_PROFIT_GIVEBACK` actions. No threshold, cohort definition, fold, or
outcome was changed. This correction was made after a preliminary aggregate was
visible, so it is disclosed rather than silently folded into the
preregistration. V17 remains an exposed diagnostic and cannot authorize a
trading change.
