# Forex Demo Readiness V1

Status: `RESEARCH_WATCHLIST`. No shadow, demo-order, live, account, chart, or
terminal authority.

This package independently audits the adaptive EURUSD Frequency V2 package
without changing its historical artifacts. Its `AUDIT.json` and decision packet
supersede the old `CONTROLLED_SHADOW_DEMO_READY` label on this branch.

The audit:

- reproduces the two standalone MT5 reports and the concatenated 697-trade ledger;
- decomposes the H4 "trend overlay" into its actual same-entry lot increment;
- audits the 58 cross-sleeve overlaps and gross/net EURUSD exposure;
- reports 3-, 6-, 12-, and 24-month metrics and explicit 5-year unavailability;
- applies +0.5 and +1.0 pip round-trip cost stress;
- runs a fixed-seed moving-block bootstrap;
- hashes the source, EX5, preset, INI, report, and compile-log evidence;
- checks report-to-INI input parity;
- audits demo guards, position ownership, and missing shared-account controls;
- snapshots prepared data coverage, the October 2024 quarantine, and the prior
  Forex trial registry.

Run from the repository root with a Python environment containing NumPy, pandas,
PyArrow, and pytest:

```powershell
python forex/forex-demo-readiness-v1/audit_demo_readiness.py
python -m pytest forex/forex-demo-readiness-v1/tests -q
python forex/forex-demo-readiness-v1/generate_manifest.py
```

Important outputs:

- `outputs/AUDIT.json`
- `outputs/FOREX_DEMO_READINESS_AUDIT.md`
- `outputs/DATA_COVERAGE_MANIFEST.json`
- `outputs/PRIOR_TRIAL_REGISTRY.csv`
- `outputs/OVERLAP_EXPOSURE_LEDGER.csv`
- `ARTIFACT_MANIFEST.csv`

The audit is offline. It does not initialize MT5, call a broker API, attach an
EA, or place an order.
