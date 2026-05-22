# NY London Overlap Compression Break v0 First-Pass Result

Date: 2026-05-22

## Verdict

`ny_london_overlap_compression_break_v0` is `REJECTED_FIRST_PASS`.

The locked v0 hypothesis did not satisfy the first Phase 0 research gate. It produced too few trades in 6 of 9 cells and only 3 of 9 matrix cells reached PF >= 1.30. The apparent PF strength in the Dukascopy cells is not usable because those cells each contain only 2 trades.

## Gate Result

| Gate | Required | Observed | Status |
| --- | --- | --- | --- |
| Matrix PF coverage | PF >= 1.30 in at least 7 of 9 cells | 3 of 9 cells | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 2 to 41 trades | FAIL |
| Retune allowed under same name | No | No | PASS |

## Matrix Summary

| Cell | Broker | Cost Model | Trades | Profit Factor | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 2 | 0.000 | -0.955 | 0.955 | 0.00% |
| 2 | capital_com | median | 2 | 0.000 | -0.955 | 0.955 | 0.00% |
| 3 | capital_com | p95 | 2 | 0.000 | -0.968 | 0.968 | 0.00% |
| 4 | pepperstone | best_case | 41 | 0.925 | -0.883 | 5.023 | 39.02% |
| 5 | pepperstone | median | 41 | 0.925 | -0.883 | 5.023 | 39.02% |
| 6 | pepperstone | p95 | 41 | 0.907 | -1.087 | 5.062 | 39.02% |
| 7 | dukascopy | best_case | 2 | 1.470 | 0.226 | 0.480 | 50.00% |
| 8 | dukascopy | median | 2 | 1.440 | 0.215 | 0.487 | 50.00% |
| 9 | dukascopy | p95 | 2 | 1.473 | 0.223 | 0.471 | 50.00% |

## Decision

Do not proceed to decile, multisymbol, adversarial, intrabar, or Phase 1 planning for this v0 candidate.

Do not tune `ny_london_overlap_compression_break_v0` in place. Any future overlap-compression idea must use a new versioned hypothesis with a fresh mechanical definition and hash registration before result-producing runs.
