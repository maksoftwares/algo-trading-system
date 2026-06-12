# Repo Review 9 — Phase2TrendGuardedFixObserver Pre-Attachment Review (2026-06-12)

Reviewer role: senior quant + MQL5 code reviewer.
Scope: full read of `Phase2TrendGuardedFixObserver.mq5` (914 lines) and both included
headers, all five committed presets, the test file, the design doc, and the agent.md
2026-06-12 section. Safety claims verified by direct grep/read, not by trusting the doc.

---

## Summary Verdict: **APPROVE_WITH_CHANGES**

The EA is genuinely observer-only and safe to attach as-is — there are **no safety
blockers**. The "changes" are two small fixes that protect the *quality of the evidence*
this observer exists to collect, plus three nice-to-haves. If attachment is time-pressed
(to catch Friday evening), attach now and apply the changes at the next recompile: every
analytical concern below is recoverable offline because the log carries raw timestamps
(UTC + local) and raw slope values.

---

## 1. Safety Audit — PASS on every check

| Check | Result | Evidence |
|---|---|---|
| No order/trade calls | **PASS** | grep for `OrderSend(Async)`, `CTrade`, `trade.Buy/Sell`, `PositionOpen/Modify/Close`, `TRADE_ACTION`, `MqlTradeRequest`, `ORDER_TYPE_*` → zero hits in the EA **and** in both includes (`Phase1Types.mqh`, `Phase1BreakoutRetest.mqh`) |
| Dry-run locked | **PASS** | `InpDryRunOnly = true` default; `OnInit` (L757–763) returns `INIT_FAILED` if it is ever set false — the EA *cannot start* in any non-dry mode |
| Demo-server lock | **PASS** | `OnInit` requires server to contain `"Demo"` and refuses any server containing `"live"`/`"real"` (L765–770) |
| Symbol/candidate lock | **PASS** | must match `InpTargetSymbol`, be in the qualified CSV, and be one of the five allowlisted candidates |
| Presets cannot trade | **PASS** | all 5 presets: `InpDryRunOnly=true`, `InpTargetSymbol=XAUUSD`, `InpExpectedServerMarker=Demo`; no broker-action input exists in the source at all |
| Isolation from running EAs | **PASS** | separate source, unique per-preset log filenames (no file contention between the 5 instances or with live EAs), no `GlobalVariable*`, no chart/profile manipulation, no kill-switch file interaction; only `EventSetTimer(1)` + CSV appends |
| CSV integrity | **PASS** | `AppendCsvRow` (L626–653): retry loop, `FileSeek(SEEK_END)`, flush, close, share-read flags — proper append semantics |
| Test coverage | **PASS** | the pytest file asserts exactly the right forbidden-term, dry-run-lock, field, and preset invariants (I verified every assertion manually; the sandbox here lacks pytest — run it once on the Windows side before attach for the record) |

Attachment itself is the only residual operational risk. Recommendation: attach in the
**portable observer terminal** (`C:\MT5PortableShadowFixObservers`, where
`Phase2ShadowFixObserver` already runs) rather than the live demo terminal. If the owner
prefers the live terminal, follow the WR50 precedent: graceful close → profile backup →
append 5 new XAUUSD M5 charts → restart → verify 5 `ATTACHED_TREND_GUARDED_FIX_TELEMETRY_ONLY`
startup rows and zero changes to existing charts.

---

## 2. Logic Quality

**Is the M15/H1 EMA20 double-slope veto a reasonable first fix?** Yes. It targets the
verified Review 8 mechanism (counter-trend entries from M5 candle color), it is symmetric
(blocks bad longs in downtrends too, so it is not a June-11-shaped patch), it requires
two-timeframe agreement (conservative), and it is XAUUSD-scoped where the defect was
proven. As a *first* shadow rule it is exactly the right shape: one rule, two parameters,
measured against five streams with two controls.

**Is 50 points reasonable?** It is **loose** — 50 points = $0.50 of EMA20 movement (over
45 min on M15, 3 h on H1), tiny against June's $80–150 daily ranges. The veto will label
BLOCK in most mild drifts, so expect a high block rate on the round/session lanes. This is
*acceptable for v1* for one design reason: the raw `m15_ema20_slope_points` and
`h1_ema20_slope_points` are logged on every row, so any stricter threshold (150, 300,
ATR-normalized) can be re-scored offline from the same data without re-running the
observer. The logged BLOCK/KEEP label is a convenience view, not the only view. Sweep
thresholds offline before promoting anything; do not pre-tune the input.

**Should D1 bias join the veto?** Not yet. Telemetry-only (as implemented) is correct.
M15+H1 agreement is already conservative; triple-conditioning would over-block and add a
parameter before there is data. The `d1_bias` column lets you score "veto + D1" offline —
earn its place from the scoreboard, not from intuition.

**Risk of blocking valid breakout shorts?** Real, and the design already handles it: the
`breakout_retest` and `swing_breakout_retest_v0` presets are controls. The Friday/weekly
scoreboard must report blocked-subset performance for the controls separately — if the
veto is deleting profitable breakout shorts (blocked control subset shows positive
expectancy), the rule must stay XAUUSD-weak-lane-scoped or be revised. Note breakout-retest
shorts in a confirmed M15/H1 uptrend were rare and net-negative in the June data, so the
expected control damage is small — but measure, don't assume.

**Candle-color direction is still in the observer — is that a problem?** No — it is
**required**. The observer must reproduce the legacy EAs' signal stream byte-for-byte,
otherwise the measured veto effect does not transfer to the running EAs. The deeper kernel
fix (broken-structure requirement before short level candidates, Review 8 §5.7) is a
separate future lane and must not be mixed into this measurement.

**Shared veto vs per-EA logic?** Shared is right for v1. Per-EA logic now = five rule sets
fitted to one week = the repair-lane mistake again. Differentiate only after the shared
rule's scoreboard shows per-EA divergence.

---

## 3. Evidence Design

**Are the log fields enough for the Friday-evening review?** Mostly yes — the three-policy
comparison is well designed (`legacy_shadow_*` vs `trend_veto_*`/`fixed_shadow_*` on
identical rows, plus `would_signal`, direction, entry/SL/TP, spread, bid/ask, stage,
level data). Two gaps and one method note:

1. **Outcomes are not in the log (by design).** The observer records would-signals only. The scoreboard must resolve each KEEP/BLOCK signal to WIN/LOSS/R by replaying its logged entry/SL/TP against subsequent M5 bars (the dynamic-exit replay script pattern already does this). Count comparisons alone are meaningless.
2. **Cross-check against actual trades.** The legacy EAs are still trading the same signals live. Match observer rows to actual broker trades by minute + symbol + direction (the weakness-shadow methodology) — that gives *realized* PnL for the KEEP and BLOCK buckets, which is stronger than replay. Use both; flag disagreements.
3. One Friday evening will produce maybe 10–40 would-signals across 5 instances. Treat Friday as a smoke test of the pipeline, not as promotion evidence. The promotion bar stays: **one full fresh forward week minimum** (the repo's own rule, which the repair lanes died for skipping).

**Exact metrics to compare (per candidate, and pooled weak-lane vs controls):**

| Metric | Requirement for the veto to advance |
|---|---|
| Would-signals n, kept %, blocked % | kept ≥ ~60% on controls; block rate on weak lanes can be high |
| Blocked-subset net R / PF (replay + matched-actual) | clearly negative (PF < 0.8) — the veto must be blocking *bad* trades, not random trades |
| Kept-subset net R / PF vs unfiltered baseline | improved PF and net R; win rate not lower |
| Controls' blocked subset | near-zero or negative expectancy (veto must not delete breakout edge) |
| Evening XAUUSD subset | kept-subset performance not degraded vs baseline evening |
| Threshold sweep (50/150/300/ATR-norm) offline | pick by expectancy, tie-break to higher kept-count |
| Max adverse same-direction cluster size in kept set | must shrink vs June 11's 5-EA clusters |

---

## 4. Missing Safeguards / Recommended Changes

**Before attaching (or at first recompile) — small, worth doing:**

1. **Time-bucket basis:** `DubaiTimeBucket(TimeLocal())` (L94–105, L840) trusts the host clock; the repair executor used `TimeGMT() + 240 min`, which is deterministic. If the VPS clock is ever not Asia/Dubai, the `legacy_shadow_*` morning/afternoon comparison silently shifts 4 hours. Either switch to the `TimeGMT()+offset` pattern or record a host-timezone assertion in the startup row. (Recoverable offline from `timestamp_utc`, but the logged labels are what the Friday review reads.)
2. **Slope-unavailable ambiguity:** `EmaValue`/`EmaSlopePoints` return `0.0` both on CopyBuffer failure (fresh `iMA` handle warm-up right after attach) and on genuinely flat EMAs — and a 0.0 slope silently produces KEEP. Cache the four indicator handles in `OnInit` (also avoids per-bar handle churn, a known source of intermittent empty buffers) and log `SLOPE_UNAVAILABLE` instead of `0.00` when `copied != 1`. The scoreboard should exclude rows where both slopes are exactly 0.00 in the first ~30 minutes after attach.

**Nice-to-have columns (add when convenient — each has a planned downstream use):**

3. `atr14_m5_points` at signal time — needed for ATR-normalized threshold sweeps and the blocked ATR-trail research; `stop_distance_points` only proxies it.
4. `estimated_cost_r` at signal (spread / stop distance) — lets the scoreboard exclude cost-doomed signals from "the veto saved us" credit.
5. `m15_ema20_distance_points` (price minus EMA20) — cheap stretch/chase context.

Skip ADX and candle body/wick ratios for now — no planned consumer, and every extra field
is a future overfitting invitation. ATR + EMA-distance are the two with defined use.

**Naming/logging nits (non-blocking):**

- Preset `InpCandidateStatus` is inconsistent: `FIX_OBSERVER_V1` (default) vs `REPAIR_OBSERVER_V1` (symbol_normalized preset). Pick one — these strings end up in every log row and will fragment groupbys.
- `broker_action_allowed` is a hardcoded `"false"` literal in rows (honest today, but if such an input is ever added the literal will mask it — derive from a constant).
- Header is written only when the file does not exist; if columns change later, version the filename (the `InpShadowPolicyVersion` field partly covers this — bump it on any schema change).

---

## 5. Final Recommendation

**APPROVE_WITH_CHANGES.**

- **Critical blockers: none.** The EA cannot trade, cannot start outside dry-run/demo, and cannot interfere with running EAs.
- **Apply before or at attach:** time-base fix (or host-clock assertion) and the slope-unavailable/handle-caching fix — ~30 minutes of work protecting the dataset's integrity.
- **Attach in the portable observer terminal** by preference; live terminal acceptable with the WR50 append procedure (profile backup, append-only charts, startup-row verification).
- **Friday evening = pipeline smoke test.** Confirm 5 startup rows, signal rows flowing, slopes non-zero, buckets correct. Promotion evidence requires a full forward week and the §3 metric table, scored by replay *and* matched-actual outcomes — and per the repo's own standing rule, any runtime guard/router change still needs explicit owner approval after that review.

Honest framing for the owner: this observer measures a *patch* (veto) on top of a kernel
whose direction logic remains structurally fragile. If the veto scoreboard is positive, the
sequence is veto-on-weak-lanes first, kernel redesign (broken-structure requirement)
second. The veto is the tourniquet, not the surgery.
