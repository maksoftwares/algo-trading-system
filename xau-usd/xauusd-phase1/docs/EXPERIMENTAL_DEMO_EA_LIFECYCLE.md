# Experimental Demo EA Lifecycle

Status: ACTIVE_REPAIR_GOVERNANCE

This document governs experimental demo EA lifecycle states only. It does not authorize canonical Phase 2, live trading, real capital, cost-suspension removal, or same-family diversification claims.

## Current Lifecycle Table

| Candidate / Scope | Status | Reason | Runtime instruction |
|---|---|---|---|
| `breakout_retest` | `DEMO_ALLOWED_CONTROLLED` | Strongest current duplicate-hidden candidate; positive PF/PnL in actual demo evidence. | Continue controlled experimental demo supervision only. |
| `P2WEAKNESS_BR_V1` | `OWNER_AUTHORIZED_DEMO_EXPERIMENT` | XAUUSD-only owner-authorized lane, magic `931000`, fixed `0.01` lot, strict guards. | Continue observation; no scaling. |
| `swing_breakout_retest_v0` | `OBSERVER_ONLY` | Tiny sample and same-family correlation; not independent diversification. | Do not promote without fresh approval. |
| `symbol_normalized_round_retest_v0` | `SUSPENDED_DEMO_NO_NEW_ENTRIES` | Major duplicate-hidden PnL drag and weak XAUUSD morning cluster. | Disable new broker-side entries after baseline/backup/reconciliation. |
| `session_extreme_retest_v0` | `SUSPENDED_DEMO_NO_NEW_ENTRIES` | Weak PF/win rate; XAUUSD night cluster is especially poor. | Disable new broker-side entries after baseline/backup/reconciliation. |
| `round_number_retest_v0` | `OBSERVER_ONLY` | Provisional, same-family, and duplicate-only evidence under current priority. | Rebuild observer evidence before any execution promotion. |
| `WR50_BreakoutEvening_v0` | `OBSERVER_ONLY` | Too small a sample to judge; current evidence is not enough for risk. | Observe only. |
| `USDJPY all variants` | `DISABLED_NO_NEW_ENTRIES` | Weak symbol result in duplicate-hidden actual demo table. | Keep disabled for new entries. |
| `GBPUSD replacements` | `EXPERIMENTAL_OBSERVE_0_01` | Replacement for USDJPY, but must earn its own evidence. | Keep at `0.01` until enough sample exists. |
| `EURUSD 0.05` | `OWNER_REVIEW_REQUIRED` | Exposure increase can distort account-level results and needs explicit risk acceptance. | Prefer `0.01-0.02` unless owner accepts risk in writing. |

## Promotion Rule

A repair rule can move from shadow-only to demo enforcement only if all conditions are true:

- duplicate-hidden PF and PnL improve,
- win rate improves or is preserved,
- retained trade count remains useful,
- one fresh forward week confirms the result,
- owner/reviewer approval is recorded,
- canonical Phase 2 status remains unchanged unless the official gates pass separately.

## Non-Negotiable Boundaries

- Do not tune parameters in place.
- Do not increase lots to compensate for weak EAs.
- Do not close open positions automatically unless an explicit risk breach occurs.
- Do not modify running charts without profile backup and post-change reconciliation.
- Do not call experimental demo evidence canonical Phase 2 evidence.
