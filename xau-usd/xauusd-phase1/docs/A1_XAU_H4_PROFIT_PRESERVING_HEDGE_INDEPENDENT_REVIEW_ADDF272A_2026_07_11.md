# Independent Review — Commit `addf272a`
## XAUUSD H4 Risk Architecture, Hedge Closure, Contract Granularity, and Next Research Direction

**Repository:** `maksoftwares/algo-trading-system`  
**Branch:** `codex/xau-router-entry-hold-audit`  
**Exact commit:** `addf272a06d1d795376f2eb0a57741af2c95562b`  
**Canonical findings reviewed:** `xau-usd/xauusd-phase1/docs/A1_XAU_H4_PROFIT_PRESERVING_HEDGE_FINDINGS_2026_07_11.md`  
**Review date:** 2026-07-11  
**Boundary:** research-only. No live/demo broker action, chart attachment, preset arming, profile mutation, order placement, or deployment is authorized.

---

# Executive decision

```text
OVERALL EVIDENCE:              VALID_WITH_MATERIAL_LIMITATION
DEPLOYMENT:                    NO_GO
ORIGINAL H4:                   QUARANTINE
MECHANICAL HEDGE LANE:         CLOSED
V1 FLOATING-HIGH-WATER RESULT: DIAGNOSTIC_ONLY
V3 TOTAL-MTM HEDGE RESULT:     VALID ECONOMIC FAILURE
R5 Q55 SPECIALIST:             REJECT / CELL CLOSED
H4 RULE-CLEAN RESULT:          INVALID AS LABELLED; EXACT RERUN REQUIRED
CURRENT $1,000 / 0.01 GOAL:    NOT PRACTICALLY EXPRESSIBLE
```

The commit contains a strong evidence packet. The source transformations are pinned and hash-addressed, the V3 settlement-synchronized hedge implementation is causally credible, the R5 probe was one preregistered cell rather than a parameter search, and the losing results are reported honestly.

However, I found one material implementation/evidence defect that the existing tests and the reported independent audit did not detect:

> The generated H4 `rule_clean_common_risk` tester INI sets the legacy hour/day mask strings to empty, but the native MT5 report proves the executed run still used `InpBlockedEntryDayHoursCsv=5:20` and `InpBlockedLongEntryHoursCsv=3,10,13,14`.

The H4 order ledger also contains `blocked_entry_day_hour` guard events. The likely cause is MT5 treating an empty string in the generated INI as “retain the prior tester value” instead of an explicit empty-string override. The test suite verifies the generated INI, not the effective values printed by the native MT5 report.

Consequences:

```text
The 36-trade / PF 2.59 / DD 0.69% result is not a rule-clean qualification.
The reported rule-clean trade census is incomplete.
The small-account feasibility census was derived from a mask-contaminated order log.
The original fixed-lot, structural first-cross, hedge-V3, and R5 failure findings are not all invalidated.
```

The immediate next experiment must therefore be an **effective-input-clean exact rerun**, not another hedge, threshold, source weight, exit rule, or new H4 optimization.

---

# A. Feasibility of approximately USD 8,000 net with approximately 10% DD

## A1. Mathematical/economic feasibility

Starting with USD 1,000 and earning USD 8,000 means ending near USD 9,000:

```text
Total ten-year net return: 800%
Approximate CAGR:          24.57%
Maximum desired DD:        approximately 10%
Approximate CAGR/DD:       2.46
```

That is mathematically possible. It is also an unusually demanding return-to-drawdown requirement for a retail single-symbol CFD system.

The original H4 result proves only that the **return number** can be reached under an unsafe fixed-lot exposure path:

```text
Original ten-year net:                 +$8,159.08
Original max relative floating DD:       39.49%
```

A simple risk-scaling diagnostic illustrates the gap. If H4 performance scaled linearly with risk:

```text
Net at a 10% DD scale ≈ $8,159.08 × 10 / 39.49 ≈ $2,066
Net at a 12% DD scale ≈ $8,159.08 × 12 / 39.49 ≈ $2,479
```

Therefore, the current path needs roughly:

```text
3.87× better return per unit of DD
```

to reach USD 8,000 at 10% DD. That improvement cannot honestly be manufactured by selecting another historical hedge threshold.

### Economic verdict

```text
Abstractly feasible:                  YES
Demonstrated by the current system:   NO
Plausible from H4 risk scaling alone: NO
```

A feasible portfolio would need:

```text
a safely risk-normalized H4 source;
at least two additional independently profitable sources;
low enough cross-source drawdown coincidence;
and integrated floating-equity control.
```

None of those four conditions is currently established.

## A2. Broker contract granularity

The committed H4 evidence reports original 0.01-lot stop risk ranging approximately from:

```text
minimum observed: $5.92
maximum observed: $191.91
```

The original H4 account allowed:

```text
maximum simultaneous positions:          14
maximum aggregate initial stop risk: $1,020.64
initial test equity:                 $1,000
```

So the original maximum aggregate initial risk was approximately `102.06%` of initial equity.

For the widest observed 0.01-lot stop, the minimum capital required to keep that one trade inside a fixed risk cap is:

| Maximum risk per trade | Required capital |
|---:|---:|
| 0.25% | $76,764 |
| 0.50% | $38,382 |
| 1.00% | $19,191 |

For a USD 1,000 account, the equivalent lot required to risk only 0.25% on that widest historical stop is:

```text
approximately 0.00013 standard lot
```

A practical broker step of `0.0001` standard lot or smaller is therefore needed to express every observed H4 stop near 0.25% risk.

The current H4 stop floor itself is 350 points. At 0.01 lot, that is approximately USD 3.50 before any larger structural stop. Therefore, even the minimum permitted stop is already above a USD 2.50 risk budget:

```text
$2.50 = 0.25% of a $1,000 account
```

### Granularity verdict

```text
0.01 minimum + $1,000 + 0.25% risk:
  mechanically incompatible with the current H4 stop geometry.

0.01 minimum + $1,000 + 10% portfolio DD:
  not safely expressible across the observed H4 stop distribution.

Required:
  smaller effective contract, materially more capital,
  or a strategy with much smaller naturally valid monetary risk.
```

The stop must not be tightened merely to make the lot fit.

## A3. Strategy architecture feasibility

The present architecture does not provide three independent specialists:

```text
H4: historically profitable, unsafe, long/uptrend concentrated
R1 pullback: same broad R1 long regime and historically rule-masked
R2 sources: do not overlap H4 exposure and did not offset its DD episodes
R5 q55: independent and available, but materially loss-making
```

The existing short sources had zero overlap with H4 exposure intervals and worsened major H4 drawdown episodes in aggregate. R5 solved opportunity coverage and independence, but failed standalone alpha.

### What would falsify a conditional “feasible in principle” answer

The objective should be considered structurally falsified for the present XAUUSD program if, after a clean common-risk implementation:

1. H4 cannot produce positive P95-cost expectancy with standalone floating DD at or below 8%.
2. Two genuinely independent new sources cannot each pass standalone gates.
3. An integrated equal-risk portfolio cannot remain at or below 10% relative floating DD.
4. The required return/DD only appears when legacy P/L masks, session masks, dynamic historical-loss controls, or excessive risk are restored.
5. The minimum contract remains too large for the intended capital.
6. Locked forward evidence fails despite historical profitability.

---

# B. What is actually wrong with H4?

## B1. Primary weakness: concurrent clustering and repeated episode entries

The original H4 logic treated an already-above-box state as another breakout. The repaired first-cross rule requires:

```text
previous completed H4 close <= box high
and current completed H4 close > box high
```

instead of simply requiring the current close to be above the box.

The original H4 produced:

```text
307 ten-year trades
maximum 14 simultaneous positions
maximum aggregate initial stop risk $1,020.64 on $1,000
seven-position December 2025 stop cluster: approximately -$866.37
```

The first-cross / one-position structural repair produced:

```text
74 ten-year trades
PF 2.3996
net +$1,743.43
max relative equity DD 14.49%
```

Compared with the original:

```text
trade count: 307 -> 74
net retention: approximately 21.4%
DD: 39.49% -> 14.49%
```

This is strong evidence that most of the original headline profit and risk arose from repeated exposure to the same broad bullish episode.

## B2. Co-primary weakness: fixed-lot risk growth

The system used fixed `0.01` lot while XAU price, volatility, and structural stop width varied materially. The observed per-ticket stop risk spans more than `32×`.

That means:

```text
the same 0.01 order is not the same risk through time;
later/high-volatility trades can dominate the equity path;
and nominal trade count understates actual risk concentration.
```

Risk normalization is not optional.

## B3. Entry edge

There is evidence of a real signal clue:

```text
original H4 PF:                2.4968
first-cross H4 PF:             2.3996
heat/lock variants:            positive
```

But the clean edge is not yet fully established because:

```text
the structural-parity result intentionally retains legacy selection rules;
the “rule-clean” result actually retained two legacy hour/day masks at runtime;
and only 36 trades executed in that contaminated common-risk ten-year run.
```

So the defensible statement is:

> H4 contains a promising long/uptrend episode edge, but no admissible rule-clean common-risk specialist has yet been proven.

## B4. Exit geometry

Exit geometry is a secondary concern, not the first repair target.

Evidence:

```text
all original losing H4 positions reached their full protective stop;
blanket regime exits damaged profitable long holds;
high-water hedging reduced recovery;
V3 correctly fixed state synchronization but still produced only
+$3,722.21 with 23.68% DD.
```

This does not prove the 2R exit is optimal. It proves that exit/hedge repair has not solved the primary exposure problem.

## B5. H4 decision

```text
Do not deploy it.
Do not run another hedge threshold.
Do not fit an exit to December 2025 or 2021.
Do not permanently discard the economic mechanism yet.
```

Primary disposition:

```text
QUARANTINE AND RADICALLY RE-ARCHITECT AS:
  one causal breakout episode;
  fixed initial risk;
  static aggregate open-risk cap;
  no legacy P/L/time masks;
  no dynamic equity-curve rescue.
```

Under the current USD 1,000 / 0.01 contract, it remains practically non-executable at the desired risk.

---

# C. Single minimum next H4 experiment

## Experiment name

```text
A1_XAU_H4_RULE_CLEAN_EFFECTIVE_INPUT_RERUN_V2
```

## Why this must be next

The current `rule_clean_common_risk` result is not rule-clean in the actual MT5 run.

Generated INI:

```text
InpBlockedEntryDayHoursCsv=
InpBlockedLongEntryHoursCsv=
```

Native MT5 report:

```text
InpBlockedEntryDayHoursCsv=5:20
InpBlockedLongEntryHoursCsv=3,10,13,14
```

The existing unit test checks the generated INI only. It does not compare all effective native-report inputs against the locked contract.

No new H4 economic change should be tested until that evidence defect is closed.

## Locked architecture

Retain exactly the already preregistered structural repair:

```text
first completed-H4 cross of the box only;
long R1/uptrend route only;
one open H4 position;
one position identity;
market-session permanent expiry;
minimum-lot excess risk block;
fixed 2R target;
no management overlay.
```

This experiment is not allowed to introduce another alpha rule.

## Exact allowed source change

Add an explicit, nonempty, fail-closed switch such as:

```text
InpLegacySelectionMasksEnabled
```

Rules:

```text
structural control: true
rule-clean run:     false
```

When false, the source must skip every legacy mask function regardless of the string inputs.

Do not rely on empty strings to reset MT5 tester state.

Also require a native-report effective-input parser. The run fails if the native MT5 report does not exactly match every locked input.

## Dates

```text
Five-year development:
  2021-07-01 -> 2026-06-30

Ten-year development:
  2016-07-01 -> 2026-06-30
```

Both remain development data.

## Capital and risk convention

```text
Reference equity:          $10,000
Compounding:               OFF
Risk per trade:            $25 = 0.25% of initial equity
Maximum H4 open risk:      0.25% because one position is allowed
Volume:                    round down to broker step
Minimum lot too large:     block
Stop geometry:             unchanged
Target:                    fixed 2R
```

Also generate a deterministic USD 1,000 feasibility table for:

```text
0.25% risk
0.50% risk
1.00% risk
```

Do not create synthetic profit for blocked trades.

## Cost convention

Report all three:

```text
NATIVE:
  exact real-tick MT5 spread + native commission/swap/fee

EXPECTED:
  NATIVE + 0.05R adverse execution/holding overlay

HARD STRESS:
  NATIVE + 0.10R adverse execution/holding overlay
```

Before any H4 promotion discussion, replace the provisional holding overlay with a documented broker funding model. H4 positions can remain open for days or weeks; an exact tester result showing zero swap/fee is not sufficient proof of live economics.

## Required standalone metrics

```text
trades
win rate
realized W/L
PF
expectancy per trade in R
net R and USD
P95-stress net and PF
maximum relative floating-equity DD
maximum monetary equity DD
maximum balance DD
maximum concurrent positions
maximum aggregate initial risk
minimum-lot blocks
legacy-mask block count
cost_R distribution
holding-time distribution
funding-cost distribution
calendar/JUL-JUN bucket performance by EXIT time
top-10-winners-removed net
top-3-winning-days-removed net
best-year contribution
best-24-month contribution
block-bootstrap confidence intervals
```

## Evidence pass

The experiment is valid only if:

```text
native report effective inputs exactly match the lock;
InpLegacySelectionMasksEnabled=false;
native report contains no effective legacy hour/day masks;
previous-month P/L gate=false;
zero blocked_entry_day_hour;
zero blocked_long_entry_hour;
zero order failures;
zero management failures;
compile 0 errors / 0 warnings;
source, EX5, config, report, order, deal, and signal hashes manifest correctly;
all trades reconcile by native position ID;
all P/L is tester-currency USD;
actual report leverage and symbol contract are captured.
```

## H4 survivor pass

H4 remains research-eligible only if all hold:

```text
ten-year trades >= 100
five-year and ten-year net > 0
five-year and ten-year PF >= 1.30
hard-stress PF >= 1.20
hard-stress expectancy > 0R
block-bootstrap 5th-percentile expectancy > 0R
block-bootstrap 5th-percentile PF > 1.00
maximum relative floating-equity DD <= 8.00%
maximum H4 open initial risk <= 0.25%
top-10-winners-removed net > 0
top-3-winning-days-removed net > 0
>= 6/10 nonoverlapping July-June buckets positive
early half net > 0
late half net > 0
best year <= 35% of net
best 24-month block <= 50% of net
```

## Stop condition that closes H4

Close the H4 direction for the current strategy family if a valid effective-input-clean run:

```text
has negative hard-stress expectancy;
has lower confidence-bound expectancy <= 0R;
has PF < 1.30;
has floating DD > 8%;
remains below 100 trades because only legacy masks/minimum-lot selection made it look strong;
or requires another historical P/L/session/DD repair.
```

If it passes economically but is blocked by minimum-lot granularity, close it for the current Capital.com USD 1,000 implementation and retain it only for a smaller-contract or materially larger-capital account.

## Untouched protocol afterward

No historical observation through 2026-06-30 is untouched.

After final source/risk lock:

```text
H4 standalone forward:
  longer of 12 calendar months or 30 mature H4 trades

Integrated portfolio forward:
  longer of 6 calendar months or 200 mature portfolio trades
```

No rule change, excluded date, threshold change, or restart of the evidence clock without a new version.

---

# D. Next genuinely independent specialist

## Recommended specialist

```text
R6_H4_DISTRIBUTION_BREAK_FAILED_RECLAIM_SHORT_V1
```

This is not another q55 M5 impulse/retest threshold.

## Regime owned

```text
UPTREND_WEAKENING / DISTRIBUTION-TO-DOWNTREND TRANSITION
```

It is not a generic `CHOP` short and not the strict established R2 downtrend continuation state.

## Causal trigger family

Use completed bars only:

1. **Context**
   - Router state at signal is `UPTREND` or `CHOP`.
   - `SHOCK` and established `DOWNTREND` are excluded.
2. **H4 distribution box**
   - exactly six completed H4 bars;
   - at least four closes remain within the box;
   - range width is between one and three H4 ATR14;
   - box is formed after an objective prior upward impulse;
   - all values fixed before outcome review.
3. **First H4 breakdown**
   - previous completed H4 close is at or above the box low;
   - current completed H4 close is below the box low;
   - bearish body fraction at least 0.50;
   - close location at or below 0.25.
4. **Failed reclaim**
   - within the next six completed H1 bars, price retests the broken box low from below;
   - the first completed H1 reclaim attempt closes back below the level;
   - only one signal is allowed per box.
5. **Execution**
   - sell on the next eligible tick;
   - stop above the H1 retest high plus 0.25 H1 ATR;
   - target fixed at 2R;
   - one position;
   - no BE, partial, trailing, daily loss stop, or session mask.

The exact box/impulse definitions must be preregistered before any P/L is opened. No threshold grid is authorized.

## Why this may complement H4 without mining H4 loss dates

The economic thesis is independent:

> After a mature bullish impulse, multi-H4 acceptance failure and a failed reclaim of the distribution floor indicate a transition from accumulation/continuation to supply-led decline.

This is a market-structure hypothesis. It does not refer to:

```text
H4 P/L
H4 open positions
H4 drawdown dates
December 2025
the V3 hedge trigger
or the q55 failure
```

It may naturally overlap H4 adverse exposure because H4 is long during mature bullish regimes, but that overlap is evaluated only after standalone qualification.

## Expected frequency

```text
Target: 10–25 trades per year
Ten-year expected sample: 100–250 trades
```

If an outcome-blind census finds fewer than 100 decade opportunities, resolve `INSUFFICIENT_INCIDENCE` before exact-MT5 P/L testing.

## Fixed risk/exit model

```text
Reference equity: $10,000
Risk per trade:   0.25% fixed initial equity
Maximum source open risk: 0.25%
Target:           2R
Compounding:      OFF
Minimum lot excess: block
```

## Evidence required before exact MT5

Generate an outcome-blind opportunity census that contains no H4 trade ledger or P/L fields.

Required census gates:

```text
>= 120 raw opportunities
opportunities in >= 8 calendar years
>= 40 opportunities in 2016-2020
>= 40 opportunities in 2021-2026
no year > 25% of opportunities
all timestamps causal
all completed-bar joins exact
0 outcome fields available to the detector
```

Hash-lock the rule after the census and before opening any result.

## Standalone exact-MT5 gates

```text
trades >= 100
net > 0 under hard stress
PF >= 1.30
hard-stress PF >= 1.20
realized W/L >= 1.80
expectancy > 0R
bootstrap 5th-percentile expectancy > 0R
bootstrap 5th-percentile PF > 1.00
maximum relative equity DD <= 8%
top-10-winners-removed net > 0
top-3-winning-days-removed net > 0
>= 6/10 July-June buckets positive
early and late halves positive
best year <= 35% of net
best 24 months <= 50% of net
```

No combined portfolio report may rescue a standalone failure.

## Independence and coverage gates

Only after standalone PASS may the sealed H4 ledger be opened.

Require:

```text
absolute daily closed-P/L correlation with H4 <= 0.30
same-opportunity overlap with H4 <= 20%
signals in >= 30% of H4 exposure episodes
signals in >= 3 independently defined H4 adverse episodes
no use of H4 position state in the R6 signal
no portfolio metric used to alter R6
```

The final integrated equal-risk test must show:

```text
portfolio PF and expectancy remain positive under hard stress;
portfolio relative floating DD <= 10%;
R6 does not worsen the H4 drawdown tail;
and no single source contributes > 50% of portfolio net.
```

## R6 no-go conditions

```text
standalone fail
sample < 100
need for an hour/month/date mask
need for H4 active-position awareness
negative hard-stress net
DD > 8%
concentration failure
high correlation or same-opportunity duplication
coverage limited to one known H4 loss period
```

One failed locked cell closes this R6 definition. No neighboring-threshold sweep.

---

# E. Should the new specialist be explicitly bearish during H4 exposure?

It may be an explicitly bearish transition specialist.

It must **not** be developed as an H4 hedge.

Correct sequence:

```text
1. Define the bearish market behavior without H4.
2. Build an outcome-blind opportunity census without H4 P/L.
3. Lock the rule.
4. Run standalone exact MT5.
5. Decide standalone PASS/FAIL.
6. Only then unseal H4 exposure and evaluate complementarity.
```

Forbidden signal inputs:

```text
H4 currently open
H4 unrealized P/L
H4 high-water drawdown
H4 loss episode ID
known adverse calendar date
```

This prevents outcome leakage and avoids disguising a fitted hedge as independent alpha.

---

# F. Is a smaller contract or more capital required?

## Answer

```text
YES
```

For the H4 family, a USD 1,000 account with a 0.01 minimum cannot express stable 0.25% risk.

Required practical standard:

```text
effective minimum volume <= 0.0001 standard lot
effective volume step    <= 0.0001 standard lot
```

At the widest observed stop, 0.0001 lot would risk approximately:

```text
$1.92
```

which fits inside a USD 2.50 risk budget.

Alternatively, with 0.01 minimum:

```text
capital for 1.00% max risk: approximately $19,191
capital for 0.50% max risk: approximately $38,382
capital for 0.25% max risk: approximately $76,764
```

The exact broker/account qualification must export and hash:

```text
SYMBOL_VOLUME_MIN
SYMBOL_VOLUME_STEP
SYMBOL_VOLUME_MAX
SYMBOL_TRADE_CONTRACT_SIZE
SYMBOL_TRADE_TICK_SIZE
SYMBOL_TRADE_TICK_VALUE
SYMBOL_TRADE_TICK_VALUE_LOSS
stops level
freeze level
account leverage
margin mode
hedging/netting mode
```

A cent/micro account is acceptable only if those effective contract figures are verified. The marketing label “cent account” is not evidence.

More capital solves risk granularity. It does not create a new edge or guarantee the USD 8,000 objective.

---

# G. Implementation and evidence-quality review

## G1. Strong work that should be preserved

### Hash and provenance discipline

The commit contains:

```text
preregistration hashes
locked-input hashes
source manifests
compiled source hashes
EX5 hashes
compile-log hashes
native report hashes
order/deal/signal ledger hashes
root manifests
```

Exact evidence directories are marked binary in `.gitattributes`, preserving bytes.

### V3 hedge implementation

The V3 builder:

```text
sums realized primary profit, commission, swap, and fee;
synchronizes from deal history;
defers hedge decisions on primary settlement ticks;
rearms after successful release;
and removes the floating-only high-water invariant defect.
```

The V3 failure is therefore credibly economic rather than an obvious implementation failure.

### R5 methodology

R5 was:

```text
one preregistered cell
one fixed q55 rule
fixed 2R
one entry per day
one position
causal UPTREND/CHOP routing
no portfolio rescue
```

It failed by a wide margin. Its rejection should stand.

## G2. Material defect — effective MT5 inputs not verified

### Generated rule-clean INI

```text
InpBlockedEntryDayHoursCsv=
InpBlockedLongEntryHoursCsv=
```

### Native MT5 report

```text
InpBlockedEntryDayHoursCsv=5:20
InpBlockedLongEntryHoursCsv=3,10,13,14
```

### Existing test

The test only parses the generated config and asserts the strings are empty.

### Consequence

```text
The “rule-clean” H4 result is mask-contaminated.
Its 36 trades, PF, net, and incidence cannot be used for admission.
```

This finding contradicts the claim that no manifest/config discrepancy exists. The files are individually hash-consistent; the defect is that the runner verifies the intended INI, not the effective inputs MT5 reports at runtime.

## G3. R5 has the same verifier design gap

`horizon_evidence()` reads:

```text
actual_inputs = parse_tester_inputs(Path(result["tester_config"]))
```

It compares the generated INI to the preregistration, not the native MT5 report.

R5’s order summary contains no hour/day mask guard reasons and its result is deeply negative, so the q55 rejection remains defensible. Still, the effective-input verifier must be repaired before another specialist run.

## G4. Generic minimum-lot risk behavior

The base EA’s historical risk-normalized path normalizes the requested volume. The episode-repair builder adds a special patch that returns zero when requested volume is below broker minimum.

That safety rule belongs in the shared risk-sizing implementation and test suite, not only in one derived H4 source.

Required invariant:

```text
never round a below-minimum risk request upward;
block it with MINIMUM_LOT_RISK_EXCESS.
```

## G5. Fees, swap, and financing

The fee-instrumented H4 deal logs show exact:

```text
commission = 0
swap       = 0
fee        = 0
```

including positions held for days or weeks.

That is valid tester evidence. It is not sufficient proof that the intended live Capital.com CFD has no overnight funding cost.

Before H4 qualification:

```text
document the broker financing formula;
include triple-charge timing;
measure demo/live statement treatment;
run expected and P95 funding overlays.
```

The ordinary base EA deal logger also omits `DEAL_FEE`; new common runners should log it natively.

## G6. Currency names

The packet correctly states that legacy `pnl_aed`/`profit_aed` fields contain tester-currency USD in the R5 packet.

This is not a numeric error, but it is a recurring schema hazard.

Migrate new reports to:

```text
pnl_account_currency
account_currency
pnl_usd only when conversion is proven
```

## G7. Leverage and account settings

Generated tester configurations request leverage `200`, while native MT5 reports show actual leverage `1:50`.

The native report is authoritative. Future runners must parse and assert:

```text
actual leverage
margin mode
account currency
company/server
```

before using margin or integrated exposure claims.

## G8. Test execution provenance

The user reports:

```text
894 local tests passed
```

No GitHub workflow run or combined commit status is visible for the exact commit.

Commit:

```text
local test command
environment
Python version
pytest version
full output
exit code
artifact hash
```

or enable CI on this branch.

## G9. Historical evidence boundary

Everything through 2026-06-30 remains development data.

The commit can:

```text
reject ideas
diagnose mechanics
prove causal implementation
and establish risk incompatibility
```

It cannot confirm future profitability.

---

# H. Ordered Codex implementation plan

## Commit 1 — preregister effective-input integrity repair

Add:

```text
xau-usd/xauusd-phase1/docs/
  A1_XAU_EFFECTIVE_MT5_INPUT_INTEGRITY_REPAIR_PREREG_2026_07_11.md
```

Lock:

```text
the exact expected effective inputs;
the two contaminated H4 inputs;
the zero-mask policy;
the five-/ten-year dates;
the no-alpha-change boundary;
the pass/fail statuses.
```

No MT5 result in this commit.

## Commit 2 — implement effective-input verification

Add:

```text
xau-usd/xauusd-phase1/scripts/
  parse_mt5_effective_inputs.py
  verify_a1_xau_effective_inputs.py
```

Modify:

```text
run_a1_xau_h4_episode_repair_exact.py
run_a1_r5_pre_downtrend_break_short_v1_exact.py
run_a1_xau_m5_momentum_backtest_variants.py
```

Requirements:

```text
parse every Inputs row from native MT5 HTML;
compare native effective values, not only generated INI;
fail on missing, extra, or unequal locked input;
record INI value and effective value side by side;
assert actual leverage/account currency/server/build;
```

Add tests:

```text
tests/test_mt5_effective_inputs.py
tests/test_a1_xau_h4_episode_repair_exact.py
tests/test_a1_r5_pre_downtrend_break_short_v1_exact.py
```

Test fixture must reproduce:

```text
INI empty
native report nonempty
=> hard failure
```

## Commit 3 — explicit legacy-mask disable

Modify the derived H4 source builder:

```text
scripts/build_a1_xau_h4_episode_repair_source.py
```

Add one explicit input:

```text
InpLegacySelectionMasksEnabled
```

Behavior:

```text
true  -> preserve frozen structural control
false -> bypass every legacy hour/day mask
```

Also move minimum-lot fail-closed sizing into a common tested helper or patch the core source with a default-safe versioned input.

Tests:

```text
test_legacy_masks_cannot_execute_when_disabled
test_empty_string_is_not_used_as_disable_authority
test_minimum_lot_never_rounds_risk_up
```

No result yet.

## Commit 4 — run the single authorized H4 experiment

Run:

```text
A1_XAU_H4_RULE_CLEAN_EFFECTIVE_INPUT_RERUN_V2
```

Generate:

```text
outputs/reports/A1_XAU_H4_RULE_CLEAN_EFFECTIVE_INPUT_RERUN_V2_20260711/
  report.md
  report.json
  effective_inputs.json
  five_year/
  ten_year/
  order/deal/signal ledgers
  cost_and_funding_report.md
  small_account_feasibility.csv
  manifest.json
  manifest.sha256
```

Assign one status:

```text
H4_RULE_CLEAN_SURVIVOR
H4_RULE_CLEAN_FAIL
H4_RULE_CLEAN_UNDERPOWERED
H4_CONTRACT_GRANULARITY_INFEASIBLE
H4_EVIDENCE_INVALID
```

Stop for review.

## Commit 5 — conditional H4 architecture preregistration

Only if Commit 4 produces `H4_RULE_CLEAN_SURVIVOR`, preregister one static architecture:

```text
A1_XAU_H4_STATIC_RISK_CAPPED_EPISODIC_V1
```

Allowed architecture:

```text
first-cross episode identity;
fixed 0.25% initial-equity risk;
maximum 0.50% H4 open initial risk;
maximum two distinct open episode positions;
no dynamic equity throttle;
no hedge;
no time/P&L masks.
```

Do not run it in the same commit.

If Commit 4 does not survive, skip this commit and close H4.

## Commit 6 — R6 outcome-blind opportunity census

Add:

```text
docs/A1_XAU_R6_H4_DISTRIBUTION_BREAK_FAILED_RECLAIM_SHORT_V1_PREREG_2026_07_11.md
scripts/build_a1_xau_r6_opportunity_census.py
tests/test_a1_xau_r6_opportunity_census.py
outputs/reports/A1_XAU_R6_OPPORTUNITY_CENSUS_20260711.*
```

The census must fail if H4 trade/P&L fields are present.

## Commit 7 — R6 exact standalone test

Only if census gates pass.

Add or modify:

```text
mt5/Experts/A1XauM5MomentumContinuationExecutor.mq5
  default-off new signal/router mode

scripts/run_a1_xau_r6_distribution_break_failed_reclaim_exact.py
tests/test_a1_xau_r6_distribution_break_failed_reclaim.py
outputs/reports/A1_XAU_R6_DISTRIBUTION_BREAK_FAILED_RECLAIM_EXACT_20260711/
```

One cell only. No portfolio test if standalone fails.

## Commit 8 — integrated harness only after three qualified sources

Do not build a promotional integrated portfolio from the current source set.

Prerequisites:

```text
H4 rule-clean survivor or approved replacement;
two other rule-clean standalone survivors;
independence gates passed;
contract granularity compatible.
```

Then build one master exact-MT5 portfolio with:

```text
unique source identities and magics;
account-wide family mutex;
fixed initial-risk sizing;
shared 10% floating-equity hard stop;
tick-level equity export;
shared margin and order reconciliation.
```

---

# What Codex must not try

```text
No V1/V3 hedge threshold.
No q50/q60/q65 sibling after q55.
No historical hour/day mask.
No December-2025-specific control.
No 2021-specific control.
No previous-month P/L gate.
No source-local daily loss rescue.
No tighter stop merely to fit 0.01.
No lower RR to raise WR.
No partial/BE/trailing repair.
No portfolio rescue of a standalone failure.
No H4 active-position flag inside the new specialist.
No “empty string means disabled” assumption.
No validation based only on generated INI.
No promotion from a fixed-lot dollar total.
No claim that 36 trades establish a ten-year source.
```

---

# Required ending

## 1. STRICT VERDICT

```text
Commit evidence quality:
  VALID_WITH_MATERIAL_LIMITATION

Deployment:
  NO_GO

Original H4:
  QUARANTINE

Mechanical hedge research:
  CLOSED

V3:
  VALID ECONOMIC FAILURE

R5 q55:
  REJECT; NO NEIGHBOR SWEEP

H4 rule-clean result:
  INVALID AS LABELLED DUE EFFECTIVE-INPUT CONTAMINATION

USD 8,000 / 10% DD with USD 1,000 and 0.01 minimum:
  NOT PRACTICALLY EXPRESSIBLE UNDER CURRENT EVIDENCE AND CONTRACT
```

## 2. SINGLE NEXT EXPERIMENT

```text
A1_XAU_H4_RULE_CLEAN_EFFECTIVE_INPUT_RERUN_V2
```

Rerun the already preregistered first-cross / one-position / common-risk H4 source only after replacing empty-string mask clearing with an explicit fail-closed mask-disable switch and verifying effective native MT5 report inputs.

## 3. ALLOWED CHANGES

```text
explicit legacy-mask enable/disable boolean
native MT5 effective-input parser
minimum-lot fail-closed common risk sizing
actual leverage/currency/symbol-spec capture
fee/funding evidence fields
tests and manifests
same five-/ten-year rerun
```

## 4. FORBIDDEN CHANGES

```text
signal threshold change
router change
RR change
stop change
session selection
P/L selection
hedge
dynamic equity throttle
loss-date rule
new source priority
H4 portfolio composition
R5 sibling
deployment
```

## 5. PASS GATES

```text
actual MT5 effective inputs exactly equal locked contract
zero legacy mask blocks
zero order/management failures
native position/P&L reconciliation
ten-year trades >= 100
PF >= 1.30
hard-stress PF >= 1.20
hard-stress expectancy > 0R
bootstrap lower expectancy > 0R
bootstrap lower PF > 1.00
max relative floating DD <= 8%
fixed per-trade/open risk respected
both halves positive
>= 6/10 annual buckets positive
top-10 and top-3-day removal remain positive
concentration caps pass
```

## 6. NO-GO GATES

```text
effective-input mismatch
legacy mask present
negative P95/hard-stress expectancy
PF < 1.30
floating DD > 8%
sample < 100 without a legitimate forward evidence path
minimum lot makes safe risk impossible
financing cannot be bounded
concentration failure
new historical rescue required
```

Any NO-GO gate closes H4 for the current contract/family. It does not authorize another threshold.

## 7. REQUIRED EVIDENCE PACKAGE

```text
preregistration and SHA
source and source-transform manifest
compiled source and EX5 hashes
compile 0/0 log
generated INI
native effective-input export
native MT5 HTML
order/deal/signal/management ledgers
fee/commission/swap/funding report
risk-sizing and minimum-lot report
five-/ten-year result JSON/MD
bootstrap and concentration reports
root manifest + manifest SHA
local test capture or CI run
```

## 8. FOLLOW-UP REVIEW CHECKLIST

```text
[ ] Verify generated INI versus native effective inputs.
[ ] Verify no legacy mask block reason exists.
[ ] Verify min-lot requests never round upward.
[ ] Verify leverage/currency/symbol contract from MT5 report.
[ ] Verify fees, swap, and funding assumptions.
[ ] Verify all trades by native position ID.
[ ] Verify max relative floating DD from native report.
[ ] Verify all standalone and concentration gates.
[ ] Verify no post-result rule change.
[ ] Decide H4 survivor / close / contract-infeasible.
[ ] Authorize R6 census only after H4 decision.
[ ] Keep runtime and broker action NO_GO.
```

