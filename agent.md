# A1 XAUUSD Authoritative Handoff

Updated: `2026-07-26`

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

## V69 Receipt-Time Innovation Engineering Stop - 2026-07-20

V69 introduced a materially new event-time mechanism: completed 100 ms COMEX
receipt buckets compared with raw Dukascopy quotes strictly before the receipt
decision. It registered exactly 1,000 policies and performed outcome-blind July
2022 calibration only.

- Calibration contained `377,909` causal feature rows over `20` eligible full
  weekdays; `662/1,000` policies met density and direction-balance requirements.
- The deterministic selector froze policy
  `H2000__CM100__IN040__FI30__VO10`: two-second horizon, USD `1.00` COMEX move,
  USD `0.40` directional innovation, `0.30` flow imbalance, and `10` contracts.
- It produced `16` calibration candidates, exactly `0.80/day`, split eight long
  and eight short. No post-decision outcome was opened in calibration.
- Contract SHA-256:
  `747c43a0e476941a08a4e0c87be78efde0c986cf45be8a6fe67cabec61ae4586`.

Development stopped before writing any candidate, label, audit, or economic
result. V69 incorrectly required `ts_recv >= ts_event`; the first violating day
had 18 such records among 93,990 trades, with a minimum `-10.83 ms` difference.
Databento documents `ts_recv` as the primary sort/index timestamp and warns that
publisher clocks may be unsynchronized. V69 is therefore an engineering stop,
not a failed economic test. Its contract remains immutable. The successor must
remove only this invalid publisher-clock assertion, rerun calibration, and
freeze a new contract without changing policy grids, execution, or gates.

## V70 Corrected Receipt-Time Innovation - 2026-07-20

V70 removed only V69's invalid publisher-clock ordering assertion, explicitly
used `ts_recv` as the primary source clock, and counted rows where publisher
event time exceeded receipt time. All 1,000 policies, calibration dates,
thresholds, execution geometry, costs, splits, and gates remained unchanged.

- Outcome-blind calibration reproduced the same `377,909` features, `662`
  eligible policies, and selected policy `H2000__CM100__IN040__FI30__VO10`.
- Contract SHA-256:
  `cc71627134dd00c051756cbe9587686717ad70b49245bff071032a01325d297a`.
- Development recorded `78,822` publisher-clock-lead rows without filtering
  them and resolved `385` trades over `491` eligible weekdays (`0.784114/day`).
- Direction balance was `184` longs and `201` shorts. Base net/PF was USD
  `18.71`/`1.054`; stress net/PF was USD `-21.45`/`0.941`.
- First/second-half stress PF was `0.978/0.906`; positive months were `43.48%`;
  winner-removed stress net was USD `-54.95`; closed DD was USD `37.55`; and
  bootstrap p-value was `1.0`.
- Decision: `V70_DEVELOPMENT_FAIL_TERMINAL`. Audit SHA-256:
  `66d9fd77b0d671188b2d8b335189d32808bcc6239d13c050046af1b54e36e867`.

Validation and exam remain sealed. V70 is not an admitted sleeve despite its
useful density and low drawdown, because realistic costs remove its edge and
both chronological halves fail. No clock, horizon, threshold, direction, exit,
cost, or quota rescue is allowed on the exposed family. V59/V60 remain the
accepted control, while V24.1/V26/V27/V42/V67 continue forward collection.

## V71 COMEX Round-Barrier Rejection - 2026-07-20

V71 tested the previously unused hypothesis that mechanically fixed COMEX round
prices concentrate liquidity and create a causal rejection signal. It
registered exactly 1,000 spacing, window, probe, rejection, and opposite-flow
policies before calibration.

- Outcome-blind calibration had `199,361` material feature rows over `20`
  eligible weekdays and selected `LS100__LB120__PR040__RJ080__FI25` at exactly
  `0.80/day`, with nine longs and seven shorts.
- The selected rule used USD `10` barriers, a `120`-second lookback, USD `0.40`
  probe, USD `0.80` rejection, and at least `0.25` opposite flow.
- Contract SHA-256:
  `5d22a4a05669f5be0eb3a1d4618387e7431c3a75f20eeb56425d20071ba7e263`.
- Development resolved `383` trades over `491` weekdays (`0.780041/day`), with
  `203` longs and `180` shorts.
- Base/stress net was USD `-238.78/-268.00`; base/stress PF was
  `0.512/0.473`; first/second-half stress PF was `0.430/0.521`.
- Positive months were `13.04%`, winner-removed stress net was USD `-284.24`,
  closed stress DD was USD `282.92`, and bootstrap p-value was `1.0`.
- Decision: `V71_DEVELOPMENT_FAIL_TERMINAL`. Audit SHA-256:
  `f7fdcf5bdb9df9c6be308418f1e2c2f8d534d747b84dad4f16ed60d77a67f9b0`.

Validation and exam remain sealed. Fixed round-barrier rejection is terminal;
its breakout mirror, spacing, window, thresholds, direction, exit, costs, and
quota may not be rescued on these outcomes. V59/V60 remain the accepted control
and the forward collectors continue independently.

## V72 Raw Silver Event-Time Catch-Up - 2026-07-20

V72 tested raw synchronized Dukascopy XAGUSD-to-XAUUSD event-time catch-up as a
new causal information class. Its source audit validated `144` frozen
symbol-month manifests, `105,216` hourly rows, and `370,219,394` declared ticks
from July 2018 through June 2024. July 2018 calibration opened no outcomes,
registered exactly `1,000` policies, and selected
`H01000__XM040__IN025__RR050__QC05` at `17/21 = 0.809524/day`, with five longs
and twelve shorts. Contract SHA-256:
`1f95f6442f037aa71b7c33886aa56722cefbab5d485c1285dd10127a1003cc90`.

Development resolved `693` trades over `745` eligible weekdays
(`0.930201/day`), with `315` longs and `378` shorts. Base/stress net was USD
`-491.63/-542.61`; base/stress PF was `0.2973/0.2646`; first/second-half stress
PF was `0.2293/0.2892`; positive-day share was `22.01%`; no month was positive;
winner-removed stress net was USD `-561.59`; stressed DD was USD `543.21`; and
bootstrap p-value was `1.0`.

Decision: `V72_DEVELOPMENT_FAIL_TERMINAL`. All later outcomes remain sealed and
the untouched July 2024-June 2026 exam source was not acquired. Do not tune or
rescue V72. A V73 anti-signal successor may invert direction exactly once while
inheriting the locked event policy and execution, and must begin in the still
unopened July 2021 period. V59/V60 remain immutable and accepted.

## V73 Fixed Silver Anti-Signal - 2026-07-20

V73 inherited V72 policy `H01000__XM040__IN025__RR050__QC05`, every event time,
the one-per-day quota, execution geometry, costs, and economic gates. It inverted
direction exactly once and began after V72's exposed cutoff. Contract SHA-256:
`c0949fe88fd157df89bf9a06b96f5fd2ee9f6eaefc2fb6b4330c93807c998ee7`.

Fresh development resolved `242` trades over `257` eligible weekdays
(`0.941634/day`), split `136` long and `106` short. Base/stress net was USD
`-136.62/-154.25`; base/stress PF was `0.3987/0.3554`; first/second-half stress
PF was `0.3359/0.3730`; no month was positive; winner-removed stress net was USD
`-166.38`; stressed DD was USD `154.25`; and bootstrap p-value was `1.0`.

Decision: `V73_DEVELOPMENT_FAIL_TERMINAL`. Confirmation, validation, and exam
remain sealed. V72/V73 retire both directional interpretations of the fixed raw
silver event family. No same-family mirror, threshold, response, timing, exit,
cost, or quota rescue is permitted. V59/V60 remain immutable and accepted.

## V74 Raw DXY Event-Time Catch-Up - 2026-07-20

V74 tested a raw one-to-twenty-second DXY lead and expected inverse XAU response.
The source audit covered `180` frozen symbol-months, `131,424` hourly rows, and
`447,967,303` declared ticks through June 2026. Outcome-blind January 2019
calibration registered `1,000` policies and selected
`H01000__DM010__IN005__RR000__QC02` at `18/22 = 0.818182/day`, exactly nine long
and nine short. Contract SHA-256:
`8e0ec9b0dd27282f9186976d97bd709d919764b34f0478a218aaa82ee78ca28d`.

Development resolved `710` trades over `871` eligible weekdays
(`0.815155/day`), with `368` longs and `342` shorts. Base/stress net was USD
`-462.04/-516.71`; base/stress PF was `0.3904/0.3519`; first/second-half stress
PF was `0.3230/0.3822`; no month was positive; winner-removed stress net was USD
`-541.04`; stressed DD was USD `517.76`; and bootstrap p-value was `1.0`.

Decision: `V74_DEVELOPMENT_FAIL_TERMINAL`. Later stages remain sealed. Do not
tune V74. One fixed direction inversion may start on the untouched July 2022
period; no additional DXY threshold, timing, response, exit, cost, or quota reuse
is permitted. V59/V60 remain immutable and accepted.

## V75 Fixed DXY Anti-Signal - 2026-07-20

V75 inherited V74 policy `H01000__DM010__IN005__RR000__QC02`, every event time,
the one-per-day quota, execution geometry, costs, and economic gates. It inverted
direction exactly once and began after V74's exposed cutoff. Contract SHA-256:
`9384d5c77a82346f057a53759d4dfc200c54531c7d49c1349634965875b6d816`.

Fresh development resolved `231` trades over `256` eligible weekdays
(`0.902344/day`), split `115` long and `116` short. Base/stress net was USD
`-131.42/-148.20`; base/stress PF was `0.4445/0.4025`; first/second-half stress
PF was `0.4536/0.3592`; positive-day share was `27.34%`; one of 12 months was
positive; winner-removed stress net was USD `-166.78`; stressed DD was USD
`153.99`; and bootstrap p-value was `1.0`.

Decision: `V75_DEVELOPMENT_FAIL_TERMINAL`. Confirmation, validation, and exam
remain sealed. V74/V75 retire both directional interpretations of the fixed raw
DXY event family. No same-family mirror, threshold, response, timing, exit,
cost, or quota rescue is permitted. V59/V60 remain immutable and accepted.

## V76 Raw Treasury-Bond Event-Time Catch-Up - 2026-07-20

V76 tested a raw one-to-twenty-second U.S. Treasury bond price lead and expected
same-direction XAU response. The source audit covered `180` frozen symbol-months,
`131,424` hourly rows, and `445,583,861` declared ticks through June 2026.
Outcome-blind January 2019 calibration registered `1,000` policies and selected
`H02000__BM005__IN005__RR000__QC05` at `9/9 = 1.0/day`, with seven long and two
short candidates. Contract SHA-256:
`56151a77385d55c6a19c577016075fa92b17db137e845695b472bd5e78b0f681`.

Development resolved `730` trades over `828` eligible weekdays
(`0.881643/day`), with exactly `365` longs and `365` shorts. Base/stress net was
USD `-512.26/-567.63`; base/stress PF was `0.3301/0.2952`;
first/second-half stress PF was `0.2233/0.3668`; positive-day share was `23.43%`;
no month was positive; winner-removed stress net was USD `-584.37`; stressed DD
was USD `567.88`; and bootstrap p-value was `1.0`.

Decision: `V76_DEVELOPMENT_FAIL_TERMINAL`. Later stages remain sealed. Do not
tune V76. One fixed direction inversion may start on the untouched July 2022
period; no additional Treasury-bond threshold, timing, response, exit, cost, or
quota reuse is permitted. V59/V60 remain immutable and accepted.

## V77 Fixed Treasury-Bond Anti-Signal - 2026-07-20

V77 inherited V76 policy `H02000__BM005__IN005__RR000__QC05`, every event time,
the one-per-day quota, execution geometry, costs, and economic gates. It inverted
direction exactly once and began after V76's exposed cutoff. Contract SHA-256:
`51450419d51bb4b5bc983f313269b1f7980dcf14c6b6adf2c232f8c095d2b3af`.

Fresh development resolved `228` trades over `253` eligible weekdays
(`0.901186/day`), split `109` long and `119` short. Base/stress net was USD
`-188.78/-204.96`; base/stress PF was `0.2677/0.2406`; first/second-half stress
PF was `0.2031/0.2776`; positive-day share was `22.13%`; no month was positive;
winner-removed stress net was USD `-216.73`; stressed DD was USD `210.51`; and
bootstrap p-value was `1.0`.

Decision: `V77_DEVELOPMENT_FAIL_TERMINAL`. Confirmation, validation, and exam
remain sealed. V76/V77 retire both directional interpretations of the fixed raw
Treasury-bond event family. No same-family mirror, threshold, response, timing,
exit, cost, or quota rescue is permitted. V59/V60 remain immutable and accepted.

## V78 Raw FX Dollar-Consensus Event-Time - 2026-07-20

V78 required synchronized EURUSD and USDJPY moves to agree on dollar direction
before a causal XAU candidate existed. The source audit covered `216` frozen
symbol-months, `157,824` hourly rows, and `608,967,406` declared ticks through
June 2024. Outcome-blind July-August 2018 calibration registered `1,000` policies
and selected `H01000__LM025__CS050__RR000__QC05` at `37/44 = 0.840909/day`, with
21 long and 16 short candidates. Contract SHA-256:
`92dea393027f32e6d9e0e05220033fd63aa777f027b9f1c650ec6bb9485db091`.

Development resolved `613` trades over `723` eligible weekdays
(`0.847856/day`), with `322` longs and `291` shorts. Base/stress net was USD
`-406.33/-452.66`; base/stress PF was `0.3394/0.3023`; first/second-half stress
PF was `0.2499/0.3410`; positive-day share was `21.58%`; no month was positive;
winner-removed stress net was USD `-474.61`; stressed DD was USD `454.91`; and
bootstrap p-value was `1.0`.

Decision: `V78_DEVELOPMENT_FAIL_TERMINAL`. Later stages remain sealed. Do not
tune V78. One fixed direction inversion may start on the untouched July 2021
period; no additional FX-consensus threshold, timing, response, exit, cost, or
quota reuse is permitted. V59/V60 remain immutable and accepted.

## V79 Fixed FX Dollar-Consensus Anti-Signal - 2026-07-20

V79 inherited V78 policy `H01000__LM025__CS050__RR000__QC05`, every event time,
the one-per-day quota, execution geometry, costs, and economic gates. It inverted
direction exactly once and began after V78's exposed cutoff. Contract SHA-256:
`471f5c9512d4ceff2c755543c5cbf91af154d15c17dceef5f6b34e7c9e615831`.

Fresh development resolved `242` trades over `257` eligible weekdays
(`0.941634/day`), split `124` long and `118` short. Base/stress net was USD
`-147.17/-165.02`; base/stress PF was `0.3985/0.3570`; first/second-half stress
PF was `0.3291/0.3885`; positive-day share was `30.74%`; no month was positive;
winner-removed stress net was USD `-179.03`; stressed DD was USD `165.47`; and
bootstrap p-value was `1.0`.

Decision: `V79_DEVELOPMENT_FAIL_TERMINAL`. Confirmation and validation remain
sealed. V78/V79 retire both directions of immediate entry after the fixed raw FX
consensus event. No same-family mirror, threshold, response, horizon, immediate
entry, exit, cost, or quota rescue is permitted. V59/V60 remain immutable and
accepted.

## V80 FX Consensus Transmission-Retracement - 2026-07-20

V80 inherited V78's locked FX-consensus event but required XAU to transmit in
the implied direction and then retrace before a candidate could exist.
Outcome-blind July-August 2022 calibration registered exactly 100 timing
policies and selected `TR150__RF075__MW010` at `43/44 = 0.977273/day`, split 21
long and 22 short. Contract SHA-256:
`2a0a7f897440c71c0dec6caa1b010f11cca536755ca880456d5d986ae375dab5`.

Fresh development from September 2022 through June 2023 resolved `202` trades
over `214` eligible weekdays (`0.943925/day`), split 105 long and 97 short.
Base/stress net was USD `-132.81/-149.24`; base/stress PF was
`0.4813/0.4417`; first/second-half stress PF was `0.3559/0.5198`; positive-day
share was `27.10%`; no month was positive; winner-removed stress net was USD
`-173.83`; stressed DD was USD `150.33`; and bootstrap p-value was `1.0`.

Decision: `V80_DEVELOPMENT_FAIL_TERMINAL`. Validation remains sealed. Do not
tune or rescue V80. V78-V80 retire the locked FX-consensus source event under
immediate, mirrored, and fast transmission-retracement interpretations. V59/V60
remain immutable and accepted; the forward collectors continue independently.

## V60 Core Demo Execution On A2 - 2026-07-21

The owner explicitly authorized broker-action demo execution on A2 account
`1033030` and waived a shadow-only waiting period. A new additive execution
package is present at
`xau-usd/xauusd-fast-research/v60-core-demo-executor-v1`. It consumes only the
parity-checked prospective candidate streams for the five frozen Core
specialists and sends fixed `0.01` lot XAUUSD orders through
`C:\MT5PortableTier1BestEA\terminal64.exe`.

- Runtime: `C:\MT5PortableTier1BestEA\MQL5\Files\v60_core_demo_v1`.
- Status: `status.json`; persistent deduplication/risk state: `state.json`;
  append-only decisions and broker results: `events.jsonl`.
- Account guard: exact login `1033030`, exact server
  `Capital.ComMena-Demo`, and required `Demo` marker. Live is always refused.
- Core magics: R1 box `960101`, R1 pullback `960102`, R2 `960201`, R3
  `960301`, R4 `960401`, and R5 `960501`.
- R5 accepts only attempt `23925` with exact risk weight `1.0`; fractional
  broker-inexpressible V59 rows remain rejected.
- V60 controls: maximum ten Core positions, USD `225/180` closed-drawdown
  suspend/resume hysteresis, and USD `449.7675` whole-account floating hard
  stop for new entries. Every order carries a broker-side stop; target/horizon
  behavior follows the candidate family.
- Activation equity was USD `3,599.04`. Activation contained zero XAUUSD
  positions, zero pending orders, and zero prospective Core candidates.
- The process was launched hidden with `start_executor.ps1`; use that launcher
  again after restart because it refuses a duplicate running process.
- Focused tests: `5 passed`; Ruff and Python compilation pass. A real broker
  `order_check` accepted the intended `0.01` lot request under FOK filling.

This is actual demo broker-action readiness, not shadow-only. It is explicitly
the **five-specialist Core**, not the full V59/V60 combined portfolio: the four
V59 add-on sleeves (`V7_SWING_HEALTH`, `V8_RETEST_HEALTH`, `V25_CHOP`, and
`V57_BREAK_SWING_H4ADX_HIGH`) still lack complete causal forward adapters and
must not be claimed as attached.

## V60 Full Canonical Demo Portfolio On Account 1033030 - 2026-07-21

The Core-only package above is superseded. Do not start
`v60-core-demo-executor-v1`. The active package is
`xau-usd/xauusd-fast-research/v60-canonical-demo-portfolio-v2`, covering six
Core streams across the five regime owners plus the four canonical V59 add-on
sleeves. It uses deterministic rules only. ML runtime, model handoff, ranker,
prediction observer, and ML shadow are all unauthorized and absent from the
active chart profile.

- Exact account: `1033030`, `Capital.ComMena-Demo`, currency `AED`.
- Terminal: `C:\MT5PortableTier1BestEA\terminal64.exe /portable`; current PID
  at handoff was `41384`. It is the only MT5 terminal process.
- Runtime: `C:\MT5PortableTier1BestEA\MQL5\Files\v60_canonical_demo_v2`.
- Status: `status.json`; feed status: `feed_status.json`; persistent state:
  `state.json`; decisions/orders: `events.jsonl`.
- Healthy status is `ACTIVE_DEMO_BROKER_ACTION`; execution is enabled and live
  authorization remains false.
- Start/restart with
  `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\start_portfolio.ps1`
  from the package directory. This starts one `run_feeds.py` process and one
  `run_portfolio.py` process hidden and refuses duplicate launchers.
- Current launcher/worker PIDs at handoff were feed `2856/42544` and executor
  `34604/27756`. PIDs are informational and will change after restart.
- The `Default` MT5 profile has six charts: `AccountEquityGuardianShadow`,
  `Account1DailyProfitFloorGuardian`, `XauProspectiveTelemetryCollector`, and
  three observer-only `A1XauM5MomentumContinuationExecutor` sensors with run
  IDs `V60_V2_BREAK_AND_RUN_SENSOR`, `V60_V2_DOWNSIDE_RETEST_SENSOR`, and
  `V60_V2_OPENING_REVERSAL_SENSOR`.
- Both legacy `Phase2ExperimentalDemoExecutor` charts and all ML-shadow flags
  were removed. New collector/sensor charts have `expertmode=0` and
  `InpAllowDemoTrading=false` where applicable.
- Terminal-wide Algo Trading is enabled for the Python executor. Use
  `set_terminal_algo_trading.ps1` only while the verified terminal is stopped;
  it backs up `Config\common.ini` before a change.
- Account balance/equity was `3627.19 AED`, correctly treated as approximately
  `987.66 USD` using `3.6725 AED/USD`. The old Core-v1 note that called the AED
  figure USD was incorrect and must not be reused.
- XAUUSD contract size is `100`; fixed `0.01` lot therefore equals one ounce.
  Broker `order_check` passed long and short geometry under FOK filling. No test
  order was sent and activation had zero XAUUSD positions.
- All eight required feed groups are healthy: R1 box, R1 pullback, R2/R3, R4,
  R5 components, R5 causal resolver, R5 causal router, and add-ons. V25 used
  `779,250` recent broker ticks with `549` quality M5 rows at activation.
- Historical selector parity is exact for V7, V8, and V57; V25 frozen identity,
  origin attempt `39583`, and geometry are verified. Deployment tests were
  `13 passed`; the four frozen source suites added `16 passed`.
- Risk controls include guardian halt-file enforcement, fixed `0.01` lot,
  maximum two add-on positions, USD `45` add-on concurrent initial risk,
  maximum two add-on entries per UTC day, USD `225/180` drawdown hysteresis,
  USD `300` combined closed-drawdown hard stop, USD `449.7675` whole-account
  floating hard stop, and emergency closure of canonical positions at either
  hard stop. The armed MT5 daily guardian additionally enforces its AED rules.

## Causal Candidate Quality ML Step 1 Rule Freeze - 2026-07-22

Step 1 is frozen under
`xau-usd/xauusd-fast-research/causal-candidate-quality-ml-v1`. The first ML
task is a candidate-quality meta-labeler: it may rank deterministic specialist
candidates as `TAKE`, `SKIP`, or `ABSTAIN`, but it may not invent entries,
change trade geometry or risk, override portfolio controls, or interact with
the active demo runtime.

- The primary target is expected stressed net R; the secondary target is the
  probability that stressed net R is positive.
- Canonical specialist candidates are the primary population. Research
  negatives, COMEX research rows, and prospective Capital.com rows remain
  explicitly separate populations.
- Historical data through `2026-06-30` is development evidence only. It cannot
  provide prospective proof or authorize execution.
- The V59/V60 benchmark is byte-bound to five frozen artifacts and remains
  immutable: `2,194` combined trades, `1.394636` final-year trades per day,
  USD `2,537.35` final-year net, profit factor `1.975779`, USD `152.59`
  closed-trade drawdown, and USD `412.06` buffered floating drawdown.
- The full-history research budget is six fixed model/feature pipelines per
  outer fold. Two COMEX-inclusive ablations are permitted only in eligible
  post-2022 folds and can never authorize deployment.
- Splits, feature clocks, labels, thresholds, costs, drawdown gates, and
  prospective confirmation rules are preregistered. There is no frequency
  quota and no threshold search to force trades.
- Contract lock SHA-256:
  `12c7e01147abf52cbf5855a5d3aab377aa1e98b8d56867f336a137bda0d31183`.
  The lock records that no economic outcomes were opened, no model was fitted,
  and no runtime was changed at lock time.
- Contract verification has `6 passed` tests. The next stage is a
  metadata-only data and candidate audit; it must not open economic outcomes
  or train a model.

## C-to-D Bulk Research Data Migration - 2026-07-22

The bulk historical/research data was physically moved from `C:` to
`D:\AlgoTradingData\C_DRIVE`. Existing absolute `C:` paths remain valid through
35 verified NTFS directory junctions, so research code and MT5 tooling do not
need path rewrites. New writes through one of those old paths are stored on
`D:` automatically.

- Migrated and verified: 738,275 files totaling 203.13 GB. This includes the
  Dukascopy, COMEX, tokenized-gold, SGE, CFTC, CBOE, SPDR, and HistData local
  foundations; Phase 0/Phase 1 and Forex data/outputs; the router-audit output
  cache; inactive MT5 tester histories/reports; and legacy roaming MetaQuotes
  history.
- The active `C:\MT5PortableTier1BestEA` installation and its live `Bases`
  directory were intentionally not moved.
- Verification used Robocopy zero-difference checks, exact file counts and
  byte totals, and non-empty SHA-256 tree hashes for all 35 entries. Two new
  hourly Dukascopy context files created during verification were quiesced,
  copied, and individually SHA-256 matched before cutover.
- The old source names now resolve to targets below
  `D:\AlgoTradingData\C_DRIVE`. The complete manifest, copy logs, tree hashes,
  junction checks, deletion audit, and purge results are under
  `D:\AlgoTradingData\migration`.
- A nested Phase 0 `outputs\matrix_results` link was caught by the final Git
  audit. Its 190 tracked files were recovered from an inactive worktree only
  after all 190 Git blob hashes matched `HEAD`; destination SHA-256 checks pass,
  and the directory has no staged or unstaged Git diff.
- The shell safety layer would not remove the final empty rollback directory
  shells. Thirty-five `*.__codex_c_backup_20260722` directories may therefore
  remain, but they contain zero items and consume no material space.
- Free space after migration was approximately 233.46 GB on `C:` and 294.22 GB
  on `D:`. Do not disconnect, reformat, or rename `D:` while these junctions
  are in use.
- Post-migration verification: causal candidate-quality ML contract `6 passed`;
  V60 portfolio `13 passed`. The deterministic portfolio workers were restarted
  and are healthy on account `1033030`: `ACTIVE_DEMO_BROKER_ACTION`, execution
  enabled, all feeds healthy, and both ML runtime and ML shadow unauthorized.

## Causal Candidate Quality ML Step 2 Audit - 2026-07-22

The outcome-blind metadata audit is complete under
`xau-usd/xauusd-fast-research/causal-candidate-quality-ml-v1/outputs/step_2`.
Its decision is `STEP_2_METADATA_AUDIT_COMPLETE_REPAIR_REQUIRED`. The audit did
not open economic outcomes, build labels or features, fit a model or threshold,
simulate a portfolio, or change the active demo runtime.

- The canonical registry contains `3,752` unique candidates: R1 `558`, R2
  `168`, R3 `490`, R4 `521`, R5 `330`, V25 `131`, V7 `587`, V8 `280`, and
  V57 `687`. It has `2,043` long and `1,709` short candidates, no duplicate
  candidate IDs, and one primary action identity per candidate.
- V59 add-on policy lineage reconciles exactly to V57 source IDs: `1,685`
  decisions, `1,379` accepted, and `306` rejected. R1 single-position policy
  records `145` decisions, `31` accepted, and `114` rejected.
- All `3,752` candidates have an entry-eligible timestamp and `3,194` have a
  signal/decision-time proxy. R1 lacks distinct signal/decision clocks for
  `558` candidates. No row currently has `source_available_at` or
  `feature_cutoff_time`, so zero rows yet satisfy the complete preregistered
  pre-label causal-clock contract.
- R5 is presently a post-selection trade ledger, not a complete pre-policy
  candidate ledger. Fully explicit action geometry is available for only
  `521` canonical rows. These are data-contract gaps, not evidence that more
  raw market history is needed.
- The duplicate/episode census finds `2,940` exact-time-direction episode
  proxies. Its more conservative non-transitive 36-hour grouping gives `853`
  provisional episodes, which is the current outcome-blind effective-sample
  upper bound. Final episode weights and serial effective size remain unlocked.
- Separate research populations contain `73,116` spot action rows over
  `28,432` candidate-directions and `44,418` COMEX action rows over `23,290`
  candidate-directions. Alternative actions from the same event are siblings,
  not independent training examples, and remain outside the canonical count.
- Independent verification recalculated all ten generated artifact hashes with
  zero failures and confirmed all seven required reports. Verification also
  passed `11` tests, Ruff format/check, Python compilation, and the unchanged
  Step 1 lock with all six contract tests.
- The only authorized next stage is
  `STEP_2A_METADATA_REPAIR_AND_CANDIDATE_ADAPTERS`: populate and validate causal
  availability clocks, recover R1 decision timing, reconstruct R5 pre-policy
  candidate lineage, normalize planned action geometry and hold intervals, and
  establish stable structural episode anchors. Labels, feature values, and ML
  fitting remain forbidden until that repair passes.

## Causal Candidate Quality ML Step 2A Repair - 2026-07-22

Step 2A is complete under
`xau-usd/xauusd-fast-research/causal-candidate-quality-ml-v1/outputs/step_2a`.
Its decision is `STEP_2A_METADATA_REPAIR_COMPLETE`. The run remained
outcome-blind: it did not build labels or feature values, fit a model or
threshold, simulate a portfolio, or change the active demo runtime.

- All `3,752` canonical candidates now have complete causal clocks and frozen
  action geometry. The clock audit has zero ordering violations and the
  geometry audit passes for every canonical family.
- Historical portfolio acceptance reconciles exactly to `2,194` candidates.
  Acceptance/rejection remains policy evidence, never an economic label.
- Native R1 reconstruction retains `3,951` pre-trade guard decisions: `558`
  accepted and `3,393` rejected. All `558` canonical R1 rows reconcile exactly
  to the original tagged R1 ledger. MT5 tester timestamps are frozen as
  UTC-like after outcome-blind price-clock discrimination against Dukascopy.
- The R1 strategies remain barrier-only with no time stop. A 90-day cap is used
  only to bound label observation and pre-label purging; it is not a forced
  trade exit.
- R5 now has its true `799`-row pre-policy population: `330` router-selected,
  `469` router-rejected, and `10` broker-executable at the frozen account size.
- The broader journey retains `117,534` registered action rows representing
  `51,722` unique candidate-directions and `40,077` structural events. Sibling
  actions are inverse-count weighted and cannot masquerade as independent
  training examples.
- Another `115` historical trade-ledger files, `665,878` physical/footer rows,
  and approximately 48.1 MB are SHA-256 cataloged for provenance. They are not
  authorized for direct model ingestion until a semantic dedup adapter proves
  which rows are unique market decisions rather than strategy-version or
  portfolio derivatives.
- Canonical weighting is locked before labels: `3,489` exact-decision
  structural episodes and `639` conservative non-transitive overlap episodes.
  Serial effective sample size remains deferred until labels exist.
- A clean rerun reproduced the exact artifact-manifest SHA-256
  `5a4ceec23a803e0c675379d25d29fe6a7b6b62288fe39fb6204ee5434f6ffe1d`.
  The next authorized stage is `STEP_2B_DATASET_AND_FEATURE_CONTRACT_LOCK`.
  It must freeze label replay, causal features, populations, deduplication,
  splits, weighting, and missing-data policy before any outcome is opened.

## Causal Candidate Quality ML Step 2B Contract - 2026-07-22

Step 2B is complete under
`xau-usd/xauusd-fast-research/causal-candidate-quality-ml-v1/outputs/step_2b`.
Its decision is `STEP_2B_DATASET_FEATURE_CONTRACT_LOCKED`. The verified
definition-contract SHA-256 is
`964eebd668d5291be94d1339d102a55101d0ec561094edbbf9d849c99a4bfc5a`.
No outcome, feature value, model, threshold, portfolio result, or runtime state
was opened or changed.

- The primary fit remains all `3,752` canonical candidates, including
  historically rejected candidates. Rejection is never a loss label and
  historical policy state is not a predictor.
- All broader failure evidence remains retained: `117,534` journey action rows,
  `51,722` unique candidate-directions, and `40,077` source events. Its frozen
  diagnostic weight sums to one per source event. This library is labeled and
  reported separately and cannot dominate or rescue the canonical V1 fit.
- The `115` additional archived trade ledgers remain SHA-cataloged provenance
  quarantine until source-specific semantic adapters prove row identity. They
  are not claimed as independent model examples.
- The earlier ten-year feature-cache boundary was corrected. Complete frozen
  Dukascopy XAUUSD monthly manifests cover January 2010 through June 2026, so
  the `241` pre-July-2016 canonical candidates remain eligible for raw bid/ask
  replay. DOLLARIDXUSD and USTBONDTRUSD are bound from January 2019 through June
  2026 for causal cross-asset features.
- The lock verifies `378` monthly manifests and the exact physical presence of
  `276,024` hourly source files. Monthly aggregate raw-file digests are bound.
  Incomplete EURUSD, GBPUSD, USDJPY, and XAGUSD histories were removed from V1
  rather than hidden by multi-year imputation.
- Label replay is source-side correct: long Ask/Bid, short Bid/Ask, observed
  stop slippage, locked targets, first quote after fixed horizons, no M5 or
  nearest-time fallback, no spread double charge, USD `0.30` ticket cost, USD
  `0.35` holding cost per 24 hours, and an additional `0.05R` stress charge.
- Source-native initial risk is frozen by family. R1 uses native stop points;
  R2/R3/R4/R5 use source-emitted pre-trade signal ATR; V7/V8/V25/V57 use the
  V57 pre-trade risk field at one ounce. R1's 90-day cap is censoring only.
- The exact ordered feature surface contains `59` raw columns across three
  primary nested blocks and one COMEX research-only block. IDs, attempts,
  versions, historical decisions, exact dates/timestamps, outcomes, nearest
  joins, forming bars, full-history normalization, and outcome-selected
  features are prohibited.
- Six purged expanding July-to-July folds are locked. Outcome-blind fit counts
  are `702`, `1,058`, `1,505`, `1,756`, `2,299`, and `2,853`; calibration counts
  are `140`, `257`, `101`, `287`, `194`, and `295`; test counts are `476`,
  `289`, `506`, `443`, `645`, and `550`. Actual label-end purging in Step 3 may
  only reduce these counts.
- Verification passes `25` tests, Ruff, Python compilation, artifact hash
  recalculation, and an idempotent rerun. The artifact-manifest SHA-256 is
  `a65e2a338e8df2398fe150e93e1323a12dc081c28f6359455cd2621b9b1b57be`.
- The only authorized next stage is
  `STEP_3_COUNTERFACTUAL_LABEL_AND_CAUSAL_FEATURE_BUILD`. It may build labels
  and the locked causal features, but model fitting, threshold fitting,
  portfolio simulation, ML shadow, demo attachment, and broker action remain
  forbidden.

## Causal Candidate Quality ML Step 3 Build - 2026-07-22

Step 3 is complete under
`xau-usd/xauusd-fast-research/causal-candidate-quality-ml-v1/outputs/step_3`.
Its decision is `STEP_3_COUNTERFACTUAL_LABEL_AND_CAUSAL_FEATURE_BUILD_COMPLETE`.
The run used the locked Step 2B definition SHA-256
`964eebd668d5291be94d1339d102a55101d0ec561094edbbf9d849c99a4bfc5a`.
No model, threshold, portfolio simulation, demo attachment, or runtime change
was performed.

- All `3,752` canonical candidates received resolved raw bid/ask labels: `1,664`
  stressed winners and `2,088` stressed failures. This includes all `1,558`
  historically rejected canonical candidates; `671` of those rejected rows are
  counterfactual winners, proving that historical rejection was not used as a
  loss label.
- The separate journey library contains `117,534` action rows. It has `116,444`
  resolved labels: `41,442` stressed winners and `75,002` stressed failures.
  Another `1,090` rows have no quote within the conservative horizon gap and
  remain explicitly unresolved. Journey rows do not enter or rescue the V1
  primary fit.
- The canonical matrix has the exact `59` locked raw feature columns. Mandatory
  XAU lookbacks pass for `3,024` rows; `728` rows fail closed with
  `ABSTAIN_MISSING_MANDATORY_XAU`, chiefly around unavailable completed 4h/24h
  market-closure lookbacks. No missing mandatory value is silently imputed into
  an executable prediction.
- Actual label-end purging preserved every locked test count and reduced fit by
  one row in each of folds F2023, F2024, and F2025. Structural siblings never
  cross a split.
- The effective-sample report contains `3,489` resolved structural episodes,
  Kish effective size `3,600.98`, serial effective size `1,321.94`, and
  conservative effective size `1,321.94`.
- The build hash-verified every source file it opened: `66,663` XAUUSD raw
  hours with `441,309,114` ticks, `60,070` cross-asset raw hours, and `984`
  COMEX GC daily files. No new or paid data was acquired.
- Final verification passes `39` package tests, Ruff, Python compilation, all
  `11` artifact hashes, exact identities and row counts, label/cost/stress
  formulas, causal clocks, feature order, finite-value checks, and split
  sibling isolation. The artifact-manifest SHA-256 is
  `5dbbdc8189524b18a230eebe8011dcf6b64e0a7eb502f8e24ec4b4bd7562bedc`.
- The next research stage is
  `STEP_4_MODEL_FIT_AND_LOCKED_WALK_FORWARD_EVALUATION`. It must train only on
  eligible historical fit rows, calibrate only in the locked calibration
  windows, evaluate once on each untouched test era, retain abstention, and
  keep journey evidence separate from the canonical primary fit.

## Causal Candidate Quality ML Step 4 Evaluation - 2026-07-22

Step 4 is complete under
`xau-usd/xauusd-fast-research/causal-candidate-quality-ml-v1/outputs/step_4`.
The locked evidence decision is `MODEL_EVIDENCE_GATE_FAIL`. This is a valid
research completion, not an implementation failure: the preregistered model was
fit and tested, and it did not prove incremental value.

- A pre-model packaging audit corrected Step 3's combined table from duplicate
  `family_id_x`/`family_id_y` fields to one exact locked `family_id`. Step 3 was
  fully rebuilt and verified before the model contract was locked.
- The final Step 4 definition-contract SHA-256 is
  `fffae17f6162b1092b672f81259cfe969ec08b0d45d114a8e1fc6cacfd3d39e8`.
  It binds the final Step 3 inputs, Python implementation hashes,
  scikit-learn `1.8.0`, four fixed model specifications, six folds, threshold
  policy, 10,000-resample bootstrap, and acceptance gates before model fitting.
- The primary `HGB_B12_PRIMARY` model used the 40 deterministic and XAU causal
  features. Across six untouched test eras it evaluated `2,368` candidates and
  `2,275` structural episodes. Weighted ROC AUC is `0.5193`, with five-weekday
  block-bootstrap 95% interval `0.4922` to `0.5474`.
- Every primary calibration window chose threshold `0.0`. All `2,368`
  candidates were retained, so selected-minus-baseline stressed EV is exactly
  `0.0R`. ML did not identify a defensible filter.
- The underlying eligible candidate baseline remains positive: weighted mean
  stressed outcome `0.2510R`, weighted profit factor `1.4142`, weighted R sum
  `570.99R`, approximately `1.51` raw candidates and `1.45` structural episodes
  per weekday. The weighted `74.69R` drawdown is a candidate-quality sequence
  diagnostic, not shared-account P&L or account equity drawdown.
- Primary per-fold AUCs are `0.4901`, `0.5490`, `0.5233`, `0.4309`, `0.5121`,
  and `0.5719`. The probability model is unstable across eras and its weighted
  Brier score `0.2558` is worse than the pooled fold-prior comparator `0.2507`.
- Logistic B1+B2 AUC is `0.5173`, deterministic-only HGB AUC is `0.4782`, and
  cross-asset HGB AUC is `0.4626`. These preregistered challengers and ablations
  cannot rescue the failed primary gate.
- The primary passed `9/12` checks. It failed minimum pooled AUC, AUC confidence
  bound above random, and positive confidence-bound improvement over baseline.
  It therefore has no MT5, shadow, demo, live, sizing, or portfolio authority.
- Journey labels remained diagnostic only; zero journey rows entered model
  fitting. COMEX features were excluded, the Databento API was not accessed,
  no new or paid data was acquired, and runtime was unchanged.
- Independent verification validates `17` artifact hashes, all locked input and
  implementation hashes, exact prediction populations, threshold selection,
  the deterministic 10,000-resample bootstrap, and exact replay of all six
  serialized primary fold models. The artifact-manifest SHA-256 is
  `9c9d2e95caf53bad5e5cc28b6562028247d6c32fd16c1dab9e69cad52a82eee3`.

The correct next decision is to keep the specialists unchanged and keep ML
offline. Further ML research requires a new preregistered version with a real
new information source or a defensible per-family target; changing thresholds
or hyperparameters against these test results would be overfitting.

## Shared-Account Portfolio Step 5 Evaluation - 2026-07-22

Step 5 is complete under
`xau-usd/xauusd-fast-research/causal-candidate-quality-ml-v1/outputs/step_5`.
Its locked evidence decision is
`STEP_5_HISTORICAL_PORTFOLIO_GATE_PASS_RESEARCH_ONLY`. This is exposed-history
research and does not authorize MT5, shadow, demo, live, or runtime changes.

- The definition-contract SHA-256 is
  `b8d8e29c14f493a54a7965b36cde4126e499c247a37e7f91b3edec0189c15803`.
  It binds the final Step 3 and Step 4 evidence, all implementation hashes, the
  four fixed portfolio populations, every account rule, all acceptance gates,
  and 157 M5 source files before combined portfolio outcomes were opened.
- Four portfolios were evaluated. The historical-policy comparators preserve
  as-recorded duplicates for V59/V60 reconciliation. The governed five- and
  nine-family portfolios use all broker-executable resolved candidates, select
  one candidate per structural episode with an outcome-blind tie break, and
  then enforce the locked account governor.
- The primary `NINE_ALL_CANDIDATES_GOVERNED` portfolio accepted `2,089` trades.
  Full-history fixed-0.01-lot net P&L is `$3,161.40`, profit factor is `1.4382`,
  and conservative M5 floating drawdown is `$275.00`, or `7.53%` of the locked
  `$3,654.45` starting equity.
- Primary trailing windows are: 3M `77` trades, `1.185/day`, `$338.07`, PF
  `1.590`, DD `$95.43`; 6M `154`, `1.194/day`, `$1,075.42`, PF `1.862`, DD
  `$146.59`; 1Y `360`, `1.379/day`, `$1,345.08`, PF `1.574`, DD `$146.59`; 2Y
  `766`, `1.467/day`, `$1,890.24`, PF `1.503`, DD `$230.76`; 5Y `1,413`,
  `1.084/day`, `$2,489.57`, PF `1.454`, DD `$275.00`; 10Y `1,989`,
  `0.763/day`, `$2,934.68`, PF `1.425`, DD `$275.00`.
- The full 2010-June 2026 frequency is only `0.485/day`. The one-trade-per-day
  target is therefore supported over the latest five years, not over ten years
  or the complete history.
- All `18/18` preregistered gates passed. No hard stop fired. Exact-event state
  peaked at three open positions, `$44.07` aggregate initial risk, `$32.73`
  directional risk, and `$517.22` estimated margin; every locked risk invariant
  held. M5 boundary envelopes conservatively report up to `$45.67` simultaneous
  initial risk because a full boundary bar can contain a closing and opening
  position that did not overlap at exact event time.
- Six-month stability is `13/20`, or `65%`, exactly the locked minimum and below
  the earlier 70% aspiration. The weakest block began July 2022 at `-$110.17`.
- Recent profit is not evenly distributed. Over one year, R1 is approximately
  flat at `$1.56` and V25 loses `$25.85`; V57, V7, V8, and R2 provide most of
  the positive result. V57 supplies `183/360` one-year trades, so recent family
  concentration remains an important prospective risk even though the locked
  five-year concentration gate passes.
- The primary rejection counts are `660` family-position conflicts, `320`
  broker-ineligible rows, `257` structural duplicates, `231` mechanism
  conflicts, `135` oversized single-trade risks, `57` daily-entry-cap blocks,
  and `3` direction-cap blocks. Historical rejection was never treated as a
  loss.
- Independent verification reproduces all four policy decision ledgers, every
  primary accepted candidate, endpoint P&L, all primary window metrics, the
  complete `1,176,817`-row M5 equity curve, all 18 gates, and all 11 artifact
  hashes. The artifact-manifest SHA-256 is
  `f6aa8a4827da8d09e33af25329b8e3d6cc855906d1210e60252231a71716b672`.
- ML predictions, ML thresholds, journey rows, COMEX, Databento, new data
  acquisition, and runtime actions were not used.

The next defensible stage is prospective confirmation of this exact frozen
portfolio and execution parity on MT5, while separately repairing recent R1 and
V25 weakness. Do not tune this Step 5 governor against its historical result or
claim that the ten-year frequency target has been achieved.

## Shared-Account AED Correction Step 5.1 - 2026-07-22

Step 5.1 is complete under
`xau-usd/xauusd-fast-research/causal-candidate-quality-ml-v1/outputs/step_5_1`.
Its locked evidence decision is `STEP_5_1_AED_PORTFOLIO_GATE_FAIL`. This
correction supersedes Step 5's account-specific risk and drawdown claims for
demo account `1033030`; it does not change any strategy, candidate, fixed lot,
risk fraction, tie break, reporting window, or acceptance gate.

- A read-only MT5 snapshot proved that account `1033030` is denominated in AED
  with balance and equity `AED 3,627.19`, while XAUUSD profit currency is USD.
  It also bound the `0.01` minimum lot, contract size `100`, profit conversion
  `3.6715 AED/USD`, adverse loss conversion `3.6740 AED/USD`, and zero open
  positions or orders. No broker action was performed.
- Step 5 had treated the numeric `3,654.45` starting balance as USD. On the real
  account, `AED 3,627.19` is only about `USD 987.26` of risk capital. The
  risk-equivalent AED capital for Step 5's original `USD 3,654.45` assumption
  would be approximately `AED 13,426.45`; this is a unit-equivalence diagnostic,
  not a funding or activation recommendation.
- The correction contract was frozen before rerun. Its definition SHA-256 is
  `969924a5d42200f2bd5b3af57e9c61a1249ac43e50068dcbc68aeaf3c4bd1d0c`;
  the final lock-file SHA-256 is
  `cdf20134880a3a5f101c1e59c8c850792418f9ea8cd7b6df3592d86fb8e87b04`.
- The corrected primary `AED_NINE_ALL_CANDIDATES_GOVERNED` portfolio accepted
  `389` trades, earned `AED 879.24`, reported PF `1.2408`, and reached
  `AED 393.61` M5 floating drawdown, or `10.85%` of starting equity.
- The primary crossed its frozen 10% closed-drawdown suspension on 17 September
  2020. With fixed `0.01` lot sizing and no smaller broker volume, the governor
  has no reduced-size recovery path. It consequently accepted zero trades in
  the trailing five-, two-, one-, six-month, and three-month windows.
- Only `5/18` gates passed. The corrected result therefore blocks prospective
  MT5 parity, EA attachment, shadow execution, and demo activation on this
  account under the current fixed-lot portfolio. Risk limits were not loosened
  after the result.
- Independent verification reproduces the currency arithmetic, all policy
  decisions, accepted ledgers, account P&L endpoints, all primary metrics, the
  full `1,176,817`-row M5 equity curve, acceptance decision, and all `12`
  artifact hashes. A clean rerun retained artifact-manifest SHA-256
  `dee2b4510425caf11202419c6d69bf1cec24bd16e8db70e42dc2a36b0496b2ad`.
- All `58` package tests pass. Ruff and Python compilation are clean. ML,
  COMEX, Databento API access, new data acquisition, runtime changes, and order
  placement remained offline.

The next decision must solve the minimum-lot/capital mismatch without tuning
against this failed history: use sufficient risk capital, use a venue that
supports smaller XAUUSD volume, or preregister a new portfolio that abstains
whenever the minimum lot exceeds the original risk budget. The corrected gate
itself does not authorize attachment to account `1033030`.

### Demo minimum-balance waiver - 2026-07-22

The owner explicitly waived minimum-balance eligibility on demo account
`1033030` so prospective trade collection can continue. The active package is
still `v60-canonical-demo-portfolio-v2`; the superseded Core-v1 executor must
not be started. The waiver is encoded as
`minimum_balance_requirement_enabled=false` and
`demo_balance_eligibility_waived=true` and is reported in runtime status.

This waiver is demo-only and does not reclassify the failed Step 5.1 historical
gate as a pass. Exact login/server/currency and MT5 demo trade-mode checks,
fixed `0.01` lot, spread gates, position and daily-entry limits, drawdown
suspension, combined/floating hard stops, emergency closure, guardian halt
files, and the complete live/ML prohibitions remain enforced.

The canonical workers were restarted after the waiver. Runtime status at
`2026-07-22T08:38:11.899430Z` was `ACTIVE_DEMO_BROKER_ACTION`: feed and chart
profile preflights were ready, execution was enabled, minimum balance was
disabled, the demo waiver was visible, and the account had zero XAUUSD
positions with zero closed or floating drawdown. Live, ML runtime, and ML
shadow authorization all remained false. Deployment tests pass `14/14`.

## Regime-Specific Candidate Quality Models V2 - 2026-07-22

The offline V2 package is complete at
`xau-usd/xauusd-fast-research/causal-candidate-quality-regime-models-v2`.
It leaves the failed pooled V1 model and deterministic demo runtime unchanged.
Its overall evidence decision is
`REGIME_V2_FAMILY_GATES_PASSED_DEVELOPMENT_ONLY`.

- The model architecture, 22 causal features, family/fold availability,
  thresholds, 10,000-resample block bootstrap, and 11 family gates were frozen
  before fitting. Definition-contract SHA-256 is
  `375b2fb7ac7808ebe1f92071873cb5dd6bcd481eafc9c1bfa5e84ff26b41639b`;
  lock-file SHA-256 is
  `b0cf213a4713b495335fb273ce45f1ace2a3ecf50c703faa9e64b34774ccbe76`.
- Seven specialist families produced 21 independent fold models. R2 has only
  128 usable examples and V25 only 101, so both failed closed as
  `REGIME_MODEL_INSUFFICIENT_EVIDENCE` rather than borrowing another family's
  test outcomes.
- R1, R3, R4, R5, V57, and V7 failed at least one locked gate. R1, V57, and V7
  showed some ranking signal, but their improvement confidence or coverage
  evidence was insufficient. R3 and R4 ranked poorly; R5's improvement was
  small and not statistically defensible.
- `V8_RETEST_HEALTH` alone passed all `11/11` development gates over three
  purged out-of-time folds and 102 candidates. It selected 60 candidates,
  achieved weighted AUC `0.6388` with 95% lower bound `0.5297`, improved mean
  stressed outcome from `0.4801R` to `0.7031R`, improved PF from `2.1883` to
  `3.3571`, and reduced candidate-sequence drawdown from `7.7286R` to
  `3.4836R`.
- V8 remains thin evidence: the 95% lower bound on selected-minus-baseline EV
  is only `+0.0076R`, and the latest F2025 fold's delta is `-0.0580R`. The model
  therefore has no runtime, filtering, routing, shadow, demo, live, or sizing
  authority. Fresh prospective confirmation is mandatory.
- Independent verification replayed all 21 serialized models, every threshold,
  prediction and selection, all family metrics, and all bootstraps. It verified
  31 artifact hashes. A clean rerun reproduced artifact-manifest SHA-256
  `66d7b783761762234380f36ed62f63733da409fc18eb48244a75a6c87d9e6156`.
- Package tests pass `3/3`; Ruff and compilation are clean. Journey rows,
  COMEX, Databento API access, demo outcomes, new data, and runtime were not
  used.

The next ML step is a separately authorized prospective V8 scorer that records
predictions without affecting deterministic trading, followed by a locked
forward evidence gate. Do not connect any V2 model to the demo executor under
the current authorization.

## Expanded Candidate Quality Dataset V3 - 2026-07-22

The research-only V3 dataset is complete under
`xau-usd/xauusd-fast-research/causal-candidate-quality-expanded-dataset-v3`.
Its decision is `V3_EXPANDED_CANDIDATE_DATASET_COMPLETE_RESEARCH_ONLY`.

- The hash-locked high-frequency ledger now provides `29,419` mechanical
  events, `28,432` events with resolved actions, and `73,116` resolved
  event/action labels: `31,049` stressed winners and `42,067` stressed
  failures. Another `987` events remain explicit in the registry without a
  completed action label and receive no training weight.
- Outcome-blind 30-minute clustering produces `15,172` structural episodes.
  Each resolved event/action row receives inverse action and resolved-event
  multiplicity weight; weights sum to exactly one per structural episode.
- The primary population contains three mechanics: break-and-run, downside
  impulse/retest, and opening-range reversal, each with fast 1R, intraday 1.5R,
  and swing 2R action choices. The exact model surface contains `58` causal,
  normalized features. IDs, timestamps, absolute prices, alignment errors,
  account feasibility, and every outcome field are forbidden as features.
- Six expanding July-to-July folds from F2021 through F2026 are materialized.
  Complete structural episodes stay in one partition and fit, calibration, and
  test labels are purged at their exact partition boundaries.
- The original `3,752` canonical rows remain a separate benchmark. The
  `117,534` journey action rows remain quarantine evidence. V3 reports `1,642`
  event-time/direction overlaps with the canonical benchmark and forbids silent
  pooling, preventing duplicated observations from inflating evidence.
- Verification passes Ruff, compilation, manifest/source hash checks, exact
  row and identity checks, finite feature checks, episode-weight invariants,
  split purging, and `4/4` package tests. The artifact-manifest SHA-256 is
  `dc8fa2b81f39041edc00f215b85713fa13bd00dc2347dc37b200e1e6e723a42a`.
- No model, threshold, portfolio simulation, Python serving, ML shadow, EA,
  demo/live authorization, runtime setting, terminal, or broker account was
  changed. The active deterministic gold demo runtime remains separate.

The next authorized ML stage requires a new preregistered per-mechanism and
per-regime action-ranking contract. It must benchmark against deterministic
take-all and fixed-action baselines, keep structural episode clustering in all
statistics, and treat the F2026 history as exposed development data rather than
a pristine holdout.

### Older XAUUSD acquisition audit - 2026-07-22

A delegated read-only audit corrected the assumed archive boundary. The local
Dukascopy extension state already contains `78` complete XAUUSD months from
January 2010 through June 2016; January 2010 has all `744` expected hourly files,
is marked complete, and has a frozen aggregate SHA-256. This complements the
later archive through June 2026. No reliable free pre-2010 XAUUSD bid/ask source
was verified, so no download, partial file, paid request, Databento request, or
archive mutation was performed. Any future extension must begin with a
read-only pre-2010 availability probe and must not lower the source-quality
standard merely to add years.

## Causal Candidate Action Models V3 - 2026-07-22

The research-only Action V3 package is complete at
`xau-usd/xauusd-fast-research/causal-candidate-quality-action-models-v3`.
Its evidence decision is `ACTION_MODEL_V3_MODEL_EVIDENCE_GATE_FAIL`; no lane is
authorized for runtime use.

- The 58-feature surface, disjoint lane ownership, six purged out-of-time
  folds, ridge and histogram-gradient-boosting models, calibration-only policy
  selection, UTC-week bootstrap, economic gates, and abstention states were
  locked before fitting. An initial run stopped before model fitting because
  the earliest disjoint break-and-run fit had 674 eligible action rows rather
  than the earlier overlapping-population estimate. The feasibility floor was
  corrected from 750 to 650 before any calibration or test result was read,
  then the contract and evaluation were regenerated. Final definition-contract
  SHA-256 is
  `b6482c02c464f1d2eb2f431e4547c88b746f86aa5559415dff22732a7f4abbcb`.
- Eighteen chosen lane/fold models produced `47,457` out-of-time action
  predictions and `10,220` selected events. These are structurally weighted
  research candidates; their events-per-weekday values are not executable
  shared-account trade frequency and must not be added without overlap,
  concurrency, and portfolio-risk simulation.
- Downside impulse/retest selected `2,864` events, with weighted mean
  `+0.1472R`, PF `1.2673`, weighted drawdown `63.61R`, weighted AUC `0.6561`,
  and a `+0.0556R` bootstrap lower bound on selected mean. It nevertheless
  failed closed: F2026 retained only `24.28%`, returned `-0.5602R` per selected
  event with PF `0.3569`, and had `-0.0753R` common-event action uplift.
- Break-and-run selected `5,421` events, with weighted mean `+0.2166R`, PF
  `1.3581`, weighted drawdown `120.97R`, weighted AUC `0.5880`, and a
  `+0.1344R` bootstrap lower bound on selected mean. It also failed: only five
  calibration folds passed, aggregate coverage was `50.84%`, common-event
  action-uplift bootstrap lower bound was `-0.0082R`, and F2026 returned
  `-0.2001R` with PF `0.7373`.
- Opening-range reversal selected `1,935` events but remained negative at
  `-0.2433R` per event and PF `0.6937`. None of its calibration folds passed
  and none of its six test folds was positive.
- The fixed-action baselines were negative in all three lanes, making the
  locked positive-baseline retention ratio undefined. This gate therefore
  failed, but it is not the decisive blocker: latest-fold losses, unstable
  coverage, calibration failures, and weak action uplift independently reject
  the models.
- Independent verification replayed all 18 serialized models, reconciled every
  prediction and selection, recomputed metrics, bootstrap intervals, and
  decisions, and verified all manifest hashes. It passed with manifest SHA-256
  `0fb873c4729974a3ee83754b29236659bcd11856f9e03531123eadc661edc11c`.
  Package tests pass `4/4`; Ruff and compilation are clean.
- No EA, Python server, shadow model, demo/live authorization, terminal,
  account, deterministic strategy, or broker setting changed. The active
  deterministic demo runtime remains separate.

The next defensible research step is an outcome-blind F2026 drift audit before
another model iteration. It should measure feature, score, action-availability,
regime, session, and label-base-rate shifts by lane; determine whether the
failure is calibration drift or disappearing edge; and preregister any V4
regime-conditioned policy before fitting. F2026 is now exposed development
history and cannot be described as a pristine holdout again.

## Action V3 F2026 Drift Audit - 2026-07-22

The locked diagnostic package is complete at
`xau-usd/xauusd-fast-research/causal-candidate-quality-drift-audit-v3`.
It compares the frozen F2026 model and threshold on its reference calibration
year, 2024-07-01 through 2025-07-01, with its current test year, 2025-07-01
through 2026-07-01. The decision is
`F2026_DRIFT_AUDIT_COMPLETE_NO_RUNTIME_AUTHORIZATION`.

- Definition-contract SHA-256 is
  `8904909a6530fdc08404fb54a63c3aaf66fed27b4ce4a7af37cc7fb933e9a4c6`.
  The audit replayed three frozen models over `20,284` available action rows
  and `9,144` events, produced `174` locked feature-drift measurements, and
  reconciled F2026 test scores and selections with the original Action V3
  ledger.
- Downside impulse/retest suffered `RANKING_AND_OUTCOME_COLLAPSE`. Coverage
  fell from `59.95%` to `24.28%`; score PSI was `1.9392`; weighted AUC fell
  from `0.7215` to `0.4717`; selected mean fell from `+0.2985R` to `-0.5602R`;
  and PF fell from `1.5899` to `0.3569`.
- Break-and-run suffered `COVERAGE_AND_OUTCOME_COLLAPSE`. Coverage fell from
  `60.01%` to `30.28%`; score PSI was `1.0366`; weighted AUC fell from `0.6764`
  to `0.5220`; selected mean fell from `+0.3868R` to `-0.2001R`; and PF fell
  from `1.7161` to `0.7373`.
- Opening-range reversal was classified `BASE_EDGE_ABSENT`. Its selected mean
  improved from `-0.3742R` to `-0.0167R`, but remained nonpositive in both
  periods. More ML cannot manufacture a reliable edge from this mechanic; it
  requires strategy redesign first.
- Composition was not the main explanation for downside or break-and-run.
  Across regime, session, direction, action availability, and chosen action,
  within-stratum deterioration explained nearly all of their `-0.8587R` and
  `-0.5869R` selected-mean changes. Threshold-only recalibration is therefore
  not a defensible fix.
- Independent verification rebuilt all seven metric tables, replayed all three
  models, and verified every input and artifact hash. Manifest SHA-256 is
  `cfd3230973697eccbb0afe3a3a2732154571ca5b0fa6445e145c6e22dc0d7bd4`.
  Package tests pass `4/4`; Ruff and compilation are clean.

### Post-audit timestamp-unit defect

The drift audit exposed a correctness defect in
`high-frequency-expansion-v1/src/dataset.py`. Pandas 3 supplied
`datetime64[us, UTC]` integers while the prior-event window durations were in
nanoseconds. The fields named `prior_events_1h` and `prior_events_4h` therefore
counted approximately 1,000 and 4,000 hours. The same-direction feature was
unaffected because its timestamps were already nanoseconds.

The builder now explicitly normalizes timestamps to nanoseconds. A new
microsecond-dtype boundary test passes. Source SHA-256 is
`d61e65c2da60b6da1f784dc045908233ca40898e57ae8f5850b06f69abc36edd`.
The corrected reference/current means are `1.18/1.17` for the intended 1-hour
count and `3.79/4.04` for the intended 4-hour count, compared with corrupted
stored means of `554.75/676.90` and `2008.46/2689.59`.

The bug explained about `-0.1345` of the downside model's `-0.2776` mean-score
shift and `-0.0570` of the break-and-run model's `-0.3124` shift. It was not the
only problem; price/EMA/spread drift and genuine within-stratum outcome decay
remain. Frozen V3 artifacts were not rewritten, but they are now ineligible as
inputs to another model or for runtime promotion. The next step is a new
versioned rebuild of the complete candidate ledger and expanded causal dataset
with corrected features, followed by a fresh preregistered evaluation. Do not
silently update Complete Candidate V4 because its old code hash intentionally
preserves the original experiment.

No terminal, EA, account, deterministic specialist, model server, shadow
process, demo/live permission, or broker setting changed.

## Corrected Complete Candidate Dataset V5 - 2026-07-22

The versioned source-ledger rebuild is complete at
`xau-usd/xauusd-fast-research/complete-candidate-dataset-v5`. Its decision is
`COMPLETE_CANDIDATE_DATASET_V5_COMPLETE_RESEARCH_ONLY`.

- V5 rebuilt the complete 2016-2026 mechanical candidate universe from the
  original nine signal logs and the frozen Dukascopy cache. It retained exactly
  `29,419` events and `73,116` resolved event/action labels, including `1,485`
  gap events and `3,881` gap action rows.
- Event identities, action identities, labels, outcomes, prices, timestamps,
  regimes, and every non-corrected feature match Complete Candidate V4 exactly.
  The action digest remains
  `e3ebe4759e4af672a3a73e1202ef1d5d7532e78e2f57729e4dfa5251778f83c0`;
  the event digest remains
  `acaba67df169d2f175c052c8bf9253e5280a0186224824a69b1faebfdc619f1b`.
- Only `prior_events_1h` and `prior_events_4h` changed. An independent checker
  rebuilt the complete pre-filter signal universe and verified both counts.
  Corrected maxima are `8` and `15`; the corrected feature digest is
  `31898d9bbcb5b7913763a03798fb03f8207d9fb1ce17548f8edf4ca799b760d3`.
- The definition-contract SHA-256 is
  `38f83de410d4bb46cbb1eaa6a760ebeee679127d23b835b4c8a43651df3bb74f`.
  Independent verification passed with artifact-manifest SHA-256
  `70e6192ce243172d59b63621f8399ce642aadfbf3d4e6d429f629f52e57294cb`.
  Package tests pass `4/4`; Ruff and compilation are clean.

## Corrected Expanded Causal Dataset V4 - 2026-07-22

The downstream research dataset rebuild is complete at
`xau-usd/xauusd-fast-research/causal-candidate-quality-expanded-dataset-v4`.
Its decision is `V4_CORRECTED_EXPANDED_DATASET_COMPLETE_RESEARCH_ONLY`.

- The locked package consumes Complete Candidate V5 and retains exactly
  `29,419` events, `73,116` action labels, and `15,172` outcome-blind
  30-minute structural episodes. Labels comprise `31,049` stressed winners
  and `42,067` stressed failures.
- All event and action rows changed in the two corrected activity-density
  fields. Every other value is exactly equal to Expanded V3, and the `91,032`
  fold-assignment rows are byte-for-byte unchanged. Split artifact SHA-256 is
  `4ab4902d363824edb82909e75a283b6c54bff26684239b1b66303f7bd41bcea5`.
- Across the event registry, corrected `prior_events_1h` has mean `1.1095`,
  median `1`, 95th percentile `3`, and maximum `8`. Corrected
  `prior_events_4h` has mean `3.2238`, median `3`, 95th percentile `8`, and
  maximum `15`.
- The 58-feature causal surface, forbidden outcome fields, action labels,
  structural weights, six purged out-of-time folds, canonical benchmark, and
  journey quarantine policy remain unchanged. Model and threshold fitting,
  portfolio simulation, serving, ML shadowing, EA consumption, demo, live,
  and broker actions remain unauthorized.
- Definition-contract SHA-256 is
  `07c66d5508503851882d113da6aea284a6360ef04e0b4fab73eb55d2e05f43dc`;
  lock-file SHA-256 is
  `3d045cde7159919090c08921457f8963f874186260444ae96437ec612c806b2b`.
  Independent verification returned
  `V4_CORRECTED_EXPANDED_DATASET_VERIFICATION_PASS`; artifact-manifest SHA-256
  is `3431a4ae2d5909e8fc45808e60d86b60070e662179d55c27e05ad7ddbeccb052`.
  Package tests pass `4/4`; Ruff and compilation are clean.

Expanded V3 and every model trained from its corrupted density fields are
historical evidence only and are ineligible for promotion. The next ML step is
a separately preregistered, fresh evaluation trained from Expanded V4. It must
re-establish out-of-time ranking, economic uplift, latest-fold stability, and
drawdown evidence from zero; no previous model pass or threshold carries over.
No terminal, EA, account, deterministic specialist, model server, demo/live
permission, or broker setting changed during either rebuild.

## Corrected Action Model Replay V4 - 2026-07-22

The research-only corrected-data replay is complete at
`xau-usd/xauusd-fast-research/causal-candidate-quality-action-models-v4`.
Its evidence decision is `ACTION_MODEL_V4_MODEL_EVIDENCE_GATE_FAIL`; all three
lanes fail and no model is authorized for runtime use.

- Action V4 exactly replays the frozen Action V3 experimental methodology on
  corrected Expanded Dataset V4. Lanes, exclusions, 58 features, targets,
  model parameters, calibration policy, acceptance gates, six purged folds,
  bootstrap, and random seeds are identical. Methodology-contract SHA-256 is
  `e3f8819d4d4a935f1412086a816decd2b70f44e86a2337ffa16164d1f52e8950`.
  The shared model-mechanics source remains byte-identical to V3 at SHA-256
  `2a936be073581fff3ae7458a98c24da43ae57bd6822c93792d5e280f1e169fce`.
- Downside impulse/retest selected `3,188` test events, or `2.037` candidate
  events per weekday, with mean `+0.0962R`, PF `1.1698`, drawdown `58.54R`, and
  weighted AUC `0.6566`. Its selected-mean 95% lower bound is `+0.0107R`, but
  only five calibration folds passed, common-event action-uplift lower bound
  is `-0.0127R`, and F2026 returned `-0.4377R` with PF `0.4640`.
- Break-and-run selected `5,600` test events, or `3.578` candidate events per
  weekday, with mean `+0.1914R`, PF `1.3110`, drawdown `164.20R`, and weighted
  AUC `0.5888`. Its selected-mean 95% lower bound is `+0.1095R`, but only five
  calibration folds passed, coverage was `52.52%`, common-event action uplift
  was negative with 95% interval `[-0.0049R, -0.0004R]`, and F2026 returned
  `-0.2119R` with PF `0.7240`.
- Opening-range reversal selected `2,140` test events but remained negative at
  `-0.2961R`, PF `0.6293`, and drawdown `351.59R`. No calibration fold passed,
  no test fold was positive, and the selected-mean 95% upper bound remained
  negative at `-0.2225R`.
- Correcting the density features changed four of 18 chosen fold policies. It
  modestly improved downside's latest-fold loss, but reduced its aggregate
  mean and PF. Break-and-run and opening reversal worsened economically. The
  result therefore confirms that the timestamp-unit defect was material but
  was not the main cause of model instability.
- The reported events-per-weekday figures are structurally weighted research
  candidate frequency across disjoint historical test folds. They are not
  executable shared-account trade frequency and cannot be added together as a
  demo-performance claim.
- Final definition-contract SHA-256 is
  `8265347e91e42d0342e00e1c15438487adf105af5075d612a0d5605f6e42e321`;
  lock-file SHA-256 is
  `92c01db8da8cf335d5e462c041676aaa1d09d7e077e9074a4497e281729e8842`.
  Independent verification refitted and replayed all `18` serialized models,
  reproduced `47,457` out-of-time predictions and `10,928` selected events,
  recomputed action choices, thresholds, metrics, and 5,000-resample weekly
  bootstraps, and returned `ACTION_V4_VERIFICATION_PASS`. Artifact-manifest
  SHA-256 is
  `b75a58d565dceb796291be23572513caeebc6df24fd07bf002fc4c245021280e`.
  Package tests pass `5/5`; Ruff and compilation are clean.

This package proves that training can run correctly on the repaired dataset,
but it does not prove a deployable filter. Do not tune the same thresholds on
the exposed F2026 losses or connect these models to MT5. The next research
iteration must change the information or mechanism rather than repeatedly
refit the same unstable policy: redesign weak candidate mechanics, add
preregistered regime-local interactions or recency-aware training, evaluate
them through nested walk-forward development, and reserve genuinely new
forward observations for promotion evidence. No terminal, EA, account,
deterministic specialist, model server, demo/live permission, sizing, or broker
setting changed.

## Adaptive Action Models V5 - 2026-07-22

The research-only adaptive-training comparison is complete at
`xau-usd/xauusd-fast-research/causal-candidate-quality-adaptive-models-v5`.
Its evidence decision is `ADAPTIVE_MODEL_V5_MODEL_EVIDENCE_GATE_FAIL`; all
lanes remain unauthorized for runtime use.

- V5 froze four ridge-alpha-20 training methods before fitting: expanding
  history, a 36-month rolling window, a normalized 12-month-half-life recency
  weighting, and regime-local experts with a 650-action/200-event minimum and
  expanding-global fallback. Candidate population, 58 features, labels,
  actions, lane ownership, calibration policy, six purged folds, economic
  gates, and bootstrap remain equal to corrected Action V4.
- Calibration made substantive use of the comparison: across 18 lane/fold
  choices it selected expanding eight times, recency-weighted five times,
  rolling three times, and regime-local twice. The experiment did not collapse
  to a disguised expanding-only replay.
- Downside impulse/retest improved modestly versus Action V4. It selected
  `3,090` events, or `1.974` candidate events per weekday, with mean
  `+0.1070R`, PF `1.1879`, drawdown `58.54R`, and weighted AUC `0.6558`.
  Selected-mean 95% lower bound is `+0.0176R`; common-event action-uplift 95%
  interval is now positive at `[+0.00045R, +0.0933R]`; and all six calibration
  folds passed. It still fails decisively because F2026 returned `-0.4377R`,
  PF `0.4640`, and `-0.0984R` common-event uplift.
- Break-and-run selected `5,580` events, or `3.565` candidate events per
  weekday, with mean `+0.2010R`, PF `1.3285`, drawdown `161.76R`, and weighted
  AUC `0.5864`. Its selected-mean 95% lower bound is `+0.1192R`. It still has
  only five passing calibration folds, aggregate coverage is `52.34%`, and
  F2026 remained unchanged at `-0.2119R` with PF `0.7240`.
- Opening-range reversal improved slightly but remained invalid: `2,077`
  selected events, mean `-0.2726R`, PF `0.6624`, and drawdown `319.66R`. Zero
  calibration folds and zero test folds were positive. Regime-local training
  reduced its F2026 loss to `-0.1067R` with PF `0.8542`, still below zero.
- The negative fixed-action baselines make the frozen baseline-retention ratio
  undefined, but this is not the decisive rejection reason. Downside and break
  fail the latest-fold mean/PF gates independently; opening reversal fails its
  expectancy, PF, stability, and robustness gates independently.
- Candidate events per weekday are research opportunities across historical
  disjoint test folds, not executable shared-account frequency or P&L.

Base-method contract SHA-256 is
`d0f0561eb14d048558e1ddbd87e98923e754943e9235396352571e08b6845fbd`;
final definition-contract SHA-256 is
`7db155ac8043d8b5cfc7b16a8abcf75707ea86b7485c9ca45477b16cd4f65510`;
lock-file SHA-256 is
`6de2a89683ce0e286e409d83f127ce87165bb63d975cb987f2e21e3b0176e1bb`.
Independent verification refitted all `72` lane/fold/variant calibration
models, reconstructed all `216` calibration policies, replayed the `18`
serialized winners and `47,457` test predictions, and returned
`ADAPTIVE_V5_VERIFICATION_PASS`. Artifact-manifest SHA-256 is
`178a4ba6daf7d964880d30c5f24a00f24df5b95c50785a8ae56b9df25e455011`.
Package tests pass `6/6`; Ruff and compilation are clean.

V5 shows genuine incremental progress in aggregate downside quality, but
training-window adaptation alone does not solve the current-regime failure.
Do not select a different V5 variant using F2026 test outcomes and do not
connect V5 to MT5. The next research change must add independently motivated
information or stronger candidate mechanics, with F2026 treated only as
exposed diagnostic history and new forward data reserved for promotion. No
terminal, EA, account, deterministic specialist, model server, demo/live
permission, sizing, or broker setting changed.

## Causal Macro Action Models V6 - 2026-07-22

The research-only DXY/Treasury augmentation is complete at
`xau-usd/xauusd-fast-research/causal-candidate-quality-macro-models-v6`.
Its evidence decision is `MACRO_MODEL_V6_MODEL_EVIDENCE_GATE_FAIL`; all three
lanes remain unauthorized for runtime use.

- A source audit rejected the broader XAGUSD/EURUSD/USDJPY feature cache for
  this iteration because it ends on 2024-06-30 and cannot test F2025/F2026.
  V6 used only the hash-locked free Dukascopy DOLLARIDXUSD and USTBONDTRUSD
  M5 cache, which contains `525,099` source rows through 2026-06-30. No paid
  data or Databento source was used.
- V6 preserved the V5 population, labels, 58 base features, ridge model, four
  training variants, calibration policy, six purged folds, economic gates,
  bootstrap, and random seeds. It added exactly eight direction-adjusted DXY,
  Treasury, consensus, and disagreement features from completed M15 bars.
  Joins are backward-only with at most ten minutes of age. Missing values are
  median-imputed inside each fit pipeline without missingness indicators, so
  all `73,116` action rows and `28,432` resolved events remain present.
- Downside impulse/retest improved slightly in aggregate versus V5: `3,073`
  selected events, `1.964` candidate events per weekday, mean `+0.1104R`, PF
  `1.1941`, drawdown `63.64R`, and AUC `0.6525`. The selected-mean 95% lower
  bound is `+0.0209R` and action-uplift lower bound is `+0.0048R`. It still
  fails because F2026 worsened to `-0.4434R`, PF `0.4587`, and `-0.0996R`
  action uplift.
- Break-and-run selected `5,977` events, or `3.819` candidate events per
  weekday, with mean `+0.1849R`, PF `1.3000`, drawdown `157.27R`, and AUC
  `0.5827`. F2026 improved modestly to `-0.1934R` and PF `0.7465`, but remains
  clearly negative. Aggregate mean, PF, and AUC regressed versus V5, and only
  five calibration folds passed.
- Opening-range reversal remained invalid: `2,057` selected events, mean
  `-0.3004R`, PF `0.6251`, drawdown `351.75R`, and AUC `0.5164`. Its F2026
  loss improved to `-0.0794R` with PF `0.8900`, but no calibration fold and no
  test fold passed the required profitability evidence.
- The negative fixed-action baselines again make the inherited retention
  ratio undefined. This does not drive the result: all lanes independently
  fail the latest-fold mean and PF gates, and opening also fails aggregate
  expectancy, PF, AUC, and robustness gates.
- Candidate-event frequency is diagnostic research frequency, not executable
  shared-account trades or P&L. No model was attached to MT5.

Definition-contract SHA-256 is
`713b455bdb87bbf5e552a1644b6fac149ca58b810a775937b7f28931917d0246`;
lock-file SHA-256 is
`21ca68ec72ddbf6dd05a784d345efdec8088477c52f5d306f690759aedcf6954`.
Independent verification refitted all `72` calibration models, reconstructed
all `216` policies, replayed `18` serialized models and `47,457` out-of-time
predictions, and returned `MACRO_V6_VERIFICATION_PASS`. Artifact-manifest
SHA-256 is
`fedaf9dc50f8fa930ff7c7ef9e56458e6d576756e8d870e2d638059afb32a6fc`.
Package tests pass `7/7`; Ruff and compilation are clean.

V6 shows that contemporaneous DXY/Treasury context is not the missing fix in
this linear formulation. The next step is a read-only latest-era failure audit
of selected and baseline events by lane, regime, action, session, month, and
macro availability. F2026 is exposed diagnostic history and must not be used
to retroactively tune V6. No terminal, EA, account, deterministic specialist,
model server, demo/live permission, sizing, or broker setting changed.

## Causal Horizon Interaction Models V7 - 2026-07-22

The research-only context-dependent action-horizon experiment is complete at
`xau-usd/xauusd-fast-research/causal-candidate-quality-horizon-interactions-v7`.
Its evidence decision is `HORIZON_MODEL_V7_MODEL_EVIDENCE_GATE_FAIL`; all
lanes remain unauthorized for runtime use.

- The latest-era audit exposed a structural limitation in V5/V6: for rows from
  one event, all market features are identical and only action descriptors
  change. A pooled linear model therefore gives fast, intraday, and swing
  actions common market-feature slopes and can vary their scores mainly by
  fixed action offsets. This prevents general context-dependent horizon
  selection.
- V7 preserved V5's corrected population, labels, 58 base features, ridge
  alpha, four training variants, calibration policy, six purged folds, gates,
  bootstrap, and seeds. It mechanically multiplied every one of the 52
  non-action event features by the intraday and swing indicators, with fast as
  reference. No feature was hand-picked. The final surface has exactly 104
  interaction features and 162 total features.
- Downside impulse/retest improved modestly in aggregate and materially in the
  latest fold. It selected `3,025` events, or `1.933` candidate events per
  weekday, with mean `+0.1138R`, PF `1.1923`, drawdown `58.44R`, and AUC
  `0.6415`. F2026 improved from V5's `-0.4377R`/PF `0.4640` to
  `-0.3344R`/PF `0.5777`, but remained decisively negative; F2026 action
  uplift was also negative at `-0.1252R`.
- Break-and-run selected `5,629` events, or `3.597` candidate events per
  weekday, with mean `+0.1675R`, PF `1.2750`, drawdown `150.10R`, and AUC
  `0.5853`. F2026 improved only slightly to `-0.1939R` and PF `0.7411`.
  Aggregate mean/PF regressed versus V5, only five calibration folds passed,
  and the action-uplift 95% interval was entirely negative at approximately
  `[-0.0315R, -0.0031R]`.
- Opening-range reversal remained invalid at `2,180` selected events, mean
  `-0.3170R`, PF `0.6001`, drawdown `386.83R`, and AUC `0.5226`. F2026
  improved to `-0.0729R` and PF `0.8962`, but still failed, while aggregate
  quality and drawdown worsened versus V5.
- The result shows that horizon interactions address a real limitation but do
  not solve the main problem. A single absolute-return regression still
  conflates event tradeability with relative action choice. The next defensible
  model experiment is a preregistered two-stage design: first estimate whether
  any allowed action has positive stressed expectancy, then rank relative
  action advantage only within candidates that pass that event-quality stage.
- Candidate-event frequency remains diagnostic and is not executable account
  trade frequency or P&L. V7 was never attached to MT5.

Final definition-contract SHA-256 is
`17b90018e53758345ce9f2748d3f4f6ede9f982fec757b5651332b7e4b1ad43d`;
lock-file SHA-256 is
`910874cab96d8af6f06bcdd064209a48854df3a6918e9e458cc8c66e5703476a`.
Independent verification refitted all `72` calibration models, reconstructed
all `216` policies, replayed `18` serialized models and `47,457` out-of-time
predictions, and returned `HORIZON_V7_VERIFICATION_PASS`. Artifact-manifest
SHA-256 is
`7a03c3c328f676028f0685fa72d4005439a37cfcabd6c56df42bdfb311e38990`.
Package tests pass `8/8`; Ruff and compilation are clean. No terminal, EA,
account, deterministic specialist, model server, demo/live permission, sizing,
or broker setting changed.

## Causal Two-Stage Models V8 - 2026-07-22

The preregistered event-quality/action-advantage experiment is complete at
`xau-usd/xauusd-fast-research/causal-candidate-quality-two-stage-models-v8`.
Its evidence decision is `TWO_STAGE_MODEL_V8_MODEL_EVIDENCE_GATE_FAIL`; all
three lanes remain unauthorized for runtime use.

- V8 tested the specific mechanism identified after V7. The event stage uses
  52 causal non-action features to predict the best available stressed action
  return. The action stage uses the 58 V5 features plus 104 frozen horizon
  interactions to predict each action's return advantage over the within-event
  mean. Both stages use the same calibration-selected training variant per
  fold; only that variant and the frozen retention quantile can be selected.
- The target audit covers `73,116` action rows and `28,432` resolved events:
  `15,578` have at least one positive stressed action and `12,854` do not.
  The repeated event targets preserve event-level training weight with maximum
  error `1.39e-17`; no event has inconsistent evaluation weights. Missing
  actions remain missing and are not imputed.
- Downside impulse/retest was the only lane with a small aggregate improvement
  over V5. It selected `3,047` events, or `1.947` candidate events per weekday,
  with mean `+0.1097R`, PF `1.1866`, drawdown `58.96R`, and event AUC `0.6600`.
  The action ranker chose a hindsight-best tied action on `46.3%` of weighted
  events. Aggregate common-event action uplift was `+0.0410R`, but this was
  `0.0059R` below V5. F2026 remained decisively negative at `-0.3995R`, PF
  `0.5059`, and `-0.0746R` action uplift.
- Break-and-run selected `5,610` events, or `3.585` candidate events per
  weekday, with mean `+0.1336R`, PF `1.2150`, drawdown `214.54R`, and event AUC
  `0.5978`. Exact best-action accuracy was `66.7%`, but aggregate action uplift
  was `-0.0346R`. Mean R regressed `0.0674R` and PF regressed `0.1136` versus
  V5; F2026 was `-0.2440R` with PF `0.6818`.
- Opening-range reversal remained invalid: `2,100` selected events, mean
  `-0.3372R`, PF `0.5748`, drawdown `398.01R`, event AUC `0.5378`, and zero
  passing calibration or positive test folds. F2026 was `-0.1697R`, PF
  `0.7654`, and `-0.0939R` action uplift.
- Event detection contains measurable information, particularly for downside,
  but the two-stage decomposition did not produce stable action selection or
  survive the latest regime. It is therefore useful diagnostic evidence, not
  a trained trading model. Candidate-event frequency is not executable shared
  account frequency or P&L.

Definition-contract SHA-256 is
`3eb7a4ce52154ca17ec20be28957c250f39dfde59223bf05f4134dae98a0e0a9`;
lock-file SHA-256 is
`12eb0585e2a6cafb9f1f2226fd190064e1b351b528dde3ac283b58f89a631aa2`.
Independent verification refitted all `72` paired calibration policies, or
`144` constituent stage models, reconstructed all `216` policies, replayed
`18` serialized paired models and `47,457` out-of-time predictions, and
returned `TWO_STAGE_V8_VERIFICATION_PASS`. Artifact-manifest SHA-256 is
`20dce93dad5af52bd6320ca6ee8debaa546b5603786d72d9a06a5e893291d133`.
Package tests pass `11/11`; Ruff and compilation are clean.

V8 closes the hypothesis that target decomposition alone can repair the
current ML route. Do not tune V8 against F2026 or attach it to MT5. The next
research move should target the actual latest-era distribution break and
candidate mechanics, while preserving unseen forward data for any promotion
decision. No terminal, EA, account, deterministic specialist, model server,
demo/live permission, sizing, or broker setting changed.

## Causal Pairwise Models V9 - 2026-07-22

The preregistered binary event-classification and pairwise horizon-ranking
experiment is complete at
`xau-usd/xauusd-fast-research/causal-candidate-quality-pairwise-models-v9`.
Its evidence decision is `PAIRWISE_MODEL_V9_MODEL_EVIDENCE_GATE_FAIL`; all
three lanes remain unauthorized for runtime use.

- V9 changed the action-learning problem rather than tuning V8. A standardized
  L2 logistic event classifier predicts whether any available stressed action
  is positive. A second classifier predicts which action wins in each
  fast/intraday/swing pair from 162 mechanically differenced features. Mean
  pairwise win probability chooses the action. Both classifiers share one of
  the four frozen training variants in each fold.
- The target audit covers `73,116` action rows, `28,432` resolved events, and
  `63,689` pair comparisons. There are `15,578` events with a positive best
  action and `12,854` without one. Pair and repeated-event weights preserve
  event influence with maximum errors `0` and `1.39e-17`; no outcome tie was
  present in the real pair ledger.
- Pairwise ranking worked substantially better than V8's pointwise advantage
  regression. Hindsight-best tied-action accuracy was `76.7%` for downside,
  `83.1%` for opening reversal, and `83.6%` for break-and-run. Weighted
  pairwise AUCs were `0.6055`, `0.5598`, and `0.5518`, respectively. This
  reduced break-and-run common-event action loss from V8's `-0.0346R` to
  `-0.0020R` and produced `+0.0206R` uplift for downside and `+0.0525R` for
  opening reversal.
- Downside impulse/retest selected `3,000` events, or `1.917` candidate events
  per weekday, with mean `+0.1022R`, PF `1.1569`, drawdown `58.38R`, and event
  AUC `0.6633`. It still failed because only five calibration folds passed and
  F2026 returned `-0.2941R`, PF `0.6331`, despite the action ranker no longer
  losing value in that fold.
- Break-and-run selected `5,642` events, or `3.605` candidate events per
  weekday, with mean `+0.1575R`, PF `1.2531`, drawdown `208.88R`, and event AUC
  `0.5974`. It also had five passing calibration and positive test folds, but
  regressed from V5 in aggregate mean/PF and returned `-0.2274R`, PF `0.7045`,
  in F2026.
- Opening-range reversal improved versus V5 but remained invalid: `2,062`
  selected events, mean `-0.2591R`, PF `0.6767`, drawdown `297.35R`, event AUC
  `0.5433`, zero passing calibration folds, and zero positive test folds.
  F2026 remained negative at `-0.1209R`, PF `0.8359`.
- F2026 event AUC fell to approximately `0.486` for downside, `0.531` for
  break-and-run, and `0.476` for opening reversal. V9 therefore isolates the
  main blocker: horizon choice is no longer the dominant defect; the immediate
  candidate events themselves lose predictable edge in the latest era.

Final definition-contract SHA-256 is
`2f454ea674365fff5a080aaa6f547f3d81829b15156d1ad3a847e4faac1cee01`;
lock-file SHA-256 is
`7d9f342c49b4dada8a133925a4d95d3f3cd923ff20ef9c8af67f0f008e663241`.
Independent verification refitted all `72` paired policies, or `144`
constituent classifiers, reconstructed all `216` calibration policies,
replayed `18` serialized paired models, `47,457` action predictions, and
`39,124` out-of-time pair predictions, and returned
`PAIRWISE_V9_VERIFICATION_PASS`. Artifact-manifest SHA-256 is
`a9e534c36b6eeffcc0833bcaf5b4dd376006da67e0400c2dd85224ebf18c1fbe`.
Package tests pass `10/10`; Ruff and compilation are clean. The final rerun
uses the scikit-learn 1.8-compatible `l1_ratio=0` spelling for fixed L2
regularization and is warning-free.

Do not tune V9 on F2026 or attach it to MT5. Another action router is no longer
the defensible next move. New work must change the causal entry information or
the candidate mechanics, such as a separately preregistered delayed
confirmation/retest action, and then rebuild its labels from raw bid/ask paths.
No terminal, EA, account, deterministic specialist, model server, demo/live
permission, sizing, or broker setting changed.
## Causal Delayed Confirmation Actions V10 - 2026-07-22

- Added and locked `xau-usd/xauusd-fast-research/causal-delayed-confirmation-actions-v10` before generating delayed-entry outcomes. Definition contract SHA-256: `bcb4ecebbd633cdcdb36c35e493928f39ac63915060ea8008b12ec67074c3836`.
- V10 used all 29,419 corrected Complete V5 events and the SHA-verified 708,538-row Dukascopy M5 bid/ask cache. The primary rule required a fixed three-bar directional confirmation within 60 minutes and entered only at the next M5 open. A 15-minute waiting-only control and immediate V5 labels were frozen comparators.
- The full replay produced 51,014 mechanic events and 126,866 side-specific action labels. Six annual tests used calibration-only action selection and episode-level boundary purging. The independent verifier rebuilt every label and returned `DELAYED_CONFIRMATION_V10_VERIFICATION_PASS`.
- Decision: `DELAYED_CONFIRMATION_V10_EVIDENCE_GATE_FAIL`.
- Primary aggregate: 7,158 selected events, 4.573802 events per weekday, +317.5435R, +0.044362R mean, PF 1.068448, 312.4508R maximum drawdown, five positive folds. The weekly-block 95% mean CI was `[-0.009678R, +0.096675R]` and therefore crossed zero.
- Latest F2026 fold: 1,927 events, 7.383142 events per weekday, -262.4610R, -0.136202R mean, PF 0.816689, and 275.1250R drawdown. The latest fold failed both mean and PF gates.
- On paired common events, delayed confirmation was materially worse than waiting alone: -0.224867R mean delta with 95% weekly-block CI `[-0.245915R, -0.203488R]`. It was also worse than immediate execution: -0.332139R mean delta with CI `[-0.361548R, -0.303372R]`. Paired drawdown was more than six times each comparator.
- Lane result: BREAK_AND_RUN remained mildly positive at +0.073249R mean and PF 1.112820, while DOWNSIDE_IMPULSE_RETEST lost -0.075723R per event at PF 0.882306. OPENING_RANGE_REVERSAL never passed the frozen calibration action gate.
- Interpretation: the fixed confirmation identifies directional movement, but entering after that movement chases exhausted price and destroys too much edge. The attractive immediate comparator is diagnostic only because its event subset is known from future confirmation and cannot be traded at the original time.
- Next experiment: preserve immediate causal entry and use the unchanged three-bar/15-minute evidence only as early position management. Stops and targets hit before the checkpoint remain binding; still-open trades that fail validation exit at the first executable M5 open after 15 minutes. No V10 threshold will be tuned in the same version.
- V10 remains offline research only. No Python serving, ML shadow, EA consumption, demo, live, or broker authorization changed. The active V60 demo portfolio was untouched.
## Causal Early Validation Management V11 - 2026-07-22

- Added `xau-usd/xauusd-fast-research/causal-early-validation-management-v11` as the causal follow-up to V10. The corrected replacement definition contract is `24281c3987dab05212fc45a105e294792037d503a6f8445695673cc728975afe`.
- The first execution attempt stopped before managed action labels or P&L were built because 16 source signals were not exactly M5-aligned. The frozen preregistration already made non-exact checkpoints unavailable. The implementation was corrected to omit them, documented in `PREOUTCOME_CORRECTION.md`, retested, and replacement-locked before the first economic run.
- V11 preserved immediate V5 entry, bid/ask spread, protective stop, target, maximum hold, and costs. Any stop/target reached by minute 15 remained binding. Still-open trades passing the unchanged V10 three-bar thresholds retained their original outcome; failures exited at the side-specific minute-15 M5 open.
- The independent verifier rebuilt 29,297 exact contiguous validation events, 145,840 immediate/managed action labels, and returned `EARLY_VALIDATION_V11_VERIFICATION_PASS`.
- Decision: `EARLY_VALIDATION_V11_EVIDENCE_GATE_FAIL`.
- Calibration selected a managed policy only in F2022 and F2026, both for DOWNSIDE_IMPULSE_RETEST. Aggregate managed test result: 900 events, 0.575080 events per weekday, -129.7541R, -0.144171R mean, PF 0.676599, 156.8655R drawdown, and zero positive folds.
- Latest F2026: 401 events, 1.536398 events per weekday, -36.4126R, -0.090804R mean, PF 0.794367, and 65.2805R drawdown.
- Paired against the same immediate event/action, V11 changed mean outcome by -0.029199R. The 95% weekly-block CI was `[-0.101209R, +0.041892R]`; it did not establish improvement. Drawdown ratio was 0.998721, only a negligible reduction.
- State audit across all available actions: 13,558 positions ended before the checkpoint at -0.404552R mean and PF 0.463648; 19,689 validated positions subsequently achieved +0.433357R mean and PF 2.017903; 39,673 failed validations exited at -0.352132R mean and PF 0.046377.
- Interpretation: validation is economically informative, but waiting to enter is too late and entering every candidate before validation incurs losses that the minute-15 exit does not recover. The defensible next test is to predict the fixed 15-minute validation state from causal features available at the original signal, then evaluate immediate entries selected entirely out of time. Final P&L remains evaluation, not the classifier target.
- V11 is offline research only. No runtime authorization or V60 demo portfolio file changed.
## Causal Follow-through Proxy Models V12 - 2026-07-22

- Added and locked `xau-usd/xauusd-fast-research/causal-followthrough-proxy-models-v12`. Definition contract SHA-256: `c3d6af3bb116660da4e4ac3e98c518d19768fda90ca81d473a7970019bc5c3d8`.
- V12 trained separate lane classifiers to predict the independently verified fixed V11 15-minute validation state from the 52 frozen causal V4 event features. Final P&L was never a fit target. Three frozen temporal variants and four frozen retention quantiles were selected only on each fold's calibration year; immediate action ranking was also calibration-only.
- A post-outcome verifier amendment normalized `None` versus `NaN` for abstaining policy rows. It changed no model or result and is documented in `POSTOUTCOME_VERIFICATION_CORRECTION.md`. The original definition lock remains authoritative.
- Independent refit reproduced 16,249 out-of-time event predictions and 3,473 selected trades, returning `FOLLOWTHROUGH_V12_VERIFICATION_PASS`.
- Decision: `FOLLOWTHROUGH_V12_EVIDENCE_GATE_FAIL`, despite a major improvement over V9-V11.
- Aggregate: 3,473 selected events, 2.219169 events per weekday, 2,216 structural episodes, +909.0564 weighted R, +0.592495 weighted mean R, PF 2.372072, 26.3412R weighted drawdown, 61.04% weighted win rate, and validation AUC 0.599345. Weekly bootstrap selected mean 95% interval: `[+0.498771R, +0.675978R]`.
- The selected-minus-baseline weekly bootstrap 95% interval was `[+0.589370R, +0.719388R]`. The unfiltered immediate baseline lost -0.064834R per weighted event at PF 0.907207.
- F2021-F2025 were all positive with PF from 1.860951 to 3.419908. F2026 alone failed: 426 events, 1.632184 events per weekday, -15.4611 weighted R, -0.102054 mean R, PF 0.858913, and 23.9533R drawdown. Latest validation AUC still passed at 0.547589.
- BREAK_AND_RUN aggregate: 2,053 events, 1.311821 per weekday, +0.634082 mean R, PF 2.408501. DOWNSIDE_IMPULSE_RETEST: 1,420 events, 0.907348 per weekday, +0.514262 mean R, PF 2.294421. OPENING_RANGE_REVERSAL never passed calibration.
- In F2026, actually validated selected trades remained profitable at +0.605735R and PF 2.291191; false validations lost -0.385555R at PF 0.532751. The selected set contained only 30.5% actual validations. Score-decile analysis showed the F2026 pass rate did not improve monotonically beyond the eighth decile, so a stricter linear cutoff is not supported.
- Interpretation: the short-horizon proxy is economically meaningful and learnable enough to create high-frequency edge in five folds, but the linear ranking does not preserve sufficient precision in the latest regime. V13 will isolate one change: a shallow, heavily regularized nonlinear classifier. Target, features, folds, quantiles, action policy, gates, and runtime authorization remain frozen.
- V12 is not eligible for serving, shadowing, EA use, demo, live, or broker action. V60 demo trading was untouched.
## Causal Follow-through Nonlinear Models V13 - 2026-07-22

- Added `xau-usd/xauusd-fast-research/causal-followthrough-nonlinear-models-v13` as a one-change adaptation of V12. The target, 52 features, folds, temporal variants, quantiles, action policy, gates, and authorization were inherited unchanged; only the classifier became a shallow regularized histogram gradient boosting model.
- Definition contract SHA-256: `a6182e5d75b30f85d1e4f0ed6d3805ab04b0af71865c7d18453f3d29c26acad1`.
- A post-outcome verifier-only correction changed the JSON normalizer call to the pinned economics module. It is documented in `POSTOUTCOME_VERIFICATION_CORRECTION.md`; no model, prediction, metric, or result changed.
- Independent refit reproduced 16,249 out-of-time predictions and 3,594 selected events, returning `FOLLOWTHROUGH_V13_VERIFICATION_PASS`.
- Decision: evidence gate fail. The inherited implementation reports the literal status string `FOLLOWTHROUGH_V12_EVIDENCE_GATE_FAIL`; the package and verifier identify the experiment as V13.
- Aggregate V13: 3,594 events, 2.296486 per weekday, +0.435498 weighted mean R, PF 1.916329, 57.2335R weighted drawdown, and validation AUC 0.589570.
- F2026: 370 events, 1.417625 per weekday, -0.273462 weighted mean R, PF 0.648405, 51.3437R weighted drawdown, and validation AUC 0.529625.
- V13 is inferior to V12: lower aggregate mean/PF/AUC, more than double drawdown, and substantially worse latest-fold economics and AUC. Additional nonlinear capacity is rejected as the next route.
- Next analysis must focus on causal regime/proxy-health detection or genuinely new pre-entry information. Do not expand classifier complexity or simply tighten the unstable linear score tail.
- No runtime or V60 demo authorization changed.

## Causal Follow-through Health Circuit V14 - 2026-07-22

- Added `xau-usd/xauusd-fast-research/causal-followthrough-health-circuit-v14` as a development-only health overlay on the stronger V12 linear model. Definition contract SHA-256: `a86d8d387bec7c0f0b83e0698f5528fa6b5261c153001c8facff81bf023e0262`.
- The first execution attempt stopped before reading model predictions because the lightweight package omitted the pinned scikit-learn dependency. The dependency-only correction is documented in `PREOUTCOME_CORRECTION.md`; the replacement contract was locked before any economic output was read.
- V14 processes V12 would-be selected events chronologically. At each event it observes only validation labels whose fixed 15-minute availability time has passed, measures the standardized residual over the last 100 completed labels, and abstains when the residual is below `-1.5`. Same-timestamp decisions share identical prior state, and blocked events continue to supply later labels.
- The `-1.5` alarm threshold was selected after all historical outcomes through F2026 were exposed. V14 is therefore development evidence only and cannot be described as an untouched confirmation test.
- Independent verification replayed all 3,580 chronological decisions and 2,845 allowed events and returned `FOLLOWTHROUGH_HEALTH_V14_VERIFICATION_PASS`.
- Decision: `FOLLOWTHROUGH_HEALTH_V14_DEVELOPMENT_GATE_FAIL`. Twelve of thirteen locked checks passed; only the latest-fold PF gate failed.
- Aggregate V14: 2,845 events, 1.817891 per weekday, 1,808 structural episodes, +867.3818 weighted R, +0.674079 weighted mean R, PF 2.698530, 14.2361R weighted drawdown, and 64.31% weighted win rate.
- Against V12, V14 retained 81.92% of events, improved weighted mean by approximately +0.081584R, and reduced drawdown to 54.05% of V12. The weekly-block 95% health-minus-V12 mean interval was `[+0.046628R, +0.117026R]`.
- F2026 became slightly positive: 232 events, 0.888889 per weekday, +2.0016 weighted R, +0.025306 mean R, PF 1.037495, and 9.3700R drawdown. The locked PF requirement was at least 1.05, so the result was correctly rejected. Removing the latest fold's 20 largest winners also made its mean negative, reinforcing that the apparent recovery is fragile.
- Do not tune the V14 threshold on the same exposed history. Preserve V12 and V14 as frozen development candidates and seek genuinely new prospective labels for confirmation, or introduce separately preregistered new causal information. No Python serving, ML shadow, EA consumption, demo, live, broker, or V60 authorization changed.

## Causal Follow-through Lane Health V15 - 2026-07-22

- Added and locked `xau-usd/xauusd-fast-research/causal-followthrough-lane-health-v15` as a one-change exposed-history development test. Definition contract SHA-256: `c41249c5491d76ca3ac0f1efe601379846fb6f82171018c3b30b705f0b147f5b`.
- V15 inherited the frozen V14 population, V12 model, actions, 15-minute label delay, 100-label window/startup, `-1.5` threshold, folds, economics, and authorization. It changed only the health-state scope from pooled to separate state per model lane. It also preregistered latest-frequency, latest-winner-robustness, and direct V14 comparison gates before the economic run.
- Independent verification replayed all 3,580 chronological decisions and 3,048 allowed events and returned `FOLLOWTHROUGH_LANE_HEALTH_V15_VERIFICATION_PASS`.
- Decision: `FOLLOWTHROUGH_LANE_HEALTH_V15_DEVELOPMENT_GATE_FAIL`.
- Aggregate V15: 3,048 events, 1.947604 per weekday, +0.642393 weighted mean R, PF 2.567619, and 18.1640R weighted drawdown. These remain strong exposed-history development economics but are inferior to V14's mean, PF, and drawdown.
- F2026 frequency rose to 1.340996 events per weekday, but economics deteriorated to -0.033126R mean, PF 0.952440, -4.1885 weighted R, and 13.4055R drawdown. Removing the 20 largest winners left -0.356788R mean.
- V15 failed latest mean, latest PF, latest winner robustness, six-positive-fold, V14 drawdown, and V14 mean-delta confidence gates. The pooled V14 state was providing useful cross-lane protection; lane-local monitoring is rejected and must not be tuned on this history.
- Preserve V14 as the better frozen development candidate, still not an authorization candidate. The next meaningful evidence is new post-`2026-07-01` candidate/market data generated under a frozen acquisition and scoring contract. No runtime or V60 demo authorization changed.

## Post-cutoff Dukascopy XAU evidence - 2026-07-22

- Added `multi-asset/data-foundation/dukascopy-xau-prospective-v1`, a data-only, resumable official-Dukascopy snapshot tool. It caps concurrency at four, excludes the open UTC hour, validates each source payload, uses no paid source, and contains no strategy or broker action.
- Acquired all 519 completed UTC hours from `2026-07-01T00:00:00Z` through `2026-07-22T15:00:00Z` exclusive into the external `D:` archive: 5,531,969 validated bid/ask ticks and 123,778,402 raw bytes.
- Raw snapshot manifest: `D:/AlgoTradingData/C_DRIVE/DukascopyTickDataFoundationV1/prospective-v1/manifests/XAUUSD_2026070100_2026072215_PROSPECTIVE_SNAPSHOT.json`; SHA-256 `ed6243f20e08c999b2d8333686fcb3bc3c341c56bf223194722f451d004da88e`.
- Independent snapshot verification checked contiguous coverage, official URLs, path containment, all 519 file hashes, all decoded payloads, tick counts, and byte totals and returned `DUKASCOPY_XAU_PROSPECTIVE_SNAPSHOT_VERIFICATION_PASS`.
- Built a separate append-only 4,272-row prospective M5 feature file. Before writing July, the builder reconstructed 276 June 30 bars from raw ticks and matched every frozen base OHLC/microstructure field with maximum absolute error `8.858608291362202e-13`.
- Prospective M5 file: `D:/AlgoTradingData/C_DRIVE/DukascopyTickDataFoundationV1/prospective-v1/features/XAUUSD_2026070100_2026072215_M5_FEATURES_V1.parquet`; SHA-256 `e957dee3ff09c8a7ae17387306a4f9162928aef64bea9eaa3ee170058f1e9231`.
- The frozen historical cache was not modified. July has not been used to tune, fit, score, or evaluate V12/V14. The remaining requirement is a frozen generator/export for the same BREAK_AND_RUN, DOWNSIDE_IMPULSE_RETEST, and OPENING_RANGE_REVERSAL candidate families, followed by causal 15-minute labels and one-shot V12/V14 scoring. No ML shadow or runtime authorization changed.

## Post-cutoff MT5 candidate export - 2026-07-22

- Added `xau-usd/xauusd-fast-research/mt5-candidate-prospective-v1` and froze
  its candidate-only contract before running an isolated Strategy Tester at
  `C:/MT5A1M5MomentumBacktest`. The active account `1033030` terminal and V60
  deterministic demo portfolio were not changed.
- The exact previously parity-tested binaries and sources generated 302
  `WOULD_SIGNAL` rows from July 1 through July 20 at 100% MT5 history quality:
  34 downside impulse/retest, 39 opening-range reversal, and 229 break-and-run.
  Tester P/L was ignored; all economics were rebuilt from Dukascopy bid/ask.
- Candidate contract SHA-256 is
  `9280aea6d9566da4d33077b67e2b5bc4134046f3c18162cb1e50356113be07ac`;
  evidence SHA-256 is
  `975afa614283a3f719ca272bd1fcc639955eb4eb30c64ffa61540a71028acde6`;
  manifest SHA-256 is
  `3d4c8973cff0e4854e831dda1af51bb5ea2d7d4214d59e74b81bc8f3c08d74a5`.
  Independent verification passed.

## Prospective Follow-through Confirmation V16 - 2026-07-22

- Added and froze
  `xau-usd/xauusd-fast-research/causal-followthrough-prospective-confirmation-v16`
  before exposing July outcomes. It reconstructed causal V4 events, V11
  15-minute labels, the exact frozen F2026 V12 models and policies, and the
  unchanged pooled V14 health circuit. No model or threshold was refitted.
- Definition-contract SHA-256 is
  `46e201e2100cad24d3c2fa9323acd95d992e5f5661df131d8ced6957f74d0426`.
  Independent reconstruction returned
  `PROSPECTIVE_CONFIRMATION_V16_VERIFICATION_PASS`.
- Decision: `PROSPECTIVE_CONFIRMATION_V16_PROVISIONAL_GATE_FAIL`. Of 302 raw
  candidates, 281 had complete features and 22 were selected across 18
  structural episodes. Frequency passed at 1.571429 events per observed
  weekday, but the result was -6.9584R, -0.637740R mean, PF 0.308085, and
  7.2773R weighted drawdown.
- Break-and-run supplied 20 selected events and lost -6.5317R at PF 0.3217.
  Downside supplied two and both lost. Every selected event was in CHOP or
  TRANSITION_UNKNOWN. Break-and-run validation-score AUC was 0.5102 and V14
  blocked zero events. July is now exposed development history and may never
  be called untouched confirmation again.
- The frozen V12/V14 prospective hypothesis is rejected for this window. No
  runtime, demo, live, shadow, serving, account, sizing, or broker permission
  changed.

## Regime-local Follow-through Experts V17 - 2026-07-22

- Added and locked
  `xau-usd/xauusd-fast-research/causal-followthrough-regime-experts-v17` to
  test one structural change: separate linear validation models per lane and
  regime, with no global fallback for cells below 400 fit or 150 calibration
  events. The V12 target, 52 features, model class, temporal variants,
  quantiles, and fold-local action rankings remained fixed.
- Definition-contract SHA-256 is
  `45bc89f42482b3374cb58e1a1284705db65244eb9fbc85a010a126501c55c6bd`;
  lock-file SHA-256 is
  `ece14a0bec845bcf414cc1992bba1b010fa015e7a063b02a2a31cebcea78715f`.
  A documented verifier-only normalization reconciles `NaN` versus `None` and
  empty Parquet frames without changing any model or result. Independent
  recomputation returned `REGIME_EXPERT_V17_VERIFICATION_PASS`.
- Decision: `REGIME_EXPERT_V17_DEVELOPMENT_GATE_FAIL`. Aggregate historical
  development remained positive with 2,804 events, 1.791693/day, +0.334973R
  mean, PF 1.624101, and AUC 0.578184. F2026 failed at 557 events,
  -0.148216R mean, PF 0.801416, and 40.5741R drawdown. Its CHOP plus
  TRANSITION_UNKNOWN subset lost -0.332387R at PF 0.593324.
- Every final July cell abstained because no current lane-regime policy passed
  pre-cutoff calibration. That avoids another July loss but supplies zero
  frequency and no deployable model. Regime separation alone is closed.
  Artifact-manifest SHA-256 is
  `46c8209bdcc543776e411ae86597a71013b57a3a7ac1db2177b574ab2a472d64`.

## Free Prospective DXY/Treasury Foundation - 2026-07-22

- Added `multi-asset/data-foundation/dukascopy-macro-prospective-v1`. It uses
  only the official free Dukascopy endpoint, caps concurrency at four, excludes
  the open UTC hour, forbids Databento and paid sources, and contains no
  strategy or broker action.
- Acquired and independently verified 1,038 symbol-hours from July 1 through
  July 22 15:00 UTC exclusive for DOLLARIDXUSD and USTBONDTRUSD: 204,834 ticks
  and 5,550,051 raw bytes. Snapshot SHA-256 is
  `ea7dc6c1e632ab00f67d84a7870cfe0f5212c5e7ba05fd41b7f203b66bdbf1ab`.
- The M5 builder matched all 266 frozen June 30 historical bars exactly with
  maximum absolute error 0.0, then wrote 4,077 prospective rows. Feature
  SHA-256 is
  `f39a8006897660c72e52dc088431815dc562a105d1a4cd0294bc1646877233f9`;
  feature-manifest SHA-256 is
  `7e7ee2cc56d90cd895a6cf06809a032bdbfb77e52ee7fe6b3381cc0830f6e5ea`.
  A read-only verifier rebuilt the complete feature frame from raw files and
  passed.

## Macro Follow-through Models V18 - 2026-07-22

- Added and locked
  `xau-usd/xauusd-fast-research/causal-followthrough-macro-proxy-models-v18`.
  It changed only the V12 information surface by adding the same eight causal
  completed-M15 DXY/Treasury pressure features used in V6. Joins are backward
  with ten-minute maximum staleness; missing history is fixed neutral zero
  without a missingness indicator.
- Definition-contract SHA-256 is
  `5b868f884eef05238a453317e078ed2e9bb66d97decb449e70cb8bf5d3cd2d4a`;
  lock-file SHA-256 is
  `3ba6dce121fa0372d56024ee1a2fa9c5d51114abcb88646105af5cda0a8a559d`.
  Independent refit returned `MACRO_FOLLOWTHROUGH_V18_VERIFICATION_PASS`.
- Decision: `MACRO_FOLLOWTHROUGH_V18_DEVELOPMENT_GATE_FAIL`. Historical
  aggregate remained strong but slightly regressed from V12: 3,586 events,
  2.291374/day, +0.576895R mean, PF 2.354856, and AUC 0.600902. Mean regressed
  0.015600R and PF regressed 0.017216. F2026 worsened to -0.157079R, PF
  0.787870, and 31.1288R drawdown.
- July selected 25 events at 1.785714/day and lost -5.9000R, with -0.532601R
  mean, PF 0.397976, 6.5377R drawdown, and validation AUC 0.519011. The macro
  features did not repair current ranking.
- Post-outcome mechanism diagnostics show why another classifier tweak is not
  the next move. Every fixed break-and-run action was negative in July, and
  even its hindsight-best available action averaged -0.0212R. Opening-range
  reversal happened to be positive in July, but all fixed actions were
  negative in F2024, F2025, and F2026, so promoting it would be recent-window
  overfitting. The next research change must redesign candidate/execution
  mechanics or add genuinely richer pre-entry path information, then reserve
  new unseen weeks for confirmation.
- Artifact-manifest SHA-256 is
  `21dab1f0a2887a7593b79e80bbb5e6460c830be5806e51c5b76b1de10e572802`.
  No ML runtime, deterministic V60 demo component, terminal, account, sizing,
  broker setting, or authorization changed.

## Completed-bar Clock Audit - 2026-07-22

- Audited the MT5 candidate clock through the EA, CSV reader, Dukascopy cache
  loader, feature join, and action-label entry. The raw parquet timestamp is
  the M5 bar start, while the loader deliberately sets `timestamp_utc` to the
  bar end. A candidate logged at `T` therefore uses the completed bar ending
  at `T`, and its simulated action enters the new bar beginning at `T`.
- The July reconstruction matched all 281 feature-complete candidates to the
  exact completed bar end. Every source bar began strictly before its signal.
  Median MT5-versus-Dukascopy signal-close error was $0.165 and maximum error
  was $0.535. The suspected look-ahead issue was a false alarm caused by
  initially comparing against the raw bar-start field without applying the
  loader's documented five-minute completion offset.

## Path Sequence Follow-through Models V19 - 2026-07-22

- Added and locked
  `xau-usd/xauusd-fast-research/causal-followthrough-path-sequence-models-v19`.
  It changed only the V12 information surface by adding 13 frozen causal path
  features from the prior 3-12 completed M5 bars. Sequences reset across data
  gaps, incomplete history is neutral with an explicit indicator, and an
  exact completed-bar-end join forbids future bars.
- Definition-contract SHA-256 is
  `f34253b8fe25b0c91f0dc51719199c3d6c35268c4769a7d599ef8afe186682d2`.
  Independent refit returned `PATH_FOLLOWTHROUGH_V19_VERIFICATION_PASS`; all
  three package tests and Ruff passed.
- Decision: `PATH_FOLLOWTHROUGH_V19_DEVELOPMENT_GATE_FAIL`. Historical results
  were 3,500 events, 2.236422/day, +0.556234R weighted mean, PF 2.246017, and
  AUC 0.599605. Versus V12, mean regressed 0.036260R and PF regressed 0.126055;
  the AUC gain was only 0.000260.
- F2026 remained negative at 424 events, 1.624521/day, -0.137729R weighted
  mean, PF 0.812367, and 27.2339R drawdown. July selected 24 events at
  1.714286/day and lost -3.3193 weighted R: -0.312810R mean, PF 0.611943,
  4.0138R drawdown, and validation AUC 0.500099.
- The combined V12-V19 evidence rejects additional feature-only work on these
  three high-frequency continuation candidate mechanisms. The next branch
  must create a genuinely different candidate mechanism for the current
  chop/transition environment, while V60 deterministic demo operation remains
  separate and unchanged. No ML runtime, shadow, EA, demo, live, account,
  sizing, or broker authorization changed.

## Failure Root-Cause Audit V1 and Adverse Rejection Fade V20 - 2026-07-23

- Added and independently verified
  `xau-usd/xauusd-fast-research/research-failure-root-cause-audit-v1`.
  The audit ranked candidate-edge decay, training-population mismatch,
  proxy-target/action mismatch, nonstationary calibration, episode dependence,
  and research multiplicity as the principal causes. Its decision was
  `ROOT_CAUSE_AUDIT_COMPLETE_NEW_MECHANISM_REQUIRED`; definition SHA-256 is
  `79d6d8ec9f06a9a463073207983a0a600bb7490a7b1055066eca14299d0f9a89`.
- The audit retired more static features, classifier complexity, threshold-only
  recalibration, static regime experts, immediate bidirectional routing, the
  old delayed-confirmation design, and forced two-trade-per-day selection.
- Added and froze
  `xau-usd/xauusd-fast-research/causal-adverse-rejection-fade-v20` to test the
  audit's distinct nominated mechanism. It uses only BREAK_AND_RUN and
  DOWNSIDE_IMPULSE_RETEST events in CHOP or TRANSITION_UNKNOWN, observes exactly
  three complete M5 bars, requires a fixed strong opposite-direction rejection,
  and enters the exact opposite direction at the next M5 open. It fits no ML.
- Pre-outcome loader, ownership-count, M5 alignment, and market-closure repairs
  are recorded in `PRE_OUTCOME_REPAIR.md`. After payoff generation showed every
  policy abstained, a report-only empty-frame repair was recorded separately in
  `POST_OUTCOME_REPAIR.md`. No threshold, policy, gate, or authorization was
  altered. Final definition SHA-256 is
  `639cdd985630beedf27db0ce369a089702e7edc59ec7d24b4499057cff03243d`.
- Decision: `ADVERSE_REJECTION_FADE_V20_EVIDENCE_GATE_FAIL`. The deterministic
  replay produced 34,603 mechanic events and 84,054 stressed bid/ask action
  labels. Every one of 36 fold/mechanic/lane policies abstained, leaving zero
  historical selections and zero July selections.
- The failure is decisive rather than a sample-size technicality. Historical
  BREAK_AND_RUN fade means were -0.3440R, -0.3946R, and -0.3907R across the
  fast, intraday, and swing actions, with PF 0.498-0.530. Historical downside
  fade means were -0.4976R, -0.4079R, and -0.3700R, with PF 0.311-0.555. Every
  annual calibration cell had negative mean and PF below one.
- July BREAK_AND_RUN fast fade was only marginally positive at +0.0242R and PF
  1.0504 over 39 raw labels; the other July actions and every downside action
  were negative. It cannot be promoted against uniformly negative historical
  calibration.
- Independent full replay returned
  `ADVERSE_REJECTION_FADE_V20_VERIFICATION_PASS`, reproducing all 34,603 events,
  84,054 labels, zero selections, artifact hashes, timing, direction reversal,
  and July cutoff. This exact rejection-fade mechanic is retired and its gates
  must not be loosened.
- The next defensible candidate branch must originate from a new market event,
  not mirror or re-rank the decayed continuation logs. A preregistered
  session-range liquidity sweep/reclaim generator with its own causal entry and
  action geometry is the leading hypothesis. V60 deterministic demo operation,
  account 1033030, MT5 terminals, sizing, and all broker/runtime permissions
  remain separate and unchanged.

## V60 Demo No-Trade Diagnosis And Feed Heartbeat Repair - 2026-07-23

- Account `1033030` had no broker trades because the canonical executor had
  received zero candidates since activation. There were no order rejections,
  open XAUUSD positions, drawdown stops, guardian halts, account mismatches, or
  terminal disconnections. The observer-only EA logs contained `GUARD_BLOCK`
  diagnostics and were not broker orders.
- The full broker-action window after the owner-authorized balance waiver began
  at `2026-07-22T08:37:32Z`; the apparent elapsed time from initial chart
  attachment overstated the fully eligible demo observation period.
- A separate availability defect was found and repaired. The executor required
  a feed-status age no greater than 180 seconds, while a synchronous R5 refresh
  had produced feed-update gaps as long as 982 seconds. Since the latest worker
  restart, this caused approximately 0.90 hours of fail-closed time and 93.0%
  measured availability. No candidate was present during those intervals, but
  the mismatch could have delayed a future valid candidate.
- `run_feeds.py` now publishes a 30-second heartbeat during feed computation.
  The executor still fails closed when the heartbeat is older than 180 seconds
  or one computation cycle exceeds 20 minutes. Fast Core feeds and add-ons now
  run before the slow R5 transition refresh so their append-only candidates are
  visible without waiting for R5.
- Feed and executor workers were restarted with persistent `state.json`
  retained. A six-minute runtime observation crossed the scheduled slow cycle:
  every sample remained `ACTIVE_DEMO_BROKER_ACTION`, feed age remained bounded,
  and candidate count stayed zero. Current ML runtime and ML shadow authority
  remain false; no signal rule, threshold, fixed lot, risk limit, or live
  authorization changed.
- Focused verification is `16 passed`; Ruff, Python compilation, and `git diff
  --check` pass.
- A final-year historical gap audit found 364 trades across 261 weekdays, with
  96 zero-trade weekdays (36.8%) and a longest run of 12 consecutive zero-trade
  weekdays. Therefore a quiet day remains expected behavior even with a fully
  healthy runtime; the portfolio average of 1.395 trades per weekday is not a
  daily quota.

## Loss-Signature One-Class Experiment V1 - 2026-07-23

- Added and froze
  `xau-usd/xauusd-fast-research/causal-loss-signature-one-class-v1` as the
  requested research-only experiment. Six deterministic Isolation Forests were
  fitted exclusively on losing FIT rows from Expanded Dataset V4. No winning
  row entered model fitting, feature preparation, or threshold selection.
- The population contains 73,116 resolved actions, including 42,067 losses and
  31,049 winners, with 58 finite causal features. Evaluation used 53,206
  out-of-time rows across the six purged F2021-F2026 folds.
- The pooled weighted loss AUC was 0.558681. The frozen veto flagged 14.22% of
  weighted actions; 69.93% of flagged actions were losses versus a 62.94%
  baseline loss rate. Loss recall was 15.79%, and winner collateral was 11.54%.
- Removing flagged actions improved weighted PF from 0.762060 to 0.789998 and
  reduced the closed-action drawdown statistic from 1,895.96R to 1,410.87R.
  Retained mean outcome improved by 0.022253R, with a weekly-block-bootstrap
  95% interval of 0.013710R to 0.030865R.
- Decision: `LOSS_ONLY_SIGNATURE_NO_RELIABLE_PROGRESS`. Eleven of twelve
  preregistered checks passed, but the pooled retained-EV gain missed the
  required 0.030R threshold. The latest F2026 fold was especially weak, with
  AUC 0.521066 and retained-EV improvement of only 0.004970R.
- The first verifier invocation exposed only an ambiguous pandas index/column
  sort. `POST_RUN_REPAIR.md` records the index reset repair. No data, feature,
  model, threshold, gate, prediction, or metric changed. The package was then
  re-locked and rerun under definition SHA-256
  `03f820a9c22094d621afd5d77121cc0d6a29406f6f1a72769b7ae13b46588817`.
- Independent refitting reproduced every model score, threshold, flag,
  bootstrap result, and acceptance decision:
  `LOSS_ONLY_V1_VERIFICATION_PASS`. Four focused tests and Ruff pass. No ML
  shadow, EA, terminal, demo/live, account, sizing, broker, or runtime setting
  changed.

## Canonical Expected-R V10 And Availability V11 - 2026-07-23

- Added and froze
  `xau-usd/xauusd-fast-research/causal-canonical-expected-r-v10`. The model
  predicts stressed net R rather than direction or win probability. It uses 36
  causal numeric features, shared global effects, nine family intercepts, and
  strongly shrunk family-by-feature deviations. Both winners and losers enter
  fitting; historical decision fields, journey rows, outcomes, identity, COMEX,
  and demo trades do not enter predictors.
- Six purged outer tests contain 2,368 candidates. V10 selected 1,622 at
  1.039078 candidates/weekday. Weighted mean improved from 0.250986R to
  0.309081R, PF from 1.414241 to 1.524791, and the candidate-sequence drawdown
  measure from 74.6915R to 53.9550R. Weighted score AUC was 0.533676.
- The 5,000-week-block bootstrap gave a 95% interval of 0.195792R to
  0.420158R for selected mean and 0.009446R to 0.109454R for uplift. V10 passed
  all 18 machine gates and independently reproduced every model, score,
  threshold, flag, bootstrap interval, acceptance check, and final model:
  `EXPECTED_R_V10_VERIFICATION_PASS`.
- The post-outcome audit found an important weakness despite the machine pass:
  V10 reduced mean outcome in F2020 and F2021, whose fit populations were only
  548 and 817 rows. It improved every fold from F2022 onward, once fit rows
  reached 1,162. `POST_OUTCOME_AUDIT.md` records that the preregistration prose
  was stricter than the machine gate and prevents treating V10 alone as final.
- Added and separately froze
  `xau-usd/xauusd-fast-research/causal-canonical-expected-r-availability-v11`.
  V11 requires at least 1,000 fit rows before ML may filter. Below that floor,
  ML abstains and retains every deterministic candidate. It changes no V10
  model, score, family threshold, or outcome.
- V11 selected 1,808 candidates at 1.158232/weekday. Weighted mean improved
  from 0.250986R to 0.315570R, PF from 1.414241 to 1.540228, and drawdown from
  74.6915R to 53.9550R. All active folds improved; the two unavailable folds
  were unchanged. The latest F2025 fold retained 1.030888 candidates/weekday,
  0.361416R mean, and PF 1.659109.
- V11's weekly-bootstrap 95% uplift interval was 0.023251R to 0.107234R, and
  its selected-PF interval was 1.334339 to 1.761977. It passed all 21 gates and
  returned `EXPECTED_R_AVAILABILITY_V11_VERIFICATION_PASS`. The final offline
  model has 2,851 fit rows, including 1,270 winners and 1,581 losers, so the
  V11 availability gate is active. End-to-end offline scoring also passed.
- Decision:
  `EXPECTED_R_V11_WORKING_OFFLINE_MODEL_FORWARD_CONFIRMATION_REQUIRED`.
  This is the first working, independently verified offline candidate-quality
  model in the campaign. It is not fresh proof because all historical outcomes
  were already exposed during development. New prospective outcomes remain
  mandatory before considering any shadow or execution role.
- V10 definition SHA-256 is
  `cee3154af687944880ff15d3e96761cf4e55a24cc29100fc925d99c42224ef42`.
  V11 definition SHA-256 is
  `676e657ac5af3eb7beead0e26d5caef2b06142c537f2034f23eec5c6ae8f4279`.
  No ML shadow, EA, terminal, demo/live, account, sizing, broker, or runtime
  setting changed.

## R5 Causal Specialist Closure V43-V46 - 2026-07-26

- V43 froze an outcome-blind structural screen of all 1,000 macro/residual
  transition definitions on independently generated Dukascopy and Capital
  candidate clocks. It found 473 structurally eligible definitions, fixed 24
  diverse components without outcomes, and wrote 3,068 outcome-free consensus
  candidates. Contract SHA-256:
  `36cc6baba4fae1d8666795742d53d5a99ebc623e839569e207440f0ef31c2a18`.
- V43 development evaluated 823 component trades. No component survived the
  preregistered Benjamini-Hochberg false-discovery correction. Attempts 23811
  and 25116 had the strongest descriptive development evidence, but V44's
  fixed untouched 2023-2026 confirmation rejected them: 22 portfolio trades,
  -4.941778R, PF 0.713212, -0.224626R mean, and 8.154514R drawdown. V44
  contract SHA-256:
  `d8ff0e6935ab946db78e9d7668c84964ee17881f79080d03f9135debc48fb9c4`.
- V45 fixed all 22 remaining validation-unopened V43 components and tested a
  distinct causal policy: both feeds had to clear 0.10R on the first completed
  M5 bar and the component's latest five fully closed paired shadow outcomes
  had to be positive with PF at least 1.10. Development failed decisively:
  82 routed trades, -36.632619R, PF 0.434392, -0.446739R mean, 38.396389R
  drawdown, and zero positive components. V45 validation remained unopened.
  Contract SHA-256:
  `f03037eca28e3b3d780588334ee27d6bdb22deab19a4f595ec80d97e1a69b8f0`.
- V46 fixed the only remaining development-positive component, attempt 24936,
  before opening its exact 2023-2026 outcomes. The single-factor resolution
  specialist produced 20 validation trades, +0.549048R, PF 1.041890,
  +0.027452R mean, and 5.716435R drawdown. It failed both-feed PF, conservative
  PF/mean, first-era positivity, and winner-removal robustness; removing the
  two largest winners left -4.757321R. Contract SHA-256:
  `1bd65e1a8067ce252e1f50c72557d12d6a784162cb2a88beac63530e20cfe975`.
- Two additional fixed diagnostics rejected the remaining distinct ideas. An
  expanding causal nearest-neighbour analogue policy produced 237 walk-forward
  trades, -1.890935R, PF 0.994349, and 64.030577R drawdown. Strict dual-feed
  consensus of the independently generated V16 exhaustion signals produced 21
  matches at 15-minute tolerance, -2.108R, and PF 0.831; a one-hour tolerance
  remained economically negligible at 25 trades, +1.078R, and PF 1.079, with
  no matched events in 2016H2-2020.
- R5 hindsight labels remain an upper bound, not executable evidence. The
  1,327 classified R5 oracle trades were selected after future paths were
  visible. Direct causal imitation, mechanism campaigns, ML classification and
  value routing, health routing, second-source replication, and sealed
  confirmation have not recovered a stable R5 edge.
- Current R5 policy is therefore `NO_TRADE_R5_TRANSITION`. This is a valid
  causal abstention decision, not a failed attempt to fill frequency. Frozen
  V34 transition definitions may continue read-only prospective collection,
  but they have no Python-serving, EA, demo, live, sizing, account, or broker
  authority. Do not tune V43-V46 or relabel their exposed periods as holdout.
- The V60 executor source registry was reconciled with that decision:
  `R5_TRANSITION` and its old attempt `23925` were removed from the broker-action
  source set. The R5 component, outcome, and router feeds remain mandatory
  read-only research inputs, and a regression test prevents silent
  reauthorization.
- The previously dead V40 R1-R4 outcome path was transported into V60 as the
  required `CORE_OUTCOMES` feed on account `1033030`. It reuses the locked V40
  causal resolver unchanged, consumes the active R1 pullback/R2/R3/R4 candidate
  folders plus raw Capital bid/ask files, and writes append-only individual
  labels below `v60_canonical_demo_v2/feeds/core_outcomes`. Aggregate economics,
  tuning, ML, EA use, and broker action remain disabled.

## R2-R4 Untouched Capital Confirmation V47 - 2026-07-26

- The strongest remaining non-R5 historical candidates are still R2
  downtrend, R3 compression, and R4 chop. Their descriptive historical results
  are R2: 118 trades, +65.99R, PF 1.77, 19.64R drawdown; R3: 118 trades,
  +44.65R, PF 1.56, 8.33R drawdown; and R4: 125 trades, +41.90R, PF 1.59,
  8.39R drawdown. These remain candidates, not proof: R2/R3 were nominated
  after outcomes were visible, and R4's 1,000-policy selection-adjusted
  significance was 1.0.
- Added and locked
  `xau-usd/xauusd-fast-research/capital-r2-r4-prospective-confirmation-v47`.
  It evaluates the exact frozen R2/R3/R4 rules on new account `1033030`
  Capital bid/ask data beginning `2026-07-27T00:00:00Z`. Contract SHA-256 is
  `7f5183ee03b4aec3d062e558527c2e5ebfa45181524ee3959db069e6d8af19e3`;
  it was created at `2026-07-26T01:37:41.177202Z`, before the boundary, with no
  aggregate economics present.
- V47 consumes the transported V40 append-only candidate/outcome ledgers. It
  does not modify candidates, signals, EAs, account risk, or demo permissions.
  Every candidate through a stage endpoint must have a final resolution,
  including non-eligible-day candidates that could alter V28 overlap routing.
- An eligible Capital day requires at least 100,000 unique quote
  milliseconds, a start no later than 02:00 UTC, an end no earlier than 22:00
  UTC, p99 interquote gap no greater than five seconds, duplicate share no
  greater than 5%, exact account/server/symbol identity, and all execution
  authority false.
- Validation uses the first outcome-blind endpoint with at least 20 eligible
  days, 10 total routed trades, and two trades from each specialist, capped at
  260 days. It requires positive stressed net, PF at least 1.10, mean at least
  0.05R, drawdown at most 10R, positive net after removing the largest winner,
  and positive PF-at-least-1.00 evidence from every specialist.
- A passing validation opens a disjoint confirmation stage requiring at least
  40 eligible days, 30 total trades, and five from each specialist, capped at
  520 days. Confirmation requires PF at least 1.20, mean at least 0.10R,
  drawdown at most 15R, positive net after removing the two largest winners,
  and positive PF-at-least-1.05 evidence from every specialist.
- The first real cycle returned
  `WAITING_FOR_UNTOUCHED_VALIDATION`: zero post-boundary eligible days, zero
  trades, zero unresolved candidates, and `aggregate_economics_opened=false`.
  Seven focused tests, Python compilation, source loading, and contract
  self-verification pass.
- The independent hidden V47 watcher started at local `2026-07-26 05:38:32`
  with launcher PID `28824` and worker PID `21420`. Runtime stdout is
  `C:/MT5PortableTier1BestEA/MQL5/Files/v47_r2_r4_evaluator.stdout.log`;
  stderr is the adjacent `.stderr.log` and is empty. It is separate from V60,
  so a research evaluator failure cannot halt demo execution.
- V60 remains healthy on account `1033030`: feed launcher/worker PIDs
  `42008`/`45896`, portfolio launcher/worker PIDs `40444`/`45588`, all nine
  required feed groups healthy, executor
  `ACTIVE_DEMO_BROKER_ACTION`, no open XAUUSD position at this checkpoint, and
  ML runtime/shadow authority false. R5 is absent from the executable source
  registry and remains read-only research only.

## R4 Pre-2016 Out-of-Era Replication V48 - 2026-07-26

- Added and locked
  `xau-usd/xauusd-fast-research/r4-pre2016-out-of-era-replication-v48`.
  It reconstructed the exact V26 R4 three-component policy on 78 frozen
  Dukascopy monthly raw-tick archives from 2010-01 through 2016-06. Candidate
  facts were built and hash-locked before outcomes. Contract SHA-256:
  `ce691c0c4c45db6b626c77d0395de931f8d3a9d1f972f174560adf8d4cc57f0c`.
- The reconstruction produced 468,279 M5 bars and 429 unique candidates.
  Exact parity against the independent pre-2016 M5 cache passed for every
  timestamp and all 12 bid/ask/mid OHLC fields with zero maximum error.
- The sealed result independently verified but failed the preregistered gates:
  90 trades, +0.898570R, +0.009984R mean, PF 1.014811, 14.245372R drawdown,
  and -8.473415R after removing the five largest winners. The 20,000-resample
  UTC-week bootstrap 90% mean interval was -0.229176R to +0.247832R.
- Era results were +6.508R/PF 1.502 for 2010-2012, -1.040R/PF 0.955 for
  2012-2014, and -4.570R/PF 0.815 for 2014-mid-2016. Result SHA-256:
  `224cf9808bd9aca576a62e86b025e420a0b201b3766258e38c78b9b050b7e172`.
- Weakness was concentrated in component `40193`, which returned -5.714R and
  PF 0.813. Components `39888` and `39427` were descriptively positive at
  +5.282R/PF 1.204 and +1.330R/PF 1.316. Those component observations used
  V48 outcomes and are development hypotheses, not independent evidence.
- Decision:
  `R4_V48_OUT_OF_ERA_REPLICATION_FAIL_NO_SAME_VERSION_TUNING`. The original
  historical R4 composite is not promoted. No Python-serving, EA, demo, live,
  sizing, account, broker, or ML authority changed.

## R4 Component Resolution Prospective V49 - 2026-07-26

- Added, preregistered, tested, and locked
  `xau-usd/xauusd-fast-research/capital-r4-component-resolution-prospective-v49`
  before the `2026-07-27T00:00:00Z` boundary. Contract SHA-256:
  `751768282196caf59df44fc0560567d63d6f8dcbdb08f732ed17db6f7bac4ceb`;
  aggregate economics were absent at lock.
- The primary branch contains fixed components `39888` and `39427`. It is
  explicitly disclosed as selected after V48 outcomes and can earn evidence
  only from new Capital data. The unchanged three-component V26/V34 branch
  containing `39888`, `40193`, and `39427` is a same-days benchmark and cannot
  rescue a failing primary branch.
- V49 independently regenerates the selected candidate stream. It does not
  merely filter V34 after candidate generation, because V34's component
  priority deduplication could otherwise hide a simultaneous selected
  candidate. The selected branch reuses the unchanged V34 feature/rule code
  and unchanged V40 executable bid/ask outcome, spread, cost, slippage,
  one-position, cooldown, and daily-cap semantics.
- Validation uses the first outcome-blind prefix with at least 20 eligible
  weekdays, five primary trades, and one trade from each selected component,
  capped at 260 days. It requires PF at least 1.10, mean at least 0.05R,
  drawdown at most 8R, positive net after the largest winner is removed, and
  positive PF-at-least-1.00 evidence from both components.
- A passing validation opens a disjoint confirmation requiring at least 40
  eligible weekdays, 15 primary trades, and three from each component, capped
  at 520 days. It requires PF at least 1.20, mean at least 0.10R, drawdown at
  most 12R, positive net after removing the two largest winners, and positive
  PF-at-least-1.00 component evidence.
- Six focused tests, compilation, command-entry smoke testing, Ruff, contract
  self-verification, correct account `1033030` integration, and independent
  status verification pass. The initial locked cycle returned
  `WAITING_FOR_UNTOUCHED_VALIDATION` with zero eligible days, zero candidates,
  zero resolutions, zero unresolved candidates, and aggregate economics
  unopened.
- The hidden V49 watcher is active with launcher PID `37984` and worker PID
  `40504`. Stdout is
  `C:/MT5PortableTier1BestEA/MQL5/Files/v49_r4_component_evaluator.stdout.log`;
  adjacent stderr is empty. It polls every 300 seconds and is separate from
  V47 and V60.
- V49 is research only. Same-version tuning, model training, Python
  predictions, EA consumption, demo/live authorization, and broker action are
  all false.

## R2/R3 Capital Bar-Portability Diagnostic - 2026-07-26

- Replayed the exact frozen R2/R3 signal definitions on the independent
  Capital M5 history as a secondary feasibility diagnostic. The source has
  1,148,599 bars from 2010-01 through 2026-07 with separate bid/ask OHLC and
  no crossed quotes. Because about 7% of early MT5 bars report zero spread,
  execution imposed a conservative $0.30 spread floor plus the frozen ticket,
  holding, and 0.05R slippage stress.
- This was a bar-level diagnostic after historical outcomes were already
  exposed. It is not tick-exact, not a new holdout, not a locked confirmation,
  and cannot authorize trading or replace V47.
- R2 downtrend did not transport robustly: 109 full-period trades, +16.768R,
  PF 1.205, 34.608R drawdown, and -35.692R after removing the five largest
  winners. Its 2018-2022 era was -12.170R/PF 0.390.
- R3 compression was the strongest unchanged cross-broker result: 101 trades,
  +27.334R, +0.2706R mean, PF 1.431, 8.430R drawdown, and +0.087R after
  removing the five largest winners. All four broad eras were positive:
  +6.218R/PF 1.439, +13.918R/PF 3.209, +1.878R/PF 1.076, and
  +5.320R/PF 1.293.
- R3 recent windows remain sparse and mixed: 3M zero trades; 6M four trades,
  +2.161R/PF 2.015; 1Y eight trades, -0.199R/PF 0.959; 5Y 36 trades,
  +3.436R/PF 1.144; 10Y 66 trades, +10.587R/PF 1.238.
- After normalizing both feeds to nanosecond timestamps, Capital R3 candidate
  events matched frozen Dukascopy events 54.8% at the exact H1 timestamp and
  71.8% within four hours. R2 matched 37.2% exactly and 59.3% within four
  hours. The first zero-match diagnostic was invalidated because it compared
  millisecond and nanosecond integer timestamps without unit normalization.
- Decision: retain unchanged R3 as the strongest remaining prospective
  candidate inside V47. Do not promote it from this diagnostic; the negative
  latest one-year result, weak 2018-2022 PF, winner concentration, MT5 history
  limitations, and low frequency still require untouched Capital confirmation.

## R4 Causal Reversal Confirmation V50 - 2026-07-26

- Quantified the gap between the 463 hindsight-selected R4 portfolio trades and
  the frozen V26 R4 candidate stream. Only 5 oracle trades, or 1.1%, had a
  same-direction V26 candidate within one hour; only 3 had an accepted V26
  trade. The old R4 mechanisms therefore target a materially different event
  population, and small threshold changes cannot recover the hindsight set.
- At 884 hindsight-selected R4 anchors, the direction opposite
  `ema_distance_atr_12` matched the hindsight side 69.7% of the time, rising
  with displacement magnitude. This used hindsight-selected rows and was
  treated only as a development clue.
- Added and preregistered
  `xau-usd/xauusd-fast-research/r4-causal-reversal-confirmation-v50`. The
  single fixed policy requires latest completed H4 R4, a short-EMA displacement
  above the causal expanding 75th percentile, an immediate completed-M5
  reversal confirmation, and one candidate per excursion. Direction is
  opposite displacement; action is the frozen H4 broker-side close.
- Candidate generation loaded only causal columns and used strictly prior,
  one-row-shifted expanding thresholds. Before outcomes, it emitted 336
  candidates from 10,624 R4 decision rows: 169 long and 167 short, spanning
  2017-05-31 through 2026-07-21. Candidate SHA-256:
  `0b7947c3f6455290fcff13d4fe897afd2b0485f6f70147ac2d0c95dd70076f45`.
- A pre-lock run caught and fixed an outcome-blind specification error:
  `spread_last_atr <= 0.15` is not equivalent to the teacher's actual
  spread/H4-risk gate. The duplicate approximation was removed before lock;
  all source decision rows already satisfy the executable action gate.
- Contract SHA-256:
  `d071a4c2e70272d2e75fdfead59109a15867842e48b4a3232f36b34e90c49873`.
  It was locked before outcomes with the candidate facts, policy, tests, gates,
  sources, and package implementation sealed.
- The locked evaluation failed after computing economics but before result
  serialization because pandas timestamps were passed directly to the
  canonical JSON hash helper. The locked package was not modified.
  `resume_evaluation.py` applies only the already locked `json_ready`
  conversion before hashing; `POST_LOCK_EVALUATION_NOTE.md` records this
  mechanical adapter.
- V50 failed decisively: 276 portfolio trades, -27.828129R, -0.100827R mean,
  PF 0.823973, 44.20% win rate, 41.837556R drawdown, and -52.777553R after
  removing the five largest winners. The 5,000-resample UTC-week bootstrap 90%
  mean interval was -0.256444R to +0.051716R. Only 4 of 11 partial/full
  calendar years were positive; latest 365 days were 17 trades, -0.305934R,
  and PF 0.980984.
- Result SHA-256:
  `25afab2d9503d92056f4dcfb5eed1d57e863cac5b120baca638b646622157590`.
  Four focused tests, compilation, artifact hashes, and metric reproduction
  pass with `R4_CAUSAL_REVERSAL_V50_VERIFICATION_PASS`.
- Post-outcome failure diagnosis did not identify a defensible horizon rescue.
  The same locked event stream lost at reversal H1/H4/H12
  (-79.127R/-27.828R/-107.103R) and continuation H1/H4/H12
  (-110.366R/-115.688R/-14.289R). At actual portfolio entries, only 76 of 137
  strong hindsight rows matched the chosen side, 55.5%, demonstrating that the
  apparent 69.7% anchor accuracy was created largely by hindsight timing.
- Decision: `R4_V50_POLICY_FAIL_NO_SAME_VERSION_TUNING`. Do not rescue V50 by
  selecting its profitable 2023 year, third displacement quartile, or
  hindsight action subgroup. R4 remains unqualified; V49 continues unchanged
  untouched prospective collection.

## Dedicated R3 Capital Prospective Confirmation V51 - 2026-07-26

- The unchanged R3 compression composite remains the strongest non-R1
  portability result. Frozen Dukascopy raw-tick history has 118 trades,
  +44.650647R, PF 1.557073, 8.333R drawdown, and +8.409R after removing the
  five largest winners. The separate Capital bar diagnostic has 101 trades,
  +27.334R, PF 1.431, and 8.430R drawdown, with all four broad eras positive.
  These are still exposed historical development results.
- V47 evaluates R2, R3, and R4 together and requires every specialist to be
  positive. Added and locked
  `xau-usd/xauusd-fast-research/capital-r3-dedicated-prospective-v51` so an
  unrelated R2 or R4 failure cannot hide R3's own untouched result.
- V51 does not change R3. It filters the frozen V28 feed to attempts 12183,
  12222, and 12389, joins unchanged V40 causal outcomes, and applies the same
  entry-time/origin-attempt/candidate-ID priority with one R3 position.
- Contract SHA-256:
  `c012d01ca8cad1d98dffe663f0afff8ff5c5de7f124d27fb1d748173a38063eb`,
  created at `2026-07-26T05:18:30.089395Z` before the
  `2026-07-27T00:00:00Z` boundary with no aggregate economics.
- Validation requires at least 20 eligible weekdays and five resolved R3
  trades, capped at 260 days. It requires positive net, PF at least 1.10, mean
  at least +0.05R, drawdown no greater than 6R, and positive net after removing
  the largest winner.
- A passing validation opens disjoint confirmation requiring at least 40
  eligible weekdays and 12 resolved R3 trades, capped at 520 days. It requires
  PF at least 1.20, mean at least +0.10R, drawdown no greater than 10R, and
  positive net after removing the two largest winners.
- Compilation, the R3 stream-isolation test, contract self-verification, V40
  identity checks, correct account `1033030`, and an initial real cycle pass.
  Initial status is `WAITING_FOR_UNTOUCHED_VALIDATION`: zero eligible days,
  zero trades, zero unresolved R3 candidates, and aggregate economics unopened.
- The hidden V51 watcher is active with launcher PID `21576` and worker PID
  `28840`. Stdout is
  `C:/MT5PortableTier1BestEA/MQL5/Files/v51_r3_evaluator.stdout.log`; adjacent
  stderr is empty. It polls every 300 seconds and is separate from V47, V49,
  V60 feed collection, and demo execution.
- V51 is research only. Same-version tuning, model training, Python
  predictions, ML shadowing, EA consumption, demo/live authority, and broker
  action are all false.

## R2 Intraday Rebound Confirmation V53 - 2026-07-26

- Added, preregistered, candidate-locked, evaluated, and independently
  verified
  `xau-usd/xauusd-fast-research/r2-intraday-rebound-confirmation-v53`.
  This was a distinct R2 mechanism rather than another RSI/wick variant:
  unusually negative short-EMA displacement relative to a strictly-prior R2
  expanding 75th percentile, followed by a completed upward M5 reversal, one
  long H4 action per excursion.
- The outcome-blind stream contained 49 candidates. Before outcomes, the
  coverage gates were set to 40 trades and 0.015 trades per weekday; all
  economic gates remained unchanged. Contract SHA-256:
  `c3be9048f968ae1070a36f703bf19ea2db160de33773a7e8a11146bd4a94dcf0`.
- V53 failed decisively: 42 portfolio trades, -25.861980R, -0.615761R mean,
  PF 0.388027, 35.71% win rate, 30.692577R drawdown, and -37.708997R after
  removing the five largest winners. The 90% UTC-week bootstrap mean interval
  was entirely negative at -0.990080R to -0.270986R. Only two calendar years
  were positive, every broad era was negative, and the latest 365 days were
  four trades, -5.415066R, and PF 0.420221.
- Result SHA-256:
  `1d06351d23af478f6a4db0f64977fd492a71e5fa62460a8cd3991a68346c58e4`;
  trade SHA-256:
  `6516c00d2726d755291e521ed8b33d821fb696169c2470f32415ef0c1f202c85`.
  Four focused tests, compilation, artifact hashes, and metric reproduction
  passed before V54; V53 is retired without same-version tuning.
- A post-outcome diagnostic found the exact event stream was descriptively
  better as short continuation, especially at H12. That direction and horizon
  were explicitly treated as a new contaminated development hypothesis, not
  a rescue of V53.

## R2 Failed-Rebound Cross-Broker Replication V54 - 2026-07-26

- Added
  `xau-usd/xauusd-fast-research/r2-failed-rebound-crossbroker-v54` to test the
  single fixed post-V53 hypothesis on the independent Capital M5 clock:
  unchanged causal R2 downside-extreme/upward-confirmation events, executed
  short at the next M5 open and closed at the exact broker-side H12 endpoint.
  Direction and horizon were selected after Dukascopy V53 outcomes and Capital
  history had been exposed for other strategies, so this was disclosed as a
  cross-broker historical replication rather than a pristine holdout.
- Candidate generation used the frozen canonical regime router, strictly-prior
  expanding thresholds, the established Capital 36-of-48 H4 validity
  convention, a $0.30 bid/ask quote floor, risk
  `max(2.25 * M5 ATR, $3.50)` capped at $50, and a 0.15R entry-spread limit.
  It could inspect only the scheduled endpoint timestamp, not its price or any
  P&L.
- The first outcome-blind clock preflight required every intermediate M5 row
  and left only 50 candidates. Because this fixed-close action has no stop,
  target, MFE, MAE, or path rule, an outcome-blind timestamp audit corrected
  the clock to require the economically relevant immediate entry and exact
  H12 endpoint. It found 181 of 217 downside events had exact endpoints. No
  direction, horizon, signal, cost, portfolio, or economic gate changed.
- The final preflight produced 173 candidates and 125 scheduled one-position
  portfolio entries. Before outcomes, coverage-only gates were calibrated
  from 0.04 to 0.025 trades per weekday and from 15 to 10 trades per era
  because the fixed stream could not attain the originals. The 100-trade,
  PF 1.20, +0.10R mean, 20R drawdown, winner-removal, ten-positive-year,
  latest-year, all-era economic, and positive-bootstrap-lower-bound gates were
  unchanged. Candidate SHA-256:
  `6d7cdd374051496afe5c1fc4bf0b78e8d3c1c8b5fef4b794332a7d6f1d84cd7a`.
- Contract SHA-256:
  `57dcdf0badb620f83d68f0e1a8a0e1bda3ad7680e2153486f5a363f2b459e177`.
  It locked all code, configuration, sources, dependencies, and candidate
  facts before exact V54 Capital exits were opened.
- V54 failed: 125 trades, -6.487900R, -0.051903R mean, PF 0.953988, 37.60%
  win rate, 73.396271R drawdown, and -57.883168R after removing the five
  largest winners. The 90% UTC-week bootstrap mean interval was
  -0.553857R to +0.504524R. Only seven calendar years were positive.
- Broad eras were unstable: 2010-2012 -4.922R/PF 0.737; 2013-2016
  +8.692R/PF 1.495; 2017-2020 -13.250R/PF 0.398; and 2021-2026
  +2.992R/PF 1.036. The latest 365 days were unusually strong at 12 trades,
  +34.389R, and PF 3.775, but 10 years remained -11.578R/PF 0.891. The
  recent burst is therefore a regime-local anomaly, not stable evidence.
- Result SHA-256:
  `0befe7fc7097dc0aa5d95b91a70fe231e81f3130e08f3aa7b817022371bb60cd`;
  trade SHA-256:
  `f948e0938e5843fdd8971427361976400863aea246492a820fd1eb4ef94224d0`.
  Five focused tests, compilation, contract and artifact hashes, and metric
  reproduction pass with `R2_FAILED_REBOUND_V54_VERIFICATION_PASS`.
- Decision:
  `R2_V54_CROSSBROKER_REPLICATION_FAIL_NO_SAME_VERSION_TUNING`. Do not tune
  V54 around 2024-2026, omit the failed eras, or promote the recent slice.
  Model training, predictions, ML shadowing, EA consumption, demo/live
  authority, account changes, and broker action remain false.

## Dedicated R2 Capital Prospective Confirmation V55 - 2026-07-26

- The strongest unresolved historical R2 object remains the unchanged
  `R2_DOWNTREND_FAILED_RALLY_DUAL_MODE_V1` composite containing attempts
  `11142` and `11266`. Its exposed Dukascopy raw-tick history has 118 trades,
  +65.990257R, PF 1.774286, +0.559239R mean, 19.642422R drawdown, every broad
  era positive, and +5.622423R after removing the five largest winners.
- Component `11266` is not independently qualified despite PF 2.107 and all
  eras positive: it has only 26 trades and becomes -14.467994R after removing
  five winners. The composite, not that sparse component alone, is the fixed
  prospective object.
- Added and locked
  `xau-usd/xauusd-fast-research/capital-r2-dedicated-prospective-v55` so R3 or
  R4 cannot hide R2's own untouched result inside V47. V55 does not change
  R2. It filters the frozen V28 stream to `R2_DOWNTREND`, reuses unchanged V40
  outcomes, retains attempts `11142` and `11266`, and applies the same
  entry-time/origin-attempt/candidate-ID priority with one R2 position.
- Contract SHA-256:
  `856a191ae6e3a897954b2ef29acf4ecd71e400cf6184803e301e8f31923fa00a`,
  created at `2026-07-26T05:51:05.620536Z` before the
  `2026-07-27T00:00:00Z` boundary with aggregate economics absent.
- Validation requires at least 20 eligible weekdays and five resolved R2
  trades, capped at 260 days. It requires positive net, PF at least 1.10,
  mean at least +0.05R, drawdown no greater than 8R, and positive net after
  removing the largest winner.
- A passing validation opens disjoint confirmation requiring at least 40
  eligible weekdays and 12 resolved R2 trades, capped at 520 days. It
  requires PF at least 1.20, mean at least +0.10R, drawdown no greater than
  12R, and positive net after removing the two largest winners.
- The isolation test, compilation, formatting check, locked-orchestration
  smoke test, contract identity, V40 identity, and initial real cycle pass.
  Initial status is `WAITING_FOR_UNTOUCHED_VALIDATION`: zero eligible days,
  zero trades, zero unresolved R2 candidates, and aggregate economics
  unopened.
- The independent V55 watcher is active with launcher PID `34112` and worker
  PID `36496`. Stdout is
  `C:/MT5PortableTier1BestEA/MQL5/Files/v55_r2_evaluator.stdout.log`; adjacent
  stderr is empty. The first launch attempt exited before evaluation because
  Windows split the unquoted repository path; the quoted relaunch is healthy.
- V55 is research only. Same-version tuning, model training, Python
  predictions, ML shadowing, EA consumption, demo/live authority, and broker
  action are all false.

## R3 Compression Overshoot Reversal V56 - 2026-07-26

- Added, preregistered, candidate-locked, evaluated, and independently
  verified
  `xau-usd/xauusd-fast-research/r3-compression-overshoot-reversal-v56`.
  V56 tested a mechanism distinct from the qualified R3 compression-release
  composite: a strictly-prior expanding 75th-percentile six-bar displacement
  extreme, body/edge-close confirmation, and one opposite-direction H1 action
  per R3 excursion.
- Candidate generation read only causal decision features and the latest
  completed canonical H4 regime. It rejected oracle, P&L, MFE/MAE, and exit
  columns. A pre-lock audit found and fixed stale excursion state across R3
  episode changes; three regression tests cover one-per-excursion behavior,
  episode resets, and outcome-column rejection.
- The final outcome-blind ledger contained 221 candidates: 103 long and 118
  short, spanning 2018-06-13 through 2026-06-05. The pre-outcome H1 clock
  estimated 178 portfolio trades, with 78/80/20 across the three fixed eras
  and 13 in the latest year. Candidate SHA-256:
  `cd7c5a70c82af84eaebd1fe469083c9ec1720c836c86468741b81f44a90e36e8`.
- Contract SHA-256:
  `6a378cf4e8f0be275b6ba118272f5e1916fc3948e8b70a0fd83e6c0156fb9e53`.
  It froze all package files, dependencies, sources, candidate facts, gates,
  and authority flags before H1 outcomes were opened.
- V56 failed decisively: 178 trades, -46.128614R, -0.259150R mean, PF
  0.426089, 31.46% win rate, 56.139479R drawdown, and -57.800274R after
  removing the five largest winners. The 90% UTC-week bootstrap mean interval
  was entirely negative at -0.363441R to -0.147095R. Only one calendar year
  was positive.
- Every broad era was negative: 2018-2020 -22.525R/PF 0.217; 2021-2023
  -20.814R/PF 0.374; and 2024-2026 -2.789R/PF 0.848. The latest year had 13
  trades, -0.410R, PF 0.968, and 10.421R drawdown.
- Result SHA-256:
  `8b4a501ac918ed141e843c453804fa6abff6e044ef4d0d7305bf40ebf229ce38`;
  trade SHA-256:
  `2cdb5548572cdf15219b6f0925ee75523e0a2b40af3fd18185da1482ec68ae81`.
  Tests, compilation, contract self-verification, artifact hashes, and metric
  reproduction pass with
  `R3_COMPRESSION_OVERSHOOT_V56_VERIFICATION_PASS`.
- A bounded post-outcome direction/horizon diagnostic found that both H1
  directions lost. The only positive cell retained the V56 reversal direction
  for H12: 84 trades, +13.263727R, PF 1.179155, and 16.999714R drawdown.
  It is not a rescue or valid successor: removing five winners gives
  -22.460381R, the bootstrap lower bound is -0.343938R, 2021 lost
  -15.916R, and the latest year lost -2.753573R/PF 0.776.
- Decision: `R3_V56_POLICY_FAIL_NO_SAME_VERSION_TUNING`. Retire this
  overshoot lineage. Do not invert it, select H12 from the exposed diagnostic,
  or filter its losing years. The unchanged V51 prospective evaluator remains
  the valid path for the already-qualified R3 compression-release composite.

## R1 Counter-Extension V57 - 2026-07-26

- Audited the timing gap between the existing R1 specialists and the hindsight
  opportunity set. The 558 existing R1 candidates are long-only and match only
  3 of 179 hindsight R1 portfolio trades within one hour and 14 within four
  hours. The hindsight set contains 96 longs and 83 shorts.
- At 309 hindsight R1 anchors, direction opposite
  `ema_distance_atr_12` matched the hindsight side 67.6% overall and 89.7%
  above the absolute full-anchor 75th percentile. H12 was the most common
  hindsight action. This was treated as a contaminated development clue.
- Added, preregistered, candidate-locked, evaluated, and independently
  verified `xau-usd/xauusd-fast-research/r1-counterextension-v57`. Its
  causal policy uses the latest completed R1 H4 state, a strictly-prior
  expanding 75th-percentile absolute EMA12 extension, one
  opposite-extension H12 candidate per excursion, and a state reset at each
  new R1 episode.
- The outcome-free candidate ledger contained 497 balanced events: 240 long
  and 257 short from 2017-08-11 through 2026-04-02. It matched 70 of 179
  hindsight R1 trades within one hour and 116 within four hours. Estimated
  one-position H12 scheduling produced 144 trades, with 50/46/48 across the
  fixed eras and 17 in the latest year; every coverage gate was feasible
  before outcomes.
- Candidate SHA-256:
  `af5cd119fc20432a1043a009b38493871406784247bb116a0f9dee2d0d51d78f`.
  Contract SHA-256:
  `5039d4fe7d389600bb5bce97acc654e55dc0d13683520b143e00a5cbb69dae14`.
- V57 failed: 144 trades, -23.922008R, -0.166125R mean, PF 0.869718, 50.00%
  win rate, 63.438200R drawdown, and -65.024001R after removing the five
  largest winners. The 90% UTC-week bootstrap mean interval was
  -0.618912R to +0.276132R. Only four calendar years were positive.
- Broad eras were unstable: 2017-2020 -0.617R/PF 0.984; 2021-2023
  +5.650R/PF 1.094; and 2024-2026 -28.956R/PF 0.658. The latest year was
  descriptively strong at 17 trades, +11.589R, and PF 1.867, but 2024 alone
  lost -33.183R. Recent-window promotion is prohibited.
- Result SHA-256:
  `ba3f3083dacc6b700cff1ba3ae67232643899d146a8b25bf4e51eb591591bf54`;
  trade SHA-256:
  `fef9205370b4002fafa600b48c1e804b2d3d70669664d8491ae3f5fdad042586`.
  Tests, compilation, contract and artifact hashes, and metric reproduction
  pass with `R1_COUNTEREXTENSION_V57_VERIFICATION_PASS`.
- A bounded post-outcome matrix tested opposite-extension and with-extension
  directions at H1/H4/H12, both combined and as standalone long/short
  specialists. All twelve side/horizon cells lost, and no side was positive
  in every era. There is no defensible direction, side, or horizon rescue.
- Decision: `R1_V57_POLICY_FAIL_NO_SAME_VERSION_TUNING`. Retire the
  displacement counter-extension lineage. Do not select the recent year,
  omit 2024, split a side, flip direction, or choose another fixed horizon
  from these exposed outcomes.

## Transition First-Block Capital Replication V58 - 2026-07-26

- Audited the strongest winner-robust sparse transition row from the earlier
  2,000-policy `chop-transition-mechanisms-v2` campaign. Frozen attempt
  `16683` had 30 Dukascopy development trades, +27.130568R, PF 3.186837,
  +0.904352R mean, 2.328642R drawdown, positive net in all four eras, and
  +4.154450R after removing five winners. It was not qualified because it
  failed the 60-trade and eight-per-era coverage gates and had a
  multiple-testing adjusted q-value of 1.0.
- Added, preregistered, candidate-locked, evaluated, and independently
  verified
  `xau-usd/xauusd-fast-research/transition-first-block-capital-replication-v58`.
  It reproduces the exact unchanged attempt on the independent Capital M5
  bid/ask history: transition after compression, age at most four H1 bars,
  four-bar momentum at least 0.60 ATR, body at least 0.30, efficiency at least
  0.05, impulse direction, 0.80 ATR stop, and six-hour fixed horizon.
- The package binds the original V2 metrics file and verifies that attempt
  number, mechanic, and parameters exactly match row `16683`. Candidate
  generation uses only completed H1/H4 price and planned entry clocks. It
  does not inspect next-bar quotes, stop paths, exits, returns, MFE/MAE, or
  P&L.
- The final outcome-free Capital ledger contained 60 raw candidates and 27
  conservatively scheduled planned events, 16 long and 11 short, with
  5/5/7/10 across the original four eras. Candidate SHA-256:
  `bf30172e6d3496e1fac4c4742ab8dea146ea2bb727d0a6c278a5442b1c59c1c1`.
- Contract SHA-256:
  `95bde18ef01a02e282bfc9b95df2a8cd28f16aa0bfc9806159a6050a8e804b97`.
  It locked package files, all feature/regime dependencies, source hashes,
  candidate facts, parameters, costs, portfolio rules, gates, and authority
  flags before Capital entry quotes or future paths were opened.
- V58 failed: 28 executed trades, -2.046104R, -0.073075R mean, PF 0.893749,
  35.71% win rate, 11.263921R drawdown, and -10.521024R after removing the
  three largest winners. The 90% UTC-week bootstrap mean interval was
  -0.472630R to +0.361485R. Only three of ten active calendar years were
  positive.
- Era portability failed: 2010-2014 had six trades, -4.179R/PF 0.176;
  2014-2018 had no executable trades; 2018-2022 had nine trades,
  -7.085R/PF 0.236; and 2022-2026 had 13 trades, +9.218R/PF 2.877. The latest
  year was five trades, +1.288R/PF 1.604, but the latest six months were
  -0.774R/PF 0.637. Recent-slice promotion is prohibited.
- Result SHA-256:
  `efaa7ea0c5fc98434f014f7db6ee963a55716ed7706bc8b0fb73c8f7aa2b9e7a`;
  trade SHA-256:
  `555d3863b186381cc66c8513280826b463f62a5245f998d4c9d2470011e8cf4e`.
  Three focused tests, compilation, contract and source identity, artifact
  hashes, and metric reproduction pass with
  `TRANSITION_FIRST_BLOCK_V58_VERIFICATION_PASS`.
- Decision:
  `TRANSITION_V58_CROSSBROKER_FAIL_NO_SAME_VERSION_TUNING`. Do not select a
  different attractive row from the same exposed 2,000-policy screen, omit
  failed eras, or promote the recent Capital slice. This transition
  first-block family is not portable enough to qualify.

## R0 Post-Shock Resolution V1 - 2026-07-26

- Audited the remaining R0 opportunity gap after the earlier immediate
  shock-fade, adaptive post-shock reversal, and chop-normalization failures.
  Added and preregistered
  `xau-usd/xauusd-fast-research/r0-postshock-resolution-v1` to test a distinct
  causal mechanism: remain flat during `UNSAFE_SHOCK`, wait for completed H4
  resolution into `TREND_UP` or `TREND_DOWN`, then take the first completed H1
  pullback-and-resumption pair in the resolved direction.
- The frozen rule permits at most one intervening `TRANSITION_UNKNOWN` run,
  requires trend resolution within 24 hours of the shock ending, searches
  only the first 12 completed H1 trend bars, requires a 0.35 resumption body,
  and uses a fixed 1.50 ATR stop and 12-hour hold. It emits one candidate per
  post-shock trend run and never trades inside the shock.
- Candidate generation opened no outcomes and emitted 59 Capital events, 40
  long and 19 short, with 57 conservatively schedulable under the one-position
  clock. The broad-era candidate distribution was 11/13/20/15. Candidate
  SHA-256:
  `6afe29d7f30b12af4033e516438d791f893a7efe95603414aee201710170b876`.
- Contract SHA-256:
  `7aa4cb54b51cc761b98e34a42f7020e08714b364050b0ffded5875fb9bbc5762`.
  It froze the package, dependencies, Capital source, candidate facts, rule,
  costs, portfolio constraints, gates, and all-false authority before exact
  post-entry paths were opened.
- The one-shot result was descriptively positive but failed robustness: 57
  trades, +3.007868R, +0.052770R mean, PF 1.106028, 43.86% win rate, and
  7.467408R drawdown. Removing the five largest winners produced
  -11.403261R, and the 90% UTC-week bootstrap mean interval was
  -0.227632R to +0.348074R. Only six of 17 active calendar years were
  positive.
- Era stability failed: 2010-2014 +1.254R/PF 1.227; 2014-2018
  +7.571R/PF 2.538; 2018-2022 -2.780R/PF 0.709; and 2022-2026
  -3.037R/PF 0.637. The latest year had two trades, both losses, for
  -2.127587R and PF 0. The last 6 months had one trade at -1.060973R.
- Result SHA-256:
  `aa620ab6ea268ea939e32d96b302f81e1eb43d49d9b2498374b9c966c756f25b`;
  trade SHA-256:
  `7bf5d0eccf6262ede447bd66c53540a3101e11c72ee7b9486690ebd2672fd7cc`.
  Three focused tests, contract/source identity, candidate regeneration,
  trade replay, metric reproduction, and artifact hashes pass with
  `R0_POSTSHOCK_RESOLUTION_V1_VERIFICATION_PASS`.
- Decision: `R0_POSTSHOCK_V1_POLICY_FAIL_NO_SAME_VERSION_TUNING`. Retire this
  exact post-shock trend-resolution lineage. Do not select the profitable
  2014-2018 era, change its horizon, or filter the exposed losing years.
  R0 remains an abstain state.

## R1 Dedicated Untouched Capital Evaluation V61 - 2026-07-26

- Closed the missing independent prospective-evaluation path for the frozen
  V29 R1 pullback specialist. Added, preregistered, tested, locked, and started
  `xau-usd/xauusd-fast-research/capital-r1-dedicated-prospective-v61`.
- The exact frozen specialist is
  `R1_PULLBACK_LONG_V2_M15_SESSION_09_15`: long only in the V29 R1 uptrend
  state, with V29's unchanged signal, session, spread, cost, and stop rules.
  V61 consumes the existing append-only V29 candidates and V40 Capital
  bid/ask resolutions transported by V60 on account `1033030`.
- V61 retains every V40-executed R1 pullback. It intentionally does not apply
  the one-position R2/R3 router because the frozen V29 execution contract
  permits up to eight concurrent positions and twelve entries per UTC day.
  This preserves the rule being tested instead of creating a new policy.
- Historical context remains exposed evidence only. The bound four-year MT5
  replay contains 413 trades. A descriptive independent reconstruction gives
  +190.646821 gross R, PF 1.860878, 49.88% wins, and 20.695852R closed
  drawdown; 2026 through June was -4.338010R. None of these rows can enter
  V61 validation or confirmation.
- Forward boundary: `2026-07-27T00:00:00Z`. The contract was created before
  that boundary at `2026-07-26T06:57:16.345055Z`, with no aggregate economics
  present.
- Contract SHA-256:
  `cfed6d8394161e84f5709b7e97894963ce3aa1e0a1471b4cd7d0d703621fed18`.
  Contract-file SHA-256:
  `67889d5b35e8c29f965c897e8757b0838eb1f39493624b849bbbc4f25a9559e4`.
  The lock binds 11 package files, eight dependencies, V29/V40 identities,
  the account/feed, stage counts, day-quality rules, routing, gates, and all
  authority flags.
- Eligible weekdays require at least 100,000 unique quote milliseconds, data
  from no later than 02:00 UTC through at least 22:00 UTC, p99 interquote gaps
  no greater than five seconds, duplicate-millisecond share no greater than
  5%, and exact account/server/symbol and read-only authority identity.
- Validation opens only at the first outcome-blind endpoint with at least 20
  eligible weekdays, five executed R1 trades, and final resolution of every
  R1 candidate through the endpoint. Gates are positive stressed net, PF at
  least 1.10, mean at least +0.05R, drawdown at most 8R, and positive net
  after removing the largest winner.
- If validation passes, confirmation uses a disjoint period with at least 40
  eligible weekdays and twelve executed trades. Gates are PF at least 1.20,
  mean at least +0.10R, drawdown at most 12R, and positive net after removing
  the two largest winners. Same-version tuning is forbidden.
- Focused V61 tests: 3 passed. V47/V49/V51/V55/V61 focused suites passed
  7/6/1/1/3 tests respectively. V61 Ruff, format, compilation, and diff checks
  pass.
- First locked V61 cycle:
  `WAITING_FOR_UNTOUCHED_VALIDATION`, zero eligible weekdays, zero candidates,
  zero executed trades, zero unresolved candidates, and
  `aggregate_economics_opened=false`. Model training, Python predictions, EA
  consumption, demo, live, and broker-action authority are all false.
- Persistent hidden V61 watcher: parent PID `33844`, child PID `21460`, poll
  interval 300 seconds. Its stderr is empty. Runtime status:
  `xau-usd/xauusd-fast-research/capital-r1-dedicated-prospective-v61/outputs/CAPITAL_R1_V61_STATUS.json`.
- Cross-check at handoff: V47, V49, V51, V55, and V61 all report
  `WAITING_FOR_UNTOUCHED_VALIDATION`, zero eligible days, and no aggregate
  economics. Their watcher pairs are V47 `28824/21420`, V49 `37984/40504`,
  V51 `21576/28840`, V55 `34112/36496`, and V61 `33844/21460`.
- V60 remained unchanged. Feed processes `42008/45896` and portfolio
  processes `40444/45588` are alive. V60 reports all requested feeds healthy,
  account `1033030`, `ml_used=false`, `ml_runtime_authorized=false`, and
  `ml_shadow_authorized=false`. V61 cannot place or alter a demo order.
- Next decision is mechanical: collect untouched Capital data from July 27,
  preserve every append-only prefix, and wait for the frozen stage endpoint.
  Do not inspect interim R1 economics, lower the trade-count requirement,
  alter the gates, or call the exposed MT5 history prospective proof.

## R1 Box Dedicated Untouched Capital Evaluation V62 - 2026-07-26

- Closed the remaining R1 prospective-measurement gap by adding, testing,
  locking, and starting
  `xau-usd/xauusd-fast-research/capital-r1-box-dedicated-prospective-v62`.
  It transports the already locked V41 box outcome engine to account `1033030`
  and evaluates only untouched rows from July 27.
- V62 changes runtime locations and account identity only. Locked V41 still
  owns candidate schema and identity, executable Capital bid/ask entry/exit,
  stop distance, 2R target, ten-minute entry window, spread limits, ticket
  cost, holding cost, 0.05R slippage stress, maximum two concurrent positions,
  and maximum one entry per UTC day.
- The V41 transport reads V60's append-only
  `R1_UPTREND_LONG_V1` candidate feed and the account `1033030` prospective
  tick files. It writes a separate append-only resolution ledger below
  `C:\MT5PortableTier1BestEA\MQL5\Files\v60_canonical_demo_v2\feeds\r1_box_outcomes`.
  It cannot alter the source candidate feed or V60.
- Forward boundary: `2026-07-27T00:00:00Z`. The V62 contract was created at
  `2026-07-26T07:07:45.290903Z`, before the boundary, with no aggregate
  economics present.
- V62 contract SHA-256:
  `dcd2b1787742b999bab2931f303c15204429350b3ca5bd88713f5e35caf99ca5`.
  Contract-file SHA-256:
  `f4fb79ca42cea3cf93355cad19946b960a5e7bd79d9da68f830c4abf30aa3c7f`.
  It binds 11 package files, nine dependencies, V41 contract
  `f78d0b01b9ed9b65e71429dd461d0b967ae44058944de2452043051402728363`,
  source contract
  `27fef83d1a57aa28a1e4d4e6968b2854184a673cdff6769da16828fbe4084908`,
  transport identity, stages, gates, and all authority flags.
- A pre-lock live transport cycle and the first complete post-lock cycle both
  passed on account `1033030`: active read-only V41 resolver, zero candidates,
  zero resolutions, no aggregate economics, and all model, EA, demo, live,
  trade, and broker-action authority false.
- V62 validation/confirmation use the same complete-day criteria and stage
  gates as V61. Validation needs at least 20 eligible weekdays and five
  executed box trades; confirmation, only after a pass, needs a disjoint 40
  eligible weekdays and twelve trades. Endpoints require every candidate
  through the date to have a final causal resolution.
- Focused tests: 4 passed. Ruff, format, compilation, and diff checks pass.
  Tests verify transport-only overrides, exclusion of preboundary candidates,
  resolution hash/policy identity, and retention of every V41 primary-policy
  execution.
- First evaluator status:
  `WAITING_FOR_UNTOUCHED_VALIDATION`, zero eligible weekdays, zero executed
  trades, zero unresolved candidates, and
  `aggregate_economics_opened=false`.
- Persistent hidden V62 watcher: parent PID `40244`, child PID `6332`, poll
  interval 300 seconds; stderr is empty. It resolves the frozen V41 stream
  before each evaluator cycle. Runtime status:
  `xau-usd/xauusd-fast-research/capital-r1-box-dedicated-prospective-v62/outputs/CAPITAL_R1_BOX_V62_STATUS.json`.
- Cross-check after V62: all six untouched evaluators V47, V49, V51, V55,
  V61, and V62 report `WAITING_FOR_UNTOUCHED_VALIDATION`, zero eligible
  weekdays, no opened aggregate economics, and no model or broker authority.
  All 16 expected evaluator/V60 processes are alive and responding.
- R1 through R4 prospective coverage is now explicit: V61 owns the R1 pullback
  decision, V62 owns R1 box, V55 owns R2, V51 owns R3, and V49 plus the
  unchanged V47 benchmark own R4. R0 and R5 remain causal abstain states.
  This is complete measurement infrastructure, not proof that any candidate
  will pass.

## Raw BREAK_60 Shared-Account Feasibility Rejection - 2026-07-26

- Before creating another research package, a read-only feasibility audit
  reconstructed the exact post-outcome V100 diagnostic lane
  `BREAK_60, 12:00-20:00 UTC` with no health circuit. The reconstruction used
  the locked V19 episode markouts, prescribed direction, V100 spread filter,
  maximum one entry per family per UTC date, maximum two open positions, fixed
  60-minute exit, ticket/holding/slippage stress, and the unchanged V60
  account simulator.
- This was an exposed diagnostic used to reject an architecture. It was not
  preregistered evidence, did not create a strategy version, and cannot support
  promotion or prospective authority.
- Stage results:
  - Development-2: 462 trades, 0.886756/day, +676.354171 stress R, PF
    2.829729, mean +1.463970R, 51.621852R closed drawdown, four of four
    profitable half-year segments.
  - Confirmation: 255 trades, 0.977011/day, +173.246326 stress R, PF
    1.742837, mean +0.679397R, 82.517351R closed drawdown, two of two
    profitable half-year segments.
  - Final: 257 trades, 0.984674/day, -34.214061 stress R, PF 0.902421, mean
    -0.133129R, 81.999523R closed drawdown, zero of two profitable half-year
    segments.
- The frozen shared-account router accepted 834 of 974 candidates. It rejected
  134 while the account drawdown circuit was suspended and six for the
  add-on-position limit.
- Shared V60 plus BREAK_60 results also failed:
  - Development-2 combined frequency was 1.953935/day, below 2.0/day.
  - Confirmation passed the window checks at 2.452107/day and combined PF
    1.693934.
  - Final frequency was 2.206897/day, but the add-on lost USD 152.08 at PF
    0.903586 and remained negative after winner removal.
  - Maximum floating drawdown was USD 397.02; the frozen 1.25 capital buffer
    made it USD 496.28, above the USD 449.7675 cap.
- Decision: reject raw BREAK_60, binary-health variants, risk-scaling variants,
  and session rerouting as the next strategy architecture. The failure is
  final-year expectancy as well as drawdown, not only position sizing.
  Reusing the same exposed outcomes would be post-selection optimization.
- The next specialist must use a materially different causal input and begin
  with an untouched July 27 boundary. Existing V59/V60 and all V47/V49/V51/
  V55/V61/V62 contracts remain unchanged.

## R4 Asia Sweep/Reclaim V63 - 2026-07-26

- Added, tested, candidate-froze, locked, opened once, and independently
  verified
  `xau-usd/xauusd-fast-research/r4-asia-sweep-reclaim-v63`.
- V63 tested one deterministic R4 mechanism with no parameter grid. It built
  each completed 00:00-06:00 UTC Asia range, required the latest completed
  canonical H4 state to be valid `R4_CHOP`, waited from 07:00-16:00 for a
  0.20-ATR sweep and completed directional reclaim, and entered opposite the
  sweep at the next exact M5 bid/ask open.
- The rule was materially different from earlier session boundary fades and
  six-bar Core add-ons: it required an actual post-session sweep/reclaim, used
  the completed six-hour auction as its reference, reversed the sweep, and
  required no existing Core position.
- Frozen execution used the larger of 1.50 ATR or a stop 0.10 ATR beyond the
  sweep extreme, a 1.50R target, six-hour maximum hold, one position and one
  entry per UTC date, 0.15R maximum entry spread, USD 0.30 ticket cost,
  prorated holding cost, 0.05R stress slippage, gap-through stops, and
  stop-first same-bar ambiguity.
- Outcome-blind preflight produced 161 executable candidates from 437 raw
  reclaim dates: 79 long and 82 short. Stage supply was 38 Discovery, 33
  Validation, 43 Confirmation, and 47 Final. No trade outcome was present at
  lock.
- Contract SHA-256:
  `3bcfe405f87a9ed3f7db287ff91545f39ca899c9217adbedaa18dbb2cd671fac`.
  Candidate SHA-256:
  `a599cf6b52e9499a337bd545a934180e33063f93b9db4c4d30e6b2febab56ee7`.
- Discovery failed terminally on its first and only opening:
  - 38 trades over 1,175 weekdays, or 0.032340/day;
  - -12.494929R net, -0.328814R mean, PF 0.562622;
  - 14 wins, 24 losses, 36.84% win rate, 16.941823R drawdown;
  - all three chronological segments lost and the worst segment PF was zero;
  - removing the three largest winners left -16.615372R;
  - the 80% weekly-block mean interval was
    [-0.575376R, -0.085344R].
- Decision:
  `R4_ASIA_SWEEP_RECLAIM_V63_DISCOVERY_FAIL_TERMINAL`. Validation,
  Confirmation, and Final remain sealed. Do not mirror direction, retune
  sweep depth, widen the session, alter stop/target/hold, or weaken gates on
  these exposed outcomes.
- Independent replay returned
  `R4_ASIA_SWEEP_RECLAIM_V63_VERIFICATION_PASS`; all five tests, Ruff,
  formatting, compilation, and diff checks pass. Model training, Python
  prediction, EA, demo/live, runtime, account, and broker authority remain
  false.
## Capital Multi-Symbol Prospective Foundation - 2026-07-26

- Audited the account `1033030` Capital quote feed before defining another
  R3/R4 strategy. July 22-24 supplied approximately 275k-305k unique XAUUSD
  millisecond quotes per day. Quotes were non-crossed and midpoint-active, but
  spread was exactly USD `0.30` at the 1st, 50th, and 99th percentiles.
  Reported tick volume and real volume were zero.
- Market-book files contain headers only. The collector reports
  `symbol_book_depth=0`, subscription failure/error `4901`, and zero book rows.
  Capital therefore supplies no usable depth, microprice, queue, volume, spread
  dynamics, or bid-versus-ask asymmetry. A new single-symbol threshold rule
  would repeat the already retired V24.1/V26/V30/V31 mechanisms.
- A read-only MetaTrader5 catalogue audit confirmed synchronized broker ticks
  are available on the exact account for `XAUUSD`, `XAGUSD`, `DXY`, `US500`,
  `EURUSD`, and `USDJPY`. A July 22 source-only probe found respectively
  `398438`, `102442`, `14900`, `63965`, `61175`, and `58645` rows. No candidate
  outcome or P/L was calculated.
- Added and preregistered
  `multi-asset/data-foundation/capital-multisymbol-prospective-v1`. It uses the
  locked information boundary `2026-07-27T00:00:00Z`, stores data under
  `D:/AlgoTradingData/prospective/capital-multisymbol-v1`, refuses every account
  except `1033030` on `Capital.ComMena-Demo`, and contains no broker-action API.
  Model training, Python prediction, EA consumption, demo execution, live
  execution, and broker action are all false.
- Contract SHA-256:
  `1038543cc35a9d77a8b416eb02060cc86163e537465f6d8aa6c1db640e29c057`.
  Contract verification passes with
  `CAPITAL_MULTISYMBOL_PROSPECTIVE_V1_VERIFICATION_PASS`; all five tests pass,
  compilation and diff checks are clean, and the real-terminal preflight passes
  for all six symbols.
- A pre-boundary collection pass returned `WAIT_BOUNDARY` and produced zero
  tick CSVs. The hidden watcher is active as Python PID `44796`; its PID and
  logs are under
  `D:/AlgoTradingData/prospective/capital-multisymbol-v1/_runtime`. The latest
  health file is
  `D:/AlgoTradingData/prospective/capital-multisymbol-v1/_state/health.json`.
- This is a prospective data foundation, not a discovered strategy and not
  trading authority. Per the owner's instruction, research stops after this
  final iteration. V59/V60 remains the accepted historical benchmark and
  unchanged demo implementation; V57 counter-extension and V63 Asia
  sweep/reclaim remain terminal historical failures.

## V60 Prospective Runtime Supervisor - 2026-07-26

- Added `xau-usd/operations/v60-prospective-supervisor-v1` as a separate
  operational continuity layer. It changes no strategy, signal, threshold,
  action geometry, lot, risk limit, contract, model authority, or broker
  authority.
- The supervisor monitors the exact Capital demo terminal, the V60 feed and
  portfolio workers, the read-only six-symbol prospective collector, and all
  six frozen R1-R4 evaluators. Missing Python workers are restarted
  idempotently. The MT5 terminal is monitored but is never started, stopped, or
  restarted by this package.
- The consolidated state is written under
  `D:/AlgoTradingData/prospective/v60-prospective-supervisor-v1`. The first
  real-runtime reconciliation and a complete later 60-second cycle both
  returned `READY`: terminal running, all nine workers running or proven fresh,
  zero process errors, and zero failed health sources.
- The live smoke test exposed two Windows-only orchestration issues before
  handoff: a UTF-8 BOM in the PowerShell process snapshot and a legacy V51
  worker whose relative command line could look absent. Both are handled. The
  duplicate V51 process created by the first smoke cycle was removed, leaving
  the original watcher active; future fallback expires after 900 seconds and
  then launches the canonical absolute command.
- Persistent hidden supervisor PID at handoff: `18780`. Runtime stderr is empty.
  The status timestamp advanced from `2026-07-26T12:40:50Z` to
  `2026-07-26T12:41:51Z` while remaining `READY`.
- Five focused tests pass, PowerShell syntax parsing passes for both scripts,
  Python compilation passes, and `git diff --check` is clean. Ruff was not
  available in the active local runtimes and was not installed.
- V60 itself remains `ACTIVE_DEMO_BROKER_ACTION` on account `1033030`, with ML
  runtime/shadow disabled. It has observed four candidates, filled three V57
  demo trades, rejected one V7 candidate under the locked daily add-on cap,
  and currently has zero XAUUSD positions. Closed prospective demo P/L at this
  checkpoint is USD `-4.82`; this tiny sample is operational evidence only.
- The next untouched evidence boundary remains
  `2026-07-27T00:00:00Z`. All R1-R4 evaluators still have zero eligible
  weekdays by design. The supervisor protects continuity but cannot shorten
  the locked evidence requirements or manufacture a profitable result.

## Causal Specialist Winner/Loser Diagnostic V1 - 2026-07-26

- Added
  `xau-usd/xauusd-fast-research/causal-specialist-win-loss-diagnostic-v1`
  to test whether entry-time measurements separate stressed winners from
  failures inside each canonical specialist. Historical outcomes were already
  exposed, so this is locked exploratory feature discovery rather than
  promotion evidence.
- The canonical population reconciles exactly to `3,752` candidates, `1,664`
  stressed winners, `2,088` stressed failures, and `2,194` historically
  accepted candidates. The accepted population reconciles to the V59 structure:
  `815` core candidates and `1,379` add-ons. The diagnostic uses the `3,024`
  rows with complete mandatory causal XAU features.
- Winners and failures are matched without replacement inside exact family,
  direction, calendar year, UTC session, stop mode, and target mode strata.
  One row per family/direction/structural episode is retained, producing `983`
  matched pairs. Feature values do not influence matching.
- Each feature's favorable direction and standardization are learned only from
  the purged expanding fit partition. Disjoint test partitions are opened once.
  Thirty-four causal, non-COMEX features were tested across all nine families.
- The locked result is
  `STABLE_EXPLORATORY_SEPARATOR_LEADS_FOUND_REQUIRES_PROSPECTIVE_CONFIRMATION`.
  It reports nine univariate leads:
  - R1: normalized planned stop width, five-minute directional tick imbalance,
    and four-hour directional bond return;
  - V57: direction-adjusted XAU returns over 5, 15, and 60 minutes;
  - V7: direction-adjusted five-minute XAU return;
  - V8: direction-adjusted 60-minute XAU return;
  - R5: direction-adjusted inverse-dollar four-hour return.
- The three V57 horizons and the V7/V8 return signals are correlated
  measurements of one interpretable mechanism, not five independent
  discoveries. Winners generally began after a pullback or weaker
  direction-aligned extension; worse candidates were more often entered after
  price had already moved in the intended direction. The strongest examples
  were V57 15-minute return, walk-forward AUC `0.6082`, and V8 60-minute
  return, walk-forward AUC `0.6183`.
- R1 normalized stop width was the strongest individual diagnostic:
  `277` walk-forward rows, AUC `0.6632`, latest-fold AUC `0.6512`, matched
  standardized difference `0.3607`, and weekly-block 95% interval
  `[0.1145, 0.6193]`. This remains a hypothesis; it is not a fitted stop rule.
- R2 remains evidence-limited despite positive baseline economics: only `128`
  feature-complete candidates and `24` matched pairs. R3 produced `49` matched
  pairs; its best apparent spread effect had aggregate walk-forward AUC
  `0.4659`, so no R3 filter advanced.
- The complete causal-feature baseline remains positive but is not an
  executable portfolio result. V59 core feature-complete accepted rows had
  weighted stressed PF `1.5894`; accepted add-ons had PF `1.2468`.
- Independent replay returned `SPECIALIST_WIN_LOSS_V1_VERIFIED`: all eight
  generated artifacts reproduced byte-for-byte, five tests pass, Ruff passes,
  formatting and compilation pass, and diff checks are clean.
- No multivariate model, threshold, portfolio simulation, MT5 attachment,
  shadow scoring, demo/live change, or broker action was created. The correct
  next research step is to collapse correlated leads into a small
  mechanism-level hypothesis set and preregister untouched prospective
  confirmation. ML runtime and shadow remain disabled.

## Causal Anti-Chase Prospective V1 - 2026-07-26

- Added
  `xau-usd/xauusd-fast-research/causal-anti-chase-prospective-v1` as the
  strictly prospective next step from the winner/loser diagnostic. It watches
  the existing V60 V57/V7/V8 candidate feed but is completely ignored by the
  demo executor.
- The untouched boundary is `2026-07-27T00:00:00Z`. The existing four add-on
  candidates are sealed in the append-only prefix and excluded; the initial
  locked status is `WAIT_BOUNDARY` with zero post-boundary candidates, zero
  feature decisions, zero resolutions, and aggregate economics closed.
- One correlated anti-chase mechanism is frozen with one causal feature per
  family: V57 uses direction-adjusted 15-minute return/ATR, V7 uses 5-minute
  return/ATR, and V8 uses 60-minute return/ATR.
- Each rule rejects only values above its outcome-blind historical 75th
  percentile. The exact thresholds are V57 `2.271208771039961`, V7
  `0.7758645561091196`, and V8 `3.8986037874340607`. They reproduce from
  `1,259` feature-complete rows while reading only family, XAU feature status,
  and the three named feature columns; no P/L, winner/failure label, or
  historical acceptance field is read.
- Pre-entry features use only Capital account `1033030` XAUUSD ticks in
  `(cutoff - horizon, cutoff]`. Health statistics, future ticks, actual demo
  acceptance, and actual demo fills are not predictors. Every candidate is
  independently resolved from executable bid/ask ticks with frozen stop,
  target, horizon, spread, ticket cost, holding cost, and `0.05R` stress
  semantics.
- Feature decisions and individual resolutions are separate append-only
  ledgers under
  `D:/AlgoTradingData/prospective/causal-anti-chase-prospective-v1`.
  Aggregate economics remain sealed until the locked 20-weekday/15-candidate
  validation endpoint is complete. A passing validation is followed by a
  disjoint 40-weekday/30-candidate confirmation.
- Contract SHA-256:
  `5752dbd34c4cc4849b7a9f12c0b81b077a1bffbff9614d4f38367ded5e8f1b9b`.
  Verification returns `CAUSAL_ANTI_CHASE_PROSPECTIVE_V1_VERIFIED`; seven
  focused tests, Ruff, formatting, compilation, supervisor tests, and diff
  checks pass.
- Added the watcher and a fail-closed health source to
  `xau-usd/operations/v60-prospective-supervisor-v1`. The restarted supervisor
  PID is `35036`; the anti-chase watcher launcher PID is `13624`. Consolidated
  supervisor status is `READY` with ten monitored workers and ten healthy
  sources.
- Model training, Python prediction, ML shadow, EA consumption, live
  authorization, and broker action all remain false. V60 deterministic demo
  trading and all account/risk settings are unchanged.

## Causal Anti-Chase Historical Robustness V1 - 2026-07-26

- Added and locked
  `xau-usd/xauusd-fast-research/causal-anti-chase-historical-robustness-v1`.
  It compares the untouched V57/V7/V8 candidate baseline, V57-only anti-chase,
  and all-family anti-chase over fixed 3M, 6M, 1Y, 2Y, 3Y, 5Y, 10Y, and full
  windows. The thresholds are byte-bound to the existing prospective V1
  contract and were not changed after viewing these results.
- The primary candidate-quality population reconciles to `1,259` resolved,
  XAU-feature-valid candidates: V57 `549`, V7 `467`, and V8 `243`. The data
  starts on `2019-02-15`, so the requested 10Y and full rows contain only
  approximately 7.4 years of actual coverage. A secondary static diagnostic
  contains the `1,021` candidates historically accepted by the account policy;
  it is explicitly not represented as a rerouted account counterfactual.
- The locked result is
  `V57_ONLY_DOES_NOT_CLEAR_HISTORICAL_ROBUSTNESS`: `15/19` gates passed. V57-only
  improved the fixed 3M candidate result from 63 trades, USD `307.9960`, PF
  `1.6976`, and USD `72.4369` closed drawdown to 53 trades, USD `331.1853`, PF
  `1.9789`, and the same drawdown.
- The recent gain did not persist. Versus baseline, V57-only lost USD
  `90.7694` over 6M, `74.5376` over 1Y, `125.1515` over 3Y, `151.6696` over
  5Y, and `119.0298` over all available history. It improved or tied annual
  net P/L in only `2/7` years with V57 evidence, below the locked `60%` gate.
  Those long-horizon P/L and annual-stability checks are the four failed gates.
- V57-only did improve long-horizon quality and closed drawdown: available
  history PF rose from `1.4192` to `1.4583`, and closed drawdown fell from USD
  `143.7412` to `128.8376`. It retained `89.12%` of trades. At doubled
  canonical stress costs it remained positive over 5Y and available history,
  and both windows remained positive after removing the five largest winners.
  These benefits do not outweigh the failed long-horizon net-profit gates.
- All-family anti-chase was also too blunt for promotion. Over available
  history it raised PF to `1.5521` and reduced closed drawdown to USD
  `123.0682`, but cut trades from `1,259` to `944` and net P/L from USD
  `1,701.7234` to `1,559.9175`.
- The core replay is deterministic: after canonical timestamp normalization,
  the result is identical and all `11` generated artifact hashes reproduce
  byte-for-byte. The locked `verify.py` stops early because it compares
  in-memory `Timestamp` objects with their correct JSON string serialization;
  this narrow verifier defect is recorded rather than hidden or repaired by
  changing the locked implementation after results.
- No new V57-only prospective lane is nominated. The existing research-only
  anti-chase watcher remains online under supervisor PID `35036`, still reports
  `WAIT_BOUNDARY`, and has zero post-boundary candidates before
  `2026-07-27T00:00:00Z`. It remains ignored by the demo executor. The
  deterministic V60 baseline, account controls, and broker authority are
  unchanged.
- The evidence says a fixed extension cutoff confuses healthy momentum with
  late chasing. Any later version must add a causal context interaction
  learned only on development history and tested once on untouched time, such
  as extension conditional on pullback state, volatility, session, and trend
  strength. It must not retune this failed percentile threshold in place.

## Canonical Expected-R Prospective V13 - 2026-07-26

- The ML audit recovered the strongest existing offline model:
  `causal-canonical-expected-r-availability-v11`. It predicts stressed
  Expected-R for already positive canonical specialist candidates rather than
  predicting direction or creating trades. V11 historically passed all `21/21`
  availability gates after requiring at least `1,000` fit rows.
- Frozen V11 historical evidence used `2,851` final fit rows and the
  byte-bound V10 model SHA-256
  `a334d911c316844f3e44bbc7f8adbb4d69c6f326b00e24d4a8e55ba5f964973b`.
  Its six purged out-of-time folds selected `1,808` candidates at about
  `1.158` per weekday, improving weighted mean stressed return to `0.3156R`,
  PF to `1.5402`, and closed drawdown from `74.69R` to `53.95R`. This remains
  historical research, not execution authorization.
- Added and locked
  `xau-usd/xauusd-fast-research/causal-canonical-expected-r-prospective-v13`
  to supply the missing forward confirmation. Contract SHA-256:
  `570a32e8174e62400059b5481ea57afd276055d5ed6516410d63fd0229408824`.
  The untouched boundary is `2026-07-27T00:00:00Z`.
- V13 captures every post-boundary deterministic candidate from all nine V60
  sources. R1 box and R1 pullback both map to the historically trained
  `R1_UPTREND` family. R2, R3, R4, V7, V8, V25, and V57 retain their exact
  family identities. Frozen `R5_TRANSITION` remains absent because it is not
  in the current V60 executable source set.
- The evaluator rebuilds the exact `36` B1/B2 numeric feature columns, applies
  the byte-bound V10 model and frozen family thresholds, and independently
  resolves both retained and vetoed candidates from executable Capital bid/ask
  ticks. Entry, stop, target, horizon, R1 90-day barrier cap, ticket cost,
  holding cost, and `0.05R` stress slippage match the original Step 3 label
  contract. Missing mandatory features cause model abstention and retain-all.
- Capital account `1033030` ticks are intentionally used for forward features
  while training used Dukascopy. Cross-broker feature-domain portability is
  therefore part of the confirmation test rather than being hidden.
- Individual scores and counterfactual outcomes are append-only under
  `D:/AlgoTradingData/prospective/causal-canonical-expected-r-prospective-v13`.
  Aggregate economics stay sealed until the locked endpoint. Validation
  requires at least `20` eligible weekdays, `20` fully resolved candidates,
  and four model-scored families. Confirmation then uses a disjoint period of
  at least `40` eligible weekdays, `60` resolved candidates, and five families.
- A passing stage never authorizes trading. Model refit, Python prediction
  serving, ML shadow, EA consumption, demo authority, live authority, and
  broker action are all false. V60 remains deterministic and unchanged.
- Five focused V13 tests pass. Ruff, formatting, compilation, real V60 source
  normalization, contract verification, and `git diff --check` pass. A real
  pre-boundary Capital candidate rehearsal produced all 36 features, replayed
  a deterministic V11 score/threshold decision, and independently resolved
  its stressed bid/ask outcome.
- The first locked cycle and independent verifier both pass with
  `WAIT_BOUNDARY`: zero post-boundary candidates, zero score rows, zero
  resolutions, and aggregate economics closed.
- V13 was added to
  `xau-usd/operations/v60-prospective-supervisor-v1` as an isolated worker and
  fail-closed health source. Supervisor tests now pass `6/6`. Persistent
  process IDs at handoff are supervisor `34584` and V13 watcher
  launcher/worker `48260/46604`. Consolidated status is `READY`, all V13 and
  supervisor stderr logs are empty, and the V13 health status is
  `WAIT_BOUNDARY`.
- V60 remains `ACTIVE_DEMO_BROKER_ACTION` on account `1033030`; both
  `ml_runtime_authorized` and `ml_shadow_authorized` remain false. V60 feed
  health is current and all requested deterministic feeds are healthy. The
  existing anti-chase prospective lane is also unchanged and still ignored by
  V60.

## V60/V13 Deployment Review Repairs - 2026-07-26

- V60 remains deterministic demo-only on Capital account `1033030`; ML runtime,
  ML shadow, EA consumption, and live authority remain false. The repaired
  supervisor status is `READY`, with no open XAU positions, no entry halt,
  no drawdown suspension, and zero emergency-close failures.
- Drawdown limits now use the lower of the locked absolute amount and the
  activation-equity fraction. At activation equity USD `987.6624`, effective
  limits are USD `74.0747` closed-drawdown suspension, USD `98.7662` closed
  hard stop, and USD `148.1494` floating hard stop.
- Account-wide and same-direction initial risk are each capped at the lower of
  USD `60` or `6%` of activation equity, currently USD `59.2597`. Core
  candidates also have a USD `45` individual initial-risk ceiling.
- MT5 chart preflight now validates each expert and all required safety inputs
  on the same chart. Order tracking no longer substitutes order/deal numbers
  for position tickets; ambiguous fills remain explicitly unresolved and are
  reconciled before horizon management.
- Startup now enforces the tracked exact-source parity artifact at
  `xau-usd/xauusd-fast-research/v60-canonical-demo-portfolio-v2/evidence/`.
  It covers `2,184` fee-stressed fixed-0.01-lot historical trades after
  excluding non-executable R5. Full-history P/L is USD `5,434.3910`, PF
  `1.6486`, and win rate `44.6429%`.
- The exact final 12 completed months, `2025-07-01` through `2026-07-01`,
  contain `363` trades, USD `2,474.8069` fee-stressed P/L, `43.8017%` win
  rate, PF `1.9467`, and USD `208.4144` closed-trade drawdown. The tracked
  monthly table is under the V60 package `reports/` directory.
- Expected-R V13 now evaluates independently routed take-all and model-selected
  account portfolios, fixes the model-scored endpoint count, requires a passed
  validation before confirmation, and adds per-family minimums plus
  deterministic weekly-block bootstrap confidence gates. Validation requires
  40 scored outcomes across five families; confirmation requires 120 new
  outcomes across six families.
- Final V13 contract SHA-256 is
  `44246a60c513d5ec1770e57165325f4ee44a815f4730dfc293b213292e7c5b50`,
  locked before `2026-07-27T00:00:00Z`. It is read-only, currently
  `WAIT_BOUNDARY`, and has no broker authority.
- Older prospective contracts that correctly failed closed after the V60
  safety-config change remain untouched as audit evidence and were retired
  from operational supervision. V13 replaces their fragmented coverage with
  the full nine-source population; the still-valid R4 V49 lane remains active.
- Final focused verification: V60 `20/20` tests, V13 `6/6` tests, supervisor
  `7/7` tests, V13 independent verification `verified=true`, and
  `git diff --check` passes.
- Active processes at handoff: MT5 `41384`; supervisor `42024`; V60 feeds
  `28036/39528`; V60 portfolio `2336/35156`; multisymbol collector
  `44796/38504`; R4 V49 `37984/40504`; V13 `28752/50692`.

## V60 Frozen ML Historical Overlay - 2026-07-27

- Added `build_ml_historical_comparison.py` to compare the exact V60
  fee-stressed fixed-0.01-lot ledger with the frozen Expected-R V10/V11
  out-of-time decisions for the final completed 12 months, July 2025 through
  June 2026. The calculation is hash-bound to the canonical dataset, V11
  predictions, and V60 ledger.
- The join is exact and one-to-one for all `363` historically routed,
  currently executable trades after excluding R5. The `296` feature-complete
  trades receive their frozen F2025 out-of-time decisions; the `67` trades
  missing mandatory XAU features follow the prospective rule
  `MODEL_ABSTAIN_RETAIN_ALL`.
- The ML overlay retains `225` trades and vetoes `138`. P/L falls from USD
  `2,474.8069` to USD `2,284.8483`, because the vetoed group still earned USD
  `189.9587`. Win rate improves from `43.8017%` to `47.1111%`, PF improves
  from `1.9467` to `2.4613`, average P/L per retained trade improves from USD
  `6.8176` to USD `10.1549`, and comparable closed-trade drawdown falls from
  USD `208.4144` to USD `155.5251`.
- This result improves selectivity but fails the total-profit objective. It is
  historical research with already-exposed outcomes, not ML deployment
  evidence. ML runtime, shadow, demo filtering, live, and broker-action
  authority remain false.
- Reports are under
  `xau-usd/xauusd-fast-research/v60-canonical-demo-portfolio-v2/reports/`:
  monthly comparison CSV, JSON summary, and 363-row trade audit.

## V60 V57 Same-Direction Post-Loss Cooldown - 2026-07-27

- The two July 23 V57 long losses were sequential, not concurrent duplicates.
  The existing one-open-position guard worked, but the second long entered 92
  minutes after the first loss closed and crossed a UTC-day boundary, so the
  per-UTC-day entry limit did not block it.
- Added a V57-only 120-minute same-direction cooldown after negative realized
  net P/L. MT5 deal lifecycles are paired by position ID, so guardian exits or
  exit deals with another magic still count. Commission, swap, and fees are
  included. Opposite-direction V57 candidates and all other sources are
  unchanged. V57 fails closed if MT5 deal history is unavailable.
- The path-dependent frozen-ledger replay changes the final completed 12 months
  from 363 trades, USD `2,474.8069` P/L, `43.8017%` win rate, PF `1.9467`,
  and USD `208.4144` drawdown to 356 trades, USD `2,502.7233` P/L,
  `44.1011%` win rate, PF `1.9837`, and the same USD `208.4144` drawdown.
  The effect is seven fewer trades and USD `27.9163` more net P/L.
- Over all available history the policy removes 31 trades, changes net P/L
  from USD `5,434.3910` to `5,432.4660`, raises PF from `1.6486` to `1.6594`,
  and changes closed-trade drawdown from USD `276.8659` to `279.0395`.
  Promotion is based on the approved replay-protection purpose and positive
  recent effect, not a claim that every historical window improves.
- Rebuilt the deployment parity artifact for 2,153 post-policy executable
  rows. Expected-R V13 routing now mirrors the cooldown for both baseline and
  selected research scenarios. Because V13 had zero scores and resolutions
  before its boundary, its old lock was preserved as superseded audit evidence
  and it was cleanly relocked before the boundary at contract SHA-256
  `12a28b26a428bd94d4169a88835e19af90d611acf6061ec3ef5a67c10c18571d`.
- ML runtime, ML shadow, EA consumption, live authority, and V13 broker action
  remain false. The deployment is deterministic demo-only on account `1033030`.

## V60 V12 Exact Profit-Policy Diagnostic - 2026-07-27

- Added
  `xau-usd/xauusd-fast-research/v60-canonical-demo-portfolio-v2/build_ml_profit_policy_comparison.py`
  and focused tests. The offline-only script hash-binds the Step 3 canonical
  labels, V12 out-of-time predictions, V12 final policy, V60 price ledger, and
  current V60 cooldown config.
- The canonical accepted non-R5 population and historical V60 ledger join
  exactly one-to-one for all `2,184` trades by family and signal minute. There
  are `1,495` V12 prediction rows; the remaining `689` rows correctly follow
  `MODEL_ABSTAIN_RETAIN_ALL`.
- Raw and V12 paths replay the V57 120-minute same-direction post-loss cooldown
  independently. In the final 12 completed months, raw is `356` trades, USD
  `2,502.7233`, `44.1011%` win rate, PF `1.9837`, and USD `208.4144`
  closed-trade drawdown. V12 is `325` trades, USD `2,565.6581`, `44.9231%`
  win rate, PF `2.1193`, and USD `191.6678` drawdown.
- V12 improves six-month P/L by USD `24.2434`, twelve-month P/L by USD
  `62.9348`, and all-history P/L by USD `56.7394`. It loses USD `43.7844`
  versus raw in the latest three months and worsens all-history closed-trade
  drawdown by USD `4.3442`. Most recent benefit is concentrated in V57 and the
  F2025 fold.
- The result is explicitly
  `POST_OUTCOME_DIAGNOSTIC_POSITIVE_NOT_DEPLOYABLE`. Historical outcomes were
  exposed, V12's final forward policy is
  `RETAIN_ALL_INSUFFICIENT_CALIBRATION_USD_IMPROVEMENT`, and disjoint
  prospective confirmation is unavailable. No V60 runtime file or authority
  changed; ML serving, shadow, EA consumption, demo filtering, live, and
  broker-action authority all remain false.
- Reports include window, fold, final-12-month monthly and family summaries,
  plus CSV and Parquet row audits under the V60 package `reports/` directory.
  The full V60 package test suite passes `24/24`.

## V60 B3 Macro Expected-R Diagnostic - 2026-07-27

- Threshold engineering on the frozen 36-feature B1/B2 score did not solve the
  ML problem. Direct expected-USD training, monthly adaptive thresholds,
  disjoint calibration/validation, and a 120-day recent-validation drift gate
  all remained worse than raw in the latest three months or over full history.
  Those exploratory variants were not promoted.
- COMEX B4 was tested only on causally complete rows. Its F2025 calibration
  correctly selected retain-all, so it produced no portfolio change. The
  older Step 4 HGB/logistic B1/B2/B3 classifiers also failed exact-portfolio
  bottom-tail veto diagnostics.
- Added `build_ml_macro_expected_r_comparison.py` and focused tests for the
  distinct B1+B2+B3 partial-pooling ridge. B3 adds completed dollar-index and
  Treasury returns while retaining alpha `300`, family-interaction scale
  `0.25`, clipped stressed-R target `[-3R,+3R]`, and purged chronological
  folds. The profit-policy grid is limited to `0%` through `15%` veto with at
  least `85%` calibration coverage.
- The script hash-binds the canonical dataset, split assignments, feature
  contract, V10 and V12 implementation/config files, V60 ledger, and current
  V60 config. F2020-F2023 retain all; F2024 chooses `15%` and F2025 chooses
  `5%`. Missing predictions abstain and retain.
- Exact V60 results after independent current-cooldown replay:
  all history `2,109` versus `2,153` trades, USD `+86.7893` ML-minus-raw,
  PF `+0.0318`, drawdown USD `-8.1658`; final 12 months USD `+66.7226`;
  final six months USD `+7.8742`; latest three months USD `-18.3237`.
- Status is `HISTORICAL_DIAGNOSTIC_POSITIVE_LATEST_WINDOW_FAIL`,
  `deployment_eligible=false`. Historical outcomes informed this diagnostic,
  and no prospective Capital dollar/bond confirmation exists. ML serving,
  shadow, EA consumption, demo filtering, live, broker action, and runtime
  change remain unauthorized.

## V14 Macro Expected-R Prospective Confirmation - 2026-07-27

- Frozen a final 44-feature B1/B2/B3 partial-pooling Ridge model from all
  `3,024` causal feature-pass candidates with labels complete before
  `2026-07-01T00:00:00Z`. The pooled veto quantile is fixed at `5%`; the
  construction fit retained `2,860` rows and `95.0119%` of structural weight.
  This in-sample fit statistic is not deployment evidence.
- Added
  `xau-usd/xauusd-fast-research/causal-canonical-macro-expected-r-prospective-v14`.
  It consumes immutable V13 B1/B2 score facts, ignores V13's model decision,
  and adds only completed Dukascopy `DOLLARIDXUSD` and `USTBONDTRUSD` state.
  Missing, stale, incomplete, or delayed features always produce
  `MODEL_ABSTAIN_RETAIN_ALL`.
- V14's initial zero-row pre-boundary lock was preserved as superseded audit
  evidence after static lint found mechanical import cleanup. The clean
  package was relocked at `2026-07-26T21:58:16Z`, still before its untouched
  `2026-07-27T03:00:00Z` boundary. Final contract SHA-256 is
  `ed5e6c2d69ac037de878017745d6c366b2a5ffdfab09500a2064bd10d9668d83`.
  No model, feature, threshold, protocol, or boundary changed; both locks had
  zero candidates and zero scores.
- The preregistered validation requires at least 20 eligible weekdays, 40
  resolved scored candidates, and five families. A later disjoint confirmation
  requires 40 additional weekdays, 120 resolved candidates, and six families.
  Each stage must retain at least 90% of raw trades, improve exact V60 P/L,
  avoid worse PF or drawdown, improve the latest stage, and pass a weekly-block
  bootstrap lower bound above zero.
- Added a continuous free Dukascopy macro refresh worker. The first real run
  reconciled `1,242` symbol-hours through `2026-07-26T21:00:00Z`, reproduced
  the frozen transformation with `0.0` maximum absolute parity error, and
  correctly retained closed-market hours as zero-tick source files. No
  Databento or paid source is used.
- Added the macro refresh and V14 watchers to the existing supervisor. Current
  supervisor status is `READY`; seven worker groups and all seven health
  sources are healthy. V14 reports `WAIT_BOUNDARY`; macro health reports
  `CURRENT`; MT5 remains PID `41384`.
- Verification: V60 `26/26`, V13 `7/7`, V14 `4/4`, macro data foundation
  `3/3`, and supervisor `7/7` tests pass. V14's model-serving, ML-shadow,
  EA-consumption, broker-action, demo, and live authorities are all false.

## Auxiliary ML Transfer Experiments V15-V18 - 2026-07-27

- V15 tested whether the overlap-cleaned auxiliary population could improve
  canonical filtering. It used `64,319` action labels from `24,835` mechanical
  events in `13,639` structural episodes after removing canonical-overlap
  episodes. The retained pool contains `26,775` winning and `37,544` failing
  action labels; the quarantined journey-attempt rows remained excluded.
- V15 stacked three causal auxiliary scores into the B1+B2+B3 canonical
  Expected-R model. It improved raw V60 over all history by USD `82.6234`, but
  finished USD `4.1659` below locked B123 and lost USD `31.8425` versus raw in
  the latest three months. Decision: `V15_HISTORICAL_GATE_FAIL`.
- V16 required two-of-three auxiliary agreement before honoring a B123 veto.
  It re-admitted `53` of `66` B123 vetoes. All-history P/L remained USD
  `44.4445` above raw but USD `42.3448` below B123; six-month and three-month
  P/L were both USD `24.1386` below raw. Decision:
  `V16_HISTORICAL_GATE_FAIL`.
- V17 isolated `V57_BREAK_SWING_H4ADX_HIGH`, where the three auxiliary scores
  achieved mean out-of-time AUCs of about `0.606-0.615`. It re-admitted `17`
  of `24` B123 V57 vetoes. It matched raw over three and six months and
  improved raw all-history P/L by USD `76.7092`, PF from `1.6594` to `1.6815`,
  and drawdown from USD `279.0395` to `263.1529`, but remained USD `10.0801`
  below B123 and did not improve the six-month raw result. Decision:
  `V17_HISTORICAL_GATE_FAIL`.
- Added, preregistered, tested, locked, evaluated once, and independently
  verified
  `xau-usd/xauusd-fast-research/causal-v8-auxiliary-veto-v18`. V18 tested the
  strongest stable family transfer relationship: the frozen nonlinear
  auxiliary score ranked `V8_RETEST_HEALTH` outcomes above `0.55` AUC in all
  six out-of-time folds, with mean AUC `0.6572`.
- V18 could only add a calibration-approved V8 bottom-tail veto to B123. It
  could not create trades, re-admit B123 vetoes, change another family, or
  alter runtime. Four folds had sufficient calibration support. V18 added
  `19` V8 vetoes, but none of the six fold-level portfolio deltas improved
  B123. All-history P/L was USD `5,490.6594`: USD `58.1935` above raw but USD
  `28.5959` below B123. PF was `1.6891`, win rate `44.7733%`, drawdown USD
  `270.8737`, and trade count `2,095`.
- V18 matched B123 over the latest twelve months: `335` trades, USD
  `2,569.4458`, `44.7761%` win rate, PF `2.0790`, and USD `191.6678`
  drawdown. It therefore retained B123's latest-three-month shortfall: `60`
  trades, USD `331.4018`, PF `1.6461`, versus raw USD `349.7255`.
  Decision: `V18_HISTORICAL_GATE_FAIL`.
- V18 contract SHA-256 is
  `7bc6ade920a1091c43973f52fa45776e016fde3064dd2d5e5ed8ba6d588e6d00`.
  Independent verification reports `VERIFIED`, `11` artifacts, and focused
  tests pass `4/4`. The full comparison through V18 is
  `causal-v8-auxiliary-veto-v18/outputs/ML_EXPERIMENT_COMPARISON_V18.md`.
- The combined conclusion is that the larger auxiliary label pool contains
  genuine ranking information, especially for V57 and V8, but the current
  binary veto policies discard occasional large winners and do not improve
  exact portfolio P/L robustly. AUC improvement alone is not sufficient.
  V14 remains the only locked prospective ML lane. V15-V18 have no serving,
  shadow, EA, demo, live, sizing, runtime, or broker authority.

## V60 Absolute-USD Demo Risk Limits - 2026-07-29

- Demo account `1033030` no longer has a minimum-balance eligibility gate or
  activation-equity scaling of risk limits. The active runtime reports
  `risk_limit_mode=ABSOLUTE_USD_ONLY` and
  `equity_fraction_limits_enabled=false`.
- Fixed controls remain active: USD `60` account and same-direction concurrent
  initial risk, USD `225/180` closed-drawdown suspend/resume, USD `300` hard
  closed-drawdown stop, and USD `449.7675` floating-drawdown hard stop. Broker
  margin remains unavoidable.
- Deployment preserved activation time, activation-equity telemetry, closed
  P/L, seen candidates, position records, and daily-entry records. No state
  reset or account funding occurred.
- Canonical tests pass `34/34`; tick replay tests pass `9/9`. The full
  position-origin runtime replay at deployed capital accepted `1,431` trades,
  produced USD `1,304.56`, PF `1.3090`, USD `189.52` maximum equity drawdown,
  and no deadlock.
- Evidence:
  `xau-usd/xauusd-fast-research/v60-canonical-demo-portfolio-v2/evidence/ABSOLUTE_USD_RISK_LIMIT_DEMO_DEPLOYMENT_20260729.md`.

## Legacy Frequency Causal Quality V2 - 2026-07-29

- Legacy Hybrid Salvage V1 confirmed that the old high-profit hybrid does not
  contain a qualifying one-ticket fixed-lot lane. Its frequency scope remained
  positive in later years but only reached PF `1.10-1.20`.
- Added, preregistered, implementation-locked, tested, and evaluated
  `legacy-frequency-causal-quality-v2`. It reconstructed `3,417` RUNNER
  frequency signals and attached exact completed-bar causal context to `3,382`;
  `35` missing contexts failed closed.
- Four fixed structural gates tested shock exclusion, opposite-H4-trend
  exclusion, dual H1/H4 slope conflict, and their combination. Selection used
  only 2022-07 through 2024-06.
- No policy passed development: net remained between USD `-193.68` and
  `-182.93`, PF between `0.9019` and `0.9068`, and top-ten-winner-removed P/L
  remained strongly negative. Later-window improvements were not used for
  selection.
- Decision: `NO_CAUSAL_QUALITY_GATE_PASSES`. No MT5 rerun, ML activation, demo
  attachment, or runtime change is authorized. Focused tests pass `6/6`.

## V60 Portable ML Top-Up V3 Demo - 2026-07-29

- V2 removed the five Dukascopy-specific microstructure fields and retained 13
  completed-bar/trade-context features. Its frozen historical policy keeps all
  `1,676` V60 trades and adds one `0.01` lot above causal rank `0.80` from
  2024 onward, subject to the existing risk limits.
- Historical development result: V60 USD `5,045.67`, PF `1.721`, floating DD
  USD `335.34`; portable top-up USD `5,296.78`, PF `1.723`, floating DD USD
  `329.35`. Delta is USD `251.10`; moving-week lower 95% bound is USD `92.38`.
- V3 reconstructed the exact forty-model 2026 ensemble. All 147 stored 2026
  scores and ranks reproduce with `0.0` error. Training has `1,918` rows,
  stops at the purged `2025-12-30T00:00:00Z` cutoff, and uses no 2026 outcomes.
- Outcome-free Capital/Dukascopy parity passed every frozen gate on `4,896`
  common July bars and `19,584` contexts: score/rank Spearman
  `0.9825/0.9825`, mean rank difference `0.0310`, top-quintile Jaccard
  `0.8892`, and Capital precision/recall `0.9548/0.9283`.
- The exact model is active on demo account `1033030` through a separately
  hash-bound overlay. The deterministic baseline order fills and is persisted
  before ML runs. Any ML failure produces baseline-only behavior. ML may add
  one separate `0.01` lot only for historically known-risk R2/R3/R4/V7/V8/V25
  or V57 signals that pass every existing portfolio control.
- Runtime limits: maximum one open ML top-up and two top-ups per UTC day. R1
  box and pullback remain baseline-only. ML shadow and live authority remain
  false.
- Active status is `ACTIVE_DEMO_BROKER_ACTION`, ML ready, feeds healthy, zero
  positions at deployment, `minimum_balance_requirement_enabled=false`, and
  `risk_limit_mode=ABSOLUTE_USD_ONLY`.
- Verification: portfolio `41/41`, tick replay `9/9`, prospective V3 `4/4`,
  and Python compilation pass. Evidence:
  `xau-usd/xauusd-fast-research/v60-canonical-demo-portfolio-v2/evidence/PORTABLE_ML_TOPUP_V3_DEMO_DEPLOYMENT_20260729.md`.
