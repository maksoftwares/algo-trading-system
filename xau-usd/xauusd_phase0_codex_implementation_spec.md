# XAUUSD Master EA — Codex Implementation Specification

**Document:** `xauusd_phase0_codex_implementation_spec.md`  
**Version:** v1.0 — Phase 0 Build Specification  
**Date:** 2026-05-20  
**Audience:** Codex / coding agent / implementation team  
**Primary goal:** Build the Phase 0 statistical validation package and passive spread logger so the team can confirm or reject XAUUSD expert edges before coding any live-trading Expert Advisor logic.

---

## 0. Non-Negotiable Instruction to Codex

You are not being asked to build the live trading EA yet.

You are being asked to build the **Phase 0 research and validation codebase** that tests whether the proposed XAUUSD expert behaviors have statistical edge. The latest project decision is:

```text
Evidence before code.
Phase 0 before Phase 1.
No live trading code yet.
No OrderSend.
No martingale.
No grid.
No optimization after results.
```

The deliverable must let the team:

1. Register locked hypotheses for each candidate expert.
2. Ingest and normalize historical data from multiple sources.
3. Run the 9-cell Phase 0 backtest matrix.
4. Run decile persistence tests.
5. Run multi-symbol consistency checks.
6. Produce adversarial review templates from losing trades.
7. Produce per-expert Phase 0 result reports.
8. Produce a consolidated `PHASE0_VERDICT.md`.
9. Run a passive MT5 spread logger for 4 weeks without any trading capability.

This document should be treated as the coding contract.

---

## 1. Scope Boundary

### 1.1 In scope

Build the following:

```text
Python Phase 0 research package
Data ingestion and normalization tools
Indicator engine
Mechanical strategy simulators for 3 candidate experts
Backtest engine
Cost model engine
Risk and position-sizing engine for backtests
Metrics engine
Gate evaluator
Report generator
Hypothesis SHA256 lock system
Result manifest system
Passive MT5 spread logger EA
Unit tests
README and usage docs
```

### 1.2 Out of scope

Do **not** build the following yet:

```text
Live trading EA
OrderSend logic
CTrade order placement
Broker order management
Magic-number allocator for live orders
Risk manager for live orders
Position manager for live positions
ExpertLifecycleManager for production
News-trading expert
Fakeout expert
Trend-continuation expert
Reversal expert
Grid
Martingale
Recovery mode
Machine learning optimizer
Parameter optimizer
Any system that can send a real trade
```

The only MQL5 code in this phase is the **passive spread logger**, which must not include trading functions.

---

## 2. Required Repository Structure

Create the repository with this structure:

```text
xauusd-phase0/
│
├── README.md
├── CODEX_IMPLEMENTATION_SPEC.md
├── pyproject.toml
├── requirements.txt
├── .gitignore
│
├── config/
│   ├── phase0.yaml
│   ├── symbols.yaml
│   ├── cost_models.yaml
│   ├── broker_sources.yaml
│   ├── true_holdout_period.yaml
│   └── logging.yaml
│
├── docs/
│   ├── PHASE0_KICKOFF_CHECKLIST.md
│   ├── HYPOTHESIS_TEMPLATE.md
│   ├── hypothesis_trend_pullback.md
│   ├── hypothesis_breakout_retest.md
│   ├── hypothesis_range_mr.md
│   ├── PHASE0_DATA_MANIFEST_TEMPLATE.md
│   ├── PHASE0_RESULTS_TEMPLATE.md
│   ├── PHASE0_VERDICT_TEMPLATE.md
│   ├── ADVERSE_REVIEW_GUIDE.md
│   └── NO_TUNING_RULES.md
│
├── data/
│   ├── raw/
│   │   ├── capital_com/
│   │   ├── pepperstone/
│   │   └── dukascopy/
│   ├── processed/
│   │   ├── ticks/
│   │   └── bars/
│   ├── manifests/
│   └── README_DATA.md
│
├── outputs/
│   ├── hashes/
│   ├── manifests/
│   ├── matrix_results/
│   ├── decile_results/
│   ├── multisymbol_results/
│   ├── adversarial_review/
│   ├── reports/
│   ├── logs/
│   └── snapshots/
│
├── scripts/
│   ├── hash_hypotheses.py
│   ├── validate_data.py
│   ├── normalize_data.py
│   ├── build_bars.py
│   ├── run_phase0_matrix.py
│   ├── run_decile_tests.py
│   ├── run_multisymbol_checks.py
│   ├── create_adversarial_packets.py
│   ├── aggregate_results.py
│   ├── generate_verdict.py
│   ├── generate_snapshot.py
│   └── run_all_phase0.py
│
├── src/
│   └── phase0/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── data_contracts.py
│       ├── data_loader.py
│       ├── data_validator.py
│       ├── normalizer.py
│       ├── bar_builder.py
│       ├── indicators.py
│       ├── candles.py
│       ├── levels.py
│       ├── execution.py
│       ├── costs.py
│       ├── sizing.py
│       ├── backtester.py
│       ├── trades.py
│       ├── metrics.py
│       ├── gates.py
│       ├── reports.py
│       ├── hashing.py
│       ├── manifests.py
│       ├── snapshot.py
│       ├── constants.py
│       ├── utils.py
│       │
│       └── strategies/
│           ├── __init__.py
│           ├── base.py
│           ├── trend_pullback.py
│           ├── breakout_retest.py
│           └── range_mr.py
│
├── tests/
│   ├── conftest.py
│   ├── test_indicators.py
│   ├── test_candles.py
│   ├── test_levels.py
│   ├── test_costs.py
│   ├── test_sizing.py
│   ├── test_backtester.py
│   ├── test_gates.py
│   ├── test_hashing.py
│   ├── test_data_validator.py
│   └── test_no_lookahead.py
│
└── mt5/
    ├── PassiveSpreadLogger_XAUUSD.mq5
    ├── README_SPREAD_LOGGER.md
    └── spread_logger_set_example.set
```

---

## 3. Coding Principles

### 3.1 Determinism

Every run must be reproducible.

Rules:

```text
Same input files + same config + same code commit = same output files.
No random decisions unless seed is fixed and logged.
No hidden parameter changes.
No silent fallback to different data.
No automatic data deletion.
No unlogged row drops.
```

### 3.2 No look-ahead bias

The backtester must never use information from a candle before that candle is closed.

Rules:

```text
Indicators calculated on closed bars only.
Signals generated after confirmation candle close.
Market entries filled at next available quote/bar after signal time unless explicitly configured otherwise.
Retest logic cannot use future bars beyond the current evaluated bar.
Levels must be known before they are traded.
Daily/weekly highs/lows must come from completed prior day/week unless specifically coded as current-session levels.
```

### 3.3 No tuning after results

Codex must not implement optimization functionality in Phase 0.

Forbidden:

```text
Grid search
Bayesian optimization
Genetic optimization
Auto-parameter search
Trying EMA(21), EMA(34), EMA(50), EMA(89) and picking the best
Adding filters after a cell fails
Dropping bad time periods
Changing stop/target after result review
```

Allowed:

```text
Bug fixes
Data cleaning with logged reason
Ambiguity removal before first result run
Re-running after confirmed code defect
Reporting failures honestly
```

### 3.4 Fail loudly

The program should stop with a clear error if:

```text
Required data is missing.
Hypothesis hash does not match locked hash.
Config is invalid.
A raw data file has impossible timestamps.
Spread is negative.
Rows are unsorted.
A required output cannot be written.
A test cell tries to use an unlocked holdout period.
```

---

## 4. Python Environment

### 4.1 Python version

Use:

```text
Python >= 3.10
```

### 4.2 Required libraries

`requirements.txt`:

```text
pandas>=2.0
numpy>=1.24
pyyaml>=6.0
pytest>=7.0
jinja2>=3.1
tqdm>=4.65
python-dateutil>=2.8
pytz>=2023.3
```

Optional but allowed:

```text
rich>=13.0
matplotlib>=3.7
```

Do not require paid packages.

### 4.3 `pyproject.toml`

Create a minimal `pyproject.toml` with:

```toml
[project]
name = "xauusd-phase0"
version = "0.1.0"
description = "Phase 0 statistical validation package for XAUUSD Master EA"
requires-python = ">=3.10"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]

[tool.black]
line-length = 100
```

Black formatting is optional unless installed.

---

## 5. Configuration Files

### 5.1 `config/phase0.yaml`

Create this file:

```yaml
project:
  name: "XAUUSD Master EA Phase 0"
  version: "0.1.0"
  base_currency: "USD"
  starting_equity_usd: 10000.0
  phase0_risk_per_trade_pct: 0.005   # 0.50% fixed for Phase 0

execution:
  signal_execution_mode: "next_available_quote"  # no look-ahead
  ambiguous_intrabar_policy: "adverse_first"     # if SL and TP hit same bar, count SL first
  allow_partial_fills: false
  allow_pyramiding: false
  max_open_positions_per_expert: 1
  one_trade_at_a_time: true

periods:
  cell_1_3_start: "2016-01-01T00:00:00Z"
  cell_1_3_end:   "2018-12-31T23:59:59Z"
  cell_4_6_start: "2019-01-01T00:00:00Z"
  cell_4_6_end:   "2021-12-31T23:59:59Z"
  cell_7_9_start: "2022-01-01T00:00:00Z"
  cell_7_9_end:   "2024-12-31T23:59:59Z"
  decile_start:   "2016-01-01T00:00:00Z"
  decile_end:     "2025-12-31T23:59:59Z"
  multisymbol_start: "2016-01-01T00:00:00Z"
  multisymbol_end:   "2025-12-31T23:59:59Z"

true_holdout:
  enabled: true
  file: "config/true_holdout_period.yaml"
  require_unlock_flag_for_true_holdout: true

experts:
  trend_pullback:
    enabled: true
    hypothesis_file: "docs/hypothesis_trend_pullback.md"
  breakout_retest:
    enabled: true
    hypothesis_file: "docs/hypothesis_breakout_retest.md"
  range_mr:
    enabled: true
    hypothesis_file: "docs/hypothesis_range_mr.md"

gates:
  min_cells_pf_pass: 7
  total_cells: 9
  min_pf_per_passing_cell: 1.30
  min_trades_every_cell: 40
  max_drawdown_pct_every_cell: 30.0
  min_total_return_pct_every_cell: -25.0
  max_largest_trade_pnl_share_pct: 10.0
  max_top5_trades_pnl_share_pct: 40.0
  max_consecutive_zero_trade_months: 3
  min_p95_to_best_pf_ratio: 0.50

  decile_min_positive_deciles: 8
  decile_min_pf: 1.0
  decile_max_pf_vs_median_multiple: 2.0
  decile_min_trades: 10

  multisymbol_min_pf: 0.90
  adversarial_max_logic_gap_loser_pct: 25.0

outputs:
  root: "outputs"
  matrix_results: "outputs/matrix_results"
  decile_results: "outputs/decile_results"
  multisymbol_results: "outputs/multisymbol_results"
  adversarial_review: "outputs/adversarial_review"
  reports: "outputs/reports"
  logs: "outputs/logs"
  snapshots: "outputs/snapshots"
```

### 5.2 `config/true_holdout_period.yaml`

Create:

```yaml
true_holdout:
  status: "reserved"
  purpose: "Never touched during development unless final pre-live review explicitly unlocks it."
  start: "2025-07-01T00:00:00Z"
  end:   "2025-12-31T23:59:59Z"
  unlock_requires_file: "docs/FINAL_HOLDOUT_UNLOCK_APPROVAL.md"
  unlock_requires_cli_flag: "--unlock-true-holdout"
```

Implementation detail:

```text
Codex must implement this guard in code.
If a run touches the true holdout window without the approval file and CLI flag, abort.
```

Important:

```text
Some Phase 0 documents refer to full 2016–2025 decile testing. This codebase must support that, but it must require explicit holdout unlock if the configured true holdout overlaps the requested period.
```

### 5.3 `config/symbols.yaml`

Create:

```yaml
symbols:
  XAUUSD:
    aliases: ["XAUUSD", "XAUUSD.", "XAUUSDm", "GOLD"]
    asset_class: "metal_cfd"
    contract_size_per_lot: 100.0
    point_size: 0.01
    price_decimals: 2
    min_lot: 0.01
    lot_step: 0.01
    default_lot_for_cost: 1.0

  EURUSD:
    aliases: ["EURUSD", "EURUSD.", "EURUSDm"]
    asset_class: "fx_cfd"
    contract_size_per_lot: 100000.0
    point_size: 0.00001
    price_decimals: 5
    min_lot: 0.01
    lot_step: 0.01
    default_lot_for_cost: 1.0

  USDJPY:
    aliases: ["USDJPY", "USDJPY.", "USDJPYm"]
    asset_class: "fx_cfd"
    contract_size_per_lot: 100000.0
    point_size: 0.001
    price_decimals: 3
    min_lot: 0.01
    lot_step: 0.01
    default_lot_for_cost: 1.0
```

### 5.4 `config/cost_models.yaml`

Create:

```yaml
cost_models:
  best_case:
    description: "Optimistic spread scenario. Must not be used alone for approval."
    spread_source: "configured"
    spread_points:
      XAUUSD: 10
      EURUSD: 8
      USDJPY: 8
    commission_usd_per_round_turn_lot: 0.0
    slippage_points_entry: 0
    slippage_points_exit: 0

  median:
    description: "Median spread scenario. Replace with measured values once spread logger completes."
    spread_source: "configured_or_measured"
    spread_points:
      XAUUSD: 20
      EURUSD: 12
      USDJPY: 12
    commission_usd_per_round_turn_lot: 0.0
    slippage_points_entry: 0
    slippage_points_exit: 0

  p95:
    description: "P95 stress cost. Approval gates must survive this scenario."
    spread_source: "configured_or_measured"
    spread_points:
      XAUUSD: 35
      EURUSD: 20
      USDJPY: 20
    commission_usd_per_round_turn_lot: 0.0
    slippage_points_entry: 2
    slippage_points_exit: 2

multi_broker_scenarios:
  capital_com_zero_commission:
    commission_usd_per_round_turn_lot: 0.0
    spread_multiplier: 1.0
  raw_spread_plus_3:
    commission_usd_per_round_turn_lot: 3.0
    spread_multiplier: 0.75
  institutional_plus_7:
    commission_usd_per_round_turn_lot: 7.0
    spread_multiplier: 0.75
```

Important:

```text
These are placeholders until measured spread logger output exists.
The cost engine must be able to replace configured spreads with measured P50/P95 spread from CSV.
```

### 5.5 `config/broker_sources.yaml`

Create:

```yaml
brokers:
  capital_com:
    display_name: "Capital.com"
    priority: 1
    raw_dir: "data/raw/capital_com"
    processed_dir: "data/processed"
    default_timezone: "UTC"
    supports_ticks: true

  pepperstone:
    display_name: "Pepperstone"
    priority: 2
    raw_dir: "data/raw/pepperstone"
    processed_dir: "data/processed"
    default_timezone: "UTC"
    supports_ticks: true

  dukascopy:
    display_name: "Dukascopy"
    priority: 3
    raw_dir: "data/raw/dukascopy"
    processed_dir: "data/processed"
    default_timezone: "UTC"
    supports_ticks: true
```

---

## 6. Data Contracts

### 6.1 Raw tick data accepted formats

Codex must implement flexible readers for these common formats.

#### Format A — normalized tick CSV

```csv
timestamp_utc,bid,ask,volume
2016-01-04T00:00:00.123Z,1061.25,1061.45,1
```

#### Format B — MT5 exported tick CSV

Possible columns:

```csv
Time,Bid,Ask,Last,Volume
```

or:

```csv
<TICKTIME>,<BID>,<ASK>,<LAST>,<VOLUME>
```

#### Format C — Dukascopy-style tick CSV

Possible columns:

```csv
Time,Ask,Bid,AskVolume,BidVolume
```

### 6.2 Normalized tick schema

All tick data must be converted to:

```text
timestamp_utc: timezone-aware datetime, UTC, nanosecond or millisecond precision accepted
broker: string
symbol: canonical string, e.g. XAUUSD
bid: float
ask: float
mid: float = (bid + ask) / 2
spread_price: float = ask - bid
spread_points: float = spread_price / point_size
volume: float, optional, default 0
source_file: string
row_number: int
```

Normalized tick files must be stored as CSV or Parquet. CSV is acceptable for v1:

```text
data/processed/ticks/{broker}/{symbol}/{symbol}_{broker}_ticks_{YYYYMMDD}_{YYYYMMDD}.csv
```

### 6.3 Normalized bar schema

Bar builder must generate M1, M5, M15, H1, H4, D1 bars.

Schema:

```text
timestamp_utc: datetime of bar close or bar open, but must be explicitly configured
bar_start_utc: datetime
bar_end_utc: datetime
broker: string
symbol: string
timeframe: string
open: float
high: float
low: float
close: float
mid_open: float
mid_high: float
mid_low: float
mid_close: float
bid_open: float
bid_high: float
bid_low: float
bid_close: float
ask_open: float
ask_high: float
ask_low: float
ask_close: float
spread_open_points: float
spread_close_points: float
spread_median_points: float
spread_p95_points: float
tick_count: int
volume_sum: float
```

### 6.4 Bar timestamp convention

Use this convention:

```text
bar_start_utc = start of interval
bar_end_utc = exclusive end of interval
timestamp_utc = bar_end_utc
```

Example:

```text
M5 bar from 10:00:00 to 10:04:59.999 has:
bar_start_utc = 10:00:00
timeframe = M5
bar_end_utc = 10:05:00
timestamp_utc = 10:05:00
```

Signals generated on this bar may only be acted on at or after `timestamp_utc`.

### 6.5 Data validation rules

The validator must check:

```text
Timestamps are parseable.
Timestamps are timezone-aware or converted to UTC.
Rows are sorted ascending by timestamp.
Duplicate timestamps are flagged.
Bid > 0.
Ask > 0.
Ask >= Bid.
Spread is not negative.
Spread is not unreasonably huge unless flagged.
There are no impossible OHLC bars: high >= max(open, close), low <= min(open, close).
There are no large missing chunks without warnings.
```

Missing data policy:

```text
Do not silently fill missing ticks.
For bars, if no tick exists for an interval, emit no bar or emit a bar with missing flag, based on config.
The default should be no bar and a gap warning.
Backtest must skip periods where required timeframe alignment is unavailable.
```

Data validation output:

```text
outputs/manifests/data_validation_{broker}_{symbol}_{YYYYMMDD}.csv
outputs/manifests/data_validation_summary.md
```

---

## 7. Phase 0 9-Cell Matrix

Implement exactly this matrix for each expert.

| Cell | Time window | Tick source | Cost model |
|---:|---|---|---|
| 1 | 2016-01-01 to 2018-12-31 | Capital.com | best_case |
| 2 | 2016-01-01 to 2018-12-31 | Capital.com | median |
| 3 | 2016-01-01 to 2018-12-31 | Capital.com | p95 |
| 4 | 2019-01-01 to 2021-12-31 | Pepperstone | best_case |
| 5 | 2019-01-01 to 2021-12-31 | Pepperstone | median |
| 6 | 2019-01-01 to 2021-12-31 | Pepperstone | p95 |
| 7 | 2022-01-01 to 2024-12-31 | Dukascopy | best_case |
| 8 | 2022-01-01 to 2024-12-31 | Dukascopy | median |
| 9 | 2022-01-01 to 2024-12-31 | Dukascopy | p95 |

Rules:

```text
Same strategy logic in all cells.
Same parameters in all cells.
Same starting equity: $10,000.
Same risk per trade: 0.50%.
No session filter unless the locked hypothesis explicitly defines one.
No news filter in Phase 0 unless the locked hypothesis explicitly defines one.
No manual exclusions.
No parameter optimization.
```

Output for every cell:

```text
outputs/matrix_results/{expert}/cell_{cell_id}_{expert}_{broker}_{cost_model}.csv
outputs/matrix_results/{expert}/cell_{cell_id}_{expert}_{broker}_{cost_model}_trades.csv
outputs/matrix_results/{expert}/cell_{cell_id}_{expert}_{broker}_{cost_model}_equity.csv
```

---

## 8. Hypothesis Registration and Hash Lock

### 8.1 Required hypothesis files

Create these template files:

```text
docs/hypothesis_trend_pullback.md
docs/hypothesis_breakout_retest.md
docs/hypothesis_range_mr.md
```

Each file must contain:

```text
Expert name
Hypothesis date
Author / owner
Mechanical definition
Expected trade count per year ±20%
Expected cost-adjusted PF ±0.3
Expected losing-month percentage ±10%
Expected worst single month
Expected max consecutive zero months
Expected R-multiple distribution
Why this hypothesis should exist
What would falsify it
```

### 8.2 Hash manifest

Implement `scripts/hash_hypotheses.py` and `src/phase0/hashing.py`.

Command:

```bash
python scripts/hash_hypotheses.py --register
```

Output:

```text
outputs/hashes/hypothesis_hash_manifest.csv
```

Schema:

```text
expert,hypothesis_file,sha256,registered_at_utc,file_size_bytes,git_commit_if_available
```

### 8.3 Hash validation before backtest

Every backtest command must validate that the current SHA256 of the hypothesis file matches the registered SHA256.

If mismatch:

```text
Abort.
Print: "Hypothesis file has changed after registration. Re-register only if no results have been produced, or create a new hypothesis version."
```

### 8.4 Versioned re-registration

If a hypothesis must change before any results exist, allow:

```bash
python scripts/hash_hypotheses.py --register --version v2 --reason "Ambiguity removed before first backtest"
```

If results already exist for that expert/version, do not overwrite the old hash. Create a new version row.

---

## 9. Indicator Definitions

Implement indicators in `src/phase0/indicators.py`.

### 9.1 EMA

Use standard exponential moving average:

```text
alpha = 2 / (period + 1)
EMA_t = alpha * Close_t + (1 - alpha) * EMA_{t-1}
```

Initialization:

```text
First EMA value = simple average of first period closes.
Values before period are NaN.
```

### 9.2 ATR

Use Wilder's ATR.

True range:

```text
TR_t = max(
  High_t - Low_t,
  abs(High_t - Close_{t-1}),
  abs(Low_t - Close_{t-1})
)
```

ATR:

```text
First ATR = simple average of first N TR values.
Subsequent ATR = ((prior_ATR * (N - 1)) + current_TR) / N
```

### 9.3 ADX

Use Wilder's ADX with period 14.

Implement:

```text
+DM
-DM
Smoothed TR
Smoothed +DM
Smoothed -DM
+DI
-DI
DX
ADX
```

Values before sufficient lookback are NaN.

### 9.4 Candle body and wick definitions

For any candle:

```text
body = abs(close - open)
upper_wick = high - max(open, close)
lower_wick = min(open, close) - low
range = high - low
bullish = close > open
bearish = close < open
doji = body <= 0.1 * range, if range > 0
```

If body is zero:

```text
body_for_ratio = max(body, point_size)
```

### 9.5 Bullish engulfing

A candle is bullish engulfing if:

```text
Current candle bullish.
Previous candle bearish.
Current close > previous open.
Current open < previous close.
Current body >= previous body.
```

### 9.6 Bearish engulfing

A candle is bearish engulfing if:

```text
Current candle bearish.
Previous candle bullish.
Current close < previous open.
Current open > previous close.
Current body >= previous body.
```

### 9.7 Bullish pin bar

A candle is bullish pin bar if:

```text
lower_wick >= 2.0 * body_for_ratio
upper_wick <= 1.0 * body_for_ratio
close >= open OR close >= low + 0.60 * range
```

### 9.8 Bearish pin bar

A candle is bearish pin bar if:

```text
upper_wick >= 2.0 * body_for_ratio
lower_wick <= 1.0 * body_for_ratio
close <= open OR close <= high - 0.60 * range
```

### 9.9 Slope

EMA slope over N bars:

```text
slope = EMA_t - EMA_{t-N}
```

Positive slope:

```text
slope > 0
```

Negative slope:

```text
slope < 0
```

No percent normalization for Phase 0 unless explicitly specified.

---

## 10. Strategy Definitions

The three candidate experts are mechanical research strategies. They are not live trading experts yet.

Each strategy must subclass `StrategyBase`.

### 10.1 `StrategyBase`

Create `src/phase0/strategies/base.py`.

Interface:

```python
class StrategyBase:
    name: str
    version: str

    def prepare_features(self, data_context):
        """Return data_context with required indicators/features."""

    def generate_signals(self, data_context):
        """Return a list/DataFrame of Signal objects without executing trades."""

    def build_trade_plan(self, signal, data_context):
        """Return TradePlan with entry, stop, target, direction."""
```

Use dataclasses:

```python
@dataclass(frozen=True)
class Signal:
    expert: str
    timestamp_utc: pd.Timestamp
    symbol: str
    direction: Literal["LONG", "SHORT"]
    reason_code: str
    metadata: dict

@dataclass(frozen=True)
class TradePlan:
    expert: str
    symbol: str
    direction: Literal["LONG", "SHORT"]
    signal_time_utc: pd.Timestamp
    entry_type: Literal["MARKET", "STOP", "LIMIT"]
    entry_price: float | None
    stop_loss: float
    take_profit: float
    invalidation_level: float
    risk_reward: float
    reason_code: str
    metadata: dict
```

### 10.2 Trend Pullback Expert

File:

```text
src/phase0/strategies/trend_pullback.py
```

#### 10.2.1 Long setup

A long signal occurs when all conditions are true:

```text
1. H1 trend filter:
   - EMA(50) on H1 > EMA(200) on H1
   - EMA(50) slope over last 20 H1 bars > 0

2. M15 pullback filter:
   - Use the latest fully closed M15 bar aligned to current M5 signal time.
   - M15 close is within 0.5 × ATR(14, H1) of EMA(21, M15).
   - Distance definition: abs(M15 close - M15 EMA21) <= 0.5 * latest H1 ATR14.

3. M5 confirmation:
   - Current fully closed M5 candle is bullish engulfing OR bullish pin bar.

4. No open position for this expert.
```

#### 10.2.2 Long execution plan

```text
Entry type: MARKET
Entry fill: next available quote/bar after M5 confirmation close.
Stop loss: pullback_low - 0.1 × ATR(14, M15)
Take profit: entry + 1.5 × trade_risk_price
Invalidation: same as stop loss
```

Pullback low definition:

```text
Minimum low of the last 10 completed M5 bars ending at confirmation candle.
```

Trade risk price:

```text
entry_price - stop_loss
```

Reject signal if:

```text
trade_risk_price <= 0
stop_loss >= entry_price
ATR unavailable
Any required EMA unavailable
```

#### 10.2.3 Short setup

Mirror logic:

```text
1. H1 trend filter:
   - EMA(50) on H1 < EMA(200) on H1
   - EMA(50) slope over last 20 H1 bars < 0

2. M15 pullback filter:
   - abs(M15 close - M15 EMA21) <= 0.5 × latest H1 ATR14

3. M5 confirmation:
   - Current fully closed M5 candle is bearish engulfing OR bearish pin bar.

4. No open position for this expert.
```

#### 10.2.4 Short execution plan

```text
Entry type: MARKET
Entry fill: next available quote/bar after M5 confirmation close.
Stop loss: pullback_high + 0.1 × ATR(14, M15)
Take profit: entry - 1.5 × trade_risk_price
Invalidation: same as stop loss
```

Pullback high definition:

```text
Maximum high of the last 10 completed M5 bars ending at confirmation candle.
```

Trade risk price:

```text
stop_loss - entry_price
```

Reject signal if:

```text
trade_risk_price <= 0
stop_loss <= entry_price
ATR unavailable
Any required EMA unavailable
```

### 10.3 Breakout-Retest Expert

File:

```text
src/phase0/strategies/breakout_retest.py
```

#### 10.3.1 Level definitions

Candidate resistance levels for long:

```text
Previous completed daily high
Previous completed weekly high
M5 swing high with 4 bars on both sides
```

Candidate support levels for short:

```text
Previous completed daily low
Previous completed weekly low
M5 swing low with 4 bars on both sides
```

M5 swing high definition:

```text
A completed M5 bar i is swing high if:
high_i > high_{i-1}, high_{i-2}, high_{i-3}, high_{i-4}
and
high_i > high_{i+1}, high_{i+2}, high_{i+3}, high_{i+4}
```

Important:

```text
A swing high is only known after the 4 bars to the right have closed.
Do not use a swing level before it is confirmed.
```

M5 swing low definition is the mirror using lows.

#### 10.3.2 Long breakout condition

For a known resistance level:

```text
Break occurs when a completed M5 candle closes above level by at least 0.3 × ATR(14, M5).
Break close condition:
M5 close >= level + 0.3 * ATR14_M5
```

After break:

```text
Wait up to 20 completed M5 bars for retest.
```

Retest condition:

```text
M5 low returns to within 5 points of broken level.
Distance condition:
abs(M5 low - level) <= 5 * point_size
OR
M5 low <= level + 5 * point_size
```

Hold condition:

```text
Retest candle must not close below level.
M5 close >= level
```

Confirmation:

```text
The next completed M5 candle after the retest candle is bullish.
```

Entry plan:

```text
Entry type: STOP
Entry price: high of retest candle + 1 point
Stop loss: low of retest candle - 0.1 × ATR(14, M5)
Take profit: entry + 1.5 × risk_price
```

A buy stop is triggered if a later bar's high >= entry_price.

Order expiration:

```text
Expire if not triggered within 5 M5 bars after confirmation candle.
```

#### 10.3.3 Short breakout condition

Mirror logic for support level:

```text
Break occurs when M5 close <= level - 0.3 × ATR(14, M5).
Wait up to 20 M5 bars for retest.
Retest occurs when M5 high returns to within 5 points of broken level.
Retest candle must not close above level.
Confirmation candle after retest is bearish.
Entry type: STOP
Entry price: low of retest candle - 1 point
Stop loss: high of retest candle + 0.1 × ATR(14, M5)
Take profit: entry - 1.5 × risk_price
Expire if not triggered within 5 M5 bars.
```

#### 10.3.4 Duplicate level control

If multiple levels are within 10 points of each other:

```text
Keep the most recent level.
Drop duplicates for that signal cycle.
```

If multiple breakout-retest signals occur simultaneously:

```text
Choose the signal with smallest stop distance.
If tied, choose the earlier level timestamp.
```

### 10.4 Range Mean-Reversion Expert

File:

```text
src/phase0/strategies/range_mr.py
```

#### 10.4.1 Range state

Range is valid if all conditions are true:

```text
1. H1 ADX(14) < 20 for the last 20 completed H1 bars.

2. On the last 50 completed M15 bars:
   - There are at least 3 upper-boundary touches.
   - There are at least 3 lower-boundary touches.

3. Range width >= 2 × ATR(14, M15).
```

Boundary calculation:

```text
upper_boundary = max(high of last 50 M15 bars)
lower_boundary = min(low of last 50 M15 bars)
range_width = upper_boundary - lower_boundary
```

Touch definition:

```text
A bar touches upper boundary if high >= upper_boundary - 0.2 × ATR(14, M15).
A bar touches lower boundary if low <= lower_boundary + 0.2 × ATR(14, M15).
```

Important:

```text
Since upper/lower boundary are calculated from the last 50 completed bars, do not include the current signal candle unless it is already closed.
```

#### 10.4.2 Long setup

A long signal occurs when:

```text
Valid range state.
Current completed M5 candle low reaches lower_boundary + 0.2 × ATR(14, M15) or lower.
Current M5 candle is bullish pin bar.
```

Entry plan:

```text
Entry type: LIMIT
Entry price: lower_boundary
Stop loss: lower_boundary - 0.3 × ATR(14, M15)
Take profit: upper_boundary
```

Limit trigger:

```text
Buy limit fills if a later bar's low <= entry_price.
```

Order expiration:

```text
Expire if not triggered within 6 M5 bars.
```

Reject signal if:

```text
Take profit <= entry price
Risk price <= 0
Reward/risk < 1.0
```

#### 10.4.3 Short setup

Mirror logic:

```text
Valid range state.
Current completed M5 candle high reaches upper_boundary - 0.2 × ATR(14, M15) or higher.
Current M5 candle is bearish pin bar.
```

Entry plan:

```text
Entry type: LIMIT
Entry price: upper_boundary
Stop loss: upper_boundary + 0.3 × ATR(14, M15)
Take profit: lower_boundary
```

Limit trigger:

```text
Sell limit fills if a later bar's high >= entry_price.
```

Order expiration:

```text
Expire if not triggered within 6 M5 bars.
```

Reject signal if:

```text
Take profit >= entry price
Risk price <= 0
Reward/risk < 1.0
```

---

## 11. Backtest Engine

File:

```text
src/phase0/backtester.py
```

### 11.1 Backtest loop

The backtester must:

```text
Load required bars and ticks.
Align M5, M15, H1, H4, D1 data.
Call strategy.prepare_features().
Iterate through M5 bars in chronological order.
At each M5 bar close, evaluate signals using only known data.
Build TradePlan.
Pass TradePlan to execution simulator.
Manage pending orders.
Manage open trade.
Record trade, equity, and diagnostics.
```

### 11.2 One-trade-at-a-time rule

For Phase 0:

```text
One open position per expert.
No pyramiding.
No simultaneous long and short for same expert.
No portfolio-level routing yet.
```

If a new signal occurs while a trade is open:

```text
Ignore it.
Log ignored_signal_reason = "open_position_exists".
```

### 11.3 Market order execution

For market entry:

```text
Signal generated at M5 bar close timestamp.
Entry fill is first available tick at or after signal timestamp.
If ticks unavailable, entry fill is next M5 bar open.
```

Long market fill:

```text
entry_price = ask price, or mid + spread/2 if using bar data.
```

Short market fill:

```text
entry_price = bid price, or mid - spread/2 if using bar data.
```

### 11.4 Stop and limit order execution

For pending stop/limit orders, simulate trigger using subsequent bar OHLC.

Buy stop:

```text
Triggered if bar_high >= entry_price.
Fill price = entry_price + entry_slippage.
```

Sell stop:

```text
Triggered if bar_low <= entry_price.
Fill price = entry_price - entry_slippage.
```

Buy limit:

```text
Triggered if bar_low <= entry_price.
Fill price = entry_price + entry_slippage.
```

Sell limit:

```text
Triggered if bar_high >= entry_price.
Fill price = entry_price - entry_slippage.
```

### 11.5 Exit simulation

For each open trade, check each subsequent bar.

Long:

```text
SL hit if bar_low <= stop_loss.
TP hit if bar_high >= take_profit.
```

Short:

```text
SL hit if bar_high >= stop_loss.
TP hit if bar_low <= take_profit.
```

Ambiguous same-bar policy:

```text
If both SL and TP are touched in same bar, assume SL hit first.
This is conservative and must be logged as ambiguous_exit = true.
```

### 11.6 Time stop

Phase 0 strategy definitions do not use live Position Manager exits unless specified. For consistency:

```text
Do not apply break-even.
Do not apply trailing stop.
Do not apply partial close.
Do not apply time stop unless the hypothesis file explicitly requires it.
```

This differs from future live EA v1. Phase 0 is testing raw behavior.

### 11.7 End-of-period close

If a trade is open at the end of a cell period:

```text
Close at final available quote/bar close.
exit_reason = "end_of_test_period"
```

---

## 12. Cost Model Engine

File:

```text
src/phase0/costs.py
```

### 12.1 Spread application

For mid-price bars:

```text
long entry = mid_entry + spread / 2
long exit  = mid_exit  - spread / 2
short entry = mid_entry - spread / 2
short exit  = mid_exit  + spread / 2
```

If bid/ask bars exist:

```text
Use ask for long entry and short exit.
Use bid for short entry and long exit.
```

### 12.2 Configured spread

If using configured cost model:

```text
spread_price = spread_points * point_size
```

### 12.3 Measured spread

If spread logger output exists:

```text
Use measured spread distribution by symbol, broker, hour, and day-of-week.
If hour/day bucket unavailable, fall back to global median/P95.
```

Implement function:

```python
def get_spread_points(symbol, broker, timestamp_utc, cost_model):
    ...
```

### 12.4 Slippage

Apply slippage as adverse price movement.

Long:

```text
Entry slippage increases entry price.
Exit slippage decreases exit price.
```

Short:

```text
Entry slippage decreases entry price.
Exit slippage increases exit price.
```

### 12.5 Commission

Commission is round-turn USD per lot.

```text
commission_usd = commission_usd_per_round_turn_lot * lots
```

Subtract commission from trade PnL once per completed trade.

---

## 13. Position Sizing and PnL

File:

```text
src/phase0/sizing.py
```

### 13.1 Risk per trade

```text
risk_money = current_equity * 0.005
```

Use current equity, not starting balance.

### 13.2 Price risk

Long:

```text
price_risk = entry_price - stop_loss
```

Short:

```text
price_risk = stop_loss - entry_price
```

Reject trade if:

```text
price_risk <= 0
```

### 13.3 Lot calculation

```text
units_per_lot = contract_size_per_lot
pnl_per_1_price_unit_per_lot = units_per_lot
risk_per_lot_usd = price_risk * units_per_lot
raw_lots = risk_money / risk_per_lot_usd
lots = floor_to_lot_step(raw_lots, lot_step)
```

Reject trade if:

```text
lots < min_lot
```

For Phase 0, if lot rounding causes risk deviation:

```text
Log actual_risk_pct.
Do not resize above allowed risk.
```

### 13.4 PnL calculation

Long:

```text
gross_pnl = (exit_price - entry_price) * lots * contract_size_per_lot
```

Short:

```text
gross_pnl = (entry_price - exit_price) * lots * contract_size_per_lot
```

Net:

```text
net_pnl = gross_pnl - commission_usd
```

R multiple:

```text
r_multiple = net_pnl / risk_money_at_entry
```

---

## 14. Metrics Engine

File:

```text
src/phase0/metrics.py
```

### 14.1 Required per-cell metrics

For each cell, compute:

```text
cell_id
time_window
tick_source
cost_model
expert
symbol
trade_count
win_rate
profit_factor
total_return_pct
total_pnl_usd
avg_trade_R
median_trade_R
max_drawdown_pct
max_drawdown_usd
worst_month_usd
best_month_usd
losing_month_pct
max_consecutive_zero_trade_months
max_consecutive_losing_months
largest_single_trade_pct_of_pnl
top5_trades_pct_of_pnl
p95_to_best_pf_ratio, computed later across paired cells
```

### 14.2 Profit factor

```text
gross_profit = sum(net_pnl for winning trades)
gross_loss = abs(sum(net_pnl for losing trades))
PF = gross_profit / gross_loss
```

If no losing trades:

```text
PF = inf
```

But gate evaluation must flag no-loss PF as unstable if trade count is low.

### 14.3 Drawdown

Use equity curve after each trade.

```text
running_peak = cumulative max equity
current_dd = running_peak - equity
dd_pct = current_dd / running_peak * 100
max_drawdown_pct = max(dd_pct)
```

### 14.4 Monthly metrics

Use trade exit timestamp for realized monthly PnL.

Zero-trade month:

```text
A calendar month in the test period with zero closed trades.
```

Consecutive zero-trade months:

```text
Longest consecutive sequence of calendar months with zero closed trades.
```

Losing month:

```text
Monthly net PnL < 0.
```

Losing-month percentage:

```text
losing_month_count / months_within_test_period * 100
```

### 14.5 Concentration metrics

Largest single trade contribution:

```text
largest_single_trade_pct_of_pnl = max(net_pnl) / total_net_profit * 100
```

If total_net_profit <= 0:

```text
Set largest_single_trade_pct_of_pnl = 100
Set top5_trades_pct_of_pnl = 100
```

Top 5 contribution:

```text
top5_trades_pct_of_pnl = sum(top 5 positive net_pnl trades) / total_net_profit * 100
```

---

## 15. Gate Evaluator

File:

```text
src/phase0/gates.py
```

### 15.1 Gate 1 — Multi-cell survival

Pass if:

```text
At least 7 of 9 cells have cost-adjusted PF >= 1.30.
```

### 15.2 Gate 2 — Sample size

Pass if:

```text
trade_count >= 40 in every cell.
```

### 15.3 Gate 3 — No catastrophic failure

Pass if:

```text
max_drawdown_pct <= 30 in every cell.
total_return_pct >= -25 in every cell.
```

### 15.4 Gate 4 — Concentration

Pass if:

```text
largest_single_trade_pct_of_pnl <= 10 in every cell.
top5_trades_pct_of_pnl <= 40 in every cell.
```

### 15.5 Gate 5 — Activity

Pass if:

```text
max_consecutive_zero_trade_months <= 3 in every cell.
```

### 15.6 Gate 6 — Cost sensitivity

For each time window:

```text
p95_pf / best_case_pf >= 0.50
```

Pairings:

```text
Cells 1 and 3
Cells 4 and 6
Cells 7 and 9
```

If best_case_pf is infinite:

```text
Use conservative fail unless p95_pf is also infinite and trade_count >= 40.
```

### 15.7 Decile gate

Pass if:

```text
At least 8 of 10 deciles have PF > 1.0.
No decile PF > 2.0 × median PF.
No decile trade count < 10.
```

If median PF <= 0:

```text
Fail.
```

### 15.8 Multi-symbol gate

Pass if:

```text
EURUSD PF >= 0.90
USDJPY PF >= 0.90
```

If not:

```text
Allow status = PASS_WITH_XAU_SPECIFIC_JUSTIFICATION only if the report contains a non-empty XAU-specific mechanism field.
```

### 15.9 Adversarial gate

Pass if:

```text
logic_gap_failures_pct <= 25
```

If manual review is incomplete:

```text
Gate status = PENDING, not PASS.
```

---

## 16. Report Generation

File:

```text
src/phase0/reports.py
```

### 16.1 Per-expert result report

Generate:

```text
outputs/reports/phase0_trend_pullback_results.md
outputs/reports/phase0_breakout_retest_results.md
outputs/reports/phase0_range_mr_results.md
```

Each report must include:

```text
Hypothesis file name
Registered SHA256
Current SHA256
Hash match: yes/no
9-cell matrix table
Gate pass/fail summary
Decile test table
Adversarial review summary
Multi-symbol check summary
Hypothesis vs reality table
Final verdict: PASS / FAIL / PENDING
If failed: exact failed gates
If passed: exact evidence
```

### 16.2 Consolidated verdict

Generate:

```text
outputs/reports/PHASE0_VERDICT.md
```

Required table:

```text
| Expert | 9-cell | Decile | Adversarial | Multi-symbol | Hypothesis-match | FINAL |
```

Decision logic:

```text
3 experts pass -> Proceed to Phase 1 with 3-expert v1.
1-2 experts pass -> Proceed to Phase 1 with reduced v1.
0 experts pass -> Stop. Do not begin Phase 1.
```

### 16.3 Raw output preservation

Do not only produce markdown. Also preserve:

```text
CSV trades
CSV equity curves
CSV cell metrics
CSV gate results
CSV decile results
CSV multisymbol results
```

---

## 17. Adversarial Review Packet

File:

```text
scripts/create_adversarial_packets.py
```

Purpose:

```text
Create manual review packets for losing trades.
```

For each expert, output:

```text
outputs/adversarial_review/{expert}_losing_trades_review.csv
```

Columns:

```text
trade_id
expert
cell_id
symbol
broker
cost_model
entry_time_utc
exit_time_utc
direction
entry_price
stop_loss
take_profit
exit_price
net_pnl
r_multiple
setup_reason_code
chart_context_start_utc
chart_context_end_utc
manual_failure_class
manual_notes
reviewer
reviewed_at_utc
```

Allowed `manual_failure_class` values:

```text
VALID_SETUP_MARKET_LOSS
VALID_BUT_WRONG_REGIME
LOGIC_GAP
DATA_OR_EXECUTION_ARTIFACT
UNCLEAR
```

Adversarial report generator must count:

```text
logic_gap_failures_pct = LOGIC_GAP count / losing trades reviewed * 100
```

Do not mark adversarial gate as passed until every losing trade or the required sample has been manually reviewed.

For large losing-trade counts:

```text
Review all losing trades if <= 100.
If > 100, review at least 100 randomly selected losing trades with fixed seed 920000 plus all top 20 largest losses.
```

---

## 18. Multi-Symbol Check

File:

```text
scripts/run_multisymbol_checks.py
```

Run the same mechanical logic on:

```text
EURUSD
USDJPY
```

Period:

```text
2016-01-01 through 2025-12-31, unless true holdout guard blocks part of it.
```

Rules:

```text
No parameter changes.
ATR-based distances naturally adjust by symbol.
Point sizes come from symbols.yaml.
Same risk per trade.
Same cost model: median by default, p95 optional.
```

Output:

```text
outputs/multisymbol_results/{expert}_multisymbol_summary.csv
outputs/multisymbol_results/{expert}_{symbol}_trades.csv
```

If PF < 0.90 on either comparison symbol:

```text
Report requires XAU-specific mechanism text.
```

---

## 19. Decile Test

File:

```text
scripts/run_decile_tests.py
```

Procedure:

```text
Use Capital.com XAUUSD data.
Split configured decile period into 10 equal time segments.
Run locked expert logic independently on each decile.
Record PF and trade count.
```

Output:

```text
outputs/decile_results/{expert}_decile_results.csv
```

Columns:

```text
expert
decile_id
start_utc
end_utc
trade_count
profit_factor
total_return_pct
max_drawdown_pct
avg_trade_R
verdict
```

---

## 20. CLI Commands

Implement `src/phase0/cli.py` so commands can be run as:

```bash
python -m phase0 <command> [args]
```

Also keep the `scripts/*.py` wrappers for simplicity.

### 20.1 Required commands

```bash
python -m phase0 hash-hypotheses --register
python -m phase0 validate-data --broker capital_com --symbol XAUUSD
python -m phase0 normalize-data --broker capital_com --symbol XAUUSD
python -m phase0 build-bars --broker capital_com --symbol XAUUSD --timeframes M1,M5,M15,H1,H4,D1
python -m phase0 run-matrix --expert trend_pullback
python -m phase0 run-matrix --expert breakout_retest
python -m phase0 run-matrix --expert range_mr
python -m phase0 run-matrix --expert all
python -m phase0 run-deciles --expert all
python -m phase0 run-multisymbol --expert all
python -m phase0 create-adversarial-packets --expert all
python -m phase0 aggregate-results --expert all
python -m phase0 generate-verdict
python -m phase0 run-all
```

### 20.2 `run-all` behavior

`run-all` should execute:

```text
1. Validate config.
2. Validate hypothesis hashes.
3. Validate processed data availability.
4. Run 9-cell matrix for each enabled expert.
5. Run decile tests.
6. Run multi-symbol checks.
7. Create adversarial packets.
8. Aggregate results.
9. Generate reports.
```

It should stop if a required step fails.

---

## 21. Passive MT5 Spread Logger

File:

```text
mt5/PassiveSpreadLogger_XAUUSD.mq5
```

### 21.1 Purpose

The passive spread logger collects real broker spread behavior for 4 weeks.

It must log:

```text
Bid
Ask
Spread price
Spread points
Broker time
UTC/GMT time
Local machine time
Symbol
Account number
Server name
Session label
Rollover flag
```

### 21.2 Absolute restrictions

The MQL5 file must not contain:

```text
OrderSend
CTrade
trade.Buy
trade.Sell
PositionOpen
OrderSendAsync
OrderCheck for trade intent
Any function that places, modifies, or closes orders
```

It is a logger only.

### 21.3 Inputs

```mql5
input string InpSymbol = "";                 // Empty means _Symbol
input int    InpLogIntervalSeconds = 5;
input bool   InpUseCommonFiles = true;
input string InpFilePrefix = "spread_log";
input bool   InpPrintToExpertsTab = false;
input int    InpRolloverHourServer = 22;
input int    InpRolloverWindowMinutes = 30;
```

### 21.4 CSV output

File name:

```text
spread_log_{account}_{server}_{symbol}_{YYYYMMDD}.csv
```

CSV header:

```text
broker_time,gmt_time,local_time,account,server,symbol,bid,ask,spread_price,spread_points,point,digits,session_label,is_rollover_window
```

### 21.5 Session label

Implement simple UTC/GMT labels:

```text
ASIA:        00:00–06:59 UTC
PRE_LONDON: 07:00–07:59 UTC
LONDON:      08:00–12:59 UTC
NY_OVERLAP:  13:00–16:59 UTC
NEW_YORK:    17:00–20:59 UTC
ROLLOVER:    rollover window based on server hour input
OFF_HOURS:   otherwise
```

### 21.6 Timer

Use:

```mql5
EventSetTimer(InpLogIntervalSeconds)
```

On every timer event:

```text
Read SymbolInfoTick.
Calculate spread.
Append CSV row.
Update chart comment/dashboard.
```

### 21.7 Dashboard text

Display:

```text
Passive Spread Logger
Symbol: XAUUSD
Account: <account>
Server: <server>
Last log: <time>
Bid/Ask: <bid>/<ask>
Spread points: <spread>
Rows written today: <N>
NO TRADING FUNCTIONS PRESENT
```

### 21.8 Spread log analysis

Codex must implement Python script:

```text
scripts/analyze_spread_logs.py
```

It reads spread logger CSVs and outputs:

```text
outputs/reports/cost_model_measured.csv
outputs/reports/spread_distribution_report.md
```

Required metrics:

```text
Median spread by hour of day
P95 spread by hour of day
Median spread by day of week
P95 spread by day of week
Rollover median/P95/max
News-window median/P95/max if event labels are provided later
Global median/P95/max
```

---

## 22. Data Manifest

Create:

```text
docs/PHASE0_DATA_MANIFEST_TEMPLATE.md
```

The generated manifest should be:

```text
outputs/manifests/PHASE0_DATA_MANIFEST.md
```

It must include:

```text
Data source
Broker
Symbol
Raw file names
Raw file hashes
Start timestamp
End timestamp
Row count
Processed file names
Processed file hashes
Known gaps
Known quality warnings
Prepared by
Prepared date
```

Codex must implement file hashing for raw and processed files.

---

## 23. Snapshot Bundle

Create:

```text
scripts/generate_snapshot.py
```

Snapshot output:

```text
outputs/snapshots/phase0_snapshot_{YYYYMMDD_HHMMSS}.zip
```

Include:

```text
config files
hypothesis files
hypothesis hash manifest
data manifest
all result CSVs
all report MD files
git commit hash if available
requirements.txt
pyproject.toml
```

Do not include raw tick data in the zip by default unless `--include-raw-data` is passed.

---

## 24. Tests

Codex must create unit tests.

### 24.1 Indicator tests

`tests/test_indicators.py` must test:

```text
EMA basic calculation
ATR basic calculation
ADX no-crash and shape correctness
NaN warmup behavior
```

### 24.2 Candle tests

`tests/test_candles.py` must test:

```text
Bullish engulfing true/false
Bearish engulfing true/false
Bullish pin bar true/false
Bearish pin bar true/false
Zero-body candle handling
```

### 24.3 Cost tests

`tests/test_costs.py` must test:

```text
Long entry/exit spread application
Short entry/exit spread application
Slippage adverse application
Commission subtraction
```

### 24.4 Sizing tests

`tests/test_sizing.py` must test:

```text
Risk money = equity * risk_pct
XAUUSD lot sizing
Lot step rounding down
Reject when lots < min_lot
Reject when stop distance invalid
```

### 24.5 Backtester tests

`tests/test_backtester.py` must test:

```text
Simple long TP hit
Simple long SL hit
Simple short TP hit
Simple short SL hit
Ambiguous same-bar exits count SL first
Pending order expiration
End-of-test close
```

### 24.6 Gate tests

`tests/test_gates.py` must test:

```text
7 of 9 PF pass
6 of 9 PF fail
Trade count fail
Drawdown fail
Concentration fail
Activity fail
Cost sensitivity fail
Decile pass/fail
```

### 24.7 Hashing tests

`tests/test_hashing.py` must test:

```text
SHA256 stable for same file
Hash mismatch detected
Manifest written correctly
```

### 24.8 No-lookahead tests

`tests/test_no_lookahead.py` must test:

```text
Swing high is not available until right-side bars close.
Previous daily high does not include current day.
Signal timestamp is after confirmation bar close.
Market fill is not before signal timestamp.
```

---

## 25. Required README

Create `README.md` with:

```text
Project purpose
What Phase 0 is
What Phase 0 is not
Setup instructions
Data folder instructions
How to register hypotheses
How to run validation
How to run 9-cell matrix
How to run decile test
How to run multi-symbol check
How to generate verdict
How to run passive spread logger
How to interpret outputs
What to do if experts fail
```

Include this warning:

```text
This repository does not contain live trading logic. It is a research validation package. Do not add OrderSend or live order placement in Phase 0.
```

---

## 26. Implementation Order for Codex

Implement in this order.

### Step 1 — Repository skeleton

Create folders, config files, README, templates.

Acceptance:

```text
Repository imports without errors.
pytest can run, even if tests are initially empty.
```

### Step 2 — Data contracts and config loader

Implement:

```text
config.py
data_contracts.py
constants.py
```

Acceptance:

```text
Can load all YAML files.
Invalid config fails with clear error.
```

### Step 3 — Hashing system

Implement:

```text
hashing.py
scripts/hash_hypotheses.py
```

Acceptance:

```text
Can register and validate hypothesis files.
Hash mismatch aborts.
```

### Step 4 — Data validation and normalization

Implement:

```text
data_loader.py
data_validator.py
normalizer.py
bar_builder.py
scripts/validate_data.py
scripts/normalize_data.py
scripts/build_bars.py
```

Acceptance:

```text
Can normalize example CSV.
Can build M5/M15/H1 bars.
Can produce data manifest.
```

### Step 5 — Indicators and candle patterns

Implement:

```text
indicators.py
candles.py
levels.py
```

Acceptance:

```text
Indicator tests pass.
No-lookahead swing tests pass.
```

### Step 6 — Costs, sizing, execution simulator

Implement:

```text
costs.py
sizing.py
execution.py
trades.py
```

Acceptance:

```text
Cost and sizing tests pass.
Simple simulated trade exits correctly.
```

### Step 7 — Strategy classes

Implement:

```text
strategies/base.py
strategies/trend_pullback.py
strategies/breakout_retest.py
strategies/range_mr.py
```

Acceptance:

```text
Strategies generate signals on synthetic data.
No strategy uses future bars.
```

### Step 8 — Backtester

Implement:

```text
backtester.py
scripts/run_phase0_matrix.py
```

Acceptance:

```text
Can run one synthetic cell end-to-end.
Outputs trades/equity/metrics CSV.
```

### Step 9 — Metrics and gates

Implement:

```text
metrics.py
gates.py
aggregate_results.py
```

Acceptance:

```text
Gate tests pass.
Metrics generated for cell outputs.
```

### Step 10 — Reports

Implement:

```text
reports.py
generate_verdict.py
```

Acceptance:

```text
Creates per-expert MD report and PHASE0_VERDICT.md.
```

### Step 11 — Decile, multisymbol, adversarial packet

Implement:

```text
run_decile_tests.py
run_multisymbol_checks.py
create_adversarial_packets.py
```

Acceptance:

```text
Outputs CSVs in correct schema.
Reports include pass/fail statuses.
```

### Step 12 — Passive spread logger

Implement:

```text
mt5/PassiveSpreadLogger_XAUUSD.mq5
mt5/README_SPREAD_LOGGER.md
scripts/analyze_spread_logs.py
```

Acceptance:

```text
MQL5 code contains no trading functions.
CSV schema matches spec.
Analyzer produces cost_model_measured.csv.
```

### Step 13 — Snapshot and final run-all

Implement:

```text
snapshot.py
generate_snapshot.py
run_all_phase0.py
```

Acceptance:

```text
run-all works on sample data.
Snapshot zip includes required outputs.
```

---

## 27. Sample Hypothesis Templates

### 27.1 `docs/hypothesis_trend_pullback.md`

```markdown
# Hypothesis: Trend Pullback Expert

Expert: Trend Pullback  
Hypothesis date: <YYYY-MM-DD>  
Hypothesis version: v1  
Author: <name>  
SHA256 after registration: <filled by script>

## Mechanical definition

Long:
- H1 EMA(50) > H1 EMA(200)
- H1 EMA(50) slope over 20 bars > 0
- M15 close within 0.5 × H1 ATR(14) of M15 EMA(21)
- M5 bullish engulfing or bullish pin bar
- Entry at next available quote after confirmation candle close
- Stop below last 10 M5 bars' pullback low by 0.1 × M15 ATR(14)
- Target 1.5R

Short: mirror logic.

## Expected behavior

Expected trade count per year: <N> ± 20%  
Expected cost-adjusted PF: <X> ± 0.3  
Expected losing-month percentage: <Y%> ± 10%  
Expected worst single month: <USD amount>  
Expected max consecutive zero-trade months: <Z>  
Expected R-multiple distribution: <description>

## Why this hypothesis should exist

<Write 2–3 sentences explaining what XAUUSD behavior this captures.>

## What would falsify it

<Write specific outcomes that reject the edge.>
```

### 27.2 `docs/hypothesis_breakout_retest.md`

```markdown
# Hypothesis: Breakout-Retest Expert

Expert: Breakout-Retest  
Hypothesis date: <YYYY-MM-DD>  
Hypothesis version: v1  
Author: <name>  
SHA256 after registration: <filled by script>

## Mechanical definition

Long:
- Level is previous completed daily high, previous completed weekly high, or confirmed M5 swing high with 4 bars on both sides
- M5 candle closes above level by at least 0.3 × M5 ATR(14)
- Price retests broken level within 20 M5 bars
- Retest candle does not close below level
- Next candle is bullish
- Buy stop above retest high by 1 point
- Stop below retest low by 0.1 × M5 ATR(14)
- Target 1.5R
- Pending order expires after 5 M5 bars

Short: mirror logic.

## Expected behavior

Expected trade count per year: <N> ± 20%  
Expected cost-adjusted PF: <X> ± 0.3  
Expected losing-month percentage: <Y%> ± 10%  
Expected worst single month: <USD amount>  
Expected max consecutive zero-trade months: <Z>  
Expected R-multiple distribution: <description>

## Why this hypothesis should exist

<Write 2–3 sentences explaining what XAUUSD behavior this captures.>

## What would falsify it

<Write specific outcomes that reject the edge.>
```

### 27.3 `docs/hypothesis_range_mr.md`

```markdown
# Hypothesis: Range Mean-Reversion Expert

Expert: Range Mean-Reversion  
Hypothesis date: <YYYY-MM-DD>  
Hypothesis version: v1  
Author: <name>  
SHA256 after registration: <filled by script>

## Mechanical definition

Long:
- H1 ADX(14) < 20 for last 20 completed H1 bars
- Last 50 M15 bars define upper/lower boundary
- At least 3 touches of upper boundary and 3 touches of lower boundary
- Range width >= 2 × M15 ATR(14)
- Price reaches lower boundary ± 0.2 × M15 ATR(14)
- M5 bullish pin bar confirms rejection
- Buy limit at lower boundary
- Stop below lower boundary by 0.3 × M15 ATR(14)
- Target opposite boundary
- Pending order expires after 6 M5 bars

Short: mirror logic.

## Expected behavior

Expected trade count per year: <N> ± 20%  
Expected cost-adjusted PF: <X> ± 0.3  
Expected losing-month percentage: <Y%> ± 10%  
Expected worst single month: <USD amount>  
Expected max consecutive zero-trade months: <Z>  
Expected R-multiple distribution: <description>

## Why this hypothesis should exist

<Write 2–3 sentences explaining what XAUUSD behavior this captures.>

## What would falsify it

<Write specific outcomes that reject the edge.>
```

---

## 28. Required Deliverables From Codex

When implementation is complete, the repository must include:

```text
1. Working Python package under src/phase0.
2. All scripts under scripts/.
3. Config files under config/.
4. Hypothesis templates under docs/.
5. Passive spread logger under mt5/.
6. Unit tests under tests/.
7. README.md.
8. No live-trading EA logic.
9. No OrderSend anywhere except possibly in a negative test string, preferably none.
10. A successful pytest run on synthetic test data.
11. Sample synthetic-data run producing reports.
```

---

## 29. Code Quality Requirements

### 29.1 Type hints

Use type hints for public functions.

### 29.2 Dataclasses

Use dataclasses for:

```text
Signal
TradePlan
Trade
BacktestConfig
CellConfig
GateResult
```

### 29.3 Clear errors

Error messages must include:

```text
Which file failed
Which row failed, if applicable
Which config value is invalid
How to fix it
```

### 29.4 Logging

Use Python `logging` module.

Write logs to:

```text
outputs/logs/phase0_run_{YYYYMMDD_HHMMSS}.log
```

### 29.5 No hidden state

Do not store important state only in memory. Results must be written to files.

---

## 30. Final Acceptance Criteria

Codex implementation is accepted only if all are true:

```text
[ ] Repository structure matches this spec.
[ ] `pytest` passes.
[ ] Hypothesis hash registration works.
[ ] Hash mismatch blocks backtests.
[ ] Data validator catches invalid bid/ask/spread rows.
[ ] Bar builder creates M5/M15/H1 bars with correct timestamp convention.
[ ] Indicator tests pass.
[ ] No-lookahead tests pass.
[ ] Strategy classes generate signals on synthetic data.
[ ] Backtester can run synthetic sample end-to-end.
[ ] Matrix runner can run all enabled experts if data exists.
[ ] Gate evaluator produces PASS/FAIL results.
[ ] Decile runner works.
[ ] Multisymbol runner works.
[ ] Adversarial packet generator works.
[ ] Report generator produces per-expert reports and consolidated verdict.
[ ] Snapshot generator works.
[ ] Passive spread logger MQL5 code contains no trading functions.
[ ] There is no `OrderSend` or `CTrade` usage in the Phase 0 codebase.
[ ] README gives clear instructions.
```

---

## 31. First Commands After Codex Completes

The human operator should run:

```bash
cd xauusd-phase0
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest
```

Then:

```bash
python scripts/hash_hypotheses.py --register
python scripts/validate_data.py --broker capital_com --symbol XAUUSD
python scripts/normalize_data.py --broker capital_com --symbol XAUUSD
python scripts/build_bars.py --broker capital_com --symbol XAUUSD --timeframes M1,M5,M15,H1,H4,D1
python scripts/run_phase0_matrix.py --expert all
python scripts/run_decile_tests.py --expert all
python scripts/run_multisymbol_checks.py --expert all
python scripts/create_adversarial_packets.py --expert all
python scripts/aggregate_results.py --expert all
python scripts/generate_verdict.py
python scripts/generate_snapshot.py
```

In parallel:

```text
Open MT5 demo account.
Attach mt5/PassiveSpreadLogger_XAUUSD.mq5 to XAUUSD chart.
Run continuously for 4 weeks.
Do not attach any trading EA to that chart.
Collect spread CSVs weekly.
Run scripts/analyze_spread_logs.py.
```

---

## 32. What Not To Do

Codex must not:

```text
Add live order placement.
Add MT5 trading functions.
Optimize strategy parameters.
Change definitions after results.
Auto-download unknown data without explicit instruction.
Silently patch missing data.
Hide failed gates.
Mark PENDING manual reviews as PASS.
Use current-day high/low as previous-day high/low.
Use future bars to confirm swing highs/lows before they are known.
Assume XAUUSD digits/point size without reading config.
Skip true-holdout guard.
Delete raw data.
```

---

## 33. Final Project Decision Logic

After Phase 0:

```text
If 3 experts pass:
    Proceed to Phase 1 dry-run Master EA shell with 3-expert v1 scope.

If 1–2 experts pass:
    Proceed to Phase 1 dry-run Master EA shell with reduced expert scope.
    Do not replace failed slots with untested experts.

If 0 experts pass:
    Stop.
    Do not start Phase 1.
    Research new candidate behaviors.
```

A failed Phase 0 is not a failure of the project. It is a successful prevention of wasted engineering effort.

---

## 34. Short Instruction Block for Codex

If Codex needs a concise task statement, use this:

```text
Build the Phase 0 statistical validation repository for the XAUUSD Master EA project. Do not build live trading logic. Implement data validation, normalization, bar building, indicators, three locked mechanical strategy simulators, an event-driven backtester, cost model, risk sizing, metrics, hard gate evaluator, decile tests, multisymbol checks, adversarial review packet generator, SHA256 hypothesis lock, report generator, snapshot generator, and passive MT5 spread logger. No OrderSend. No CTrade. No optimization. No look-ahead. All outputs must be deterministic, auditable, and saved as CSV/Markdown. Acceptance is pytest pass + synthetic end-to-end sample + passive spread logger with no trading functions.
```

---

**End of specification.**
