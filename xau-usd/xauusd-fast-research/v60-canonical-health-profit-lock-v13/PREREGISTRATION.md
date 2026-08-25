# V60 Canonical Health Profit Lock V13 Preregistration

## Objective

Test whether the frozen V12 entry policy can keep its profitable August result
and established V6 edge while a conservative causal per-position profit lock
removes V12's small closed-drawdown failure under execution-cost stress.

August improvement is a hard objective. A policy that makes August profitable by
reducing long-history, 3/6/12-month, annual, cross-feed, cost-stress, frequency,
or drawdown evidence is rejected.

## Frozen policy

V13 keeps V12's canonical alpha-health ledger, V2 source-health veto,
V57 anti-chase rule, dynamic retained path, candidate population, sizing,
portfolio protection, account-risk engine, and acceptance gates unchanged.

It adds one causal per-position rule:

1. Track executable open P/L from five-second quote states.
2. Arm after open P/L reaches `1.50R` of the position's initial risk.
3. If the armed position later falls to or below `0.25R`, close it at the current
   executable quote.
4. Otherwise preserve the source exit.

There is no peak-trailing term, no source-specific exception, no threshold grid,
and no post-run tuning. A managed close is fed back into V12's dynamic source
health at its actual managed P/L and time.

## Why this rule

The earlier exposed individual-protection study found that this exact high-arm,
low-floor policy improved all-history net/PF/drawdown and made no change to 2026
H1. More aggressive policies damaged recent profit. V12 failed only because its
stressed closed drawdown was `$1.41` and `$1.91` above V60, while its equity and
terminal wealth remained higher. The conservative rule is therefore a
pre-existing causal risk hypothesis, not a threshold fitted to V12's drawdown
sequence.

The prior study did not select this policy on its development rule, and all of
its outcomes are exposed. Reusing it is post-hoc and cannot create independent
validation.

## August evidence

Before evaluating the policy, V13 freezes:

- the 24 resolved V60 broker trades through `2026-08-25T01:01:06.651Z`;
- each position's actual entry, direction, entry price, and initial risk; and
- 19,754 five-second executable Capital.com quote states covering those paths.

The snapshot builder applies no policy and records `policy_evaluated=false`.
V13 then applies the unchanged V12 August veto set and tests the profit lock only
on retained trades. The August data are exposed diagnostics, not a holdout.

## Hard acceptance gates

V13 is rejected unless every retrospective gate passes:

- Nominal V13 net and PF are not below frozen V12/V6, and closed/equity
  drawdown are not above them.
- Nominal 3/6/12-month net and PF are not below frozen V12/V6.
- At least 99% of V60 trades and frequency remain.
- Every V60 comparative gate, every annual gate, both veto-component gates, and
  the frozen cross-feed gates remain passing.
- At `+$0.10` and `+$0.20` per trade, every V60 comparative gate passes; V13 net
  and PF are not below V12 and closed/equity drawdown are not above V12.
- August net stays positive and is not below V6's `$17.50`; PF is not below
  V6's `1.1621`; closed drawdown is not above V6's `$56.69`.
- August uses the same V12 retained entry set; management cannot manufacture
  frequency or add trades.
- The historical policy arms and closes at least one position, and no replay
  deadlock or open position remains.
- Clean causal forward evidence remains mandatory before deployment.

Failure rejects V13 without tuning. V60 remains deployed, V6 stays read-only,
and V12 remains rejected.

## Authorization

Historical and exposed-August research only. Runtime changes, MT5 order actions,
demo deployment, live deployment, ML execution, and broker actions are
prohibited.
