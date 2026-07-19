# V27 Capital Forward Family Portfolio Preregistration

## Purpose

V24.1 and V26 share one untouched Capital forward stream but use mechanically
disjoint event clocks. V27 freezes how they may be selected and combined before
either component has a validation trade or economic audit.

V27 is a portfolio hypothesis, not a third signal generator. The claim under
test is that the fixed union can add enough independently profitable activity to
the unchanged five-specialist Core without exceeding the account risk budget.

## Frozen Inputs

- Core ledger: exactly 1,249 rows, SHA-256
  `fec25e1127b8bea261109010c7b0ad3eca275adf14e0ec52395e7efdfa86d372`.
- Core reference window: realized exits from 2025-07-01 through 2026-06-30.
- Core reference: 160 trades over 261 weekdays, or 0.6130268199233716/day;
  USD 4,508.783898966717 net, PF 3.491826050898352, and USD 889.69
  closed-trade drawdown.
- V24.1 contract SHA-256:
  `84a1d60b025be15f9cedf3c0fc6688ac30c9c06075ab415efc155996df4858c0`.
- V26 contract SHA-256:
  `4981f20bff17e36fc990816e433b9cb69b708a7f39dd1cc85b3a1f96db68f1ee`.

## Multiplicity And Component Admission

The registered Capital forward family now contains three claims: V24.1, V26,
and their V27 fixed portfolio. The family alpha is 0.05, so every claim must pass
a one-sided p-value threshold of 0.05 / 3, or 0.016666666666666666.

The test is a centered-null circular moving-block bootstrap of chronological
daily base P&L with five-weekday blocks and 10,000 samples. Seeds are fixed at
2701 for V24.1, 2702 for V26, and 2703 for V27.

Both components must pass:

1. Their own immutable stage gate.
2. The V27 external block-bootstrap threshold.
3. Exact audit, contract, date, and trade-file verification.

If either component fails, V27 fails terminally before portfolio economics are
calculated. V27 cannot select only the winning component.

## Fixed Router

1. Use only executable component trades from the same sealed stage dates.
2. Tag source as `V24_1` or `V26`.
3. Sort by candidate millisecond, then fixed priority `V24_1`, `V26`.
4. Permit at most one satellite position. Reject a candidate arriving before
   the prior selected satellite exit.
5. Keep at most the first three selected satellite trades per UTC day.
6. Do not use score, direction, P&L, session, regime, or later price to choose
   between candidates.

## Frozen Gates

- Satellite frequency: 2.386973180076628 through 3.386973180076628 trades per
  complete weekday.
- Projected Core-plus-satellite frequency: 3.0 through 4.0/day.
- At least 20% long, 20% short, 20% V24.1, and 20% V26 selected trades.
- Positive base and stress net.
- Base PF at least 1.20; stress PF at least 1.05.
- At least 50% profitable days.
- Satellite closed-trade drawdown no more than USD 100 and recovery at least 1.
- Base PF at least 1.0 in both chronological halves.
- V27 block-bootstrap p-value no more than 0.016666666666666666.
- Core-plus-satellite base net greater than the frozen Core reference net.
- Core-plus-satellite PF at least 2.0.
- Appended closed-trade drawdown no more than USD 1,000.
- No more than 20% of raw family trades rejected because another satellite
  position was open.

Validation uses the first 20 complete component weekdays. Failure is terminal.
Confirmation uses the next 20 and may open only on a later invocation after an
immutable passing V27 validation exists.

## Interpretation

The projected total frequency uses the frozen one-year Core average because the
historical Core ledger ends before the prospective satellite period. Even dual
V27 passage remains research-shadow evidence. Same-period Core shadow signals,
floating-equity overlap, margin, and exact MT5 portfolio reproduction remain
mandatory before any execution decision.
