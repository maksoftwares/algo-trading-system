# A1 XAU R6 Market-Only Native-Parity Acquisition Preregistration

**Phase:** `R6-NP1_MARKET_ONLY_NATIVE_PARITY_AND_CONTRACT_EVIDENCE_ACQUISITION`
**Commit cell:** `NP1-A` acquisition locks only
**Date:** `2026-07-12`
**Status before evidence:** `R6_C2_NATIVE_PARITY_EVIDENCE_MISSING`
**Historical boundary:** all observations through `2026-06-30` remain `DEVELOPMENT_DATA`
**Deployment status:** `NO_GO_RESEARCH_ONLY`

## 1. Purpose and authority

NP1 acquires only the missing market-only native evidence required before R6-C2R5 can resume:

1. native Router V1 indicators and states from the pinned `d5134057` lineage;
2. the causal H1/H4/D1 bars supporting each native decision;
3. a fresh account/symbol contract snapshot;
4. direct read-only `OrderCalcProfit` probes;
5. function-level source-equivalence proof;
6. zero-order, zero-deal, and zero-position proof.

Controlling directions:

- `A1_XAU_R6_NATIVE_PARITY_EVIDENCE_ACQUISITION_DIRECTION_2026_07_12.md`, SHA256 `a2d10661e58e95c516291b7e1d9b07b8b59904b94cff8474e28b16d569f0c1ca`;
- `A1_XAU_INDEPENDENT_SPECIALIST_PRIMARY_DIRECTION_2026_07_12.md`, SHA256 `c68a669f160b7469f8204101d05d38c36cf46f0501ca1f11c77ff3f91659b9af`;
- IS1-A2 exact-commit approval `A1_XAU_IS1A2_FAIL_CLOSED_GOVERNANCE_REVIEW_CD40A818_2026_07_12.md`, SHA256 `e7bb6e572120e4092c4e3868a9381d0c49ff708f367ad1d87a2a1c9c1b4ed0da`.

NP1 does not produce an R6 opportunity, census, trade, or performance result.

## 2. Frozen three-commit sequence

The commits are mandatory and separate:

```text
NP1-A: the four lock artifacts only
NP1-B: oracle, builder, runner, verifier, and four tests only
NP1-C: exact evidence directory only; no code or lock changes
```

NP1-A adds only this preregistration, the source contract, the output schema, and their lock manifest. NP1-A adds no Python, test, MQ5/MQH, EX5, compile log, tester INI, MT5 output, evidence row, or census row. NP1-B and NP1-C each require separate exact-commit review.

## 3. Pinned native source

The authorized generated oracle name is:

```text
A1XauR6MarketOnlyNativeParityOracle.mq5
```

Its sole Router authority is:

```text
path: xau-usd/xauusd-phase1/mt5/Experts/A1XauM5MomentumContinuationExecutor.mq5
commit: d51340574d90a39fe0032e54e4a8252370c19058
Git blob: d59338facaa01032a47c71186e64e1ba9f1dba8f
```

The NP1-B builder must extract the locked enum/functions and their transitive pure dependencies with balanced-brace parsing and copy each raw block byte-for-byte. Hand transcription is prohibited. A missing, renamed, or ambiguously overloaded block stops with `SOURCE_CONTRACT_AMENDMENT_REQUIRED`.

The generated wrapper may contain only fixed inputs, logging, Strategy Tester lifecycle handlers, new-H4-boundary detection, market-bar export, contract export, read-only `OrderCalcProfit` probes, and source/evidence assertions. It may not contain a trade library, order request, order send, position management, or history-order/deal processing surface.

## 4. Fixed Router inputs

```text
InpTargetSymbol = XAUUSD
InpAtrPeriod = 14
InpRegimeFastEmaPeriod = 20
InpRegimeSlowEmaPeriod = 50
InpRegimeSlopeLagBars = 5
InpRegimePersistenceD1Bars = 2
InpRegimeRequireH4Confirm = true
InpRegimeShockH1RangeAtrMultiple = 3.00
InpRegimeShockD1AtrPercentileMin = 95.00
InpRegimeShockD1AtrLookback = 60
InpRegimeCompressionD1AtrPercentileMax = 30.00
InpRegimeCompressionBoxDays = 5
InpRegimeCompressionRangeMedianMax = 1.00
```

Only the run ID and output filenames may vary in the evidence runs. Router priority remains the pinned native implementation: data unavailable/unknown first, then `SHOCK`, `UPTREND`, `DOWNTREND`, `COMPRESSION`, and otherwise `CHOP`.

## 5. Fixed Strategy Tester environment

```text
account login: 1025742
server: Capital.ComMena-Demo
company: Capital Com Mena Securities Trading L.L.C
account currency: USD
account leverage: 1:50
MT5 build: 5833
symbol: XAUUSD
chart period: M5
model: Every tick based on real ticks
initial deposit: USD 10,000
test start: 2015-06-01T00:00:00 broker time
test end exclusive: 2026-07-01T00:00:00 broker time
evidence interval: [2016-07-01T00:00:00, 2026-07-01T00:00:00)
repetitions: run1 and run2
```

If the exact build, server, account contract, or pinned source is unavailable, stop for an environment/source-contract amendment and review. No substitution is allowed.

## 6. Decision and market-data schedule

At the first recorded tick of each new native H4 bar, emit one Router row for the decision time if it lies in the evidence interval. The completed H4 decision bar is shift 1. Export all causal native H1/H4/D1 warm-up and evidence bars required to reproduce every row.

There is no selection by R6 candidate, H4 trade, signal, position, loss, P/L, exposure, drawdown, or known adverse date. Missing native data remains missing; it is never forward-filled or replaced with zero.

All floating-point fields use `%.17g`. Timestamps are broker-server wall-clock values in `YYYY-MM-DDTHH:MM:SS` form. Rows are unique and strictly chronological under the keys frozen in the output schema.

## 7. Contract and OrderCalcProfit probes

The oracle captures the complete market-only account/symbol contract in `native_contract.tsv`. It then calls, without constructing or sending an order:

```text
OrderCalcProfit(order_type, XAUUSD, SYMBOL_VOLUME_MIN, entry_price, exit_price, result)
```

Locked SELL probes use entry `2000.00` and exits:

```text
2002.49, 2002.50, 2002.51, 2024.99, 2025.00, 2025.01
```

Locked BUY probes use entry `2000.00` and exits:

```text
1997.51, 1997.50, 1997.49, 1975.01, 1975.00, 1974.99
```

Every native row is classified `NATIVE_ORDERCALCPROFIT_PROBE`. Later Python linear-contract cases may be classified `DERIVED_FROM_NATIVE_ORDERCALCPROFIT_PROBE`; they may not be represented as independent native captures.

## 8. Source equivalence and determinism

`compiled/source_equivalence.json` records, for each copied block, the signature, authoritative path/commit/blob, source and generated byte offsets, raw SHA256 values, and `exact_equal`. Every `exact_equal` must be true.

Both runs use the same EX5 and effective inputs. Causal market-only outputs must be byte-identical after normalizing only the explicitly declared run ID and report timestamp fields. The verifier binds every Router row to canonical causal bar prefixes through H1/H4/D1 prefix-chain hashes.

## 9. Zero-action contract

Both runs must prove all of:

```text
MT5 Total Trades = 0
MT5 Total Deals = 0
order.zero = 0 bytes
deal.zero = 0 bytes
no open position
no pending order
compile = 0 errors / 0 warnings
all copied source blocks exactly match d5134057
```

The static source scan must reject every forbidden token in the source contract. `OrderCalcProfit` is the only permitted order-related calculation API and is read-only.

## 10. Terminal statuses

Exactly one terminal status is allowed:

```text
R6_NP1_EVIDENCE_INVALID
R6_NP1_SOURCE_EQUIVALENCE_FAIL
R6_NP1_ZERO_ACTION_CONTRACT_FAIL
R6_NP1_NATIVE_EVIDENCE_COMPLETE_PYTHON_PARITY_FAIL
R6_NP1_NATIVE_EVIDENCE_COMPLETE_PYTHON_PARITY_PASS
```

Native evidence plus Python parity FAIL is valid diagnostic evidence for a later C2R5 review; it never authorizes changing native Router rules.

## 11. Validation and attestation

The NP1-B/NP1-C verifier must check pinned source identity, exact copied blocks, source safety, compile cleanliness, effective inputs, environment, two-run completeness, monotonic/unique rows, causal prefix identity, complete contract fields, successful probes, zero trades/deals/orders/positions, output schema conformance, normalized repetition equality, and every artifact hash/size.

The attestation records exact HEAD/tree/clean status; OS, architecture, MT5 and MetaEditor builds; Python/dependency versions; exact commands; stdout/stderr; exit codes; command-output hashes; and hashes of every source, EX5, INI, report, log, parity file, and manifest. Run1 and run2 must use the same EX5 hash. No file changes after attestation.

## 12. Prohibitions

NP1 may not modify existing R6 detector/validator code, tests, fixtures, rule locks, census preregistration, or outcome-blind schema. It may not generate the real census; calculate or inspect R6/H4/portfolio P/L; simulate targets/exits; calculate MFE/MAE; read H4 strategy ledgers, positions, exposure, drawdown, or adverse dates; join portfolio evidence; attach to demo/live; arm a preset/profile; run a trading EA; send/modify/close an order; or change broker/runtime state.

The only later MT5 activity contemplated by this lock is the zero-action Strategy Tester oracle/probe run after NP1-B passes exact-commit review. This NP1-A commit itself authorizes no MT5 execution.

## 13. Phase boundary

NP1-A does not authorize NP1-B automatically. If NP1-A passes, the single next proposal is NP1-B using only the eight implementation/test files frozen by the source contract. C2R5 and C3 remain unauthorized until their separate prerequisite reviews pass. No historical result is deployment authorization.
