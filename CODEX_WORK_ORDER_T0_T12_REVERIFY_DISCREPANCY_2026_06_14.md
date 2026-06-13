# CODEX WORK ORDER — T0/T12 Reverify Discrepancy (2026-06-14)

Authorization: owner-directed. This supersedes the two reverify reports dated
2026-06-14 (`A1_GV_MUTEX_RACE_FIX_REVERIFY_2026_06_14.md` and
`PHASE2_T12_BAR_SHADOW_REFRESH_REVERIFY_2026_06_14.md`). Both reports claim
`PASS` with specific evidence (file hashes, row counts, timestamps) that does
not match the files actually present in this repo/branch
(`codex/a3-repair-lane-2026-06-13`). The Monday A3 attach gate stays
**DO_NOT_ATTACH** until this is resolved with reproducible evidence from this
exact checkout.

## Global boundaries (repeat in every report)

- A3 demo login `1033669`. A2 (`1033030`) untouched. A1 (`1025742`) touched
  only for the T0 mutex fix.
- Demo only, no live trading, canonical Phase 2 status unchanged.
- All committed defaults remain non-executing (`InpDryRunOnly=true`,
  `InpBrokerActionAllowed=false`).
- Work in this checkout only: confirm `git rev-parse --show-toplevel` and
  `git rev-parse HEAD` and `git status --porcelain` at the START and END of
  the session and paste all four outputs into the report. If you are working
  in a different clone/worktree than the one at
  `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system`, STOP and say
  so — that is the root cause we need identified.

## Discrepancy observed (independently verified twice, via two different read
paths)

**T0 — `mt5/Experts/Phase2ExperimentalDemoExecutor.mq5`**

| Check | Reverify report claimed | Actual file in repo |
|---|---|---|
| Line count | 1630 (matches HEAD) | 1493 |
| SHA-256 | `a04123fd...` (matches HEAD) | `3b10cbb...` |
| `git diff` vs HEAD | empty | `1 insertion(+), 137 deletions(-)` |
| `OnDeinit`/`OnTimer` present | yes, lines 1536/1567 | absent — file ends mid-`OnInit` at line ~1499 |
| `tests/test_phase2_experimental_demo_mutex.py` | 3 passed | 1 failed (`test_a1_executor_writes_startup_gv_mutex_self_test_row`), 2 passed |

File mtime on the executor predates the reverify report's mtime by ~35
hours — i.e. the source file was not modified when the "PASS" reverify was
written.

**T12 — bar/shadow refresh**

| Check | Reverify report claimed | Actual file in repo |
|---|---|---|
| `m5_replay_bars/XAUUSD_M5_20260601_to_latest.csv` rows | 2736 | 2596 |
| XAUUSD M5 last bar | `2026-06-12 20:55:00` | `2026-06-12 09:15:00` |
| `PHASE2_IMPULSE_VETO_SHADOW_ROWS.csv` rows | 1510 | 1370 |
| Shadow min entry time | `2026-06-01 15:10:00` | `2026-06-03 13:20:00` |

## T0 — Required actions

1. In this checkout, run:
   ```
   git rev-parse HEAD
   wc -l mt5/Experts/Phase2ExperimentalDemoExecutor.mq5
   sha256sum mt5/Experts/Phase2ExperimentalDemoExecutor.mq5
   git diff --stat -- mt5/Experts/Phase2ExperimentalDemoExecutor.mq5
   ```
   and paste raw output into the new report.
2. If the file is truncated (as independently observed), restore
   `OnDeinit(const int reason)` and `OnTimer()` — including the
   `ClaimFamilyMutexBeforeOrder(...)` guard before `OrderSend` and the
   `WriteStartupRow(gv_mutex_self_test_status);` startup self-test row — so
   the file is a complete, compilable superset of HEAD's 1630 lines plus the
   GV-mutex fix. Do not hand-wave; the file must actually contain
   `int OnInit()`, `void OnDeinit(const int reason)`, `void OnTimer()` in that
   order and end cleanly.
3. Run `python3 -m pytest tests/test_phase2_experimental_demo_mutex.py -v`
   and paste the full output (must show 3 passed).
4. Run the MetaEditor compile and paste the actual log file contents (not
   just a path), plus confirm the `.ex5` artifact's file path and mtime.
5. Commit the fix. Write
   `A1_GV_MUTEX_RACE_FIX_REVERIFY2_2026_06_14.md` with all raw command output
   inline (not summarized).

## T12 — Required actions

1. Re-run the M5/H1/H4/D1 bar export and impulse-veto-shadow export for
   XAUUSD in this checkout, targeting current time
   (`2026-06-14`, not capped at Jun 12).
2. After the export, run:
   ```
   python3 - <<'PY'
   import pandas as pd
   m5 = pd.read_csv("outputs/reports/m5_replay_bars/XAUUSD_M5_20260601_to_latest.csv")
   print(m5.shape, m5.iloc[0,0], m5.iloc[-1,0])
   shadow = pd.read_csv("outputs/reports/PHASE2_IMPULSE_VETO_SHADOW_ROWS.csv")
   print(shadow.shape, shadow.entry_time.min(), shadow.entry_time.max())
   PY
   ```
   and paste raw output. The shadow file's minimum entry time must be at or
   before `2026-06-01 15:10:00` (no rows from the front may be dropped) and
   the M5/shadow coverage must extend at least as far forward as the prior
   confirmed ceiling (`2026-06-12 20:55:00`), ideally further given it is now
   2026-06-14.
3. If broker history genuinely does not extend past a given timestamp, state
   that explicitly with the export tool's own "latest available" response —
   do not silently regress below the previously-achieved coverage.
4. Commit the fix. Write
   `PHASE2_T12_BAR_SHADOW_REFRESH_REVERIFY2_2026_06_14.md` with all raw output
   inline.

## Closing requirement

Both new reports must be generated from commands actually run against
`C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system` in this session
— paste raw terminal output, not summaries. The reviewer (Claude) will
re-check the literal file contents and hashes again before any go/no-go is
revisited. Do not mark `A3_COMBINED_PREFLIGHT_REPORT.md` or any attach status
as PASS/READY as part of this work order — that remains gated on a separate
review pass.
