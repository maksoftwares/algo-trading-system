# Second Candidate Research Plan

Last updated: 2026-05-22

## Purpose

Phase 0 approved only one future expert: `breakout_retest`. That is a correct outcome of strict gates, but it creates concentration risk. This research track starts a second candidate without weakening the original gate discipline.

## Candidate Selection

Primary candidate for the next research pass:

```text
squeeze_breakout_long_v0
```

Reason for selection:

- It is close to the reviewer-recommended `squeeze breakout long` family.
- It targets a different behavior from `breakout_retest`: compression release rather than level break and retest.
- It can be defined mechanically with volatility compression, range contraction, expansion candle, and follow-through rules.
- It should be falsifiable without adding discretionary filters.

Alternates, if the primary definition cannot be made mechanical enough:

| Candidate | Why it remains on deck |
| --- | --- |
| `post_spike_short_v0` | Tests exhaustion after a fast XAUUSD displacement. |
| `emr_inactivity_long_v0` | Tests inactivity-to-reversion behavior with strict activity gates. |
| `ny_failed_london_reversal_v0` | Tests session failure mechanics, but requires careful router separation. |

## Required Pre-Registration Before Testing

No matrix, decile, multisymbol, or adversarial run may begin until the candidate has:

1. A completed hypothesis document with no placeholders.
2. Mechanical entry, stop, target, and invalidation rules.
3. Expected trade count, expected PF range, expected losing-month rate, expected worst month, expected zero-trade months, and expected R distribution.
4. Falsification criteria.
5. Code mapping after implementation.
6. SHA256 registration in the hypothesis manifest.

## Draft Mechanical Definition

This candidate now has a locked v0 hypothesis. The table below is retained as the design summary, while the controlling definition is `docs/hypothesis_squeeze_breakout_long_v0.md`.

| Component | Draft rule |
| --- | --- |
| Market | XAUUSD M5 entries with M15/H1 context. |
| Compression | M15 rolling range width is below its recent percentile threshold, and M5 ATR is below its recent percentile threshold. |
| Direction | Long only for v0. |
| Trigger | M5 close breaks above the compression range high by a fixed ATR fraction. |
| Confirmation | The breakout candle closes in the upper portion of its range and does not immediately close back inside compression. |
| Entry | Next eligible M5 open after confirmation, subject to spread and session filters already used in Phase 0. |
| Stop | Below compression range low or an ATR-based protective distance, whichever is farther. |
| Target | Fixed R target matching the Phase 0 framework unless the hypothesis explicitly justifies a different value before registration. |
| Invalidation | No trade if compression is too old, breakout is too extended, spread is above threshold, or the move occurs inside a blocked session window. |

## Validation Path

The second candidate must pass the same reduced-portfolio discipline:

| Gate | Requirement |
| --- | --- |
| Hypothesis completeness | PASS before any run. |
| SHA256 lock | PASS before any run. |
| 9-cell matrix | Same PF, sample-size, drawdown, concentration, activity, and cost-sensitivity thresholds. |
| Decile persistence | Same decile rules. |
| Multisymbol check | Same EURUSD/USDJPY directionality check or a written XAU-specific defense. |
| Adversarial review | Manual review with logic-gap failure rate at or below threshold. |
| Intrabar ambiguity | Report required before any approval. |
| Final verdict | PASS, FAIL, or INVALID_PRE_REGISTRATION. No soft approval. |

## Current Status

| Field | Value |
| --- | --- |
| Candidate | `opening_drive_failed_continuation_v0` |
| Status | REJECTED_FIRST_PASS |
| Testing allowed | NO_FURTHER_V0_TESTING |
| Hypothesis document | `docs/hypothesis_opening_drive_failed_continuation_v0.md` |
| Hash manifest | `outputs/hashes/research_hypothesis_hash_manifest.csv` |
| Implementation draft | `src/phase0/strategies/opening_drive_failed_continuation_v0.py` |
| Research smoke | `outputs/reports/opening_drive_failed_continuation_v0_research_smoke.md` |
| First-pass matrix | `docs/OPENING_DRIVE_FAILED_CONTINUATION_V0_FIRST_PASS.md` |
| Next action | Move to the next backlog candidate, `liquidity_sweep_reversal_v0`, starting with a fresh hypothesis lock. |

## Promotion Prep Command

Before the candidate can be promoted into result-producing Phase 0 runs, run:

```powershell
.\.venv\Scripts\phase0.exe run-research-candidate-smoke --expert squeeze_breakout_long_v0 --hypothesis-file docs/hypothesis_squeeze_breakout_long_v0.md
```

This verifies:

- The hypothesis is complete and matches the research hash manifest.
- The strategy exists only in the research registry, not the active `all` registry.
- A synthetic signal and trade plan can be produced.
- Phase 0 result-producing runs remain blocked until explicit promotion.

## Explicit Research Matrix Command

After the smoke check passes, the candidate may be evaluated with:

```powershell
.\.venv\Scripts\phase0.exe run-research-matrix --expert squeeze_breakout_long_v0 --hypothesis-file docs/hypothesis_squeeze_breakout_long_v0.md
```

This command keeps the boundary explicit:

- `squeeze_breakout_long_v0` is not included in `phase0 run-matrix --expert all`.
- `squeeze_breakout_long_v0` is not an approved EA.
- Matrix output is candidate evidence only until all Phase 0 gates pass.

Rejected experts remain rejected. `trend_pullback` and `range_mr` should not be retuned under their original names. Any future revisit must use a new versioned hypothesis.
