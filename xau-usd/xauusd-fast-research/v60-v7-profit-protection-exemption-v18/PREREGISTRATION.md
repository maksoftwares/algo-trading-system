# V60 V7 Profit-Protection Exemption V18 Preregistration

Date: `2026-08-25`

Status: **HISTORICAL CHALLENGER RESEARCH ONLY**

V17 found that account-level profit protection is beneficial overall but that
its 40 actual `OPEN_PROFIT_GIVEBACK` closes involving `V7_SWING_HEALTH` lost
`$19.46` relative to V7's frozen source endpoints and were negative in two of
three fixed historical folds. V18 tests exactly one mechanism and no threshold:

> Exclude `V7_SWING_HEALTH` positions from both the P/L calculation and close
> set of the account-level open-profit protection basket. V7 positions retain
> their frozen source exits. Every other V60/V6 entry, exit, veto, risk,
> capacity, and protection rule remains unchanged.

The challenger is layered on frozen Dynamic V6, not on a newly selected entry
policy. The full tick-runtime replay must resolve all capacity and overlap
changes caused by allowing V7 positions to remain open.

## Frozen Mechanism

- Exempt source: `V7_SWING_HEALTH` only.
- Account-level protection arm: unchanged at `1.50R` for non-exempt positions.
- Account-level protection retention floor: unchanged at `0.50R` for
  non-exempt positions.
- When only exempt positions are open, account-level profit protection is
  inactive and V7 follows its source exit.
- When exempt and non-exempt positions overlap, only non-exempt positions
  contribute to basket risk/P&L and only non-exempt positions are closed by a
  basket giveback.
- V7 remains subject to every entry, exposure, drawdown, cost, source, and
  emergency rule.
- No individual profit lock, monthly rule, spread change, rank change, sizing
  change, or same-day cluster rule is added.

## Evidence Boundary

- Historical replay: exposed 2021-01-01 through 2026-06-30 candidate entries.
- July and August outcomes are exposed and cannot nominate or authorize V18.
- The August broker snapshot does not contain V7's unprotected future source
  exit after its actual basket close, so V18 must report August as
  `NOT_EVALUABLE_WITH_FROZEN_ENDPOINT` rather than impute an outcome.
- Capital.com forward demo confirmation is mandatory before any deployment
  consideration.

## Acceptance Gates Against Frozen V6

Nominal replay must satisfy all:

1. Net P/L is not lower.
2. Profit factor is not lower.
3. Maximum closed drawdown is not higher.
4. Maximum floating-equity drawdown is not higher.
5. Every calendar year P/L is not lower.
6. Three-, six-, and twelve-month net P/L and profit factor are not lower.
7. At least 99% of V60 closed-trade frequency is retained.
8. Losing-month P/L burden and worst month are not worse; losing-month count is
   reported but is not a knife-edge optimization gate.
9. At least one accepted trade outcome or portfolio decision changes, proving
   the mechanism was exercised.
10. No open position, flat-suspension deadlock, or floating-peak deadlock remains.

The same net, PF, closed-drawdown, equity-drawdown, annual, and recent-window
floors must pass with an additional `$0.10` and `$0.20` charged per accepted
trade. No gate may be relaxed after results are seen.

## Decision Vocabulary

- `REJECT_KEEP_V60_AND_FROZEN_V6`
- `HISTORICAL_CHALLENGER_PASSES_CLEAN_FORWARD_REQUIRED`

Even a passing result has `deployment_authorized=false` and
`broker_action_authorized=false`. V18 cannot replace the deployed V60 policy or
the frozen V6 observer without clean causal forward evidence.
