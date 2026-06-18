# A3 Signal Quality V1 Implementation Addendum 01

Status: `LOCKED`

Scope:

- Account: `1033669`
- Symbol: `XAUUSD`
- Family: breakout-retest only
- Runtime mode: repo-only / shadow-only
- Broker action: prohibited
- Existing A3 lanes `933200`, `933300`, and `933400`: remain paused
- Profit-lock manager: remains dry-run/disarmed

This addendum clarifies implementation details left open by `A3_SIGNAL_QUALITY_V1_IMPLEMENTATION_CONTRACT.md`. It does not relax, strengthen, tune, or replace any locked threshold in `A3_SIGNAL_QUALITY_HYPOTHESES_V1_2026_06_18.md`.

## Version Links

- Locked hypothesis: `docs/A3_SIGNAL_QUALITY_HYPOTHESES_V1_2026_06_18.md`
- Locked hypothesis manifest: `outputs/manifests/A3_SIGNAL_QUALITY_HYPOTHESES_V1.sha256.json`
- Locked implementation contract: `docs/A3_SIGNAL_QUALITY_V1_IMPLEMENTATION_CONTRACT.md`
- Locked contract manifest: `outputs/manifests/A3_SIGNAL_QUALITY_V1_IMPLEMENTATION_CONTRACT.sha256.json`
- This addendum manifest: `outputs/manifests/A3_SIGNAL_QUALITY_V1_IMPLEMENTATION_ADDENDUM_01.sha256.json`

## Completed-Bar Indexing

- Index `[0]` is the forming bar and must not be used for signal decisions.
- Index `[1]` is the most recently completed bar.
- Index `[4]` is the fourth most recently completed bar.
- All M5, M15, H1, and D1 features are sampled only from completed bars available at the signal decision timestamp.
- If any required completed bar is missing, duplicated, out of order, or timestamp-inconsistent, the candidate is blocked and logged as `DATA_UNAVAILABLE`.

## First-Retest Definition

The raw breakout detector defines the candidate level and break direction. The retest-quality filters use this addendum definition:

- Long break: the break bar closes above the level.
- Short break: the break bar closes below the level.
- A long retest candidate is the first completed M5 bar after the break whose low touches or crosses the level.
- A short retest candidate is the first completed M5 bar after the break whose high touches or crosses the level.
- "First retest only" means that if this first touch/cross fails a locked retest rule, the signal is rejected; later touches are not searched under the same break event.
- For V1 strict retest, the retest must occur 1-5 completed M5 bars after the break exactly as locked.
- For any future diagnostic-light retest, the separately locked diagnostic document controls the allowed bar window.

## Signal Timestamp

- The signal decision timestamp is the close time of the confirmation M5 bar.
- Logs must store both confirmation bar open time and decision close time.
- The canonical `signal_id` must include account, symbol, base family, direction, break bar open time, retest bar open time, confirmation bar open time, and normalized level price.
- Candidate rows must reference the same `signal_id` so kept and blocked decisions can be paired.

## Entry Tick Eligibility

- Entry eligibility starts strictly after the signal decision timestamp.
- Long virtual entry fills at the first fresh ask tick after the decision timestamp.
- Short virtual entry fills at the first fresh bid tick after the decision timestamp.
- A tick is fresh only when its exchange/server timestamp is greater than the decision timestamp and greater than the last processed tick timestamp for the same symbol.
- No historical same-bar fill is allowed.
- Entry expires at the close time of the next M5 bar after the confirmation bar. If no eligible tick arrives by then, log `CANCELLED_NO_FRESH_TICK`.

## Indicator Seeding And Warm-Up

- EMA uses alpha `2 / (period + 1)`.
- EMA seed is the simple average of the first `period` completed closes in the calculation window.
- Wilder ATR14 seed is the simple average of the first 14 true ranges; subsequent values use Wilder smoothing.
- Minimum warm-up before any candidate may evaluate:
  - M5: at least 200 completed bars.
  - M15: at least 200 completed bars.
  - H1: at least 200 completed bars.
  - D1: at least 100 completed bars.
- Python and MQL implementations must document and test these seeds. A seed mismatch on an accepted candidate is a NO-GO.

## Timezone And DST Mapping

- Canonical report timestamps are UTC ISO-8601.
- Dubai time is UTC+04:00 fixed. Dubai has no DST adjustment.
- The locked Dubai `16:00-19:59` session is evaluated from UTC by adding four hours.
- Broker-server timestamps must be logged separately for audit, but broker-server time must not drive the Dubai session gate.
- Session boundary comparisons are inclusive at `16:00:00` and exclusive at `20:00:00` Dubai time.

## Weekend And Gap Behavior

- Missing bars must not be synthesized.
- If a completed M5 sequence has a gap greater than one expected M5 interval, new signals are blocked until all required timeframe warm-up windows are valid again.
- Higher-timeframe gaps block only candidates requiring that timeframe.
- Open virtual trades are not force-closed for weekends or data gaps.
- During a gap, SL/TP evaluation resumes on the first later eligible tick. If price gaps beyond SL or TP, the virtual close uses the actual executable quote, not the requested level.

## Restart Recovery

- Decisions, virtual events, and virtual trades are append-only.
- On restart, state must be rebuilt from append-only events before evaluating new signals.
- If rebuilt state does not exactly match the persisted state file, log `RECOVERY_REQUIRED` and block new virtual signals.
- Restart recovery must never fabricate fills, exits, MFE, or MAE.

## Tick Freshness

- A tick with a timestamp less than or equal to the last processed tick timestamp is stale and ignored for entry/exit.
- A tick with missing bid or ask is invalid for execution and logged as `INVALID_DATA`.
- Spread and cost calculations use the actual bid/ask pair from the execution tick.

## Rounding And Points

- Use broker symbol metadata for `_Point`, digits, and tick size when available.
- For XAUUSD parity fixtures, one point is `0.01` unless broker metadata states otherwise.
- Prices written to `signal_id` are normalized to broker digits.
- Entry, SL, TP, MFE, and MAE parity tolerance is one point.
- Risk distance is rounded after applying the locked floor formula, never before.

## Holding Duration

- V1 uses the fixed locked exit only: SL or TP at `1.50R`.
- There is no time stop in V1.
- A virtual trade remains open until an executable quote crosses SL or TP.
- Reports must include bars held and wall-clock duration, but those values are diagnostics, not exits.

## Gap Exit Pricing

- Long SL/TP is evaluated on bid.
- Short SL/TP is evaluated on ask.
- If a quote gaps beyond the requested level, close at the actual quote and record the slippage in R.
- Do not subtract spread a second time; bid/ask execution already embeds spread.

## Evidence Window Clarification

The contract's one-trading-week language is an implementation-validation minimum only. It is not the promotion minimum.

Promotion evidence for locked V1 still requires every minimum in `A3_SIGNAL_QUALITY_HYPOTHESES_V1_2026_06_18.md`, including:

- At least 100 closed virtual trades.
- At least 20 active market days.
- At least 4 calendar weeks.
- At least 25 long and 25 short trades unless a new one-sided hypothesis is separately registered.
- At least 3 distinct weeks with at least 15 trades.

No diagnostic discovery window may be reused as V1 or V2 promotion evidence.

## Reactivation Boundary

This addendum does not authorize A3 reactivation, MT5 attachment, profile edits, preset arming, lot changes, SL/TP changes, order sends, or position management. A3 remains paused until separate evidence, review, and owner authorization gates pass.
