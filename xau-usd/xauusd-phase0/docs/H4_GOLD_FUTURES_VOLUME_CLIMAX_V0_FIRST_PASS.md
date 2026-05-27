# H4 Gold Futures Volume Climax v0 First Pass

Status: REJECTED_FIRST_PASS

Generated at UTC: 2026-05-27

## Boundary

This was a research-candidate first pass only. It does not approve an EA, does not add any Phase 1 observer, and does not authorize decile, multisymbol, adversarial, paper-mode, or live execution work for this candidate.

## Data Class

This candidate used a new data class for this repo: GC continuous futures daily volume.

The local source file is:

```text
data/reference/futures/gc_continuous_daily_yahoo_2015_2025.csv
```

It was acquired from Yahoo Finance chart API symbol `GC=F`. This is explicitly a non-authoritative continuous futures volume proxy, not primary CME order-flow or depth data.

## Hypothesis Lock

| Item | Value |
| --- | --- |
| Expert | `h4_gold_futures_volume_climax_v0` |
| Hypothesis file | `docs/hypothesis_h4_gold_futures_volume_climax_v0.md` |
| SHA256 | `ff54364c95f0c1ace5c439ac788c273b735fbb9297ee2fdccd11ee004e158131` |
| Synthetic smoke | PASS |
| Result-producing command | `phase0 run-research-matrix --expert h4_gold_futures_volume_climax_v0 --hypothesis-file docs/hypothesis_h4_gold_futures_volume_climax_v0.md` |

## Matrix Summary

| Cell | Broker | Cost | Trades | PF | Return % | Max DD % |
| ---: | --- | --- | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 16 | 0.7607 | -1.1102 | 2.9104 |
| 2 | capital_com | median | 16 | 0.7607 | -1.1102 | 2.9104 |
| 3 | capital_com | p95 | 16 | 0.7520 | -1.1582 | 2.9413 |
| 4 | pepperstone | best_case | 11 | 0.6417 | -0.9972 | 1.3022 |
| 5 | pepperstone | median | 11 | 0.6417 | -0.9972 | 1.3022 |
| 6 | pepperstone | p95 | 11 | 0.5680 | -1.2082 | 1.5034 |
| 7 | dukascopy | best_case | 20 | 1.1661 | 0.6927 | 2.8039 |
| 8 | dukascopy | median | 20 | 1.1514 | 0.6352 | 2.8272 |
| 9 | dukascopy | p95 | 20 | 1.1208 | 0.5138 | 2.8788 |

## Gate Read

| Gate | Result |
| --- | --- |
| PF >= 1.30 in at least 7/9 cells | FAIL: 0/9 cells |
| Minimum 40 trades per cell | FAIL: 0/9 cells reached 40 trades |
| Cross-venue robustness | FAIL: Capital.com/Pepperstone negative; Dukascopy mildly positive only |
| Concentration | FAIL: very low sample count makes concentration unusable |
| Next validation | STOP: no deciles, multisymbol, intrabar, or Gate 9 |

## Decision

Reject v0 without tuning.

The new GC futures volume proxy was useful as a data-class experiment, but the locked mechanism did not produce enough trades or enough PF strength to continue. This does not prove primary CME order-flow has no value; it only rejects this specific daily continuous-volume proxy definition.
