# Post-Audit Prior-Event Window Correctness Finding

The locked F2026 drift audit exposed a timestamp-unit defect in
`high-frequency-expansion-v1/src/dataset.py`.

Pandas 3 parsed `signal_time` as `datetime64[us, UTC]`. The prior-event builder
converted that series directly to integers, producing microseconds, but
subtracted `Timedelta.value` constants expressed in nanoseconds. Consequently:

- `prior_events_1h` counted roughly the prior 1,000 hours;
- `prior_events_4h` counted roughly the prior 4,000 hours;
- `prior_same_direction_1h` remained correct because it used
  `Timestamp.value`, which is nanoseconds.

This was causal, not future-looking, but it was materially mis-specified and
created artificial secular score drift as candidate density changed.

## Evidence

Across all unique events in the F2026 comparison periods:

| Feature | Stored reference mean | Stored current mean | Corrected reference mean | Corrected current mean |
|---|---:|---:|---:|---:|
| prior_events_1h | 554.75 | 676.90 | 1.18 | 1.17 |
| prior_events_4h | 2008.46 | 2689.59 | 3.79 | 4.04 |

For the frozen F2026 ridge models, the two corrupted fields contributed
approximately `-0.1345` of the downside model's `-0.2776` mean-score shift and
`-0.0570` of the break-and-run model's `-0.3124` mean-score shift. They did not
explain all deterioration: directional returns, EMA distances, spread, and
within-stratum outcome collapse also changed materially.

## Fix And Consequence

The feature builder now explicitly converts timestamps to nanoseconds before
window arithmetic. A regression test uses `datetime64[us, UTC]` and checks
exact 1-hour and 4-hour boundary counts. The corrected source SHA-256 is
`d61e65c2da60b6da1f784dc045908233ca40898e57ae8f5850b06f69abc36edd`;
the updated test SHA-256 is
`54e8c321911ebcd4767a2a79cc46d1a215da0d12db171761c3985be46017d9db`.
The high-frequency package passes `4/4` tests, Ruff, and compilation.

Frozen V3 datasets and model artifacts were not rewritten. They remain valid
records of the experiment but are not eligible as inputs to another model or
for runtime promotion. The next dataset must use a new version, rebuild the
complete candidate ledger and all downstream feature/split artifacts, and
rerun model evaluation under a fresh preregistration. Opening-range reversal
also requires a mechanical strategy redesign because its selected edge was
nonpositive in both comparison periods.
