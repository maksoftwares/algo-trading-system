# Chop Microstructure-State Campaign V16 Preregistration

## Purpose and exposed history

V12 through V15 rejected price-anchor, episode-state, direction-inversion, and
side-only chop hypotheses. An earlier all-regime M5 microstructure campaign also
found no discovery survivor. V16 tests the missing interaction: whether native M5
flow, book absorption, and liquidity conditions become useful specifically while
the latest completed H4 owner is `CHOP`.

All cited outcomes were exposed before V16. This is historical discovery, not
independent evidence, and the contract hashes those prior results as provenance.

## Frozen data and causality

- Free verified Dukascopy bid/ask M5 cache from 2016-07-01 through 2026-07-01.
- Tick imbalance, book imbalance, quote intensity, spread, realized variance, and
  price efficiency are measured only on the completed signal bar or earlier bars.
- H4 regime ownership is attached from the latest completed H4 bar.
- Chop episode age is counted causally in M5 bars.
- Entry is the next contiguous side-correct M5 open; missing intervals reject entry.
- Same-bar stop and target collisions resolve stop first.

## Frozen attempts

Attempts 31239 through 32238 contain exactly 1,000 policies:

- 200 flow-continuation policies.
- 200 flow-exhaustion policies.
- 200 book-absorption policies.
- 200 liquidity-shock reversion policies within H4 chop.
- 200 post-shock normalization policies within H4 chop.

Each source mechanism is additionally conditioned on causal chop episode age.
Manifest membership uses raw signal counts only; no outcomes are available during
preflight.

## Frozen execution and gates

Mechanism-specific stops are 1.0 to 1.2 ATR, targets are 1.4R to 1.8R, and maximum
holds are 60 or 120 minutes. Spread, ticket cost, holding cost, and 0.05R stress
slippage are deducted. Policies permit one open trade and at most six entries per
UTC day.

A finalist needs at least 100 trades and 15 in every era, total stress PF at least
1.25, every-era stress PF at least 1.10, every-era average stress R at least 0.02,
closed drawdown no more than 25R, and positive net stress R after removing its five
largest winners. Benjamini-Hochberg correction applies across all 1,000 policies at
FDR 0.10.

## Decision rule

Any survivor remains a historical candidate requiring independently frozen
replication and prospective shadow evidence. Failure rejects this microstructure by
H4-chop interaction; gates will not be weakened. Shock remains an abstain state at
the portfolio level.
