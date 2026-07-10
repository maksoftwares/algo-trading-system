# A1 XAUUSD Current Research Freeze

Date: `2026-07-10`

Scope: A1 XAUUSD research, exact-MT5 testing, offline analysis, and shadow evidence

Authority: [A1_XAU_PROFITABLE_SYSTEM_MASTER_DIRECTION_2026_07_10.md](A1_XAU_PROFITABLE_SYSTEM_MASTER_DIRECTION_2026_07_10.md)

## Frozen program state

| Item | Frozen state |
| --- | --- |
| Current control | `current_r1_r2_baseline` |
| Control standing | Research control only; not a qualified, demo-authorized, or live-authorized portfolio |
| R1 role | Primary bullish/uptrend profit engine |
| R2 role | Strict downtrend hedge and secondary profit source |
| R3 standing | `STANDALONE_SHADOW_ONLY`; portfolio use killed |
| R4 standing | No survivor; chop default is `NO_TRADE` |
| Historical data through | `2026-06-30` |
| Historical-data standing | `DEVELOPMENT DATA`; not an untouched holdout |
| Deployment standing | `NO_GO` for demo or live broker action |
| Next task | `A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_V1` |
| Runtime action from this freeze | None; runtime, terminal attachments, account state, and EA trading logic remain untouched |

## North star

> Build an automated XAUUSD system that produces positive net returns over rolling 6- and 12-month periods, survives realistic costs and regime changes, limits portfolio equity drawdown, and can eventually support controlled withdrawals from accumulated profits.

This is the exact program north star. It does not mean every month must be profitable,
that activity must be forced, or that historical output may be repaired until a target
score appears.

## Frozen R1+R2 research control

The only defensible current portfolio baseline is:

```text
current_r1_r2_baseline
```

Its frozen evidence is:

| Metric | Value |
| --- | ---: |
| Trades | `678` |
| Win rate | `51.03%` |
| Realized W/L | `2.6082` |
| Profit factor | `2.7182` |
| Net | `+$9,640.05` |
| Stress net at `-$0.30/ticket` | `+$9,436.65` |
| Recent-three-month net | `+$764.92` |
| Maximum closed drawdown | `$889.69` |
| Positive months | `26` |
| Active weekdays | approximately `21.28%` |

Frozen ledger:
`outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709_current_r1_best_r2_pullback_plus_r2_impulse_body45_atr45_daily_loss10_KEPT.csv`

SHA256: `47cbe6a562ba2874d93a97255affbde613566ed06340a149ed2795d69a5dae52`

These metrics freeze a comparison and audit control. They do not establish untouched
forward evidence, standalone admission under the newer specialist contract, or
permission to deploy. Exact MT5 can validate execution fidelity on known history; it
cannot remove selection bias or turn development history into a holdout.

### Legacy rule-admissibility warning

The frozen control preserves four historical source identities exactly. Three embed
selection rules the master direction forbids for future admission; the fourth embeds
a source-local containment rule that cannot be reused as standalone alpha evidence:

| Frozen source | Legacy rule retained only to preserve the audit control |
| --- | --- |
| `h4_d1_long_best_box2_atr80` | Previous-month P/L health gate: `InpH4D1PrevMonthHealthGateEnabled=true`, minimum net `-$50` |
| `r1_h1_pullback_long_v1` | Directional server-session gate: `09 <= hour < 15` |
| `r2_pullback_rejection_short_v1` | Directional server-session gate: `05 <= hour < 19` |
| `r2_continuation_short_v1` | Legacy source-local daily-loss stop: `$10`; not reusable as standalone alpha/admission evidence |

Those selection/containment rules are not endorsed by this freeze. They remain only
because changing or removing one would change the 678-trade audit universe. After
the router audit, each prospective source must pass both standalone quality gates and
rule admissibility. Any future daily/weekly/monthly containment must be the shared,
preregistered integrated risk policy, not a source-local historical rescue.
Unless a rule-clean, independently qualified source already exists or a later
reviewed governance packet explicitly authorizes a fixed rule-clean replacement, the
integrated portfolio path is `NO_GO`. The router audit itself cannot remove, repair,
or retest any of these rules.

### Native-position attribution warning

The frozen ledger's aggregate counts, win/loss multiset, chronological exit P/L, and
source/portfolio totals remain authoritative, but its upstream legacy trade parser
FIFO-paired exits by direction instead of native MT5 `position_id`. Pre-audit
reconciliation found `388/678` rows with a non-native exit deal and `387/678` with a
non-native individual P/L assignment. Native truth is recoverable from the exact deal
logs because the same 678 unique entries map one-to-one to 678 position IDs with one
entry and one exit each.

No per-trade holding-path conclusion may use the FIFO pair. The router audit must
first publish an outcome-blind entry-deal-to-position reconciliation, retain the
legacy fields as provenance, and reproduce every source/aggregate total. Any failed
join makes the audit evidence invalid. This is an evidence-attribution repair only;
it does not authorize a strategy change or alter the frozen audit entry universe.

## Frozen specialist roles and boundaries

### R1 — uptrend profit engine

R1 owns bullish/uptrend opportunity. Its mandate is to trade only when the broad gold
uptrend is valid, remain inactive outside its owned regime, and provide most of the
long-side expectancy. It is not required to create daily activity. This is a frozen
role assignment, not a claim that every historical R1 source has passed the current
standalone admission gate.

### R2 — strict downtrend hedge

R2 owns genuine downtrend/downside participation. Its mandate is to protect and add
return in valid downside regimes, avoid shorting chop or exhausted breakdowns, and
remain small or inactive when no strict R2 state exists. It need not mirror R1's
frequency. This is also a role assignment, not a promotion claim.

### R3 — standalone shadow only; portfolio use killed

R3 remains frozen as `STANDALONE_SHADOW_ONLY`. That label permits diagnostic shadow
observation only; it does not mean qualified standalone alpha and does not authorize
portfolio inclusion.

The controlling overlap evidence is:

```text
139 total R3 trades
110 same-opportunity overlaps with the existing R1 box
29 non-overlap trades
```

R3-first source priority improved profit but exceeded the hard drawdown cap. Portfolio
use is therefore killed. Do not run another source-priority test, add a drawdown
governor to rescue it, tune it, or describe it as diversification.

### R4 — no survivor

No R4/chop specialist is approved. The unsuccessful frozen forms are M5
sweep/reclaim, daily-extreme reclaim, prior-day reclaim, and opening-range reversal.
The default action in chop remains `NO_TRADE`. No activity filler inherits the R4
slot.

## Specialist-campaign reconciliation

The completed specialist campaign working record is development-only,
nonpromotion evidence. Its governing checkpoint is:

```text
NO_QUALIFIED_STANDALONE_SPECIALIST_NO_PORTFOLIO_TEST_AUTHORIZED
```

The campaign's clean exact-MT5 cells use already inspected development windows and
therefore may reject weak hypotheses, expose implementation or incidence defects, and
inform future preregistration. They cannot confirm a system on unseen evidence. The
completed evidence rejected the incumbent R1 box as a newly qualified specialist,
the tested R1 replacements, the tested R2 continuations/retests, and the tested R3
compression/chop families under the campaign's stricter standalone and drawdown
contract. No failed candidate may be rescued by a portfolio result, mask, post-result
sibling, or risk governor.

The five previously frozen mode-27 prehistory overlap-control ledgers had already
been reconstructed before this master direction was received. That reconstruction
did not implement or execute the mode-27 candidate. Its outputs are quarantined as
development-only diagnostics and are excluded from candidate promotion, the router
audit decision, and forward evidence. No further mode-27 work is authorized.

There is no contradiction between retaining `current_r1_r2_baseline` and recording
those rejections: the former is a frozen research control for path audit and
comparison; it is not an admitted production portfolio. The campaign does not promote
a replacement, does not reopen R3 or R4, and does not authorize an integrated
portfolio test until the applicable standalone gates are satisfied.

## Historical evidence boundary

Every project-inspected observation through `2026-06-30`, including the campaign's
`2016-01` through `2021-12` and `2022-07` through `2026-06` exact-MT5 windows, is
`DEVELOPMENT DATA`.

Consequences:

- No result on those windows alone can authorize demo or live action.
- No subset of those windows may be relabeled an untouched holdout.
- Offline recomposition is diagnostic only and cannot promote a portfolio.
- Historical exact-MT5 evidence may diagnose and qualify a frozen idea, but final
  confirmation requires locked, genuinely new forward-shadow evidence.
- A weak or absent regime during a future exam must produce `CONTINUE_EVIDENCE`, not
  fabricated coverage.

## Immediate next task

Proceed next with `A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_V1` on every trade in the
frozen R1+R2 control. EA-side Router V1 is authoritative for this audit. The audit must
distinguish wrong-router entry, stale tactical entry, later regime change while open,
data/timestamp error, and valid loss without using final P/L to assign the class.

No trading rule may change before the path audit closes. In particular, do not start
a new specialist, tune R1/R2/R3/R4, add a filter, or modify entry and exit together.
Any nonzero wrong-router count is a routing/configuration defect stop, not permission
for strategy tuning.

## Authorization and runtime boundary

This freeze authorizes repository-only governance, reproducible exact-MT5 Strategy
Tester work, offline analysis, and shadow evidence. It authorizes no broker action.

```text
No demo attach.
No live attach.
No order placement outside Strategy Tester.
No terminal runtime-state change.
No account or risk-setting change.
No EA trading-logic change from this documentation action.
```

Demo and live remain separate future programs requiring an integrated exact-MT5 pass,
locked forward evidence, tested containment, exact hash approval, independent review,
and explicit owner authorization. Until such a packet exists, research stays offline
and runtime stays untouched.

## Frozen conclusion

The project currently has one historically profitable R1+R2 research control, no
newly qualified standalone specialist under the completed campaign evidence, R3
restricted to standalone shadow diagnostics with portfolio use killed, and no R4
survivor. The truthful next action is the router entry/hold-path audit—not historical
repair, forced activity, or deployment.
