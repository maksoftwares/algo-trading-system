# A3 ML Dukascopy Candidate-Label Factory V1 Result

Date: `2026-07-15`

Classification: `DUKASCOPY_LABEL_DATASET_READY_FAMILY_NO_SURVIVOR`

## Plain-English Decision

The label factory is ready for research-model training. The first symmetric H1 pullback candidate family is not profitable and is rejected without tuning.

This result authorizes offline research training on resolved labels only. It does not authorize Python demo predictions, EA consumption, broker action, or deployment.

## Source Integrity

- Source: verified Dukascopy XAUUSD bid/ask ticks.
- Period: July 2018 through June 2024.
- Verified monthly partitions: `72/72`.
- Source composite SHA-256: `5a4f7ec77dcdc915e945e2dd1941986ba6be7511a7cc745e1d90250f5251f32f`.
- Derived H1 bars: `35,459`.
- MT5 historical prices were not used for signal prices, entries, stops, targets, or exits.

## Label Quality

- Mechanically generated candidates: `3,340`.
- Candidates with no quote inside the frozen five-minute entry window: `77`.
- Entry-window eligible candidates: `3,263`.
- Resolved labels: `3,261` (`99.94%`).
- Unresolved at the end of available history: `2`.
- Long resolved labels: `1,826`.
- Short resolved labels: `1,435`.
- Minority outcome-label share: `33.30%`.
- Every preregistered dataset-quality gate passed.

The `77` entry-window failures are explicitly ineligible candidates, not missing or corrupted outcomes. This follows the preregistered rule that an entry quote must arrive within five minutes. They remain in the audit ledger and are excluded from model rows.

## Fixed-Family Result

| Split | Trades | Win rate | Stress net USD | Stress PF | Average stress R | Maximum closed DD R |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Train | 1,488 | 33.87% | -1,618.30 | 0.8160 | -0.1100 | 175.46 |
| Validation | 1,206 | 31.59% | -1,356.45 | 0.8147 | -0.1528 | 206.21 |
| Test | 567 | 35.45% | -145.32 | 0.9569 | -0.0658 | 88.93 |

Overall:

- Stress net: `-$3,120.07` at fixed `0.01` lot.
- Stress profit factor: `0.8399`.
- Average stress outcome: `-0.1182R` per candidate.
- Long PF: `0.8830`.
- Short PF: `0.7854`.
- All six strategy-research gates failed.

The test segment was less negative than train and validation, but it remained below break-even after the frozen costs. There is no defensible reason to promote or loosen this family.

## What This Achieves

We now have a reusable path that can:

1. Verify raw Dukascopy months against their manifests and SHA-256 hashes.
2. Derive side-specific H1 bars without filling missing market hours.
3. Generate causal mechanical candidates from completed bars.
4. Resolve entries and exits using correct Bid/Ask sides and raw tick order.
5. Record cost-stressed P/L, R, MFE, MAE, holding time, and chronological splits.
6. Keep data-quality acceptance separate from strategy-profitability acceptance.

The next research family must be preregistered independently. This failed family must not be repaired by inspecting losing timestamps and adding calendar masks.
