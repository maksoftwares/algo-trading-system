# CODEX WORK ORDER — Export today's GOLD trades from all three accounts (2026-06-15 end of day)

Owner: Ali (mohdalikhans97.com@gmail.com), 2026-06-15. Demo only. **Read-only export — change nothing.**

## Why
End-of-day review of today's trading, **GOLD (XAUUSD) only**, across all three demo accounts.
The data is needed inside the repo so it can be analyzed; nothing has synced yet.

## What to export
Window: **market open 2026-06-14 ~22:00 UTC through now.** Symbol: **XAUUSD only** (drop EUR/GBP/JPY).
For each account below, export to the repo at `xau-usd/xauusd-phase1/outputs/reports/`:

### A1 — `1025742` (kitchen-sink)  → `EOD_GOLD_A1_20260615.csv`
### A2 — `1033030` (solo breakout) → `EOD_GOLD_A2_20260615.csv`
### A3 — `1033669` (repair lanes)  → `EOD_GOLD_A3_20260615.csv`

Each file, one row per closed/closing XAUUSD deal, with columns:
`account, entry_time_utc, entry_time_dubai, exit_time_utc, candidate, magic, direction, lots,
entry_price, exit_price, sl, tp, exit_reason(SL/TP/other), profit_aed, dirstate_regime`

Also include, per account, a short companion file or section:
- **Open XAUUSD positions right now** (ticket, magic, direction, lots, entry, current floating PnL).
- **Counts from the signal/order logs since open:** would-signals, orders sent, orders filled,
  guard-blocks **by reason code** (so we can see what each EA wanted to do vs what it took).

## Output
Write `EOD_GOLD_EXPORT_REPORT_2026_06_15.md` listing the three file paths, row counts per
account, total closed XAUUSD trades, and total closed XAUUSD PnL per account. Raw evidence
(the broker-history query and log tails) appended.

## Boundaries
Read-only. Do not change any EA, preset, arming flag, or setting. Gold only. If an account had
zero XAUUSD trades today, say so explicitly (that is a valid, useful result).
