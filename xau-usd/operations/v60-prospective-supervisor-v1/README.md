# V60 Prospective Runtime Supervisor V1

This operational package keeps the canonical XAUUSD demo workers observable
and restartable as one system.

It does not contain strategy logic, economic thresholds, model inference, order
construction, or broker APIs. It does not modify V59/V60, the locked July 27
prospective contracts, or their output ledgers.

The supervisor watches:

- the Capital.com MT5 terminal for demo account `1033030`;
- the V60 canonical execution-feed worker;
- the read-only outcome/R5 research-feed worker;
- the V60 canonical portfolio worker with the drawdown-protection V1 and V4 ML
  overlays; and
- the read-only monitor covering all nine deployed source IDs and telemetry
  date transport.

Missing Python workers are restarted with their existing commands. A running
portfolio worker that reports anything other than
`ACTIVE_DEMO_BROKER_ACTION`, or a stale status, for three consecutive
supervisor cycles is stopped and restarted as one process group.
The executor independently reconnects a stale MT5 API session and holds a
single-instance lock. The MT5
terminal is monitored but is never started, stopped, or restarted by this
package. Each cycle writes:

- `process_state.json`, containing process presence and worker-recovery state; and
- `status.json`, containing the consolidated readiness decision.

Runtime files are stored outside the repository at:

`D:/AlgoTradingData/prospective/v60-prospective-supervisor-v1`

Start the hidden supervisor:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File `
  xau-usd\operations\v60-prospective-supervisor-v1\start_supervisor.ps1
```

Stop only the supervisor and its six Python workers:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File `
  xau-usd\operations\v60-prospective-supervisor-v1\stop_supervisor.ps1
```

Run one foreground reconciliation:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File `
  xau-usd\operations\v60-prospective-supervisor-v1\runtime_supervisor.ps1 -Once
```

Full machine-loss recovery is documented in
`xau-usd/xauusd-fast-research/v60-canonical-demo-portfolio-v2/RECOVERY_RUNBOOK.md`.
