# A1 XAU M5 Regime Specialist Campaign Verdict

Date: `2026-07-13`

Status: `RESEARCH_COMPLETE_NOT_DEMO_READY`

## Plain-English outcome

We did not find one deployable M5 EA for every gold regime.

We found a statistically acceptable but economically weak DOWNTREND specialist.
UPTREND is profitable but loses too much edge in the older half of the ten-year
test. COMPRESSION and CHOP still have no positive high-frequency specialist.
SHOCK is intentionally handled by not trading.

| Regime | Honest status | Best relevant MT5 evidence |
|---|---|---|
| UPTREND | Ten-year confirmation failed | 1,076 trades, 63.94% WR, +$345.88, PF 1.16, 13.68% DD |
| DOWNTREND | Ten-year edge confirmed; not demo-ready | 477 trades, 64.78% WR, +$183.73, PF 1.24, 5.19% DD |
| COMPRESSION | No specialist | Frequent candidate: 545 trades, -$2.92, PF 1.00, 8.72% DD |
| CHOP | No specialist | Least-bad candidate: 179 trades, -$37.28, PF 0.92, 6.18% DD |
| SHOCK | Capital protection | No-trade by design |

All money values above use a `$1,000 USD` MT5 test deposit and fixed `0.01 lot`.
All native reports show `98%` history quality.

## What was actually achieved

The campaign executed `58` frozen five-year candidate runs and `7` untouched
ten-year confirmation runs. It added strict fail-closed ownership for R3 and
made every active router mode block trading when regime data is unavailable.
SHOCK blocks every specialist.

Two DOWNTREND profiles pass all frozen ten-year gates:

| Profile | Trades | Win rate | Net USD | PF | Equity DD | Use |
|---|---:|---:|---:|---:|---:|---|
| `r2_router_v13_ema_short` | 477 | 64.78% | +183.73 | 1.24 | 5.19% | Selected when frequency matters |
| `r2_router_v13_feature_loss_short` | 191 | 69.63% | +169.45 | 1.52 | 3.93% | Cleaner but much sparser alternative |

This is real progress, but neither profile produces enough absolute profit or
trade cadence to meet the owner's full business goal by itself. It is therefore
research-confirmed, not demo-authorized.

## Why the missing regimes failed

- UPTREND: the best five-year result was strong (`PF 1.26`, `8.36% DD`), but
  unchanged ten-year PF fell to `1.16`. The recent edge does not generalize
  strongly enough into 2016-2021.
- COMPRESSION: strict setups had attractive PF but only seven trades. Loosening
  them created 545-1,273 trades and collapsed PF to approximately `1.00`.
- CHOP: trend, sweep, opening reversal, prior-day reclaim, and daily-extreme
  reclaim all had negative expectancy. High win rates did not overcome larger
  losses and trading costs.
- SHOCK: entering during shocks was never an objective; no-trade is the risk
  control.

## Drawdown boundary

The router prevents specialists from leaking into other regimes and blocks on
unknown data or SHOCK. The confirmed R2 profiles stayed below `5.2%` relative
equity DD in ten years. Rejected R4 trend candidates reached `59.89-65.20%` DD,
which validates the decision to keep CHOP disabled.

## Evidence integrity

Ignored native output root:

`xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_REGIME_SPECIALIST_CAMPAIGN_20260713`

| Compact verdict file | Bytes | SHA256 |
|---|---:|---|
| `REGIME_ROUTER_SUBSTITUTION_5Y_20260713.json` | 7,755 | `294593377d9d116270adb48fbd7cb828344d891f72b93997df2a894ae85b6c80` |
| `REGIME_ROUTER_SUBSTITUTION_R2_CONFIRM_10Y_20260713.json` | 3,242 | `bfc0ea28af30c44040fcf93b84fb9fe519b610524ab5ab6f2dd8dda7793bc558` |
| `REGIME_MECHANISM_FOLLOWUP_5Y_20260713.json` | 6,268 | `ae6f407ca18816d02843687d40e2d4129e063a37397bc6131a406df56da8712a` |
| `REGIME_MECHANISM_R1_CONFIRM_10Y_20260713.json` | 2,731 | `d99a6e8524b3d494ec3257607485a4ecca97f758b72352cf2641cfbb3fd8744f` |
| `REGIME_BOUNDED_DISCOVERY_5Y_20260713.json` | 7,349 | `1884f3b955416e8abb6cf2c57c684dbce288fae3075220359b631eb8b2e3842f` |
| `REGIME_BOUNDED_DISCOVERY_R1_CONFIRM_10Y_20260713.json` | 3,237 | `79f0ab22e09c86816c859e41910eedb6c0c4fadada9734869f78e773fa0656ad` |

The zero-trade exact-profile stack is preserved separately. It diagnosed two
conflicting regime owners and was not used as profitability evidence. The
router-substitution repair was preregistered before its MT5 execution.

## Decision

Do not attach this portfolio to demo yet. Keep R2 as the only confirmed research
lane; keep R1, R3, and R4 disabled; keep SHOCK no-trade. The next research phase
must introduce genuinely new R3/R4 mechanisms or revisit the regime definition
out of sample. More threshold sweeps of the rejected families are not justified.
