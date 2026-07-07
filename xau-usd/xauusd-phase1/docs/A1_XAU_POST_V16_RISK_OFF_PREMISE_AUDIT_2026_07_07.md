# A1 XAU Post-V16 Risk-Off Premise Audit

Date: 2026-07-07

## Boundary

- No MT5 runtime attach and no demo/live change.
- Uses exact-MT5 reconstructed exit-time signal table:
  `outputs/reports/A1_XAU_HYBRID_WEEKLY_EXIT_ANATOMY_202207_202606_SIGNALS_EXIT_TIME.csv`.
- Purpose is premise screening only: decide whether a simple risk-off lever deserves exact MT5 implementation.

## Red-Week Anatomy

Baseline exit-time anatomy has `114/208` positive weeks (`54.81%`) and `94` red weeks.

| Slice | Count | Read |
|---|---:|---|
| Red weeks dominated by frequency frontier | `51` | mostly small/medium losses |
| Red weeks dominated by H4/D1 | `43` | most large-loss weeks |
| H4/D1 net negative inside red weeks | `44` | large-tail problem |
| Frequency net negative inside red weeks | `76` | broad small/medium leak |
| Small red weeks above `-20 USD` | `28` | mostly frequency-driven |
| Medium red weeks `-100..-20 USD` | `42` | mixed, frequency-heavy |
| Large red weeks below `-100 USD` | `24` | `22/24` H4/D1 dominated |

The remaining weekly gap is therefore two problems, not one:

1. Large weekly losses come mainly from the H4/D1 engine.
2. The many small/medium red weeks come mainly from the frequency book.

## Simple Block Diagnostic

Single-block and two-block diagnostic filters were tested on the reconstructed exact-ledger table. This is not a promotion search; it is a quick check for an obvious risk-off lever.

| Diagnostic | Signals | WR% | W/L | PF | Positive weeks% | Worst week | Read |
|---|---:|---:|---:|---:|---:|---:|---|
| Baseline | `3751` | `50.23` | `2.0002` | `2.0336` | `54.81` | `-878.18` | current frontier |
| Block H4/D1 bucket | `3417` | `49.49` | `1.4545` | `1.4366` | `57.69` | `-148.52` | smooths by deleting the profit engine |
| Block entry hour `08` | `3320` | `52.20` | `1.7890` | `1.9710` | `57.69` | `-750.24` | improves weeks but breaks payoff |
| Block opening-range reversal hour `08` | `3385` | `52.38` | `1.8808` | `2.0868` | `57.21` | `-905.76` | not enough weekly progress |
| Block H4/D1 + entry hour `08` | `3051` | `51.79` | `1.3591` | `1.4738` | `60.58` | `-138.61` | best weekly smoothing, but payoff collapses |
| Block entry hours `08+16` | `3223` | `52.03` | `1.6860` | `1.8455` | `59.13` | `-597.31` | still below target and payoff broken |

## Decision

No simple risk-off block deserves exact-MT5 implementation as a path to the owner target.

The only blocks that materially improve positive weeks do so by either:

- deleting the H4/D1 profit engine;
- cutting too much activity;
- reducing W/L far below `2.0`;
- or still staying around `57-60%` positive weeks.

## Next Premise Requirement

The next exact-MT5 source must be materially different from the current archive and should be rejected before coding unless it has a plausible reason to:

- win in frequency-driven small/medium red weeks without broadly adding noise;
- reduce or hedge H4/D1 large red weeks without deleting the H4/D1 edge;
- preserve W/L near `2.0`;
- keep activity near or above `90%`;
- and avoid post-hoc week/hour masks.

No reviewer token is justified by this diagnostic alone.
