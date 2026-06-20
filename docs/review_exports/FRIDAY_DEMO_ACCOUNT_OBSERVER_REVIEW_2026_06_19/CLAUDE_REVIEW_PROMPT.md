Claude, please review this evidence package from Codex for Friday 2026-06-19.

Context:
- Demo-only research. No live trading or real-capital approval.
- A1 is the standard experimental demo account `1025742`.
- A2 is the clean Tier-1 breakout-only account `1033030`.
- A3 is the paused repair lane `1033669`.
- Codex says no runtime was changed while generating this package.

Please inspect:
- `README_REVIEW_EXPORT.md`
- `reports/FORWARD_WEEK_FRIDAY_SCORE_2026_06_19.md`
- `reports/GOLD_DAILY_SCAN_2026_06_19.md`
- `reports/EOD_GOLD_SCAN_REPORT_2026_06_19.md`
- `reports/OBSERVER_OUTCOME_RESOLUTION_REPORT_2026_06_19.md`
- `reports/RUNTIME_AUTHORIZATION_RECONCILIATION_2026_06_19.md`
- `reports/A2_TIER1_ACCOUNT_HISTORY_2026_06_19.md`
- `reports/A3_REPAIR_LANE_ACCOUNT_HISTORY_2026_06_19.md`
- The CSV files under `csv/`
- The dashboard files under `dashboard/`

Specific asks:
1. Verify whether Friday was genuinely positive or negative across A1/A2/A3, separating gold-only from all-symbol evidence.
2. Explain whether A1's +90.30 AED XAUUSD Friday result is useful evidence or too small/noisy.
3. Check the discrepancy where `PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv` shows two A1 XAUUSD entries as 0.00 with blank exits, while `EOD_GOLD_A1_20260619.csv` pairs them as +41.74 and +68.95 AED.
4. Judge H1/H2/H3/H4 from `FORWARD_WEEK_FRIDAY_SCORE_2026_06_19.md`; say what is pass, fail, pending, and why.
5. Recommend the next action: keep running unchanged, repair dashboard parser first, export M5 replay bars, change runtime rules, or pause something.

Please be strict. Prefer broker-joined/direct MT5 evidence over replay. Do not recommend any live-capital action.
