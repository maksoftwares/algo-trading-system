# Independent Review Request: EURUSD Profit-Factor Improvement

Date: `2026-07-23`

Candidate: `EURUSD_M30_RSI_BB_CLOSE_FADE_LONG_V1`

Requested reviewer role: independent strategy, execution, and
overfitting-risk reviewer.

## Review objective

Please determine whether this EURUSD strategy contains a defensible edge and,
if so, propose the smallest causal research program that could improve its
profit factor and realized win/loss ratio without manufacturing a historical
result.

The current profit factor is too low for promotion:

| Window | Trades | Win rate | Net USD at 0.01 lot | PF | Max closed DD USD |
|---|---:|---:|---:|---:|---:|
| 3 completed months | 68 | 55.88% | +3.29 | 1.1010 | 7.19 |
| 6 completed months | 140 | 57.14% | +11.43 | 1.1502 | 8.84 |
| 1 completed year | 241 | 57.26% | +16.03 | 1.1194 | 12.30 |
| Full MT5 run | 831 | 59.33% | +101.82 | 1.20 | 30.85 equity DD |

The three-, six-, and twelve-month figures include swap and commission and
exclude incomplete July 2026. The full run covers 2022-07-01 through
2026-07-02 on actual MT5 Strategy Tester history.

## Frozen strategy under review

- Symbol: EURUSD
- Execution chart: M5
- Decision timeframe: completed M30 bars
- Direction: long only
- Entry condition:
  - M30 close at or below the lower Bollinger Band;
  - Bollinger Bands use close, period 20, deviation 2.0;
  - RSI(14) <= 35.
- Entry timing: first executable tick after the new M30 bar is detected.
- Retrospectively selected blocked broker/tester hours: `6,7,10,13`.
- Fixed research size: 0.01 lot.
- Stop: wider of:
  - 1.4 x ATR(14);
  - 30 points;
  - lowest low of the six completed M30 bars.
- Stop ceiling: 700 points.
- Target: 0.8R.
- Spread guard: 100 points.
- Maximum entries per broker/tester day: 20.
- Maximum open positions owned by this strategy: one.
- No trailing, partial close, compounding, ML, or discretionary override.

## Evidence quality

The current source was compiled on 2026-07-23 with zero errors and zero
warnings. A new run in the isolated MT5 Strategy Tester reproduced all 831
trades from the inherited ledger byte-for-byte.

Frozen artifacts include:

- current MQL5 source and SHA256;
- compiled EX5 and SHA256;
- research preset;
- tester INI;
- MT5 HTML report;
- startup, signal, order, and trade ledgers;
- evidence audit;
- parity manifest;
- completed-window report;
- tests.

The EA contains a hard Strategy-Tester-only initialization guard. No chart,
demo order, live order, or active broker runtime was touched.

## Known weaknesses and contamination

1. The blocked-hour mask `6,7,10,13` was selected after historical inspection.
   Treat it as contaminated development evidence.
2. The strategy targets 0.8R, so average winners are smaller than average
   losses. The realized win/loss ratio is approximately `0.84-0.87` in the
   recent windows.
3. Recent PF is only `1.10-1.15`; small cost or execution degradation may erase
   the edge.
4. Three historical order attempts failed: two at market close and one for
   invalid stops. They are logged and must not be silently deleted.
5. Repository Capital.com bar exports are stale and not promotion-grade
   Bid/Ask evidence. The exact MT5 run is the execution evidence currently
   available.
6. All current outcomes are development data. There is no locked prospective
   shadow sample.
7. The strategy is long only and may be expressing a regime or sample bias
   rather than a stable EURUSD mechanism.
8. Cross-asset USD exposure and drawdown overlap with XAUUSD have not been
   evaluated.

## Questions requiring explicit answers

### A. Edge and implementation verdict

1. Is the strategy a genuine weak edge, an overfit hour-mask result, or
   statistically indistinguishable from noise after realistic costs?
2. Is the completed-bar implementation causal and free of bar-zero/look-ahead
   errors?
3. Do the stop calculation, spread guard, order-failure behavior, and 0.8R
   target match the stated contract?
4. Are the exact-MT5 evidence, ledger reconciliation, and hashes sufficient for
   a research baseline?
5. Should the candidate be retained, redesigned as a new hypothesis, or killed?

### B. Profit-factor diagnosis

Please decompose the low PF into:

- entry-quality failure;
- target/stop geometry;
- volatility or trend-regime mismatch;
- time-of-day/session dependence;
- spread and swap drag;
- repeated entries during the same adverse episode;
- large-loss concentration;
- long-only structural bias;
- exit timing;
- market-close/rollover behavior.

State which cause is supported by evidence and which is only a hypothesis.

### C. Safe improvement directions

Rank the following possible directions by causal plausibility, overfitting
risk, expected PF benefit, trade-frequency cost, and implementation complexity:

1. Replace the contaminated hour mask with a market-state rule defined before
   seeing outcomes.
2. Add one slow trend/regime ownership condition.
3. Require a completed-bar reclaim/confirmation after the oversold close.
4. Use a volatility-normalized entry-quality threshold.
5. Add an episode mutex or cooldown to prevent repeated entries into one
   falling-market event.
6. Test one alternative exit geometry while leaving entry frozen.
7. Test one alternative stop geometry while leaving target and entry frozen.
8. Separate setup detection from execution and skip rollover/closed-market
   conditions for operational, not performance, reasons.
9. Create a distinct short specialist instead of forcing symmetry into this
   long system.
10. Retire this candidate and research a materially different EURUSD mechanism.

Do not merely recommend increasing the target. Explain why the proposed change
should improve net expectancy after costs, what failure mode it addresses, and
what result would falsify it.

### D. Required research design

Please propose a bounded experiment sequence with:

- one change per experiment;
- fixed causal definitions;
- no grid search over hours, RSI, Bollinger, ATR, stop, or target values;
- a frozen development/validation/forward boundary;
- realistic spread, slippage, swap, and failed-order treatment;
- exact MT5 parity requirements;
- trade-count and regime-coverage minimums;
- concentration and rolling-window tests;
- explicit stop/kill rules.

Recommend numerical admission gates. Our provisional desired direction is:

- full and recent PF materially above the current result;
- stress PF >= 1.15;
- net positive after removing the ten largest winners;
- positive result in at least three calendar-year buckets;
- acceptable 100/150/250-trade rolling windows;
- no single month or session responsible for the edge;
- maximum floating-equity drawdown within the locked account cap;
- no promotion from the already inspected historical window alone.

If you recommend a PF target such as `>=1.30`, explain whether it is realistic
for this frequency and cost structure or whether the candidate should be
retired rather than tuned toward the target.

## Prohibited recommendations

Please do not recommend:

- searching more excluded hours on the same history;
- sweeping RSI/Bollinger/ATR/RR parameters and retaining the best result;
- removing losing trades or market-close failures from the ledger;
- adding multiple filters at once;
- using portfolio results to rescue a failing standalone strategy;
- calling existing history an untouched holdout;
- demo/live deployment from this packet;
- increasing lot size to make the dollar P&L look larger.

## Requested response format

Please return:

1. `VERDICT`: retain, redesign, or kill.
2. `CONFIDENCE`: low, medium, or high, with reasons.
3. `TOP_FINDINGS`: ordered by severity.
4. `PF_ROOT_CAUSE`: evidence-backed decomposition.
5. `RECOMMENDED_EXPERIMENTS`: ordered, bounded, and one change at a time.
6. `EXPECTED_TRADEOFFS`: PF, frequency, drawdown, and robustness.
7. `PROMOTION_GATES`: exact numerical gates.
8. `INVALID_OR_OVERFIT_IDEAS`: what must not be tested or claimed.
9. `MISSING_EVIDENCE`: files or analyses still required.
10. `NEXT_SINGLE_ACTION`: the first action to take after review.

## Reproduction

From the repository root:

```powershell
& 'xau-usd\xauusd-phase0\.venv\Scripts\python.exe' `
  'eur-usd\eurusd-phase0\run_evidence_audit.py'

& 'xau-usd\xauusd-phase0\.venv\Scripts\python.exe' `
  'eur-usd\eurusd-phase0\run_window_report.py'

& 'xau-usd\xauusd-phase0\.venv\Scripts\python.exe' -m pytest `
  'eur-usd\eurusd-phase0\tests' -q
```

The exact Strategy Tester rerun command and frozen tester inputs are documented
in the package README and parity artifacts. No reviewer should attach this EA
to an active chart.
