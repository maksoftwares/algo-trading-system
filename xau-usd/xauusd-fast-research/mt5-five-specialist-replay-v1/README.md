# MT5 Five-Specialist Three-Month Replay V1

This package builds a frozen April-June 2026 MT5 Strategy Tester packet for the
five reported specialists.

- R1 uses its two existing native MT5 components.
- R2 through R5 use a tester-only schedule replay EA against MT5 real ticks.
- The replay changes execution venue and tick path, but does not claim native
  MQL5 signal-generation parity for the Python specialists.
- The EA refuses to initialize outside Strategy Tester and refuses non-demo
  account context.

The replay window is `[2026-04-01, 2026-07-01)` and all tests use `XAUUSD`,
fixed `0.01` lots, and MT5 `Model=4` real ticks.

Build the packet:

```powershell
python build_packet.py
```

Generated schedules and tester configurations are written under `outputs/`.

After the tester runs, collect and verify the native reports:

```powershell
python collect_reports.py
```

The packet also emits an `ALL_SPECIALISTS` replay. It places all six R2-R5
signals on one MT5 balance/equity curve; R1 and R4 have no trades in this
window. This combined run is still schedule replay evidence, not native MQL5
signal-generation parity for R2-R5.

The collector archives the raw HTML reports and charts, replay event logs,
compiled EX5, compile log, machine-readable results, and SHA-256 evidence.
