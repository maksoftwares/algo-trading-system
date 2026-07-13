# A1 XAUUSD H4 Breakout Episode-Identity Repair Preregistration

Date: `2026-07-11`

Status: `PREREGISTERED_NOT_RUN`

Runtime boundary: local MT5 Strategy Tester only. No demo/live attachment or broker action.

## Defect being repaired

The frozen H4 source evaluates a completed H4 bar as a candidate whenever its close
is still above the current two-day compression box. It does not require the prior H4
close to have been inside/below the same box. Combined with fixed `0.01` volume,
`InpOnePositionPerMagic=false`, no cooldown, six entries per day, and a 32-position
cap, one bullish thesis can be copied across many H4 bars.

Ten-year native evidence fixes the diagnosis before this experiment:

- maximum concurrent H4 positions: `14`;
- maximum aggregate original-stop risk: `$1,020.64` on a `$1,000` control account;
- seven positions stopped on `2025-12-29` for `-$866.37` combined;
- all `149` losing H4 positions reached their full original stop;
- maximum relative native MT5 equity drawdown: `39.49%`.

Prior cap/cooldown experiments are not repeated. In particular, the historical hard
open cap of two improved the known weekly tail but reduced the earlier portfolio net
to `$10,064.02` and W/L to `1.7101`. The new hypothesis is narrower: the source is
detecting an above-box state repeatedly instead of the first transition across the box.

## Fixed repair

The repaired source is derived from commit `d15fc9a6b3ff18d1748428ea6519fbe58ab30721`
and retains fee instrumentation only for evidence.

Exactly these structural changes are allowed:

1. Long H4 entry requires:
   - current completed H4 close `> box_high`;
   - current completed H4 close `> current H4 open`;
   - previous completed H4 close `<= the same box_high`.
2. Short symmetry is implemented in source but remains blocked by the frozen long-only
   direction input.
3. Only one H4 position may be open for this magic/symbol at a time.
4. A current broker trade-session preflight permanently expires a closed-session
   signal. No deferral and no retry are allowed.
5. Risk-normalized variants must round volume down and block the trade when broker
   minimum volume would exceed the fixed risk amount.
6. Calendar/month/rolling output is attributed by native `exit_time`.

No early exit, breakeven, trailing stop, partial close, stop/target change, RR change,
new time mask, P/L throttle, outcome-based regime filter, or parameter sweep is allowed.

## Locked runs

Each variant runs both `2021-07-01 -> 2026-06-30` and
`2016-07-01 -> 2026-06-30` using Capital.com real-tick history.

### Variant A: structural parity diagnostic

- Deposit/currency: `$1,000 USD`.
- Fixed volume: `0.01`.
- Frozen supportive-state, previous-month-health, and time inputs retained.
- Only the episode-transition, single-position, and market-session repairs differ.

Purpose: isolate whether repeated episode exposure caused the native floating-DD tail.
This variant is not deployable because it retains legacy rules and fixed lots.

### Variant B: rule-clean common-risk qualification

- Deposit/currency: `$10,000 USD`.
- Compounding: off.
- Requested initial risk: `$25` per trade (`0.25%`).
- Minimum-lot excess risk: block.
- Previous-month P/L gate: disabled.
- Discovered entry-hour/day masks: empty.
- Supportive D1 state and frozen Router remain unchanged.

### Variant C: intended small-account feasibility

- Deposit/currency: `AED 3,672.50` (the owner's approximately `$1,000` pilot basis).
- Compounding: off.
- Requested initial risk: `AED 9.18` (`0.25%`).
- Minimum-lot excess risk: block.
- Same rule-clean inputs as Variant B.

This variant tests executability only. Capital.com's dynamic AED conversion markup and
overnight financing require a later dedicated cost harness; they are not silently
claimed by an MT5 report that records zero historical swap/fee.

Fail-closed environment rule: if the isolated tester lacks historical `USDAED`
conversion quotes, it may not fabricate AED P/L. In that case the variant is classified
from the validated USD minimum-contract original-stop-risk ledger using the equivalent
`$2.50` ceiling and must report `AED_MT5_CONVERSION_HISTORY_UNAVAILABLE`.

## Required reporting

For every run report:

- trades, WR, W/L, PF, net, stress net;
- native balance and equity DD maximal and relative;
- requested and actual leverage;
- order failures and market-session blocks;
- minimum-lot risk blocks;
- maximum simultaneous H4 positions;
- maximum aggregate original-stop risk;
- exit-time monthly/yearly/rolling results;
- source/config/report/log SHA256 values.

## Decision gates

Variant A establishes a structural survivor only if:

- no order-send failures;
- maximum relative native floating-equity DD `<= 10%`;
- PF `>= 1.30` and net `> 0` in both horizons;
- maximum simultaneous H4 positions `<= 1`;
- the December 2025 seven-position loss basket cannot recur.

Variant B qualifies H4 for later integrated research only if:

- all Variant A gates pass;
- maximum relative native floating-equity DD `<= 8%`;
- at least `100` ten-year trades;
- point PF under the later P95 cost overlay remains `>= 1.30`;
- no legacy P/L or discovered time mask is active.

Variant C passes feasibility only if it produces executable trades without any
minimum-lot risk excess. Zero trades is `SMALL_ACCOUNT_CONTRACT_INFEASIBLE`, not a
zero-drawdown success.

If Variant A fails, status is `H4_EPISODE_IDENTITY_REPAIR_FAILED`. No further H4
parameter repair is authorized from this experiment. If Variant A passes but Variant B
fails, the frozen H4 edge is not a rule-clean qualified source. If B passes and C fails,
the strategy may remain valid research but cannot trade the intended Capital.com MT5
small account without a genuinely smaller contract.
