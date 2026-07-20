# A1 XAUUSD Authoritative Handoff

Updated: `2026-07-20`

## Repository authority

- Base commit: `006824cde421ea61a0bcdb074804f9ccf95c17a9`
- Current operational branch: `codex/xau-independent-specialists-v1`
- Latest pushed research implementation checkpoint before this handoff update: `41367ca7`
- Scope: A1 XAUUSD repository research, exact-MT5 Strategy Tester evidence, offline analysis, and shadow-only preparation.
- This file replaces the prior oversized handoff. If an older statement conflicts with the documents below, the documents below control.

## Governing documents

1. [Master direction](xau-usd/xauusd-phase1/docs/A1_XAU_PROFITABLE_SYSTEM_MASTER_DIRECTION_2026_07_10.md)
2. [Current research freeze](xau-usd/xauusd-phase1/docs/A1_XAU_CURRENT_RESEARCH_FREEZE_2026_07_10.md)
3. [Router entry/hold-path audit preregistration](xau-usd/xauusd-phase1/docs/A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_PREREG_2026_07_10.md)
4. [Independent-specialist primary direction](xau-usd/xauusd-phase1/docs/A1_XAU_INDEPENDENT_SPECIALIST_PRIMARY_DIRECTION_2026_07_12.md)

Read all four before changing code or generating evidence.

## Latest frequency-milestone supersession - 2026-07-20

This section supersedes older statements in this handoff that say the first
frequency milestone or whole-account historical floating-equity audit is still
unavailable.

- V59 is the corrected broker-expressible historical portfolio. It preserves the
  exact frozen V57 add-on policy while replacing legacy FIFO R1 attribution with
  native MT5 position joins and rejecting all transition rows below the broker's
  0.01-lot minimum.
- Required-window combined frequency remains above one trade per weekday:
  `1.142` in development-2, `1.690` in confirmation, and `1.395` in the final
  year.
- Final-year economics are `364` trades, USD `2,537.35` net, PF `1.976`, USD
  `152.59` closed drawdown, 83.3% positive months, and USD `1,143.73` after
  removing the five largest winners.
- V60 reconstructed all `2,194/2,194` accepted trades from native-position or
  raw-tick prices and evaluated `1,172,191` bid/ask M5 bars. Conservative
  whole-account floating drawdown is USD `329.64`, or USD `412.06` with the
  frozen 25% capital buffer. Under an extra USD `0.30` charge on every R1 trade,
  it is USD `335.34`, or USD `419.18` buffered. Both pass the USD `449.77` hard
  limit.
- Exact raw ticks independently confirm the identified episode at USD `328.77`
  base and USD `334.47` under fee stress.
- Historical milestone one is therefore achieved. It is an exposed historical
  research result, not demo/live authority. MT5 portfolio parity and sealed
  prospective shadow evidence remain mandatory.

Do not weaken or retune V59/V60. The next research phase may target two trades per
weekday as an additive, separately preregistered expansion after this checkpoint is
committed and pushed.

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

Frozen uncapped diagnostic metrics: `678` trades; `51.03%` win rate; `2.6082` realized W/L; `2.7182` profit factor; `+$9,640.05` net; `+$9,436.65` stress net at `-$0.30/ticket`; `+$764.92` recent-three-month net; `$889.69` maximum closed drawdown; `26` positive months; approximately `21.28%` active weekdays. The `$889.69` curve is retained for audit history only and is not a deployable portfolio result.

Current drawdown status: V43 attributes the `$889.69` episode to R1 position
stacking. V50 replaces the two-position research policy with a prospective
maximum of one open R1 box position and one new R1 box entry per UTC day. The
one-year closed drawdown falls to `$106.71`; exact ten-year stress floating
drawdown is `$335.58`, or `11.19%` of the reference `$2,998.45` equity and
`13.99%` after the frozen 25% buffer. The R1 lane therefore fits its 15% gate at
0.01 lot, but whole-account historical floating drawdown is still unavailable.
Execution remains fail-closed pending sealed shared-account forward evidence.

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

## Frequency Expansion Checkpoint - 2026-07-19

This checkpoint supersedes the earlier one-to-two-trades-per-weekday research target
in this file. The current owner target is **three to four executed XAUUSD trades per
weekday on average**, including zero-trade weekdays, without removing or weakening
the frozen five-specialist Core. It remains a research target, not permission to
force trades or authorize execution.

### Frozen Core and corrected accounting

- Core ledger remains exactly 1,249 rows with SHA-256
  `fec25e1127b8bea261109010c7b0ad3eca275adf14e0ec52395e7efdfa86d372`.
- `audited-common-dollar-frontier-v6` found that every R1 Core row lacks a normalized
  R denominator. In the final 2025-07 through 2026-06 window, only 44 of 160 Core
  rows, or 27.5%, have normalized R. Prior mixed Core-plus-Expansion R averages and
  drawdowns silently omitted the other 116 rows and are not complete-account metrics.
- V6 therefore uses every row's fixed-lot USD P&L and applies Expansion risk weights
  explicitly. It verified exact Core ID, timestamp, direction, and USD P&L identity
  in all imported V3/V4 combined ledgers.
- Corrected final-window frontier:

| Policy | Trades/day | Expansion USD | Expansion PF | Combined USD | Combined PF | Closed DD USD |
|---|---:|---:|---:|---:|---:|---:|
| Core only | 0.613 | 0.00 | n/a | 4,508.78 | 3.492 | 889.69 |
| Core + V3 trend only | 1.391 | -1.34 | 0.999 | 4,507.45 | 2.489 | 860.76 |
| Core + all V3 | 3.801 | -1,170.08 | 0.762 | 3,338.71 | 1.496 | 950.43 |
| Core + V4 diagnostic | 1.425 | -163.90 | 0.866 | 4,344.88 | 2.432 | 893.69 |

Decision: `EDGE_PRESERVING_FREQUENCY_TARGET_NOT_ACHIEVED`. The high-frequency
policies preserve Core rows mechanically but do not preserve marginal expectancy.

### Additional campaigns completed after the restart handoff

1. `walkforward-regime-expert-expansion-v4`: exactly 1,000 causal adaptive policies.
   Confirmation reached 3.188 combined trades/day with strong expectancy; final
   expansion fell to 0.812/day, PF 0.674, and -0.173 R/trade. Rejected.
2. `comex-short-horizon-expansion-v5`: 44,418 executable COMEX-plus-spot action
   labels and exactly 1,000 policies using only local free data. Diagnostic final
   result was 39 trades, PF 0.563, and -13.55 R. Rejected.
3. `pullback-swing-replication-v7`: the strongest interpretable 2019-2026 executable
   pattern was frozen before reverse-time replication. On 2016-2018 it produced 165
   trades, PF 0.751, -USD 108.44, and both directions were negative. Rejected with
   no same-version tuning.
4. `interpretable-family-replication-v8`: family-wide executable screen and
   Benjamini-Hochberg correction. Only two unique rules passed all four forward
   development blocks; neither passed reverse-period economics and there were zero
   FDR survivors. Rejected.
5. A causal fixed-lot-dollar router diagnostic tested quarterly HGB dollar-return
   regressors and a win-probability classifier. Several variants produced useful
   frequency and PF above 1.3 before 2025-07, but every tested variant failed in the
   final year; the best final PF was 0.879 and higher-frequency variants were near
   PF 0.72-0.88. This rules out normalized-R target mismatch as the primary blocker.

### Information boundary and next work

- More executed trades are not required to train an ML ranker. The local research
  set already contains 69,235 spot candidate-action labels and 44,418 COMEX
  candidate-action labels, including rejected/no-trade counterfactual outcomes.
- Do not retune the exhausted breakout/retest/action pool, lower score thresholds,
  count multiple action labels as trades, split one economic signal into several
  tickets, or force a daily quota. Those operations increase a counter, not edge.
- Preserve the Core unchanged. Admit a new sleeve only when its standalone marginal
  P&L is positive in independent evidence, its addition does not worsen account risk
  beyond the locked budget, and it contributes genuinely independent entry events.
- The defensible route to three-to-four executed trades/day now requires materially
  new information or a broader tradable opportunity set: zero-cost primary depth,
  causal options/skew data, synchronized executable multi-broker quotes, or owner
  approval to broaden beyond one XAUUSD instrument. Existing spot bars, existing
  COMEX M5/trade summaries, and the current candidate mechanics have been tested
  through distinct deterministic and ML routes and do not support the target.
- If XAUUSD-only remains mandatory and no new information source becomes available,
  the evidence-supported frequency ceiling is lower than three trades/day. Do not
  conceal this by weakening gates.

All new V4-V8 work remains research-only. No Python prediction, EA consumption,
demo, live, paid-data, broker action, runtime input, lot-size, guardian, account, or
terminal change was authorized or made by these campaigns.

### Repository/worktree restart facts

- Branch: `codex/xau-independent-specialists-v1`.
- HEAD and pushed origin: `40d4f1c74dbb7932d5121090e30320ba997286b4`.
- The worktree intentionally contains modified runtime reports and many untracked
  research packages. These are pre-existing work and must not be reverted or
  removed during restore.
- `agent.md` itself contains the prior uncommitted July 15 restart handoff plus this
  July 19 supersession. Commit only this file when preserving the handoff; do not
  stage unrelated runtime outputs or research directories.

## Frequency Generalization Reset - 2026-07-19

This section supersedes the V8-era next-work language immediately above. The
owner target remains **three to four combined executed XAUUSD trades per weekday
on average**, including zero-trade weekdays, without changing the frozen Core.
The target has been solved mechanically but has **not** been solved economically
or authorized for execution.

### V7-V11 causal frequency-control evidence

1. `adaptive-frequency-credit-controller-v7` tested 240 locked causal credit
   policies. None passed validation; the best reached only 2.714 combined trades
   per weekday. Decision: `ADAPTIVE_FREQUENCY_CREDIT_V7_REJECTED_AT_VALIDATION`.
2. `rolling-frequency-ceiling-controller-v8` tested 480 locked rolling-window
   policies. None passed validation; the best reached 2.994/day and exceeded the
   stress drawdown gate. Decision:
   `ROLLING_FREQUENCY_CEILING_V8_REJECTED_AT_VALIDATION`.
3. `periodic-frequency-budget-controller-v9` tested 480 natural-period policies.
   None passed validation; repeated reset deficits limited the best result to
   2.988/day. Decision: `PERIODIC_FREQUENCY_BUDGET_V9_REJECTED_AT_VALIDATION`.
4. `startup-reserve-frequency-budget-v10` tested 600 half-year reserve policies.
   None passed validation; changing the startup reserve did not remove recurring
   reset deficits. Decision:
   `STARTUP_RESERVE_FREQUENCY_BUDGET_V10_REJECTED_AT_VALIDATION`.
5. `balanced-periodic-frequency-budget-v11` tested 520 locked rate/reserve pairs.
   Nineteen passed validation and advanced unchanged. All 19 failed confirmation,
   but they did hold confirmation frequency near 3.95-4.00/day with venue PF near
   1.88-1.92 and stress PF near 1.38-1.40. The universal blocker was stress
   drawdown near 114R. Attribution showed the mandatory V4 base alone had 670
   trades, PF 1.440, +169.97R, and 97.94R drawdown; therefore the 75R gate was
   impossible while that base remained mandatory. Decision:
   `BALANCED_PERIODIC_FREQUENCY_BUDGET_V11_REJECTED_AT_CONFIRMATION`.

These campaigns show that a quota or rate controller cannot create edge. They
also provide reusable causal frequency-ceiling infrastructure.

### V12 result: frequency achieved, final economics failed

`causal-expansion-health-circuit-v12` made the expansion base risk-controlled
while preserving every Core row. It tested exactly 912 locked policies. There
were 304 validation passers and 76 confirmation passers. One unchanged policy,
`EEP0028__PH__R325__B75__H30__C40__SA`, opened the single sealed final window.

| Stage | Combined trades/day | Expansion venue PF | Expansion stress PF | Stress DD R | Gate |
|---|---:|---:|---:|---:|---|
| Validation | 3.006 | 1.861 | 1.317 | 86.09 | PASS |
| Confirmation | 3.751 | 2.449 | 1.859 | 38.34 | PASS |
| Final, 2025-07-01 to 2026-07-01 | 3.471 | 0.869 | 0.763 | 144.52 | FAIL |

- Core identity remained exact: 1,249 rows and SHA-256
  `fec25e1127b8bea261109010c7b0ad3eca275adf14e0ec52395e7efdfa86d372`.
- The final expansion had 746 trades, venue net -67.14R and stress net -128.45R.
- The base sleeve was independently negative: 556 trades, venue PF 0.885 and
  stress PF 0.798.
- The add-on sleeve was independently negative: 190 trades, venue PF 0.821 and
  stress PF 0.656.
- Final positive rolling six-month share was zero. The drawdown covered almost
  the full final year, so this was broad family failure rather than one isolated
  session or month.
- Core itself remained profitable, but the expansion reduced its common-dollar
  PF ratio to 0.905 venue and 0.898 stress. Edge preservation therefore failed.
- Decision: `CAUSAL_EXPANSION_HEALTH_CIRCUIT_V12_REJECTED_AT_FINAL`.
- Result SHA-256:
  `1262fedfffd95602b400e68f9ab3c697a8a2bc9bf79538d5e81cd6dde66978ed`.
- Manifest SHA-256:
  `0ee30a7d3f33806a5825b67bbb11c809c55a5a988e8dd71b1f8c47719055dcae`.

The final window is now exposed development evidence. It may be used to explain
or reject a future design, but it can never again authorize a tuned version.

### V13 orthogonal research reset

`orthogonal-frequency-program-v13` is the authoritative next-research contract.
It was locked before the next market week and does not authorize execution.

- All data through 2026-07-19 is development evidence.
- Forward-only shadow evidence starts at 2026-07-20 00:00 UTC.
- Core filtering and resizing are forbidden.
- `BREAK_AND_RUN`, `DOWNSIDE_IMPULSE_RETEST`, and
  `OPENING_RANGE_REVERSAL` are retired from same-family optimization. Their
  labels remain useful negative evidence.
- Six independent research lanes are registered: auction displacement/reclaim,
  anchored-flow reversion, multi-scale continuation, independent compression
  release, cross-venue dislocation, and event aftermath.
- Historical work advances through an additive frequency ladder. No sleeve is
  weakened to raise frequency, no daily floor is allowed, and zero-trade days
  remain valid.
- The first ML role remains candidate ranking, calibration, routing, or veto for
  Satellite candidates. It cannot generate entries or suppress Core trades.
- Historical passage nominates only a shadow candidate. An unchanged version
  still needs post-freeze forward evidence and exact MT5 reproduction.
- Contract tests: 3 passed. Ruff: passed.
- Config SHA-256:
  `107bccc71d16503ec21c80ccc31dcc68ba1d06ffc0fe908f41e9360b167fb11e`.
- Preregistration SHA-256:
  `9e03dcb51da9507d4b9850e7e549282febd02d03fa57c2a0a94e520b44867cd6`.

### Restart instruction

Do not resume V4-V12 threshold, quota, cooldown, or same-family ranker tuning.
Resume from V13. Preserve Core, build distinct event clocks, reject new sleeves
quickly on historical and cross-feed evidence, and begin collecting the locked
post-2026-07-20 forward shadow stream. No runtime, terminal, account, guardian,
lot-size, EA, demo, or live setting was changed by V7-V13.

## V14-V17 Orthogonal Research Results - 2026-07-19

Four additional preregistered campaigns were completed without changing the
frozen Core or any trading runtime.

1. `trend-passive-pullback-campaign-v14` tested exactly 1,000 locked passive
   trend-entry policies. None passed the V13 admission gates. The family is
   rejected for same-version tuning.
2. `trend-failure-transition-campaign-v15` tested exactly 1,000 locked trend
   failure and transition policies. None passed. Result SHA-256:
   `a53b0edc97a72e243f41dca1fa728430518a2bd242c38e06a757a60ef2fdf9e9`.
3. `causal-crossvenue-ranker-v16` generated 56,124 independent PAXG tail-entry
   events and 110,584 side-correct XAU action labels. Ten causal quarterly
   rankers and exactly 1,000 locked policies were evaluated across four yearly
   gates. Although 119 policies maintained three-to-four trades/day in every
   yearly block, no policy was profitable: the best frequency-valid stress PF
   was 0.755 and the best venue PF was 0.800. Decision:
   `NO_V16_HISTORICAL_ADMISSION_SURVIVOR`. Result SHA-256:
   `c4c13b2a1cf17621092c516163f3313547a2a56b70b8273d23e66d296811f579`.
4. `causal-crossvenue-reversion-v17` was locked as the exact opposite-direction
   mirror of V16 before outcomes were evaluated. It also tested exactly 1,000
   policies and produced no survivor; its best frequency-valid stress PF was
   0.712. Decision: `NO_V17_HISTORICAL_ADMISSION_SURVIVOR`. Result SHA-256:
   `022b8062503b9a4001c4ebd4409a9223cb02897b5d478ed13edbc5c53dd51910`.

The matched V16/V17 audit found only USD 0.020 average directional information
per action versus USD 0.404 native round-trip drag before ticket cost and stress.
Both directions therefore fail for structural economic reasons. Retire the full
PAXG tail-event lane; do not rescue it with thresholds, ML variants, or passive
entry assumptions.

## Permanent Anti-Overfitting Protocol

The owner's anti-overfitting requirement is a hard constraint. Literal zero
overfitting cannot be proven statistically, so every claim must instead satisfy
all of these controls:

- Freeze each hypothesis, event clock, feature set, label, execution rule, cost
  model, split, metric, and pass/fail gate before reading its outcome.
- Use only causal features and purged chronological walk-forward evaluation.
  Random row splits and shuffled time-series validation are forbidden.
- A failed sealed stage permanently becomes development evidence. It cannot be
  reused as an untouched holdout or tuned until it passes.
- Count and disclose every attempted policy and family. Correct family-wide
  statistical claims for multiple testing; Holm is the default locked method.
- Do not select a strategy because one recent period, direction, regime, session,
  broker feed, or P&L chart looks attractive. Require positive marginal economics,
  yearly and rolling stability, cost stress, and cross-feed consistency.
- Never weaken a threshold, add a filter, alter a label, or change a time window
  after seeing holdout P&L under the same campaign version. A materially new idea
  needs a new preregistration and a later untouched evaluation period.
- Historical passage can nominate only a research-shadow candidate. Execution
  still requires unchanged post-2026-07-20 forward evidence and exact MT5
  reproduction. No historical result alone authorizes demo or live use.
- Preserve all rejected results as negative evidence. Do not silently discard
  failures, cherry-pick survivors, or report overlapping action labels as extra
  independent trades.

This protocol is non-negotiable. The 3-4 trades-per-weekday research target is
never a reason to relax a split, gate, cost assumption, correction, or forward
evidence requirement. A candidate that reaches the frequency target only after
outcome-informed repair is rejected, not promoted.

The next step is an edge-density audit of prior independent mechanisms, followed
by one preregistered high-displacement lane chosen from mechanism-level evidence,
not from a profitable-looking parameter combination.

## V18-V19 Edge-Density And Dependence Audits - 2026-07-19

`mechanism-edge-density-audit-v18` was locked before opening its common-horizon
outcomes. It compared 103,590 registered events from 12 sources and 31 families
on one exact Dukascopy Bid/Ask surface. Every prescribed direction and exact
mirror was measured at 30, 60, 180, 720, and 1,440 minutes with ticket, holding,
and 0.05-ATR stress costs. There were 101,376 aligned events and 673,214 valid
markout rows. Holm correction included every family, direction, and horizon.

- Contract SHA-256:
  `fa1eed9ba60f7be339c66f8c435050c32c06687f69c593f184c7f8f1e15a9ae8`.
- Decision: `V18_NO_BROAD_ECONOMIC_LANE`.
- No family passed the additive or full-frequency diagnostic at three of five
  fixed horizons.
- Break-and-run at 60/180 minutes and downside-retest at 60 minutes looked
  profitable in pooled history, but both collapsed in the 2025-2026 era. These
  are not candidates and remain retired.
- No family/direction/horizon with at least four eligible eras was profitable in
  every era. The apparent pooled edges were nonstationary.
- Result SHA-256:
  `77bc7a88e8434112ebb396a4d50e222859970aec684554fbfe818ca1f4a2bcfb`.

`episode-independence-audit-v19` then tested one outcome-blind dependence rule:
only the first signal in each contiguous same-family, same-direction M5 state was
retained. It had no cooldown grid, family exception, or outcome filter.

- Contract SHA-256:
  `979bf84196ffea856ff2055f7210cc3d6a0b2171d3f93fdeed1241989a280b81`.
- 101,165 recoverable V18 event IDs became 97,245 episode starts; only 3,920
  signals, or 3.9%, were removed. Repeated contiguous bars were not the main
  failure.
- V19 required stress PF >=1.05 in every eligible July-to-July era, at least four
  eras, positive total expectancy, cost coverage above one, and Holm-adjusted
  weekly p <=0.10.
- Decision: `V19_NO_STRICT_EPISODE_LANE`. There were zero additive and zero
  full-gap broad families.
- The strongest minimum-era PF was 1.116 for a sparse 12-hour compression clock,
  but it ran at only about 0.105 episodes/day and failed corrected significance.
  Compression is already represented in Core and this fragment is not additive
  qualification evidence.
- Result SHA-256:
  `df5bc75c01de62d088a0eb5228deedaf2dfb12054dafc2c51df4b4d183e6115d`.

The available spot, PAXG, COMEX summary, macro, auction, VWAP, compression, and
session event clocks have now failed both common-horizon economic feasibility and
strict episode-independence checks. Do not reopen them with new thresholds,
cooldowns, directions, horizons, or ML rankers. The remaining route requires a
genuinely new causal information set, a broader tradable opportunity set, or
untouched post-2026-07-20 forward evidence. Core remains byte-identical and no
runtime, account, terminal, EA, model, demo, live, or broker setting was changed.

## V20 Oracle Mixture Feasibility - 2026-07-19

`oracle-mixture-feasibility-v20` was locked before its outcome coefficients were
opened. It is an optimistic fractional linear-program upper bound, not a
strategy or backtest. One global set of nonnegative weights was required to add
2.387-3.387 satellite episodes per weekday and maintain positive stress P&L and
stress PF >=1.05 in every July-to-July era from 2016-2017 through 2025-2026.

- Contract SHA-256:
  `bdc4e74a59acbc013128a4df31cb4efb309582a7517c66f627164a1871984e91`.
- It evaluated 2,120 era coefficients from 31 families and 212
  family/horizon/direction sleeves.
- Mechanical frequency alone was feasible but lost USD 2.336 per weekday in
  its worst era and had minimum era PF 0.582.
- The optimistic family-constrained oracle was feasible only when globally
  hindsight-selected mirror directions were permitted. It projected 3.00-4.00
  combined trades/day, minimum era PF 1.05, and worst-era stress net USD 0.552
  per weekday. This is in-sample arithmetic and is not admissible evidence.
- The prescribed-direction, family-constrained economic problem was infeasible.
- Decision: `V20_ONLY_ORACLE_DIRECTION_RELAXATION_FEASIBLE`.
- Result SHA-256:
  `9089a9a5900110b1aefc84eec57b5be8812d7b68306b91e91895b449609e8a9d`.

Do not trade, admit, or hand-code the V20 oracle weights. They select direction
and horizon after seeing all ten years and would overfit by construction. The
only defensible continuation is a separately frozen causal direction-routing
diagnostic using information known at the event timestamp, followed by unchanged
post-2026-07-20 forward shadow evidence. A historical diagnostic can reject that
architecture but cannot authorize it. Core and all runtime settings remain
unchanged.

## V21 Causal Event Action Router - 2026-07-19

`causal-event-action-router-v21` tested the V20 direction-routing hypothesis once
under a locked, low-complexity protocol. It used exactly the completed M5 bar
before entry, timestamp-normalized sample weights, L2 logistic regression with
fixed `C=0.05`, one-hour stress labels, one action per entry timestamp, six purged
expanding walk-forward folds, and prior-year score-only frequency calibration.
There was no model, feature, threshold, or horizon grid.

- Contract SHA-256:
  `d10f8cb663837d7be64215f0552f9e3f2efc3db28f6e54ee9b467b3df9aff7b9`.
- All 190,598 action rows aligned to the exact completed prior M5 bar; feature
  coverage was 100% with a fixed five-minute lag.
- Test AUC remained above 0.50 in all six folds, ranging from 0.519 to 0.569.
- The first five test years were profitable, with stress PF from 1.305 to 1.689.
- The newest 2025-2026 fold failed decisively: 803 actions, 3.077/day, stress net
  -USD 1,283.62, PF 0.790, closed drawdown USD 1,565.11, and win rate 45.33%.
- Aggregate: 5,057 actions, 3.231/day, stress net USD 2,733.88, PF 1.196,
  closed drawdown USD 1,745.66, and 65.15% positive rolling six-month windows.
  It failed the locked PF 1.20, drawdown USD 1,733.37, rolling 70%, per-fold
  economics, frequency, and overlap gates.
- Selection was not genuinely diversified. In every fold, 93% or more of actions
  came from the already retired `SPOT_DOWNSIDE_IMPULSE_RETEST` and
  `SPOT_BREAK_AND_RUN` clocks. In 2025-2026 those two clocks accounted for every
  selected action and both lost money.
- Decision: `V21_HISTORICAL_ARCHITECTURE_DIAGNOSTIC_FAIL`.
- Result SHA-256:
  `169b39781cb567da459d267d7c4d508c74a74a08c74aa9542ab846860a23e64d`.

V21 is retired without rescue tuning. Do not add a family cap, shorten the
retraining interval, alter regularization, add a regime filter, or change the
threshold under V21: all would be responses to the exposed 2025-2026 result.
Those two high-volume clocks must not be reopened under another historical ML
wrapper. Any materially new architecture must preregister genuinely new causal
information and remains development-only until unchanged forward evidence exists.
No Python prediction, EA consumption, demo, live, runtime, terminal, account,
guardian, lot-size, or broker action was authorized or changed by V18-V21.

## V22-V23 Fresh Cross-Venue Evidence - 2026-07-19

This work used a new Capital millisecond quote stream and free Dukascopy ticks.
It did not change the frozen Core, any MT5 attachment, runtime input, account,
guardian, lot size, or execution authorization.

1. `capital-dukas-crossvenue-foundation-v22` failed closed before pairing because
   the first five Capital daily files did not contain tick fields. The failure is
   preserved; V22 was not edited after lock.
2. `capital-dukas-crossvenue-foundation-v22-1` corrected only the source start to
   2026-05-27. It produced 346,160 backward-only pairs from 356,159 unique Capital
   quotes across 28 active UTC dates, with 97.19% coverage. Paired artifact SHA-256:
   `6eefecfdaa569d3c6a7ea6a518506f1893a23ea6e06efef3814ba13896c5a4fb`.
   Contract SHA-256:
   `0190d0f8bb42848073e6cf3646743505980174f0fb7d8fed2dff6e0dd6770e7c`.
3. The timing audit proved the logger has no local millisecond receipt clock.
   `TimeCurrent` versus `TimeGMT` is not a stable latency measure. Same-timestamp
   or millisecond arbitrage claims are forbidden. Subsequent work used Dukascopy
   data at least 15 seconds old and the first strictly later Capital quote.
4. `capital-dukas-lagged-opportunity-audit-v22-2` opened no future P&L. At the
   strictest frozen threshold it still found 15 validation candidates/day at a
   15-second lag, 12.42/day at 20 seconds, and 10/day at 30 seconds. Candidate
   abundance therefore passed mechanically but failed its intended 2-4/day
   structure gate. Decision: `V22_2_OPPORTUNITY_STRUCTURE_FAIL`. Opportunity
   artifact SHA-256:
   `9bc1a8ee73a17844c78bbbb834e11bfe99fc29c324de181276f6f93b9ae64b35`.
5. V23 registered one economic hypothesis before outcomes: convergence toward the
   causal two-hour basis after a same-direction one-minute Dukascopy impulse, fixed
   five-minute hold, strict later Capital fills, real bid/ask, 0.05 adverse price
   slippage per side, and 0.15 stress slippage per side. There was no model,
   threshold grid, direction grid, or horizon grid. Contract SHA-256:
   `2a3f6d996bd85378d7461d6f6c444b49b717eb9fe7f300048b671390f4a898d3`.
6. Free July Dukascopy acquisition was attempted only after lock. Local and clean
   GitHub runners received official-source HTTP 503 responses. GitHub Actions runs
   `29697538248`, `29697607811`, and `29698092570` are transport-failure evidence;
   no paid source was used and no July economic outcome was opened.
7. July confirmation was not needed because V23 failed its preregistered
   development gate first:

| Safety lag | Trades/day | Trades | Base net USD | Base PF | Stress PF |
|---:|---:|---:|---:|---:|---:|
| 15 seconds | 16.091 | 354 | -54.50 | 0.918 | 0.821 |
| 20 seconds | 13.227 | 291 | -98.63 | 0.836 | 0.752 |
| 30 seconds | 11.227 | 247 | -171.25 | 0.704 | 0.637 |

The frozen development gate required positive net and PF at least 1.05. Both
primary checks failed. Decision:
`V23_DEVELOPMENT_GATE_FAIL_NO_CONFIRMATION_REQUIRED`. Audit SHA-256:
`e6b5b0e1f3cdc3fe653e784833f4676faf293641107871221bb245d9b8e5b4df`.
The reporting package is
`xau-usd/xauusd-fast-research/capital-dukas-lagged-economic-test-v23-postlock-audit/`.

V23 is terminal. Do not reverse it, alter its hold, costs, lag, threshold,
session, direction, or filters after seeing this result. A successor must use a
materially new mechanism, receive a new preregistration, count as another attempt,
and require untouched post-2026-07-20 evidence.

### Next outcome-independent information lane

The `ProspectiveCollector` millisecond Capital demo tick file for 2026-07-17 has
159,949 rows from 12:49:00 to 20:58:56 UTC, 158,127 unique millisecond timestamps,
a 123 ms median inter-update gap, and a 1,093.53 ms 99th-percentile gap. This can
support a quote-update microstructure candidate stream after deterministic
deduplication. The corresponding book files contain only headers, so no depth or
order-book imbalance claim is currently supportable.

Past telemetry may be used only for outcome-blind schema checks, causal feature
scaling, and candidate-frequency calibration. Freeze any microstructure event
definition before reading its future returns. All outcomes from 2026-07-20 onward
must remain untouched forward evidence, and historical passage still cannot
authorize Python prediction, EA consumption, demo, live, or broker action.

## V24.1 Forward Quote-Microburst Freeze - 2026-07-19

`capital-quote-microburst-forward-v24` registered one new millisecond Capital
quote hypothesis before any forward source file existed. It uses a five-second
causal quote-update imbalance and displacement gate, the first false-to-true event
in each fixed four-hour UTC block, one continuation direction, one 120-second
horizon, real bid/ask entry and exit, and fixed base/stress slippage. It has no
parameter, session, direction, horizon, model, or cost grid.

- Frozen V24 contract SHA-256:
  `046a3015486c212e0e2e8f832a2e53413f77dc2d364b6f2e08ca6901745ec640`.
- Outcome-blind calibration read 158,127 unique millisecond quotes from the fixed
  2026-07-17 file. It produced three candidates in three observed four-hour blocks,
  two long and one short. It calculated no post-event return, P&L, or win rate.
- The first empty-forward dry run then raised `KeyError: tick_time_msc` because an
  empty candidate frame had no declared columns. No 2026-07-20-or-later file,
  validation outcome, confirmation outcome, or P&L existed. V24 is preserved as
  `V24_IMPLEMENTATION_FAIL_BEFORE_FORWARD_DATA`; its locked files were not edited.

`capital-quote-microburst-forward-v24-1` is the only permitted structural
successor. Its sole change is a stable schema for empty candidate frames plus a
regression test. Automated comparison confirmed that all source rules, causal
features, thresholds, block selection, direction, horizon, costs, data-quality
rules, stage lengths, economic gates, and research permissions are identical to
V24.

- V24.1 contract SHA-256:
  `84a1d60b025be15f9cedf3c0fc6688ac30c9c06075ab415efc155996df4858c0`.
- Calibration manifest SHA-256:
  `2f4c4fabe390818b02efeb50812183be8b1d0f08d087ead464b42a063ccc730e`.
- Calibration audit SHA-256:
  `0d4d1031b1b96edc9687fecfe261c7ebac0b2dd745acd9a968f9f3cac2ae9766`.
- Calibration decision:
  `V24_1_CALIBRATION_STRUCTURE_PASS_FORWARD_COLLECTION_REQUIRED`.
- Forward runner decision: `V24_1_CONTINUE_SEALED_FORWARD_COLLECTION` with
  `0/20` eligible validation weekdays and `economic_outcomes_opened=false`.
- Validation and confirmation audits and trade files are absent. Confirmation
  cannot open in the same invocation that first opens validation.
- Tests: 7 passed. Ruff: passed.

The sequential forward protocol is now immutable:

1. Existing telemetry continues from 2026-07-20 without a new attachment or
   runtime change.
2. A weekday counts only with at least 100,000 unique millisecond quotes, no more
   than 5% duplicate milliseconds, coverage from no later than 02:00 UTC through
   at least 22:00 UTC, and 99th-percentile interquote gap no more than five seconds.
3. Before 20 full weekdays, the runner may disclose inventory and candidate counts
   only. It must not simulate a trade or expose an economic outcome.
4. At 20 full weekdays, validation opens once. Failure is terminal. Passing only
   allows continued sealed collection.
5. Confirmation uses the next 20 full weekdays and may open only on a later run
   after immutable passing validation exists.
6. Even dual passage nominates research shadow only. It does not authorize a model,
   Python prediction, EA consumption, demo, live, or broker action.

Read-only runtime verification found the existing ProspectiveCollector terminal
running from `C:\MT5PortableProspectiveCollector\terminal64.exe` as PID `20892`.
Its heartbeat advanced through 2026-07-19 18:37:57 UTC on account `1033669` /
`Capital.ComMena-Demo`. Weekend tick files contain headers only, as expected while
XAUUSD is closed. No process, chart, EA input, terminal, account, or permission was
changed.

## V25 Dukascopy Microburst Replication Freeze - 2026-07-19

`dukascopy-microburst-replication-v25` is an exact cross-feed replication of the
locked V24.1 rule. It imports the V24.1 candidate, execution-label, cost, and gate
implementation by SHA-256 and refuses any difference in the source-quality,
feature, episode, simulation, or gate dictionaries. V25 has one hypothesis and
no threshold, session, direction, horizon, feature, cost, or model grid.

- Free Dukascopy source window: 2016-07-01 through 2026-06-30.
- Frozen coverage: 120/120 valid months, 87,648 hourly files, 518,307,832 ticks,
  and 11,375,007,955 raw JSON bytes.
- Source manifest SHA-256:
  `76eab4348d9a7c16afad51e0f4c9fbd17f8086b966633de03a2117e61a459c3b`.
- V25 contract SHA-256:
  `1d02d71e2b124d98cb126a02d7b00a581880165a92d6ffdb45ef102f352402cc`.
- At lock, `candidate_generation_performed_before_lock=false`,
  `dukascopy_microburst_pnl_opened_before_lock=false`, and no stage audit existed.
- Tests: 8 passed. Ruff: passed. Contract verification: passed.

Evidence opens sequentially and at most one stage per invocation:

1. `EARLY_REPLICATION`: 2016-07-01 to 2020-07-01.
2. `MIDDLE_VALIDATION`: 2020-07-01 to 2023-07-01.
3. `RECENT_FINAL_HOLDOUT`: 2023-07-01 to 2026-07-01.

Each stage uses the unchanged V24.1 complete-day and economic gates. Candidate
labels are purged at stage boundaries by the full 124-second maximum entry,
holding, and exit-delay path. A failed stage is terminal and later stages remain
sealed; no same-version repair is permitted.

The Dukascopy archive was used by earlier, different research, so V25 is
mechanism-level cross-feed replication rather than an untouched final holdout.
Untouched Capital evidence from 2026-07-20 onward remains mandatory. V25 passage
alone cannot authorize model training, Python predictions, EA consumption, demo,
live, paid data, or broker action.

### V25 Early Replication Result

The precommitted `EARLY_REPLICATION` stage opened once after contract commit
`a00104fe` and failed terminally. The runner verified 35,064 hourly files and
169,163,189 raw tick rows from 2016-07-01 through 2020-06-30 before calculating
the unchanged V24.1 labels and gates.

- Decision: `V25_EARLY_REPLICATION_FAIL_TERMINAL`.
- Audit SHA-256:
  `662b616363fe730badb405310208be35f15df74eee5fd324743918050b51d86f`.
- Eligible full weekdays: 417.
- All-source candidates: 555; candidates on eligible days: 308.
- Executable trades: 291, or 0.6978 per eligible weekday.
- Direction balance: 137 long / 154 short.
- Base net: -USD 137.124; base PF: 0.2777; win rate: 24.74%.
- Stress net: -USD 195.324; stress PF: 0.1716.
- Closed-trade drawdown: USD 137.124.
- First-half PF: 0.2241; second-half PF: 0.3012.
- Profitable-day share: 7.19%; 90% bootstrap lower bound: -USD 0.391/day.

Only executable-trade count, maximum frequency, and direction balance passed.
Every edge, minimum-frequency, stability, drawdown, recovery, and bootstrap gate
failed. Rerunning the locked runner reproduced the terminal decision without
opening another outcome. `MIDDLE_VALIDATION` and `RECENT_FINAL_HOLDOUT` remain
absent and sealed.

V25 must not be tuned, reversed, or reinterpreted as a viable specialist. It is
negative evidence that the exact Capital-calibrated microburst rule transfers to
historical Dukascopy quotes. V24.1 untouched Capital forward collection remains
unchanged, but V25 provides no training or execution authorization.

## V26 Forward Gap-Restart Freeze - 2026-07-19

`capital-gap-restart-forward-v26` registers one mechanically independent,
forward-only Capital quote hypothesis. It is not a historical backtest and no
economic outcome was opened during calibration. The event requires a 2,001-5,000
ms quote gap, observes only the first causal second after restart, requires at
least five nonzero midpoint updates, absolute signed-update imbalance at least
0.60, absolute displacement at least USD 0.30, agreeing signs, and spread no
greater than USD 0.35. It takes the first qualifying continuation event per fixed
four-hour block, with at most six per day and the unchanged V24.1 120-second
execution, quality, cost, and economic gates. The strict 2,001 ms lower boundary
makes the candidate clock disjoint from V24.1's maximum 2,000 ms continuity rule.

- The fixed 2026-07-17 source-only calibration found 391 eligible restart
  episodes, 13 raw candidates, and three block candidates in three observed
  blocks. The full file was loaded to enumerate events, but no post-candidate
  price was used to label or economically evaluate a candidate and no return,
  P&L, or win rate was calculated.
- Calibration candidate SHA-256:
  `f9b0ad64e1b8dd5f8885c7a4a5378e16f94424648c700f7ae7bc35b8807ab35b`.
- Calibration audit SHA-256:
  `210b2fe3ebcfb55a8c7816bf62bca8b5f52c99d61354bbdffbfeaf4bc2c35147`.
- V26 contract SHA-256:
  `4981f20bff17e36fc990816e433b9cb69b708a7f39dd1cc85b3a1f96db68f1ee`.
- At lock, no file at or after the 2026-07-20 forward boundary existed,
  `calibration_post_candidate_prices_used_for_label_or_outcome=false`,
  `calibration_pnl_calculated=false`, and `parameter_grid_allowed=false`.
- The empty-forward runner decision is
  `V26_CONTINUE_SEALED_FORWARD_COLLECTION` with `0/20` eligible validation
  weekdays and `economic_outcomes_opened=false`.
- Tests: 9 passed. Ruff: passed. Contract verification: passed.

V26 and V24.1 count as two forward hypotheses. V26 therefore adds a
locked one-sided circular moving-block-bootstrap p-value gate of at most 0.025,
using five-weekday blocks, 10,000 samples, and seed 2601, while retaining every
original V24.1 gate. This is the 0.05 family alpha divided across two hypotheses;
V24.1 must pass the same external admission recheck before either member can be
selected. Validation may open once after 20 complete eligible weekdays; failure
is terminal. A passing validation only permits sealed collection of the next 20
eligible weekdays for confirmation. Historical data must not be used to tune or
pre-screen V26, and even dual forward passage authorizes research shadow only,
not a model, Python prediction, EA consumption, demo, live, or broker action.

A pre-commit audit superseded provisional local lock
`1e500f9392c01c30996f56ef7da11088f1bd71495cc99aafd542ddcda2f12a08`
before any forward file or economic outcome existed. It corrected the false 0.05
Bonferroni claim, removed the exact 2,000 ms clock overlap, and made the physical
calibration-read boundary explicit. These were stricter outcome-blind governance
corrections, not same-version economic tuning.

## V27 Capital Forward Family Portfolio Freeze - 2026-07-20

`capital-forward-family-portfolio-v27` freezes the selection and combination of
V24.1 and V26 before either component has a validation audit or trade file. V27
does not create a signal. It is the family-level test of whether both independent
forward clocks can add enough positive marginal activity to the byte-identical
five-specialist Core without exceeding the locked risk budget.

- V27 contract SHA-256:
  `8f62bb6bf9bd7ff1d69c01cd79abb502e385a87aacf90f6a40cbcab6083f15a6`.
- At lock, all V24.1/V26 validation and confirmation audits and trade files were
  absent. Component and portfolio economics were both unopened.
- Frozen Core identity: 1,249 rows, SHA-256
  `fec25e1127b8bea261109010c7b0ad3eca275adf14e0ec52395e7efdfa86d372`.
- Frozen Core frequency reference: 160 trades over 261 weekdays, or
  0.6130268199233716/day, in the 2025-07-01 through 2026-06-30 realized-exit
  window.
- The Capital forward family now has three registered claims: V24.1, V26, and
  their fixed V27 portfolio. V27 therefore applies a 0.05 / 3 =
  0.016666666666666666 one-sided threshold to both components and the portfolio,
  using centered-null circular five-weekday block bootstraps with fixed seeds.
  This stricter external gate supersedes V26's earlier two-claim 0.025 threshold
  for family admission without modifying the locked V26 runner.
- Both components must pass their own immutable gates and the V27 external gate.
  If either fails, V27 fails terminally before portfolio economics are opened.
  Selecting only the winning lane is forbidden.
- The fixed router sorts by candidate millisecond with V24.1 then V26 tie
  priority, permits only one satellite position, and retains at most the first
  three selected satellite trades per UTC day. It never fills a quota.
- Satellite frequency must be 2.386973180076628 to 3.386973180076628/day, which
  projects the unchanged 0.6130268199233716/day Core reference into the 3-4/day
  owner target.
- Marginal base/stress net must be positive, base PF at least 1.20, stress PF at
  least 1.05, profitable days at least 50%, satellite closed drawdown no more
  than USD 100, and both half-period PFs at least 1.0. Both directions and both
  components must each contribute at least 20% of selected trades.
- The appended Core-plus-satellite curve must increase Core net, retain PF at
  least 2.0, and keep closed drawdown no greater than USD 1,000.
- Empty-stage decision: `V27_WAITING_FOR_COMPONENT_VALIDATION` with both component
  artifacts absent, `component_economic_outcomes_opened_by_v27=false`, and
  `portfolio_economic_outcomes_opened=false`.
- Tests: 6 passed. Ruff and Ruff format: passed. Contract verification: passed.

Validation and confirmation each require the same 20 complete weekdays as the
component contracts and open sequentially. Even dual V27 passage is not final
frequency proof because the total-frequency gate uses the frozen historical Core
rate. Same-period Core shadow signals, floating-equity overlap, margin, and exact
MT5 portfolio reproduction remain mandatory. No model training, Python
prediction, EA consumption, demo, live, runtime, account, or broker action is
authorized.

## Same-Period Core Shadow Preflight - 2026-07-20

The concrete remaining gap is same-period portfolio evidence, not missing price
history or a missing research framework. The profitable five-specialist Core has
historical evidence at approximately 0.613 trades per weekday. Earlier attempts
that reached approximately 3-4 trades per weekday did not retain positive stressed
expectancy. V24.1/V26 are locked forward satellite hypotheses, not proven edge.
The owner frequency target is therefore still open.

A read-only MetaTrader5 bridge query against the existing
`C:\MT5PortableProspectiveCollector\terminal64.exe` verified account `1033669`,
server `Capital.ComMena-Demo`, and a connected terminal without changing a chart,
EA, order, position, profile, or account setting. Available broker history from
2025-01-01 through the 2026-07-19 market open includes 108,837 M5 bars, 9,082 H1
bars, 2,463 H4 bars, and 482 D1 bars. This removes the Core indicator-warm-up
blocker.

The existing read-only R1 sidecar was then found `FAILED_CLOSED` because it
required the latest H4 decision timestamp to equal the wall-clock H4 boundary,
including during the weekend when no new gold bar exists. The source repair:

- accepts the latest actual completed H4 bar when it is not after the evaluation
  cutoff;
- separately rejects future M5 history and history more than 96 hours stale;
- records the evaluation cutoff and M5 history age; and
- skips the 42 MB prospective-tick scan when no candidate exists.

Eight focused tests and Ruff pass. An isolated read-only real-terminal cycle
completed in 1.7 seconds with `ACTIVE_READ_ONLY_SHADOW`, no candidate, decision
`ABSTAIN_D1_TREND`, 232,003 M5 rows, and a 49.74-hour weekend history age. It
performed no broker action. The already-running sidecar process still has the old
module loaded and was not restarted because no runtime-change instruction was
given; its persistent runtime status remains fail-closed until an authorized
restart.

Exact remaining same-period Core work:

1. Extend the frozen Capital adapter from R1 to the deterministic R2/R3 rules.
2. Reconstruct and freeze the R4 M5 microstructure fields from prospective bid/ask
   quotes; do not substitute guessed values.
3. Update and freeze the external macro/cross-asset inputs required by R5, whose
   dynamic router may use only component outcomes closed strictly before each
   candidate.
4. Run R1-R5 and V24.1/V26 over identical untouched forward dates on one shared
   timeline, reporting actual frequency, overlap, costs, floating equity,
   concurrent exposure, margin, and drawdown.
5. Admit nothing unless the locked validation and confirmation gates pass. More
   data, more attempted strategies, or an ML ranker cannot replace this proof.

### R1 Repair Activated And V28 R2/R3 Lock

The repaired R1 sidecar was intentionally restarted without changing the MT5
terminal or any chart, EA, order, position, account, or permission. It now reports
`ACTIVE_READ_ONLY_SHADOW` from the pushed v1.1 source, with decision
`ABSTAIN_D1_TREND`, no candidate, and all three authority flags false.

Source-identity inspection also corrected an earlier simplification: normalized
`R1_UPTREND` contains 145 `h4_d1_long_best_box2_atr80` trades and 413
`r1_h1_pullback_long_v1` trades. The current R1 sidecar covers the portability/box
rule only. Complete same-period R1 evidence therefore still requires an exact
pullback adapter; no total Core-frequency claim may omit it.

`capital-core-same-period-shadow-v28` is now the outcome-blind R2/R3 forward
candidate collector.

- Final contract SHA-256:
  `b197323782a289b7c59734c55ef97485a86d0eb5da0bfc229ea8025e56ded974`.
- Rule dependency SHA-256:
  `fa0fdf85c6d630c9c1306ecb1b5ac78c11c7db4e91a931b408dbbe1b13324e60`.
- Lock time: `2026-07-19T23:00:08.898187Z`, before any July 20 prospective
  tick file existed.
- Historical candidate parity: 658 expected and 658 observed; every source ID,
  composite, attempt, variant, regime, mechanic, UTC signal/entry instant,
  direction, stop, hold, parameter payload, and ATR value matched.
- Real-account pre-boundary dry run: 232,003 M5 rows, 19,310 feature rows, zero
  candidates, `WAITING_FORWARD_BOUNDARY`, and `economic_outcomes_opened=false`.
- Persistent hidden runner: parent PID 24200 with child PID 6500 at startup; its
  runtime authority remains read-only with no order surface.
- Tests: 3 passed. Ruff and Ruff format: passed. Re-running the lock command
  verifies the existing immutable payload and historical parity.

V28 records R2/R3 candidate facts only. It does not calculate outcome, return,
win rate, P/L, or an economic gate. R1 pullback, R4 Capital microstructure, R5
current macro/cross-asset state, shared floating equity, and the 20+20 completed
weekday decisions remain mandatory.

## V29 Exact R1 Pullback Forward Shadow - 2026-07-20

`capital-r1-pullback-forward-v29` closes the missing R1 pullback candidate-clock
coverage without changing the historical specialist's `SHADOW_ONLY` status. It
ports the exact MT5 `r1_pullback_long_v2_m15_session_09_15` signal, regime,
session, spread, cost, and stop guards into an outcome-blind Python collector.

The parity audit identified and corrected one important numerical assumption:
the bound MT5 `iATR` values are the simple average of the last 14 true ranges,
not Wilder smoothing. At the audit timestamp MT5 and the corrected Python path
both produce `4.036428571428603`; Wilder smoothing would produce
`3.750412711024045`.

- Final contract SHA-256:
  `80efb0907d2742e47f9e871f25cfacef485853f60f973145461b5655d4db43fb`.
- Rule dependency SHA-256:
  `5de2d9fb972f04cc90d458622fe9fe33d55cb4238d3857f3f9177c9e742d1456`.
- Lock time: `2026-07-19T23:50:35.097373Z`, before the
  `2026-07-20T00:00:00Z` forward boundary.
- Historical decision parity: 94,223 expected and observed.
- Raw-signal parity: 3,318 expected and observed, with exact timestamps,
  directions, reasons, guard actions, and guard reasons.
- Accepted-entry parity: 413 expected and observed.
- Break distance and cost ratio match the four-decimal MT5 logs; stop distance
  matches the two-decimal MT5 log precision. Every cost, spread, stop, session,
  and regime decision is exact.
- Guard counts match exactly: 2,265 session blocks, 254 chop blocks, 110
  compression blocks, 7 downtrend blocks, 234 shock blocks, 33 stop-ceiling
  blocks, 2 spread blocks, and 413 passes.
- Real ProspectiveCollector dry run on account `1033669` returned
  `WAITING_FORWARD_BOUNDARY`, latest decision `2026-07-19T23:30:00Z`, no raw
  signal, zero candidates, no opened economics, and all authority flags false.
- Each forward M15 decision freezes its first observed signal, spread, and guard
  state in an append-only decision ledger, so later polls cannot turn a
  bar-open spread block into a pass.
- Persistent hidden collector: parent PID `21480`, child PID `22960`; its first
  final-lock cycle advanced status at `2026-07-19T23:52:45.061396Z`, with zero
  candidates, zero frozen forward decisions before the boundary, and empty
  stderr.
- Online warm-ups are frozen at 30 M15 days, 120 H1 days, 400 H4 days, and 800
  D1 days. These exceed all explicit lookbacks and avoid repeatedly requesting
  eleven years of H1 history from the live terminal.
- Tests: 5 passed. Ruff and Ruff format: passed.

V29 writes append-only candidate facts only. It cannot place orders, calculate
outcomes or P/L, authorize model training or Python predictions, or promote the
underlying R1 pullback rule. MT5 remains replication evidence for this exact EA,
not the preferred research-quality feed. Prospective validation, confirmation,
shared-account economics, R4/R5 same-period coverage, and the 3-4 trades/day
frequency proof remain open.

### July 20 Forward Boundary Handoff

The untouched forward interval opened successfully. The prospective EA created
all four July 20 ledgers at `2026-07-20T00:00:03Z`; the first readable XAUUSD
tick is `2026-07-20T00:00:05.812Z`. Tick and heartbeat rows contain
`dry_run=true`, `trade_permission=false`, `broker_action_allowed=false`, and
`python_execution_authorized=false`.

- R1 box sidecar: `ACTIVE_READ_ONLY_SHADOW`, fresh M5 history through
  `2026-07-20T00:00:00Z`, decision `ABSTAIN_D1_TREND`, zero candidates.
- V28 R2/R3 sidecar: `ACTIVE_READ_ONLY_CANDIDATE_SHADOW`, 232,027 M5 rows,
  19,312 feature rows, zero candidates, no economics opened.
- V29 R1 pullback sidecar: `ACTIVE_READ_ONLY_CANDIDATE_SHADOW`; it froze the
  first forward decision at exactly `2026-07-20T00:00:00Z` as
  `NO_SIGNAL/no_m15_independent_candidate`, with one immutable decision row and
  zero candidates.
- Locked V24.1 evaluator: `V24_1_CONTINUE_SEALED_FORWARD_COLLECTION`, `0/20`
  complete eligible weekdays, no economics opened.
- Locked V26 evaluator: `V26_CONTINUE_SEALED_FORWARD_COLLECTION`, `0/20`
  complete eligible weekdays, no economics opened.

This proves collection started; it does not prove edge or frequency. The first
economic decision remains sealed until 20 complete eligible weekdays exist.

## V30 Capital Quote Exhaustion Reversal - 2026-07-20

`capital-quote-exhaustion-reversal-v30` tested a new real-tick mechanism on the
locked June Capital packet. A three-second one-sided quote impulse armed the
rule; at least three consecutive counter-updates and a USD 0.40 retracement
triggered a fade of the original impulse. Only the first trigger in each fixed
four-hour block was retained and each trade used a locked 120-second hold.

The July 17 calibration packet was used only to select a frequency-capable,
direction-balanced configuration. It exposed no P/L: 32 impulse arms produced
20 raw triggers and two selected candidates, one per eligible four-hour block.
The original contract SHA-256 is
`456b4ae5ddca695c2e5b37a79ab297c859d133b39e5197c4a78a80cf8a687d95`.

Two fail-closed interface corrections were separately preregistered before any
economic outcome was opened:

- timestamp adapter contract
  `3a209900f9e063263356084aa59ff3fd0b7d74c758b73f62452906eb7d2a79d1`;
  whole-second `time_utc` must equal the floor of authoritative `time_msc`;
- simulator metadata alias contract
  `a68b8e183d493734b6e563a89e02562f193397d98d0ddb023e8e434c3673a9ca`;
  it maps two metadata names without changing rows, signals, or fills.

The locked June development packet contains 6,367,635 raw rows, 6,297,928
unique millisecond rows, and ten eligible full weekdays. It produced 59
executable trades, or 5.9/full weekday, split 30 long and 29 short. Base net was
USD -19.99, base PF 0.7170959524, stress net USD -31.79, and stress PF
0.5906515581. Only 40% of days were profitable; first-half PF was 0.856 and
second-half PF was 0.490. The terminal decision is
`V30_DEVELOPMENT_FAIL_TERMINAL`. Audit SHA-256 is
`d9f60d5242b65a950ffe8224edd1b168073782c5036ca925ea17248433e09ad7` and
trade-ledger SHA-256 is
`108ba9977abd54b9440456e976dcd2d75e9938e3d9e12c8a69580407beddcf04`.

V30 may not be tuned, mirrored, re-timed, trained, or executed from the exposed
June outcomes.

## V31 Capital Quote Absorption Release - 2026-07-20

`capital-quote-absorption-release-v31` tested the opposite real-tick mechanism.
A completed trailing 30-second window required at least 100 nonzero updates,
absolute update imbalance no greater than 0.10, range no greater than USD 0.75,
maximum internal gap no greater than two seconds, and spread no greater than
USD 0.75. A later USD 0.75 release beyond the frozen range triggered
continuation, again limited to the first candidate per fixed four-hour block
with a 120-second hold.

The outcome-blind July 17 calibration found 297 absorption arms, 14 raw
releases, and two selected candidates, balanced one long and one short. The
contract SHA-256 is
`6a681021a595ed8679454aab1bfbe29dff512ccd4ad9872986b7151bcc29745c`.

On the same locked ten-full-weekday June development packet, V31 produced 54
executable trades, or 5.4/full weekday, split 30 long and 24 short. Base net was
USD -29.85, base PF 0.4924332596, stress net USD -40.65, and stress PF
0.3815609311. Only 20% of days were profitable; first-half PF was 0.575 and
second-half PF was 0.380. The terminal decision is
`V31_DEVELOPMENT_FAIL_TERMINAL`. Audit SHA-256 is
`0d0f7cafafb0800d5455b8e708485bba76fd510f34612199df775e3928930bfc` and
trade-ledger SHA-256 is
`f11a69f03d719c8a8d511438e9fb2e71b04a4b9c66baa346243298e5a6cafa04`.

V31 may not be tuned, mirrored, re-timed, trained, or executed from the exposed
June outcomes.

### V30/V31 Mechanism Decision

Both rules solved mechanical frequency, at 5.9 and 5.4 trades per full weekday,
but both lost money after real bid/ask execution and locked slippage. The June
short-horizon Capital market-order threshold family is therefore retired. More
threshold, mirror, or holding-period variants on that exposed packet would be
outcome-driven overfitting, not independent research.

V24.1 and V26 remain valid locked forward hypotheses because their rules and
boundaries were frozen before the untouched post-July-20 evidence began. Their
20-day validation and 20-day confirmation requirements are unchanged. No V30
or V31 result authorizes model training, Python prediction, EA consumption,
demo, live, account, terminal, or broker action.

## V32/V33 COMEX Size-Segment Flow - 2026-07-20

The mechanism failure map identified one untested field in the already acquired
COMEX trades data: prior COMEX campaigns aggregated all aggressive volume and
did not separate large-lot from small-lot flow. V32/V33 therefore registered one
narrow hypothesis that a completed five-minute window with strongly directional
large-lot flow and opposing small-lot flow could precede a slower XAUUSD move in
the large-lot direction. This was a distinct input segmentation, not a mirror of
the failed Capital 120-second quote rules.

V32 preregistered 144 outcome-blind density policies. Its July 2022 calibration
contained 1,351,730 COMEX trade rows and 20 eligible full weekdays. The highest
density was only 43 candidates, or 2.15/day, below the locked
2.3869731801/day minimum. Direction balance and active-day coverage were
adequate. V32 therefore stopped before reading a future spot price or opening a
fill, label, return, or P/L. Decision:
`V32_CALIBRATION_FREQUENCY_STRUCTURE_FAIL`; calibration payload SHA-256:
`b84d951eb9e935581552029dc7e09f15e3acef8919ebf53c5b05442e6a61d090`.

Because V32 exposed candidate density only, V33 registered one explicit
frequency-only repair with 96 additional policies. It preserved the hypothesis,
five-minute completed clock, direction, one-hour economic hold, stop, target,
costs, splits, and gates. It widened only activity thresholds and allowed a 45-
or 60-minute signal cooldown. One pre-candidate path-resolution failure occurred
before any source file or candidate metric was read; a regression-tested package-
root adapter corrected it without changing the grid.

V33 selected the deterministic policy
`SZ08__LV020__LI35__SI10__SV050__CD45`: trades of at least eight contracts,
minimum large volume 20, absolute large imbalance at least 0.35, opposing small
imbalance at least 0.10, small volume at least 50, and 45-minute cooldown. It
produced 58 candidate facts over 20 full weekdays, exactly 2.9/day, active on
95% of days, with 21 long and 37 short. Calibration payload SHA-256 is
`4c2f51c99961fff129e92b2bbc6bf69e121011896119e449a619e68a6745a1e3`.
The immutable contract SHA-256 is
`3bc928c5eddc2254a2b086ed2d0901c5af8314df57fa65aff068b4898713addc`.

The locked development stage then processed 594 COMEX daily files and priced
the retained candidates from verified Dukascopy bid/ask ticks. Across 491
eligible full weekdays it resolved 1,170 trades, or 2.3828920570/day, split 560
long and 610 short. The economic result was consistently negative:

- base net USD -692.87 and base PF 0.4928;
- stress net USD -775.75 and stress PF 0.4547;
- first-half stress PF 0.4606 and second-half stress PF 0.4487;
- 24.44% profitable weekdays and 0% positive months;
- top-five-winners-removed stress net USD -800.21; and
- closed stress drawdown USD 775.75.

Decision: `V33_DEVELOPMENT_FAIL_TERMINAL`. Audit SHA-256 is
`888e38a5c1361dcbea9b528087e8424e8a398199e5cbac0d93c80aa6f73e62ab`,
candidate SHA-256 is
`8ef040907d7dd3d06a306fca0d54413993dcb8ed5a8c34bcd9842cae45c25475`,
and label SHA-256 is
`0804b646fbc84130d3ee7de3e50bcc62aa282ee4bdfcb31183062fc8852ec544`.
Validation and exam remain sealed.

The COMEX large-versus-small continuation family is retired on exposed history.
Its mirror, thresholds, hold, stop, and target may not be selected from these
outcomes. V32/V33 authorize no training or execution. The untouched V24.1/V26
forward collection and same-period Core reconstruction remain the authoritative
active evidence paths.

## V34 Capital R4 Chop Forward Adapter - 2026-07-20

`capital-r4-chop-forward-v34` closes the R4 same-period candidate-clock
engineering gap without changing the frozen V26 rules. The adapter imports all
three V26 component masks and parameters directly. It uses read-only Capital MT5
M5 history for long indicator context and replaces only quality-passed completed
M5 buckets with OHLC and signed-tick fields reconstructed from the prospective
Capital bid/ask quote ledger.

The quote aggregation reproduces the original Dukascopy semantics, including
resetting the first price change in each M5 bucket so cross-bucket jumps cannot
leak into tick imbalance. A signal requires three contiguous quality-passed live
M5 buckets. Unavailable Capital book volume is not fabricated and is not consumed
by any frozen R4 mask.

- Transport contract SHA-256:
  `9fa530dc59595d43873c890b82699fbbba36e00c1db34f1fe9ee4540ff7caeea`.
- Rule dependency SHA-256:
  `d14634f35004e9691e05b2153885e44a2531175af9f7f7a2f7f2091f152c6d58`.
- Frozen V26 contract SHA-256 remains
  `6294d575c93bc70d3720773bd0056dee7dcd4509e3e36f31b38409c46428f650`.
- Historical feature parity: all 19 signal-used fields matched over 708,538
  rows.
- Historical candidate parity: 948 raw signals, 588 valid component candidates,
  67 priority duplicates removed, and exactly 521 unique candidates. Generated
  and frozen canonical stream SHA-256 values both equal
  `ab23adb10a65538f0a4ac5013f32d858f4ca02e9b5ceeff0413f9161302dba01`.
- Focused tests: 5 passed, including Git/Windows line-ending-independent rule
  hashing. Ruff: passed.
- First real Capital cycle on account `1033669`: 209,875 unique quotes, 143
  completed quote M5 bars, 141 quality-passed bars, 137 contiguous 15-minute
  fields, latest regime `CHOP`, and zero candidates. Zero is a valid abstention,
  not a failed cycle.
- Persistent hidden collector: parent PID `37864`, Python child PID `39176`.
  Runtime directory:
  `C:\MT5PortableProspectiveCollector\MQL5\Files\r4_chop_shadow_v34`.

V34 was necessarily locked after the July 20 forward boundary, so it is recorded
as a post-boundary transport adapter rather than a new preregistration of economic
edge. No post-boundary outcome, P/L, label, exit, win rate, or return was opened
while implementing it. It emits append-only candidate facts only and has no
broker-action path. R5 current-input coverage, same-period shared-account
outcomes, and the 3-4 trades/day proof remain open.

## V35 Capital R5 Transition Forward Adapter - 2026-07-20

`capital-r5-transition-forward-v35` closes the current macro-input and candidate-
clock gap for the frozen R5 transition specialist without changing its four
components or selected router. The exact components are attempts `23925`,
`24877`, `24995`, and `25048`. The router is attempt `27135`, the frozen 180-day
trailing-drawdown policy.

Capital exposes DXY but no exact Treasury total-return instrument. V35 therefore
uses the original free official Dukascopy instruments rather than substituting a
proxy:

- `DOLLAR.IDX-USD`;
- `USTBOND.TR-USD`.

The official Jetta July backfill completed 916 hour-symbol records through the
2026-07-20 02:00 UTC boundary: 914 new validated downloads, two resumed validated
hours, 176,961 ticks, and zero failures. Concurrency never exceeded four. No paid
data service or account was used.

- Final transport contract SHA-256:
  `23a0c31a6d6466bac93362945947b8022ae466583f02a26a24c77e69ee24e7fd`.
- Rule dependency SHA-256:
  `863b9f19635b7a7a120a51c37d80770da90cc9ee7a913cf01b348ba595642ec0`.
- Historical V9 candidate parity: exactly 799 rows; generated and frozen
  canonical SHA-256 values both equal
  `feab363ab7aa9b93e335bbcae2d83a735df50b07922ada4574d40d064abc3a2c`.
- Historical V11 router parity for attempt `27135`: exactly 330 selected trades;
  generated and frozen canonical SHA-256 values both equal
  `a6755d5903376766a0abcda05666a5b33bfb527544457bb9f841e99501ea3efa`.
- Focused tests: 5 passed. Ruff: passed. Existing lock re-verification: passed.
- First integrated Capital cycle: 232,054 gold M5 bars, 137,986 joint macro M15
  rows through `2026-07-20T01:15:00Z`, zero component candidates, zero routed
  candidates, and all authority flags false.
- Persistent hidden collector: parent PID `38784`, Python child PID `532`.
  Runtime directory:
  `C:\MT5PortableProspectiveCollector\MQL5\Files\r5_transition_shadow_v35`.

V35 emits current component and router candidate facts only. It uses frozen
component outcomes whose exits precede each candidate. Updating the 180-day
router with new prospective component outcomes is intentionally unauthorized
until a separate causal resolver is preregistered and locked. This limitation
does not affect the initial candidate clock. V38 now provides the separately
locked causal component resolver, but a successor router must still consume only
outcomes causally known before each future candidate before exact long-horizon
online-router continuity can be claimed. V35 opens no economic outcomes and has
no broker-action path. Same-period shared-account economics and the 3-4
trades/day proof remain open.

## V36 Macro-Informed Bidirectional Router - 2026-07-20

`macro-informed-bidirectional-router-v36` tested one locked structural change to
the rejected V1 bidirectional router: causal DXY and Treasury total-return
pressure at H1/H4 horizons, plus exact route-direction alignment. The 100,780
actions, 20,331 events, 81 base features, labels, costs, Core ledger, model,
walk-forward schedule, four blocks, 1,000 policies, and economic gates remained
unchanged.

Two pre-economic input checkpoints are documented in
`PRE_OUTCOME_AMENDMENT.md`. Exact H12 returns were unusable across regular
Treasury session gaps, and initially requiring complete macro fields reduced a
calibration block below the unchanged 200-event minimum. No policy economics had
opened. The final lock preserved every V1 row and used native histogram-model
missing branches; the 200-event guard was not weakened.

- Final contract lock SHA-256:
  `8f7831444854995c7b77854c388bfc762c64e1db450d61bb9f1feb69a5b1eaf6`.
- Dataset: 100,780 actions, 20,331 events, 98 model fields, balanced 50,390
  long/short rows.
- Macro timestamps available: 88,216 action rows; every available timestamp was
  no later than its signal and at most 15 minutes old.
- Policies evaluated: exactly 1,000; all-block survivors: zero.
- Diagnostic best: `MACRO_Q90__D6__S60__A2__W0P5`.
- Final Expansion: 298 trades, 1.142/day, -$128.32 at 0.50 risk weight,
  PF 0.881, $223.04 drawdown.
- Final combined: 458 trades, 1.755/day, +$4,380.47, PF 2.515, $944.81
  closed-trade drawdown.
- The unchanged final Core alone remained 160 trades, 0.613/day, +$4,508.78,
  PF 3.492, and $889.69 drawdown. V36 therefore weakened the Core.
- 68 policies reached at least 3.0 combined trades/day in every block, but none
  maintained PF >=1.20 or positive Expansion net in every block.
- In the final block the top-decile router shifted to 85.9% long and 42.6%
  flipped actions; its top-decile PF fell to 0.843. This is a nonstationary
  direction failure, not a candidate-density failure.
- Result SHA-256:
  `41892e5071878cb6bed2f77d5ebdca5add0ce86e19f30b98b438471b04267ef1`.
- Manifest SHA-256:
  `6944d281b52054eec87bb926ba1fb2e01b3a695bb22ec950b9ccbef782e3c80d`.
- Focused tests: 10 passed after the documented input-only amendments. Ruff:
  passed. Manifest, causal alignment, split boundaries, duplicates, infinity,
  and exact baseline-evaluator parity all reverified.

Decision: `MACRO_ROUTER_V36_NO_ALL_BLOCK_SURVIVOR`. V36 is terminal and may not
be rescued with a score threshold, direction cap, regime filter, feature subset,
or model retune against the exposed final result. It authorizes no model serving,
EA consumption, demo/live trading, or broker action.

## V37 Sealed Forward Frequency Observer - 2026-07-20

`sealed-forward-frequency-observer-v37` now provides one outcome-blind status for
the six active candidate clocks: V28 R2/R3, V29 R1, V34 R4, V35 R5, V24.1
microburst, and V26 gap-restart. It reads candidate counts and liveness only.

- Static contract SHA-256:
  `930b7f8a6bcbb17dea2658ea3efadafaa0195333ff4a60b8ff368a7c2f6599c8`.
- Focused tests: 7 passed. Ruff: passed. Any malformed, missing, or failed
  source cycle now overwrites the prior status with an explicit `FAIL_CLOSED`
  record rather than leaving a stale green status visible.
- First sealed cycle: `PASS_READ_ONLY_SEALED`, all four specialist adapters fresh,
  all authority flags false, no economic outcome open.
- Partial Monday supply at 03:13 UTC: one V24.1 candidate and one V26 candidate;
  all R1-R5 candidate counts remained zero. Raw component supply was two, with a
  one-to-two unique-count bound because cross-clock timestamps remain sealed.
- Zero complete evidence weekdays exist. Candidate frequency is explicitly not
  authorized from a partial day.
- Automatic inventory refresh is permitted only below 19 eligible weekdays and
  stops before the 20-day validation can open.
- Persistent hidden observer PID: `37456`, polling every 900 seconds.
- Runtime directory:
  `C:\MT5PortableProspectiveCollector\MQL5\Files\forward_frequency_observer_v37`.

V37 does not deduplicate clocks, resolve shared-account concurrency, calculate an
exit, open P/L, admit a strategy, or call a broker API. The untouched V24.1/V26
validation path and same-period Core candidate collection remain the authoritative
route forward.

## V38 R5 Causal Prospective Outcome Resolver - 2026-07-20

`capital-r5-causal-outcome-resolver-v38` closes the missing R5 component-label
engineering path without modifying the locked V35 candidate adapter or the
frozen Core. It consumes V35's append-only component candidate facts and the
Capital quote CSV ledger only.

- Contract SHA-256:
  `ef58627347cc0d10775f1d1cc0bd152abcab995bbc7a2e3ae844e9f7cd17cccd`.
- Frozen components: attempts `23925`, `24877`, `24995`, and `25048`.
- Historical audit: all 799 V9 candidates retained exact
  `signal_time == scheduled_entry_time` parity and all four component identities.
- Execution semantics: first timely quote, side-correct bid/ask, observed stop
  slippage, locked target fill, fixed horizon, spread/risk gates, ticket and
  holding costs, stress slippage, component overlap, and the four-trade UTC-day
  cap all remain frozen from V9.
- Candidate and resolution ledgers have independent persisted append-only prefix
  hashes. Mutation, truncation, partial output, dependency changes, malformed
  quotes, or any enabled authority flag fails closed.
- Focused tests: 11 passed. Ruff: passed. A complete synthetic outcome is exactly
  equal to the frozen V9 execution function; pending windows, missing-data
  cutoffs, stop/target/horizon behavior, overlap, daily cap, idempotence, source
  mutation, ledger mutation, and authority rejection are covered.
- First real cycle: `ACTIVE_READ_ONLY_CAUSAL_RESOLVER`, zero V35 candidates, zero
  resolutions, no aggregate economics opened, and all execution flags false.
- Capital quote ledger observed through `2026-07-20T03:50:55.516Z` on the first
  persistent cycle.
- The V38/V39 polling order was rephased after V39 entered
  `WAITING_FOR_V38_SYNC`: V35 now updates before V38, and V39 polls after V38.
  Current V38 status is `ACTIVE_READ_ONLY_CAUSAL_RESOLVER`.
- Persistent hidden parent PID: `27700`; wrapper PID: `44264`; current Python
  child PID: `39464`; poll interval: 300 seconds.
- Runtime directory:
  `C:\MT5PortableProspectiveCollector\MQL5\Files\r5_transition_outcomes_v38`.

V38 records individual prospective component outcomes but does not publish an
aggregate result, tune R5, train a model, route broker orders, or admit the
sleeve. A separately locked successor router/evaluator must use each label only
after its recorded causal knowledge time and preserve the 20-weekday validation
plus 20-weekday confirmation boundary.

## V39 R5 Causal Successor Router - 2026-07-20

`capital-r5-causal-router-v39` now continues the frozen V11 180-day R5 router
using V38 prospective labels without retrospective leakage. It leaves V35 and
V38 unchanged.

- Contract SHA-256:
  `38f9daf3578ae209cd602321aa54706ce5897f3a7c713a5a0043d6512c8c6980`.
- Frozen policy: attempt `27135`, router ID `16df08f0e24d9d95`, trailing
  180-day component drawdown, minimum history five, pass threshold `2.0 R`,
  cold-start multiplier `0.50`, weak multiplier `0.25`, and unchanged component
  base weights.
- A prospective component label is eligible only when its V38 status is
  `EXECUTED` and both its exit and causal knowledge time are strictly earlier
  than the candidate. Equal-time and future labels are excluded; rejected
  component candidates never enter history.
- V39 waits for V38 prefix and status synchronization before appending a route,
  so a poll-order race cannot bypass the outcome resolver.
- Historical route parity: 457 component route decisions, zero statistic or
  multiplier mismatches. The generated 330 selected trades and V11 artifact
  both hash to
  `a6755d5903376766a0abcda05666a5b33bfb527544457bb9f841e99501ea3efa`.
- Focused tests: 7 passed. The strict knowledge cutoff, frozen cold/weak weights,
  rejected-label exclusion, no-outcome route schema, invalid knowledge ordering,
  and append-only prefix behavior are covered.
- First persistent cycle: `ACTIVE_READ_ONLY_CAUSAL_ROUTER`, synchronized with
  V38, zero candidates, zero resolutions, zero routes, no aggregate economics,
  and all authority flags false. Stderr is empty.
- Current status after poll rephasing: `ACTIVE_READ_ONLY_CAUSAL_ROUTER`,
  `v38_synchronized=true`; V35 updated at `2026-07-20T05:31:17.748755Z`, V38
  at `2026-07-20T05:31:27.569843Z`, and V39 at
  `2026-07-20T05:32:09.340740Z`.
- Persistent hidden parent PID: `31524`; wrapper PID: `30960`; current Python
  child PID: `44808`; poll interval: 300 seconds.
- Runtime directory:
  `C:\MT5PortableProspectiveCollector\MQL5\Files\r5_transition_router_v39`.

V39 records route decisions only. It does not attach a candidate outcome,
evaluate forward profitability, tune the router, train a model, or authorize any
EA/demo/live action. The untouched validation and confirmation boundaries remain
the admission gate.

## V40 R1-R4 Core Causal Outcome Resolver - 2026-07-20

`capital-core-causal-outcome-resolver-v40` now closes the remaining same-period
individual-label gap for V28 R2/R3, V29 R1 pullback, and V34 R4 without changing
any frozen candidate collector or strategy rule.

- Contract SHA-256:
  `5968e3f6c43b1bb01be93ba7ecce76b1ad2ea42c4c1389bd7c82803b49d4e9fa`.
- V28 historical parity: 658 candidates, 379 component trades, 236 exact rebuilt
  composite trades, and frozen component attempts `11142`, `11266`, `12183`,
  `12222`, and `12389`.
- V29 historical parity: all 413 accepted MT5 orders paired to all 413 closed
  trades with zero entry-price error, maximum stop-rounding error `0.005`,
  maximum 2R target-rounding error `0.0028491`, only stop/target exits, peak
  seven concurrent positions, and peak nine entries per UTC day. The frozen
  eight-position and twelve-entry limits remain unchanged; no time exit was
  invented.
- V34 historical parity: 521 candidates, 125 trades, frozen attempts `39427`,
  `39888`, and `40193`, exact one-position/cooldown behavior, and peak two
  entries per UTC day.
- V28 resolves executable stops or fixed horizons per component. V29 resolves
  only executable stops or locked 2R targets and keeps open positions pending.
  V34 resolves executable stops, locked 2R targets, or its 12-hour horizon with
  the frozen shared-position, cooldown, priority, and daily-cap policy.
- Candidate and resolution ledgers have independent persisted append-only prefix
  hashes. Source contract changes, prefix mutation/truncation, malformed quotes,
  candidate schema drift, or enabled authority fails closed.
- Focused tests: 10 passed. Integrated V28/V29/V34/V38/V39/V40 tests: 41 passed.
  Ruff and format checks passed.
- First persistent cycle: `ACTIVE_READ_ONLY_CAUSAL_RESOLVER`, synchronized with
  all three source clocks, zero candidates, zero resolutions, no aggregate
  economics, and all authority flags false. Stderr is empty.
- Persistent hidden parent PID: `13644`; current Python child PID: `7252`;
  poll interval: 300 seconds.
- Runtime directory:
  `C:\MT5PortableProspectiveCollector\MQL5\Files\core_outcomes_v40`.

V40 may append individual causal labels only. It does not route the R2/R3
composites into a shared account, combine R1-R5 with V24.1/V26, publish aggregate
P/L, train a model, tune a strategy, or authorize EA/demo/live action. A locked
same-period shared-account evaluator remains the next engineering dependency.

## V41 R1 Box Causal Outcome Resolver - 2026-07-20

`capital-r1-box-causal-outcome-resolver-v41` replaces the R1 sidecar's mutable
latest-outcome snapshot as evidence with an append-only causal label path. The
source observer and frozen R1 rule remain unchanged.

- Contract SHA-256:
  `f78d0b01b9ed9b65e71429dd461d0b967ae44058944de2452043051402728363`.
- Frozen source contract SHA-256:
  `27fef83d1a57aa28a1e4d4e6968b2854184a673cdff6769da16828fbe4084908`.
- Historical Dukascopy parity: 354 candidates, 345 executable candidate paths,
  464 policy rows, and 119 decision-eligible
  `PORTFOLIO_CONSTRAINED_PRIMARY` trades. Candidate, all-policy, and primary-policy
  digests exactly reproduce the frozen source artifacts.
- The primary policy reached exactly two concurrent positions and one entry per
  UTC day, matching its frozen limits. The diagnostic 32-position policy remains
  excluded from prospective decisions.
- Long entry uses the first timely Capital ask; exits use Capital bid. Stops pay
  observed executable slippage, targets fill at the locked 2R price, and no time
  exit is invented. An accepted position remains pending until stop or target.
- Candidate and resolution ledgers have independent immutable prefix hashes.
  Candidate identity, settings, source bytes, status identity, authority, tick
  schema, or consumed-prefix drift fails closed.
- Focused tests: 7 passed. Ruff and format checks passed.
- First locked Capital cycle: `ACTIVE_READ_ONLY_CAUSAL_RESOLVER`, zero candidates,
  zero resolutions, quote ledger observed through
  `2026-07-20T04:57:32.643Z`, and all authority flags false. Stderr is empty.
- Persistent hidden parent PID: `25780`; current Python child PID: `24392`; poll
  interval: 300 seconds.
- Runtime directory:
  `C:\MT5PortableProspectiveCollector\MQL5\Files\r1_box_outcomes_v41`.

V41 records individual primary-policy R1 box outcomes only. It does not combine
R1 sleeves, route R2/R3 composites, attach an R5 routed outcome, calculate
shared-account economics, train a model, or authorize an order. The sealed
same-period shared-account evaluator is the next engineering dependency.

## V42 Sealed Shared-Account Forward Evaluator - 2026-07-20

`capital-shared-account-forward-evaluator-v42` now closes the same-period Core
and floating-equity measurement gap without changing or rejecting a frozen Core
or V27 satellite trade.

- Contract SHA-256:
  `bcb1b985161d1d889c1953441af065bad897715fc57e46c4c3e97dd896551bfa`.
- V42 reconstructs V41 R1 box, V40/V29 R1 pullback, exact one-position V40/V28
  R2 and R3 composites, V40/V34 R4, and V38/V39 causally weighted R5. It then
  adds only the already frozen V27 satellite selections.
- Validation uses V27's exact first 20 full weekdays; confirmation uses the next
  20 and remains sealed unless V42 validation passes its research gates.
- Before a complete stage, V42 exposes liveness and counts only. It verifies
  source contract identity, consumed append-only prefixes, candidate fact
  hashes, final causal resolutions, route weights, timestamps, authority flags,
  and exact Capital entry/exit ticks.
- Every combined position is marked on each Capital bid/ask tick. V42 reports
  base and stress floating drawdown, closed drawdown, daily loss, concurrent
  positions, gross/directional lots, and leverage-based margin.
- Research gates require 3.0-4.0 trades per weekday, V27 passage, positive base
  and stress net, PF at least 1.20/1.05, at least 50% profitable days, PF at
  least 1.0 in both chronological halves, and no more than USD 1,000 closed
  drawdown.
- Account readiness is separate. The locked reference is USD 3,000 equity,
  1:100 leverage, 0.01 minimum/step, 15% maximum equity drawdown, 3% daily loss,
  and 40% margin. The historical USD 1,733.37 conservative Core drawdown alone
  requires at least USD 11,555.80 equity at the 15% limit. Therefore this
  reference account is known not ready before forward economics open.
- The live Capital account check at lock returned balance/equity USD 2,998.45,
  leverage 100, XAUUSD contract size 100 ounces, and volume minimum/step 0.01.
  Historical USD 889.69 closed drawdown is about 29.7% of USD 3,000; USD
  1,733.37 floating-equity evidence is about 57.8%.
- R5 fractional research weights are not broker lots. V42 cannot pass account
  readiness until a separate causal broker-size mapping is preregistered and
  validated.
- Focused tests: 7 passed. Integrated V28/V29/V34/V38/V39/V40/V41/V42 tests:
  55 passed. Ruff and format checks passed.
- First cycle: `WAITING_FOR_SEALED_STAGE`, V27 validation unavailable, all Core
  sources active, zero Core candidates/resolutions, aggregate economics sealed,
  and all authority flags false. Stderr is empty.
- Persistent hidden parent PID: `34168`; wrapper PID: `35696`; current Python
  child PID: `6420`; poll interval: 300 seconds.
- Runtime status:
  `xau-usd/xauusd-fast-research/capital-shared-account-forward-evaluator-v42/outputs/CAPITAL_SHARED_ACCOUNT_V42_STATUS.json`.

V42 has no model-training, prediction, EA, demo, live, or broker authority. A
historical shared-account drawdown attribution and separately preregistered risk
controller are mandatory before the account-readiness failure can be addressed.

## V43 Historical Core Drawdown-Control Audit - 2026-07-20

`historical-core-drawdown-control-audit-v43` attributes the USD 889.69 closed
drawdown and applies only the R1 box exposure policy that was frozen before this
diagnostic. It does not search a new drawdown threshold or alter another
specialist.

- Contract SHA-256:
  `b85fa207b87f7fdd91775cda3433b8e5222fe30b26c09bc54b227e1d2f92895c`.
- The one-year drawdown ran from the 2025-12-26 equity peak to the 2026-01-09
  trough. All 11 exits were R1 uptrend trades: seven stacked R1 box trades lost
  USD 866.37 and four R1 pullbacks lost USD 23.32.
- The pre-existing R1 box cap permits at most two concurrent positions and one
  new entry per UTC day. It keeps 54 of 145 historical R1 box rows and leaves
  all other Core rows unchanged.
- One-year metrics change from 160 trades, 0.613/day, USD 4,508.78 net, PF
  3.492, and USD 889.69 closed drawdown to 142 trades, 0.544/day, USD 2,478.19
  net, PF 3.195, and USD 259.53 closed drawdown. Closed drawdown falls 70.8%,
  but this is retrospective evidence and not a fresh holdout.
- The independent ten-year Dukascopy `PORTFOLIO_CONSTRAINED_PRIMARY` replay has
  119 trades. Its globally marked M5 stress drawdown is USD 521.21; exact raw
  ticks verify USD 521.21 from 2025-04-02 23:52:59.261 UTC to 2025-08-28
  13:07:00.727 UTC.
- USD 521.21 is 17.38% of the current USD 2,998.45 equity and fails the frozen
  15% ceiling. R1 alone needs USD 3,474.76 without a capital buffer or USD
  4,343.45 with the frozen 25% buffer.
- At current equity the buffered maximum lot is 0.0069. Capital's minimum and
  step are 0.01, so the broker cannot express the safe size. Until V42 produces
  complete same-period evidence, the legacy whole-Core USD 1,733.37 floating
  drawdown requires USD 14,444.75 with the same buffer.
- Decision: `R1_STACKING_CONTROL_EFFECTIVE_ACCOUNT_NOT_READY`. Keep the R1 cap,
  reject a 0.01-lot executor on the current account, and retain V42 exact
  shared-account validation. No demo/live or broker authority is granted.
- Focused tests: 6 passed. Ruff and format checks passed. Source hashes include
  the normalized Core ledger, frozen portability code/config, V41 contract,
  ten-year Dukascopy M5 cache, and exact raw peak/trough hours.

## V44 COMEX Flow-Transition Diagnostic - 2026-07-20

`comex-flow-transition-v44` tested a genuinely event-ordered COMEX mechanism
after static flow, bar lead/lag, auction, and large-versus-small lanes failed. It
used individual already-acquired Databento trade prints and opened no paid or
network data.

- Hypothesis: one-sided prior aggressor flow with weak directional price impact,
  followed by accelerated opposite five-second flow and at least one tick of
  confirmation, may continue in the new-flow direction.
- All feature events are strictly earlier than the decision. The fixed windows
  are prior `(t-35s,t-5s]` and current `(t-5s,t]`, followed by a global
  45-minute dependence cooldown.
- Pre-outcome tests caught and fixed a pandas-3 timestamp-resolution mismatch
  before calibration. Four focused causality/grid/selector tests and Ruff pass.
- Outcome-blind July-2022 calibration evaluated exactly 1,000 registered
  policies over 20 eligible weekdays. It selected
  `PV220__PI25__IE10__CV50__CI20`: 58 candidates, 2.90/day, 90% active days,
  31 long, and 27 short. No spot price, label, return, or P/L was opened.
- Calibration audit payload SHA-256:
  `e3f8cdd4acdbfdc8abde1c8584bf1b0cb4a41fc54ee639b1388fadb318171a08`.
- Immutable contract SHA-256:
  `3f0fa32f8b5d70c2abdcd93b0eb4bb1823912ab7780dee34f9e5d611294ebcf6`.
- Development opened 491 eligible weekdays and 1,615 executable Dukascopy
  labels. Frequency passed at 3.289/day with 878 long and 737 short.
- Economics failed terminally: base net `-$1,050.65`, stress net `-$1,168.09`,
  base PF `0.4695`, stress PF `0.4333`, 22.20% profitable days, zero positive
  months, first/second-half PF `0.4164/0.4508`, and top-five-winners-removed net
  `-$1,194.37`.
- Development closed stress drawdown was `$1,168.09`, far above the frozen
  `$250` specialist ceiling. The bootstrap p-value was `1.0`.
- Decision: `V44_DEVELOPMENT_FAIL_TERMINAL`. Validation and exam remain sealed.
  Threshold repair, direction mirroring, and same-version economic changes are
  prohibited.

V44 proves that event-level COMEX data can generate the requested density, but
not that density has positive expectancy. It cannot enter Core, V42, model
training, Python prediction, an EA, demo/live, or broker action. Forward V24.1
and V26 collection remains untouched.

## V45 COMEX Sequence-Ignition Diagnostic - 2026-07-20

`comex-sequence-ignition-v45` tested event-order persistence and trade-arrival
acceleration, not V44's exhausted-flow flip. It used only already-acquired
Databento trade prints and verified Dukascopy execution labels.

- Fixed mechanism: a persistent terminal same-side aggressor run, elevated
  same-side transition share, directional five-second flow/price response, and
  arrival acceleration relative to the preceding 30 seconds.
- Exactly 1,000 outcome-blind density policies were registered. Four focused
  causality/grid/selector tests and Ruff pass.
- July-2022 calibration selected `TC30__RL05__TS70__IM35__AC125`: 58 signals,
  2.90/day, 95% active days, and exactly 29 long/29 short. No spot outcome or
  P/L participated.
- Calibration payload SHA-256:
  `a6b189f8b92d7c9fb720b9e7a5175cac58c59bf63ac7ffb8e5ae2a56aed74105`.
- Immutable contract SHA-256:
  `3e950672a46401187d2bcddbc2634c53bd862a420c15b2c8c19c59a26cec019b`.
- Development produced 1,939 executable trades over 491 eligible weekdays,
  3.949/day, with 984 long and 955 short. Frequency drift exceeded the locked
  3.38697/day maximum.
- Economics failed terminally: base/stress net `-$1,231.11/-$1,373.04`,
  base/stress PF `0.4599/0.4224`, mean stress `-$0.7081/trade`, 18.33%
  profitable days, zero positive months, first/second-half stress PF
  `0.4431/0.4021`, and winner-removed net `-$1,410.19`.
- Closed stress drawdown was `$1,373.04`, versus the frozen `$250` maximum; the
  bootstrap p-value was `1.0`.
- Decision: `V45_DEVELOPMENT_FAIL_TERMINAL`. Validation/exam stay sealed and
  same-version repair is prohibited.

The 1,939 development feature/outcome rows are high-quality executable labels
for a separately preregistered Python ranking diagnostic. They do not make V45
tradable and cannot authorize model, EA, demo/live, or broker use.

## V46 COMEX Sequence Python Ranker - 2026-07-20

`comex-sequence-ml-ranker-v46` trained the first new Python model in this COMEX
sequence lane under a fixed feature/model/chronology contract. It attempted to
filter V45 candidates without allowing frequency to collapse.

- Fixed model: shallow `HistGradientBoostingClassifier`, 100 iterations, seven
  leaves, minimum 50 samples/leaf, L2 1.0, early stopping off, seed 460046.
- Eleven candidate-time features cover log flow counts/volume, imbalance,
  same-side transitions, arrival acceleration, terminal run length/volume,
  directional impulse, direction, and session progress. No label, exit, P/L,
  MFE/MAE, future regime, candidate ID, or date identity is a feature.
- Fit used 2022-08 to 2023-07. Threshold calibration used only model scores and
  candidate facts from 2023-07 to 2024-01; its labels were not read.
- Pre-fit tests: three passed; deterministic dual fits produced identical
  probabilities. Ruff and format checks pass.
- Immutable model contract SHA-256:
  `dc2066337e4bc8e72fbca5561ddc7e96af93a8305ea8cc7cff55ed4040e87a6b`.
- Locked threshold `0.2568986845` accepted 372 calibration candidates over 129
  eligible weekdays: 2.884/day, 96.12% active days, 183 long, and 189 short.
- The 2024-01 to 2024-07 internal exam was opened only after lock. It accepted
  323 trades over 128 days, 2.523/day, with 149 long and 174 short.
- Rank AUC was `0.5340`, below the frozen `0.55` minimum. Base/stress net was
  `-$193.18/-$218.30`; base/stress PF `0.5192/0.4785`; profitable days 24.22%;
  positive months zero; first/second-half PF `0.3691/0.5815`; winner-removed net
  `-$236.35`; and bootstrap p-value `1.0`.
- Closed stress drawdown was `$221.53`, passing the `$250` ceiling. Frequency,
  sample size, direction balance, and drawdown passed, but discrimination and
  every economic/stability gate failed.
- Decision: `V46_INTERNAL_EXAM_FAIL_TERMINAL`. Historical validation and exam
  remain sealed. Retraining, threshold repair, alternate seeds, or feature
  changes are prohibited.

V46 is a real trained and hashed Python research artifact, but not a usable
prediction model. It proves drawdown and frequency can coexist in this stream;
it does not prove positive expectancy. No model, Python, EA, demo/live, or
broker authority is granted.

## V47 HistData Independent-Feed Audit - 2026-07-20

`histdata-xauusd-independent-feed-audit-v47` tested whether the free HistData
XAUUSD tick download could add an independent market view without payment.

- January 2024 contained `3,062,220` valid tick rows and covered `6,066` matched
  active M5 bars against the immutable Dukascopy cache.
- Quote quality was internally valid, but M5 mid closes matched exactly on
  `100%` of matched bars; return correlation was effectively `1.0`, median basis
  was zero, and basis standard deviation was zero.
- Decision: `REJECT_SOURCE_FOR_CROSSVENUE_RESEARCH`. HistData is a
  wrapper/derivative of the existing Dukascopy feed, so more HistData years
  would add volume, not information. No additional years should be downloaded.
- Seven focused tests, Ruff, formatting, source hashing, and contract
  verification passed. No paid request or broker action occurred.

## V48 Capital Micro-Pullback Calibration - 2026-07-20

`capital-micro-pullback-forward-v48` tested a short-horizon Capital quote
mechanism using only candidate density and no future outcomes.

- The fixed USD `0.35` spread ceiling excluded the first chronological half
  because ordinary logged spread changed from roughly USD `0.50` to USD `0.30`
  on 2026-07-02.
- All `108` registered policies therefore had zero first-half density.
- Decision: `V48_CALIBRATION_STRUCTURE_FAIL_TERMINAL`. No candidate P/L or
  post-candidate outcome was opened, and same-version repair is prohibited.

## V49 Relative-Spread Pullback Forward Lane - 2026-07-20

`capital-relative-spread-pullback-forward-v49` is the preregistered portability
successor to V48. It uses the current spread relative to a completed lagged
30-minute median, plus a USD `1.00` hard ceiling.

- Outcome-blind calibration registered `240` policies and selected
  `I200__R50__S10__C120`: `33` candidates over `33` eligible weekdays, exactly
  `1.0/day`, `66.67%` active days, `17` long and `16` short.
- First/second-half density was `1.125/0.882` per weekday. No calibration P/L,
  post-candidate price, or future label was used.
- Calibration audit SHA-256:
  `edfbeabb542b34fe850a8c4d951cd71877eb960d2567ce33334b1a12223d3bda`.
- Contract SHA-256:
  `d37d5da5660db1eb743dfe722e536da545fd33e5c2835c5f02d73efb03c94218`.
- Forward collection begins 2026-07-21. It currently has zero eligible full
  weekdays and keeps economics sealed until `20` complete weekdays exist.
- Eight focused tests and Ruff/format checks pass. Hidden watcher PID `6084`
  polls every `300` seconds. All model, EA, demo/live, payment, and broker
  authority flags remain false.

## V50 Single-R1 Exposure Risk Control - 2026-07-20

`historical-core-single-exposure-risk-v50` directly addresses the USD `889.69`
drawdown by locking the smallest non-zero broker-expressible exposure: one open
R1 box position and one new R1 box entry per UTC day.

- This is retrospective risk governance with zero parameter search, not an
  untouched-alpha claim. Signal, stop, target, and all other specialists remain
  unchanged.
- One-year results move from the V43 two-position policy's `142` trades,
  `0.544/day`, USD `2,478.19` net, PF `3.195`, and USD `259.53` closed DD to
  `138` trades, `0.529/day`, USD `1,997.98` net, PF `3.047`, and USD `106.71`
  closed DD.
- Ten-year results retain `1,053` trades, USD `4,230.82` net, PF `2.127`, and
  USD `252.68` closed DD.
- Independent Dukascopy replay has `68` R1 trades. Global M5 stress floating DD
  is USD `335.5784`; exact raw ticks verify USD `335.5782` from 2025-04-02
  23:52:59.261 UTC to 2025-08-28 02:36:56.104 UTC.
- The exact drawdown is `11.19%` of USD `2,998.45`, or `13.99%` after the locked
  25% capital buffer. Buffered minimum equity is USD `2,796.48`, so 0.01 lot is
  broker-expressible with USD `201.97` reserve above that minimum.
- Decision: `V50_SINGLE_R1_EXPOSURE_RISK_GATE_PASS`. Contract SHA-256:
  `3a9649fe6e77105e19583a1351262699dd9a1bb21dc19fd97dc514f916020195`;
  result SHA-256:
  `602bee9ec80812f365cc39ba18696b12c23ca1b2bdecebc03cd2e7928f73ba15`.
- Five focused tests, Ruff, formatting, contract verification, and a fresh full
  audit pass. Whole-account execution remains fail-closed because historical
  intratrade marks are unavailable for every specialist; V42 prospective
  shared-account confirmation is still mandatory.

## V51 One-Trade-Per-Day Portfolio - 2026-07-20

`one-trade-per-day-portfolio-v51` tested the strongest development-period
high-frequency ranker as a separate, account-feasible add-on beside unchanged
V50. The exact policy was locked before its later ranked outcomes were opened.

- V51 corrected a predecessor defect by enforcing the existing
  `current_account_feasible` label and USD `8.165487` maximum initial risk at
  0.01 lot.
- Validation reached `1.624` combined trades/weekday, USD `1,145.69` net, PF
  `1.636`, and USD `196.31` closed DD, but missed the positive-month gate.
- Final reached `1.738/day`, but the add-on lost USD `235.04`, had PF `0.862`,
  and USD `532.50` DD. Combined DD was USD `313.60`.
- Recent tail reached `1.307/day`; the add-on lost USD `422.02`, PF was `0.545`,
  and add-on DD was USD `422.02`. The profitable V50 Core masked that loss in
  the combined result, so frequency alone was not accepted.
- Failure attribution: pure `BREAK_AND_RUN` generated `462/542` final add-on
  trades and lost USD `308.41`; the model chose the 12-hour action for
  `496/542` trades.
- Decision: `V51_ONE_TRADE_PER_DAY_HISTORICAL_GATE_FAIL_TERMINAL`. Contract
  SHA-256: `5509ee0437281befee5546e22b536893331fb56f312f9abc4e2b8fd6f5489e4d`;
  result SHA-256:
  `e85aa72f36967a87d95d5f1969ce3c5b53cc3a39368da8a9f1769922fd1f7d29`.
- Seven focused tests and Ruff pass. No same-version repair or execution is
  authorized.

## V52 Fixed Break-Swing Ranker - 2026-07-20

`break-swing-ranker-portfolio-v52` removed V51's action-selection freedom. It
fixed pure break-and-run to the 36-hour swing action, retrained a shallow Python
ranker quarterly using only completed prior trades, and used a development-
selected 40th-percentile training-score threshold.

- Validation: `1.184` combined trades/weekday, USD `1,177.11` net, PF `1.741`,
  USD `161.70` closed DD. Add-on PF was `1.759`; only the combined
  positive-month gate failed.
- Final: `1.282/day`, USD `3,295.76` combined net, PF `2.041`; add-on PF fell to
  `1.114`, add-on winner-removal net failed, and combined DD was USD `311.61`.
- Recent tail: `1.034/day`, USD `1,896.07` combined net, PF `2.219`, USD
  `163.96` combined closed DD. The add-on itself lost USD `101.92`, PF was
  `0.824`, and winner-removal net failed. This is not an acceptable frequency
  pass because the new trades had negative marginal expectancy.
- A fixed no-ML swing diagnostic confirmed the constraint. At one open
  position and one entry/day, the account-feasible latest-year subset was
  negative. The unbounded 0.01-lot set made USD `251.84` at `0.920/day`, but
  risk ranged to USD `41.08`, all profit came from rows above the current risk
  budget, and net after removing the top five winners was USD `-45.52`.
- Decision: `V52_BREAK_SWING_RANKER_GATE_FAIL_TERMINAL`. Contract SHA-256:
  `f43c7e259950f41bdf3a28c391ac503812f893d4bb6ec64c055f05c85502faf2`;
  result SHA-256:
  `d3db59a63fb167108d18e89779f78dc01d2921919a5b173dd70afbef53d87878`.
- Post-run audit found that the exploratory 408-trade development description
  included multi-tag break rows, while the sealed contract correctly required
  pure break rows and produced 355 development trades. V52 is therefore also
  marked with a development-selection provenance mismatch. The locked policy,
  contract, and failed outcomes remain unchanged; this cannot rescue V52.
- Four focused tests and Ruff pass. V52 proves that one-trade/day frequency is
  mechanically reachable, but not yet with positive marginal expectancy at the
  current broker minimum and account risk budget. V50 remains the protected
  Core; no Python, EA, demo/live, or broker authority is granted.

## V53-V55 One-Trade-Per-Day Risk Diagnostics - 2026-07-20

The health-gated add-on portfolio combined unchanged V50 with V7 swing, V8
retest, and V25 chop candidates behind shared add-on concurrency and daily
limits.

- V53 reached exactly `1.000` final-year trades/weekday with USD `2,402.46`
  combined net, PF `2.435`, and USD `146.31` final closed DD. It failed only
  because development-2 closed DD was USD `303.10`, USD `3.10` above the locked
  USD `300` ceiling. Decision: `V53_ONE_TRADE_PER_DAY_HISTORICAL_GATE_FAIL_TERMINAL`.
- V54 tightened the hard circuit to USD `225/180`. Development-2 DD fell to USD
  `295.44`, but 21 final-window candidates were suspended and frequency fell to
  `0.927/day`. Decision: `V54_ONE_TRADE_PER_DAY_HISTORICAL_GATE_FAIL_TERMINAL`.
- V55 replaced deletion with half-risk sizing. It restored exactly `1.000/day`
  and final PF `2.435`, but development-2 DD was USD `311.92`. More importantly,
  fractional sizing is not broker-expressible for trades already at the 0.01-lot
  minimum. Decision: `V55_ONE_TRADE_PER_DAY_HISTORICAL_GATE_FAIL_TERMINAL`.

V53 contract/result SHA-256 values are
`1d4ffd4e69a9839e2068e21f4cd213be0d59aa7f6da358b6e053bf02ccc667c1` and
`23043684765726e54df389aa5ca2073dab53536bf3a2f4bb25da88e4b36908a6`.
V54 values are
`c44dacba9d621b97bf4c50c2820082bd4e600f88b06b5cad6fe7514b13fe1bef` and
`cf3ed3155825349d6605cfd89a99880cdaef4e854ab6bb8500111448e7c6cc7d`.
V55 values are
`fefa9e63db9127acaa6f4107749baf773b3b7f7e0603b09f477e6097561fc113` and
`f165847a2f8806e2e4c45d155007e92d728366ca32c03791be12592cf23a7a7d`.

## V56-V57 One-Trade-Per-Day Historical Pass - 2026-07-20

An exposed fixed-family search evaluated `4,989` unique interpretable rules
after the established causal 100-completed-trade health gate. Six passed the
development-2, confirmation, and final economic screens. The selected
high-frequency rule is pure `BREAK`, `SWING_2R_36H`, and H4 ADX above 30.

- The candidate has `168/145/189` health-gated trades across development-2,
  confirmation, and final, with PF `1.549/1.732/1.350`. All three windows stay
  positive after removing their five largest winners.
- It excludes 31 underlying events already eligible for V7 or V8, so those are
  not counted again through a second sleeve.
- V56 preserved the fixed V54 ledger and passed, but self-review found that its
  replayed base decisions used a counterfactual shadow equity path. V56 remains
  valid capacity evidence and is superseded for shared-account design.
- V57 sends all unchanged base and breakout candidates through one causal
  account governor using the actual combined closed-equity path. It uses the
  original 0.01-lot-equivalent actions, two add-on positions, USD `45`
  concurrent add-on initial risk, two add-on entries per UTC date, and the hard
  USD `225/180` drawdown circuit.
- V57 development-2: `694` trades, `1.332/day`, USD `1,025.42` net, PF `1.565`,
  USD `275.38` closed DD, and USD `704.83` after removing five winners.
- V57 confirmation: `501` trades, `1.920/day`, USD `1,641.99` net, PF `1.836`,
  USD `206.17` closed DD, and USD `1,066.77` after removing five winners.
- V57 final year: `377` trades, `1.444/day`, USD `2,580.27` net, PF `1.977`, USD
  `158.19` closed DD, 91.7% positive months, and USD `1,156.15` after removing
  five winners.
- Recent three/six months remain above the first target: `1.062/1.202` trades
  per weekday, USD `372.31/1,706.65` net, PF `1.656/2.289`, and USD
  `109.16/110.06` closed DD.
- Across the full available 2016-07-18 to 2026-07-01 ledger, frequency is
  `0.935/day`; the one-trade/day claim applies to each required recent window,
  not the early health-gate warm-up era.

V57 decision: `V57_ONE_TRADE_PER_DAY_HISTORICAL_GATE_PASS`. Contract SHA-256:
`c9e0511ce15f9c5b221263b0291fee9741468cf192c2f35d6f57badffa515fb4`;
result SHA-256:
`982cea4420eb79a5953c3be6a98d3bb19fdff3429ddf3b04d54d3294ec29a2d3`.
Ruff, formatting, focused tests, source hashes, implementation hashes, and the
fresh locked reproduction pass.

This is an exposed historical milestone, not demo/live authority. Final-year
add-on concurrency is capped at two, but the unchanged five-specialist Core can
overlap to seven open positions. USD `158.19` is therefore verified closed
drawdown, not complete whole-account floating-equity drawdown. MT5 parity,
prospective shadow evidence, and full intratrade equity reconstruction remain
mandatory before execution or before starting the two-trades/day phase.

## V58-V60 Correctness And Floating-Equity Closure - 2026-07-20

Self-review found and corrected two execution-significant defects before accepting
the V57 historical milestone.

### V58 native-position correction

- The legacy R1 parser paired exits FIFO by direction instead of using native MT5
  position IDs. In the frozen 678-row R1/R2 control, `388` exits and `387`
  individual P&L assignments did not belong to the native position, although the
  total P&L multiset and aggregate source totals were unchanged.
- V58 rebuilt all `558` R1 rows from the previously sealed native-position
  reconciliation and reapplied the V50 one-open-position/one-entry-per-day rule
  using corrected holding intervals. It did not change a strategy threshold or
  economic gate.
- Final year remained above target at `376` trades, `1.441/day`, USD `2,579.36`
  net, PF `1.988`, and USD `152.59` closed DD.
- Decision: `V58_NATIVE_POSITION_ONE_TRADE_PER_DAY_GATE_PASS`. Contract SHA-256:
  `29b33bd139536f51b0e0a71dd7c5643b6dba82ae128d911a96aa5936313627f5`;
  result SHA-256:
  `3ab433bf59875286983de11c9960cfd72f324fdb563e4641dadae17d1ba7ec2d`.

### V59 broker-expression correction

- Transition V11 counted fractional `risk_weight` rows as trades even though
  their implied lots were below the broker's 0.01 minimum. Rounding those rows up
  would change their risk and is prohibited.
- V59 retained only the `10/330` transition rows with weight exactly `1.0` and
  rejected the remaining `320` without replacement. Every other Core and add-on
  trade remained unchanged and the same causal governor was replayed.
- Development-2: `595` trades, `1.142/day`, USD `1,099.82` net, PF `1.624`, USD
  `242.03` closed DD, and USD `793.17` after removing five winners.
- Confirmation: `441` trades, `1.690/day`, USD `1,273.45` net, PF `1.656`, USD
  `291.76` closed DD, and USD `710.31` after removing five winners.
- Final: `364` trades, `1.395/day`, USD `2,537.35` net, PF `1.976`, USD `152.59`
  closed DD, 83.3% positive months, and USD `1,143.73` after removing five
  winners.
- Decision: `V59_BROKER_EXPRESSIBLE_ONE_TRADE_PER_DAY_GATE_PASS`. Contract
  SHA-256:
  `6e21c5d0316cc0e9b6d7f4b8a8bc9d0b5de0c61feb2154f28814290ed6ba81bf`;
  result SHA-256:
  `ab59b9f62fd03f719412f7e6982bdb59fe98991b5de45b7fc9419500c5822e61`.

### V60 whole-account floating equity

- V60 locked its metric and source hashes before opening the floating result. It
  reconstructed all `2,194/2,194` accepted trades one-to-one and found zero
  timestamp, direction, source-P&L, source-risk, or endpoint mismatches.
- The audit combined `468,279` legacy bid M5 rows, `468,279` matching ask M5
  rows, and `708,538` modern bid/ask feature rows, covering 2010-01-01 through
  2026-06-30. The evaluated portfolio interval contained `1,172,191` bars.
- The mark-to-market envelope uses bid lows/highs for longs, ask highs/lows for
  shorts, charges known cost at entry, exposes boundary trades to the full M5
  bar, and allows favorable-before-adverse ordering inside each bar.
- Base whole-account floating DD is USD `329.64`; with the 25% buffer it is USD
  `412.06`. The extra USD `0.30` native-R1 fee stress produces USD `335.34` raw
  and USD `419.18` buffered. Both pass the frozen USD `359.814` raw and USD
  `449.7675` buffered limits on USD `2,998.45` starting equity.
- Window fee-stress floating DD is USD `298.34` in development-2, USD `335.34`
  in confirmation, and USD `258.70` in the final year. Maximum historical
  concurrency is ten positions, with add-ons capped at two.
- The worst episode is caused by three overlapping R1 longs, not the new add-on
  sleeves. Exact raw ticks independently confirm USD `334.47` fee-stress DD,
  USD `0.87` below the conservative M5 envelope.
- Decision: `V60_WHOLE_ACCOUNT_FLOATING_EQUITY_GATE_PASS`. Contract SHA-256:
  `d9c691f62ce5e39831a6a07f38dc22d01e6b39d06cfa4eeb3aa1030fa50c6ad3`;
  result SHA-256:
  `31c0af548e314b8cd0e935082f58fe088aa91c574b410320b28f3ffe4945af5a`.

V58 has four focused tests, V59 has three, and V60 has two; Ruff, compile checks,
source hashes, implementation hashes, contract verification, endpoint
reconciliation, and fresh locked reproductions pass. The first historical
one-trade-per-weekday milestone is achieved without weakening the locked edge or
breaching the inherited drawdown gate.

The result does not authorize Python prediction, EA consumption, demo/live attach,
or broker action. Remaining execution gates are MT5 portfolio parity and genuinely
new sealed prospective shadow evidence. The two-trades/day research phase must be
additive and separately preregistered; V59/V60 are frozen controls.

## V61-V64 Two-Trade-Per-Day Expansion Audit - 2026-07-20

V59/V60 remained immutable while the first additive two-trades/day research paths
were tested. No rejected experiment removed, resized, or rewrote a frozen trade.

- A capacity-only replay proved that the complete existing qualified V57 pool can
  reach at most `1.659/day` in the final year even with three add-on positions,
  four daily entries, and USD `75` add-on risk. Existing sleeve capacity therefore
  cannot produce two trades/day.
- The complete width-one through width-four interpretable census evaluated
  `13,362` four-condition rules after `1,698` narrower rules. Every stable passer
  was a duplicate or narrower expression of V7, V8, or V57; no independent rule
  remained.
- V61 tested 48 development-only causal state-health policies over events not
  qualified by V57. Several approached or crossed `2/day` in development-2, but
  none passed the original full development gate. The strongest honest near-pass
  reached `2.038/day`, new-trade PF `1.434`, combined PF `1.558`, and USD `268.21`
  closed DD.
- V62 locked exactly that H4-ADX state policy before opening confirmation and
  final. Confirmation was strong at `2.674/day`, USD `1,955.82` net, PF `1.767`,
  and USD `280.84` closed DD. The final-year new lane then failed at only `43`
  trades, USD `-190.51`, and PF `0.294`; combined frequency was `1.559/day`.
  V62 is rejected. Its circuit preserved all V59 trades and combined final PF
  remained `1.818` with USD `166.02` closed DD.
- V63 opened all 48 already exposed policies only as a post-lock architecture
  audit. Zero passed. The maximum final combined frequency was `1.943/day`, but
  its add-on lost USD `442.20` at PF `0.431`. The maximum final frequency with a
  positive add-on was only `1.747/day`. Causal state-health routing over this
  event family is retired for frequency expansion.
- V64 tested the independent counter-direction action ledger: `48,811`
  broker-feasible counter-route rows, bounded interpretable rule widths one to
  four, V57 timestamps excluded, and final outcomes not loaded for selection.
  Zero rules survived both development-2 and confirmation PF, winner-removal,
  sample, and frequency gates.

The current accepted result is still V59/V60: final-year `1.395/day`, USD
`2,537.35` net, PF `1.976`, USD `152.59` closed DD, and USD `419.18` conservative
buffered floating DD under extra fee stress. The requested first milestone is
achieved. Two trades/day is not achieved and must not be claimed by relaxing edge
or drawdown requirements. The next expansion must use a genuinely new mechanical
event family or prospective data, not another threshold variation on the retired
action-ledger routers.

## V65 Box-Breakout Scale Replication - 2026-07-20

V65 tested whether the qualified higher-timeframe box-breakout mechanism could
be translated mechanically to H4/H1 and H1/M15. It loaded only Dukascopy bid/ask
M5 bars before `2025-07-01`, used broker-side executable prices, charged ticket,
holding, and slippage stress, resolved same-bar ambiguity stop-first, and kept the
final year sealed.

- The bounded manifest contained exactly `256` variants across two scales, both
  directions, two causal regime modes, two box widths, two volatility ceilings,
  two range ceilings, two signal-body floors, and two reward targets.
- Zero variants passed all three chronological development-1, development-2,
  and confirmation gates.
- The best H4/H1 long minimum-window stressed PF was only `1.013`; its later
  windows improved to `1.085` and `1.465`, but the first window failed average
  return, winner-removal, and positive-month gates.
- The best H4/H1 short minimum-window PF was `0.870`. H1/M15 generated more
  signals but the best long and short minimum-window PF values were only `0.698`
  and `0.639` after costs.
- Decision: `V65_NO_PREFINAL_SURVIVOR`. No final-year evaluation was run, no
  sleeve was admitted, and no V59/V60 trade or risk rule changed.
- Result SHA-256:
  `49789c525c96189cd0fcf9772eda9be5544e64a398c5409d0c7f6608c4ed76cf`.
- Metrics SHA-256:
  `c15090cdb709650a435ca31d23dd008eac11dd9fd223584ecc6bd458df1dd646`.

The accepted first milestone remains V59/V60: final-year `1.395/day`, USD
`2,537.35` net, PF `1.976`, USD `152.59` closed DD, and USD `419.18`
conservative buffered floating DD under extra fee stress. V65 shows that simply
compressing the box-breakout clock raises activity without preserving the edge;
the next additive study must change the economic mechanism.

## V66 Roll-Safe COMEX-Spot Basis Residual - 2026-07-20

V66 tested the remaining absolute futures-minus-spot basis hypothesis without
making a network request or paid-data operation. It restored raw COMEX
instrument identity from immutable DBN metadata, restricted rolling centers and
MAD scales to prior bars from the same instrument, and used the complete
Dukascopy M5 stream for broker-side entries, stops, targets, and holding exits.

- The bounded manifest contained `288` preregistered catch-up and fade policies.
- Selection used `47,783` synchronized completed bars, `773` sessions, and `16`
  raw COMEX instruments through `2025-06-30`. The final year was not loaded.
- Zero policies passed development-1, development-2, and confirmation.
- Sparse catch-up policies sometimes showed high PF but had only one to nine
  trades in a year. The maximum minimum-window frequency was `0.146/day`, and
  those denser variants failed economics.
- The best fade minimum-window stressed PF was only `0.621`.
- Decision: `V66_NO_PREFINAL_SURVIVOR`. V59/V60 remain unchanged.
- Result SHA-256:
  `582ac00a75e33363c9cd5d0bfb4e9c2d029b49a4f0fcd881241de86964fc9892`.
- Metrics SHA-256:
  `861d7ef0afa13e308a6e4d7ab053cd9a95106371ed03c263699fcab933368dcb`.

Self-review also rejected a proposed continuation add-on before implementation.
The project failure map correctly states that pyramiding changes frozen Core
risk and splits one economic opportunity into correlated tickets; it cannot be
claimed as independent frequency or new ML labels.

### Untouched forward status

The V24.1 microburst and V26 gap-restart watchers are running and reading the
Capital demo quote stream. As of approximately `2026-07-20T12:28Z`, each had
generated four sealed candidates from about 197,000 unique-millisecond quotes.
The day was still incomplete, so eligible full weekdays remained zero and no
economic outcome was opened. V27 and V42 correctly remain fail-closed pending
component validation. These collectors are now the only genuinely unexposed
high-density evidence path; they require complete forward weekdays and may not
be accelerated by retrospective tuning.

## V67 Automatic Forward Handoff Watch - 2026-07-20

An operational audit found that V24.1 and V26 can publish their sealed stage
artifacts automatically, and V42 already polls V27, but the locked V27 family
evaluator itself is intentionally one-shot. Without an external scheduler, V42
could wait indefinitely after a component stage became available. V67 closes
that scheduling gap without modifying any locked research package.

- Package: `xau-usd/xauusd-fast-research/capital-forward-handoff-watch-v67`.
- V67 invokes the unchanged V27 runner with the current Python interpreter and
  no strategy arguments every 300 seconds.
- V27 still performs all contract, component-artifact, date, hash, admission,
  and portfolio checks. V67 only records child-process health, operational
  inventory counts, and the already-published V27 decision.
- Any child error, missing status, hash mismatch, or contract mismatch produces
  a self-hashed `FAILED_CLOSED` V67 status. Every model, Python, EA, demo, live,
  trade, and broker permission remains false.
- Six focused tests, Ruff lint, and Ruff format verification pass. The first
  real one-shot and the first detached watch cycle both completed successfully.
- V67 contract SHA-256:
  `f267ab2d30339b351a4bfae807019f616a2e53e1c0b71cd19fbe10d2fd0b1ab9`.
- Detached V67 process tree at launch: `uv` PID `38824`, intermediary Python
  PID `29084`, worker Python PID `25544`.
- Existing V24.1 worker PIDs `32220/35740` and V26 process tree
  `30672/4120/27408` remained responsive. The Capital tick source grew to
  `51,304,414` bytes at `2026-07-20T12:44:25Z`.
- The finalized scheduled V67 status at `2026-07-20T12:48:45Z` was
  `HANDOFF_HEALTHY`; V27 remained
  `V27_WAITING_FOR_COMPONENT_VALIDATION`, both eligible-full-weekday counts
  remained zero, and no economics were opened. V67 now prefers a verified V27
  validation or confirmation audit over a stale waiting status, so terminal
  stage decisions cannot be hidden by V27's one-shot status behavior.
- V42 independently refreshed at `2026-07-20T12:43:55Z` with
  `WAITING_FOR_SEALED_STAGE`, zero authority flags, and V27 health correctly
  reported as waiting for component validation.

V67 adds no alpha and does not shorten the 20-validation-day plus
20-confirmation-day evidence requirement. Its sole achievement is making the
sealed forward handoff automatic and observable while preserving every frozen
edge, gate, and drawdown control.

## V68 COMEX Liquidity-Provision Anti-Signal - 2026-07-20

V68 tested whether the terminally failed V44 exhausted-flow transition and V45
sequence-ignition candidates contained a mechanically recoverable reversal
edge. The package was frozen before opening V68 outcomes; it inverted source
direction exactly once, kept the first candidate per UTC date, and preserved
all source thresholds, sessions, stops, targets, holds, costs, and risk.

- Contract SHA-256:
  `89385b6604d6012f5ba16bc383a24d3c302a8b2bf122b3feec746738b5b4fca3`.
- Development selected `479` candidates over `491` eligible weekdays; `475`
  resolved for `0.967413/day`, with `235` longs and `240` shorts.
- Base/stress net was USD `-365.52/-402.40`; base/stress PF was
  `0.4338/0.4006`; both half-stage stress PF values were below `0.425`.
- Positive-month share was zero, top-five-winner-removed stress net was USD
  `-425.19`, closed stress DD was USD `410.41`, and bootstrap p-value was `1.0`.
- Decision: `V68_DEVELOPMENT_FAIL_TERMINAL`. Validation and exam remain sealed.
  Audit SHA-256:
  `d4ee2fa4363e026aa2479909548b140053117406c39a36dc4aa235f8e0152aa7`.

V68 closes the V44/V45 continuation-versus-mirror question: neither direction
has evidence of edge after costs. V59/V60 remain immutable and accepted. Any
next historical expansion must add a materially new causal input; threshold,
quota, direction, or timing rescue on these outcomes is prohibited. V24.1,
V26, V27, V42, and V67 continue as the untouched forward evidence path.
