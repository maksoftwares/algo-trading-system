# A1 XAU M5 Momentum Frequency-First V4 Demo Replacement Readiness - 2026-07-02

Status: `READY_FOR_REVIEW_NOT_ATTACHED`

## Purpose

The owner rejected sparse momentum lanes as the primary path because they do not satisfy the project objective:

```text
multiple trades on active days
win rate above 50%
positive expectancy
XAUUSD M5 first
```

The current A1 demo momentum lane is the sparse RR2 long-only configuration. It is robust, but it is not a good fit for the frequency-first objective. The current best replacement candidate is:

```text
freq_h1_h4_long_rr0p7_v4_combo_rank1
```

## Candidate Summary

| Field | Value |
|---|---|
| EA | `A1XauM5MomentumContinuationExecutor.mq5` |
| Symbol / timeframe | `XAUUSD` / `M5` |
| Account | A1 `1025742` only |
| Direction | LONG only |
| Trend filters | H1 + H4 EMA20/50 aligned |
| Target | `0.7R` |
| Cost cap | `cost_R <= 0.05` |
| Blocked server hours | `2,9,10,11,12,13,17,19,21,23` |
| Max trades/day | `12` |
| Cooldown | `5` minutes |
| Fixed lot | `0.01` |
| Magic | `932200` if replacing RR2 |
| Run ID | `A1_XAU_M5_MOMENTUM_FREQ_FIRST_V4_COMBO_RANK1_20260702` |

## Four-Year MT5 Evidence

| Window | Trades | Win Rate | Net USD | PF | Avg Trades / Active Day |
|---|---:|---:|---:|---:|---:|
| 2022.07 -> 2024.06 | 520 | 65.00% | +309.24 | 1.40 | 2.91 |
| 2024.07 -> 2026.06 | 612 | 66.67% | +732.83 | 1.47 | 3.00 |
| 2022.07 -> 2026.06 | 1132 | 65.90% | +1042.07 | 1.45 | 2.96 |

Robustness:

```text
Active entry days: 383
Positive months: 36
Negative months: 11
Top-10 winners removed: still +899.51 USD
Nearby hour masks remain profitable, so V4 is not dependent on one exact mask.
```

## Tooling Status

The A1 momentum attach script now supports explicit variant selection:

```powershell
.\xau-usd\xauusd-phase0\.venv\Scripts\python.exe `
  .\xau-usd\xauusd-phase1\scripts\attach_a1_xau_m5_momentum_continuation.py `
  --variant freq_v4
```

Important:

```text
This command has NOT been run as part of this readiness note.
No demo terminal was touched by this note.
No profile, chart, preset, EA runtime, order, or position was changed.
```

## Guards

Before attachment:

```text
1. Independent reviewer accepts V4 as demo-test-worthy.
2. Owner explicitly approves replacing the sparse RR2 lane.
3. There is no open/pending magic 932200 exposure.
4. The V4 spec SHA256 matches:
   2b5fe5ba37f5649353534a06f682c328f4c410ebd2ef95a45986e3172b19db3b
5. Attachment is a replacement/supersession, not a parallel stack, unless owner explicitly chooses parallel testing with a new magic.
```

After attachment:

```text
1. Compile log must show 0 errors.
2. Startup log must show the V4 run ID.
3. Signal log must show V4 guard decisions.
4. First order or guard-block row must be captured.
5. Status page must show V4 as the active A1 momentum lane and RR2 as superseded.
```

## Forward Test Gate

Minimum observation:

```text
>= 100 closed trades
>= 4 active trading weeks
>= 20 active trading days
no input changes
no lot-size changes
```

Pass candidate:

```text
WR >= 55%
PF >= 1.25
net positive
average trades per active day >= 2.0
positive after removing top 5 winners
no safety/runtime violation
```

Kill or revise:

```text
net negative after 60 closed trades
rolling 40-trade PF < 0.90
WR < 50% after 80 closed trades
equity drawdown > 15% for this lane
average trades per active day < 2.0 after 20 active days
any account/symbol/magic/lot violation
```

## Decision

`freq_h1_h4_long_rr0p7_v4_combo_rank1` is the current best match for the original frequency-first objective. It is not proven and not attached yet. The next valid move is independent review, then owner-approved demo replacement of the sparse RR2 lane if accepted.
