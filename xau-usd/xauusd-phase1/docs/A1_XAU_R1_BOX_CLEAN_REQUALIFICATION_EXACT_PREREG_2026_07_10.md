# A1 XAU R1 Box Clean Requalification Exact-MT5 Preregistration

Date: `2026-07-10`

## Objective

Requalify the existing H4/D1 box2 long source as a standalone R1/uptrend specialist after removing the calendar and previous-performance masks that contaminated the earlier Router V1 result. This is a frozen one-candidate exact-MT5 exam, not a parameter search.

## Frozen candidate

- Source: `h4_d1_long_best_box2_atr80`
- EA signal mode: `InpSignalMode=7`
- Direction: long only, `InpDirectionMode=1`
- Router: strict completed-bar R1/uptrend only, `InpRegimeRouterMode=1`
- Entry geometry remains the existing box2 definition:
  - D1 ATR percentile maximum `80`
  - box length `2` completed D1 bars
  - range/median maximum `1.50`
  - H4 minimum body fraction `0.35`
- Existing supportive-state entry guard remains frozen:
  - D1 close above EMA20
  - EMA20 non-declining over five completed D1 bars
- Stop/target/management remain frozen:
  - ATR stop multiple `2.50`
  - stop floor `350` points
  - no stop ceiling or stop cap
  - fixed target `2.00R`
  - no breakeven, trailing, partial close, split entry, profit protection, or early-adverse exit
- Fixed size `0.01` lot, starting deposit `1,000 USD`.

## Required clean overrides

The exact run must explicitly set all of the following, even where the EA default is already disabled:

- `InpBlockedEntryHoursCsv=""`
- `InpBlockedEntryDayHoursCsv=""`
- `InpBlockedLongEntryHoursCsv=""`
- `InpBlockedShortEntryHoursCsv=""`
- `InpUseDirectionalSessionFilter=false`
- long and short session bounds `0` to `24`
- `InpH4D1PrevMonthHealthGateEnabled=false`
- `InpH4D1WeeklyLossGovernorEnabled=false`
- `InpH4D1NegativeStackGuardEnabled=false`
- `InpH4D1ThirdEntryQualityGateEnabled=false`
- `InpFeatureLossFilterEnabled=false`
- `InpD1SupportStateGateMode=0`
- `InpD1StructuralDownGateEnabled=false`

The existing `6` entries/day ceiling and maximum `32` same-magic open positions remain unchanged. They are exposure limits, not mined calendar masks.

## Exact windows

1. Primary exam: `2022-07-01` through `2026-06-30`.
2. Frozen prehistory exam: `2016-01-01` through `2021-12-31`, using precisely the same candidate inputs. This run is mandatory durability evidence and may not be used to change any threshold.

MT5 model: every tick, local agent only, XAUUSD M5.

## Mandatory evidence

The report must include:

- trades, win rate, average-win/average-loss, profit factor and net profit;
- fixed `-$0.30` per-ticket stress net and profit factor;
- yearly exposure and yearly results;
- top-ten-winners-removed net, top-three-entry-days-removed net and best-month profit share;
- closed-ledger drawdown;
- MT5 balance drawdown maximal and relative, in money and percent;
- MT5 equity drawdown maximal and relative, in money and percent;
- strict router-state attribution for every successful and failed order-send attempt;
- number and PnL of independently traded R1 episodes. An episode is a contiguous run of active entry months separated from the next run by at least one full calendar month with no executed entry;
- every order-send failure with timestamp, retcode and description;
- reconciliation between successful order sends and MT5 trades;
- counts for every guard reason, including an explicit assertion that no calendar/session/performance-mask guard fired.

## Frozen qualification gates

### Alpha

- at least `100` trades;
- win rate at least `50%`;
- average-win/average-loss at least `2.00`;
- profit factor at least `2.00`;
- stressed profit factor at least `1.75` and stressed net positive;
- at least three calendar years with exposure and three profitable calendar-year buckets;
- at least three independently traded R1 episodes;
- pre-2026 net positive in the primary exam.

### Robustness and concentration

- top-ten-winners-removed net positive;
- top-three-entry-days-removed net positive;
- best-month share no more than `30%`.

### Regime and execution integrity

- every successful or failed order-send attempt attributed to native `uptrend`; signals blocked by the strict router are expected to carry their actual non-R1 states;
- zero forbidden calendar/session/previous-performance guard blocks;
- successful order sends equal MT5 total trades;
- every order failure fully described and reconciled;
- zero order-send failures for full qualification.

### Drawdown

- MT5 balance drawdown relative no more than `20%`;
- MT5 equity drawdown relative no more than `20%`.
- net profit divided by maximal MT5 equity drawdown at least `2.00`;
- maximal MT5 equity drawdown no more than `2.0x` closed-ledger drawdown.

The drawdown limits are deliberately stricter than the earlier routed R1 result. Passing alpha but failing drawdown is reported as `ALPHA_ONLY_RISK_REPAIR_REQUIRED`, not promoted as a complete specialist.

## Decision rule

- The primary and prehistory windows must each pass the core alpha shape separately. The three-year and pre-2026 checks apply to the primary window; the prehistory window must instead have exposure in at least three calendar years and positive net across its full frozen window.
- `R1_BOX_CLEAN_FULLY_QUALIFIED`: both windows pass their frozen alpha gates and every robustness, regime-integrity, execution, and drawdown gate passes in the primary window.
- `R1_BOX_CLEAN_ALPHA_ONLY_RISK_REPAIR_REQUIRED`: both windows pass core alpha and regime-integrity, but one or more primary concentration, execution-quality, or drawdown gates fail.
- `R1_BOX_CLEAN_REJECT`: either window fails core alpha, or the primary regime-integrity gate fails.

No post-result mask, threshold sibling, stop tweak, or management variant is authorized by this preregistration.
