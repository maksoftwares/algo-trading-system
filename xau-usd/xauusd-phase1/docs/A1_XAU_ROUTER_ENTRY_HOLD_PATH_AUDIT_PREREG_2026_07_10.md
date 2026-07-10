# A1 XAUUSD Router Entry/Hold-Path Audit V1 Preregistration

Date: `2026-07-10`

Status: `PREREGISTERED_NOT_RUN`

Audit ID: `A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_V1`

Scope: repository-only, exact-MT5 snapshot generation, offline audit, and shadow
diagnostics. This document changes no strategy rule and authorizes no demo, live, or
other broker action.

## Purpose

Audit every trade in the frozen R1+R2 research control and determine, without using
final numeric P/L or any other prohibited outcome field to choose a class, whether it:

1. entered under the wrong EA-side router state;
2. entered under the expected slow D1/H4 state after tactical structure had already
   turned against it;
3. entered correctly and experienced a later regime change while still open;
4. contains a data, timestamp, attribution, or snapshot defect; or
5. was a causally valid protective-stop exit inside its expected regime.

This is a path and attribution audit, not a new strategy test. The separate ten-year
D1 diagnostic map is contextual evidence only and must not replace the authoritative
EA-side router.

## Frozen trade universe

The universe is exactly the `678` rows in:

```text
outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709_current_r1_best_r2_pullback_plus_r2_impulse_body45_atr45_daily_loss10_KEPT.csv
```

SHA256:
`47cbe6a562ba2874d93a97255affbde613566ed06340a149ed2795d69a5dae52`

No trade may be added, removed, deduplicated again, or substituted. R3 may appear in a
separate shadow diagnostic, but no R3 row may enter this audit universe or alter any
R1+R2 total.

### Frozen source reconciliation

| Source ID | Component | Direction | Expected regime | Trades | Frozen P/L USD |
| --- | --- | --- | --- | ---: | ---: |
| `h4_d1_long_best_box2_atr80` | R1 | LONG | `UPTREND` | 145 | +7,050.42 |
| `r1_h1_pullback_long_v1` | R1 | LONG | `UPTREND` | 413 | +1,665.94 |
| `r2_continuation_short_v1` | R2 | SHORT | `DOWNTREND` | 57 | +589.46 |
| `r2_pullback_rejection_short_v1` | R2 | SHORT | `DOWNTREND` | 63 | +334.23 |
| **Total** | **R1+R2** | **558 LONG / 120 SHORT** | — | **678** | **+9,640.05** |

Source counts and cent-precise P/L totals are hard reconciliation controls, not
performance gates.

### Legacy rule-admissibility boundary

The frozen universe intentionally retains its historical rules: the box source's
previous-month P/L health gate, the R1 `09 <= server hour < 15` session gate, the R2
pullback `05 <= server hour < 19` session gate, and the R2 continuation `$10`
source-local daily-loss stop. The master direction forbids the previous-P/L and
discovered session/hour selection rules. The `$10` stop cannot be reused as
standalone alpha/admission evidence; any future daily/weekly/monthly containment must
be the shared preregistered integrated risk policy. Their presence does not invalidate
this identity-preserving path audit, but it blocks these sources from silently
becoming an integrated candidate. No audit code may remove or repair them.
Post-audit work must apply a separate hard rule-admissibility and standalone gate;
failure produces `NO_GO`, not an implicit rule-stripped variant.

### Native-position attribution repair boundary

A preregistration-time evidence audit found a legacy parser defect in the frozen
ledger's upstream `_trades.csv` files. The parser FIFO-paired entries and exits by
direction instead of joining native MT5 `position_id`. Consequently, `388/678`
frozen rows name an exit deal from another position and `387/678` carry another
position's individual P/L. The exit-event/P&L multiset and every source/aggregate
total remain unchanged, so the frozen control-level metrics still reconcile, but the
legacy per-entry holding paths cannot be audited as native trades.

The audit universe is therefore frozen as the same 678 unique namespaced entry-deal
identities, not the legacy FIFO entry/exit pairs. Before any router classification,
perform this outcome-blind identity repair:

1. Resolve each baseline row's exact upstream raw trade using `source_csv` and
   numeric `source_row`; retain the legacy entry, exit, and P/L fields unchanged as
   provenance.
2. Take that row's unique `entry_deal` and join it to the exact source `_deals.csv`
   on `(run_id, account, symbol, magic, deal_ticket)`.
3. Read the joined entry deal's native `position_id`; group deals only by
   `(run_id, account, symbol, magic, position_id)`.
4. Require exactly one entry and one exit deal for every one of the 678 native
   positions, equal full entry/exit volume, unique entry ownership, no partial close,
   add-on, orphan/duplicate deal, and no added or removed entry.
5. Derive native exit time, exit deal, exit reason, final P/L, holding interval, and
   trade ID only from that position group. Mapping may not inspect profit sign,
   magnitude, month, or router class.
6. Reconcile the repaired result back to source counts `145/413/57/63`, source cents,
   aggregate `+$9,640.05`, and the unchanged chronological exit-event/P&L multiset.

Native tickets restart across independent tester runs and are not globally unique.
The immutable audit trade ID is the literal namespaced key:

```text
source_id::run_id::account::symbol::magic::native_position_id
```

Every namespace component must be nonempty, contain no `::`, and reproduce exactly
one of 678 unique IDs. Native entry deal, exit deal, order, and position IDs remain in
separate columns.

If any native join or reconciliation fails, assign
`ROUTER_PATH_INVALID_EVIDENCE`; do not fall back to FIFO. Repairing this attribution
does not change a strategy rule or select a result. The underlying shared parser may
be fixed with a regression test, but historical artifacts remain immutable.

### Frozen raw evidence hashes

The audit must first copy or manifest these currently ignored raw artifacts and
reproduce the SHA256 values below. Any mismatch fails closed before classification.

| Source | Trades | Orders | Deals | Signals | MT5 HTML | Tester config |
| --- | --- | --- | --- | --- | --- | --- |
| H4/D1 box | `6ca00153146c3f62ae1acd20dc7b9bc640c5ffcdf258d0826a00f2fb694237b5` | `e337af7d3e5698f623db5e428f9b987edc5f25c2138cad901a4e54ba6b58b44b` | `dbfa77504f598421e55066bc7c23eac44ad3d93ce99cf165dcd8927682921cbb` | `b53ee54afacfae9a5dceb74a2a16b8297b9aad1c3b582fdc2d77302d344afc3c` | `e1c9ccafb773aea77d67052e86d9ec883bb192694b4a1cea9c47cdbcafdf3605` | `3d52e33afb4d7ec323c6c540b21b9f516e06d446de2f55f2a8ba5d0b39441222` |
| R1 pullback | `91976d2bd3d1a373eb95b5d43efe7a4cad848e64baca69e88db2fc2240312aa6` | `8482016a012efcbb61470b8936815e0277234612d25e1bc2e084306f8338a749` | `f02e02508af05a2c823c422b864df92bae544629a45073091107bdf83acb0fa1` | `2ea28ff551bc1c1c071aa3ca1862447c10c483de70ffcc981797a2b403c355bd` | `9a64333a1fd240fcb8f2ddf7786ef1f63f22a2efea804d992e012c54faeb9e77` | `ce6218537800d4dc51705f32997d3b2ff29a8217fedc3fc7a091a7109991e5f6` |
| R2 continuation | `171df13b53cd682e6de531f868fbb50dd03e94aaf0667c9685a1bf3755471798` | `2284ce7a7847d6ecda755100d4e7e2bfb58eac42bf1829922ada58bb4b3e19d7` | `075e44185c5cf02d8042fb289b902a73021d3602656d3b7ecb72e3e4ae3961b6` | `f21b1182a991edfde99abe03b12b3cc04bf830c342962ba9121b2d3499fb961b` | `f16a1f4aaec5f0b3818ce52c0432e1ded23492e6cb3bd06b08f90b0942439596` | `97f6cdac7ef758c2ee0b2c836b67970ceea01e525639d8b751ef7d238127dbb7` |
| R2 pullback | `3b37ab94c6543286268b98ce73ce491d3be4774c8337ea4a53e0f435f586b3bb` | `893e617218c5b923545cbd6d571a035c6892b5b050a55013e7368f7642b66b66` | `449db6f98db7a9bd54725b095dc785a490944eafab9da6edd7872e137d49c02d` | `a9db4cc1f0461bb7ff6e14944ea5762da019ea959aec248a489731cacda0d49c` | `61762b770864a82f7cf91fdcc7e207735751e7d3a47c58a33c7b5620c6b0bb62` | `cd911b5220915e59e4465923d56bc568b380b36909a6e56fe41c27f9598a6c9a` |

All four management files are zero bytes with SHA256
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
All four MT5 reports identify Build `5833`, `98%` history quality, `282,644` bars,
and `204,204,660` ticks. These are development-data provenance facts, not a quality
waiver or untouched-holdout claim.

## Authoritative Router V1

The sole regime authority is the EA-side Router V1 at repository commit:

```text
006824cde421ea61a0bcdb074804f9ccf95c17a9
```

Authoritative source at that commit:

```text
xau-usd/xauusd-phase1/mt5/Experts/A1XauM5MomentumContinuationExecutor.mq5
```

Source-blob SHA256: `3372d8e751141f1d397d9967b8c14272046e1a733a64f67e63fcc3f56e53d355`

The authoritative state cascade is, in order:

```text
SHOCK -> UPTREND -> DOWNTREND -> COMPRESSION -> CHOP
```

Frozen Router V1 inputs are:

| Input | Value |
| --- | ---: |
| `InpAtrPeriod` | 14 |
| `InpRegimeFastEmaPeriod` | 20 |
| `InpRegimeSlowEmaPeriod` | 50 |
| `InpRegimeSlopeLagBars` | 5 |
| `InpRegimePersistenceD1Bars` | 2 |
| `InpRegimeRequireH4Confirm` | `true` |
| `InpRegimeShockH1RangeAtrMultiple` | 3.00 |
| `InpRegimeShockD1AtrPercentileMin` | 95.00 |
| `InpRegimeShockD1AtrLookback` | 60 |
| `InpRegimeCompressionD1AtrPercentileMax` | 30.00 |
| `InpRegimeCompressionBoxDays` | 5 |
| `InpRegimeCompressionRangeMedianMax` | 1.00 |

The audit must use the commit-pinned implementation or prove byte/behavioral parity
with it. The current working-tree EA, an offline reimplementation, or the ten-year
diagnostic classifier cannot silently become the authority. Any read-only snapshot
mode added later must reproduce Router V1 and the inputs above exactly.

## Completed-bar snapshot contract

All regime, indicator, structure, and path decisions use completed bars only.

1. A bar is available only on the first actual modeled tester tick/event at which MT5
   exposes it as shift 1. Nominal `bar_open_time + PeriodSeconds()` is not proof of
   availability across no-tick gaps.
2. Every D1, H4, H1, M15, and M5 join is a backward as-of join on the exact event key
   `(tester_time_msc, callback_sequence, event_sequence)`. The selected observation
   key must be recorded and must be less than or equal to the source-event key.
3. Bar `0`, a still-forming bar, a nearest-time join, and a forward-filled future
   snapshot are forbidden.
4. `signal_time` is the original exact-MT5 would-signal timestamp. It must not be
   inferred from `entry_time`.
5. `router_state_at_signal` and `router_state_at_entry` use the latest completed data
   available at those respective timestamps.
6. The holding path contains every newly observable completed-H1 event whose event
   key is strictly after the entry-deal key and strictly before the exit-deal key.
   `router_state_at_exit` is the latest router observation whose event key is not
   after the exit-deal key.
7. The first later change is the earliest eligible holding-path observation whose
   Router V1 state differs from the expected regime while the position is still
   open. A snapshot sharing the exit timestamp is diagnostic only unless its event
   sequence proves that Router V1 was evaluated before the exit deal; an ambiguous
   or post-exit snapshot cannot establish `CORRECT_ENTRY_LATER_REGIME_CHANGE`.
8. D1/H4/H1 EMA values and slopes use the same symbol, broker history, price basis,
   periods, and completed-bar semantics as the authoritative EA. D1/H4 router slopes
   are the five-bar EMA differences used by Router V1.
9. MFE, MAE, and unrealized R at change use only exact modeled tester ticks whose
   event keys are inside the frozen interval. Initial risk is frozen from the original
   entry and original protective SL; it is never recomputed from outcome.
10. Missing warm-up history, nonpositive ATR, absent exact timestamps, duplicate or
    ambiguous joins, unexplained gaps, or inability to reproduce an EA state is
    `DATA_OR_TIMESTAMP_ERROR`; unknown state fails closed.

All audit timestamps must preserve broker timezone and millisecond precision and
include an unambiguous UTC offset or a frozen broker-time-to-UTC conversion table in
provenance. Snapshot instrumentation must assign one monotonically increasing event
sequence at every log emission. When legacy source evidence lacks enough ordering to
prove a same-timestamp join, the implementation must obtain no-op exact replay
evidence or fail that row closed; nominal clock ordering may not be invented.

## Causal H1 strong-slope definition

There is one preregistered, distribution-based threshold and no threshold grid.

For completed H1 bar `t`:

```text
ema20_slope_5_price[t] = EMA20[t] - EMA20[t-5]
ema20_slope_5_norm[t]  = ema20_slope_5_price[t] / ATR14[t]
```

The threshold at `t` is the 80th percentile of the absolute normalized slopes from
exactly the prior 252 completed H1 bars, excluding `t`:

```text
h1_abs_slope_q80[t] = Q80(
    abs(ema20_slope_5_norm[t-252]),
    ...,
    abs(ema20_slope_5_norm[t-1])
)
```

Use the deterministic Type-7/linear quantile: sort the 252 values, set
`h=(n-1)*0.80`, and linearly interpolate between zero-based indices `floor(h)` and
`ceil(h)`. All 252 observations must be finite and causal.

```text
strongly negative at t: ema20_slope_5_norm[t] <= -h1_abs_slope_q80[t]
strongly positive at t: ema20_slope_5_norm[t] >=  h1_abs_slope_q80[t]
```

ATR normalization is price-unit invariant. A missing/zero ATR, incomplete 252-bar
window, or nonfinite value is unknown and fails closed. The threshold is computed
before outcomes are opened and is never changed after class or P/L analysis.

## Causal M15 swing and structure definition

Use fixed `2-left / 2-right` completed-M15 pivots.

- M15 bar `k` is a confirmed swing high only when its high is strictly greater than
  the highs of bars `k-2`, `k-1`, `k+1`, and `k+2`.
- M15 bar `k` is a confirmed swing low only when its low is strictly less than the
  lows of bars `k-2`, `k-1`, `k+1`, and `k+2`.
- Ties are not swings.
- A pivot becomes observable only on the first actual modeled tester event at which
  `k+2` is exposed as a completed bar. Store that confirmation event key; nominal
  close-time arithmetic is insufficient.
- At a source event, the last confirmed swing is the latest pivot whose confirmation
  event key is not after the source-event key.
- On the latest observable completed M15 bar, compute `above_high = close > last
  confirmed swing high` and `below_low = close < last confirmed swing low`.
  Structure-break direction is `BULLISH` only for `(above_high, below_low) = (true,
  false)`, `BEARISH` only for `(false, true)`, and `NONE` only for `(false, false)`.
  `(true, true)` is `AMBIGUOUS`, because independently latest confirmed high/low can
  be crossed simultaneously; any class that needs it fails closed.

Insufficient bars or a missing required swing is recorded as `UNKNOWN`, not imputed.
If an unknown is needed to decide a class, that trade becomes
`DATA_OR_TIMESTAMP_ERROR`.

## Objective entry predicates

### Expected regime

R1 LONG expects Router V1 `UPTREND`. R2 SHORT expects Router V1 `DOWNTREND`.

### Transition predicate

At signal and entry, derive D1/H4 structural direction using Router V1's completed-bar
EMA20/EMA50 stack and five-bar slope rules. An objective transition exists if any of
the following is true:

1. D1 and H4 structural directions are directly opposed (`UP` versus `DOWN`);
2. the expected D1 trend still persists but H4 has lost the expected stack; or
3. D1 and H4 remain aligned with the expected regime while H1 is strongly opposed on
   two consecutive completed H1 bars.

For condition 3, R1 opposition means both `H1 close < H1 EMA50` and the preregistered
strongly-negative EMA20 slope on each of the two bars. R2 opposition means both
`H1 close > H1 EMA50` and the strongly-positive slope on each bar. No P/L, MFE, MAE,
month, session, or discovered threshold enters this predicate.

### Stale tactical-opposition predicate

After excluding wrong-router and transition entries, an expected-regime entry is
stale if at signal or entry any direction-specific opposition flag is true:

For R1 LONG:

```text
H1 close < H1 EMA50
OR H1 EMA20 five-bar normalized slope is strongly negative
OR M15 completed-bar structure break is BEARISH
```

For R2 SHORT:

```text
H1 close > H1 EMA50
OR H1 EMA20 five-bar normalized slope is strongly positive
OR M15 completed-bar structure break is BULLISH
```

Signal and entry flags are retained separately. The predicate is symmetric and fixed
before outcomes are read.

## Required trade-level schema

Every one of the 678 trades must contain these required fields:

```text
source_id
component
trade_id
direction
signal_time
entry_time
exit_time

expected_regime
router_state_at_signal
router_state_at_entry
router_state_on_each_completed_H1_bar_while_open
router_state_at_exit

D1 close
D1 EMA20
D1 EMA50
D1 EMA20 slope
D1 EMA50 slope

H4 close
H4 EMA20
H4 EMA50
H4 EMA20 slope
H4 EMA50 slope

H1 close
H1 EMA20
H1 EMA50
H1 EMA20 slope
H1 EMA50 slope

M15 tactical structure
M15 last confirmed swing high
M15 last confirmed swing low
M15 structure-break direction

M5 signal state
spread
cost_R
initial risk
entry price
SL
TP

first_regime_change_time
router_state_before_change
router_state_after_change
unrealized_R_at_change
MFE_R_before_change
MAE_R_before_change
final_R
final_PnL
holding_seconds
holding_H1_bars
percentage_of_holding_time_in_expected_regime
```

The audit must additionally retain snapshot timestamps, `exit_reason`, original-SL
history, H1 normalized slope/Q80 values, M15 pivot confirmation times, every primary
predicate flag, `primary_class`, and class-lock provenance. Field names may be
machine-safe snake_case in CSV/JSON, but the mapping to every required field above
must be explicit and one-to-one.

## Frozen metric and path formulas

All money arithmetic uses decimal USD to cents for reconciliation and full-precision
decimal values for R ratios. Binary-float rounding cannot decide a gate.

### Entry, risk, cost, and final return

- Actual `entry_price` and executed volume come from the authoritative native entry
  deal. Original requested `SL`, `TP`, spread, and `cost_R` come from the unique
  original `ORDER_SEND_OK` row and native HTML entry order joined to that deal.
  `ORDER_SEND_OK.result_price` and lots must reconcile to the native deal at symbol
  price precision and volume step; any unexplained fill/volume disagreement fails
  closed. `cost_R` is the source EA's logged `estimated_cost_r`; it is not recomputed
  or stressed after the result.
- `initial_risk_usd = abs(OrderCalcProfit(order_type, symbol, executed_volume,
  entry_price, original_SL))`, using the exact tester symbol specification and USD
  account conversion. The audit must also log point, tick size, contract size,
  `SYMBOL_TRADE_TICK_VALUE_LOSS`, and the independent tick-value formula. MT5 and the
  independent calculation must reconcile to one cent; risk must be finite and
  positive.
- `final_PnL` is the native-position value, reconciled to the exact position's sum of
  `DEAL_PROFIT + DEAL_COMMISSION + DEAL_SWAP + DEAL_FEE` over every entry and exit
  deal belonging to that position, and then reconciled back to frozen source and
  aggregate cents.
- `final_R = final_PnL / initial_risk_usd`.
- The historical `-$0.30/ticket` stress result remains a control-level reference. No
  extra stress debit is added to path metrics or classifications in this audit.

### Executable marks, MFE, MAE, and change return

Use exact modeled tester ticks, not OHLC extrema, for every price-path metric. The
executable mark is bid for a LONG and ask for a SHORT. For a tick mark `p`:

```text
mark_pnl_usd = OrderCalcProfit(order_type, symbol, executed_volume, entry_price, p)
mark_R       = mark_pnl_usd / initial_risk_usd
```

`mark_pnl_usd` excludes commission, swap, and fees; those remain in final P/L.
`unrealized_R_at_change` uses the executable mark on the exact router-change tick.
`MFE_R_before_change` is the maximum `mark_R`, and `MAE_R_before_change` is the
minimum `mark_R`, over ticks with keys strictly after entry and strictly before the
change observation. The entry mark contributes `0R`; therefore a path with no
intermediate tick has MFE and MAE of zero. If there is no regime change, the endpoint
is the exit-deal key. The change tick is excluded from "before change" MFE/MAE but is
used for unrealized R. No bar-high/bar-low substitute may promote valid evidence.

For a changed trade:

```text
post_change_R = final_R - unrealized_R_at_change
```

This convention attributes all later price movement and exit slippage to the
post-change remainder. It is frozen before outcome summaries.

For this V1 formula, exact history must prove `DEAL_COMMISSION = DEAL_SWAP =
DEAL_FEE = 0.00` across all entry and exit deals in the 678 native positions. The
existing raw extracts indicate zero commission and swap, but Commit 3 must also
extract and verify fee. Any nonzero amount invalidates V1 rather than being silently
misallocated between pre- and post-change R; a new preregistration would be required
for accrued-cost attribution.

### Holding duration and expected-regime percentage

```text
holding_seconds = (exit_deal_time_msc - entry_deal_time_msc) / 1000
holding_H1_bars  = count(completed-H1 observation keys strictly between entry and exit)
```

For percentage attribution, Router V1 state at entry applies from the entry event to
the first eligible completed-H1 observation; each observed H1 state then applies
until the next observation or exit. Use actual elapsed wall-clock milliseconds,
including market-closure gaps under the last causally observed state:

```text
percentage_of_holding_time_in_expected_regime =
    100 * expected_regime_elapsed_milliseconds / holding_elapsed_milliseconds
```

Boundaries are clipped exactly to entry and exit event times. A zero/negative holding
interval, an unobservable state interval, or a non-monotone event key fails closed.

## Frozen concentration and drawdown interval

The baseline's maximum closed-equity drawdown is frozen at `$889.69`, from peak exit
`2025-12-26 16:05:13` through trough exit `2026-01-09 13:30:42` in broker time.
Derivation uses the frozen ledger hash above, starts closed equity at zero, adds
decimal `pnl_usd`, and sorts ascending by:

```text
(exit_time, entry_time, numeric source_priority, source_id, numeric source_row)
```

A new equity peak and a new maximum drawdown replace the prior event only on strict
`>`; ties retain the earliest event.

The stale-entry concentration test groups `final_R` by entry month and removes the
single entry month with the most negative aggregate stale `final_R`; it removes DD
observations whose `entry_time` lies in the inclusive broker-time interval
`[2025-12-26 16:05:13, 2026-01-09 13:30:42]`.

The holding-change concentration test groups `post_change_R` by the month of
`first_regime_change_time` and removes the single first-change month with the most
negative aggregate `post_change_R`; it removes observations whose
`first_regime_change_time` lies in that same inclusive DD interval. Month ties use
the chronologically earliest month. These timestamps, ordering rules, metrics, and
inclusion boundaries cannot change after outcome unsealing.

## Primary classes and deterministic precedence

Assign exactly one primary class to every trade:

```text
CORRECT_ENTRY_STABLE_REGIME
CORRECT_ENTRY_LATER_REGIME_CHANGE
STALE_TREND_ENTRY
WRONG_ROUTER_ENTRY
TRANSITION_ENTRY
DATA_OR_TIMESTAMP_ERROR
VALID_LOSS_IN_EXPECTED_REGIME
```

Evaluate in this fixed precedence; first match wins:

1. `DATA_OR_TIMESTAMP_ERROR`: any required identity, timestamp, snapshot, causal join,
   router reproduction, path, or exit-reason evidence is missing, ambiguous, or
   contradictory.
2. `WRONG_ROUTER_ENTRY`: an R1 LONG entered when Router V1 state at entry was not
   `UPTREND`, or an R2 SHORT entered when it was not `DOWNTREND`.
3. `TRANSITION_ENTRY`: router-at-entry is expected, but the objective transition
   predicate was present at signal or entry.
4. `STALE_TREND_ENTRY`: router-at-entry is expected, no transition predicate was
   present, and the fixed tactical-opposition predicate was present at signal or
   entry.
5. `CORRECT_ENTRY_LATER_REGIME_CHANGE`: entry passed all earlier checks and an
   eligible router observation changed away from the expected regime with an event
   key strictly before the exit deal, or with explicit same-timestamp ordering that
   proves snapshot-before-exit. A diagnostic exit snapshot cannot match by itself.
6. `VALID_LOSS_IN_EXPECTED_REGIME`: entry and complete holding path passed all causal
   checks, no later regime change occurred, and exact order/deal history proves the
   position exited through its original, never-modified protective SL. Gap/slippage
   at that SL does not change this event-based rule.
7. `CORRECT_ENTRY_STABLE_REGIME`: entry and complete holding path passed all causal
   checks, no later regime change occurred, and the original-protective-SL rule above
   did not match.

Unknown or overlapping evidence never receives a favorable lower-precedence class.
All predicate flags remain in the row so precedence can be independently reproduced.

### Outcome-sealed classification

Classification is two-pass:

1. Build and hash all class assignments through a typed classifier interface that
   admits only identity/direction, expected regime, event keys, causal router and
   D1/H4/H1/M15 snapshot fields, original entry/SL/TP/order identity, and the two
   booleans `exit_is_exact_deal_reason_sl` and `original_sl_never_modified`.
2. The classifier interface must exclude `final_R`, `final_PnL`, profit/loss sign,
   MFE, MAE, unrealized R, post-change R, costs after entry, year/month aggregate,
   drawdown-window membership, and every other outcome-derived field. A schema test
   must prove those columns are absent, not merely ignored by convention.
3. Lock the classes and class-input hash, verify that replacing every prohibited
   outcome field leaves all assignments unchanged, and only then unseal outcomes for
   gate summaries.

`VALID_LOSS_IN_EXPECTED_REGIME` is resolved solely from the original protective-SL
exit event after every causal path check passes. It requires exact MT5
`DEAL_REASON_SL` provenance and proof that the original SL was never modified; an
exit-comment string alone is insufficient. The classifier must not read the sign or
value of `final_R` or `final_PnL` before the class is locked.

## Required output artifacts

Generate all of the following, with a shared provenance ID and hashes:

```text
outputs/reports/A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_20260710.md
outputs/reports/A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_20260710.json
outputs/reports/A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_20260710_NATIVE_POSITION_RECONCILIATION.csv
outputs/reports/A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_20260710_TRADES.csv
outputs/reports/A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_20260710_REGIME_PATHS.csv
outputs/reports/A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_20260710_CLASS_SUMMARY.csv
outputs/reports/A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_20260710_SOURCE_SUMMARY.csv
outputs/reports/A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_20260710_YEARLY.csv
outputs/reports/A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_20260710_MONTHLY.csv
```

The JSON must include baseline/router/source hashes, tester build and inputs, broker
symbol/timezone provenance, snapshot-log hashes, reconciliation checks, class-lock
hash, all gate booleans, and the one final status. The path CSV must contain one row
per trade per eligible completed H1 path snapshot, plus the separate exit snapshot.

## Exact reconciliation and validity gates

The audit is valid only if every check below passes:

```text
baseline SHA256 equals the frozen hash
exactly 678 baseline rows are traced one-to-one
exactly 678 unique namespaced baseline entry-deal identities map one-to-one to 678 native position IDs
legacy FIFO mismatch counts reproduce as 388 exit-deal and 387 individual-P/L mismatches
each native position has exactly one entry and one exit deal
each native position exits the full entry volume with no partial close or add-on
all namespaced audit trade IDs are nonempty and unique across 678 positions
native and legacy chronological exit-event/P&L multisets reconcile exactly
source counts equal 145 / 413 / 57 / 63
source P/L equals +7050.42 / +1665.94 / +589.46 / +334.23 USD exactly to cents
aggregate P/L equals +9640.05 USD exactly to cents
0 missing source IDs or trade IDs
0 missing signal timestamps
0 missing entry timestamps
0 missing exit timestamps
0 missing router snapshots
0 missing eligible completed-H1 holding snapshots
0 missing required tick/event-order evidence
0 future-bar reads
0 bar-0 decisions
all snapshot joins are backward as-of by exact event key and at or before their source events
all counted later regime changes were observed before the exit-deal event
all MT5 order/deal/trade identities reconcile exactly
all original SL histories and DEAL_REASON_SL claims reconcile exactly
all initial-risk OrderCalcProfit and independent tick-value calculations reconcile to one cent
all entry/exit DEAL_COMMISSION, DEAL_SWAP, and DEAL_FEE values equal exactly 0.00
all source trade counts and source P/L totals reconcile exactly
all four sources retain their frozen expected direction and regime mapping
all 678 trades receive exactly one deterministic primary class
classifier schema excludes every prohibited outcome field
classification is invariant to replacement of every prohibited outcome field
all ambiguous or unknown cases fail closed
all artifact and source hashes verify
```

There is no tolerance-based row or P/L reconciliation. Currency values use decimal
cents, not binary floating-point equality.

### Wrong-router defect gate

```text
WRONG_ROUTER_ENTRY count == 0
```

If the count is nonzero, stop. Only the routing/configuration defect may be fixed; rerun
the frozen exact-MT5 baseline and require zero violations. Do not add a filter or
change a threshold.

### Stale-entry evidence gate

Router V2 is justified only if all are true after classes are locked and outcomes are
unsealed:

```text
stale losing trades / all specialist losing trades >= 15%
STALE_TREND_ENTRY aggregate net R < 0
STALE_TREND_ENTRY PF < 1.0
STALE_TREND_ENTRY count >= 30
STALE_TREND_ENTRY net R < 0 in at least 3 entry-year buckets
aggregate stale net R remains < 0 after removing its single worst calendar month
aggregate stale net R remains < 0 after removing trades entered during the frozen
  control's maximum closed-equity peak-to-trough drawdown interval
```

A losing trade in the ratio means post-lock `final_PnL < 0`; it never influences the
class. PF is gross positive final R divided by the absolute gross negative final R
within the stale class. A zero gross-loss denominator does not pass.

### Holding-regime-change gate

A separate exit/de-risk study is justified only if all are true:

```text
CORRECT_ENTRY_LATER_REGIME_CHANGE count >= 30
aggregate post-change R < 0
post-change R < 0 in at least 3 first-change-year buckets
aggregate post-change R remains < 0 after removing its single worst calendar month
aggregate post-change R remains < 0 after removing observations inside the frozen
  control's maximum closed-equity peak-to-trough drawdown interval
```

For each changed trade, `post_change_R = final_R - unrealized_R_at_change`, using the
same initial-risk denominator and cost convention. This diagnostic is calculated only
after class lock. Do not change entry and exit in the same test.

## Allowed status and decision precedence

Assign exactly one status in this order:

1. `ROUTER_PATH_INVALID_EVIDENCE` if any reconciliation or validity gate fails.
2. `ROUTER_PATH_WRONG_ENTRY_DEFECT` if evidence is valid and wrong-router count is
   nonzero.
3. `ROUTER_PATH_STALE_ENTRY_V2_JUSTIFIED` if evidence is valid, wrong-router count is
   zero, and every stale-entry gate passes.
4. `ROUTER_PATH_HOLDING_CHANGE_STUDY_JUSTIFIED` if the prior conditions do not select
   a status and every holding-change gate passes.
5. `ROUTER_PATH_VALID_NO_CHANGE` otherwise.

If both stale and holding-change gates pass, the stale-entry status wins and any
management study is deferred. Entry and exit changes must never be bundled.

Allowed consequences are limited to:

- `ROUTER_PATH_VALID_NO_CHANGE`: freeze Router V1, keep the control, and move to the
  next governance-authorized proof step.
- `ROUTER_PATH_WRONG_ENTRY_DEFECT`: fix only the defect and rerun the frozen baseline.
- `ROUTER_PATH_STALE_ENTRY_V2_JUSTIFIED`: test one symmetric opposition veto or one
  explicit `TRANSITION_NO_TRADE` state as one fixed candidate—no grid or calendar
  filter.
- `ROUTER_PATH_HOLDING_CHANGE_STUDY_JUSTIFIED`: run one shadow-only comparison of the
  original SL/TP control versus one preregistered regime-change de-risk rule.
- `ROUTER_PATH_INVALID_EVIDENCE`: stop and repair evidence only.

None of these statuses promotes a specialist, authorizes a portfolio, or constitutes
new forward confirmation.

## Evidence gap and Commit 3 requirement

The frozen 678-row ledger currently supplies component/source identity, entry/exit
times, direction, P/L, and upstream provenance, but it is not full multi-timeframe
exact snapshot evidence. It does not by itself contain the complete exact signal-time,
Router V1 signal/entry/hold/exit path, D1/H4/H1 indicator, causal M15 swing, M5 signal,
or original-SL event record required above.

The four raw run directories are currently ignored/untracked, their management CSVs
are empty, and the historical runs did not bundle their exact source/EX5 hashes.
Schema forensics show the H4 run came from an earlier committed input schema, the R1
pullback run from an intermediate schema, and the two R2 runs from the 242-input base
schema. The Router V1 state core, its 11 Router-specific inputs, and common
`InpAtrPeriod=14` are behaviorally identical for the relevant versions, but that
parity must be proven and hashed; the dirty working-tree EA is forbidden as audit
authority. Empty management logs alone are not
proof of an unchanged SL: affirmative proof requires frozen disabled-management
inputs, source control-flow evidence, native order/deal history, and equality of the
native exit event with the original submitted SL/TP.

Therefore no audit result exists at preregistration. Commit 3 must generate immutable
exact-MT5 snapshot/log evidence, tester/order/deal provenance, and artifact hashes
before classification or any status assignment. If exact evidence cannot be produced
and reconciled, the only allowed status is `ROUTER_PATH_INVALID_EVIDENCE`.

## Forbidden changes and authorization boundary

```text
No strategy parameter change.
No new R1, R2, R3, or R4 variant.
No entry, exit, SL, TP, sizing, or management change.
No threshold grid or post-result threshold change.
No session, hour, weekday, month, loss-window, or previous-P/L filter.
No outcome-dependent class definition.
No substitution of the ten-year D1 diagnostic map for Router V1.
No offline recomposition as promotion evidence.
No runtime terminal, chart attachment, account, or broker-state change.
No demo or live attach.
No broker order outside isolated Strategy Tester runs.
```

Read-only instrumentation or an isolated tester snapshot mode is permitted only to
produce the required exact evidence and must prove no-op parity for trading behavior.
This preregistration leaves runtime, trading logic, and broker state untouched.
