# Claude XAUUSD ML and V8 Audit V1

Seven research lanes run 2026-07-26 to 2026-07-27, restated here in the
`v6-causal-ml-*` package format so they sit alongside those lanes and can be
compared directly. The work itself lives on branch `codex/regime-teacher-eas-v1`
in the `regime-teacher-eas-v1` package; this directory is a faithful restatement,
not a re-run.

Historical research only. No lane authorizes Python, EA, demo, live, or broker
execution.

## Frozen Outcome

**CLAUDE_XAU_ML_AND_V8_AUDIT_V1_SIX_LANES_FAIL_QUARANTINED_ONE_PARTIAL_PASS**

| Lane | Hypothesis | Decision |
|---|---|---|
| A | per-regime specialist family | FAIL — quarantined |
| B | multi-instrument transfer | FAIL — terminal |
| C | GOLD V8 horizon-diversified family | FAIL — rejected by review |
| D | ML early exit before the stop | FAIL — quarantined |
| E | ML entry filter on the V6 book | FAIL — quarantined |
| F | cross-asset position sizing | FAIL — quarantined |
| G | microstructure-generated entries | FAIL — quarantined |
| C' | V6 entry-time slot locking | **partial pass** |

Headline corrections after independent adversarial review of lane C:

- causal walk-forward PF **2.03 -> 1.202**, 95% CI [0.96, 1.46] — contains 1.0
- full-history PF 1.79 -> **1.242**; maxDD $1,167 -> **$1,980**
- removing the top 1% of trades (56 of 5,572) leaves **PF 1.000 and -$4**

## Two independent corroborations of the `v6-causal-ml-*` lanes

Reached separately, by different methods, before either result was read:

- **Early exit does not work.** This package: adverse trades sit at -0.313R and
  finish at -0.270R, so holding wins by +0.043R; best of 90 searched subsets was
  noise. `v6-causal-ml-early-exit-v3`: net dollars saved **-$299.44** on 399k
  training rows.
- **The ML entry filter is redundant.** This package: PF rises and P&L falls at
  every cutoff — removal, not selection. `v6-causal-ml-veto-v1`: PF 1.177 ->
  1.221 while net fell $303.59 -> $293.99.

Two agents, two toolchains, same two conclusions. That is stronger evidence than
either lane alone.

## Two defects found in the deployed V6 line

Independent of every hypothesis above, and live today:

1. **Double-booking** — 79.4% of V6 signals open two positions at the same
   instant, same direction, same stop. Peak combined risk on one signal
   **$236.58**. Deduplicating costs ~20% of profit and cuts drawdown 34%
   ($270 -> $201). This is a decision to make, not obviously a bug to fix.
2. **Starved threshold** — the ranker cut is a frozen 2016-21 score value rather
   than a percentile, so realised selectivity has drifted to **0.43-0.62x** the
   spec. A spec asking for the top 20% delivers ~13%.

Both need an owner decision; neither is actioned here.

## Durable measurements worth reusing

- **Selection-leak ladder on this data:** PF 1.99 -> 1.45 -> 0.82 as hindsight is
  progressively removed from the *choosing*. About 0.3-0.6 PF per layer.
- **Tick microstructure carries most of the edge:** gold PF **1.89 -> 1.10**
  without `tick_signed_move`, `tick_book_imbalance_mean`, `price_efficiency_5m`.
  Ranking signal, not entry signal — lane G tested the latter and it failed.
- **Selection instability predicts failure** before any P&L is read.

## Layout

```
PREREGISTRATION.md   questions, frozen decisions, gates (see its status note)
outputs/RESULT.md    per-lane findings, defects, corrected figures
outputs/REVIEW_BRIEF_GOLD_V8.md          the adversarial brief that rejected lane C
outputs/GOLD_V8_SPEC.json                lane C spec, status REJECTED
outputs/PREREGISTRATION_MULTI_INSTRUMENT.md   lane B, genuinely pre-committed
outputs/REGIME_SPECIALIST_FAMILY_V7.md   lane A narrative
outputs/HANDOFF_TO_OTHER_AGENT.md        corpus guide for a fresh agent
src/                 the scripts behind each lane
```

## Honest limitation of this package

The `PREREGISTRATION.md` here was **written after the experiments ran**. The gates
recorded were applied during the work, but they were not committed to a file
first, and one is marked `[POST-HOC]`. Its pass/fail tokens are therefore weaker
evidence than those in `v6-causal-ml-veto-v1` or `v6-causal-ml-early-exit-v3`,
which were preregistered before execution. Lane B is the exception — its
preregistration and amendments were written before each attempt.

Known defects still live in `src/`: `gold_v8_walkforward.py` and the assembler it
calls size positions in exit order (look-ahead); `v8_lot_constrained.py` computes
PF on a different series from its dollars. `v6_fix.py` shows the correct
entry-order pattern with heap-settled exits.
