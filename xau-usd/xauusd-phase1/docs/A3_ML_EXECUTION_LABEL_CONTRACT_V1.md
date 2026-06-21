# A3 ML Execution Label Contract V1

Status: PRELOCK_CONTRACT

This contract owns entry timing, bid/ask side, risk geometry, TP, holding horizon, timeout, gaps, and label application.

The slippage-model contract owns distribution fitting. This contract references the locked slippage model and defines how P50 and P95 values are applied to labels.

## Entry

Rules:

- decision uses completed bars only;
- LONG fills at first fresh ask after decision;
- SHORT fills at first fresh bid after decision;
- no historical same-bar fill;
- entry expires at the close of the next M5 bar.

If no fresh eligible tick arrives, label_status is CANCELLED_NO_FRESH_TICK.

Cancelled signals remain in audit and are excluded from supervised fitting.

## Risk And Target

```text
risk_price = max(
  raw signal risk,
  broker stops level + 5 points,
  3 x spread at virtual fill,
  300 XAU points
)

TP distance = 1.50 x risk_price
```

XAU point means the broker SYMBOL_POINT for XAUUSD as recorded at decision or fill time. If SYMBOL_POINT or equivalent point-size evidence is unavailable, the row is not eligible for candidate labels.

## Executable Quote Side

LONG:

- entry uses ask;
- SL, TP, and timeout exit use bid.

SHORT:

- entry uses bid;
- SL, TP, and timeout exit use ask.

## Holding Horizon

Primary horizon:

```text
MAX_HOLD_ACTIVE_M5_BARS = 288
```

This is 24 active-market hours.

Only completed M5 bars with market data consume the horizon.

Weekend or market closure does not consume it.

The trade remains exposed across closure.

Timeout occurs after the 288th active M5 bar closes, at the first fresh executable quote.

If no fresh quote occurs within 15 active minutes, label_status is DATA_UNRESOLVED_TIMEOUT.

## Gaps

If the first executable quote crosses SL or TP, exit at the actual quote and record level-to-fill slippage.

Do not force a fill at the requested level.

## Ambiguous Aggregate Data

Candidate labels require true tick data.

If only aggregate data is available and SL/TP order is ambiguous, label_status is EXECUTION_AMBIGUITY and the row is excluded from supervised candidate training.

Do not create promotion labels from OHLC adverse-first approximations.

## Slippage Application

The slippage-model contract owns the numeric P50/P95 application rule, including TP favorable-slippage treatment and fold-causal fitting.

This execution-label contract references the locked slippage artifact and requires expected and P95-stress label columns to be produced according to A3_ML_SLIPPAGE_MODEL_CONTRACT_V1.md.

Base bid/ask labels without adequate slippage are marked OPTIMISTIC_DIAGNOSTIC_ONLY.

## Label Columns

Store:

- y_win_expected;
- y_net_R_expected;
- y_win_p95_stress;
- y_net_R_p95_stress;
- y_outcome;
- y_loss_class;
- y_MFE_R;
- y_MAE_R;
- y_holding_seconds;
- y_holding_active_m5_bars;
- label_status.

Allowed outcomes:

- TP;
- SL;
- TIMEOUT_POSITIVE;
- TIMEOUT_NEGATIVE;
- TIMEOUT_FLAT;
- CANCELLED_NO_FRESH_TICK;
- DATA_UNRESOLVED_TIMEOUT;
- EXECUTION_AMBIGUITY;
- DATA_UNRESOLVED.

## Holding-Horizon Change Governance

The holding horizon is a trading-product parameter, not a model-capacity parameter.

The locked primary horizon is 288 active M5 bars.

The horizon-sensitivity table is mechanics-only and informational.

A holding-horizon change is permitted only when all hold:

1. The rationale is stated in trade-economics terms: exposure window, target/stop geometry, session and overnight risk, and signal decay.
2. The rationale does not cite implied feature budget, feature count, or model capacity.
3. A new versioned label contract, new review, and new SHA256 lock are produced.

Explicitly prohibited:

- shortening the horizon because a shorter horizon yields a larger global_feature_budget;
- shortening the horizon in order to admit more features;
- selecting the horizon from any outcome metric: PF, expectancy, win rate, score, or threshold.

A larger implied feature budget is never, by itself, a valid reason to change the holding horizon.
