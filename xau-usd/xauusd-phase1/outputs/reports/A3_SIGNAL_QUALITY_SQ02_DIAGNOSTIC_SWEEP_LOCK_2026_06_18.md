# A3 Signal Quality SQ-02 Diagnostic Sweep Lock

Status: `PASS`

Boundary: offline discovery / shadow-only. No promotion evidence, MT5 runtime, terminal profile, preset arming, order, position, or broker action was touched.

Base commit: `c257dd6`

## Artifacts

- Sweep: `docs/A3_SIGNAL_QUALITY_DIAGNOSTIC_SWEEP_V1_2026_06_18.md`
- Manifest: `outputs/manifests/A3_SIGNAL_QUALITY_DIAGNOSTIC_SWEEP_V1.sha256.json`
- SHA256: `abe95ebcdddb14f710b911dbe93bb12d6603a24b3475df06a8e473bc1763dc58`

## Registered Candidates

- `B0_RAW_ALL_SESSION`
- `B1_EVENING_BASELINE`
- `F_LOOSE_CT_VETO`
- `F_H1_ALIGN`
- `F_H1_M15_ALIGN`
- `F_RETEST_LIGHT`
- `F_LOOSE_CT_PLUS_RETEST_LIGHT`
- `A3_SQ_MTF_ONLY_V1`
- `A3_SQ_RETEST_ONLY_V1`
- `A3_SQ_COMBINED_V1`

## Frequency Floor

```text
signal retention >= 40% of B0
virtual-trade retention >= 35% of B0
closed virtual trades >= 100
median weekly trades >= 40% of B0 median weekly trades
```

## Verification

```text
cd xau-usd/xauusd-phase1
..\xauusd-phase0\.venv\Scripts\python.exe -m pytest tests\test_a3_signal_quality_hypothesis.py -q
8 passed

..\xauusd-phase0\.venv\Scripts\python.exe scripts\audit_phase1_arming.py
Phase 1 arming audit OK: committed arming/profile artifacts are disarmed and auth tokens are blank.

Get-FileHash -Algorithm SHA256 docs\A3_SIGNAL_QUALITY_DIAGNOSTIC_SWEEP_V1_2026_06_18.md
ABE95EBCDDDB14F710B911DBE93BB12D6603A24B3475DF06A8E473BC1763DC58
```

## Next

SQ-03 is the offline Python discovery sweep. If no candidate clears the V2 registration eligibility bar, stop and keep A3 paused.
