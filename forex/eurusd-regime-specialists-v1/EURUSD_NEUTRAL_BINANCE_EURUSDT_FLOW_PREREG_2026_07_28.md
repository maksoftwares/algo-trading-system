# EURUSD Neutral Binance EURUSDT executed-flow preregistration

Frozen before the first EURUSD outcome pass for this source on 2026-07-28.

## Hypothesis

Buyer-initiated EUR flow on the login-free EURUSDT spot market may contain
short-horizon directional information that is absent from quoted Dukascopy
volume. At each fixed first-hour clock, the sign of the prior 15 minutes of
executed taker flow will choose the EURUSD side.

This is deliberately a simple source test, not a fitted model.

## Frozen rule

- Regime 1 Neutral dates only.
- Entries at 00:00, 00:15, 00:30, and 00:45 UTC.
- At each entry, use exactly the three immediately preceding, consecutive,
  fully completed EURUSDT M5 bars.
- Sum total quote volume and taker-buy quote volume across the three bars.
- Calculate
  `(2 * taker_buy_quote - total_quote) / total_quote`.
- Enter LONG EURUSD when the value is nonnegative; otherwise enter SHORT.
- A zero value maps to LONG.
- Never abstain.
- Exclude the entire date before outcomes when any clock lacks three
  consecutive bars or positive aggregate quote volume.
- Do not reverse the sign, select an imbalance strength, change the horizon,
  or combine it with price after outcomes.

## Outcome-blind census

| Window | Eligible dates | Forced trades |
|---|---:|---:|
| 2020-2021 development | 185 | 740 |
| 2022-2023 validation | 149 | 596 |
| 2024 validation | 66 | 264 |
| 2025 pseudo-OOS | 80 | 320 |
| 2026 H1 pseudo-OOS | 39 | 156 |
| Total | 519 | 2,076 |

All 519 retained dates have exactly four candidates.

## Frozen execution

- 4-pip EURUSD stop.
- 6-pip target, or 1.5R.
- 12-hour maximum hold.
- Executable bid/ask prices.
- Minimum 0.7-pip spread.
- Additional 0.1 pip of adverse slippage per execution side.
- Stop first when stop and target share one M5 bar.
- Overlapping positions are retained.
- Each ticket carries 0.25 portfolio R.

## Frozen admission

Every chronological window must have:

- at least 120 trades;
- 45%-55% win rate;
- 1.35-1.75 realized payoff;
- PF at least 1.10 and positive expectancy;
- conditional winning-side accuracy at least 70%;
- daily portfolio PF at least 1.10.

Overall admission also requires:

- PF at least 1.30;
- exact oracle precision at least 40%;
- same-side 15-minute oracle precision at least 45%;
- positive net and PF at least 1.15 after another 0.5 pip per trade;
- positive net after removing the best 5% of winners;
- daily portfolio drawdown no more than 20R;
- four executed trades on every eligible date.

## Causality and evidence status

Every flow bar closes before its EURUSD entry. The deterministic direction
rule has no fitted parameters. Oracle membership and EURUSD future paths are
used only after the trade ledger for evaluation.

This archive has already existed and other EURUSD outcomes have been
inspected, so the test is adaptive historical research rather than pristine
out-of-sample evidence. Even a full pass requires at least six months and
400 post-lock observations beginning 2026-07-29 before promotion review.
No historical result authorizes broker action.
