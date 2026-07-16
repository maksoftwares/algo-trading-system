# A3 ML Broker Cost Calibration V1 Preregistration

Date: 2026-07-16

## Purpose

Iteration 4 showed that only 10.61% of broad M5 events had an executable barrier label
under the locked 0.15ATR spread ceiling. Before selecting higher-timescale trade
geometry, V1 measures the target demo broker's actual XAUUSD Bid/Ask spread and compares
it with the verified Dukascopy Bid/Ask cache during their common June 2026 period.

This is execution calibration, not strategy research. It cannot authorize model
training, an EA consumer, demo orders, or live orders.

## Locked Broker Source

The source is the read-only C02 multi-account MT5 export:

- dataset: `xauusd_c02_multiacct_202606262247_g0a9823b0_c9221d066`;
- requested start: 2026-06-01 UTC;
- snapshot cutoff: 2026-06-26 22:47 UTC;
- C02 report SHA256:
  `c0568d6db09c14055400f6025c49d77b5b99854a973bdfd3d3b29909d42ab355`;
- root manifest SHA256:
  `a8a9271cab3728a363ecb06cd8c8c276d9e846b7cb3f9e35db2008524755dc70`.

All three exports identify `Capital.ComMena-Demo`, XAUUSD with point 0.01, and contain
7,616,882 ticks across the same 18 active UTC date files. Account A3 / `1033669` is the
canonical feed because it is the last account explicitly selected by the owner. A1 and
A2 are same-server mirrors used only for boundary consistency checks. They are not
three independent market samples.

Every active canonical tick file must match its C02 manifest hash. The first and last
quote tuple for every active date must match across all three account exports after
account identity columns are removed.

## Locked Dukascopy Source

The comparison source is the 708,538-row verified M5 Bid/Ask feature cache:

- feature SHA256:
  `e587306f530a615dfdc6f869c4f79f881cfa0b572e078fd26d3c9995fbc66228`;
- source digest:
  `4282fffda04d3b23218d4064b67e036af15b9b2937df3f0fb434d68bfb6ae738`.

The run must fail closed on a hash, row-count, chronology, Bid/Ask, or spread
reconciliation mismatch.

## Frozen Measurements

For the canonical broker ticks, V1 reports:

- absolute spread quantiles;
- spread-point quantiles;
- daily and UTC-hour spread distributions;
- invalid or negative Bid/Ask rows;
- timestamp chronology and duplicate quote rows;
- M5 median, 90th percentile, 99th percentile, and last spread.

For matched broker/Dukascopy M5 buckets, V1 reports absolute and ATR-normalized spread
distributions and broker-to-Dukascopy differences. At least 3,000 matched M5 bars are
required.

The locked broker spread floor is the canonical tick-level 90th percentile. This does
not replace native historical Dukascopy Bid/Ask execution. A later strategy screen must
stress entry cost to at least that floor and add $0.30 per 0.01 lot. Total stressed
entry cost must be no more than 0.15 of initial risk.

No threshold may be changed after the V1 distribution is seen.

## Auxiliary Evidence

The existing Phase 2 actual-demo cost report is locked for context only. Its raw order
log is no longer present, so V1 does not use it to calibrate or pass a gate.

## Decision Rule

- any source or quality failure: `BROKER_COST_CALIBRATION_INVALID`;
- all quality gates pass: `BROKER_COST_CALIBRATION_VALID`;
- a valid result may lock cost assumptions for a new Iteration 5 strategy
  preregistration;
- no result can authorize a strategy, model, EA, demo, or live action.

## Authorization

- research only: yes;
- strategy parameter selection: no;
- model training: no;
- Python demo predictions: no;
- EA consumption: no;
- broker action: no.
