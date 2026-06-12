# Repo Review 10 — Phase2PositionPathObserver Pre-Attachment Review (2026-06-12)

Reviewer role: senior quant + MQL5 code reviewer.
Scope: full read of `Phase2PositionPathObserver.mq5` (946 lines, zero includes), the preset,
the 433-line attach script, both test files, build report/doc claims, and the agent.md
2026-06-12 section. Magic-number coverage was verified against the *actual* magics in
`PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv` and the WR50 registry, not against the docs.

---

## Summary Verdict: **APPROVE_WITH_CHANGES**

Safety is clean — this is a genuinely read-only camera, and the attach script's isolation
design is the best-engineered runtime tooling in the repo so far. The "changes" are one
real (small) code bug in slippage attribution, magic-mapping gaps confirmed against live
data, and one operational verification that decides whether the observer sees anything at
all. None are attachment-safety blockers; two should be fixed before data is trusted.

---

## 1. Safety — PASS on all checks

| Check | Result | Evidence |
|---|---|---|
| Read-only | **PASS** | Zero trade/modify calls (independent grep: `OrderSend(Async)`, `CTrade`, `Position{Open,Modify,Close}`, `TRADE_ACTION`, `MqlTradeRequest`, `ORDER_TYPE_*` — no hits). Zero `#include`/`#import` — fully self-contained, no hidden paths via headers. Only side effects: CSV appends to its own three files + `SymbolSelect(...,true)` (adds symbols to the *observer terminal's* Market Watch — benign, worth knowing). |
| Hidden modify paths | **NONE** | All `Position*`/`HistoryDeal*` calls are getters. `const bool BROKER_ACTION_ALLOWED = false` is compile-time, not an input — cannot be flipped by preset. |
| Dry-run/demo lock | **PASS** | `OnInit` hard-fails unless `InpDryRunOnly=true`; demo-marker required; "live"/"real" servers refused. Sufficient for a no-trade-call EA (the lock is belt-and-suspenders on top of structural read-onlyness). |
| Attach script guards | **PASS** | Refuses standard demo terminal data dir AND standard terminal exe unless `--allow-standard-demo-terminal`; builds isolated portable root (`C:\MT5PortablePositionPathObserver`); compiles in a scratch tree (never touches any terminal's live MQL5 folder); backs up the portable profile before replacing; archives (moves, never deletes) prior observer logs; writes a JSON+MD audit report. The chart template carries the safe preset inline and one `<expert>` block only — test-asserted. |
| Existing EAs untouched | **PASS** | Nothing in EA or script reads/writes the standard terminal's profile, charts, or MQL5 tree (config `*.dat` files are *copied out*, read-only with PermissionError tolerance). |

---

## 2. The One Decision That Matters: which terminal, which login

The portable-first design is correct **and** sufficient — the observer does NOT need the
standard terminal. MT5 positions live on the *account*, not the terminal: the script copies
`accounts.dat`/`servers.dat` from the standard terminal's config, so the portable terminal
opens with the same saved demo login (`1025742`) and will stream the same open positions.
Concurrent sessions on one MT5 demo account are supported.

Required verification at attach (add to the procedure):
1. Startup row shows `account_login = 1025742` and `account_server = Capital.ComMena-Demo`.
2. While the trading terminal has open positions, the snapshot file shows `FIRST_SEEN`/`SNAPSHOT` rows within ~20 s with matching tickets, and `open_positions_total` matches the trading terminal.
3. If the copied session demands a password re-entry, **log in with the account's INVESTOR password**, not the master password. Investor mode makes the entire observer terminal broker-side read-only — a stronger guarantee than any code review can give. Recommend this regardless of whether re-entry is prompted.

Fallback only if same-account dual login misbehaves on Capital.com (rare): standard-terminal
attach via the WR50 append procedure (graceful close, profile backup, append one chart,
`--allow-standard-demo-terminal`, owner approval recorded in the attachment report — the
script already journals that flag honestly as `existing_trading_eas_touched: true`).

---

## 3. Bugs / Required Changes (before trusting the data)

### 3.1 Slippage attribution bug — fix before attach (10 lines)
`SlippagePointsForExit` (L713–738) picks its reference level by comparing `exit_price` to
`entry_price`: any close on the profit side of entry is measured against `tp_initial`, any
on the loss side against `sl_initial`. Consequences: a manual/kill-switch/guardian close,
or any future BE-style exit near entry, produces a large bogus "slippage" number (distance
to a TP that was never hit); and SL-modified positions are measured against the *initial*
SL rather than the SL that was actually active. Fix: select the reference from
`exit_reason` (`DEAL_REASON_SL → sl_last`, `DEAL_REASON_TP → tp_last`) and emit empty/`NA`
for `CLIENT/EXPERT/MOBILE/WEB/OTHER`. The raw columns (`exit_reason`, `sl_last`, `tp_last`,
`exit_price`) are all logged, so historical rows are recomputable offline — but don't ship
a known-wrong column into a dataset built to settle exit arguments.

### 3.2 Magic mapping — verified gaps against actual broker data (15 minutes)
Actual magics observed in the broker CSV vs the observer's map:

| Observed | Candidate | Observer maps it? |
|---|---|---|
| 920101–920104, 920201–920204, 920301–920304, 920401/403, 920501–920504 | five executor families | **Yes** (band checks — correct) |
| 921101, 921201–921202 | repair lanes | **Yes** |
| 931000 + comment | p2weakness_br_v1 | **Yes** |
| **930000 / 930100 / 930200** | WR50 BEV0 / BQV0 / E1R0 | **No** — falls to comment `"WR50"` → `WR50_unknown` (lossy) |
| **930300/930400** | WR50 WST12/WST15 | **Exact-match only** — registry assigns bands 930300–930399/930400–930499, and every other lane uses base+offset per instance; if WST instances ever use offsets the mapping silently misses |
| **930101 (historical p2weakness)** | p2weakness_br_v1 | Only via comment `P2WEAKNESS` (it sits inside the WR50-BQV0 band — a genuine registry collision). Comment check runs first, so it works *today*; brokers can rewrite position comments, so magic-first mapping is the durable rule |
| **932100 (W1D1, not yet attached)** | W1D1 momentum | **No** → `unknown_magic_932100` |

Fix: convert WST to band checks, add the three old WR50 bands and 932100–932199, and note
the 930101 collision in `MAGIC_NUMBERS.md`. Longer term: generate the mapping from the
registry into an include/Files CSV instead of hand-coding it twice (this is the second EA
carrying a hand-written copy).

### 3.3 Restart semantics — document, and compensate offline
In-memory state dies on reload: (a) positions that close while the observer is offline get
**no summary row ever** (`DetectClosedPositions` only checks the rebuilt active list);
(b) after restart, open positions re-emerge as `FIRST_SEEN`, `snapshots_count` resets, and
`sl_initial` re-locks to the *current* SL. Today (b) is harmless — no running EA modifies
SLs — but the moment any BE/trail experiment deploys, restart-contaminated R baselines
appear. Required: the analysis pipeline treats `PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv` as
closure ground truth (join on ticket; summary rows are enrichment, not census), prefers the
broker CSV's SL for R math, and a coverage report quantifies the gaps (§5). Add the caveat
to the doc.

---

## 4. Data-Quality / Schema Answers

- **10-second cadence: yes.** Median holds are 20–32 min → ~120–190 rows per trade; worst-case June 11 load (~20 positions) ≈ 7,200 rows/h — trivial for CSV. Don't go to ticks; don't bother adding M1-close events (10 s already brackets every M1 close).
- **Daily rotation: correct.** Filename chosen per write from Dubai date, header ensured per file; midnight-spanning positions split across files — the loader must concat by ticket (one line of pandas).
- **FIRST_SEEN / SNAPSHOT / CLOSE_DETECTED: sufficient.** `OnInit` snapshots immediately (catches already-open positions), `OnDeinit` takes a final pass, close detection lags ≤10 s with exact exit price/time/reason recovered from history deals — good design. `CLOSE_DETECTED` hardcodes `same_symbol_same_dir_count=0` (cosmetic inconsistency; fine).
- **Initial-SL locking: correctly implemented** for positions born under observation; the mid-flight-attach caveat is §3.3 — at attach time, positions opened before attach get `sl_initial = current SL` (today: identical, since nothing modifies SLs).
- **Close summary via history deals: reliable.** Sums all `DEAL_ENTRY_OUT/OUT_BY` deals (handles partial closes), latest deal supplies price/reason, PnL includes swap+commission. `HistorySelect` over a wide window per close is fine at current volumes.
- **Schema completeness for the seven planned analyses: complete.** Loser anatomy & winner giveback (`unrealized_R` path + summary `realized_R`), spread-spike SL hits (`spread_points` + `distance_to_sl_points` + `exit_reason`), slippage (after §3.1 fix), time-stop curve (row timestamps + entry time), exposure stacking (`open_positions_total`, `same_symbol_same_dir_count`), ATR-trail replay (`atr14_m5_points` + price path + `initial_stop_points`). Regime columns (M15/H1 slope with availability flags, D1 bias) carry the Review 9 fixes — handle caching and `SLOPE_UNAVAILABLE` are implemented properly this time. No additional fields needed before attach.

---

## 5. Recommended Attach Procedure

1. Apply §3.1 and §3.2 (≈25 minutes), recompile, rerun the focused tests.
2. `--allow-prepare` → build portable root; verify the standard terminal was not touched (script report + spot-check).
3. `--allow-attach` → deploy + scratch-compile + profile write; review `PHASE2_POSITION_PATH_OBSERVER_ATTACHMENT.md`.
4. `--allow-launch` → prefer **investor-password** login; verify §2's three checks; let it run 30 minutes; confirm snapshot rows for every open position and no errors in the terminal journal.
5. Leave running 24/7. It is the highest-data-value process in the project; treat its uptime like production.

## 6. Reports to Generate Once Data Accumulates

- **Day 3 — `POSITION_PATH_COVERAGE_REPORT.md`:** % of broker-CSV positions with ≥1 snapshot (target ≥95%), % of closures with summary rows (target ≥90%), snapshot cadence histogram, restart gaps, unknown-candidate row count (validates §3.2).
- **Week 1–2 — `POSITION_PATH_EXIT_QUALITY_REPORT.md`:** the seven pre-registered questions, per candidate × symbol × session, duplicate-hidden. Headline tables: % of SL-hit trades that reached +0.3/+0.5/+1.0R first; winner max-R vs realized 1.5R giveback; phantom-stop count (spread-spike SL hits where mid never crossed); slippage distribution by exit reason and hour; unrealized-R-vs-time decay curve; max concurrent same-direction exposure timeline.
- Then, and only then: the ATR-trail replay against the plain 1.5R hold, KPI `net_expectancy_R_after_measured_cost`, with any promising exit rule going shadow → fresh forward week → owner approval. The camera does not skip the ladder.

---

## 7. Verdict Recap

**APPROVE_WITH_CHANGES.** Critical blockers: none. Pre-attach fixes: slippage-reference
logic (§3.1), magic bands (§3.2). Attach to the portable terminal with the same-account
(ideally investor) login and the §2 verification; standard terminal is not needed. Document
the restart caveat and make the broker CSV the closure ground truth in analysis. After
Reviews 8–10, this is the first piece of new runtime code that *narrows* uncertainty
instead of adding exposure — attach it before the next trading session if the two fixes
land today.
