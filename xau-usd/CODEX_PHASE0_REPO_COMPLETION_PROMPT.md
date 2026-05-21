# Codex Prompt — Complete Missing Phase 0 Repository Work Before EA Coding

**Repository:** `maksoftwares/algo-trading-system`
**Project area:** `xau-usd/xauusd-phase0`
**Intended recipient:** Codex / coding agent
**Purpose:** bring the repository from bootstrap / partial implementation to Phase 0 execution-readiness without accidentally starting live EA coding.

---

## 0. Read this first

You are working on an XAUUSD algorithmic trading project. The project deliberately follows a **Phase-0-first** process.

The immediate task is **not** to build a live MT5 Expert Advisor. The immediate task is to complete the Phase 0 research/backtesting repository so the team can validate or reject the proposed strategy edges before any expert EA logic is written.

The Phase 0 repository must support:

```text
1. Pre-registered strategy hypotheses
2. SHA256 hypothesis locking
3. Historical data validation
4. Normalization and bar building
5. Mechanical strategy simulation
6. 9-cell matrix testing
7. Hard pass/fail gates
8. Decile persistence testing
9. Multi-symbol consistency testing
10. Adversarial review packets
11. Passive spread logging and spread analysis
12. Result manifests
13. Review bundle generation
14. Strict safety audit proving no live-trading code exists
```

The goal is to make the repository good enough that a reviewer can inspect the output and decide:

```text
Proceed to Phase 1 with approved experts
Proceed to Phase 1 with reduced scope
Stop because no expert edge survived Phase 0
```

All three outcomes are valid. Do not bias the implementation toward passing.

---

## 1. Non-negotiable constraints

### 1.1 Do not implement live trading

Do **not** add any live order placement, trade modification, or live position management code in Phase 0.

Forbidden in Phase 0:

```text
OrderSend
OrderSendAsync
CTrade
trade.Buy
trade.Sell
PositionOpen
PositionModify
PositionClose
OrderSendResult
MqlTradeRequest
MqlTradeResult
```

If these terms appear only inside documentation, comments, or safety-audit blocklists, the safety scanner must handle that correctly. The scanner should not fail merely because a README says “OrderSend is forbidden.” It should scan executable code separately from comments/docs or maintain an explicit allowlist for documentation files.

### 1.2 Do not tune strategy logic

Do **not** tune EMA periods, ATR multipliers, ADX thresholds, retest windows, stop multipliers, targets, time filters, session filters, or any other strategy parameters after seeing results.

The purpose of Phase 0 is not to find a profitable parameter set. The purpose is to test whether the pre-registered mechanical behavior has edge.

Forbidden behavior:

```text
Backtest fails → add filter
Backtest fails → change EMA period
Backtest fails → adjust ATR multiplier
Backtest fails → exclude a session
Backtest fails → exclude news after seeing losses
Backtest fails → modify range-touch definition to improve results
Backtest fails → remove outlier losses
Backtest passes only in one cell → call it good
```

Allowed behavior:

```text
Fix code bugs
Fix lookahead bias
Fix timestamp alignment bugs
Fix parser/schema bugs
Clarify ambiguous wording before final hypothesis lock
Add tests
Improve reporting
Improve validation and auditability
```

If a strategy hypothesis fails the gates, mark it failed. Do not rescue it with filters.

### 1.3 Do not touch the true holdout

The true holdout period is reserved for final pre-live review. The normal Phase 0 matrix, decile, and multi-symbol tests must not access it unless an explicit unlock file and explicit CLI flag are present.

Required behavior:

```text
If config/true_holdout_period.yaml exists:
    block all normal Phase 0 workflows from reading that date range
    write true_holdout_unlocked=false in all manifests
    require both:
        1. unlock file exists
        2. CLI flag explicitly passed
    before accessing holdout data
```

If any result touches true holdout without unlock, mark the result invalid.

### 1.4 Do not create Phase 1 EA files yet

Do **not** create the live MT5 Master EA implementation in this task.

Do not create:

```text
MasterEA.mq5
RiskManager.mqh
ExecutionGuard.mqh
RegimeRouter.mqh
PositionManager.mqh
MagicNumberAllocator.mqh
ExpertLifecycleManager.mqh
TrendPullbackExpert.mqh
BreakoutRetestExpert.mqh
RangeMRExpert.mqh
```

Those are Phase 1+ files. This task is Phase 0 only.

The only MQL5 file allowed in Phase 0 is a **passive** logger/exporter, such as:

```text
PassiveSpreadLogger.mq5
PassiveBarExporter.mq5
```

These files must not place, modify, or close trades.

---

## 2. Immediate repo state to assume

Assume the repository may already contain some of these files. Inspect first. Do not duplicate modules if they already exist.

Expected or intended area:

```text
xau-usd/xauusd-phase0/
```

Likely existing folders:

```text
config/
docs/
mt5/
outputs/
src/
scripts/
tests/
```

Your job is to fill the gaps, harden the existing scaffold, and produce a complete Phase 0 implementation.

If something already exists, extend or fix it. If something is missing, create it. If existing code conflicts with this document, preserve behavior only if it is safer and document the reason.

---

## 3. Priority summary

### P0 blockers — must be completed first

```text
1. Add missing reference/spec files or make this repo self-contained.
2. Fix SHA256 hypothesis locking design.
3. Add hypothesis completeness validator.
4. Block real Phase 0 runs if hypotheses are draft/unlocked/incomplete.
5. Fix 9-cell matrix semantics.
6. Protect true holdout from accidental access.
7. Clarify mechanical definitions before final locking.
8. Add robust safety audit.
9. Implement review-bundle generator.
10. Add test suite and CI coverage for all of the above.
```

### P1 implementation — Phase 0 research engine

```text
1. Data contract and schema validation
2. Raw-data normalization
3. Bar building for M1/M5/M15/H1/H4/D1
4. Indicator engine
5. Level detection
6. Strategy signal generation
7. Backtest simulator
8. Cost model
9. Position sizing
10. Metrics and hard gates
11. Matrix runner
12. Decile runner
13. Multi-symbol runner
14. Adversarial packet creator
15. Report generator
16. Snapshot generator
17. CLI workflow
```

### P2 improvements — useful but can follow P0/P1

```text
1. Intrabar ambiguity report for Breakout-Retest
2. Passive spread logger improvements
3. Spread analysis tooling
4. Synthetic sample-data generator
5. Additional statistical tests
6. Release artifact packaging
```

---

## 4. Required final repository structure

Target structure:

```text
xau-usd/xauusd-phase0/
├── README.md
├── CODEX_HANDOFF.md
├── pyproject.toml
├── requirements.txt
├── pytest.ini
├── .gitignore
│
├── config/
│   ├── phase0.yaml
│   ├── symbols.yaml
│   ├── cost_models.yaml
│   ├── broker_sources.yaml
│   └── true_holdout_period.yaml
│
├── docs/
│   ├── NO_TUNING_RULES.md
│   ├── PHASE0_KICKOFF_CHECKLIST.md
│   ├── PHASE0_DATA_MANIFEST_TEMPLATE.md
│   ├── PHASE0_REVIEW_BUNDLE_CONTENTS.md
│   ├── HYPOTHESIS_LOCKING.md
│   ├── TRUE_HOLDOUT_POLICY.md
│   ├── INTRABAR_AMBIGUITY_POLICY.md
│   ├── DATA_CONTRACTS.md
│   ├── STRATEGY_CODE_MAPPING.md
│   └── REPO_MISSING_ITEMS_STATUS.md
│
├── docs/hypotheses/
│   ├── hypothesis_trend_pullback.md
│   ├── hypothesis_breakout_retest.md
│   └── hypothesis_range_mr.md
│
├── reference/
│   ├── xauusd_phase0_codex_implementation_spec.md
│   ├── PHASE0_STATISTICAL_STUDY_SPEC.md
│   ├── PATH_TO_10.md
│   ├── PLAN_V01_REVIEW_FINDINGS.md
│   └── xauusd_master_ea_plan_v0_3_phase0_first_review_ready.md
│
├── data/
│   ├── raw/              # gitignored
│   ├── normalized/       # gitignored
│   ├── bars/             # gitignored
│   └── synthetic/        # committed small test fixtures allowed
│
├── mt5/
│   ├── PassiveSpreadLogger.mq5
│   ├── PassiveBarExporter.mq5          # optional
│   └── README_SPREAD_LOGGER.md
│
├── outputs/              # gitignored except .gitkeep and maybe templates
│   ├── hashes/
│   ├── manifests/
│   ├── reports/
│   ├── review_bundles/
│   ├── snapshots/
│   ├── trades/
│   ├── matrix/
│   ├── deciles/
│   ├── multisymbol/
│   ├── adversarial/
│   └── spread_logs/
│
├── scripts/
│   ├── run_phase0.sh
│   ├── run_phase0.ps1
│   ├── generate_synthetic_data.py
│   └── verify_real_artifacts.py
│
├── src/
│   └── phase0/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── constants.py
│       ├── paths.py
│       ├── safety.py
│       ├── hashing.py
│       ├── hypotheses.py
│       ├── data_contracts.py
│       ├── validation.py
│       ├── normalize.py
│       ├── bars.py
│       ├── indicators.py
│       ├── candles.py
│       ├── levels.py
│       ├── costs.py
│       ├── sizing.py
│       ├── trades.py
│       ├── execution.py
│       ├── backtester.py
│       ├── metrics.py
│       ├── gates.py
│       ├── matrix.py
│       ├── deciles.py
│       ├── multisymbol.py
│       ├── adversarial.py
│       ├── reports.py
│       ├── review_bundle.py
│       ├── snapshots.py
│       ├── spread_analysis.py
│       ├── workflow.py
│       └── strategies/
│           ├── __init__.py
│           ├── base.py
│           ├── trend_pullback.py
│           ├── breakout_retest.py
│           └── range_mr.py
│
└── tests/
    ├── test_imports.py
    ├── test_config.py
    ├── test_hypothesis_locking.py
    ├── test_hypothesis_completeness.py
    ├── test_true_holdout_guard.py
    ├── test_safety_audit.py
    ├── test_data_contracts.py
    ├── test_normalize.py
    ├── test_bars.py
    ├── test_indicators.py
    ├── test_candles.py
    ├── test_levels.py
    ├── test_costs.py
    ├── test_sizing.py
    ├── test_execution.py
    ├── test_strategies.py
    ├── test_backtester.py
    ├── test_metrics.py
    ├── test_gates.py
    ├── test_matrix.py
    ├── test_deciles.py
    ├── test_multisymbol.py
    ├── test_reports.py
    ├── test_review_bundle.py
    ├── test_spread_analysis.py
    └── test_workflow_synthetic.py
```

If the repo already uses a different but sensible structure, keep it, but ensure all required capabilities exist.

---

## 5. Reference/spec files

### 5.1 Problem

The bootstrap package may reference files such as:

```text
reference/xauusd_phase0_codex_implementation_spec.md
reference/PHASE0_STATISTICAL_STUDY_SPEC.md
reference/PATH_TO_10.md
reference/PLAN_V01_REVIEW_FINDINGS.md
```

but the reference folder may be missing.

### 5.2 Required action

Add a `reference/` folder.

If source reference documents are available, copy them into `reference/`.

If not available, create a `reference/README.md` saying exactly which files are missing and that the repository is operating from this prompt as the active implementation spec.

Add a CLI command:

```bash
python -m phase0.cli validate-reference
```

It should check:

```text
reference/ exists
key expected reference docs exist OR reference/README.md explains missing docs
CODEX_HANDOFF.md does not point to a nonexistent required file without warning
```

Do not block synthetic tests if references are missing, but do block final real-data Phase 0 verdict generation unless this status is explicitly documented.

---

## 6. Hypothesis locking

### 6.1 Problem

Do not hash a file and then insert that hash into the same file without normalization. That creates a self-hash problem: inserting the hash changes the file content, so the hash no longer matches.

### 6.2 Required design

Use external hash records.

Preferred approach:

```text
Hypothesis file contains no live hash field that gets rewritten.
Hash is stored externally in:
  outputs/hashes/hypothesis_hash_manifest.csv
  outputs/hashes/<expert>_v1.0.json
```

Each hash record must include:

```text
expert
hypothesis_file
hypothesis_version
sha256
hash_algorithm
normalized_content=false
registered_at_utc
git_commit
registered_by
file_size_bytes
line_count
status=LOCKED
```

If you decide to keep a hash line inside the hypothesis file, then hashing must explicitly normalize the file by excluding the hash line. Document that method in `docs/HYPOTHESIS_LOCKING.md`. External hash storage is simpler and preferred.

### 6.3 Required CLI commands

Implement:

```bash
python -m phase0.cli validate-hypotheses
python -m phase0.cli hash-hypotheses
python -m phase0.cli verify-hypothesis-hashes
```

Behavior:

```text
validate-hypotheses:
    fail if required files missing
    fail if status is DRAFT when running real-data workflows
    fail if any required field missing
    fail if any required field contains TBD, TODO, placeholder, [USER TO CONFIRM]
    fail if mechanical definitions are empty or ambiguous markers remain

hash-hypotheses:
    compute SHA256 over exact file bytes
    write manifest rows externally
    write one JSON per expert
    do not mutate hypothesis markdown files after hash is computed

verify-hypothesis-hashes:
    recompute exact file hashes
    compare to manifest
    fail if any mismatch
```

### 6.4 Required hypothesis fields

Every hypothesis file must include:

```text
Expert name
Hypothesis version
Hypothesis date
Status: LOCKED or DRAFT
Author / owner
Mechanical definition
Long setup
Short setup
Entry type
Stop logic
Target logic
Risk model
Expected trade count per year
Expected cost-adjusted PF
Expected losing-month percentage
Expected worst single month
Expected max consecutive zero-trade months
Expected R-multiple distribution
Underlying XAU behavior thesis
Failure modes
Falsification criteria
Forbidden after registration
Allowed implementation bug fixes
Hard gates override expected-value bands
Code mapping placeholder
```

Add this sentence to every hypothesis file:

```text
Hypothesis-match bands are descriptive only. Hard gates override expected-value bands. Any result below a configured hard gate is a Phase 0 failure even if it falls inside the expected-value band.
```

---

## 7. Strategy-definition clarification before locking

Before final hypothesis lock, update the docs and implementation to remove ambiguous wording.

### 7.1 Breakout-Retest hold condition

Replace ambiguous wording like:

```text
M5 low does not close below the broken level
```

with precise long/short logic:

```text
Long retest hold:
    Retest candle may wick below the broken level.
    Retest candle close must remain above the broken level.
    Retest candle low may pierce the level by no more than configured tolerance points, if tolerance is declared before lock.

Short retest hold:
    Retest candle may wick above the broken level.
    Retest candle close must remain below the broken level.
    Retest candle high may pierce the level by no more than configured tolerance points, if tolerance is declared before lock.
```

If no tolerance is configured, use close-only hold logic.

### 7.2 M5 swing level timing

If a swing high/low uses prior and subsequent bars, make lookahead prevention explicit.

Required rule:

```text
A swing level requiring 4 subsequent bars becomes eligible only after those 4 subsequent bars have closed.
The strategy may not use that level before confirmation time.
```

Add tests proving there is no lookahead.

### 7.3 Range MR distinct-touch rule

Do not count adjacent candles as independent touches.

Required rule:

```text
Upper-boundary touches must be separated by at least 3 M15 bars.
Lower-boundary touches must be separated by at least 3 M15 bars.
A candle cannot count as both upper and lower touch.
```

If the current hypothesis uses another separation value, keep it only if it is explicitly locked before testing.

### 7.4 Range boundary construction

If using median of highs/lows near extremes, document exact algorithm:

```text
range_window_bars = 50 M15 bars
atr = ATR(14, M15)
upper_candidates = highs within X * ATR of absolute window high
lower_candidates = lows within X * ATR of absolute window low
upper_boundary = median(upper_candidates)
lower_boundary = median(lower_candidates)
range_width = upper_boundary - lower_boundary
range_valid if range_width >= 2 * ATR(14, M15)
```

Whatever rule is chosen must be implemented exactly and tested.

---

## 8. 9-cell matrix semantics

### 8.1 Problem

Avoid ambiguity between:

```text
3 time windows × 3 tick sources × 3 cost models = 27 cells
```

and the intended Phase 0 design:

```text
3 paired time/source windows × 3 cost models = 9 cells
```

### 8.2 Required implementation

Implement the 9-cell matrix exactly as:

```text
Cell 1: 2016–2018, Capital.com, best-case spread
Cell 2: 2016–2018, Capital.com, median spread
Cell 3: 2016–2018, Capital.com, P95 spread
Cell 4: 2019–2021, Pepperstone, best-case spread
Cell 5: 2019–2021, Pepperstone, median spread
Cell 6: 2019–2021, Pepperstone, P95 spread
Cell 7: 2022–2024, Dukascopy, best-case spread
Cell 8: 2022–2024, Dukascopy, median spread
Cell 9: 2022–2024, Dukascopy, P95 spread
```

The config may support an optional 27-cell extended stress matrix later, but the default Phase 0 gate is the 9-cell matrix above.

Add tests:

```text
test_matrix_default_has_9_cells
test_matrix_cell_ids_are_stable
test_matrix_does_not_expand_to_27_by_default
```

---

## 9. True holdout protection

### 9.1 Required config behavior

If `config/true_holdout_period.yaml` reserves:

```text
2025-07-01 through 2025-12-31
```

then normal Phase 0 runs must end before the holdout begins unless explicitly unlocked.

If existing config uses:

```text
decile_end: 2025-12-31
multisymbol_end: 2025-12-31
```

change it to:

```text
decile_end: 2025-06-30T23:59:59Z
multisymbol_end: 2025-06-30T23:59:59Z
```

or implement a hard exclusion that automatically truncates normal runs before true holdout.

### 9.2 Required CLI behavior

Every workflow that reads data must call a holdout guard.

```text
If date range overlaps holdout and unlock not provided:
    fail with clear error
    write attempted access to logs
    do not produce result artifacts marked PASS
```

Unlock requires both:

```text
--unlock-true-holdout
```

and a file such as:

```text
outputs/manifests/TRUE_HOLDOUT_UNLOCK_APPROVAL.md
```

The unlock file must contain:

```text
approval_date_utc
approved_by
reason
commit_hash
```

### 9.3 Manifest fields

Every result manifest must include:

```text
true_holdout_period_start
true_holdout_period_end
true_holdout_unlocked
true_holdout_unlock_file
true_holdout_overlap_detected
```

---

## 10. Safety audit

### 10.1 Required command

Implement:

```bash
python -m phase0.cli audit-safety
```

### 10.2 Required behavior

The audit must scan executable source code for forbidden trading calls.

It must:

```text
scan .py, .mq5, .mqh, .mq4 files
ignore docs unless docs are explicitly configured as executable
ignore comments or handle known documentation allowlist
report file path, line number, forbidden token, and context
fail if forbidden live-trading code appears
pass if forbidden terms appear only in safety blocklists or docs explaining constraints
```

### 10.3 Forbidden tokens

At minimum:

```text
OrderSend
OrderSendAsync
CTrade
trade.Buy
trade.Sell
trade.PositionOpen
PositionOpen
PositionModify
PositionClose
MqlTradeRequest
MqlTradeResult
OrderCheck
```

If a passive MQL5 logger requires benign functions that resemble trading APIs, document why they are safe.

---

## 11. Data contracts

Create `docs/DATA_CONTRACTS.md` and implement schema validation.

### 11.1 Normalized tick schema

Required columns:

```text
timestamp_utc: ISO-8601 or pandas-compatible UTC timestamp
broker_time: optional string/datetime
symbol: string
bid: float
ask: float
spread: float, ask - bid
source: string
```

Optional columns:

```text
volume
tick_volume
server
account
raw_file
```

Validation:

```text
ask >= bid
timestamp_utc monotonic per symbol/source
no duplicate timestamp/source/symbol rows unless explicitly allowed
spread >= 0
symbol not empty
source not empty
```

### 11.2 Bar schema

Required OHLCV columns:

```text
timestamp_utc
symbol
source
timeframe
open
high
low
close
tick_volume
spread_median
spread_p95
```

Validation:

```text
high >= max(open, close, low)
low <= min(open, close, high)
timestamps align to timeframe boundaries
no missing required columns
bar count sufficient for requested run
```

### 11.3 Trade schema

Every simulated trade row must include:

```text
trade_id
expert
strategy_version
cell_id
symbol
source
cost_model
entry_time_utc
exit_time_utc
direction
entry_type
entry_price
stop_loss
take_profit
exit_price
exit_reason
risk_usd
position_size
pnl_usd
pnl_R
spread_cost_usd
commission_usd
slippage_usd
holding_minutes
setup_reason
invalidation_level
hypothesis_hash
config_hash
data_manifest_hash
cost_model_hash
```

---

## 12. Config validation

Implement:

```bash
python -m phase0.cli validate-config
```

It must validate:

```text
all required config files exist
YAML parses
symbol definitions exist for XAUUSD, EURUSD, USDJPY
cost models include best, median, p95
phase0 matrix has exactly 9 default cells
true holdout exists and is protected
paths are valid
risk-per-trade is a single value, not a range
```

Preferred Phase 0 fixed values:

```text
initial_equity_usd: 10000
risk_per_trade: 0.005
one_trade_at_a_time: true
ambiguous_intrabar_policy: adverse_first
matrix_default_cells: 9
```

---

## 13. Data processing implementation

### 13.1 Normalize raw data

Implement:

```bash
python -m phase0.cli normalize-data --source capital --symbol XAUUSD
```

Support CSV input formats from:

```text
Capital.com MT5 exports
Dukascopy CSV
Pepperstone or third-party tick/bar exports
```

If exact raw format is unknown, implement flexible column mapping in `config/broker_sources.yaml`.

### 13.2 Build bars

Implement:

```bash
python -m phase0.cli build-bars --symbol XAUUSD --source capital
```

Required timeframes:

```text
M1, M5, M15, H1, H4, D1
```

For tick data:

```text
open = first mid or bid/ask-derived price
high = max price
low = min price
close = last price
spread_median = median ask-bid within bar
spread_p95 = p95 ask-bid within bar
```

For broker bar exports:

```text
preserve OHLC as supplied
attach spread if available
otherwise attach cost model spread later
```

Add `validate-data` command:

```bash
python -m phase0.cli validate-data
```

It must produce:

```text
outputs/manifests/data_readiness_report.md
outputs/manifests/data_manifest.csv
```

Include:

```text
symbol
source
timeframe
start_date
end_date
row_count
missing_bars
largest_gap
has_required_range
true_holdout_overlap
```

---

## 14. Indicator engine

Implement indicator functions with tests:

```text
EMA(n)
ATR(14)
ADX(14)
Candle body size
Upper wick size
Lower wick size
Bullish engulfing
Bearish engulfing
Bullish pin bar
Bearish pin bar
Swing high/low with delayed eligibility
```

Rules:

```text
No lookahead.
Indicator values at bar T may only use data up to bar T close.
If a pattern requires confirmation after future bars, level becomes eligible only after confirmation bars close.
```

Add tests with small deterministic fixtures.

---

## 15. Strategy implementation

Implement three strategies as mechanical simulators, not live EAs.

Required files:

```text
src/phase0/strategies/base.py
src/phase0/strategies/trend_pullback.py
src/phase0/strategies/breakout_retest.py
src/phase0/strategies/range_mr.py
```

### 15.1 Base interface

Create a base interface such as:

```python
class Strategy(Protocol):
    name: str
    version: str

    def generate_signals(self, market_data: MarketData, config: Phase0Config) -> list[Signal]:
        ...
```

Signal fields:

```text
strategy
strategy_version
symbol
time_utc
direction
entry_type
entry_price
stop_loss
take_profit
invalidation_level
setup_reason
metadata
```

### 15.2 Trend Pullback

Implement the locked draft logic unless the finalized hypothesis says otherwise.

Starting long logic:

```text
H1 EMA(50) > EMA(200)
H1 EMA(50) slope over last 20 bars > 0
M15 price retraces to within 0.5 × H1 ATR(14) of M15 EMA(21)
M5 bullish engulfing OR bullish pin bar with lower wick ≥ 2 × body
Entry at close of confirmation candle
Stop = pullback low − 0.1 × ATR(14, M15)
Target = 1.5R
```

Short logic mirrors long logic.

No session/news/spread filters in Phase 0 unless explicitly locked in hypothesis.

### 15.3 Breakout-Retest

Starting long logic:

```text
Level = previous day high, weekly high, or confirmed M5 swing high
Break = M5 close > level by ≥ 0.3 × ATR(14, M5)
Retest = price returns to within 5 points of broken level within 20 M5 bars after break
Hold = retest candle close remains above broken level
Confirmation = bullish M5 candle after retest
Entry = buy stop above retest high
Stop = retest low − 0.1 × ATR(14, M5)
Target = 1.5R
```

Short logic mirrors long logic.

Swing levels must not be available until fully confirmed.

Add an intrabar ambiguity flag to any trade where entry/SL/TP ordering inside a bar cannot be known.

### 15.4 Range Mean-Reversion

Starting long logic:

```text
H1 ADX(14) < 20 for last 20 H1 bars
Within last 50 M15 bars:
    at least 3 distinct upper-boundary touches
    at least 3 distinct lower-boundary touches
    touches separated by at least 3 M15 bars
Range width ≥ 2 × ATR(14, M15)
Price reaches lower boundary ± 0.2 × ATR(14, M15)
Confirmation = bullish rejection candle with lower wick ≥ 2 × body
Entry = limit at boundary
Stop = range low − 0.3 × ATR(14, M15)
Target = opposite range boundary
```

Short logic mirrors long logic.

---

## 16. Backtester implementation

Implement a deterministic, auditable bar-based backtester suitable for Phase 0.

### 16.1 Required assumptions

```text
initial equity: $10,000
risk per trade: 0.50% fixed in Phase 0
one open position at a time per expert/cell
no scaling
no trailing
no break-even unless locked in Phase 0 hypothesis
cost model applied on entry/exit
slippage applied according to selected cost model
ambiguous intrabar policy: adverse_first
```

### 16.2 Intrabar policy

If a bar contains both stop-loss and take-profit after entry and ordering cannot be known:

```text
adverse_first = assume the stop-loss happened first
```

Log:

```text
intrabar_ambiguous = true
intrabar_policy = adverse_first
```

### 16.3 Execution simulation

Support:

```text
market entry at bar close
limit entry
stop entry
```

For stop/limit entries, use conservative logic.

If a pending order and exit would occur inside the same bar and ordering cannot be known, mark as ambiguous and use adverse-first.

### 16.4 Required output

For every run, write:

```text
outputs/trades/<expert>_<cell_id>_trades.csv
outputs/matrix/<expert>_<cell_id>_summary.json
outputs/matrix/<expert>_<cell_id>_equity.csv
```

---

## 17. Cost model

Implement cost model parsing from `config/cost_models.yaml`.

Required modes:

```text
best
median
p95
```

Each cost model should support:

```text
spread_points
commission_per_lot
slippage_points
point_value or tick value if needed
```

Phase 0 approval must use P95-cost gates.

If measured spread data exists, allow:

```text
cost_model_source = measured
```

Otherwise label:

```text
cost_model_source = provisional
```

Write cost model hash into every result manifest.

---

## 18. Position sizing

Implement risk-based sizing:

```text
risk_money = equity * risk_per_trade
stop_distance = abs(entry_price - stop_loss)
position_size = risk_money / monetary_value_of_stop_distance
```

Because CFDs/broker contract specs vary, do not hardcode blindly. Use symbol config:

```yaml
contract_size:
point:
tick_value:
min_lot:
lot_step:
max_lot:
```

Round down to broker lot step.

If sizing cannot be computed safely, fail the run rather than guessing.

---

## 19. Metrics and gates

### 19.1 Required metrics

Compute per cell:

```text
trade_count
win_rate
profit_factor
total_return_pct
total_pnl_usd
avg_trade_R
max_drawdown_pct
max_drawdown_usd
worst_month_usd
best_month_usd
losing_month_pct
max_consecutive_zero_trade_months
max_consecutive_losing_months
largest_single_trade_pct_of_pnl
top5_trades_pct_of_pnl
```

### 19.2 Hard gates

Implement exact gate evaluation:

```text
Gate 1 — Multi-cell survival:
    cost-adjusted PF ≥ 1.30 in at least 7 of 9 cells

Gate 2 — Sample size:
    trade_count ≥ 40 in every cell

Gate 3 — No catastrophic failure:
    max_drawdown_pct ≤ 30% in every cell
    total_return_pct ≥ -25% in every cell

Gate 4 — Concentration:
    largest_single_trade_pct_of_pnl ≤ 10% in every cell
    top5_trades_pct_of_pnl ≤ 40% in every cell

Gate 5 — Activity:
    max_consecutive_zero_trade_months ≤ 3 in every cell

Gate 6 — Cost sensitivity:
    for each time window:
        P95_cost_PF / best_case_PF ≥ 0.50
```

Each gate result must include:

```text
gate_name
status PASS/FAIL
threshold
observed_value
explanation
failed_cells
```

Never output only PASS/FAIL without observed values.

---

## 20. Matrix runner

Implement:

```bash
python -m phase0.cli run-matrix --expert trend_pullback
python -m phase0.cli run-matrix --expert breakout_retest
python -m phase0.cli run-matrix --expert range_mr
python -m phase0.cli run-matrix --all
```

Pre-run checks:

```text
config valid
hypotheses valid and locked
hypothesis hashes verified
required data present
true holdout not touched
safety audit passed
```

Outputs:

```text
outputs/matrix/<expert>_matrix_results.csv
outputs/matrix/<expert>_gate_summary.json
outputs/reports/phase0_<expert>_matrix.md
```

If hypotheses are DRAFT or UNLOCKED, real-data matrix must fail.

Allow synthetic demo workflow with draft hypotheses only if flag is explicit:

```bash
--synthetic-ok
```

---

## 21. Decile test

Implement:

```bash
python -m phase0.cli run-deciles --expert breakout_retest
```

Use full non-holdout 2016-01-01 to 2025-06-30 Capital.com data unless config says otherwise.

Acceptance:

```text
PF > 1.0 in at least 8 of 10 deciles
No decile PF > 2.0 × median PF
No decile trade count < 10
```

Outputs:

```text
outputs/deciles/<expert>_decile_results.csv
outputs/reports/phase0_<expert>_deciles.md
```

---

## 22. Multi-symbol check

Implement:

```bash
python -m phase0.cli run-multisymbol --expert breakout_retest
```

Run identical mechanical logic on:

```text
EURUSD
USDJPY
```

Do not change parameters.

Acceptance:

```text
EURUSD PF ≥ 0.90
USDJPY PF ≥ 0.90
```

If either is below 0.70, result should be:

```text
FAIL unless XAU-specific mechanism is documented
```

Outputs:

```text
outputs/multisymbol/<expert>_multisymbol_results.csv
outputs/reports/phase0_<expert>_multisymbol.md
```

---

## 23. Adversarial review packet

Implement:

```bash
python -m phase0.cli create-adversarial-packets --expert breakout_retest
```

The tool should collect losing trades and create a review file.

Output file:

```text
outputs/adversarial/<expert>_adversarial_packet.csv
outputs/adversarial/<expert>_adversarial_review.md
```

CSV fields:

```text
trade_id
expert
cell_id
entry_time_utc
exit_time_utc
symbol
source
direction
entry_price
exit_price
pnl_R
setup_reason
chart_context_fields
review_classification
review_notes
```

Allowed classifications:

```text
valid_loss
router_opportunity
logic_gap
data_issue
execution_ambiguity
```

Add a scoring command:

```bash
python -m phase0.cli score-adversarial --expert breakout_retest
```

Acceptance:

```text
logic_gap_pct ≤ 25% of losing trades
```

Do not auto-classify subjective review as PASS. Human annotation is required.

If unreviewed:

```text
Final verdict = PENDING_MANUAL_REVIEW
```

---

## 24. Breakout-Retest intrabar ambiguity report

Implement:

```bash
python -m phase0.cli intrabar-report --expert breakout_retest
```

Report:

```text
number of trades with intrabar ambiguity
percentage of trades ambiguous
number where adverse-first changed outcome
PF under adverse-first
PF under neutral assumption, if implemented
PF under optimistic assumption, if implemented
list of top ambiguous trades by P&L impact
```

Output:

```text
outputs/reports/breakout_retest_intrabar_ambiguity_report.md
```

If Breakout-Retest only passes under optimistic assumptions, mark fragile.

---

## 25. Report generation

Implement:

```bash
python -m phase0.cli generate-report --expert breakout_retest
python -m phase0.cli generate-verdict
```

### 25.1 Per-expert report

Required file:

```text
outputs/reports/phase0_<expert>_results.md
```

Must include:

```text
Hypothesis file
Hypothesis hash at registration
Hypothesis hash at result writing
Config hash
Data manifest hash
Cost model hash
Strategy version
9-cell matrix table
Gate summary with observed values
Decile table
Adversarial status
Multi-symbol table
Hypothesis-vs-reality table
Intrabar ambiguity summary if relevant
Final expert verdict
Reason if failed
```

### 25.2 Consolidated verdict

Required file:

```text
outputs/reports/PHASE0_VERDICT.md
```

Final status values:

```text
PASS
FAIL
PENDING_MANUAL_REVIEW
INVALID_PRE_REGISTRATION
INVALID_HOLDOUT_LEAK
INSUFFICIENT_DATA
```

Do not use vague statuses like “almost pass.”

Decision tree:

```text
3 experts PASS:
    proceed to Phase 1 with 3-expert v1

1–2 experts PASS:
    proceed to Phase 1 with reduced v1

0 experts PASS:
    stop; do not begin Phase 1

Any expert PENDING_MANUAL_REVIEW:
    not approved until reviewed

Any expert INVALID_PRE_REGISTRATION:
    previous results are exploratory only; re-run required
```

---

## 26. Review bundle generator

Implement:

```bash
python -m phase0.cli create-review-bundle
```

Create:

```text
outputs/review_bundles/PHASE0_REVIEW_BUNDLE_<timestamp>_<commit>.zip
```

Bundle contents:

```text
docs/hypotheses/*.md
outputs/hashes/hypothesis_hash_manifest.csv
outputs/manifests/data_manifest.csv
outputs/manifests/data_readiness_report.md
outputs/manifests/config_manifest.json
outputs/matrix/*_matrix_results.csv
outputs/deciles/*_decile_results.csv
outputs/multisymbol/*_multisymbol_results.csv
outputs/adversarial/*_adversarial_review.md
outputs/reports/phase0_*_results.md
outputs/reports/PHASE0_VERDICT.md
outputs/reports/*intrabar*ambiguity*.md
outputs/snapshots/*snapshot*.json
config/*.yaml
```

If raw data cannot be included, do not include it. But include the data manifest.

Add bundle manifest:

```text
outputs/review_bundles/manifest.json
```

with:

```text
git_commit
created_at_utc
files
sha256 for each file
true_holdout_status
final_verdict
```

---

## 27. Real-artifact verifier

Implement:

```bash
python -m phase0.cli verify-real-artifacts
```

It should verify:

```text
hypothesis files contain no TBD/TODO/placeholders
hypotheses are LOCKED
hashes match
config hash exists
result manifest exists
PHASE0_VERDICT.md exists
adversarial review exists for any expert not failed before adversarial stage
true holdout status is explicit
approved experts have PASS, not PENDING
rejected experts are not marked buildable
review bundle can be created
```

If any check fails, print exact missing file or failed field.

---

## 28. Passive spread logger improvements

If `mt5/PassiveSpreadLogger.mq5` exists, improve it. If missing, create it.

Required log columns:

```text
broker_time
trade_server_time
gmt_time
local_time
tick_time
tick_time_msc
seconds_since_tick
account
server
symbol
bid
ask
spread_price
spread_points
point
digits
session_label
is_rollover_window
```

Required behavior:

```text
No trading functions
Timer-based logging
Append to daily CSV
Filename sanitizes server and symbol
Dashboard label says “rows written this session” if existing rows are not counted
```

Create or update:

```text
mt5/README_SPREAD_LOGGER.md
```

Include install instructions, expected CSV path, and how to analyze logs.

Implement spread analysis:

```bash
python -m phase0.cli analyze-spreads --input outputs/spread_logs/
```

Outputs:

```text
outputs/reports/spread_analysis.md
outputs/reports/cost_model_measured.csv
```

Analysis should include:

```text
median spread by hour
P95 spread by hour
median spread by day of week
P95 spread by day of week
rollover spread distribution
max observed spread per session
news-window spread stats if news calendar markers exist
```

---

## 29. Snapshot generator

Implement:

```bash
python -m phase0.cli generate-snapshot
```

Snapshot file:

```text
outputs/snapshots/phase0_snapshot_<timestamp>_<commit>.json
```

Fields:

```text
git_commit
created_at_utc
python_version
package_version
config_hash
hypothesis_hashes
data_manifest_hash
cost_model_hash
true_holdout_status
safety_audit_status
matrix_status
decile_status
multisymbol_status
adversarial_status
final_verdict
```

---

## 30. CLI command list

At minimum, implement these commands:

```bash
python -m phase0.cli validate-reference
python -m phase0.cli validate-config
python -m phase0.cli validate-hypotheses
python -m phase0.cli hash-hypotheses
python -m phase0.cli verify-hypothesis-hashes
python -m phase0.cli audit-safety
python -m phase0.cli validate-data
python -m phase0.cli normalize-data
python -m phase0.cli build-bars
python -m phase0.cli run-matrix
python -m phase0.cli run-deciles
python -m phase0.cli run-multisymbol
python -m phase0.cli create-adversarial-packets
python -m phase0.cli score-adversarial
python -m phase0.cli intrabar-report
python -m phase0.cli generate-report
python -m phase0.cli generate-verdict
python -m phase0.cli create-review-bundle
python -m phase0.cli verify-real-artifacts
python -m phase0.cli generate-snapshot
python -m phase0.cli run-all
```

`run-all` should execute safe Phase 0 workflow in this order:

```text
validate-reference
validate-config
audit-safety
validate-hypotheses
verify-hypothesis-hashes
validate-data
build-bars if needed
run-matrix for each expert
run-deciles for eligible experts
run-multisymbol for eligible experts
create-adversarial-packets for eligible experts
generate-report for each expert
generate-verdict
generate-snapshot
create-review-bundle
verify-real-artifacts
```

Do not automatically mark adversarial review PASS without human review.

---

## 31. CI requirements

Add or update GitHub Actions workflow:

```text
.github/workflows/phase0.yml
```

It should run on push and PR:

```bash
python -m pip install -e .[dev]
python -m phase0.cli validate-config
python -m phase0.cli audit-safety
pytest -q
python -m phase0.cli generate-snapshot --synthetic-ok
```

CI should use synthetic fixtures only. It should not require private raw broker data.

Add artifact upload for synthetic snapshot and test reports if useful.

---

## 32. Tests required

Tests must include:

```text
import/package tests
config validation tests
hypothesis completeness tests
SHA256 locking tests
hash mismatch tests
true holdout guard tests
safety audit tests, including forbidden terms in docs/comments
bar-building tests
indicator tests
lookahead-prevention tests
strategy signal tests
backtester deterministic tests
intrabar adverse-first tests
cost model tests
position sizing tests
metric tests
gate PASS/FAIL tests
matrix exactly-9-cell tests
decile tests
multisymbol tests
adversarial packet tests
review bundle tests
real artifact verifier tests
synthetic end-to-end workflow test
```

Minimum acceptance:

```text
pytest -q passes
safety audit passes
synthetic workflow completes
review bundle generation works on synthetic outputs
```

---

## 33. Documentation updates

Update README and CODEX handoff so they are accurate after implementation.

README must state:

```text
This is Phase 0 only.
No live trading code exists.
No EA expert coding begins until Phase 0 verdict approves at least one expert.
How to install.
How to run synthetic workflow.
How to run real workflow after data and locked hypotheses.
How to create review bundle.
Where outputs are written.
```

Add `docs/REPO_MISSING_ITEMS_STATUS.md` with a table:

```text
Item
Status: DONE / PARTIAL / BLOCKED
File(s)
Notes
```

This document should make it easy for the reviewer to see what was fixed.

---

## 34. Do not hide uncertainty

If data is missing, say so.

If a command cannot complete because raw broker data is absent, fail gracefully and explain:

```text
INSUFFICIENT_DATA: missing XAUUSD Dukascopy M5 bars for 2022-2024
```

If hypotheses are not locked, say:

```text
INVALID_PRE_REGISTRATION: hypotheses are draft or hash manifest missing
```

If adversarial review is not done, say:

```text
PENDING_MANUAL_REVIEW: adversarial packet generated but not scored
```

Do not silently treat incomplete workflow as PASS.

---

## 35. Implementation order for Codex

Work in this order:

```text
1. Inspect repository tree and summarize existing implementation.
2. Create/update reference and documentation files.
3. Implement config loader and validation.
4. Implement hypothesis validator and external SHA256 locking.
5. Implement true holdout guard.
6. Implement safety audit.
7. Implement data contracts and synthetic fixtures.
8. Implement indicators, candles, and level detection.
9. Implement strategy classes.
10. Implement backtester, execution, costs, and sizing.
11. Implement metrics and hard gates.
12. Implement matrix, decile, multisymbol runners.
13. Implement adversarial packet generator and scorer.
14. Implement report, verdict, snapshot, and review bundle generation.
15. Improve PassiveSpreadLogger.mq5 and add spread analysis.
16. Add tests.
17. Add CI.
18. Run full synthetic workflow.
19. Produce final completion summary.
```

Do not skip directly to strategy code before the validation/hashing/safety infrastructure exists.

---

## 36. Final response required from Codex

When done, respond with:

```text
Summary of work completed
Files added
Files modified
Commands run
Test results
Safety audit result
Synthetic workflow result
Unresolved blockers
Whether real-data Phase 0 can run now
Whether Phase 1 EA coding is still blocked
```

Expected final status should usually be:

```text
Phase 0 repository implementation: READY FOR DATA + LOCKED HYPOTHESES
Phase 1 EA coding: STILL BLOCKED UNTIL PHASE0_VERDICT PASS
```

If the final status is different, explain exactly why.

---

## 37. Acceptance checklist

The work is acceptable only when all of these are true:

```text
[ ] No live trading code added.
[ ] Safety audit passes.
[ ] Hypothesis completeness validator exists.
[ ] Hashing uses external manifest or documented normalized hashing.
[ ] Real-data runs are blocked if hypotheses are draft/unlocked.
[ ] True holdout guard exists and is tested.
[ ] Default matrix is exactly 9 cells.
[ ] Phase 0 hard gates are implemented with observed values.
[ ] Decile test exists.
[ ] Multi-symbol test exists.
[ ] Adversarial packet generator exists.
[ ] Intrabar ambiguity report exists for Breakout-Retest.
[ ] Review bundle generator exists.
[ ] Real-artifact verifier exists.
[ ] Passive spread logger is passive and improved.
[ ] Synthetic end-to-end workflow passes.
[ ] CI runs tests and safety audit.
[ ] README and CODEX_HANDOFF are accurate.
[ ] `docs/REPO_MISSING_ITEMS_STATUS.md` documents fixed and remaining items.
```

Do not mark this task complete until the checklist is satisfied or every unfinished item is clearly marked BLOCKED with a reason.
