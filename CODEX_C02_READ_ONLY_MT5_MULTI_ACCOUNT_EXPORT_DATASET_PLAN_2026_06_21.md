# CODEX IMPLEMENTATION PLAN
## C02 — Read-Only MT5 Multi-Account Data Export and Dataset Builder

**Project:** `maksoftwares/algo-trading-system`  
**Date:** 2026-06-21  
**Stage:** C02  
**Accounts:**  
- A1 — `1025742`
- A2 — `1033030`
- A3 — `1033669`

**Symbol:** `XAUUSD` only  
**Base ML family:** `breakout_retest`  
**Mode:** Read-only export, offline normalization, dataset staging, and audit  
**Broker action:** Prohibited  
**Model training in C02:** Prohibited  
**Live/demo execution changes:** Prohibited  
**Status on completion:** One of `PASS`, `PARTIAL_EXPORT`, or `FAIL_CLOSED`

---

# 0. Codex instruction

Read this document completely before changing files.

Reuse the existing C00 contracts and C01 bootstrap. Do not build a second competing account registry, dataset status enum, schema package, or manifest convention when C01 already provides one.

C02 exists to solve the current problem:

```text
C01 supports A1/A2/A3 account scopes
but the normalized discovery data currently has usable rows only for A3.
```

C02 must export and normalize all data that is already available in the three MT5 terminals, without changing their state.

Do not train a model in C02.

Do not place, check, modify, or close any broker order.

Do not attach an EA.

Do not alter a chart, profile, preset, Market Watch selection, login, terminal setting, or terminal process state.

---

# 1. Executive verdict and boundary

```text
Read-only A1/A2/A3 export:                 GO
Offline dataset normalization:             GO
Diagnostic virtual labels:                 GO
Final trainable dataset promotion:         C03 gate
Model training in C02:                     NO-GO
Random train/test split:                   PROHIBITED
Python broker-write API:                   PROHIBITED
MT5 login/account switching:               PROHIBITED
Terminal auto-launch by exporter:          PROHIBITED
Symbol selection / Market Watch mutation:  PROHIBITED
A3 runtime or profile change:              PROHIBITED
Live trading authorization:                ABSOLUTE NO-GO
```

C02 should produce:

1. immutable raw snapshots from A1, A2, and A3;
2. normalized source tables;
3. one account-neutral signal/setup staging layer;
4. preliminary tick-based outcome labels and slippage readiness;
5. a complete coverage and leakage audit;
6. an honest dataset status;
7. no trained model.

The master program requires C02 to inventory signals, bars, ticks, spreads, fills, position paths, directions, sessions, and regimes before any model work. The contracts also require all would-signals—not merely executed trades—to form the ML signal universe.

---

# 2. Account registry

Create or extend:

```text
config/ml/mt5_accounts.yaml
```

Do not store passwords.

Suggested schema:

```yaml
schema_version: mt5_multi_account_registry_v1

common:
  symbol: XAUUSD
  expected_server_regex: "^Capital\\.ComMena-Demo$"
  require_demo_trade_mode: true
  require_existing_terminal_process: true
  allow_mt5_login_call: false
  allow_symbol_select_call: false
  export_timezone: UTC
  snapshot_safety_lag_minutes: 5

accounts:
  A1:
    account_scope: A1
    account_label: A1_FLOW_CONTROL
    expected_login: 1025742
    terminal_exe: "C:/Program Files/MetaTrader 5/terminal64.exe"
    expected_data_path: null
    portable: false
    role: control_baseline
    symbol: XAUUSD
    files_roots: []
    log_catalog: "config/ml/log_catalog_a1.yaml"

  A2:
    account_scope: A2
    account_label: A2_EDGE
    expected_login: 1033030
    terminal_exe: "C:/MT5PortableTier1BestEA/terminal64.exe"
    expected_data_path: "C:/MT5PortableTier1BestEA"
    portable: true
    role: clean_breakout_edge
    symbol: XAUUSD
    files_roots:
      - "C:/MT5PortableTier1BestEA/MQL5/Files"
    log_catalog: "config/ml/log_catalog_a2.yaml"

  A3:
    account_scope: A3
    account_label: A3_REPAIR
    expected_login: 1033669
    terminal_exe: "C:/MT5PortableRepairLane/terminal64.exe"
    expected_data_path: "C:/MT5PortableRepairLane"
    portable: true
    role: repair_research
    symbol: XAUUSD
    files_roots:
      - "C:/MT5PortableRepairLane/MQL5/Files"
    log_catalog: "config/ml/log_catalog_a3.yaml"
```

The paths above are seed values, not authority.

At runtime, the exporter must verify the exact executable path, terminal data path, login, server, and symbol. A mismatch must fail closed.

For A1, Codex should populate the validated data path from the existing local status/agent configuration rather than hardcode a MetaQuotes profile hash.

---

# 3. Read-only safety architecture

## 3.1 One account per isolated worker process

The MetaTrader5 Python module exposes a process-global connection to a terminal.

Use:

```text
one controller process
three isolated worker subprocesses
one worker per terminal/account
```

The controller must not import `MetaTrader5`.

Each worker:

1. loads only its account registry entry;
2. verifies the expected terminal process already exists;
3. connects to the exact terminal path;
4. verifies account and terminal identity;
5. exports read-only data;
6. calls `mt5.shutdown()` to close only the Python API connection;
7. exits.

Do not switch accounts within a worker.

Do not call `mt5.login()`.

## 3.2 Explicit MT5 API allowlist

Create:

```text
ml/a3_meta_v1/mt5_readonly.py
```

Only this module may import `MetaTrader5`.

Allowed calls:

```text
initialize
shutdown
version
last_error
account_info
terminal_info
symbols_get
symbol_info
symbol_info_tick
copy_rates_range
copy_ticks_range
history_orders_get
history_deals_get
positions_get
orders_get
```

Prohibited calls include, but are not limited to:

```text
login
order_send
order_check
symbol_select
market_book_add
market_book_release
```

The exporter should not expose the raw `MetaTrader5` module to other packages.

Use a narrow `ReadOnlyMT5Client` interface.

## 3.3 Prevent terminal auto-launch

`mt5.initialize(path=...)` may launch a terminal if one is not running.

C02 must prevent that behavior.

Before calling `initialize`:

1. resolve the configured executable path;
2. enumerate running processes;
3. require a process whose executable path exactly matches;
4. record matching PID(s);
5. if no process exists, abort with:

```text
TERMINAL_NOT_ALREADY_RUNNING
```

After `initialize`:

1. enumerate matching PIDs again;
2. require the same PID set;
3. if a new process appeared, disconnect and fail:

```text
UNEXPECTED_TERMINAL_LAUNCH
```

The exporter must never start or stop a terminal.

## 3.4 File-system read-only rule

The worker may read from:

```text
terminal executable metadata
terminal MQL5/Files
configured observer/path log roots
```

It may write only under the project-controlled C02 snapshot directory.

It must never write into:

```text
MQL5/Files
MQL5/Profiles
MQL5/Presets
MQL5/Experts
MQL5/Include
terminal config directories
```

## 3.5 Static and runtime safety tests

Add an AST-based test that fails if exporter modules reference a non-allowlisted `mt5.*` call.

Add source-text checks for:

```text
order_send
order_check
login(
symbol_select
TRADE_ACTION_
CTrade
OrderSend
PositionModify
PositionClose
```

The tests must scan all C02 Python modules and scripts.

Also record before/after:

```text
account login
server
terminal path
terminal data path
position ticket set
pending-order ticket set
```

For A3, any position/order difference is a hard failure because A3 is paused.

For A1/A2, existing EAs may act while export runs. Record such drift as:

```text
EXTERNAL_RUNTIME_ACTIVITY_OBSERVED
```

Do not claim the exporter caused it. All export queries must use one fixed historical cutoff, so concurrent activity after the cutoff does not alter the snapshot.

---

# 4. Account and terminal verification

Before data extraction, require all checks:

```text
terminal executable exists
terminal process already running
initialize(path=exact_path, portable=config_value) succeeds
terminal_info is not None
account_info is not None
account login equals expected login
server matches expected demo regex
trade mode is demo
terminal_info.path matches expected terminal root
terminal_info.data_path matches expected data path when configured
terminal connected is true
XAUUSD symbol_info exists
XAUUSD is already visible/available
symbol point > 0
symbol digits is valid
```

Do not call `symbol_select` if XAUUSD is hidden.

Fail:

```text
SYMBOL_NOT_ALREADY_AVAILABLE
```

Record terminal/account metadata, but redact:

```text
account holder name
passwords
tokens
personal filesystem username where possible
```

Account login may remain because it is the project account identifier.

---

# 5. Common export cutoff and time rules

## 5.1 One cutoff for all accounts

The controller establishes:

```text
export_started_utc
snapshot_cutoff_utc =
  floor(export_started_utc - safety_lag_minutes, minute)
```

Default safety lag:

```text
5 minutes
```

The same cutoff applies to A1, A2, and A3.

No row after this cutoff enters the immutable snapshot.

## 5.2 UTC only

All MT5 API request datetimes must be timezone-aware UTC.

Store:

```text
time_utc
time_msc
```

Do not treat local Python time or broker display time as UTC.

Store broker/server timestamps from log files separately:

```text
timestamp_broker_raw
timestamp_broker_parsed
timestamp_utc
timestamp_dubai
timezone_conversion_status
```

## 5.3 Completed bars only

Export raw bars through the cutoff, but normalized feature bars must satisfy:

```text
bar is fully completed before snapshot_cutoff_utc
```

Do not use the currently forming M5/M15/H1/H4/D1 bar.

## 5.4 Requested start

Require a controller argument:

```text
--requested-start-utc
```

C02 must report:

```text
requested start
actual earliest bar per account/timeframe
actual earliest tick per account
actual earliest signal log row
actual earliest order/deal
coverage shortfall
```

Do not silently claim full coverage.

---

# 6. Data export matrix

For each account, export the following.

## 6.1 Bars

Timeframes:

```text
M5
M15
H1
H4
D1
```

MT5 fields:

```text
time
open
high
low
close
tick_volume
spread
real_volume
```

Normalized additions:

```text
snapshot_id
dataset_version
account_scope
account_label
account_login
server
symbol
timeframe
bar_open_utc
bar_close_utc
is_complete
point
digits
source_file_sha256
export_cutoff_utc
```

Export direct MT5 bars for all timeframes.

Also create a parity report comparing direct M15/H1/H4/D1 with bars reconstructed from M5 using the observed terminal bar boundaries.

Do not automatically replace direct higher-timeframe bars in C02.

C03 must decide the canonical feature source after parity is known.

Important audit:

```text
MT5 bar history can be limited by the terminal’s available chart history
and Max bars setting.
```

C02 may not mutate that setting.

Mark short coverage:

```text
BAR_HISTORY_TRUNCATED_OR_UNAVAILABLE
```

## 6.2 Ticks

Use:

```text
COPY_TICKS_ALL
```

Export in daily chunks by default.

Raw/normalized fields:

```text
snapshot_id
account_scope
symbol
time_utc
time_msc
bid
ask
last
volume
volume_real
flags
spread_price
spread_points
point
source_chunk_sha256
```

Chunk rules:

```text
one UTC day per request
retry transient failures
never silently skip a failed day
write each successful day atomically
```

Deduplicate exact ticks using:

```text
account_scope
symbol
time_msc
bid
ask
last
flags
```

Do not drop repeated timestamps with different prices or flags.

For large history, support two modes:

```text
continuous discovery-window ticks
union-of-signal-label-window ticks
```

The first C02 run should export the full available discovery window for XAUUSD if storage permits.

## 6.3 Observer and would-signal logs

Create explicit per-account log catalogs.

Each catalog entry defines:

```text
logical source name
glob/path
source type
schema version
candidate/family mapping
timestamp columns
signal columns
whether file is append-active
```

Potential source types:

```text
observer_signal_log
experimental_executor_signal_log
tier1_signal_log
A3 plain/improved/compat signal log
trend-guarded observer log
shadow-fix observer log
position-path summary
```

Do not use one unbounded wildcard over all CSVs.

Preserve exact raw bytes.

For actively appended files, use a stable-copy loop:

1. record source size/mtime;
2. copy to a temporary snapshot file;
3. record source size/mtime again;
4. retry if changed;
5. after bounded retries, mark:

```text
VOLATILE_SOURCE_SNAPSHOT
```

Normalize only rows at or before the common cutoff.

## 6.4 Executed trade history

Export all XAUUSD-relevant historical orders and deals over the requested interval.

Orders should preserve every namedtuple field, including when available:

```text
ticket
time_setup
time_setup_msc
time_done
time_done_msc
type
state
time_expiration
type_filling
type_time
magic
position_id
position_by_id
reason
volume_initial
volume_current
price_open
sl
tp
price_current
price_stoplimit
symbol
comment
external_id
```

Deals should preserve every namedtuple field, including when available:

```text
ticket
order
time
time_msc
type
entry
magic
position_id
reason
volume
price
commission
swap
profit
fee
symbol
comment
external_id
```

Export current positions and current pending orders only as an audit snapshot, not as training rows.

## 6.5 Spreads

Create spread observations from three sources:

```text
tick-derived ask - bid
existing passive spread logger files
bar spread field
```

Primary spread source for signal/label work:

```text
tick-derived spread
```

Store:

```text
spread_price
spread_points
spread_R when a valid signal risk exists
spread_source
```

Use logger/bar spread as parity and fallback diagnostics, not silent replacement.

## 6.6 Fills and slippage

Build a raw fill-reconciliation table by joining:

```text
runtime order logs
MT5 history orders
MT5 history deals
```

Preferred requested-price source order:

```text
1. runtime order log request_price / actual_request_price
2. historical order price_open when semantics are validated
3. unresolved
```

Actual fill:

```text
matching deal price
```

Store:

```text
account_scope
order_ticket
deal_ticket
position_id
magic
candidate
direction
request_time_utc
deal_time_utc
request_price
actual_fill_price
slippage_points_signed
slippage_points_adverse
spread_at_request_points
source_quality
join_status
```

Do not invent requested prices from nearby quotes.

If unavailable:

```text
SLIPPAGE_REQUEST_PRICE_UNRESOLVED
```

## 6.7 Position-path snapshots

Read configured position-path observer files.

Preserve:

```text
timestamp
account
symbol
ticket
position_id
magic
candidate
direction
volume
open price
current bid/ask
SL
TP
profit
initial risk
current R
MFE
MAE
event type
source row
```

If the raw file does not contain MFE/MAE, do not backfill them as source fields. Compute them later and distinguish:

```text
source_MFE
derived_MFE
```

## 6.8 Terminal/account/symbol metadata

Export:

```text
MetaTrader5 Python package version
terminal version/build
terminal executable path
terminal data path
terminal common-data path
terminal maxbars
connected status
trade_allowed status as observed
account login
account server
account company
account currency
trade mode
leverage
margin mode
symbol digits
symbol point
tick size
tick value
contract size
volume min/max/step
stops level
freeze level
filling mode
latest tick time
```

Do not use balance/equity as model features.

If stored in private raw metadata, mark them audit-only.

---

# 7. Raw snapshot layout

Create immutable snapshots outside Git-tracked data.

Suggested root:

```text
data/ml/a3_meta_v1/c02/
```

Dataset version:

```text
xauusd_c02_multiacct_<UTCSTAMP>_g<GITSHA8>_c<CONTRACTSHA8>
```

Layout:

```text
data/ml/a3_meta_v1/c02/<dataset_version>/
  raw/
    A1/
      metadata/
      bars/
      ticks/
      history/
      logs/
      audit/
    A2/
      ...
    A3/
      ...

  normalized/
    account_metadata/
    source_files/
    symbols/
    bars/
    ticks/
    signals/
    orders/
    deals/
    fills/
    spreads/
    position_paths/

  staging/
    signal_instances/
    exact_market_signals/
    setup_groups/
    setup_account_labels/
    model_rows/

  manifests/
    RAW_SNAPSHOT_MANIFEST.json
    NORMALIZED_SNAPSHOT_MANIFEST.json
    DATASET_MANIFEST.json

  reports/
    ...
```

Use Parquet with Zstandard compression for normalized tables.

Preserve raw CSV/log snapshots in original format.

Every write must be:

```text
temporary file
fsync/close
hash
atomic rename
```

Never modify a completed snapshot.

A rerun creates a new version.

---

# 8. Source-file manifest

For every exported/copied source record:

```text
snapshot_id
dataset_version
account_scope
source_kind
logical_source_name
original_path
snapshot_relative_path
source_size_before
source_size_after
source_mtime_before_utc
source_mtime_after_utc
stable_copy_status
sha256
row_count
min_time_utc
max_time_utc
parser_name
parser_version
schema_version
export_status
error_code
```

Root manifest:

```text
manifest_schema_version
dataset_version
source_commit
contract_manifest_hash
export_started_utc
snapshot_cutoff_utc
requested_start_utc
accounts_requested
accounts_completed
overall_status
file_count
total_bytes
root_manifest_sha256
```

Do not place passwords, account-holder names, or authorization tokens in manifests.

---

# 9. Normalized relational tables

Do not force all data into one giant table.

## 9.1 `account_metadata`

One row per account snapshot.

Key:

```text
snapshot_id + account_scope
```

## 9.2 `bars`

Key:

```text
snapshot_id + account_scope + symbol + timeframe + bar_open_utc
```

## 9.3 `ticks`

Key:

```text
snapshot_id + account_scope + symbol + time_msc + bid + ask + last + flags
```

## 9.4 `signal_instances`

One row per source signal row.

Required fields:

```text
dataset_version
snapshot_id
account_scope
account_label
account_login
server
terminal_id
symbol
candidate
family
lane
magic
run_id
signal_schema_version
source_signal_file_sha256
source_signal_row_number
source_signal_instance_id
decision_time_utc
feature_time_utc
entry_eligible_from_utc
direction
would_signal
stage
reason_code
level_kind
level_price
planned_entry
planned_sl
planned_tp
planned_stop_points
break_bar_time_utc
retest_bar_time_utc
confirmation_bar_time_utc
break_shift
retest_shift
confirmation_shift
timestamp_quality
schema_mapping_status
```

## 9.5 `exact_market_signals`

Account-neutral exact signal identity.

Required identity components:

```text
symbol
family
direction
level_kind
normalized_level_price
break_bar_time_utc
retest_bar_time_utc
confirmation_bar_time_utc
```

Store:

```text
market_signal_id
instance_count
account_count
account_scopes
lane_count
source_instance_ids
```

`market_signal_id` must not include account.

Keep an account-specific `source_signal_instance_id` separately.

## 9.6 `setup_groups`

Fuzzy grouping is account-neutral.

Store:

```text
setup_group_id
market_signal_ids
canonical_signal_id
group_start_utc
group_end_utc
direction
symbol
family
canonical_level
group_span_minutes
account_scopes
source_instance_count
grouping_contract_hash
grouping_status
```

The same setup seen on A1, A2, and A3 is one group.

## 9.7 `setup_account_labels`

One row per:

```text
setup_group_id × account tick source
```

Store:

```text
account_scope_label_source
tick_coverage_status
entry_time_utc
entry_price
sl
tp
label_end_time_utc
label_status
y_outcome
y_net_R_expected
y_net_R_p95_stress
MFE_R
MAE_R
slippage_source
slippage_model_hash
```

## 9.8 `model_rows`

One row per account-neutral `setup_group_id`.

Required identifiers/audit fields:

```text
dataset_version
snapshot_id
account_scope_canonical_source
account_label_canonical_source
symbol
candidate_canonical
family
signal_id
market_signal_id
setup_group_id
decision_time_utc
feature_time_utc
entry_eligible_from_utc
label_end_time_utc
direction
source_signal_file_sha256
bar_source_manifest_sha256
tick_source_manifest_sha256
contract_manifest_hash
feature_registry_hash
grouping_contract_hash
label_contract_hash
slippage_model_hash
feature_ready
label_ready
label_mature
trainable_status
bar_coverage_status
tick_coverage_status
timezone_status
schema_status
leakage_status
label_source_count
label_sign_agreement
account_feed_dispersion_R
unresolved_reason
```

Append only the locked feature-registry fields.

Do not include account scope/label as model features.

---

# 10. Canonical row and cross-account label policy

## 10.1 Canonical signal instance

Choose a canonical source instance without using outcomes.

Pre-registered quality order:

```text
1. complete required signal fields
2. millisecond/second timestamp quality
3. completed-bar references available
4. complete bar warm-up
5. complete tick label window
6. fixed account priority from registry as final tie-break
```

The fixed account priority must be recorded before dataset results are viewed.

Suggested tie-break only:

```text
A2
A3
A1
```

This is not a model feature.

## 10.2 Cross-account virtual labels

For every setup group, attempt the same virtual execution on each account’s XAUUSD tick feed.

Store all account labels.

Combined label rules:

```text
if >=2 complete account labels and outcome signs agree:
    combined net R = median of account net R values
    trainable label may be produced

if >=2 complete account labels and signs disagree:
    label_status = ACCOUNT_FEED_DISAGREEMENT
    exclude from supervised training

if only 1 complete account label:
    label_status = SINGLE_ACCOUNT_LABEL
    usable for PIPELINE_ONLY / EXPLORATORY diagnostics
    report separately

if no complete labels:
    unresolved
```

Do not count the same setup three times merely because three accounts saw it.

Report multi-source label coverage.

Do not add a new candidate-status threshold without updating the locked contract; expose the coverage for review.

## 10.3 Per-account diagnostics

All combined results must also report:

```text
A1-only
A2-only
A3-only
combined account-neutral
```

The model is pooled and account-neutral.

Account fields are metadata only.

---

# 11. Signal source hierarchy

A raw would-signal source is preferred.

Status hierarchy:

```text
OBSERVER_LOG
EXECUTOR_SIGNAL_LOG
OFFLINE_RECONSTRUCTION_PARITY_APPROVED
EXECUTED_TRADE_ONLY
NO_SIGNAL_SOURCE
```

Rules:

- `OBSERVER_LOG` and complete `EXECUTOR_SIGNAL_LOG` can enter the staging universe.
- `OFFLINE_RECONSTRUCTION_PARITY_APPROVED` is allowed only after an independent replay matches logged signals:
  - at least 99% overall decision parity;
  - 100% parity on would-signal rows;
  - no unresolved timestamp/lookahead mismatch.
- `EXECUTED_TRADE_ONLY` cannot define the raw signal universe.
- An account with bars/ticks/history but no signal logs is still a successful market/execution export, but contributes no raw signal rows until reconstruction passes parity.

This prevents selection bias.

---

# 12. Label-building approach

C02 may build diagnostic labels, but official trainable-dataset promotion remains a C03 gate.

## 12.1 Entry

Use the locked execution-label contract:

```text
decision from completed bars
LONG entry at first fresh ask after decision
SHORT entry at first fresh bid after decision
entry expires at close of next M5 bar
```

No fresh tick:

```text
CANCELLED_NO_FRESH_TICK
```

## 12.2 Risk/target

```text
risk = max(
  raw signal risk,
  broker stops level + 5 points,
  3 × spread at fill,
  300 XAU points
)

TP = 1.50R
```

## 12.3 Exit quote side

```text
LONG exits on bid
SHORT exits on ask
```

## 12.4 Maturity

A label is mature when:

```text
TP resolved
or SL resolved
or 288 active M5 bars completed and timeout resolved
```

Signals too near the export cutoff:

```text
NOT_MATURE
```

Do not force a timeout at the snapshot cutoff.

## 12.5 Status values

```text
TP
SL
TIMEOUT_POSITIVE
TIMEOUT_NEGATIVE
TIMEOUT_FLAT
CANCELLED_NO_FRESH_TICK
NOT_MATURE
DATA_UNRESOLVED_TIMEOUT
EXECUTION_AMBIGUITY
TICK_COVERAGE_INCOMPLETE
ACCOUNT_FEED_DISAGREEMENT
DATA_UNRESOLVED
```

## 12.6 Tick versus OHLC

Candidate labels require tick data.

OHLC replay may produce:

```text
DIAGNOSTIC_BAR_LABEL
```

It must never be mixed with tick labels as if equivalent.

If an M5 bar touches both SL and TP and tick ordering is absent:

```text
EXECUTION_AMBIGUITY
```

Exclude from supervised training.

## 12.7 Label audit fields

```text
decision_time
first_eligible_tick_time
entry_time
entry_quote_side
entry_price
risk_price
SL
TP
first_SL_cross_time
first_TP_cross_time
timeout_time
exit_time
exit_price
active_M5_bars_held
MFE_R
MAE_R
label_mature
label_status
label_engine_version
```

---

# 13. Slippage readiness in C02

C02 exports and reconstructs raw fill/slippage observations.

It may generate a preliminary P50/P95 readiness report.

Do not declare the final slippage model until the locked C03 implementation validates it.

Report per account and pooled:

```text
entry fill count
SL exit count
TP exit count
timeout/market exit count
P50 adverse slippage
P95 adverse slippage
session buckets
spread terciles
unresolved joins
```

Fallback analysis hierarchy:

```text
account + session + spread bucket
account global
pooled server + session + spread bucket
pooled server global
insufficient
```

Do not pool silently.

Candidate readiness minima remain:

```text
entry >= 200
SL exits >= 100
TP exits >= 50
```

If insufficient:

```text
slippage_status = INSUFFICIENT
dataset cannot exceed EXPLORATORY_MODEL
```

Fold-causal slippage fitting is implemented in C03/C04, not finalized from the full C02 dataset.

---

# 14. Feature-building approach

C02 should produce feature-ready staging, not fit a model.

## 14.1 Completed bars only

Every feature row must satisfy:

```text
all source bars completed before decision_time_utc
```

Do not reference current bar zero unless the contract explicitly defines it as completed—which it does not.

## 14.2 Causal windows

Rolling values must use only rows strictly before the decision.

Examples:

```text
ATR
EMA slopes
trailing volatility percentile
trailing session spread percentile
range compression
tick-volume ratio
```

The current row must not enter its own percentile reference distribution.

## 14.3 Registry alignment

Use only fields from:

```text
A3_ML_FEATURE_REGISTRY_V1.csv
```

C02 must report:

```text
registry field present
formula implemented
unit
timeframe
warm-up status
missingness rate
causal audit status
```

Do not create new model features in C02.

## 14.4 Forbidden feature sources

Never use:

```text
future PnL
MFE
MAE
exit reason
outcome
future spread
future slippage
post-signal balance
post-signal daily loss
account label
account login
lane
magic
duplicate count
```

These may remain metadata/audit columns.

## 14.5 Missingness

Critical missing feature:

```text
ABSTAIN / FEATURE_INCOMPLETE
```

Do not impute zero.

C02 reports missingness only.

Training-only imputation is later and must be fit inside each training fold.

## 14.6 Prefix invariance

Required test:

```text
build features with full snapshot
build with future rows removed after T
all feature values at or before T must match
```

---

# 15. Merge and leakage prevention

## 15.1 Account fields are metadata only

Block these from the model feature matrix:

```text
account_scope
account_label
account_login
terminal_id
server
magic
lane
run_id
```

## 15.2 Group integrity

All instances of the same account-neutral setup group must stay in one split.

Never allow:

```text
A1 instance in train
A2 version of same setup in test
```

## 15.3 Chronological validation only

No random split.

Future C04 uses:

```text
5 outer expanding folds
3 inner expanding folds
purging
embargo
disjoint calibration tail
```

C02 should already produce:

```text
event_start = decision_time_utc
event_end = label_end_time_utc
setup_group_id
```

## 15.4 Embargo readiness

The locked holding horizon is 288 active M5 bars.

C02 must retain enough timing fields for active-market purge/embargo calculations.

## 15.5 Cross-account diagnostics

Report account distributions for:

```text
signal count
label status
direction
session
regime
spread
cost_R
outcome
feature missingness
```

A combined result that is carried entirely by one account must be clearly visible.

---

# 16. Storage and versioning

## 16.1 Immutable version name

```text
xauusd_c02_multiacct_<UTCSTAMP>_g<GITSHA8>_c<CONTRACTSHA8>
```

## 16.2 Dataset manifest

Required:

```text
dataset_version
source_commit
contract_manifest_hash
account registry hash
log catalog hashes
snapshot cutoff
requested start
account export statuses
source file hashes
normalized table hashes
row counts
time coverage
schema hashes
root manifest hash
```

## 16.3 What to commit

Commit:

```text
scripts
modules
schemas
configs without secrets
log catalog templates
contract-compatible fixtures
tests
small synthetic test data
manifests
coverage/audit reports
dataset summary
```

## 16.4 What to ignore

Git-ignore:

```text
raw tick files
raw bar/history dumps
copied runtime logs
full normalized Parquet tables
full model staging tables
account metadata containing private local paths
credentials
terminal databases
EX5 files unless existing policy explicitly allows
```

Add a committed pointer:

```text
C02_DATASET_POINTER.json
```

It may contain:

```text
dataset_version
private storage root alias
root manifest SHA256
row counts
coverage dates
no raw path with personal username
```

---

# 17. Proposed modules and scripts

Reuse C01 packages where equivalent.

Add or extend:

```text
ml/a3_meta_v1/
  account_registry.py
  mt5_readonly.py
  mt5_worker.py
  export_controller.py
  source_snapshot.py
  source_manifest.py
  log_catalog.py
  log_adapters.py
  bars_normalizer.py
  ticks_normalizer.py
  history_normalizer.py
  signal_normalizer.py
  fill_reconciliation.py
  position_path_normalizer.py
  cross_account_audit.py
  staging_builder.py
  coverage.py
  time_utils.py
```

Scripts:

```text
scripts/c02_verify_mt5_accounts.py
scripts/c02_export_mt5_account_worker.py
scripts/c02_export_mt5_multi_account.py
scripts/c02_snapshot_runtime_logs.py
scripts/c02_normalize_snapshots.py
scripts/c02_build_signal_staging.py
scripts/c02_build_diagnostic_labels.py
scripts/c02_audit_multi_account_dataset.py
scripts/c02_verify_read_only_boundary.py
scripts/c02_generate_reports.py
scripts/c02_verify_dataset_manifest.py
```

Do not duplicate C01 schema/status classes.

---

# 18. Suggested CLI

## Account verification

```text
python scripts/c02_verify_mt5_accounts.py \
  --registry config/ml/mt5_accounts.yaml \
  --output outputs/ml/a3_meta_v1/reports/C02_ACCOUNT_VERIFICATION.json
```

## Multi-account export

```text
python scripts/c02_export_mt5_multi_account.py \
  --registry config/ml/mt5_accounts.yaml \
  --requested-start-utc 2026-06-01T00:00:00Z \
  --output-root data/ml/a3_meta_v1/c02 \
  --require-accounts A1,A2,A3
```

## Normalize

```text
python scripts/c02_normalize_snapshots.py \
  --dataset-version <version> \
  --output-root data/ml/a3_meta_v1/c02
```

## Build staging

```text
python scripts/c02_build_signal_staging.py \
  --dataset-version <version> \
  --contracts outputs/manifests/A3_ML_V1_LOCK_MANIFEST.json
```

## Diagnostic labels

```text
python scripts/c02_build_diagnostic_labels.py \
  --dataset-version <version> \
  --tick-labels-only \
  --no-training
```

## Audit

```text
python scripts/c02_audit_multi_account_dataset.py \
  --dataset-version <version> \
  --fail-on-leakage \
  --fail-on-account-mismatch
```

---

# 19. Required reports

Generate Markdown and JSON where practical.

```text
C02_ACCOUNT_VERIFICATION_MATRIX
C02_READ_ONLY_BOUNDARY_AUDIT
C02_SOURCE_INVENTORY
C02_RAW_SNAPSHOT_MANIFEST
C02_BAR_COVERAGE_REPORT
C02_BAR_TIMEFRAME_PARITY_REPORT
C02_TICK_COVERAGE_REPORT
C02_SIGNAL_LOG_SCHEMA_REPORT
C02_SIGNAL_SOURCE_COVERAGE_REPORT
C02_TRADE_HISTORY_RECONCILIATION
C02_FILL_SLIPPAGE_READINESS
C02_POSITION_PATH_COVERAGE_REPORT
C02_TIMEZONE_ALIGNMENT_REPORT
C02_CROSS_ACCOUNT_MARKET_DATA_DIVERGENCE
C02_EXACT_AND_FUZZY_DUPLICATE_AUDIT
C02_NORMALIZATION_AUDIT
C02_LABEL_MATURITY_REPORT
C02_MULTI_ACCOUNT_LABEL_CONSENSUS_REPORT
C02_FEATURE_READINESS_REPORT
C02_DATASET_STATUS_REPORT
C02_DATASET_MANIFEST
C02_FINAL_VERDICT
```

`C02_FINAL_VERDICT` must state:

```text
account export status
usable signal rows by account
usable setup groups
tick-label coverage
slippage readiness
dataset classification
training authorized = false
next allowed stage
```

---

# 20. Tests

## 20.1 Read-only safety

```text
test_only_allowlisted_mt5_methods_are_used
test_mt5_login_is_forbidden
test_order_send_is_forbidden
test_symbol_select_is_forbidden
test_terminal_must_already_be_running
test_initialize_cannot_create_new_pid
test_worker_writes_only_under_snapshot_root
test_no_terminal_profile_or_files_write
```

## 20.2 Account verification

```text
test_login_mismatch_fails
test_server_mismatch_fails
test_live_trade_mode_fails
test_terminal_path_mismatch_fails
test_data_path_mismatch_fails
test_symbol_unavailable_fails
test_A1_A2_A3_registry_unique_logins
```

## 20.3 Time

```text
test_all_api_requests_are_utc_aware
test_incomplete_bars_are_dropped
test_broker_time_conversion_is_explicit
test_Dubai_time_is_UTC_plus_4
test_common_cutoff_is_identical_across_accounts
```

## 20.4 Snapshot/manifests

```text
test_active_log_stable_copy_retry
test_snapshot_is_immutable
test_atomic_write
test_every_file_has_sha256
test_root_manifest_hash_verifies
test_rerun_creates_new_version
```

## 20.5 Bars/ticks

```text
test_bar_schema
test_tick_schema
test_tick_exact_dedup
test_same_timestamp_different_quotes_preserved
test_tick_spread_calculation
test_history_truncation_is_reported
test_daily_tick_chunk_failure_not_silently_skipped
```

## 20.6 Logs/signals

```text
test_each_catalog_source_has_explicit_adapter
test_unknown_signal_schema_is_quarantined
test_signal_source_row_traceability
test_executed_trades_not_used_as_raw_signal_proxy
test_account_neutral_market_signal_id
```

## 20.7 Cross-account grouping

```text
test_same_setup_across_A1_A2_A3_forms_one_group
test_account_fields_not_in_feature_registry
test_group_does_not_cross_split
test_conflicting_account_labels_marked_unresolved
test_single_account_label_is_flagged
```

## 20.8 Labels

```text
test_long_ask_entry_bid_exit
test_short_bid_entry_ask_exit
test_entry_expiry
test_TP
test_SL
test_288_active_bar_timeout
test_not_mature_near_cutoff
test_tick_ambiguity_blocks_trainable_label
test_OHLC_label_is_diagnostic_only
test_spread_not_double_counted
```

## 20.9 Features/leakage

```text
test_completed_bars_only
test_feature_time_not_after_decision
test_no_future_PnL_fields
test_prefix_invariance
test_rolling_percentile_excludes_current_row
test_missing_critical_feature_blocks_readiness
```

## 20.10 C01 integration

```text
test_C01_ingests_A1_A2_A3_account_scopes
test_dataset_status_is_based_on_setup_groups
test_PIPELINE_ONLY_is_not_auto_promoted
test_training_authorized_false_in_C02
```

---

# 21. C02 acceptance criteria

## 21.1 Overall `PASS`

Require:

```text
A1 verification PASS
A2 verification PASS
A3 verification PASS
no forbidden MT5 API usage
no terminal launched/stopped
no account switched
no profile/chart/preset mutation
raw snapshot manifests verify
all requested data types attempted for each account
bar/tick coverage honestly reported
observer log schemas mapped or explicitly quarantined
orders/deals/history normalized
source hashes trace every normalized row
cross-account grouping audit PASS
no leakage finding
A3 remains paused
C02 training_authorized = false
```

Accounts may legitimately have:

```text
NO_SIGNAL_SOURCE
NO_POSITION_PATH_SOURCE
INSUFFICIENT_SLIPPAGE
```

Those conditions do not falsify the read-only export, but they reduce dataset status.

## 21.2 `PARTIAL_EXPORT`

Use when:

```text
one account cannot be verified/exported
or a required data class is unavailable
or tick coverage is partial
or signal logs are unavailable on A1/A2
```

Requirements:

```text
available data is still immutable and audited
missing scope is explicit
combined model training remains blocked
```

Do not silently call this PASS.

## 21.3 `FAIL_CLOSED`

Use when any applies:

```text
account/login/server mismatch
terminal auto-launch detected
write-capable MT5 API found
terminal/profile write attempted
source manifest mismatch
UTC/leakage failure
unexplained account switching
A3 runtime state changed
raw snapshot corruption
```

---

# 22. Dataset classification after C02

C02 must use the locked C01 classification rules.

## `PIPELINE_ONLY`

Typical current result when:

```text
fewer than 300 usable setup groups
minority class below 90
less than 8 active weeks
only one direction/regime
slippage insufficient
feature budget below 5
```

No model training.

## `EXPLORATORY_MODEL`

Requires at least:

```text
300 labeled setup groups
90 minority outcomes
8 active weeks
both directions
at least two regimes
feature budget >= 6
```

Allows regularized logistic diagnostics only after C03/C04.

## `CANDIDATE_MODEL`

Requires at least:

```text
1000 labeled setup groups
240 minority outcomes
16 active weeks
both directions
RISING/FALLING/MIXED
feature budget >= 12
adequate slippage
```

## `MATURE_MODEL`

Requires:

```text
2000 labeled setup groups
450 minority outcomes
26 active weeks
all regimes
feature budget 16
```

C02 must not inflate counts by duplicating the same setup across accounts.

---

# 23. Training workflow after C02

Training is not allowed merely because C02 finishes.

Required order:

```text
C02 export/inventory PASS
C03 final slippage/labels/grouping PASS
C04 purged walk-forward/power infrastructure PASS
C05 deterministic benchmarks complete
C06 M0/M1 training
C07 calibration and threshold
C08 OOS verdict
```

First models:

```text
M0 base rate
M1 regularized L2 logistic
```

No tree model unless dataset status is `MATURE_MODEL`.

Validation:

```text
no random split
5 outer expanding folds
3 inner expanding folds
purge
embargo
group integrity
disjoint calibration
threshold selected without test labels
```

Shadow score output later:

```text
signal_id
setup_group_id
model_id
model_hash
feature_schema_hash
p_win_raw
p_win_calibrated
threshold
TAKE/SKIP/ABSTAIN
score_decile
drift_status
explanations
```

No broker action.

---

# 24. Offline replay and shadow comparison

## 24.1 Safe replay

Preferred replay:

```text
Python reconstruction from immutable bars/ticks/signals
```

Do not replay by attaching EAs to A1/A2/A3.

If later MQL5 parity is required:

```text
use a disposable isolated tester/observer environment
with a passive source that has no broker-action APIs
```

That is outside C02.

## 24.2 Raw versus model comparison

For every account-neutral setup group:

```text
raw strategy take = 1
model take = 1 only for TAKE
model skip/abstain return = 0
```

Compute:

```text
raw portfolio R
model portfolio R
delta R per raw signal
retention
PF
expectancy
drawdown
BAD_SIGNAL share
```

Do not calculate only on retained trades; include skipped setups as zero in paired value comparison.

## 24.3 Per-account and combined scoring

Produce:

```text
A1 label-source result
A2 label-source result
A3 label-source result
combined consensus result
```

The same model score applies to the setup group.

Do not train an account-specific model in V1.

## 24.4 Evidence before forward shadow

Require:

```text
C02 source/coverage audits PASS
C03 labels/slippage PASS
C04 no-leakage validation PASS
deterministic benchmark defined
offline parity PASS
model artifact locked
threshold locked
read-only shadow scorer safety PASS
```

---

# 25. Main risks and mitigations

## 25.1 MT5 history limitations

Risk:

```text
bars limited by terminal history / Max bars
ticks may not cover requested history
```

Mitigation:

```text
coverage report per account
no silent backfill
no terminal setting mutation
partial status when short
```

## 25.2 Timezone mistakes

Risk:

```text
Python local time
MT5 UTC
broker log time
Dubai time
```

Mitigation:

```text
UTC-aware API calls
retain raw broker timestamps
explicit conversion status
cross-check signals against M5 bar boundaries
```

## 25.3 Duplicate signals

Risk:

```text
same market setup triplicated across A1/A2/A3 or lanes
```

Mitigation:

```text
account-neutral exact ID
fuzzy setup group
one model row per setup group
group-integrity tests
```

## 25.4 Incomplete ticks

Risk:

```text
wrong SL/TP ordering
false labels
missing weekend gap behavior
```

Mitigation:

```text
tick coverage audit
candidate labels require ticks
ambiguous labels excluded
OHLC diagnostic only
```

## 25.5 Concurrent runtime activity

Risk:

```text
A1/A2 EAs place trades while export runs
```

Mitigation:

```text
common historical cutoff
read-only API allowlist
pre/post runtime audit
record external activity
never attribute concurrent drift to exporter without evidence
```

## 25.6 Account-specific execution differences

Risk:

```text
different spreads/ticks/fills across terminals
```

Mitigation:

```text
per-account labels
combined median only with sign agreement
dispersion and feed-consensus report
account not a model feature
```

## 25.7 Slippage insufficiency

Risk:

```text
too few request/fill pairs
```

Mitigation:

```text
explicit adequacy counts
no invented request price
diagnostic optimistic labels only
candidate status blocked
```

## 25.8 Observer schema drift

Risk:

```text
many evolving CSV headers
```

Mitigation:

```text
explicit adapters
source schema hash
unknown schema quarantine
row-level traceability
```

## 25.9 Overfitting from limited history

Risk:

```text
three-week discovery sample
```

Mitigation:

```text
honest dataset status
no training in C02
no final holdout claims
purged walk-forward later
new forward confirmation
```

## 25.10 Privacy and secrets

Risk:

```text
account name, local username, tokens, passwords
```

Mitigation:

```text
no credentials in config
redact account holder
private raw storage
commit only manifests/reports
secret scan before commit
```

---

# 26. Commit sequence

## C02-00 — Registry and read-only facade

Add:

```text
account registry
log catalog schema
ReadOnlyMT5Client
process/path verification
forbidden-call tests
```

No data export yet.

Report:

```text
C02_READ_ONLY_BOUNDARY_BUILD.md
```

## C02-01 — Account verification workers

Implement isolated workers for A1/A2/A3.

Output:

```text
C02_ACCOUNT_VERIFICATION_MATRIX.md/json
```

No bars/ticks yet.

## C02-02 — Bars and ticks export

Implement:

```text
all five timeframes
daily tick chunks
UTC cutoff
coverage reports
source manifests
```

No logs/history normalization yet.

## C02-03 — History and runtime log snapshots

Implement:

```text
orders
deals
positions/orders audit snapshot
observer logs
spread logs
position paths
stable file copy
```

## C02-04 — Normalized source tables

Build:

```text
accounts
sources
symbols
bars
ticks
orders
deals
spreads
position paths
```

## C02-05 — Signal normalization and cross-account grouping

Build:

```text
signal_instances
exact_market_signals
setup_groups
signal-source coverage
duplicate audit
```

No trainable model rows yet.

## C02-06 — Fill/slippage readiness and diagnostic labels

Build:

```text
fill reconciliation
slippage readiness
tick-level diagnostic labels
maturity report
per-account label rows
```

Mark official C03 promotion pending.

## C02-07 — Feature-ready staging

Build locked causal feature fields and audit.

No fitted preprocessing.

## C02-08 — Dataset manifests and C01 integration

Generate:

```text
model_rows
dataset status
C01 ingestion verification
all reports
root manifest
final verdict
```

Training remains false.

Each commit must include:

```text
scope
changed files
tests run
result
runtime boundary
next permitted task
```

---

# 27. Final C02 go/no-go

## GO to C03

Only when:

```text
C02 overall PASS
all three account verification rows PASS
read-only safety PASS
manifests verify
time/leakage audit PASS
cross-account grouping PASS
signal-source coverage honestly classified
tick-label and slippage readiness quantified
C01 ingestion supports all exported scopes
training_authorized remains false
```

## Continue data collection

Use:

```text
PARTIAL_EXPORT / PIPELINE_ONLY
```

when export is safe but evidence is insufficient.

## NO-GO

Use:

```text
FAIL_CLOSED
```

on safety, identity, mutation, UTC, leakage, or manifest failure.

---

# 28. Explicitly out of scope

```text
No model training in C02
No threshold selection
No automatic account switching
No MT5 login call
No terminal launch
No symbol selection
No Market Book subscription
No OrderSend
No CTrade
No TRADE_ACTION
No position/order modification
No chart/profile/preset mutation
No EA attachment
No A3 reactivation
No live or real capital
No final profitability claim
```

---

# 29. Codex first action

Start with `C02-00` only:

```text
1. Inspect and reuse the current C01 account/schema/bootstrap code.
2. Add the multi-account registry entries.
3. Build the strict read-only MT5 facade.
4. Add process/path/account verification.
5. Add forbidden-call tests.
6. Produce C02_READ_ONLY_BOUNDARY_BUILD.md.
7. Do not connect to MT5 until the tests pass.
8. Do not export data in this first commit.
```

After review of C02-00, proceed to C02-01.

---

# 30. Bottom line

C02 succeeds when it can truthfully say:

```text
We connected separately to A1, A2, and A3 without launching,
switching, stopping, or modifying any terminal.

We exported every available XAUUSD market, signal, execution,
spread, and path source through one common UTC cutoff.

Every raw and normalized row is traceable to an immutable
SHA256 source snapshot.

The same market setup is not counted three times merely
because three accounts observed it.

Missing ticks, logs, fills, and history remain visible as
missing evidence rather than being silently invented.

The resulting dataset has an honest PIPELINE_ONLY,
EXPLORATORY_MODEL, CANDIDATE_MODEL, or MATURE_MODEL status.

No model was trained and no trade was affected.
```
