# Review Response - Forex MT5 USDJPY Asia-London M30 Raw Lead - 2026-07-04

Verdict: `METHODOLOGY_SOUND_WATCHLIST_ONLY`. The `USDJPY asia_london_break_m30` raw lead is legitimate enough to keep researching, but it is not demo-forward and not yet tuned.

## Boundary

Runtime isolation passes for this evidence packet.

- EA guard: `ForexSessionBreakoutScout.mq5` fails `OnInit()` unless `MQL_TESTER` is true, before any trading path can run.
- Runner boundary: the runner launches only `C:\MT5A1M5MomentumBacktest\terminal64.exe` with `/portable`.
- Tester config uses `ShutdownTerminal=1`, `UseLocal=1`, `UseRemote=0`, and `UseCloud=0`.
- The result is actual MT5 Strategy Tester output; Python compiled/launched/parses reports and did not simulate the price path.
- No live/demo chart, preset, position, order, running XAU EA, or existing MT5 runtime state is required for this packet.

The use of `CTrade` inside the EA is acceptable for tester-only research because non-tester initialization returns `INIT_FAILED`. This is materially different from an EA that can attach and trade live.

## Causality

Causality looks sound for a raw tester research lead.

- Signal evaluation is triggered on a new bar, then reads shift `1`, the completed signal bar.
- The Asia range is built only from bars whose timestamps fall inside the completed 00:00-06:00 broker-server range.
- The M30 breakout decision is made after the signal bar has closed, and the order is sent on the following tester tick.
- The run uses the fixed raw definition: Asia range, M30 signal, both directions, RR `1.00`, fixed `0.01` lots.

One metadata caveat: the wrapper may mark `tuning_attempted=true` when the CLI narrows the sweep to `M30`, but the candidate replay itself did not change thresholds, hours, direction, RR, or symbol after this raw pocket was selected.

## Result Read

Watchlist status is justified:

- 2018-2019: 207 trades, CSV PF `1.1996`, MT5 PF about `1.17`, +`$54.04` parsed / +`$46.56` MT5.
- 2020-2026: 721 trades, CSV PF `1.1564`, MT5 PF about `1.14`, +`$179.97` parsed / +`$161.13` MT5.
- 2018-2026: 928 trades, CSV PF `1.1646`, MT5 PF about `1.14`, +`$234.01` parsed / +`$207.69` MT5.
- Both directions are positive: long PF `1.2054`, short PF `1.1194`.

The blockers are also real:

- Full PF is thin.
- 2021 and 2023 are negative.
- Only `58/102` active months are positive.
- Worst 250-trade rolling window is negative: PF `0.9142`, -`$30.37`.
- Top-50-winner removal flips negative: PF `0.9527`, -`$67.27`.

## Decision

This is the cleanest raw M30 USDJPY all-window frequency lead found so far, and it is stronger than the parallel `london120_break_m30` raw extension because `london120_break_m30` failed 2018-2019.

It still cannot be promoted beyond watchlist. The negative rolling window and top-winner dependency block demo-forward promotion. They do not block a single pre-declared research tuning pass, provided the tuning is designed from an older split and validated unchanged on the recent split.

## Next Allowed Step

Allowed: one constrained research tune only.

Pre-declared tuning rule:

- Use the raw `USDJPY asia_london_break_m30` MT5 trade CSV.
- Design only on 2018-2023 entry-date trades.
- Pick at most the two worst entry hours by net PnL among hours with at least 50 design trades and PF below `0.95`.
- Do not change symbol, range window, signal timeframe, direction, RR, stop logic, or max trades/day.
- Replay the selected blocked-hour set in actual MT5 Strategy Tester on 2018-2023 design, 2024-2026 validation, and full 2018-2026.
- Any pass remains `WATCHLIST_ONLY`; no demo-forward spec.

Blocked: direction-only tuning, RR tuning, stop changes, range-time changes, or promotion based on this raw result alone.

## Evidence

- Prompt: `forex-research/docs/FOREX_MT5_USDJPY_ASIA_LONDON_M30_RAW_REVIEW_PROMPT_2026_07_04.md`
- Robustness report: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_USDJPY_ASIA_LONDON_M30_RAW_SESSION_BREAKOUT_ROBUSTNESS_2026_07_04.md`
- Robustness JSON: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_USDJPY_ASIA_LONDON_M30_RAW_SESSION_BREAKOUT_ROBUSTNESS_2026_07_04.json`
