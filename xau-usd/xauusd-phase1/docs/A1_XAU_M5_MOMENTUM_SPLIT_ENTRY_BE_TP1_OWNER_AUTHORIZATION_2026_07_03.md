# A1 XAU M5 Momentum Split-Entry BE-on-TP1 Owner Authorization

Date: 2026-07-03
Owner: Muhammad Ali Khan
Status: APPROVED_FOR_A1_SMALL_DEMO_ATTACH

## Authorization Source

The owner approved the split-entry approach in the project thread:

```text
I am fine with this approach. You already have the owner approval now.
Nothing wrong in it.
```

This approval is recorded as acceptance of the split-entry structure and its higher minimum exposure. It does not by itself mean the lane has been attached to MT5 or that any live/real-money trading is approved.

## Locked Spec Reference

Frozen spec:

```text
xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_SPLIT_ENTRY_BE_TP1_FORWARD_V0_2026_07_03.md
```

Spec SHA256:

```text
69cafce956f2e4cb8b0326d98513b757b03f9e5f332f86a673b6248ce76a68a3
```

EA source:

```text
xau-usd/xauusd-phase1/mt5/Experts/A1XauM5MomentumContinuationExecutor.mq5
```

EA source SHA256 at approval:

```text
a4d75f617ef4864fd6e28fa210ec02ce4b0b6e87171382534f51dbbecdc016c4
```

The original approval hash above is the pre-review package hash. The spec and EA source are intentionally rehashed after Claude's two blocker fixes; the updated hashes are recorded in the current `.sha256.json` manifests.

Post-review note:

```text
Claude review dated 2026-07-03 required a quantified exposure acceptance before attach.
The spec was revised after this authorization to add runtime signal-claim enforcement and practical exposure numbers.
The owner accepted the quantified exposure in the project thread on 2026-07-03, so the governance acceptance blocker is closed.
```

## Approved Exposure

The owner approves the following demo-only exposure:

```text
One signal may open two same-direction minimum-lot tickets.
Ticket 1: _TP1, target 0.70R.
Ticket 2: _RUN, target 2.00R.
Runner SL moves to breakeven when TP1 closes at TP.
Both tickets may lose if the signal fails before TP1.
```

Approved lot/exposure behavior:

```text
2 x 0.01 minimum-lot tickets per signal when broker minimum lot prevents a true partial close.
```

Quantified exposure requiring explicit owner acceptance before attach:

```text
Worst case per failed signal: approximately -36 USD at the 1800-point stop ceiling with two 0.01 tickets.
Typical losing signal: approximately -20 to -30 USD.
Recent 3-month average losing signal: -28.37 USD.
Approximately one-third of signals may lose both tickets before TP1 is reached.
InpMaxRiskLots remains 0.05 because this is the tested input, but the broker-minimum 2 x 0.01 pair dominates typical large-stop XAU losses.
```

Quantified exposure acceptance:

```text
ACCEPTED_BY_OWNER_2026_07_03
Owner message: I accept the quantified split-entry exposure and approve demo attach on A1
```

## Boundaries

Approved:

```text
Small demo preparation for the split-entry BE-on-TP1 lane.
Owner acceptance of 2-ticket minimum exposure.
Proceeding to pre-attach checks and review package preparation.
```

Not approved by this document:

```text
Live trading.
Real capital.
Canonical Phase 2 pass.
Changing the frozen strategy rules.
May-only optimization.
Post-hoc hour/threshold tuning.
Removing safety gates.
Attaching without final pre-attach checks.
```

## Proposed Forward Identifiers

```text
Magic: 932280
Order comment prefix: A1_XAU_M5_MOM_SPLIT_BE
Kill switch: a1_xau_m5_momentum_split_be_tp1_kill_switch.txt
Symbol: XAUUSD
Timeframe: M5
Account: A1 demo unless separately approved otherwise
```

## Remaining Pre-Attach Checklist

Before any MT5 attach or broker-action deployment:

```text
[ ] Confirm magic 932280 is unused in runtime and history.
[ ] Confirm comment prefix A1_XAU_M5_MOM_SPLIT_BE is unique.
[ ] Confirm kill-switch filename is unique and reachable.
[x] Confirm owner accepts quantified exposure: worst case approximately -36 USD per failed signal, typical loss -20 to -30 USD, approximately one-third both-ticket losses.
[ ] Confirm runtime signal-claim smoke report is PASS and attach packet renders three priorities.
[ ] Confirm package guard/account currency is USD for this lane.
[ ] Confirm demo account/server only.
[ ] Confirm no existing lane is modified or removed by the attach.
[ ] Compile EA cleanly.
[ ] Generate owner-authorized preset or attach packet.
[ ] Record first fill timestamp after attach.
[ ] Continue long-window evidence debt: rerun V6/V13 with reduced management logging.
```

## Approval

Owner decision:

```text
APPROVE
```

Approval meaning:

```text
The owner accepts the split-entry structure and authorizes moving to the next preparation step for a small demo lane, within the frozen spec boundaries above.
```
