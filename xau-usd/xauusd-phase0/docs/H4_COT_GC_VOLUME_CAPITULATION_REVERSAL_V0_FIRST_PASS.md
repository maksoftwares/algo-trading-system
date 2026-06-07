# H4 COT + GC Volume Capitulation Reversal v0 First Pass

Date: 2026-06-07

Expert: `h4_cot_gc_volume_capitulation_reversal_v0`

Hypothesis file: `docs/hypothesis_h4_cot_gc_volume_capitulation_reversal_v0.md`

SHA256: `0b105ea322a87678232ab39d334b28dd3d4e37bbea7107a538c764268a5ddfb5`

## Verdict

REJECTED_FIRST_PASS. Do not tune v0.

This candidate combined official CFTC gold COT positioning extremes with shifted GC futures daily-volume climax and completed H4 reversal candles. The combined filter did not create a worthy EA. It produced sparse, broker-fragmented results: one Capital.com trade, three losing Pepperstone trades, and a small Dukascopy-only PF pocket.

## Smoke

PASS.

- Signals: 1
- Phase 0 result run allowed: false

## Matrix Summary

| Cell | Broker | Cost | Trades | PF | Return % | Max DD % | Max zero months | Concentration |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 1 | inf | 0.7102 | 0.0000 | 32 | 100.00 |
| 2 | capital_com | median | 1 | inf | 0.7102 | 0.0000 | 32 | 100.00 |
| 3 | capital_com | p95 | 1 | inf | 0.7062 | 0.0000 | 32 | 100.00 |
| 4 | pepperstone | best_case | 3 | 0.0000 | -1.3920 | 1.3920 | 27 | 100.00 |
| 5 | pepperstone | median | 3 | 0.0000 | -1.3920 | 1.3920 | 27 | 100.00 |
| 6 | pepperstone | p95 | 3 | 0.0000 | -1.4024 | 1.4024 | 27 | 100.00 |
| 7 | dukascopy | best_case | 7 | 1.9413 | 1.2710 | 0.8448 | 10 | 51.74 |
| 8 | dukascopy | median | 7 | 1.9677 | 1.2714 | 0.8663 | 10 | 51.09 |
| 9 | dukascopy | p95 | 7 | 1.9045 | 1.2136 | 0.8844 | 10 | 52.98 |

## Gate Read

- PF >= 1.30 cells: 6/9 if counting the one-trade Capital.com infinite PF cells, but this is not meaningful.
- Trade-count cells: 0/9.
- Broker consistency: failed; Pepperstone is negative and Capital.com is a single-trade artifact.
- Max zero-trade months: 32.
- Concentration: failed across all cells due tiny samples.

## Decision

Reject without tuning. Combining COT positioning with the non-authoritative public GC volume proxy made the filter too sparse and did not generalize across broker windows. The only positive evidence is Dukascopy-only and cannot support promotion.
