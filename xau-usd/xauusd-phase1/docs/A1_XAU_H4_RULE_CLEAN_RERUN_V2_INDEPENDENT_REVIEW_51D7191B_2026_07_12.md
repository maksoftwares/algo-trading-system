# Independent Exact-Commit Review — `51d7191b`

## H4 Rule-Clean Effective-Input Rerun V2 and Authorization Boundary for the R6 Census

**Repository:** `maksoftwares/algo-trading-system`  
**Branch:** `codex/xau-router-entry-hold-audit`  
**Exact reviewed commit:** `51d7191b050697eb9854c25b092ee5f3c11fad67`  
**Previous reviewed base:** `addf272a06d1d795376f2eb0a57741af2c95562b`  
**Intermediate implementation commits:** `e1986be7`, `59b9a1f6`, `b173fd13`, `51d7191b`  
**Review boundary:** repository and MT5 Strategy Tester evidence only  
**Data boundary:** every observation through `2026-06-30` remains development data  
**Runtime boundary:** no live or demo attachment, preset arming, chart/profile mutation, account action, or broker order is authorized

---

# Executive verdict

```text
EVIDENCE VALIDITY:
  VALID_WITH_ONE_NONBLOCKING_TEST-PROVENANCE GAP

166 -> 224 INPUT-LOCK AMENDMENT:
  METHODOLOGICALLY ACCEPTABLE AS A DISCLOSED COMPLETENESS AMENDMENT
  NOT EVIDENCE_INVALID

NATIVE EFFECTIVE INPUTS:
  PASS — 224 EXPECTED / 224 INI / 224 NATIVE, NO MISSING, EXTRA, OR UNEQUAL

LEGACY MASK REMOVAL:
  PASS — EXPLICIT SOURCE AUTHORITY FALSE, SENTINELS PRESENT, ZERO MASK BLOCKS

H4 PRIMARY LOCKED STATUS:
  H4_RULE_CLEAN_UNDERPOWERED

H4 CURRENT FAMILY:
  CLOSED — NO FURTHER H4 REPAIR, THRESHOLD, MASK, HEDGE, OR EXIT LOOP

SMALL-ACCOUNT STATUS:
  CONTRACT_GRANULARITY_INFEASIBLE FOR THIS H4 FAMILY
  0 / 156 CANDIDATES FIT $2.50 RISK AT 0.01 LOT

0.69% TEN-YEAR DD:
  A REAL LOW-RISK RESULT FOR THE RE-ARCHITECTED REFERENCE RUN
  NOT A PROFIT-PRESERVING SOLUTION TO THE OWNER'S RETURN OBJECTIVE

R6 OUTCOME-BLIND CENSUS:
  AUTHORIZED, CENSUS-ONLY, SUBJECT TO THE DEFINITIONS AND COMMIT BOUNDARIES BELOW

STANDALONE R6 P/L:
  NOT AUTHORIZED IN THE CENSUS PHASE

BROKER/RUNTIME ACTION:
  NOT AUTHORIZED
```

No numeric, input-equality, source-hash, native-report, trade-ledger, or status defect was found that requires `H4_EVIDENCE_INVALID`. The result is nevertheless a terminal **NO-GO for this H4 family** because it is underpowered, misses the locked 24-month concentration gate, and cannot be expressed on the stated USD 1,000 account at the verified `0.01` minimum contract.

---

# 1. The 166-to-224 pre-result lock amendment

## Decision

**Acceptable. Do not mark the packet invalid.**

It is not a pristine never-amended preregistration, so it must remain disclosed exactly as it is now. It is nevertheless a permissible evidence-completeness amendment because the amendment did not alter the market hypothesis or any economic degree of freedom.

## Why it is acceptable

The first attempt revealed a schema-completeness problem:

```text
initial locked tester inputs: 166
native MT5 inputs exposed:    224
unlocked defaults:             58
```

The verifier is exact and fail-closed. It compares:

```text
locked expected inputs
generated INI inputs
native MT5 HTML inputs
```

and rejects missing, extra, and unequal values. The run pipeline performs that verification before it copies the trading ledgers and before it builds or evaluates the trade metrics. Thus the initial attempt could generate a native HTML report, but the result pipeline could not accept it as evidence.

The final amendment:

1. Added the unchanged 58 EA defaults to `native_defaults`.
2. Explicitly emitted those defaults into both generated INIs.
3. Required all 224 values to match the native report.
4. Changed none of:
   - signal logic;
   - router mode or thresholds;
   - first-cross definition;
   - dates;
   - risk amount;
   - lot-sizing rule;
   - stop geometry;
   - 2R target;
   - stress convention;
   - survivor gates;
   - status precedence.

The final five- and ten-year packets each record:

```text
expected_count = 224
actual_count   = 224
missing        = []
extra          = []
unequal        = {}
pass           = true
```

The valid native reports also show the four mask strings as `__DISABLED__` and `InpLegacySelectionMasksEnabled=false`.

## Additional corroboration

The clean rerun's executed deal and signal ledgers have the same SHA256 values as the earlier mask-contaminated packet, while the INI, native report, startup, order, and effective-input artifacts changed. That is consistent with the old masks not changing the finally executed trades, while still proving that the new run actually removed their authority.

This does not rehabilitate the earlier packet as rule-clean. It shows that the valid rerun independently reached the same trade path under a properly verified input contract.

## Caveat

The amendment and final result were committed together in `51d7191b`, rather than placing the amended lock in a separate pre-run commit. Also, the native report physically contains its performance table even though the pipeline refuses to parse/accept performance before input verification.

Therefore, the correct characterization is:

```text
ACCEPTABLE ADMINISTRATIVE COMPLETENESS AMENDMENT
NOT A PRISTINE UNAMENDED LOCK
NOT OUTCOME-BASED TUNING
NOT EVIDENCE_INVALID
```

It would have been invalid if any of the 58 values had been selected from performance, if the expected set had been narrowed to whatever MT5 happened to report, or if any signal/risk/gate value had changed. I found none of those conditions.

---

# 2. Exact implementation and evidence verification

## 2.1 Native effective-input equality

**PASS.**

The final verifier merges the 58 `native_defaults` with the 166 horizon-specific values, parses the generated tester INI and native HTML independently, and performs exact set/value comparisons.

Both horizons have:

```text
intended INI comparison: 224 / 224, exact
native HTML comparison:  224 / 224, exact
environment mismatches:  none
status:                  EFFECTIVE_INPUTS_MATCH
```

The native environment was also matched to:

```text
server:     Capital.ComMena-Demo
build:      5833
company:    Capital Com Mena Securities Trading L.L.C
currency:   USD
leverage:   1:50
symbol:     XAUUSD
period:     M5
```

## 2.2 Explicit legacy-mask disable

**PASS.**

The source repair adds:

```text
InpLegacySelectionMasksEnabled
```

as the sole authority. Each of these functions returns `false` immediately when the authority is disabled:

```text
EntryHourBlocked
EntryDayHourBlocked
DirectionEntryHourBlocked
```

The valid native report proves:

```text
InpBlockedEntryHoursCsv=__DISABLED__
InpBlockedEntryDayHoursCsv=__DISABLED__
InpBlockedLongEntryHoursCsv=__DISABLED__
InpBlockedShortEntryHoursCsv=__DISABLED__
InpLegacySelectionMasksEnabled=false
```

The order-ledger summaries contain:

```text
blocked_entry_hour:             0
blocked_entry_day_hour:         0
direction_blocked_entry_hour:   0
```

The result packet records `legacy_mask_block_count=0` in both horizons.

## 2.3 Shared minimum-lot fail-closed behavior

**PASS for the locked invariant and this evidence packet.**

The shared M5 executor now computes requested risk-normalized volume before normalization and returns `0.0` when requested volume is below `SYMBOL_VOLUME_MIN`. The order path converts that to:

```text
minimum_lot_risk_excess
```

rather than rounding the position upward.

Because the H4 test source is generated from a pinned older source, its source builder applies the same invariant as a deterministic one-time transformation. The final generated MQ5 hash in the source manifest matches the compiled-source artifact hash in the root manifest.

### Remaining hardening item

If tick size, tick value, or stop distance is invalid, the shared risk-sizing function still falls back to fixed lots. That path was not reached here—the captured symbol contract is valid—but a future runtime-capable version should return zero on invalid risk metadata rather than fall back to a position.

This is not a defect in the present numerical result. It is a mandatory fail-closed improvement before any future runtime discussion.

## 2.4 Account and symbol contract capture

**PASS as evidence; automated gating is incomplete.**

The startup ledger captured exactly one row per horizon and contains:

```text
account_currency:   USD
account_leverage:   50
margin_mode:        2
volume_min:         0.01
volume_step:        0.01
volume_max:         1000
contract_size:      100
tick_size:          0.01
tick_value:         1.00
tick_value_loss:    1.00
stops_level:        0
freeze_level:       0
server:             Capital.ComMena-Demo
status:             INIT_OK
```

The current evidence gate checks that a startup-contract object exists, while the native-environment verifier locks server, build, company, currency, leverage, and symbol. It does not yet exact-lock every symbol-contract value.

For R6, every contract field must be exact-locked and validated—not merely present.

## 2.5 Native position and P/L reconciliation

**PASS.**

The native trade builder is strict:

```text
one entry deal per position
one exit deal per position
exactly two deals per position
entry volume equals exit volume
profit + commission + swap + fee summed by position
nonzero DEAL_FEE rejected by this historical parser
```

Ten-year reconciliation:

```text
successful order sends:       36
native report total trades:   36
derived position trades:      36
native report total deals:    72
deal-ledger data rows:         72
derived net:                  $486.82
native report net:            $486.82
derived PF:                    2.589253
native report PF:              2.59
wins / losses:                 20 / 16
maximum simultaneous:          1
residual management failures: 0
order failures:                0
```

Five-year reconciliation:

```text
successful order sends:        9
native report total trades:    9
derived position trades:       9
native report total deals:     18
derived net:                   $122.56
native report net:             $122.56
derived PF:                     2.543382
native report PF:               2.54
wins / losses:                  5 / 4
maximum simultaneous:           1
```

## 2.6 Compile and source provenance

**PASS.**

The compile log ends with:

```text
Result: 0 errors, 0 warnings
```

Cross-manifest relationships are internally consistent:

```text
pinned source commit:
  d15fc9a6b3ff18d1748428ea6519fbe58ab30721

pinned source SHA256:
  bc61515d51b9414760ebe7d4d8e6bbf11fdfe760fd21d91246c0aae017449a51

generated/repaired MQ5 SHA256:
  52e7b3b9258c650635c782069e7abf135cda074ddb64ea8afbad3163d3821c05

root-manifest compiled MQ5 SHA256:
  52e7b3b9258c650635c782069e7abf135cda074ddb64ea8afbad3163d3821c05
```

The root manifest covers 24 output artifacts, including source, EX5, compile log, source manifest, both native reports, both INIs, both effective-input reports, every ledger, funding boundary, feasibility CSV, and result JSON/Markdown.

The result JSON and root manifest agree on:

```text
effective-input lock SHA256:
  73e59226bd447a9e6648493479cf2fc73d2c51b2fe4d906b5b4d1869dd55e0ad

preregistration SHA256:
  81158882d789d17a4c5bb6d121fd957f769af7a1dc29889267bb0610d14de816

five-year native-report SHA256:
  575b65e768d7d9a58ba35460b954d362c882971afbd20cca8a466996a1f385c9

ten-year native-report SHA256:
  98b54fb159f77ec39d4a5082b79e8d7f9e9d36fd2e52ae94e267bafd6e9081f7

five-year INI SHA256:
  1213f5bc7ebeca36db795152794f60b0bdf458aea9ee8c10fb840717cbb2ee7d

ten-year INI SHA256:
  ef14a60d2abb71799d81d6e5dd9c5d0620525ad499379f954bc53858263123d5
```

I reviewed the committed source and hash relationships. I did not execute the Windows EX5 binary independently.

## 2.7 Test provenance

**CREDIBLE, BUT NOT EXACT-COMMIT-BOUND.**

The committed validation record captures:

```text
Python:     3.12.13
uv:         0.11.12
command:    uv run --with pytest --with pyyaml --with pandas python -m pytest xau-usd/xauusd-phase1/tests -q
exit code:  0
result:     910 passed in 27.91s
```

However, it records:

```text
Pre-test repository HEAD: b173fd138e9397798c001049511d50c6cfe9f5dd
```

rather than exact reviewed commit `51d7191b`. The final experiment runner, its tests, the amended lock, and the evidence packet were uncommitted working-tree content at test time. There is also no GitHub Actions run or commit status for `51d7191b`.

Thus:

```text
the console capture is credible;
the exact final tree is not cryptographically proven by that capture.
```

This does not invalidate the native MT5 evidence or the economic conclusion. It is a provenance gap that must be fixed for R6 by recording:

```text
exact generator commit
exact tree SHA
git status --porcelain = empty
test command/environment/output
test-output SHA256
CI run or equivalent immutable attestation
```

## 2.8 Fee, swap, and funding boundary

The deal ledgers include profit, commission, swap, and `DEAL_FEE`. All observed commission, swap, and fee values are zero.

The longest ten-year holding period is approximately 607 hours and P95 is approximately 506 hours. Therefore, zero historical tester funding must not be interpreted as proof of zero future CFD overnight financing.

The packet reports this limitation correctly. It does not affect the underpowered/contract-infeasible decision.

---

# 3. Exact H4 status and closure

## Primary locked status

```text
H4_RULE_CLEAN_UNDERPOWERED
```

That is the correct status under the committed precedence:

1. evidence invalid;
2. fewer than 100 ten-year trades;
3. other survivor failure;
4. small-account contract infeasible;
5. survivor.

The evidence checks pass, but the decade contains only 36 trades. The runner therefore stops at `UNDERPOWERED`.

## Other failed gate

```text
best 24-month contribution:
  locked maximum: 50.000000%
  actual:         54.798488%
```

The source also fails this concentration condition. It is not labelled generic `H4_RULE_CLEAN_FAIL` because the locked status ordering assigns `UNDERPOWERED` first.

## Secondary implementation fact

The target account is independently contract-infeasible:

```text
USD 1,000 at 0.25% risk:
  0 / 156 feasible

USD 1,000 at 0.50% risk:
  0 / 156 feasible

USD 1,000 at 1.00% risk:
  4 / 156 feasible
```

Minimum/median/maximum 0.01-lot initial stop risk:

```text
minimum:  $5.92
median:  $36.50
P95:     $95.31
maximum: $191.91
```

## Does this close H4?

**Yes.**

The valid terminal state is not permission to collect another H4 historical variant. The current H4 family is closed for:

```text
threshold adjustment
new time/session mask
previous-P/L gate
neighboring first-cross definition
hedge
profit lock
break-even
partial close
trailing stop
stop/target change
loss-date control
portfolio rescue
```

H4 may remain archived as a diagnostic benchmark. No further H4 repair experiment is authorized.

---

# 4. Meaning of the 0.69% ten-year drawdown

## What it does establish

The re-architected H4 source—one causal first-cross episode, one position, fixed USD 25 initial risk on USD 10,000—has low historical floating-equity drawdown:

```text
five-year native relative equity DD: 0.39%
ten-year native relative equity DD:  0.69%
```

That is a meaningful result. It strongly supports the diagnosis that the old H4 tail arose primarily from repeated episode exposure, uncontrolled concurrency, and fixed-lot monetary-risk variation.

## What it does not establish

It does not preserve the old return engine:

```text
old original H4:
  +$8,159.08 on $1,000
  39.49% DD
  307 trades

clean common-risk reference:
  +$486.82 on $10,000
  0.69% DD
  36 trades
```

These are different risk architectures and different capital bases. The new run bought low drawdown by using one position, fixed 0.25% reference risk, and very low incidence.

At a perfectly divisible USD 1,000 equivalent risk of USD 2.50, the 19.4728R decade would correspond to only approximately:

```text
$48.68 net
```

before any unmodelled funding. The actual Capital.com contract cannot express even that risk path.

Therefore:

```text
the drawdown mechanism is repaired;
the owner's return/DD objective is not solved;
the H4 source is not a portfolio admission candidate.
```

The 0.69% figure is not evidence that the earlier approximately 23% V3 hedge problem was solved while retaining its economics. It is evidence that radically reducing and normalizing exposure removes the drawdown.

---

# 5. Runtime and broker authorization

```text
NO RUNTIME OR BROKER ACTION IS AUTHORIZED.
```

The native tester uses `InpAllowDemoTrading=true` so that simulated orders can execute inside Strategy Tester. The startup ledger's `broker_action=true` describes that tester input; it does not authorize a chart attachment or broker operation.

The experiment runner has no CLI surface for:

```text
live
demo attachment
profile
chart
account
server
preset
order
```

The result JSON, source manifest, preregistration, and report Markdown all explicitly set the boundary to Strategy Tester research and `broker_action_authorized=false`.

---

# 6. Authorization decision for R6

## Decision

**Authorize the outcome-blind R6 opportunity census.**

Exact study name:

```text
R6_H4_DISTRIBUTION_BREAK_FAILED_RECLAIM_SHORT_V1
```

Authorized phase:

```text
market-structure opportunity census
causal next-tick availability
contract-risk feasibility
incidence and concentration only
```

Not authorized:

```text
standalone P/L
SL/TP outcome replay
MFE/MAE
portfolio join
H4 overlap/coverage join
correlation with H4
MT5 execution
demo or live attachment
```

Portfolio complementarity must remain sealed until a later standalone source passes its own preregistered gates.

---

# 7. Frozen R6 outcome-blind definitions

These definitions are the recommended exact lock. They must be committed before the census code or output.

## 7.1 Time and indexing convention

Evaluate on the first tick after a completed H4 bar.

At that decision tick:

```text
H4 shift 1:
  candidate completed breakdown bar B0

H4 shifts 2..7:
  six completed distribution bars
  shift 7 is oldest, shift 2 is newest

H4 shifts 8..13:
  six completed prior-impulse bars
  shift 13 is oldest, shift 8 is newest
```

No shift `0` OHLC or indicator value may be read for signal construction.

Use native broker bars. Do not forward-fill a missing H4 or H1 bar. A duplicate timestamp, non-monotonic series, invalid OHLC, or missing required completed bar makes the candidate unavailable.

## 7.2 ATR calculation

For timeframe `TF`:

```text
TR_t = max(
  high_t - low_t,
  abs(high_t - close_{t-1}),
  abs(low_t  - close_{t-1})
)
```

`ATR14` is Wilder's RMA:

```text
seed = arithmetic mean of first 14 valid TR values
ATR_t = (13 * ATR_{t-1} + TR_t) / 14
```

Only completed bars are used.

Locked references:

```text
A_impulse = H4 ATR14 at shift 8
A_box     = H4 ATR14 at shift 2
A_break   = A_box
A_reclaim = H1 ATR14 ending at the completed first reclaim-attempt bar
```

Insufficient ATR history or a nonpositive ATR is `DATA_UNAVAILABLE`, never a zero substitute.

## 7.3 Objective prior upward impulse

Using H4 shifts `13..8`:

```text
impulse_low   = minimum low
impulse_high  = maximum high
impulse_range = impulse_high - impulse_low
net_advance   = close(shift 8) - open(shift 13)
bullish_bars  = count(close > open)
final_location =
  (close(shift 8) - impulse_low) / impulse_range
```

The prior upward impulse passes only if all hold:

```text
net_advance   >= 1.50 * A_impulse
impulse_range >= 2.00 * A_impulse
bullish_bars  >= 4 of 6
final_location >= 0.75
```

No EMA period, date, session, H4 strategy state, or outcome statistic is part of this definition.

## 7.4 Six-H4-bar distribution box

Using H4 shifts `7..2`:

```text
box_high  = maximum high
box_low   = minimum low
box_width = box_high - box_low
box_mid   = (box_high + box_low) / 2
```

Width gate:

```text
1.00 * A_box <= box_width <= 3.00 * A_box
```

Acceptance tests:

1. At least four of six closes lie in the inner 60% of the box:

```text
box_low + 0.20 * box_width
  <= close
  <= box_high - 0.20 * box_width
```

2. At least four of the five adjacent chronological bar pairs have range-overlap ratio at least `0.25`:

```text
overlap =
  max(0, min(high_a, high_b) - max(low_a, low_b))

overlap_ratio =
  overlap / min(high_a - low_a, high_b - low_b)
```

3. Net box drift is limited:

```text
abs(close(shift 2) - open(shift 7))
  <= 0.75 * A_box
```

There is no neighboring width, overlap, close-band, or drift sweep.

## 7.5 Router context

At the first tick after breakdown-bar completion, compute the existing market-only Router V1 state from completed data.

Allowed:

```text
UPTREND
CHOP
```

Blocked:

```text
SHOCK
COMPRESSION
DOWNTREND
UNKNOWN
```

This router state is a causal market classification. It may not read H4 positions, H4 P/L, or any strategy ledger.

## 7.6 First H4 breakdown

The completed H4 shift-1 bar is the only breakdown bar for its immediately preceding six-bar box.

It passes only if all hold:

```text
close(shift 2) >= box_low
close(shift 1) <= box_low - 0.10 * A_break
close(shift 1) < open(shift 1)

body_fraction =
  abs(close - open) / (high - low)
body_fraction >= 0.50

close_location =
  (close - low) / (high - low)
close_location <= 0.25
```

The box is not held open waiting for a later breakdown. If the immediately following completed H4 bar does not pass, that box has no event. A later bar is evaluated only against its own newly formed immediate six-bar box.

## 7.7 First failed H1 reclaim

Freeze the broken level:

```text
L = box_low
```

After the H4 breakdown closes, inspect exactly the first six subsequently completed native H1 bars in chronological order.

For each H1 bar, calculate `A_reclaim` at that completed bar.

A reclaim attempt is the first H1 bar satisfying:

```text
high >= L - 0.10 * A_reclaim
```

Only that first attempt is classified. Later attempts are structurally unavailable.

It is a failed reclaim only if all hold:

```text
close <= L - 0.05 * A_reclaim
close < open

body_fraction =
  abs(close - open) / (high - low)
body_fraction >= 0.35

close_location =
  (close - low) / (high - low)
close_location <= 0.35
```

If the first attempt fails any one of those conditions, classify:

```text
FIRST_RECLAIM_NOT_REJECTED
```

and expire the episode. Do not inspect a later attempt.

If no attempt occurs in six completed H1 bars, classify:

```text
NO_RECLAIM_WITHIN_SIX_H1
```

and expire the episode.

## 7.8 Structural stop for contract-risk census

For a valid failed reclaim:

```text
structural_stop =
  max(reclaim_bar_high, box_low)
  + 0.25 * A_reclaim
```

Normalize upward to the next valid symbol tick.

No arbitrary stop floor, stop ceiling, stop cap, break-even, target, or outcome simulation is allowed in the census.

## 7.9 Duplicate box and signal suppression

Create:

```text
box_id = SHA256(
  rule_version |
  symbol |
  six distribution H4 open timestamps |
  box_low normalized to tick |
  box_high normalized to tick
)
```

There is at most one breakdown candidate for each `box_id`.

After a valid H4 breakdown, open one causal distribution episode for the symbol/direction. Suppress every later R6 candidate for that symbol/direction until the first of:

```text
a completed H4 close >= original box_mid
12 additional completed H4 bars after the breakdown
```

Only one failed-reclaim signal may be emitted from an episode. Suppression is independent of any trade result or position state.

## 7.10 Causal next-tick entry timestamp

The failed-reclaim decision becomes known only when its H1 bar completes.

The entry tick is:

```text
the first recorded tick belonging to the next H1 bar,
with tick sequence strictly after the failed-reclaim bar,
while the broker trade session is open
```

The tick may share the scheduled bar-boundary second; ordering is resolved by the recorded tick sequence, not by reading the prior bar before it is complete.

Require the entry tick within 15 minutes of the scheduled H1 close. Otherwise classify:

```text
ENTRY_TICK_UNAVAILABLE
```

For the short census record:

```text
entry_reference = tick bid
entry_ask       = tick ask
spread_points   = (ask - bid) / point
```

No subsequent tick or bar may be read for the opportunity record.

## 7.11 Outcome information structurally unavailable

The census builder may accept only:

```text
native H4 OHLC/timestamps
native H1 OHLC/timestamps
ordered XAUUSD ticks through the entry tick
causally computed Router V1 state
symbol/account contract snapshot
rule-lock JSON
input-data manifests
```

It must not accept, import, join, or discover:

```text
H4 order ledger
H4 deal ledger
H4 signal ledger
H4 position intervals
H4 magic or source ID
H4 entry or exit timestamps
H4 exposure episodes
H4 P/L
portfolio P/L
balance or equity
drawdown
MFE or MAE
win/loss labels
SL/TP hit labels
future high/low after entry
known H4 adverse dates
December 2025 identifiers
loss-cluster identifiers
```

The census output may contain structural-stop and minimum-contract-risk fields. It may not contain:

```text
target price
exit timestamp
profit
P/L
R outcome
win/loss
MFE/MAE
future path
portfolio overlap
correlation
```

A prefix-invariance test must prove that appending market data after an emitted entry tick cannot change any earlier census row.

---

# 8. Exact incidence gates and resolution of 100 versus 120

There is no discrepancy once the stages are separated.

```text
120 = minimum raw causal opportunities before contract/risk attrition
100 = minimum risk-qualified opportunities expected to remain available
      for a later exact standalone test
```

Both are mandatory.

## 8.1 Raw causal incidence gates

Count only events that pass:

```text
impulse
box
router
breakdown
first failed reclaim
duplicate suppression
entry-tick availability
```

Before lot/risk feasibility.

Required over `2016-07-01` through `2026-06-30`:

```text
raw opportunities >= 120

early half, 2016-07-01 through 2021-06-30:
  >= 40

late half, 2021-07-01 through 2026-06-30:
  >= 40

July-June buckets:
  at least 8 of 10 buckets have >= 5 opportunities

single July-June bucket share:
  <= 25% of decade opportunities

best contiguous 24-month share:
  <= 40% of decade opportunities
```

If any raw-incidence or temporal-concentration gate fails:

```text
R6_CENSUS_INSUFFICIENT_INCIDENCE
```

No neighboring definition may be run.

## 8.2 Reference research-risk gate

Using the captured contract and a USD 10,000 reference with USD 25 maximum initial risk:

```text
risk-qualified opportunities >= 100
early-half risk-qualified      >= 35
late-half risk-qualified       >= 35
risk-qualified coverage        >= 8 July-June buckets
```

Every accepted row must have minimum-contract initial risk `<= $25.00`.

Failure status:

```text
R6_CENSUS_REFERENCE_RISK_UNDERPOWERED
```

No standalone P/L is authorized.

## 8.3 Intended USD 1,000 deployment-risk gate

For the current Capital.com contract:

```text
initial equity:       $1,000
maximum initial risk: $2.50
broker minimum lot:   actual captured SYMBOL_VOLUME_MIN
broker lot step:      actual captured SYMBOL_VOLUME_STEP
```

A candidate is deployment-feasible only if the minimum permitted lot, using the normalized structural stop and exact contract calculation, risks no more than `$2.50`.

The census passes small-account feasibility only if:

```text
deployment-feasible opportunities >= 100
deployment-feasible / raw opportunities >= 80%
early-half deployment-feasible >= 35
late-half deployment-feasible  >= 35
deployment-feasible events occur in >= 8 July-June buckets
```

Failure status:

```text
R6_SMALL_ACCOUNT_CONTRACT_INFEASIBLE
```

That status does not authorize a smaller stop, different buffer, larger risk percentage, or excluded historical period.

---

# 9. Census-only implementation plan

## Commit R6-C1 — preregistration and locks only

Add:

```text
xau-usd/xauusd-phase1/docs/
  A1_XAU_R6_H4_DISTRIBUTION_BREAK_FAILED_RECLAIM_SHORT_V1_CENSUS_PREREG_2026_07_12.md

  A1_XAU_R6_H4_DISTRIBUTION_BREAK_FAILED_RECLAIM_SHORT_V1_RULE_LOCK.json

  A1_XAU_R6_OUTCOME_BLIND_CENSUS_SCHEMA_V1.json

xau-usd/xauusd-phase1/outputs/manifests/
  A1_XAU_R6_CENSUS_LOCK_MANIFEST_V1.json
```

The lock manifest must hash all three contract files.

This commit must contain:

```text
no detector code
no census output
no P/L code
no MT5 source change
```

## Commit R6-C2 — detector and tests only

Add:

```text
xau-usd/xauusd-phase1/scripts/
  build_a1_xau_r6_distribution_break_failed_reclaim_census.py
  validate_a1_xau_r6_outcome_blind_census.py

xau-usd/xauusd-phase1/tests/
  test_a1_xau_r6_distribution_break_failed_reclaim_definition.py
  test_a1_xau_r6_census_outcome_blind.py
  test_a1_xau_r6_census_contract_risk.py
  test_a1_xau_r6_census_manifest.py
```

Required tests:

```text
exact H4 shift mapping
no shift-0 signal input
Wilder ATR fixture parity
impulse boundary cases
box width/acceptance boundary cases
adjacent-overlap calculation
first-breakdown behavior
Router state allow/block
first reclaim attempt consumes the episode
successful/ambiguous first reclaim prevents later selection
six-H1 expiry
duplicate episode suppression
first-fresh-tick sequencing
15-minute tick expiry
prefix invariance
no H4 strategy-ledger dependency
forbidden outcome-field schema scan
exact OrderCalcProfit/contract-risk fixture
incidence and concentration gate fixtures
manifest completeness
no live/demo/attach/profile CLI surface
```

The implementation must not contain an exit simulator, target checker, P/L metric function, H4 ledger path, or portfolio join.

Run tests at the exact committed R6-C2 SHA with:

```text
clean git status
recorded commit SHA
recorded tree SHA
immutable output hash or CI run
```

## Commit R6-C3 — census evidence only

Generate:

```text
xau-usd/xauusd-phase1/outputs/reports/
  A1_XAU_R6_DISTRIBUTION_BREAK_FAILED_RECLAIM_CENSUS_20260712/
    A1_XAU_R6_DISTRIBUTION_BREAK_FAILED_RECLAIM_CENSUS_20260712.csv
    A1_XAU_R6_DISTRIBUTION_BREAK_FAILED_RECLAIM_CENSUS_20260712.json
    A1_XAU_R6_DISTRIBUTION_BREAK_FAILED_RECLAIM_CENSUS_20260712.md
    annual_incidence.csv
    contract_risk.csv
    input_data_manifest.json
    generator_manifest.json
    manifest.json
```

The generator manifest must contain:

```text
R6-C1 prereg SHA
rule-lock SHA
schema SHA
R6-C2 generator commit SHA
R6-C2 tree SHA
dirty_worktree=false
script SHA
test-file SHAs
market-data manifest SHAs
contract-snapshot SHA
output artifact SHAs
```

No code or threshold change is permitted in R6-C3.

## Locked census-row schema

Minimum required fields:

```text
schema_version
rule_version
rule_sha256
candidate_id
box_id
episode_id
symbol
router_state
impulse_start_h4_time
impulse_end_h4_time
box_start_h4_time
box_end_h4_time
breakdown_h4_time
reclaim_h1_time
decision_time
entry_tick_time
entry_tick_sequence
A_impulse
A_box
A_reclaim
impulse_low
impulse_high
impulse_range_atr
impulse_net_advance_atr
impulse_bullish_bars
impulse_final_location
box_low
box_high
box_width_atr
box_inner_close_count
box_overlap_pair_count
box_net_drift_atr
breakdown_distance_atr
breakdown_body_fraction
breakdown_close_location
reclaim_touch_distance_atr
reclaim_body_fraction
reclaim_close_location
entry_bid
entry_ask
spread_points
structural_stop
stop_points
volume_min
volume_step
contract_size
tick_size
tick_value_loss
minimum_contract_risk_usd
reference_risk_feasible
deployment_risk_feasible
availability_status
exclusion_reason
```

Explicitly absent:

```text
exit_time
target
profit
pnl
net_r
win
loss
mfe
mae
drawdown
equity
balance
H4 exposure
portfolio fields
```

## Census result statuses

Exactly one:

```text
R6_CENSUS_EVIDENCE_INVALID
R6_CENSUS_INSUFFICIENT_INCIDENCE
R6_CENSUS_REFERENCE_RISK_UNDERPOWERED
R6_SMALL_ACCOUNT_CONTRACT_INFEASIBLE
R6_CENSUS_PASS
```

`R6_CENSUS_PASS` authorizes only a new standalone preregistration review. It does not itself authorize a P/L run.

---

# 10. Is all XAUUSD specialist research economically irrelevant at USD 1,000?

## Decision

**No—not before R6's own contract-risk census.**

The H4 source is infeasible because its structural stops at `0.01` lot risked at least `$5.92`, with a `$36.50` median. R6 uses a different H1 failed-reclaim stop geometry and has no 350-point H4 stop floor. It could, in principle, produce sufficiently small monetary stops.

Under the captured contract:

```text
tick size:        0.01
tick value/lot:   $1.00 per tick
minimum lot:      0.01
minimum-lot value:$0.01 per point
```

A `$2.50` risk budget therefore corresponds to approximately:

```text
250 XAUUSD points
```

before conservative price normalization.

## Exact contract-risk calculation

Do not use a hardcoded `stop_points * 0.01` formula in R6. For every candidate, calculate:

```text
risk_min_usd =
  abs(
    OrderCalcProfit(
      ORDER_TYPE_SELL,
      XAUUSD,
      SYMBOL_VOLUME_MIN,
      entry_bid,
      normalized_structural_stop + one_symbol_tick
    )
  )
```

or an independently validated mathematically equivalent calculation from the captured symbol contract.

A candidate is feasible only if:

```text
volume_min and volume_step are valid
stop satisfies broker stop/freeze rules
risk_min_usd <= $2.50
all inputs are finite and positive
```

The decade must then satisfy the deployment-frequency gates in §8.3.

If it does not, XAUUSD research may remain relevant for a genuinely smaller contract or materially larger capital base, but it is economically irrelevant for deployment under the current USD 1,000 / 0.01 objective. No standalone R6 P/L run should then be authorized for that current deployment objective.

---

# 11. Hard NO-GO conditions

Any one of the following stops R6 or preserves the H4 closure:

## Evidence and causality

```text
preregistration not committed before code
rule/schema hash mismatch
dirty or unrecorded generator tree
native market-data manifest missing
bar timestamp duplicate/non-monotonic
missing required completed bar
shift-0 signal input
noncausal ATR
future bar/tick read after entry tick
prefix-invariance failure
```

## Outcome leakage

```text
H4 P/L input
H4 position/exposure input
H4 loss-date input
H4 episode ID input
portfolio P/L or drawdown input
MFE/MAE or exit-path input
known-loss-period filter
post-entry price path in census
```

## Researcher degrees of freedom

```text
neighboring impulse threshold
neighboring box width
neighboring overlap threshold
neighboring body/close threshold
alternate reclaim window
second reclaim attempt
hour/day/month mask
q55 sibling
R5 relabel
H4 threshold or hedge repair
portfolio rescue
```

## Incidence, concentration, and contract

```text
raw decade opportunities < 120
either five-year half < 40
fewer than 8/10 buckets with >=5 events
single bucket >25%
best 24 months >40%
reference-risk-qualified <100
deployment-feasible <100
deployment-feasible <80% of raw
invalid or uncaptured symbol contract
minimum contract risk cannot be computed
```

## Runtime and phase boundary

```text
any standalone P/L in census phase
any MT5 EA execution in census phase
any demo/live attachment
any preset/profile change
any broker order
any portfolio test
```

---

# Single next authorized action

```text
Create and commit R6-C1 only:
  the R6 census preregistration,
  exact rule lock,
  outcome-blind schema lock,
  and their SHA256 lock manifest.
```

Do not implement the detector, open P/L, run MT5, or join H4 evidence in that same commit.

---

# Final review checklist

```text
[PASS] Exact commit is four commits ahead of reviewed base.
[PASS] Completeness amendment is disclosed and non-economic.
[PASS] 224 INI inputs exactly match 224 native inputs in both horizons.
[PASS] Explicit legacy-mask authority is false.
[PASS] Native mask strings are sentinel-disabled.
[PASS] Zero legacy-mask blocks.
[PASS] Minimum-lot risk requests do not round upward.
[PASS] One position maximum.
[PASS] Native positions are one-entry/one-exit and volume matched.
[PASS] Order/deal/trade/P&L counts reconcile.
[PASS] Compile is 0 errors / 0 warnings.
[PASS] Source and root manifests cross-reconcile.
[PASS] Account/symbol contract is captured.
[PASS] No order or management failures.
[PASS] H4 status is UNDERPOWERED.
[PASS] H4 family is closed.
[PASS] USD 1,000 H4 implementation is contract-infeasible.
[PASS] No runtime/broker action is authorized.
[CAVEAT] 910-test capture is not exact-commit-bound; fix for R6.
[AUTHORIZED] R6 outcome-blind census preregistration phase only.
[NOT AUTHORIZED] R6 standalone P/L or portfolio testing.
```
