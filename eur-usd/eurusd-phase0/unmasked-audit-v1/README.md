# EURUSD V1 Unmasked Audit

This package executes the independent reviewer's single next action:

`EURUSD_M30_RSI_BB_CLOSE_FADE_LONG_V1_UNMASKED_AUDIT`

The only strategy change is removal of the retrospectively selected blocked
hours `6,7,10,13`. Frozen V1 remains immutable.

The audit also identifies a prior packet defect: exact V1 MT5 used
`InpMinBodyFraction=0.40`, but the published V1 preset stated `0.0`. The exact
unmasked comparison retained `0.40`, so attribution is valid against the actual
V1 run. No intervention is authorized until that contract discrepancy and the
startup-latch behavior are resolved in a newly frozen baseline.

The package contains the preregistration, exact MT5 report and ledgers, a
zero-order M30 bar telemetry run for episode labeling, a matched V1/unmasked
comparison, cost stresses, calendar and broker-time buckets, an episode branch
decision, source/EX5/compiler evidence, and a hash manifest.

Run the derived audit after the exact MT5 and bar-export outputs exist:

```powershell
python eur-usd/eurusd-phase0/unmasked-audit-v1/run_unmasked_audit.py
```

After staging the complete packet, freeze checkout-stable SHA256 values from
the Git index:

```powershell
python eur-usd/eurusd-phase0/unmasked-audit-v1/freeze_git_manifest.py
```

This is retrospective Strategy Tester research only. It does not authorize
shadow, demo, live, or broker action.
