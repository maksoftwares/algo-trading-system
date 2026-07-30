# EURUSD frequency/edge frontier diagnostic

## Result

The best retrospective causal health gate gets the portfolio close to the
average-frequency target without destroying its full-period edge, but it does
**not** make the portfolio demo-ready.

The diagnostic evaluated 500 global and regime-specific rolling gates. Every
gate used only shadow outcomes whose exits were known before the next candidate
entry. Rejected trades remained observable in shadow, so the health state did
not depend on placing orders.

Only four variants passed the diagnostic full-period and both-half stressed
edge checks. None of the gated RSI variants achieved trailing-12-month PF 1.15.
The highest-frequency passing variant used the most recent 30 completed global
shadow outcomes and admitted candidates while trailing PF was at least 1.05.
This rule was selected after inspecting history and may be tested forward only.

## Selected historical diagnostic

The health-gated RSI sleeve was combined with the broker-transferred M15
chop-plus-compression expert. Both were normalized to fixed 0.01-lot P&L.

| Metric | Full two years | Second 12 months |
|---|---:|---:|
| Trades | 447 | 182 |
| Trades per weekday | 0.8563 | 0.6973 |
| Weekday coverage | 43.30% | 37.16% |
| Win rate | 60.18% | 55.49% |
| Payoff ratio | 0.984 | 1.025 |
| Profit factor | 1.487 | 1.278 |
| PF after +0.5 pip | 1.374 | 1.184 |
| Best-5%-removed PF | 1.160 | 0.938 |
| Net at fixed 0.01 lot | +$111.40 | +$29.12 |

The daily learner's diagnostic rate would project the average to 0.8695
trades per weekday before overlap and risk caps. The remaining average-rate gap
to 1.0/day is 0.1305/day.

## Why this still misses the real goal

1. **The frequency is clustered.** The 447 trades occurred on only 226 of 522
   trading days. There were 1.98 trades on an active day but no trade on 56.7%
   of trading days.
2. **The gated RSI rule was mined retrospectively.** Its attractive historical
   result cannot be counted as fresh evidence.
3. **The gated sleeve itself remains weak recently.** Its second-12-month PF
   was 1.142, below the 1.15 floor.
4. **Recent portfolio profit is concentrated.** Removing the largest 5% of
   second-year winners drops combined PF to 0.938.
5. **Forward execution evidence is absent.** Signal parity, outcome parity,
   cost parity, risk interaction, and soak have not been proven prospectively.

The precise missing mechanism is therefore not another way to create several
trades on already-active RSI days. It is an independent specialist that trades
profitably on the currently empty days and survives recent and concentration
tests.

## Boundary

This diagnostic authorizes no orders. The 30-trade/1.05-PF gate can be frozen
as a disarmed forward experiment, but it cannot enter the demo portfolio until
new evidence passes the same portfolio admission gates.

## Reproducibility

- `RESULT.json`:
  `8b0a9ec172f05085a761f8f1625a4eef613d95bdf9fe738bf7710ab551c5a3b6`
- `RESULT.md`:
  `fa2d809eb9b6010ae48faf02ea7a4e1dcdb3e4f7ac8032bad3cfda9075cdd51f`
- `FRONTIER.csv`:
  `8e3c1f15de351945c3d305c8209211f5c85a5e3edec704dccf7d4ca03ca85400`
- `SELECTED_COMBINED_TRADES.csv`:
  `b977310f469648aa7301a9cac5cec1643c6cde92155519eb19246981bf93afa9`
