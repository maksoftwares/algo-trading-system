# W1/D1 Momentum M5 Continuation - Experimental Deployment Note

Date: 2026-06-11

Artifact: `xau-usd/xauusd-phase1/mt5/Experts/W1D1MomentumM5ContinuationExperimental.mq5`

Status: `SOURCE_READY_COMPILES_NOT_ATTACHED`

## Boundary

This is a new experimental EA variant, not a canonical Phase 2 approval and not a live-capital system. It must not be counted as a Phase 0 approved expert until a matching Python research mirror, backtest, and review packet exist.

The existing `W1D1MomentumContinuationExperimental.mq5` is the low-frequency D1-close version. This file is different: it keeps a W1/D1 directional bias, then uses completed M5 bars for pullback-continuation triggers.

## Identity

| Field | Value |
|---|---|
| EA file | `W1D1MomentumM5ContinuationExperimental.mq5` |
| Order comment | `W1D1_M5_EXP` |
| Magic number | `932100` |
| Intended symbol | `XAUUSD` |
| Intended chart | M5 |
| Default lot | `0.01` |
| Default broker action | Off: `InpAllowDemoTrading=false` |
| Kill switch file | `W1D1_M5_MOMENTUM_KILL.txt` |

## Mechanical Shape

1. Build a higher-timeframe bias from D1 EMA fast/slow and W1 multi-week momentum.
2. On each new completed M5 bar, check the M5 EMA, M5 ATR, candle body, and pullback/continuation relationship.
3. If bias and M5 trigger align, emit a `W1D1_M5_EXP SIGNAL` log line.
4. If explicitly armed for demo trading, send a 0.01-lot market order with ATR/floor stop and 1.5R target.

The source includes an impulse-continuation branch, but `InpEnableImpulseTrigger=false` is the committed default because the first bounded scan showed the loose impulse branch increased activity while reducing PF below 1.0.

## Safety Defaults

Committed source is observer-safe by default:

```text
InpAllowDemoTrading=false
InpAllowNonDemoAccounts=false
InpAllowedAccountLogin=0
InpMagicNumber=932100
InpFixedLots=0.01
InpMaxSpreadPoints=75
InpMaxTradesPerDay=12
InpCooldownMinutes=10
InpOnePositionAtATime=false
InpEnableImpulseTrigger=false
```

`InpMaxTradesPerDay=0` is intentionally treated as unlimited, but the committed default remains `12`.

## Compile Proof

Compiled in an isolated scratch portable copy, not in the running MT5 terminals:

```text
Scratch portable: C:\MT5CompileScratch\W1D1M5CompileProof_20260611_1110
Source file: W1D1MomentumM5ContinuationExperimental.mq5
Result: 0 errors, 0 warnings
```

The local compile log was written to:

```text
xau-usd/xauusd-phase1/outputs/reports/compile_W1D1MomentumM5ContinuationExperimental.log
```

That report path is ignored by git under the current output policy.

## Backtest Status

This M5 version has only a preliminary bounded historical backtest. It cannot inherit approval from the parent W1/D1 continuation study.

The parent W1/D1 study result remains:

| Item | Value |
|---|---:|
| Verdict | `FAIL_REJECTED_VERSION_FINAL` |
| Matrix cells with PF >= 1.30 | `0 / 9` |
| PF range | `1.0715 - 1.2764` |
| Average PF | `1.2026` |

Before any owner decision to arm this M5 variant for demo execution, run a locked Phase 0 campaign and review the last-week/forward-week evidence.

## Next Required Work

1. Register and hash-lock a dedicated hypothesis before any formal result-producing campaign.
2. Run a full matrix-style backtest over the longer historical sample.
3. Compare signal frequency, win rate, PF, net expectancy, and cost sensitivity against the current demo lanes.
4. Only then decide whether to attach it as a demo experiment.
