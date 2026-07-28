# EURUSD Neutral Growth/Risk Selected Portfolio: Confirmation Verdict

Date: 2026-07-28

## Verdict

`N47_NEUTRAL_GROWTH_RISK_SELECTED` is rejected in untouched 2023 confirmation.

Status:

`REJECTED_IN_CONFIRMATION_2024_2026_FORBIDDEN`

The selected Asia-plus-Europe portfolio did not generalize from profitable 2022 development. No 2024, 2025, or 2026 EURUSD outcome was loaded.

## Development versus confirmation

| Window | Trades | Win rate | Payoff | PF | Net | Drawdown |
|---|---:|---:|---:|---:|---:|---:|
| 2022 development | 54 | 48.15% | 1.471 | 1.366 | +10.356R | 6.122R |
| 2023 confirmation | 60 | 31.67% | 1.526 | 0.707 | -11.686R | 17.158R |

The target and execution mechanics continued to produce the intended payoff neighborhood. The failure came from directional selection: the win rate fell well below both the frozen 40% confirmation floor and the desired 45–55% range.

## 2023 specialist and side results

| Slice | Trades | Win rate | Payoff | PF | Net |
|---|---:|---:|---:|---:|---:|
| Asia 03:00 | 39 | 38.46% | 1.568 | 0.980 | -0.450R |
| Europe 09:00 | 21 | 19.05% | 1.471 | 0.346 | -11.236R |
| LONG | 31 | 38.71% | 1.467 | 0.927 | -1.412R |
| SHORT | 29 | 24.14% | 1.580 | 0.503 | -10.274R |

Every profitability, expectancy, drawdown, and expert-robustness gate that should reject the portfolio did so.

## Firewall audit

- Candidate census: 71 for 2023, with another 133 reserved for 2024–2026 H1.
- Executed 2023 trades: 60.
- Risk-ceiling cash decisions: 11.
- EURUSD stage requested: 2023 only.
- Last loaded EURUSD M5 timestamp: `2023-12-29T21:55:00Z`.
- `future_rows_loaded`: false.
- `forward_eurusd_outcomes_loaded`: false.
- Broker action: forbidden.

## Research interpretation

The external three-market consensus preserved a roughly 1.5 realized payoff but lacked stable EURUSD direction. Asia was much less unstable than Europe, but PF 0.98 is not a pass. Any successor must be separately named, disclose 2022–2023 as development, add a causal transmission condition rather than post-outcome direction reversal, and be locked before opening 2024.
