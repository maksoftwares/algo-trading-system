# Liquidity Sweep Continuation v0 First-Pass Result

Status: REJECTED_FIRST_PASS
Generated: 2026-05-23

## Summary

`liquidity_sweep_continuation_v0` was registered, hash-locked, smoke-tested, and run through the real 9-cell research matrix. It is rejected at first pass and must not proceed to deciles, multisymbol validation, adversarial review, or EA coding.

## Matrix Result

| Metric | Result |
| --- | ---: |
| Matrix cells completed | 9 / 9 |
| PF passing cells >= 1.30 | 0 / 9 |
| Total trades across cells | 12,222 |
| Min cell trades | 1,281 |
| Max cell trades | 1,423 |
| PF range | 0.732 to 0.966 |
| Total return range | -63.73% to -15.01% |

## Verdict

The candidate had enough trades, so this was not a frequency-only failure. It failed the core expectancy gate: no cell reached PF 1.30 and every cost setting produced sub-1.0 PF. The independent liquidity-sweep continuation idea is therefore rejected under the current v0 definition.

## Artifacts

- Hypothesis: `docs/hypothesis_liquidity_sweep_continuation_v0.md`
- Smoke report: `outputs/reports/liquidity_sweep_continuation_v0_research_smoke.md`
- Matrix folder: `outputs/matrix_results/liquidity_sweep_continuation_v0/`
