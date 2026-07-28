# Codex V60 ML Sizing Causal Retest V1

This package independently retests the proposed V60 ML sizing overlay after
removing the entry-bar look-ahead and reconciling the experiment to the current
deployed V60 population.

The package is historical research only. It does not authorize ML serving,
shadow consumption, demo orders, live orders, EA changes, account changes, or
MT5 runtime changes.

See `PREREGISTRATION.md` and
`config/CAUSAL_RETEST_CONTRACT.json` for the outcome-blind rules.

## Result

The locked retest rejects the ML overlay for demo execution.

- All 2,069 feature rows use M5 bars that had completed before entry.
- The continuous research policy improves net P&L, but is not executable from
  a 0.01-lot base and fails the floating-drawdown, green-month, yearly
  consistency, and net-to-drawdown gates.
- The broker-expressible policy makes less than deterministic V60, has worse
  floating drawdown, and fails the weekly dependence-aware confidence gate.
- No MT5, runtime, shadow, or broker setting was changed.

Run the audit with:

```powershell
& '..\balanced-horizon-ml-v5\.venv\Scripts\python.exe' run_retest.py
```

The reviewer-facing decision is in `outputs/RESULT.md`; exact metrics and gate
outcomes are in `outputs/RESULT.json`.
