# A1 XAUUSD Effective MT5 Input Integrity Repair Preregistration

Date: 2026-07-12
Status: `PREREGISTERED_NOT_RUN`
Experiment: `A1_XAU_H4_RULE_CLEAN_EFFECTIVE_INPUT_RERUN_V2`
Boundary: research-only Strategy Tester work. No live/demo broker action, chart attachment, preset arming, profile mutation, order placement, or deployment is authorized.

## Review authority and frozen base

- Base commit: `addf272a06d1d795376f2eb0a57741af2c95562b`.
- Independent review: `A1_XAU_H4_PROFIT_PRESERVING_HEDGE_INDEPENDENT_REVIEW_ADDF272A_2026_07_11.md`.
- Independent-review SHA-256: `909ca9d69599a52b418e0445956b518e896f4adc6790c0f0ae83f75e0590b2e2`.
- Locked effective-input contract: `A1_XAU_H4_RULE_CLEAN_EFFECTIVE_INPUT_LOCK_V2.json`.
- Locked-contract SHA-256 after the pre-result completeness amendment below: `73e59226bd447a9e6648493479cf2fc73d2c51b2fe4d906b5b4d1869dd55e0ad`.

The previous `rule_clean_common_risk` result is withdrawn as a qualification result. Its generated INI contained empty legacy-mask values, but the native MT5 report showed effective values `InpBlockedEntryDayHoursCsv=5:20` and `InpBlockedLongEntryHoursCsv=3,10,13,14`. The existing verifier checked the intended INI rather than the effective native-report inputs.

## Objective

Establish one valid rule-clean H4 baseline by:

1. disabling legacy selection masks with an explicit nonempty boolean;
2. parsing every effective EA input from native MT5 HTML;
3. requiring exact equality with the locked contract;
4. rerunning the unchanged first-cross, one-position, fixed-risk, fixed-2R source over the frozen five- and ten-year windows.

This is an evidence-integrity rerun, not a new alpha variant.

## Frozen horizons

- Five-year: `2021-07-01` through `2026-06-30`.
- Ten-year: `2016-07-01` through `2026-06-30`.
- All observations through `2026-06-30` remain development data.

## Frozen architecture

- completed-H4 first cross of the box only;
- long R1/uptrend route only;
- one open H4 position and one position identity;
- market-session permanent expiry;
- minimum-lot excess risk block;
- USD 10,000 reference equity;
- compounding disabled;
- USD 25 fixed initial risk per trade, equal to 0.25% of reference equity;
- maximum H4 open initial risk 0.25%;
- unchanged structural stop;
- fixed 2R target;
- no management overlay.

## Only authorized implementation changes

- Add `InpLegacySelectionMasksEnabled` with default `true` for frozen controls and locked value `false` for this clean run.
- When false, bypass every legacy hour/day mask regardless of string values.
- Set each clean-run legacy-mask string to the explicit nonempty sentinel `__DISABLED__`; an empty string is forbidden because MT5 may retain a prior tester value.
- Add a native MT5 effective-input parser and exact locked-contract verifier.
- Fail on a missing, extra, or unequal locked input.
- Export intended and effective values side by side.
- Capture native leverage, account currency, company/server, terminal build, margin mode, and symbol-contract fields when available.
- Move below-minimum requested-volume blocking into the shared risk-sizing implementation: never round a risk request upward to the broker minimum.
- Log `DEAL_FEE` in the ordinary shared deal ledger.
- Add tests, manifests, cost/funding fields, and a deterministic USD 1,000 feasibility table at 0.25%, 0.50%, and 1.00% risk.

## Forbidden changes

- no signal or breakout threshold change;
- no router change;
- no stop or RR change;
- no session selection;
- no P/L selection or previous-month gate;
- no hedge or dynamic equity throttle;
- no known-loss-date rule;
- no partial close, breakeven, trailing, or exit repair;
- no H4 portfolio composition;
- no R5 sibling or neighboring threshold;
- no new specialist in this experiment;
- no deployment.

## Effective-input validity gates

The experiment is `H4_EVIDENCE_INVALID` if any condition fails:

- every native MT5 effective input exactly equals the horizon-specific locked contract;
- `InpLegacySelectionMasksEnabled=false` is present in the native report;
- no effective legacy hour/day mask is active;
- previous-month P/L gate is false;
- zero `blocked_entry_day_hour` and zero `blocked_long_entry_hour` events;
- zero order failures and zero management failures;
- compile result is exactly 0 errors and 0 warnings;
- source, EX5, config, report, order, deal, signal, and management hashes reconcile;
- all trades reconcile by native position ID;
- P/L is explicitly tester-currency USD;
- actual native leverage and contract specifications are recorded.

## Cost and funding convention

Report:

- native real-tick MT5 result including native spread, commission, swap, and fee;
- expected stress of native plus 0.05R per executed trade;
- hard stress of native plus 0.10R per executed trade.

The exact report must state that a zero native swap/fee observation does not prove zero future CFD financing. A documented broker funding model remains required before promotion.

## H4 survivor gates

All must pass:

- ten-year trades at least 100;
- five- and ten-year net greater than zero;
- five- and ten-year PF at least 1.30;
- hard-stress PF at least 1.20;
- hard-stress expectancy greater than 0R;
- block-bootstrap fifth-percentile expectancy greater than 0R;
- block-bootstrap fifth-percentile PF greater than 1.00;
- maximum native relative floating-equity drawdown no more than 8.00%;
- maximum H4 open initial risk no more than 0.25%;
- top-ten-winning-trades-removed net greater than zero;
- top-three-winning-entry-days-removed net greater than zero;
- at least 6 of 10 nonoverlapping July-to-June buckets positive by exit time;
- early and late halves both positive;
- best year no more than 35% of net;
- best 24-month block no more than 50% of net.

## Locked outcomes

Exactly one status must be assigned:

- `H4_RULE_CLEAN_SURVIVOR`
- `H4_RULE_CLEAN_FAIL`
- `H4_RULE_CLEAN_UNDERPOWERED`
- `H4_CONTRACT_GRANULARITY_INFEASIBLE`
- `H4_EVIDENCE_INVALID`

Any valid economic failure closes this H4 family under the current contract and does not authorize another repair. A valid economic pass blocked only by the minimum contract closes it for the current USD 1,000 Capital.com implementation and preserves it only for a smaller effective contract or materially more capital.

## Forward boundary after any survivor

- H4 standalone forward: longer of 12 calendar months or 30 mature H4 trades.
- Integrated portfolio forward: longer of 6 calendar months or 200 mature portfolio trades.
- Any post-lock strategy change creates a new version and restarts the forward evidence clock.

## Next research dependency

`R6_H4_DISTRIBUTION_BREAK_FAILED_RECLAIM_SHORT_V1` is not authorized until this experiment has a valid reviewed status. No R6 P/L test may be run in this batch.

## Pre-result completeness amendment — 2026-07-12

The first execution attempt stopped at the effective-input gate before its native
performance report was accepted or analyzed. MT5 exposed 224 native inputs while the
initial lock enumerated only the 166 values inherited by the tester INI. The omitted
58 values were unchanged EA defaults, but the stated policy requires a complete native
surface and therefore treated them as disallowed extras.

Before rerunning, those 58 defaults were added once to `native_defaults` in the lock
and explicitly emitted into the tester INI. The verifier now merges that block with
the 166 horizon-specific values and requires exact equality for all 224 inputs in both
the intended INI and native MT5 HTML. No signal, sizing, management, date, risk, stress,
or decision-gate value changed. The rejected partial output is not evidence and will
be replaced by the complete rerun packet.
