# V60 V7-Only Profit-Protection Bypass V20 Preregistration

Date: `2026-08-26`

Status: **HISTORICAL CHALLENGER RESEARCH ONLY**

V17 found that deployed account-level profit protection improves aggregate
profit factor, drawdown, and losing-month severity, while its actions on
`V7_SWING_HEALTH` lost `$19.46` relative to V7's frozen source endpoints. V18
fully removed V7 from the protection basket. V18 gained `$55.13` versus frozen
Dynamic V6 but was rejected because profit factor, drawdown, annual stability,
frequency retention, losing-month burden, and cost-stress gates failed.

V20 tests one narrower structural mechanism and no fitted threshold:

> Bypass account-level open-profit protection only while every open position
> belongs to `V7_SWING_HEALTH`. When any non-V7 position is open, apply the
> unchanged deployed protection logic to the complete basket, including V7.

This distinguishes single-specialist source management from the portfolio
protection use case. It directly addresses V18's broad exemption without
changing any entry, rank, health, cost, sizing, risk, or protection threshold.

## Frozen Mechanism

- Target source: `V7_SWING_HEALTH` only.
- Solo-basket definition: at least one open position and every open position
  has source ID `V7_SWING_HEALTH`.
- During a solo V7 basket, reset the account-level open-profit protection state
  and allow every V7 position to follow its frozen source endpoint.
- During any mixed basket, call the unchanged frozen V6/V60 account-level
  protection implementation on every open position.
- Account protection arm remains `1.50R`.
- Account protection retention floor remains `0.50R`.
- V7 remains subject to every entry, capacity, exposure, drawdown, cost,
  source, emergency, and same-direction rule.
- Vetoed or rejected trades do not enter later challenger health state.
- No parameter sweep or alternative V20 policy is permitted.

## Evidence Boundary

- Historical replay is exposed: candidate entries from `2021-01-01` through
  `2026-06-30` on the frozen five-second runtime path.
- July and August 2026 are exposed diagnostics and cannot nominate or
  authorize V20.
- V17 and V18 were inspected before this hypothesis was registered.
- A historical pass remains post-selection evidence and requires a separately
  locked clean Capital.com forward observer before deployment consideration.

## Acceptance Gates Against Frozen Dynamic V6

Nominal replay must satisfy every gate:

1. Net P/L is not lower.
2. Profit factor is not lower.
3. Maximum closed drawdown is not higher.
4. Maximum floating-equity drawdown is not higher.
5. Every calendar-year P/L is not lower.
6. Final three-, six-, and twelve-month net P/L and profit factor are not
   lower.
7. At least `99%` of deployed V60 closed-trade count and weekday frequency is
   retained.
8. Losing-month aggregate P/L and worst-month P/L are not worse than V6.
9. At least one solo V7 protection cycle and one outcome or portfolio decision
   changes.
10. The replay ends flat, with no flat-suspension or floating-peak deadlock.

The same net, profit-factor, closed-drawdown, equity-drawdown, annual, and
recent-window floors must pass after adding `$0.10` and `$0.20` execution cost
to every accepted trade. No gate may be relaxed after results are observed.

## Decision Vocabulary

- `REJECT_KEEP_V60_AND_FROZEN_V6`
- `HISTORICAL_CHALLENGER_PASSES_CLEAN_FORWARD_REQUIRED`

Both decisions keep `deployment_authorized=false` and
`broker_action_authorized=false`. V20 cannot change demo or live trading.
