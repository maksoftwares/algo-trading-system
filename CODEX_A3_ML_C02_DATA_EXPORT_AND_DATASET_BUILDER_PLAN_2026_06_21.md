# CODEX PLAN — C02: Read-Only MT5 Multi-Account Data Export and Dataset Builder

**Project:** `maksoftwares/algo-trading-system`
**Program:** A3 Python ML Signal-Quality V1.2 (multi-account A1/A2/A3)
**Date:** 2026-06-21
**Accounts:** A1 `1025742`, A2 `1033030`, A3 `1033669`
**Symbol:** XAUUSD · **Family:** breakout_retest · **Mode:** read-only export, offline build, shadow-only
**Depends on:** C00 contracts (merged), C01 bootstrap (`scripts/generate_a3_ml_c01_pipeline.py`, currently `PIPELINE_ONLY`)
**Authorizes:** nothing beyond read-only export + offline dataset build + audit. No training in C02. No live trading, no broker action, no runtime/terminal mutation.

---

## 0. Boundary (non-negotiable)

```text
A3 lanes 933200/933300/933400 remain paused.
A1/A2 runtime unchanged. Profit-lock remains DRY_RUN_DISARMED.
No OrderSend, CTrade, TRADE_ACTION_*, order/position modify or close.
No EA attach, preset arm, chart change, symbol add, or terminal/login mutation.
No MetaTrader5.login() account switching. Attach read-only to an operator-named terminal path only.
Training code must never import MetaTrader5.
Any verification failure => fail closed, write failure report, exit non-zero, emit no "complete" dataset.
```

## 0.1 Assumptions / decisions needed (resolve before C02b)

```text
D1. Do A1 and A2 actually emit breakout_retest would-signals?
    The locked model is family-scoped to breakout_retest. If A1 (920101 evening core)
    and A2 run other families, their rows are exported and audited but CANNOT be pooled
    into the breakout_retest model. Multi-account then only deepens A3 + builds infra.
D2. Are A1/A2/A3 on the same broker/server? Affects per-account execution params and
    whether the same XAUUSD market setup co-occurs across accounts (leakage; see 4.2).
D3. Tick-history depth actually retained in each terminal (drives label resolvability).
D4. Package naming: keep `ml/a3_meta_v1/` (currently empty) or rename account-agnostic
    `ml/signal_quality_v1/`. Plan uses `signal_quality_v1` and notes the alias.
```

---

## 1. Architecture — two-stage hard separation

```text
STAGE A  EXPORTER  (Windows MT5 host only, imports MetaTrader5 read-only)
  scripts/mt5_export/  ->  immutable per-account raw snapshot bundle + SHA256 manifest
                           (bars, ticks, deals/orders, account/terminal/symbol meta,
                            copies of observer/would-signal + position-path logs)

STAGE B  BUILDER  (platform-independent, NO MetaTrader5 import; runs in CI/sandbox)
  ml/signal_quality_v1/  ->  normalized dataset (parquet) + decisions/trades/bars CSVs
                             + per-fold + per-account audits + dataset status

STAGE C  (existing) C01 pipeline consumes the normalized CSVs/bars and emits status:
  scripts/generate_a3_ml_c01_pipeline.py  (extended to multi-account inputs)
```

Rationale: (a) the broker API lives in one isolated package the training/build code cannot import; (b) the sandbox has no MetaTrader5, so Stage B/C run anywhere; (c) raw snapshots are write-once and hashed, so every downstream artifact is reproducible from an immutable, verifiable source.

---

## 2. Module & script inventory

| Path | Stage | Imports MT5 | Role |
|---|---|---|---|
| `scripts/mt5_export/mt5_readonly.py` | A | yes (whitelist only) | Thin wrapper exposing only read-only MT5 calls |
| `scripts/mt5_export/verify_terminal.py` | A | yes | Account + terminal + symbol verification, fail-closed |
| `scripts/mt5_export/export_account_snapshot.py` | A | yes | Export one account's bundle (bars/ticks/deals/meta + log copies) |
| `scripts/mt5_export/collect_observer_logs.py` | A | no | Read-only copy + hash of would-signal / position-path logs |
| `scripts/mt5_export/write_snapshot_manifest.py` | A | no | SHA256 manifest + coverage report for a bundle |
| `ml/signal_quality_v1/snapshot_loader.py` | B | no | Load + validate raw bundle against its manifest |
| `ml/signal_quality_v1/timebase.py` | B | no | Server-time → UTC normalization, DST/offset handling |
| `ml/signal_quality_v1/signal_id.py` | B | no | exact_signal_id + market_setup_id (account-independent) |
| `ml/signal_quality_v1/fuzzy_dedup.py` | B | no | setup_group_id + cross-account market_setup_group_id |
| `ml/signal_quality_v1/labels.py` | B | no | Tick-level virtual execution labels (exec-label contract) |
| `ml/signal_quality_v1/slippage.py` | B | no | Per-account P50/P95 slippage model, fold-causal |
| `ml/signal_quality_v1/features.py` | B | no | Causal feature build aligned to feature registry |
| `ml/signal_quality_v1/causal_percentiles.py` | B | no | Trailing percentile features, prefix-invariant |
| `ml/signal_quality_v1/regime.py` | B | no | Deterministic D1 regime (regime contract) |
| `ml/signal_quality_v1/schema.py` | B | no | Normalized row schema + validators |
| `ml/signal_quality_v1/dataset_builder.py` | B | no | Orchestrates B; writes dataset + audits + status |
| `scripts/build_signal_quality_dataset.py` | B | no | CLI entry for the builder |
| `scripts/generate_a3_ml_c01_pipeline.py` | C | no | Existing; extend `--accounts`, multi-account inputs |

All Stage-A scripts share the read-only wrapper; none of B/C may import `MetaTrader5` (enforced by test, §14).

---

## 3. Area 1 — Exact data to export (per account)

One bundle per account under `outputs/ml/exports/<ACCOUNT_LABEL>/<SNAPSHOT_VERSION>/`.

| Source | MT5 read-only call / source | Output | Notes |
|---|---|---|---|
| Bars M5/M15/H1/H4/D1 | `copy_rates_range(symbol, TF, t0, t1)` | `bars_<TF>.parquet` | cols: time_utc, open, high, low, close, tick_volume, spread, real_volume |
| Ticks | `copy_ticks_range(symbol, t0, t1, COPY_TICKS_ALL)` | `ticks/date=YYYY-MM-DD.parquet` | bid, ask, last, volume, time_msc, flags; partitioned by day; record gaps |
| Would-signal / observer logs | file copy from `MQL5/Files` + common files | `observer_logs/*.jsonl` + hashes | raw breakout_retest decisions per lane/magic (incl. blocked/rejected) |
| Executed trade history | `history_deals_get(t0, t1)` | `deals.parquet` | reconstruction + slippage only; never a feature |
| Orders | `history_orders_get(t0, t1)` | `orders.parquet` | join key to deals/positions |
| Spreads | bars `spread` col + tick `ask-bid` + observer spread logs | `spread_series.parquet` | decision-time spread feeds `cost_R` |
| Fills / slippage | derived from `deals` (request vs fill price per leg) | `fills.parquet` | entry/SL/TP/timeout adverse slippage source |
| Position-path snapshots | position-path observer log copy | `position_paths/*.jsonl` + hashes | LABEL/diagnostic only; MFE/MAE never an entry feature |
| Account metadata | `account_info()` | `account_info.json` | login, server, company, currency, leverage, **trade_mode (must be DEMO)** |
| Terminal metadata | `terminal_info()` | `terminal_info.json` | build, path, data_path, company, connected, community_account(false) |
| Symbol metadata | `symbol_info(symbol)` | `symbol_info.json` | point, digits, trade_tick_size/value, contract_size, stops_level, freeze_level, vol_min/step |

Each export records the requested `[t0, t1]` window, rows returned, and a per-source coverage/gap summary.

---

## 4. Area 2 — Safe read-only export

### 4.1 Read-only wrapper (`mt5_readonly.py`)
Expose only: `initialize(path=...)`, `shutdown`, `last_error`, `account_info`, `terminal_info`, `symbol_info`, `symbol_info_tick`, `copy_rates_range`, `copy_rates_from`, `copy_ticks_range`, `history_deals_get`, `history_orders_get`, `positions_get`. Hard-deny (never wrapped/imported): `order_send`, `order_check`, `order_calc_margin/profit`, `positions_modify`, anything writing state. `order_check` is excluded deliberately even though "read-only," to keep zero broker-write surface.

### 4.2 Verification (fail-closed, before any export)
```text
account:  account_info().login in {1025742,1033030,1033669}
          AND trade_mode == ACCOUNT_TRADE_MODE_DEMO   else ABORT
terminal: terminal_info().path matches operator-provided allowlisted path for that account
          AND terminal_info().connected == true       else ABORT
symbol:   symbol_info("XAUUSD") present, point/digits/tick_size available  else ABORT
no switch: do NOT call login(); attach to the one terminal the operator named.
```
Mismatch, unknown login, real account, missing symbol metadata, or connection error ⇒ write `…_EXPORT_FAILCLOSED.json` and exit non-zero. No partial bundle is marked complete.

### 4.3 Forbidden-symbol static guard
A test greps every file under `scripts/mt5_export/` for `order_send|OrderSend|CTrade|TRADE_ACTION|positions_modify|order_check|login(` and fails on any hit outside the wrapper's deny-list comment (mirrors `tests/test_a3_ml_shadow_safety.py`).

**Reports:** `A3_ML_C02_EXPORT_<LABEL>_REPORT.md/json`, `A3_ML_C02_EXPORT_FAILCLOSED_<LABEL>.json` (on failure).

---

## 5. Area 3 — Normalized dataset schema

One row per **canonical setup_group** (post fuzzy-dedup), family = breakout_retest. Written as `outputs/ml/signal_quality_v1/data/dataset_<VERSION>.parquet`, plus C01-compatible `…_DECISIONS.csv` / `…_TRADES.csv`.

```text
# identity / scope (metadata — never features)
account_scope        (1025742|1033030|1033669)
account_label        (A1|A2|A3)
symbol               (XAUUSD)
family               (breakout_retest)
candidate_id         (e.g. B0_RAW_ALL_SESSION)
exact_signal_id      (sha256, account-scoped; per grouping contract)
setup_group_id       (within-account fuzzy group)
market_setup_group_id(account-INDEPENDENT; symbol+family+direction+level+times) # see 6.2
lane_list, magic_list, duplicate_count                  # metadata only

# time contract (UTC, completed-bar causal)
feature_time_utc <= decision_time_utc < entry_eligible_from_utc <= label_end_time_utc
direction            (LONG|SHORT)
regime               (RISING|FALLING|MIXED|UNKNOWN)

# features (16 ordered numeric, exact formulas from A3_ML_FEATURE_REGISTRY_V1.csv)
f01_h1_ema20_slope_aligned_atr ... f16_minutes_from_session_start_scaled
(+ per-feature *_missing indicator where noncritical)

# labels (execution-label contract)
y_win_expected, y_net_R_expected, y_win_p95_stress, y_net_R_p95_stress,
y_outcome, y_loss_class, y_MFE_R, y_MAE_R, y_holding_seconds,
y_holding_active_m5_bars, label_status

# audit / provenance
data_complete_flag, slippage_model_status, label_maturity (MATURE|IMMATURE),
server_time_offset_min, tick_coverage_flag, ohlc_fallback_flag,
exporter_version, builder_version, feature_registry_hash,
snapshot_manifest_hash, source_file_hashes{bars,ticks,deals,observer,position_path},
dataset_version, build_commit
```
The schema validator rejects any column in the C01 pipeline's `PROHIBITED_FEATURE_COLUMNS` from the feature block, and excludes `NON_TRAINABLE_LABEL_STATUSES` from supervised rows.

---

## 6. Area 4 — Merge A1/A2/A3 without leakage

### 6.1 Account as metadata only
`account_scope`, `account_label`, `lane_list`, `magic_list`, `duplicate_count` are never model features (already enforced by C01's prohibited set + grouping contract). No `account`-derived feature, ratio, or one-hot.

### 6.2 Cross-account duplication is the central leakage risk
Because `exact_signal_id` is account-scoped, the **same XAUUSD market setup** observed by A1, A2 and A3 yields three different rows that do **not** collapse. Pooling them naively (a) triples pseudo-sample and (b) puts near-identical rows in different folds.

```text
Fix: build an account-INDEPENDENT market_setup_group_id from
  symbol + family + direction + normalized_level + break/retest/confirmation times
  (drop account_scope; reuse the locked fuzzy thresholds: 0.10xATR level, 10-min
   decision window, <=20-min component span).
Rules:
  - market_setup_group_id may not cross train/test boundaries (split integrity unit).
  - one canonical row per (market_setup_group_id) for SUPERVISED FITTING;
    per-account copies retained as attribution metadata + for per-account scoring.
  - duplicate_count / contributing accounts stored as metadata, never features.
Contract touchpoint: this is ADDITIVE (does not change locked exact_signal_id).
  If fitting will dedup on market_setup_group_id, record it in a grouping-contract
  addendum and re-hash before any CANDIDATE claim (not required for PIPELINE_ONLY).
```

### 6.3 Splitting
Reuse C01 constants: 5 outer expanding + 3 inner folds, `EMBARGO = 24h + 5min` in **active-market time**, purge full event-interval overlap, group integrity on both `setup_group_id` and `market_setup_group_id`. No random/shuffled splits. Fit all transforms train-only; disjoint chronological calibration tail (0.20).

### 6.4 Per-account diagnostics
Every audit reports counts, class balance, regime mix, label-status mix, slippage adequacy, and fold diagnostics **per account and combined**, plus a cross-account duplication rate (how many market_setup_groups appear on >1 account).

---

## 7. Area 5 — Label building

Per `A3_ML_EXECUTION_LABEL_CONTRACT_V1.md`, applied to **all raw would-signals** (executed + blocked + rejected), not only executed trades.

```text
entry:    LONG first fresh ask / SHORT first fresh bid after decision_time;
          no same-bar fill; expire at next M5 close -> CANCELLED_NO_FRESH_TICK.
risk:     risk_price = max(raw, broker_stops+5pt, 3xspread@fill, 300 XAU pts); TP=1.50R.
horizon:  MAX_HOLD_ACTIVE_M5_BARS=288 active bars; weekend closure does not consume;
          timeout exit at first fresh quote, else DATA_UNRESOLVED_TIMEOUT.
gaps:     if first quote crosses SL/TP, exit at actual quote, record level-to-fill slip.
labels:   y_outcome in {TP,SL,TIMEOUT_*,CANCELLED_NO_FRESH_TICK,DATA_UNRESOLVED_TIMEOUT,
          EXECUTION_AMBIGUITY,DATA_UNRESOLVED}; y_win_expected primary; P95-stress for gates.
```

### 7.1 Tick-vs-OHLC ambiguity
```text
window fully covered by ticks         -> resolve TP/SL ordering precisely.
tick gap, SL & TP both inside one bar -> EXECUTION_AMBIGUITY (do NOT assume adverse-first);
                                         set ohlc_fallback_flag, exclude from supervised.
tick gap, only one of SL/TP in range  -> resolvable; record ohlc_fallback_flag.
```

### 7.2 Slippage P50/P95 (per account, fold-causal)
Per `A3_ML_SLIPPAGE_MODEL_CONTRACT_V1.md`, fit **one model per account** (execution differs by terminal/broker). Buckets global / Dubai-session / spread-tercile (use a bucket only at ≥50 rows). Adequacy: entry≥200, SL≥100, TP≥50 → else `slippage_model_status=INSUFFICIENT` and that account caps at `EXPLORATORY_MODEL`. Expected labels use adverse P50; stress labels adverse P95; no favorable TP slippage. Fit only from fills before each test-fold start.

### 7.3 Label maturity
A row is `MATURE` only if its full label window has closed AND data covers it. Recent/open signals → `IMMATURE`, excluded from supervised training, kept in audit. This protects future forward data from being mislabeled on truncated windows.

---

## 8. Area 6 — Feature building

```text
- completed bars only; every input bar closed before decision_time_utc.
- causal windows; percentiles trailing, exclude current row (causal_percentiles.py).
- forbidden as inputs: future bar/tick, final PnL, MFE/MAE, exit reason/price/time,
  future spread/slippage, post-signal balance/PnL, manual labels, later model scores.
- missingness by registry criticality:
    critical missing  -> reject row, log DATA_INCOMPLETE_SIGNAL (not scoreable).
    noncritical miss  -> train-only median impute + *_missing indicator (counts to budget).
- exact formulas + ordering pulled from A3_ML_FEATURE_REGISTRY_V1.csv (hash recorded).
- prefix-invariance test: features(full_history)[rows<=T] == features(prefix_to_T).
```
The builder emits `feature_registry_hash` and fails if the CSV hash differs from the locked value.

---

## 9. Area 7 — Storage / versioning

```text
immutable raw snapshot:  outputs/ml/exports/<LABEL>/<SNAPSHOT_VERSION>/  (write-once, hashed)
normalized dataset:      outputs/ml/signal_quality_v1/data/dataset_<DATASET_VERSION>.parquet
manifests:               outputs/ml/signal_quality_v1/manifests/<...>_MANIFEST.json (SHA256 of every input+output)
reports/audits:          outputs/ml/signal_quality_v1/reports/  (see §13)

DATASET_VERSION = SQV1_<YYYYMMDD>_<gitshort>_<accounts>     e.g. SQV1_20260622_e74fe61_A1A2A3
SNAPSHOT_VERSION= EXP_<LABEL>_<YYYYMMDDHHMM>_<terminalbuild>

commit (small, text/JSON): manifests, audit reports, schema, dataset status, tiny fixtures.
gitignore (large/raw):     bars/ticks parquet, raw terminal exports, full dataset parquet,
                           observer/position-path raw copies.  (matches "no raw tick history in git")
Every ignored artifact is represented by a committed SHA256 entry so it stays reproducible/verifiable.
```

---

## 10. Area 8 — Training workflow & status gating (C02 builds; later commits train)

C02 **does not train**. It determines `dataset_status` from the built, audited dataset; training is C05+ per the owner timeline.

```text
PIPELINE_ONLY     : contracts unlocked OR setups<300 OR minority<90 OR weeks<8
                    OR global_feature_budget<5 OR one direction OR one regime OR slippage INSUFFICIENT.
                    => pipeline/audit only, NO supervised training.
EXPLORATORY_MODEL : setups>=300, minority>=90, weeks>=8, both directions, >=2 regimes, budget>=6.
                    => M0 base-rate + M1 logistic L2 diagnostics only, NO promotion.
CANDIDATE_MODEL   : setups>=1000, minority>=240, weeks>=16, all regimes, budget>=12, slippage adequate.
                    => full purged-OOS candidate eval + calibration + threshold + gates.
```
When (later) training is allowed: baseline first (M0 → M1_L2), 5 outer / 3 inner purged walk-forward, sigmoid calibration on disjoint tail, threshold on calibration only, shadow scores to `a3_ml_offline_scores.csv`. Status is computed **per account and combined**; a combined CANDIDATE claim still requires the cross-account dedup of §6.2.

C02's measurable goal: show, per account, whether exported history moves the status needle (e.g., A3 PIPELINE_ONLY→EXPLORATORY), and quantify what A1/A2 contribute given decision D1.

---

## 11. Area 9 — Backtest / shadow replay workflow

```text
"replay EAs" == replay the already-logged would-signals offline. Do NOT run EAs against a broker.
harness: scripts/replay_shadow_scores.py (Stage B, no MT5) reads the normalized dataset,
         (later) applies the selected model -> TAKE/SKIP/ABSTAIN, writes a3_ml_offline_scores.csv.
compare vs raw deterministic: paired delta_R per raw base signal (skips contribute 0),
         model_take*y_net_R_p95_stress vs raw/rule_take*y_net_R_p95_stress  (power/MDE contract).
scoring: per account AND combined; report retention, PF, expectancy, delta_R with 90/95% block-bootstrap CIs.
evidence gate before ANY forward shadow use:
  dataset_status=CANDIDATE_MODEL, leakage audit PASS, calibration PASS, confidence-bound gates PASS,
  power/MDE adequate or CONTINUE_EVIDENCE, both directions + required regimes, cross-account dedup applied.
C02 deliverable here = the read-only replay substrate + the comparison report skeleton (no model yet).
```

---

## 12. Area 10 — Risks & blockers

| Risk | Impact | Mitigation / gate |
|---|---|---|
| MT5 data quality (bar revisions, missing history) | biased labels/features | coverage report per source; `data_complete_flag`; revision hash check on re-export |
| Tick gaps / incomplete ticks | unresolved or ambiguous labels | `tick_coverage_flag`, OHLC fallback → EXECUTION_AMBIGUITY; exclude from supervised |
| Timezone / server offset / DST | silent feature & label misalignment | normalize all to UTC in `timebase.py`; record `server_time_offset_min`; DST-boundary test |
| Cross-account duplicate setups | pseudo-replication + fold leakage | `market_setup_group_id` dedup + split integrity (§6.2) |
| Cross-lane duplicate setups | same as above within account | locked fuzzy grouping; lane/magic metadata-only |
| Account-specific execution (spread/slippage) | label bias if pooled | per-account slippage model + per-account decision-time spread in `cost_R` |
| Slippage insufficiency (A1/A2 thin fills) | over-optimistic labels | adequacy gate → `INSUFFICIENT` caps account at EXPLORATORY; P95-stress gating |
| Family mismatch (A1/A2 ≠ breakout_retest) | invalid pooling | partition by family; pool only same-family; surface in audit (decision D1) |
| Limited history → overfitting | false edge | events/15 feature budget, PIPELINE/EXPLORATORY caps, no promotion, walk-forward only |
| Label immaturity on recent rows | truncated-window mislabel | `label_maturity` rule; exclude IMMATURE from supervised |

---

## 13. Reports & audit files (names)

```text
A3_ML_C02_EXPORT_<LABEL>_REPORT.md / .json          # per-account export coverage
A3_ML_C02_EXPORT_FAILCLOSED_<LABEL>.json            # on any verification failure
A3_ML_C02_SNAPSHOT_MANIFEST_<LABEL>_<SNAPSHOT>.json # SHA256 of raw bundle
A3_ML_C02_DATA_AUDIT.md / .json                     # combined + per-account dataset audit
A3_ML_C02_SIGNAL_GROUPING_AUDIT.md                  # exact/fuzzy/market dedup + cross-account rate
A3_ML_C02_LABEL_AUDIT.md                            # outcome/status mix, maturity, ambiguity rate
A3_ML_C02_SLIPPAGE_ADEQUACY_<LABEL>.json            # per-account adequacy + buckets
A3_ML_C02_FEATURE_AUDIT.md                          # missingness, prefix-invariance, registry hash
A3_ML_C02_LEAKAGE_AUDIT.md                          # time ordering, purge/embargo, group integrity
A3_ML_C02_PER_ACCOUNT_STATUS.json                   # PIPELINE/EXPLORATORY/CANDIDATE per account+combined
A3_ML_C02_DATASET_MANIFEST_<DATASET_VERSION>.json   # SHA256 of every input + output
A3_ML_C02_BUILD_REPORT.md                           # end-to-end summary + status verdict
```

---

## 14. Test cases

```text
# safety (Stage A)
test_export_uses_readonly_whitelist_only          # no forbidden symbols outside deny-list
test_export_rejects_non_demo_account              # trade_mode != DEMO -> ABORT
test_export_rejects_unknown_login                 # login not in allowlist -> ABORT
test_export_terminal_path_mismatch_failcloses
test_no_mt5_import_in_builder_or_training         # grep ml/ + training scripts: 0 MetaTrader5 imports
test_failclose_emits_no_complete_dataset

# timebase / identity
test_server_time_to_utc_dst_boundaries
test_exact_signal_id_stable_and_account_scoped
test_market_setup_group_id_account_independent
test_cross_account_same_setup_groups_together
test_group_ids_never_cross_train_test

# labels
test_long_ask_entry_short_bid_entry
test_tp_before_sl_and_sl_before_tp_resolution
test_tick_gap_both_levels_in_bar_is_ambiguous     # no adverse-first assumption
test_288_active_bar_timeout_skips_weekend
test_immature_window_excluded_from_supervised
test_slippage_adequacy_caps_status_when_insufficient
test_per_account_slippage_used_in_labels

# features
test_completed_bars_only
test_no_future_or_pnl_fields_in_feature_block
test_causal_percentile_excludes_current_and_future
test_prefix_invariance_full_equals_prefix
test_missing_critical_rejects_row
test_feature_registry_hash_matches_locked

# splits / status / storage
test_purge_removes_event_overlap
test_embargo_active_market_time
test_status_thresholds_pipeline_exploratory_candidate
test_per_account_and_combined_audit_present
test_dataset_manifest_hashes_all_inputs_and_outputs
test_raw_artifacts_gitignored_but_hashed
```
All assert real content/behavior (mutation-tested, no always-pass stubs) per master-plan rule.

---

## 15. Acceptance criteria (C02 done)

```text
[ ] Exporter runs read-only, demo+login+terminal verified, fail-closed proven by test.
[ ] No MetaTrader5 import in any Stage-B/training module (test-enforced).
[ ] Immutable raw bundles exist per available account with SHA256 manifests + coverage reports.
[ ] Normalized dataset has the full §5 schema incl. four time fields, source hashes, market_setup_group_id.
[ ] A1/A2/A3 merged with account-as-metadata; cross-account dedup + group integrity verified.
[ ] Labels built from all would-signals; tick/OHLC ambiguity + maturity handled; per-account slippage P50/P95.
[ ] Features causal, registry-aligned, prefix-invariant; missingness policy enforced.
[ ] Per-account + combined dataset_status computed and reported (no training performed).
[ ] All §14 tests pass; leakage audit PASS.
[ ] A3 paused, profit-lock DRY_RUN_DISARMED, zero broker-write surface — unchanged.
[ ] Dataset + manifests committed (small) / raw ignored-but-hashed; build reproducible from manifest.
```

---

## 16. Sequencing (sub-commits)

```text
C02a  Read-only export core: mt5_readonly.py + verify_terminal.py + safety tests (no data yet).
C02b  Per-account exporter + manifest; produce A3 bundle first; coverage report.       [resolve D1–D3]
C02c  Builder skeleton: snapshot_loader + timebase + schema; UTC normalization tests.
C02d  Identity + grouping: signal_id + fuzzy_dedup + market_setup_group_id; grouping audit.
C02e  Labels + per-account slippage; label/ambiguity/maturity audits.
C02f  Features + causal percentiles + regime; feature audit + prefix-invariance.
C02g  dataset_builder + per-account/combined status + leakage audit + dataset manifest;
      extend generate_a3_ml_c01_pipeline.py to multi-account inputs; BUILD_REPORT + verdict.
```

Each sub-commit is one task, tests green, A3 paused. After C02g, C03 (splits/power) and later training commits consume the dataset. No model is trained, and no live or broker action is authorized by this plan.
```
