# A3 ML Contract Expansion Packet

Overall status: CONTRACT_EXPANSION_REVIEW_REQUIRED
Dataset version: xauusd_c02_multiacct_202606220547_geffebb6d_c9221d066

## Current Lock

- Symbol: XAUUSD.
- Family scope: breakout_retest only.
- Contract expansion authorized: false.
- Python demo predictions authorized: false.
- Broker action authorized: false.

## Evidence Summary

- C03 readiness: NO_GO.
- Active weeks: 3.37 / >=8.
- Market setup groups: 223 / >=300.
- Current-scope uncataloged files: 0.
- Out-of-scope would-signal rows: 2747.
- Out-of-scope estimated groups: 1381.
- All demo accounts collecting: true.

## Candidate Families

| Family | Rows | Groups | Files | Min | Max |
| --- | --- | --- | --- | --- | --- |
| rdguard | 78 | 78 | 1 | 2026-06-14T22:39:59Z | 2026-06-16T11:14:56Z |
| rdstruct | 78 | 78 | 1 | 2026-06-14T22:39:59Z | 2026-06-16T11:14:56Z |
| round_number_retest | 2455 | 1127 | 7 | 2026-05-29T09:34:56Z | 2026-06-19T16:10:00Z |
| session_extreme_retest | 136 | 98 | 4 | 2026-05-29T13:05:00Z | 2026-06-19T16:14:59Z |

## Reviewer Questions

1. Should A3 ML Data Contract V1 be versioned to allow multi-family XAUUSD rows beyond breakout_retest?
2. If yes, which families are approved: round_number_retest, session_extreme_retest, rdguard, rdstruct, or a smaller subset?
3. Should family be a model feature in one global model, or should each approved family receive its own model/gates?
4. Should market_setup_group_id include family to avoid cross-family dedupe?
5. Can the existing 288-bar diagnostic label horizon be reused for every approved family, or does any family need a new label contract?
6. What minimum per-family rows/groups/minority labels must pass before any Python demo prediction authorization?
7. Should C03 slippage readiness stay per account, or become per account plus per family?

## Required Changes If Approved

- Create a versioned A3 ML data contract addendum that explicitly changes family scope.
- Add allowed_families configuration and tests; keep default locked to breakout_retest until approval is present.
- Update C02 normalization to preserve family and include only approved families.
- Update signal grouping so setup groups cannot merge different families unless the reviewer explicitly approves it.
- Update C03 readiness gates for global and per-family row/group/minority/regime/slippage checks.
- Update C05/C04/C06/C23 so model artifacts, shadow predictions, and EA handoff include model scope/family hashes.
- Regenerate C08, C03, C05, C04, C06, C23, C33 and keep broker_action_authorized=false.

## Reviewer Prompt

```markdown
You are reviewing an A3 Python ML contract-expansion proposal for an MT5 demo trading system.

Current locked contract:
- XAUUSD only
- accounts 1025742, 1033030, 1033669
- breakout_retest only
- broker_action_authorized must remain false

Current readiness:
- C03 status: NO_GO
- active weeks: 3.37 / >=8
- market setup groups: 223 / >=300
- feature budget: 0 / >=6
- slippage readiness: INSUFFICIENT / ADEQUATE
- all three demo accounts collecting: True

Backfill audit:
- uncataloged current-scope files: 0
- current-scope would-signal rows: 574
- out-of-scope would-signal rows: 2747
- out-of-scope estimated groups: 1381

Out-of-scope families found:
- rdguard: 78 rows, 78 estimated groups, 2026-06-14T22:39:59Z to 2026-06-16T11:14:56Z
- rdstruct: 78 rows, 78 estimated groups, 2026-06-14T22:39:59Z to 2026-06-16T11:14:56Z
- round_number_retest: 2455 rows, 1127 estimated groups, 2026-05-29T09:34:56Z to 2026-06-19T16:10:00Z
- session_extreme_retest: 136 rows, 98 estimated groups, 2026-05-29T13:05:00Z to 2026-06-19T16:14:59Z

Please decide whether to approve a versioned contract expansion. If approved, specify:
1. allowed families
2. whether to use one global model with family as a feature or separate per-family models
3. family-aware C03 gate thresholds
4. whether 288-bar diagnostic labels are valid for each family
5. slippage readiness requirements
6. exact conditions before Python demo predictions may be authorized

If not approved, say so clearly and require continued live collection under the current breakout_retest-only contract.
```

## Boundary

- MT5 connection attempted: false.
- Data export attempted: false.
- Terminal runtime change authorized: false.
- Model training authorized: false.
- Python demo predictions authorized: false.
- Broker action authorized: false.

## Next

Send this packet to the reviewer. Do not import out-of-scope rows or authorize Python demo predictions without an approved versioned contract expansion.
