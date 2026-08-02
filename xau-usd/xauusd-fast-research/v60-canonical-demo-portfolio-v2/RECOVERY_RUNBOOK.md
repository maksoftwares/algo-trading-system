# V60 Demo Disaster-Recovery Runbook

This runbook rebuilds the XAUUSD V60 demo system represented by Git tag
`v60-demo-recovery-20260730`. The tag, recovery manifest, model bundle, source
code, tests, evidence, and six-chart MT5 profile are the durable source of
truth.

The recovery target is:

- Capital.com demo account `1033030`;
- server `Capital.ComMena-Demo`;
- symbol `XAUUSD`;
- terminal root `C:\MT5PortableTier1BestEA`;
- nine deterministic source IDs;
- bounded V4 ML top-ups for confirmed sources only;
- hash-bound drawdown-protection V1 overlay;
- no minimum-balance gate;
- activation-equity-scaled risk limits;
- loss-only `-100 AED` daily guardian;
- no live-account authorization.

Passwords, broker credentials, MT5 installation files, current open positions,
and mutable runtime state are intentionally not stored in Git.

## What Git preserves

Git contains:

1. All deterministic portfolio, feed, execution, risk, and monitoring code.
2. The exact ML serving code, implementation lock, model bundle, and parity
   result.
3. The four required EA sources and exact six-chart MT5 profile snapshot.
4. Fixed Python package versions.
5. Exact source-to-specialist mappings and guardian inputs.
6. The deployment parity artifact.
7. The full before/after replay results and their comparison.
8. A SHA-256 recovery manifest and verifier.
9. Focused tests and the tick-runtime replay implementation.

The authoritative inventory is
`recovery/recovery_manifest.json`. Do not hand-edit it.

## What Git cannot preserve

You must obtain these separately:

1. Windows x64 and internet access.
2. A Capital.com MetaTrader 5 installation.
3. Credentials for demo account `1033030`.
4. Access to `Capital.ComMena-Demo`.
5. Current broker-side positions and deal history.
6. Optional Dukascopy raw ticks when independently rerunning the long-horizon
   replay.

The deployed strategy can resume without the old D-drive research archive.
The archive is needed to reproduce historical research, not to process new
demo signals.

## Normal restart

Use this when the repository, V60 terminal, profile, and login still exist.

1. Start the target terminal:

```powershell
Start-Process "C:\MT5PortableTier1BestEA\terminal64.exe" -ArgumentList "/portable"
```

2. Verify the terminal shows account `1033030`, server
   `Capital.ComMena-Demo`, and the `Default` profile with six XAUUSD charts.
3. Start the supervisor from the repository root:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File `
  .\xau-usd\operations\v60-prospective-supervisor-v1\start_supervisor.ps1
```

4. Verify the repository and live deployment:

```powershell
& .\xau-usd\xauusd-fast-research\v60-canonical-demo-portfolio-v2\.venv\Scripts\python.exe `
  .\xau-usd\xauusd-fast-research\v60-canonical-demo-portfolio-v2\recovery\verify_recovery.py `
  --terminal-root "C:\MT5PortableTier1BestEA"
```

5. Confirm:

- `status.json` reports `ACTIVE_DEMO_BROKER_ACTION`;
- supervisor `status.json` reports `READY`;
- account login is `1033030`;
- `live_authorized` is `false`;
- all nine deployed sources are healthy;
- no hard stop, suspension, or entry-halt file is active.
- `portfolio_protection.enabled` is `true` and
  `profit_protection_close_failures` is `0`.

Runtime status files:

- `C:\MT5PortableTier1BestEA\MQL5\Files\v60_canonical_demo_v2\status.json`
- `C:\MT5PortableTier1BestEA\MQL5\Files\v60_canonical_demo_v2\feed_status.json`
- `D:\AlgoTradingData\prospective\v60-prospective-supervisor-v1\status.json`
- `D:\AlgoTradingData\prospective\v60-deployed-specialist-monitor-v1\status.json`

## Complete-machine recovery

Use this when the repository and terminals are lost.

### 1. Restore the exact Git version

```powershell
git clone https://github.com/maksoftwares/algo-trading-system.git
Set-Location .\algo-trading-system
git checkout v60-demo-recovery-20260730
```

Do not recover from a moving branch without first comparing it to this tag.

### 2. Install prerequisites

Install Git, Capital.com MetaTrader 5, and `uv`. The `uv` installer is
documented at `https://docs.astral.sh/uv/`.

Install or copy MT5 to:

`C:\MT5PortableTier1BestEA`

Launch it once in portable mode:

```powershell
Start-Process "C:\MT5PortableTier1BestEA\terminal64.exe" -ArgumentList "/portable"
```

Log in manually to demo account `1033030` on `Capital.ComMena-Demo`. Do not
store the password in the repository. Add XAUUSD to Market Watch and allow MT5
to download its available M5, H1, and H4 history. Close only this verified
terminal before continuing.

### 3. Rebuild Python and MT5

From the repository root:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File `
  .\xau-usd\xauusd-fast-research\v60-canonical-demo-portfolio-v2\restore_v60_demo.ps1 `
  -TerminalRoot "C:\MT5PortableTier1BestEA" `
  -InstallMt5Profile `
  -EnableAlgoTrading
```

This command:

1. installs Python `3.14.4` through `uv`;
2. creates a dedicated V60 `.venv`;
3. installs the exact runtime package versions;
4. verifies every critical Git artifact against the recovery manifest;
5. compiles all four required EAs with zero errors and warnings;
6. backs up any existing profile;
7. restores the exact six-chart `Default` profile;
8. enables terminal Algo Trading while the terminal is stopped.

### 4. Start and verify

Start MT5 in portable mode, check the account and profile, then run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File `
  .\xau-usd\operations\v60-prospective-supervisor-v1\start_supervisor.ps1
Start-Sleep -Seconds 15
& .\xau-usd\xauusd-fast-research\v60-canonical-demo-portfolio-v2\.venv\Scripts\python.exe `
  .\xau-usd\xauusd-fast-research\v60-canonical-demo-portfolio-v2\recovery\verify_recovery.py `
  --terminal-root "C:\MT5PortableTier1BestEA"
```

Do not consider recovery complete until the verifier passes and the supervisor
reports `READY`.

## Recovery with broker-side open positions

Open positions survive a local computer failure because they are held by the
broker. Treat this as a special recovery:

1. Do not start the Python executor immediately.
2. Log in to MT5 and inspect every XAUUSD position, magic number, stop, target,
   volume, and comment.
3. Compare magic numbers with the nine values in the canonical config.
4. Confirm protective stops exist.
5. Decide whether to manage or close unmatched positions manually.
6. Start the supervisor only after the account is understood.

Never restore an old `state.json` over a newer broker history. The runtime
reconstructs V60 closed P/L from MT5 position-ID lifecycles.

## Mutable state and logs

These files are operational and are not committed:

- V60 `state.json`, feed ledgers, status files, and logs;
- telemetry tick, book, transaction, and heartbeat CSV files;
- supervisor process state;
- MT5 account credentials and `common.ini`;
- halt files.

On a clean recovery, let the system recreate runtime state. Before deleting a
damaged runtime directory, preserve a forensic copy. Never delete state while
V60 positions are open.

## Historical replay restoration

The committed after-repair result is:

- 1,619 closed trades;
- `$2,628.44` net P/L;
- profit factor `1.4398`;
- maximum lifetime equity drawdown `$227.24`;
- no flat suspended deadlock.

The full result and its SHA-256 identity are in `evidence/`.

To recompute it, restore Dukascopy XAUUSD ticks beneath:

`D:\AlgoTradingData\C_DRIVE\DukascopyTickDataFoundationV1\raw\XAUUSD`

The replay evidence used:

- 14,579 source files;
- 2,374,468,868 source bytes;
- 107,229,569 source ticks;
- first cycle `2021-01-04T15:00:05Z`;
- last cycle `2026-06-29T01:59:55Z`.

Then run:

```powershell
& .\xau-usd\xauusd-fast-research\v60-canonical-demo-portfolio-v2\.venv\Scripts\python.exe `
  .\xau-usd\xauusd-fast-research\codex-v60-tick-runtime-replay-v1\run_replay.py `
  --contract .\xau-usd\xauusd-fast-research\codex-v60-tick-runtime-replay-v1\config\SAFETY_REPAIR_REPLAY_CONTRACT.json `
  --output-directory .\xau-usd\xauusd-fast-research\codex-v60-tick-runtime-replay-v1\outputs\recovery-check
```

Recomputed evidence must be compared with the committed result. Dukascopy is
not the Capital.com execution feed, so prospective demo observation remains
the broker-specific validation.

## Tests

From the repository root:

```powershell
$python = ".\xau-usd\xauusd-fast-research\v60-canonical-demo-portfolio-v2\.venv\Scripts\python.exe"
Push-Location .\xau-usd\xauusd-fast-research\v60-canonical-demo-portfolio-v2
& .\.venv\Scripts\python.exe -m pytest .\tests -q
Pop-Location
& $python -m pytest .\xau-usd\xauusd-fast-research\codex-v60-tick-runtime-replay-v1\tests -q
& $python -m pytest .\xau-usd\operations\v60-prospective-supervisor-v1\tests -q
& $python -m pytest `
  .\xau-usd\xauusd-phase1\tests\test_xau_prospective_telemetry_collector.py `
  .\xau-usd\xauusd-phase1\tests\test_account_daily_guardian_scope.py -q
```

## Safety rules

1. This package is demo-only. `live_authorized` must remain `false`.
2. Never commit broker passwords or API keys.
3. Never run the superseded V60 core executor beside this canonical executor.
4. Never run two copies of the V60 feed or portfolio worker.
5. Never bypass the profile, parity, model-hash, account, server, currency,
   spread, drawdown, or order-check gates.
6. V8 and V25 remain baseline-only probation sources and cannot receive ML
   top-ups.
7. The ML layer can only add one bounded top-up after a baseline fill. Failure
   always falls back to the deterministic baseline.
8. A successful historical replay is not a profit guarantee.
