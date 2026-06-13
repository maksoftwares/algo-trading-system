# A3 Round Retest Structured Hypothesis - 2026-06-13

Status: PRE_REGISTERED_PENDING_T17_PREFLIGHT

Scope: experimental demo evidence only on A3 login `1033669`. This does not approve canonical Phase 2, live trading, or real capital. EA-T3 is not built; magic band `933200-933299` remains reserved.

EA: `Account3RoundRetestStructuredExecutor.mq5`

Identity: magic `933100`, comment `RDSTRUCT_V1`, XAUUSD only, all sessions, fixed lot `0.01`.

Kernel: the same independent `symbol_normalized_round_retest_v0` mechanics used by EA-T1. This EA does not include G1 or any impulse veto.

Structural variable: only allow entry if a same-direction confirmed M15 swing break occurred within `20` M15 bars. Because the Phase B write-up did not specify exact constants, this locks the existing swing-breakout definition: confirmed swing left/right equals `4/4`; LONG requires a close above a confirmed M15 swing high; SHORT requires a close below a confirmed M15 swing low.

## Hypotheses

### H-A3S.1 - Full-Stack Outcome

The structured round-retest stack is viable if, over the locked evaluation window:

- profit factor is at least `1.20`,
- window length is at least 2 weeks,
- at least 30 closed trades are available,
- it beats the A1 unfixed round-family duplicate-hidden same-period control by at least `200 AED` or at least `0.30 PF`.

### H-A3S.2 - Structural Filter Efficacy

The M15 structure filter is validated if at least `60%` of `STRUCT_FILTER_BLOCK` rows are losers when matched to the A1 same-period signal/control outcome.

### H-A3S.3 - Brake Efficacy

The G3 streak breaker and G4 daily stop are validated only if blocked rows would have reduced realized A3 expectancy or drawdown. Attribute `STRUCT_FILTER_BLOCK`, G3, and G4 separately and as a combined stack; report overlaps.

## Decision Matrix

| H-A3S.1 | H-A3S.2 | H-A3S.3 | Decision |
|---|---|---|---|
| PASS | PASS | PASS or inconclusive-positive | Promote as validated structural repair candidate under demo governance only. |
| PASS | FAIL | any | Stack promising, structure filter not validated; run one additional 2-week extension with the same locked thresholds. |
| FAIL | PASS | PASS | Structure filter helped but full stack failed; do not arm beyond the locked window without a new owner-reviewed hypothesis. |
| FAIL | any | any | Retire EA-T2 unless owner explicitly approves the single locked extension. |

Permanent-retirement clause: if after the initial window plus one extension, approximately 4 weeks and at least 60 closed trades, this Phase B structural variant fails to beat the A1 control and absolute PF is below `1.0`, the round family closes permanently. No third life is available.

## Locked Parameters

- Structure filter: M15 lookback `20`; swing confirmation left/right `4/4`; reason `STRUCT_FILTER_BLOCK`.
- G2: `FAMMUX_RDSTRUCT_XAUUSD_<dir>_<barTime>` claimed before `OrderSend`.
- G3: 3 own-magic SL closes inside 2 hours pauses to next 4-hour boundary.
- G4: own-magic realized Dubai-day PnL `<= -150 AED` pauses entries until next Dubai day.
- G5: max 1 open position per magic; cost cap `0.15R`; `COST_WARN` above `0.20R`; absolute reject above `0.30R`; spread cap 75 points; minimum 60 seconds between orders; fixed lot `0.01`.
- G6: XAUUSD only; demo marker required; live/real refused; account allowlist `1033669`; shared kill switch `A3_KILL.txt`; committed defaults non-executing.

No threshold changes are allowed after first trade. Supersede with a new dated hypothesis instead of editing this file.
