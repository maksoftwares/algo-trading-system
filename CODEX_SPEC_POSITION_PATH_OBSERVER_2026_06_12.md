# Codex Spec — Position Path Observer (2026-06-12)

Purpose: log every open position's state on a fixed cadence so we can answer, with data
instead of hindsight: why did we hit SL, did the trade reach +1R first, when *could* we
have exited, how much do spread spikes and slippage cost us — and unblock the ATR-trail /
dynamic-exit research that is currently `BLOCKED_NO_PRICE_PATH`.

Boundary: observer-only, demo-only, additive. No existing EA, chart, preset, or position
is touched. No order/trade calls of any kind. Same safety pattern as
`Phase2TrendGuardedFixObserver` (dry-run locked in `OnInit`, demo-server lock, refuses
"live"/"real" servers).

---

## 1. Design decisions (and why they differ from the first sketch)

1. **One EA instance, one chart, sees everything.** `PositionsTotal()` is account-wide; a single observer on one chart snapshots ALL positions on ALL symbols. Do not deploy per-chart copies — one instance means one file, one clock, zero duplicate rows.
2. **Log 24 h, not just the evening window.** June 11's damage was night + evening; an evening-only collector rebuilds a blind spot. Storage is trivial (worst case ~20 positions × 6 rows/min ≈ 7,200 rows/h; daily-rotated CSV). Filter to the evening window at analysis time, never at collection time.
3. **10-second timer + boundary events.** `EventSetTimer(10)` for the cadence, plus an immediate snapshot pass when the open-position set changes (new ticket appears / ticket disappears), so every position gets a first row at entry and a final row at exit. Exact exit details come from history (deal close price/time) in the summary row.
4. **Keep the EA dumb.** It writes raw snapshots only. MFE/MAE, R-multiples, exit-quality metrics are computed offline in Python from the snapshots. Less MQL5 logic = less to review = nothing to get wrong silently. (Running MFE/MAE in the EA dies on reload/restart anyway; offline recompute doesn't.)
5. **Lock the R basis at first sight.** `unrealized_R` must be computed against the SL distance captured in the position's FIRST snapshot, persisted in memory keyed by ticket. If SL is later modified, the R denominator must not move (otherwise every BE/trail study is contaminated). Log current SL separately so modifications are visible.

---

## 2. Snapshot row schema (`position_path_log_YYYYMMDD.csv`, daily rotation)

```
ts_utc, ts_broker, ts_local,
position_ticket, magic, candidate, symbol, direction, volume,
entry_time_broker, entry_price,
sl_current, tp_current, sl_initial, initial_stop_points,
bid, ask, spread_points,
price_current, unrealized_pnl_aed, unrealized_R,
distance_to_sl_points, distance_to_tp_points,
atr14_m5_points, m15_ema20_slope_points, h1_ema20_slope_points, d1_bias,
open_positions_total, same_symbol_same_dir_count,
account_equity, account_floating_total,
row_type            // SNAPSHOT | FIRST_SEEN | CLOSE_DETECTED
```

`candidate` from the magic registry (`MAGIC_NUMBERS.md` mapping baked as a function, same
as existing reporting scripts). The four regime columns reuse the TrendGuardedFixObserver
helpers — apply the Review 9 fixes here from day one (cached `iMA` handles,
`SLOPE_UNAVAILABLE` on CopyBuffer failure, `TimeGMT()+240` for any Dubai bucketing).

**Close summary row** (`position_path_summary.csv`, one row per closed ticket, written on
CLOSE_DETECTED using history): ticket, candidate, symbol, direction, entry/exit time+price,
exit_reason (SL/TP/manual from deal info), realized_pnl_aed, realized_R,
**slippage_points = |exit_price − sl_or_tp_level|**, snapshots_count, first/last snapshot ts.

---

## 3. Offline analysis pack (Python, `scripts/analyze_position_paths.py`)

Pre-register these questions NOW, before the first data arrives — path data is the most
hindsight-tempting dataset there is, and "we could have exited here" cherry-picking is how
overfit exit rules get born. The script answers exactly these, per candidate × symbol ×
session, duplicate-hidden view:

1. **Loser anatomy:** of SL-hit trades, what % reached +0.3R / +0.5R / +1.0R first? Time spent in profit before dying? → directly scores break-even and partial rules on REAL paths (the June BE test had only sparse logged snapshots).
2. **Winner giveback:** distribution of max R reached vs the realized 1.5R; how much TP money is left on the table → feeds the per-cell TP optimizer (greenfield spec §B5).
3. **Spread-spike SL hits:** SL-hit rows where `spread_points` at the hit was > 2× session median and mid-price never reached the SL level → counts "phantom stop-outs", especially night XAUUSD. This is a known unknown worth a number.
4. **Slippage distribution:** from summary rows — the live-trading cost model input you don't currently have.
5. **Time-stop curve:** unrealized_R trajectory vs bars held — is there a holding time after which losers rarely recover? (Time-stop candidate, expectancy-tested.)
6. **Exposure concentration replay:** `same_symbol_same_dir_count` over time — quantifies stacking risk continuously (June 11 peaked at 19).
7. **ATR-trail backtest — now unblocked:** replay trail variants on actual paths; promotion KPI stays `net_expectancy_R_after_measured_cost` vs the plain 1.5R hold.

Outputs: `POSITION_PATH_EXIT_QUALITY_REPORT.md` + per-question CSVs. Anything that looks
promising goes to the standard ladder: shadow rule → fresh forward week → owner approval.
No exit rule deploys straight from this analysis.

---

## 4. Safety checklist (same bar as Review 9)

- No `OrderSend/CTrade/Position{Open,Modify,Close}/TRADE_ACTION` anywhere; pytest forbidden-terms test cloned from `test_phase2_trend_guarded_fix_observer.py`.
- `InpDryRunOnly=true` locked in `OnInit` (refuse start otherwise); demo-server marker check; refuse "live"/"real".
- Unique log filenames; append-with-retry CSV writer (reuse `AppendCsvRow`); daily rotation by filename, never deletion.
- Attach preference: the portable observer terminal. Note: the observer must run in the SAME terminal as the positions it watches — if the trading EAs run in the standard demo terminal, this observer attaches there on ONE new appended chart (profile backup first, WR50 procedure).
- Compile log + startup-row verification before leaving it unattended.

## 5. Explicitly out of scope

- Any live exit action, trailing, or position modification — this is a camera, not a hand.
- Tick-level capture (10 s + boundary events is sufficient; ticks triple complexity for marginal gain).
- Evening-only filtering at collection time.
- Real-money trading remains NOT authorized; this observer is part of the evidence bar, not a bypass of it.
