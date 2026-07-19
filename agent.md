# A1 XAUUSD Authoritative Handoff

Updated: `2026-07-19`

## Repository authority

- Base commit: `006824cde421ea61a0bcdb074804f9ccf95c17a9`
- Current operational branch: `codex/xau-independent-specialists-v1`
- Current pushed HEAD: `40d4f1c74dbb7932d5121090e30320ba997286b4`
- Scope: A1 XAUUSD repository research, exact-MT5 Strategy Tester evidence, offline analysis, and shadow-only preparation.
- This file replaces the prior oversized handoff. If an older statement conflicts with the documents below, the documents below control.

## Governing documents

1. [Master direction](xau-usd/xauusd-phase1/docs/A1_XAU_PROFITABLE_SYSTEM_MASTER_DIRECTION_2026_07_10.md)
2. [Current research freeze](xau-usd/xauusd-phase1/docs/A1_XAU_CURRENT_RESEARCH_FREEZE_2026_07_10.md)
3. [Router entry/hold-path audit preregistration](xau-usd/xauusd-phase1/docs/A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_PREREG_2026_07_10.md)
4. [Independent-specialist primary direction](xau-usd/xauusd-phase1/docs/A1_XAU_INDEPENDENT_SPECIALIST_PRIMARY_DIRECTION_2026_07_12.md)

Read all four before changing code or generating evidence.

## Exact north star

> Build an automated XAUUSD system that produces positive net returns over rolling 6- and 12-month periods, survives realistic costs and regime changes, limits portfolio equity drawdown, and can eventually support controlled withdrawals from accumulated profits.

Authoritative status: `NO_GO_RESEARCH_ONLY`.

Priority is safety, causal correctness, stressed expectancy, equity-drawdown control, robustness, independence, and forward confirmation. Activity is secondary and must never be forced.

## Frozen research state

### R6 primary independent-specialist lane

- Specialist: `R6_H4_DISTRIBUTION_BREAK_FAILED_RECLAIM_SHORT_V1`.
- Standing: `PRIMARY_INDEPENDENT_SPECIALIST_LANE`.
- Economic mandate: pre-downtrend H4 distribution / first failed-H1-reclaim short
  while Router V1 is `UPTREND` or `CHOP`.
- Immediate action: `NP1-A`, the market-only native Router/contract acquisition
  lock packet.
- NP1 is a mandatory bounded prerequisite within R6, not a second program.
- Historical R6 P/L, census output, MT5 strategy execution, and portfolio evidence
  remain unauthorized at IS1-A.
- No parallel specialist family is authorized. H1/H4 range-box research is backlog
  only if R6 closes and a later owner/reviewer packet selects it.

### R1+R2

- `current_r1_r2_baseline` is the only current research control.
- It is an offline/component-exact historical control, not an integrated portfolio pass and not deployment evidence.
- R1 is the primary bullish/uptrend profit engine.
- R2 is the strict downtrend hedge and secondary profit source.

The four frozen sources also preserve legacy rules: a now-forbidden previous-month
P/L health gate, two now-forbidden directional session gates, and a source-local
daily-loss stop that cannot be reused as standalone alpha evidence. They remain only
to keep the 678-trade audit identity unchanged. Any future containment must be the
shared preregistered integrated risk policy, not a source-local historical rescue.
They cannot enter an integrated candidate unless a later reviewed packet resolves
rule admissibility and each source independently passes the master standalone gates.

Rule-admission status: `BLOCKED_LEGACY_RULE_ADMISSIBILITY`.

The legacy upstream trade parser also FIFO-paired exits by direction rather than by
native MT5 position ID: `388/678` rows have a non-native exit deal and `387/678` a
non-native individual P/L assignment, although the exit/P&L multiset and all
source/aggregate totals remain correct. The router audit must first reconstruct the
same 678 entries by native position ID and publish exact reconciliation; no path
classification may use the legacy FIFO pair.

Attribution status: `REPAIR_REQUIRED_NATIVE_POSITION_JOIN`.

Frozen metrics: `678` trades; `51.03%` win rate; `2.6082` realized W/L; `2.7182` profit factor; `+$9,640.05` net; `+$9,436.65` stress net at `-$0.30/ticket`; `+$764.92` recent-three-month net; `$889.69` maximum closed drawdown; `26` positive months; approximately `21.28%` active weekdays.

Frozen ledger: [current R1+R2 baseline](xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709_current_r1_best_r2_pullback_plus_r2_impulse_body45_atr45_daily_loss10_KEPT.csv)

Ledger SHA256: `47cbe6a562ba2874d93a97255affbde613566ed06340a149ed2795d69a5dae52`

### R3

- Standing: `STANDALONE_SHADOW_ONLY`.
- Portfolio use is killed by the drawdown gate.
- Evidence: `139` R3 trades, `110` same-opportunity R1-box overlaps, and `29` non-overlaps.
- Do not retest source priority, tune R3, add a drawdown governor, or call it diversification.

### R4

- No R4/chop specialist survived.
- Default chop action is `NO_TRADE`.
- Do not create activity filler or another micro-reclaim repair.

## Evidence boundary

- All inspected history through `2026-06-30` is `DEVELOPMENT_DATA`.
- It is not an untouched holdout and may not be relabeled as one.
- Historical exact MT5 can diagnose execution and causal behavior; it cannot remove selection bias.
- Offline recomposition is diagnostic only and cannot authorize portfolio promotion.
- Final confirmation requires locked, genuinely new forward-shadow evidence.

## Authorization flags

```text
demo_authorized: false
live_authorized: false
broker_action_authorized: false
runtime_attach_authorized: false
strategy_tuning_authorized: false
new_specialist_authorized: R6_REPOSITORY_RESEARCH_ONLY
parallel_specialist_lane_authorized: false
```

No demo/live attach or broker order outside the isolated Strategy Tester is allowed.
No real broker/account change, risk-setting change, runtime-state change, or
production-terminal touch is allowed.

## Immediate next task

`R6-NP1-A_MARKET_ONLY_NATIVE_PARITY_ACQUISITION_LOCKS`

Create only the NP1-A acquisition locks after IS1-A passes reviewer audit. NP1-A
freezes the deterministic market-only Router/contract oracle source contract, output
schemas, exact tester boundary, hashes, and zero-action gates. It contains no MQ5,
Python implementation, tests, compiled artifacts, MT5 evidence, census, or P/L.

The old `A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_V1` is now
`DEFERRED_CONTROL_DIAGNOSTIC`. It remains required before the old R1+R2 control can
ever enter an integrated portfolio, but it does not block R6 standalone discovery.

## Immediate sequence

1. IS1-A owner-direction supersession and R6 primary-lane lock.
2. NP1-A market-only native-parity acquisition locks.
3. NP1-B oracle/probe implementation and tests.
4. NP1-C exact zero-action native evidence.
5. C2R5 native-parity and input-attestation closure.
6. C3A exact historical-input lock.
7. C3 outcome-blind incidence and USD 1,000 contract census.
8. If C3 passes, one standalone exact-MT5 preregistration and one result.
9. If standalone passes, sealed independence audit.
10. If independence passes, forward-shadow lock.

Do not start a second specialist family, optimization, threshold neighbor, session or
calendar mask, management variant, portfolio rescue, or historical P/L study outside
this sequence.

## Isolated tester boundary

- Exact runs are allowed only in the isolated Strategy Tester workspace: `C:\MT5A1M5MomentumBacktest`.
- Use local tester agents only; no remote/cloud agents and no visual/runtime attachment.
- Keep account context, terminal profiles, charts, live/demo terminals, positions, and broker state untouched.
- Freeze and hash EA source, EX5, tester INI, compile log, raw logs, reports, and derived artifacts for each evidence run.
- The audit baseline must be derived from base commit `006824cde421ea61a0bcdb074804f9ccf95c17a9`, not from uncommitted campaign EA changes.

## Prior campaign quarantine

- The prior specialist campaign and its uncommitted files are `DEVELOPMENT_DATA` and nonpromotion evidence only.
- Its checkpoint remains `NO_QUALIFIED_STANDALONE_SPECIALIST_NO_PORTFOLIO_TEST_AUTHORIZED`.
- The previously completed mode-27 five-control reconstruction is quarantined as development-only diagnostics.
- It did not authorize mode-27 candidate implementation or execution, does not enter the router-audit decision, and is not forward evidence.
- Do not continue mode-27 or merge prior campaign trading-logic changes into the governance/audit baseline.

## Terminal rule

The valid outcomes include `NO_GO`, `CONTINUE_EVIDENCE`, `NO_TRADE`, and `FREEZE_CURRENT_BASELINE`. Never weaken a gate to avoid one of them. Build only the smallest integrated system whose expectancy, regime ownership, independence, equity risk, and forward survival can be demonstrated without changing rules after seeing results.

## Restart Handoff - 2026-07-15

- Pre-restart state snapshot recorded at `xau-usd/xauusd-phase1/outputs/reports/RESTART_STATE_SNAPSHOT_2026_07_15.md` and `.json`.
- Snapshot captured nine running MT5 terminals, relaunch commands, git HEAD/dirty status, latest runtime chart inventory, runtime authorization reconciliation, observer heartbeat, recent log roots, and read-only MT5 account/position state.
- Important pre-existing status: `generate_runtime_authorization_reconciliation.py` returned `FAIL_CURRENT_RUNTIME_DRIFT` before restart. Do not treat that as restart-caused without comparing the saved snapshot.
- Owner chose to keep guardian micro-close trades as future evaluation evidence. Do not change entry/guardian behavior during restore unless newly instructed.
- After reboot, relaunch/verify terminals, then rerun runtime authorization reconciliation, A1/A2 920101 supplemental verification, observer heartbeat, and status dashboard freshness before making any runtime changes.

## Current Owner Supersession - 2026-07-19

This section is the authoritative restart and continuation handoff. It supersedes
the stale `Immediate next task`, `Immediate sequence`, R6-only research direction,
and the nine-terminal July 15 restore count above. Keep the older sections as
historical governance context, but do not resume that older sequence by accident.

### Current objective and honest status

- Goal: build several independent XAUUSD specialists that collectively produce a
  large enough quality-candidate pool for an ML ranker/router while keeping positive
  expectancy and controlled shared-account equity drawdown.
- Desired end-state frequency is approximately one to two executed trades per
  weekday. This is a research target, never permission to force a trade.
- The candidate pool should eventually provide roughly four to seven qualified
  candidates per weekday so an ML layer can reject weak candidates without reducing
  execution frequency below the target.
- The frequency goal has **not** been achieved. The latest MT5 three-month window
  produced six trades across 65 weekdays, or `0.09` trades per weekday. Two trades
  per weekday would have required about 130 trades in the same window.
- Profitability is promising development evidence, not proof. Six recent trades are
  too few to establish a stable edge.
- Current authorization remains research/shadow only for the new specialist/ML work.
  Do not enable new Python, EA, demo, live, or broker execution from these research
  results without a separate reviewed decision.

### Research progress now preserved

1. A deterministic 1,000-attempt H1 campaign completed all `1000/1000` attempts
   across ten archetypes. It produced zero two-window passes and zero finalists.
   This was a valid rejection result, not a reason to weaken gates. Local evidence:
   `xau-usd/xauusd-fast-research/thousand-strategy-campaign-v1/outputs/THOUSAND_STRATEGY_SCREEN_RESULT.md`.
2. Later bounded, regime-specific campaigns produced five historical specialist
   definitions:
   - `R1_UPTREND`
   - `R2_DOWNTREND`
   - `R3_COMPRESSION`
   - `R4_CHOP`
   - `R5_TRANSITION`
3. Historical development-window report through 2026-06-30:

| Window | Trades | Net USD | PF | Closed DD USD | Important limitation |
|---|---:|---:|---:|---:|---|
| 3M | 6 | 192.59 | 3.566 | 46.99 | Only three specialists active |
| 6M | 37 | 3,302.88 | 12.778 | 57.46 | Additive, no shared risk engine |
| 1Y | 160 | 4,508.78 | 3.492 | 889.69 | Development data |
| 2Y | 439 | 7,332.55 | 2.708 | 889.69 | Development data |

   Source: `xau-usd/xauusd-fast-research/five-specialist-window-report-v1/outputs/FIVE_SPECIALIST_WINDOW_REPORT_V1.md`.
4. MT5 real-tick validation ran for 2026-04-01 through 2026-06-30 using
   `XAUUSD`, M5, model 4 (`100% real ticks`), fixed `0.01` lot, and a USD 1,000
   tester deposit:

| Specialist | MT5 mode | Trades | Net USD | PF | Max equity DD |
|---|---|---:|---:|---:|---:|
| R1 uptrend | Native MT5, two components | 0 | 0.00 | 0.00 | 0.00% |
| R2 downtrend | Frozen Python schedule replay | 2 | 130.57 | 3.95 | 9.17% |
| R3 compression | Frozen Python schedule replay | 2 | -3.88 | 0.85 | 6.28% |
| R4 chop | Frozen Python schedule replay | 0 | 0.00 | 0.00 | 0.00% |
| R5 transition | Frozen Python schedule replay | 2 | 54.24 | 8.07 | 2.80% |
| Combined | One MT5 account curve | 6 | 180.93 | 3.31 | 8.81% |

   Combined balance drawdown was `$44.29 (3.61%)`; maximal floating equity
   drawdown was `$114.08 (8.81%)`. All six replay signals opened and none were
   missed. R3 failed venue portability, while R1 and R4 had no opportunities.
   R2-R5 evidence validates MT5 execution of frozen signal times, not native MQL5
   signal-generation parity. Full packet:
   `xau-usd/xauusd-fast-research/mt5-five-specialist-replay-v1/outputs/reports/FIVE_SPECIALIST_MT5_3M_RESULTS.md`.
5. The exact MT5 packet, raw reports/charts, schedules, event logs, source/EX5
   hashes, and compile result (`0 errors, 0 warnings`) are committed and pushed in
   `40d4f1c7`.
6. The next research phase is candidate expansion, not immediate model promotion:
   retain R2/R5 as provisional baselines, repair or replace R3, create active R1/R4
   opportunity coverage, and add orthogonal M5/M15/H1/session mechanisms. Evaluate
   the coverage-versus-expectancy frontier with realistic costs and shared-account
   equity risk before training an execution-facing model.
7. ML should initially rank, route, calibrate, or veto mechanically generated
   candidates. It should not invent all entries or force a daily quota. Training
   data must include candidates that were rejected/no-trade, causal features, and
   high-quality outcome labels.
8. `DATABENTO_API_KEY` is absent from process, user, and machine environment scopes
   as of this snapshot. Do not make paid Databento requests. Do not create extra
   accounts to multiply free credits. Databento account deletion is a user-portal
   action and remains unverified here.

### Pre-restart runtime snapshot

Captured at `2026-07-19T04:08:29+04:00` (`2026-07-19T00:08:29Z`). There are
exactly ten running MT5 terminals. All ten were read through the local MT5 API:
they were connected, with zero open positions and zero pending orders at snapshot
time. Account balances are comparison evidence only and may legitimately change
before or after restart.

| Terminal | Login / server | Balance | Equity | Positions | Orders |
|---|---|---:|---:|---:|---:|
| GoldMission | `121409` / `Capital.ComMena-Live` | 0.00 | 0.00 | 0 | 0 |
| PositionPathObserver | `1025742` / `Capital.ComMena-Demo` | 1,439.65 | 1,439.65 | 0 | 0 |
| ProspectiveCollector | `1033669` / `Capital.ComMena-Demo` | 2,998.45 | 2,998.45 | 0 | 0 |
| RepairLane | `1033669` / `Capital.ComMena-Demo` | 2,998.45 | 2,998.45 | 0 | 0 |
| ShadowFixObservers | `1025742` / `Capital.ComMena-Demo` | 1,439.65 | 1,439.65 | 0 | 0 |
| SpreadLogger | `121409` / `Capital.ComMena-Live` | 0.00 | 0.00 | 0 | 0 |
| Tier1BestEA | `1033030` / `Capital.ComMena-Demo` | 3,654.45 | 3,654.45 | 0 | 0 |
| Tier1PathObserver | `1033030` / `Capital.ComMena-Demo` | 3,654.45 | 3,654.45 | 0 | 0 |
| TrendGuardedFixObservers | `1025742` / `Capital.ComMena-Demo` | 1,439.65 | 1,439.65 | 0 | 0 |
| StandardA1 | `1025742` / `Capital.ComMena-Demo` | 1,439.65 | 1,439.65 | 0 | 0 |

### Exact MT5 relaunch matrix

Before launching anything after reboot, enumerate existing `terminal64.exe`
processes by executable path. Never launch a duplicate instance for a root that is
already running.

| Label | Exact relaunch command |
|---|---|
| GoldMission | `"C:\MT5PortableGoldMission\terminal64.exe" /portable /config:C:\MT5PortableGoldMission\Config\phase1_dry_run_startup.ini` |
| PositionPathObserver | `"C:\MT5PortablePositionPathObserver\terminal64.exe" /portable /config:C:\MT5PortablePositionPathObserver\Config\position_path_observer_startup.ini` |
| ProspectiveCollector | `"C:\MT5PortableProspectiveCollector\terminal64.exe" /portable /config:C:\MT5PortableProspectiveCollector\Config\xau_prospective_collector_startup.ini` |
| RepairLane | `"C:\MT5PortableRepairLane\terminal64.exe" /portable` |
| ShadowFixObservers | `"C:\MT5PortableShadowFixObservers\terminal64.exe" /portable` |
| SpreadLogger | `"C:\MT5PortableSpreadLogger\terminal64.exe" /portable /config:C:\MT5PortableSpreadLogger\Config\phase0_spread_logger_startup.ini` |
| Tier1BestEA | `"C:\MT5PortableTier1BestEA\terminal64.exe" /portable` |
| Tier1PathObserver | `"C:\MT5PortableTier1PathObserver\terminal64.exe" /portable /config:C:\MT5PortableTier1PathObserver\Config\position_path_observer_startup.ini` |
| TrendGuardedFixObservers | `"C:\MT5PortableTrendGuardedFixObservers\terminal64.exe" /portable` |
| StandardA1 | `"C:\Program Files\MetaTrader 5\terminal64.exe"` |

### Terminal roles, attachments, and log roots

| Terminal | Current role/attachments | Primary log root |
|---|---|---|
| GoldMission | Startup `Phase1DryRunShell`; startup config has `AllowLiveTrading=0`; writes `decision_log.csv` | `C:\MT5PortableGoldMission\MQL5\Files` |
| PositionPathObserver | `Phase2PositionPathObserver`, dry-run, XAUUSD; `position_path_log_YYYYMMDD.csv` and summary | `C:\MT5PortablePositionPathObserver\MQL5\Files` |
| ProspectiveCollector | `XauProspectiveTelemetryCollector`, dry-run, XAUUSD ticks/book/transactions/heartbeat; feeds Python R1 shadow | `C:\MT5PortableProspectiveCollector\MQL5\Files` |
| RepairLane | Five paused/dry-run A3 charts, paused fill collector, plus active demo R1 forward chart `chart08`, magic `934100`, max `0.01` lot | `C:\MT5PortableRepairLane\MQL5\Files` |
| ShadowFixObservers | 14 dry-run `Phase2ShadowFixObserver` charts over EURUSD/USDJPY/XAUUSD | `C:\MT5PortableShadowFixObservers\MQL5\Files` |
| SpreadLogger | Startup `PassiveSpreadLogger_XAUUSD`; startup config has `AllowLiveTrading=0`; daily spread CSV | `C:\MT5PortableSpreadLogger\MQL5\Files` |
| Tier1BestEA | A2 broker-action demo executor `920101`, active daily guardian, equity shadow guardian, one disabled extra executor | `C:\MT5PortableTier1BestEA\MQL5\Files` |
| Tier1PathObserver | `Phase2PositionPathObserver`, dry-run, XAUUSD; A2 path logs and summary | `C:\MT5PortableTier1PathObserver\MQL5\Files` |
| TrendGuardedFixObservers | 14 dry-run `Phase2TrendGuardedFixObserver` charts over EURUSD/GBPUSD/XAUUSD | `C:\MT5PortableTrendGuardedFixObservers\MQL5\Files` |
| StandardA1 | A1 broker-action demo executor `920101`, active daily guardian, equity shadow guardian, four demo-enabled XAU momentum charts, one disabled extra executor | `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files` |

Restoration must preserve this factual runtime without changing EA inputs, lot
sizes, kill switches, guardians, or account assignments. Reopening an existing
demo runtime is not authorization to promote any new research strategy.

### Profile and startup-config fingerprints

Profile hashes are SHA-256 over sorted `chart*.chr` names and hashes. MT5 may save
cosmetic chart state during shutdown, so a mismatch is an audit trigger, not by
itself proof of strategy drift. Compare expert names and inputs before acting.

| Terminal | Charts | Profile SHA-256 | Startup config SHA-256 |
|---|---:|---|---|
| GoldMission | 25 | `c49a9f3882efe8cc2ef6c68433453097aa02a5baaff221a167cf55e6589f6cb7` | `c75c90fd95ce4b4868661269d2c5ac289c2b477791af9612ff4412aeb1e4e3bc` |
| PositionPathObserver | 2 | `50647891dffbe6ac8c47b156de9cb02d106811600a27da4e4a02d42c28fb8108` | `5029c6f7c506e85797971d4de7199802c716d5410a7ee39dcd3eb2f23c018b10` |
| ProspectiveCollector | 2 | `35f8f2a81c540a305fd5456f24e6be17058c5f06d0d07f3513606b0bf876df8a` | `4a2dc23c1b42ba273880894c9026af9a35cab7b72d436f7814a92e66bf4dce6d` |
| RepairLane | 8 | `941896193f13b40faa53a143d3f97f1c10c98ddcbbaa2617a4934082202aa726` | N/A |
| ShadowFixObservers | 14 | `a37a13d57e30793befffad3d373f94a405119bfe9e2422e93f249233f5f42a55` | N/A |
| SpreadLogger | 16 | `584c5c9a1810604903981bc2aa8826d92a2111a01c94ae7cce9a5ea6edc3c26e` | `6851a1886ddf755256d7bd515dc14a67fbe33cc606e83594867260268c4790e4` |
| Tier1BestEA | 4 | `63b8456050e3f4f8a1ff0f92beb0506924485b6946fe0361bf32bd409ffac483` | N/A |
| Tier1PathObserver | 2 | `60d7ec632c3d59b87864e7d88b2e8fcf370b436968631904de6d4d9b61887788` | `4632cbdac371acd05749fb44f66cc3e64f4b3e9e4e76aee923733ce388276a2c` |
| TrendGuardedFixObservers | 14 | `f5700645db944be3287ffcc69639aea7dab632b89183140aacd219ec481b7ae9` | N/A |
| StandardA1 | 32 | `0230a1b1c474135573f947bb612cc72365d7ecccf6788cbb54259f8cc6bd93bb` | N/A |

### Companion Python shadow process

MT5 is not the complete runtime. One read-only Python observer is running and must
be restored after `ProspectiveCollector` is connected:

```powershell
$repo = 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system'
$py = "$repo\xau-usd\xauusd-phase0\.venv\Scripts\python.exe"
Start-Process -FilePath $py `
  -ArgumentList 'xau-usd/xauusd-phase1/scripts/run_xau_specialist_shadow.py' `
  -WorkingDirectory $repo `
  -WindowStyle Hidden
```

- Script: `xau-usd/xauusd-phase1/scripts/run_xau_specialist_shadow.py`
- Terminal: `C:\MT5PortableProspectiveCollector\terminal64.exe`
- Runtime: `C:\MT5PortableProspectiveCollector\MQL5\Files\specialist_shadow_v1`
- Poll interval: 60 seconds.
- Specialist: frozen read-only `R1_UPTREND_LONG_V1`.
- Trade permission, broker action, and Python execution flags are all false.
- Pre-restart process pair: PIDs `16940` and `20672`, both started
  `2026-07-17T17:59:52+04:00`. PIDs are not reusable after restart.
- Pre-restart status is `FAILED_CLOSED`, not active, because the weekend history
  check found latest completed H4 `2026-07-18T00:00:00Z` while expecting
  `2026-07-19T00:00:00Z`. This failure existed before restart. Do not blame the
  restart; keep it fail-closed and reassess after Monday market history advances.

### Restore procedure Codex must perform after reboot

1. Read this entire latest section and inspect `git status`; do not reset, clean,
   delete, or overwrite the existing dirty/untracked research worktree.
2. Enumerate running `terminal64.exe` processes with executable paths. Launch only
   missing roots using the exact relaunch matrix. Open MT5 terminals visibly and
   one at a time, allowing each to load its saved `Default` profile.
3. Recommended launch order: GoldMission, SpreadLogger, StandardA1, Tier1BestEA,
   RepairLane, PositionPathObserver, Tier1PathObserver, ShadowFixObservers,
   TrendGuardedFixObservers, ProspectiveCollector.
4. Wait for each terminal to show the expected login/server. Verify exactly one
   process per executable root and confirm the expected chart count/expert inputs.
5. Read account info, positions, and orders through the local MT5 API. Compare with
   the pre-restart snapshot, but never close a position or change an order merely
   because the snapshot differs.
6. Check that primary log files resume modification when ticks/heartbeats are
   expected. Weekend zero-byte daily tick/book/transaction files are not by
   themselves a failure.
7. Start the Python shadow process only if no existing
   `run_xau_specialist_shadow.py` process is present. Keep it hidden and read-only.
8. Rerun read-only reconciliation and heartbeat checks using the current date:

```powershell
$repo = 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system'
$py = 'C:\Users\ZHAO ZHU INFORMATION\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$date = Get-Date -Format 'yyyy_MM_dd'
Set-Location $repo
& $py xau-usd\xauusd-phase1\scripts\generate_runtime_authorization_reconciliation.py --phase1-root xau-usd\xauusd-phase1 --evidence-date $date
& $py xau-usd\xauusd-phase1\scripts\generate_a1_a2_920101_supplemental_verification.py
& $py xau-usd\xauusd-phase1\scripts\generate_observer_heartbeat_report.py
& $py xau-usd\xauusd-phase1\scripts\verify_status_dashboard_freshness.py
```

9. The pre-existing reconciliation status was `FAIL_CURRENT_RUNTIME_DRIFT`. Compare
   the post-restart inventory with the July 15 snapshot and this section before
   deciding whether any difference is restart-caused.
10. Report which terminals/processes restored, expected accounts, chart/EA parity,
    active/stale logs, Python shadow status, and any mismatch. Do not change runtime
    behavior during this verification.

### Repository/worktree restart facts

- Branch: `codex/xau-independent-specialists-v1`.
- HEAD and pushed origin: `40d4f1c74dbb7932d5121090e30320ba997286b4`.
- The worktree intentionally contains modified runtime reports and many untracked
  research packages. These are pre-existing work and must not be reverted or
  removed during restore.
- `agent.md` itself contains the prior uncommitted July 15 restart handoff plus this
  July 19 supersession. Commit only this file when preserving the handoff; do not
  stage unrelated runtime outputs or research directories.
