# Independent Review Prompt: USDJPY H4 Bond-Vol MT5 Cross-Check

Please review the new actual-MT5 Strategy Tester evidence for the frozen Forex bond-volatility clue.

## Scope

- Candidate: `usdjpy_h4_bond_vol_asia_session_carry_relief_v1`
- EA: `forex-research/mt5/Experts/ForexBondVolAsiaCarryReliefV1.mq5`
- Runner: `forex-research/scripts/run_forex_mt5_bond_vol_backtest.py`
- Main MT5 report: `forex-research/outputs/reports/mt5_backtests/bond_vol_scout/FOREX_MT5_BOND_VOL_BACKTEST_FULL_2018_2026_BOND_VOL_V1_MT5.md`
- Main MT5 JSON: `forex-research/outputs/reports/mt5_backtests/bond_vol_scout/FOREX_MT5_BOND_VOL_BACKTEST_FULL_2018_2026_BOND_VOL_V1_MT5.json`
- Trade CSV: `forex-research/outputs/reports/mt5_backtests/bond_vol_scout/ForexBondVol_FULL_2018_2026_BOND_VOL_V1_MT5_USDJPY_H4_offset0/ForexBondVol_FULL_2018_2026_BOND_VOL_V1_MT5_USDJPY_H4_offset0_trades.csv`
- Context CSV: `forex-research/outputs/reports/mt5_backtests/bond_vol_scout/ForexBondVol_FULL_2018_2026_BOND_VOL_V1_MT5_USDJPY_H4_offset0/forex_bond_vol_context.csv`
- Status context: `forex-research/docs/FOREX_MT5_FREQUENCY_STATUS_2026_07_04.md`

## Result To Audit

- Window: `2018.01.01` to `2026.06.27`
- Symbol/period: `USDJPY H4`
- Actual MT5 Strategy Tester, every tick model, isolated root `C:\MT5A1M5MomentumBacktest`
- Trades: `79`
- Parsed trade CSV PF: `1.701`
- MT5 report PF: `1.68`
- Parsed net: `+$79.04` at fixed `0.01` lots
- MT5 total net profit: `+$77.37`
- Equity drawdown maximal: `$37.68 (3.59%)`
- Context rows/SHA256: `2804` / `9d8636756487c8a9864b2915cab4fec7e228c7faf43bbcd16c5532fb4bbc7c19`
- Context available through: `2026-06-27T00:00:00Z`

## Robustness Overlay

- Year splits:
  - 2018: 14 trades, PF `2.6660`, +`$24.14`
  - 2019: 14 trades, PF `1.5637`, +`$10.67`
  - 2020: 11 trades, PF `0.7278`, -`$7.35`
  - 2021: 3 trades, PF `0.0000`, -`$4.84`
  - 2022: 4 trades, PF `0.5475`, -`$4.48`
  - 2023: 11 trades, PF `13.0963`, +`$48.99`
  - 2024: 9 trades, PF `7.4201`, +`$24.91`
  - 2025: 7 trades, PF `0.7838`, -`$3.53`
  - 2026 partial: 6 trades, PF `0.2901`, -`$9.47`
- Bucket read:
  - 2018-2019: 28 trades, PF `2.0416`, +`$34.81`
  - 2020-2021: 14 trades, PF `0.6171`, -`$12.19`
  - 2022-2024: 24 trades, PF `4.8934`, +`$69.42`
  - 2025-2026: 13 trades, PF `0.5618`, -`$13.00`
  - 2024-2026: 22 trades, PF `1.3550`, +`$11.91`
- Top-winner removal:
  - Top 1 removed: 78 trades, PF `1.6136`, +`$69.19`
  - Top 3 removed: 76 trades, PF `1.4487`, +`$50.59`
  - Top 5 removed: 74 trades, PF `1.2974`, +`$33.53`
  - Top 10 removed: 69 trades, PF `1.0003`, +`$0.03`

## Questions

1. Confirm this is actual MT5 Strategy Tester evidence, not Python price-path backtesting. Python should only prepare the fixed lagged MOVE context file, launch MT5, and parse the finished MT5 report.
2. Confirm runtime isolation: the EA is tester-only via `MQL_TESTER`, the runner launches only `C:\MT5A1M5MomentumBacktest\terminal64.exe` with `/portable`, `UseLocal=1`, `UseRemote=0`, `UseCloud=0`, and `ShutdownTerminal=1`, and no live/demo chart/order/position/runtime state is touched.
3. Audit context causality: MOVE observations must be available only from the next UTC date; the Strategy Tester window should end at `2026.06.27`, matching the latest available MOVE context from `2026-06-26`.
4. Audit signal causality: the EA should evaluate completed H4 bar `shift=1`, enter on the next H4 bar, and apply the Asia-session filter to the entry bar in UTC after the declared server offset.
5. Compare the MT5 result against the earlier Python/proxy evidence. Does the MT5 pass confirm the clue enough to stay watchlist-only, or do the weak 2020-2022 and 2025-2026 splits demote it further?
6. Decide whether any tuning is justified. My proposed answer is no: 79 trades over 2018-2026 is too sparse for frequency-first tuning, 2025-2026 is negative, and removing the top 10 winners leaves the run flat.
7. Final verdict requested: methodology sound or flawed; status should be `WATCHLIST_ONLY` or rejected; demo-forward remains blocked unless you find a reason otherwise.

Please lead with findings and file/line references, then give the verdict.
