# A3 Round Retest Guarded Hypothesis - 2026-06-13

Status: PRE_REGISTERED_PENDING_T17_PREFLIGHT

Scope: experimental demo evidence only on A3 login `1033669`. This does not approve canonical Phase 2, live trading, or real capital. A2 (`1033030`, `breakout_retest`) is not touched. A1 (`1025742`) is the treatment-control reference after T0's mutex fix.

EA: `Account3RoundRetestGuardedExecutor.mq5`

Identity: magic `933000`, comment `RDGUARD_V1`, XAUUSD only, all sessions, fixed lot `0.01`.

Kernel: `symbol_normalized_round_retest_v0` mechanics copied into an independent source file: round levels, retest, confirmation candle, ATR/floor stop, and `1.5R` target.

## Hypotheses

### H-A3.1 - Full-Stack Outcome

The guarded round-retest stack is viable if, over the locked evaluation window:

- profit factor is at least `1.20`,
- window length is at least 2 weeks,
- at least 30 closed trades are available,
- it beats the A1 unfixed round-family duplicate-hidden same-period control by at least `200 AED` or at least `0.30 PF`.

### H-A3.2 - Impulse Veto Efficacy

The G1 impulse veto is validated if at least `60%` of `VETO_IMPULSE` rows are losers when matched to the A1 same-period signal/control outcome.

Evidence rule: broker-joined A1/A3 evidence outranks replay or observer-only rows.

### H-A3.3 - Brake Efficacy

The G3 streak breaker and G4 daily stop are validated only if blocked rows would have reduced realized A3 expectancy or drawdown. Attribute G1, G3, and G4 separately and as a combined stack; report overlaps.

## Decision Matrix

| H-A3.1 | H-A3.2 | H-A3.3 | Decision |
|---|---|---|---|
| PASS | PASS | PASS or inconclusive-positive | Promote as validated repair candidate; continue only under owner-approved demo governance. |
| PASS | FAIL | any | Stack promising, veto not validated; run one additional 2-week extension with the same locked thresholds. |
| FAIL | PASS | PASS | Context filter helped but full stack failed; do not arm beyond the locked window without a new owner-reviewed hypothesis. |
| FAIL | any | any | Retire EA-T1 unless the permanent-retirement clause has not yet had its extension window and owner explicitly authorizes that extension. |

Permanent-retirement clause: after the initial window plus one extension, approximately 4 weeks and at least 60 closed trades, if the stack fails to beat the A1 control and absolute PF is below `1.0`, `round_retest_guarded_v1` retires forever. Only the pre-registered Phase B structural variant remains eligible. If Phase B also fails its window, the round family closes permanently.

## Locked Parameters

- G1: `InpImpulseVetoThreshold=-1.5`.
- G2: `FAMMUX_RD_XAUUSD_<dir>_<barTime>` claimed before `OrderSend`.
- G3: 3 own-magic SL closes inside 2 hours pauses to next 4-hour boundary.
- G4: own-magic realized Dubai-day PnL `<= -150 AED` pauses entries until next Dubai day.
- G5: max 1 open position per magic; cost cap `0.15R`; `COST_WARN` above `0.20R`; absolute reject above `0.30R`; spread cap 75 points; minimum 60 seconds between orders; fixed lot `0.01`.
- G6: XAUUSD only; demo marker required; live/real refused; account allowlist `1033669`; shared kill switch `A3_KILL.txt`; committed defaults non-executing.

No threshold changes are allowed after first trade. Supersede with a new dated hypothesis instead of editing this file.
