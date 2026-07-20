# V81 Shared-Portfolio Precommitment

Date: `2026-07-20`

This document is frozen before any V81 post-calibration economic outcome is
opened. It prevents a V81 historical pass from being followed by convenient
portfolio rules selected from the combined result.

## Entry Conditions

Shared-account evaluation is permitted only after all six V81 economic stages
pass in order and the complete July 2018 through June 2026 source audit passes.
V59/V60 must remain byte-identical. No V59/V60 candidate, execution rule, cost,
risk rule, trade, or result may be changed to accommodate V81.

## Required Windows

The combined timeline is tested separately on:

- `development_2`: July 2022 through June 2024.
- `confirmation`: July 2024 through June 2025.
- `final`: July 2025 through June 2026.

Each window must retain at least 2.0 accepted entries per full weekday after
account conflicts and risk blocks. Rejected, blocked, or mechanically split
tickets do not count as frequency.

## Economic And Risk Gates

For each required window, the shared account must have positive base and stress
net, base PF at least 1.50, stress PF at least 1.35, at least 60% positive
months, and positive stress net after removing the five largest winners.

Across the shared timeline, stressed closed-trade drawdown may not exceed USD
500 and conservative buffered stressed floating-equity drawdown may not exceed
USD 600. Worst stressed day may not lose more than USD 150 and worst rolling
five full weekdays may not lose more than USD 250. Absolute daily P&L
correlation between V81 and V59/V60 may not exceed 0.50.

The simulation must use actual accepted entry times, bid/ask execution, costs,
overlap, net directional exposure, maximum concurrency, and risk blocks. A
frequency pass without these account interactions is invalid.

Failure is terminal for this exact combination. It cannot be rescued by
changing a threshold, removing a losing period, dropping costs, counting
blocked entries, or loosening a V59/V60 or V81 rule.
